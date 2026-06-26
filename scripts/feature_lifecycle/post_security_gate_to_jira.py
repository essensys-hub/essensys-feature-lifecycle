#!/usr/bin/env python3
"""Publish a Security Gate report to Jira as a parent issue + remediation backlog.

Reads the artifacts produced by the security gate
(`.artifacts/security-gate/{summary,trivy,gitleaks}.json`) and:

  1. Builds a rich parent issue (Atlassian Document Format) containing the full
     context a remediation sub-agent needs: scan summary, every finding grouped
     by remediation action, fix commands, and how to extract the Jira token.
  2. Optionally creates one Jira sub-task per remediation group, each with its
     own acceptance criteria, so a sub-agent can pick them up and fix the issues.

Auth: Atlassian Cloud Basic auth (email + API token).

Environment variables:
  JIRA_BASE_URL   default https://essensys-hub.atlassian.net
  JIRA_PROJECT    default SCRUM
  JIRA_EMAIL      Atlassian account email (Basic auth user)
  JIRA_SECRET     Atlassian API token (from SOPS)
  REPO_NAME       repository name shown in the issue (default: cwd name)

Usage:
  # dry run — print the issue (markdown preview) without touching Jira
  python3 post_security_gate_to_jira.py --dry-run

  # create the parent issue only
  python3 post_security_gate_to_jira.py

  # create the parent issue + remediation sub-tasks
  python3 post_security_gate_to_jira.py --with-subtasks
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SEVS = ("critical", "high", "medium", "low")


def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Findings extraction
# --------------------------------------------------------------------------- #
def collect_findings(artifacts: Path) -> dict:
    summary = read_json(artifacts / "summary.json") or {}
    trivy = read_json(artifacts / "trivy.json") or {}
    gitleaks = read_json(artifacts / "gitleaks.json") or []

    secrets = []
    for f in gitleaks if isinstance(gitleaks, list) else []:
        secrets.append(
            {
                "rule": f.get("RuleID", "secret"),
                "file": f"{f.get('File', '?')}:{f.get('StartLine', '?')}",
                "commit": f.get("Commit") or "working-tree",
            }
        )

    vulns = []
    miscs = []
    for result in trivy.get("Results", []) or []:
        target = result.get("Target", "?")
        for v in result.get("Vulnerabilities", []) or []:
            vulns.append(
                {
                    "sev": str(v.get("Severity", "UNKNOWN")).upper(),
                    "pkg": v.get("PkgName", "?"),
                    "installed": v.get("InstalledVersion", "?"),
                    "fixed": v.get("FixedVersion", "—"),
                    "id": v.get("VulnerabilityID", "?"),
                    "target": target,
                }
            )
        for m in result.get("Misconfigurations", []) or []:
            miscs.append(
                {
                    "sev": str(m.get("Severity", "UNKNOWN")).upper(),
                    "id": m.get("ID", "?"),
                    "title": m.get("Title", ""),
                    "target": target,
                    "resolution": m.get("Resolution", ""),
                }
            )

    return {"summary": summary, "secrets": secrets, "vulns": vulns, "miscs": miscs}


def remediation_groups(data: dict) -> list[dict]:
    """Group findings into actionable remediation tasks for sub-agents."""
    groups: list[dict] = []

    if data["secrets"]:
        groups.append(
            {
                "key": "secrets",
                "summary": "Trier et révoquer les secrets détectés (gitleaks)",
                "severity": "high",
                "items": [f"{s['rule']} — {s['file']} ({s['commit']})" for s in data["secrets"]],
                "acceptance": [
                    "Confirmer si chaque match est un vrai secret ou un exemple/faux positif.",
                    "Vrai secret : révoquer + rotation, purger l'historique git, ne JAMAIS muter.",
                    "Faux positif : ajouter une allowlist justifiée dans .gitleaks.toml.",
                    "gitleaks dir . repasse au vert.",
                ],
            }
        )

    # group CVEs by (target, pkg) -> bump to max fixed version
    by_pkg: dict[tuple, dict] = {}
    for v in data["vulns"]:
        if v["sev"] not in ("CRITICAL", "HIGH"):
            continue
        k = (v["target"], v["pkg"])
        g = by_pkg.setdefault(
            k, {"target": v["target"], "pkg": v["pkg"], "installed": v["installed"], "fixed": set(), "cves": set()}
        )
        g["cves"].add(v["id"])
        for fv in str(v["fixed"]).replace(" ", "").split(","):
            if fv and fv != "—":
                g["fixed"].add(fv)

    for (target, pkg), g in sorted(by_pkg.items()):
        ecosystem = "go" if target.endswith("go.mod") else "npm" if "package" in target else "dep"
        fixed_str = ", ".join(sorted(g["fixed"])) or "dernière version corrigée"
        groups.append(
            {
                "key": f"cve-{ecosystem}-{pkg}".replace("/", "-"),
                "summary": f"Bump {pkg} ({g['installed']}) → {fixed_str} [{len(g['cves'])} CVE]",
                "severity": "high",
                "items": [f"{pkg} {g['installed']} ({target})"] + sorted(g["cves"]),
                "acceptance": [
                    f"Mettre {pkg} à une version >= corrigée ({fixed_str}), garder le pin.",
                    "Mettre à jour le lockfile (go.mod/go.sum ou package-lock.json).",
                    "trivy fs . ne remonte plus ces CVE en HIGH/CRITICAL.",
                    "Build + tests verts.",
                ],
            }
        )

    for m in data["miscs"]:
        if m["sev"] not in ("CRITICAL", "HIGH"):
            continue
        groups.append(
            {
                "key": f"misconfig-{m['id']}",
                "summary": f"Misconfig {m['id']} — {m['title']} ({m['target']})",
                "severity": m["sev"].lower(),
                "items": [f"{m['target']}: {m['title']}"],
                "acceptance": [
                    m["resolution"] or "Corriger la misconfiguration signalée par Trivy.",
                    "trivy fs --scanners misconfig ne remonte plus ce point.",
                ],
            }
        )

    return groups


# --------------------------------------------------------------------------- #
# ADF (Atlassian Document Format) builders
# --------------------------------------------------------------------------- #
def adf_text(text, marks=None):
    node = {"type": "text", "text": text}
    if marks:
        node["marks"] = marks
    return node


def adf_para(*children):
    return {"type": "paragraph", "content": list(children)}


def adf_heading(text, level=2):
    return {"type": "heading", "attrs": {"level": level}, "content": [adf_text(text)]}


def adf_bullets(items):
    return {
        "type": "bulletList",
        "content": [
            {"type": "listItem", "content": [adf_para(adf_text(str(i)))]} for i in items
        ],
    }


def adf_code(text):
    return {"type": "codeBlock", "attrs": {}, "content": [adf_text(text)]}


def build_parent_adf(repo: str, data: dict, groups: list[dict], branch: str, commit: str) -> dict:
    s = data["summary"]
    tc = s.get("trivy_counts", {})
    body: list = []
    body.append(adf_heading(f"Security Gate — {repo}", 1))
    body.append(
        adf_para(
            adf_text("Rapport automatique du security gate (open source : gitleaks + Trivy). "),
            adf_text("Bloquant : Critical/High.", [{"type": "strong"}]),
        )
    )
    body.append(
        adf_bullets(
            [
                f"Findings bloquants: {s.get('blocking_findings', '?')}",
                f"Secrets (gitleaks): {s.get('secret_count', 0)}",
                f"Trivy CVE — Critical: {tc.get('critical', 0)} / High: {tc.get('high', 0)} / Medium: {tc.get('medium', 0)}",
                f"Branche: {branch} — Commit: {commit}",
                f"Scan: {datetime.now(timezone.utc).isoformat()}",
            ]
        )
    )

    if data["secrets"]:
        body.append(adf_heading("Secrets détectés (jamais mutés)", 2))
        body.append(adf_bullets([f"{x['rule']} — {x['file']} ({x['commit']})" for x in data["secrets"]]))

    if data["vulns"]:
        body.append(adf_heading("CVE (HIGH/CRITICAL)", 2))
        hi = [v for v in data["vulns"] if v["sev"] in ("CRITICAL", "HIGH")]
        body.append(
            adf_bullets(
                sorted({f"{v['sev']} {v['id']} — {v['pkg']} {v['installed']} → {v['fixed']} ({v['target']})" for v in hi})
            )
        )

    if data["miscs"]:
        body.append(adf_heading("Misconfigurations", 2))
        body.append(adf_bullets([f"{m['sev']} {m['id']} — {m['title']} ({m['target']})" for m in data["miscs"]]))

    body.append(adf_heading("Backlog de correction (sous-tâches pour sub-agent)", 2))
    for i, g in enumerate(groups, 1):
        body.append(adf_para(adf_text(f"{i}. {g['summary']}", [{"type": "strong"}])))
        body.append(adf_bullets(["Critères: " + " ".join(g["acceptance"])]))

    body.append(adf_heading("Contexte pour le sub-agent", 2))
    body.append(
        adf_bullets(
            [
                f"Dépôt: {repo} (Go/Node selon surface).",
                "Politique: secrets jamais mutés (rotation + scrub historique). CVE: bump + lockfile, garder le pin.",
                "Outils: gitleaks (secrets), trivy fs --scanners vuln,misconfig (CVE/IaC).",
                "Re-scan local: trivy fs . --scanners vuln,misconfig --severity CRITICAL,HIGH --ignore-unfixed",
                "Token Jira via SOPS (jamais en clair): voir bloc ci-dessous.",
            ]
        )
    )
    body.append(
        adf_code(
            'cd essensys-ansible\n'
            'export SOPS_AGE_KEY_FILE="$PWD/.age/keys.txt"\n'
            'export JIRA_SECRET="$(sops -d --extract \'["JIRA_SECRET"]\' secrets/cloud/essensys.sops.yaml)"'
        )
    )
    return {"type": "doc", "version": 1, "content": body}


def build_subtask_adf(group: dict, parent_key: str | None) -> dict:
    body = [
        adf_para(adf_text(f"Sévérité: {group['severity']}", [{"type": "strong"}])),
        adf_heading("Éléments concernés", 3),
        adf_bullets(group["items"]),
        adf_heading("Critères d'acceptation", 3),
        adf_bullets(group["acceptance"]),
    ]
    if parent_key:
        body.insert(0, adf_para(adf_text(f"Parent: {parent_key}")))
    return {"type": "doc", "version": 1, "content": body}


# --------------------------------------------------------------------------- #
# Jira REST
# --------------------------------------------------------------------------- #
def jira_post(base, email, token, path, payload):
    url = f"{base}/rest/api/3{path}"
    raw = json.dumps(payload).encode("utf-8")
    creds = base64.b64encode(f"{email}:{token}".encode()).decode()
    req = urllib.request.Request(url, data=raw, method="POST")
    req.add_header("Authorization", f"Basic {creds}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"Jira HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:500]}\n")
        raise


def markdown_preview(repo, data, groups, branch, commit):
    s = data["summary"]
    tc = s.get("trivy_counts", {})
    secret_lines = [f"- {x['rule']} — {x['file']} ({x['commit']})" for x in data["secrets"]] or ["- aucun"]
    lines = [
        f"# Security Gate — {repo}",
        "",
        f"- Findings bloquants: **{s.get('blocking_findings', '?')}**",
        f"- Secrets: **{s.get('secret_count', 0)}**",
        f"- Trivy High: **{tc.get('high', 0)}** / Critical: **{tc.get('critical', 0)}** / Medium: **{tc.get('medium', 0)}**",
        f"- Branche: {branch} — Commit: {commit}",
        "",
        "## Secrets",
        *secret_lines,
        "",
        "## Backlog de correction (sous-tâches)",
    ]
    for i, g in enumerate(groups, 1):
        lines.append(f"{i}. **{g['summary']}**  — critères: {'; '.join(g['acceptance'])}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts-dir", default=".artifacts/security-gate")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--with-subtasks", action="store_true")
    ap.add_argument("--issue-type", default="Task")
    ap.add_argument("--subtask-type", default="Sub-task")
    args = ap.parse_args()

    base = os.environ.get("JIRA_BASE_URL", "https://essensys-hub.atlassian.net").rstrip("/")
    project = os.environ.get("JIRA_PROJECT", "SCRUM")
    email = os.environ.get("JIRA_EMAIL", "")
    token = os.environ.get("JIRA_SECRET", "")
    repo = os.environ.get("REPO_NAME", Path.cwd().name)
    branch = os.environ.get("GIT_BRANCH", "?")
    commit = os.environ.get("GIT_COMMIT", "?")

    data = collect_findings(Path(args.artifacts_dir))
    groups = remediation_groups(data)
    title = (
        f"[Security Gate] {repo} — {data['summary'].get('blocking_findings', '?')} findings bloquants"
    )

    if args.dry_run:
        print(markdown_preview(repo, data, groups, branch, commit))
        print(f"\n[dry-run] Parent issue: '{title}' dans {project} ({base})")
        print(f"[dry-run] {len(groups)} sous-tâches seraient créées avec --with-subtasks")
        return 0

    if not email or not token:
        sys.stderr.write("JIRA_EMAIL et JIRA_SECRET requis (export via SOPS).\n")
        return 2

    parent_payload = {
        "fields": {
            "project": {"key": project},
            "summary": title,
            "issuetype": {"name": args.issue_type},
            "description": build_parent_adf(repo, data, groups, branch, commit),
            "labels": ["security-gate", "trivy", "gitleaks", repo],
        }
    }
    parent = jira_post(base, email, token, "/issue", parent_payload)
    parent_key = parent.get("key")
    print(f"Parent créé: {parent_key} — {base}/browse/{parent_key}")

    if args.with_subtasks:
        for g in groups:
            st = {
                "fields": {
                    "project": {"key": project},
                    "summary": f"[{repo}] {g['summary']}"[:250],
                    "issuetype": {"name": args.subtask_type},
                    "parent": {"key": parent_key},
                    "description": build_subtask_adf(g, parent_key),
                    "labels": ["security-gate", g["key"]],
                }
            }
            try:
                sub = jira_post(base, email, token, "/issue", st)
                print(f"  sous-tâche: {sub.get('key')} — {g['summary']}")
            except urllib.error.HTTPError:
                sys.stderr.write(f"  échec sous-tâche: {g['summary']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
