#!/usr/bin/env python3
"""Liste des tickets exploitables par Claude dans le Project #6 (report-triage-2026-10-005).

Entrée unique des tâches planifiées : seuls sortent les tickets ouverts validés (`valide`)
ou ouverts par un mainteneur sans label de tri bloquant.

Usage : list_workable.py [--repo owner/repo] [--json] [--show-blocked]
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import project_sync as ps
import triage


def classify(items: list[dict[str, Any]], role_of) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Sépare les issues ouvertes du Project en (exploitables, bloquées). `role_of(repo, login, type)`."""
    workable, blocked = [], []
    for item in items:
        content = item.get("content") or {}
        if content.get("type") != "Issue" or (content.get("state") or "").upper() != "OPEN":
            continue
        repo, login, utype = content.get("repo") or "", content.get("author") or "", content.get("author_type")
        try:
            role = role_of(repo, login, utype)
        except triage.ReadError as exc:
            verdict = triage.Verdict(False, f"lecture impossible : {exc}", "réessayer")
        else:
            verdict = triage.evaluate("open", content.get("labels") or [],
                                      triage.is_maintainer(login, utype, role))
        row = {"ref": f"{repo}#{content.get('number')}", "title": content.get("title"),
               "feature_id": (item.get("fields") or {}).get(ps.FEATURE_ID_FIELD),
               "status": (item.get("fields") or {}).get(ps.STATUS_FIELD), **verdict.to_dict()}
        (workable if verdict.workable else blocked).append(row)
    return workable, blocked


def main(argv: list[str] | None = None, client: ps.GhClient | None = None,
         json_runner: triage.JsonRunner = triage.gh_json) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", help="restreindre à un dépôt owner/repo")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--show-blocked", action="store_true", help="afficher aussi les tickets bloqués (lecture seule)")
    args = parser.parse_args(argv)
    client = client or ps.GhClient(dry_run=True)
    items = list(client.iter_items())
    if args.repo:
        items = [i for i in items if (i.get("content") or {}).get("repo") == args.repo]
    cache: dict[tuple[str, str], str] = {}

    def role_of(repo: str, login: str, utype: str | None) -> str:
        key = (repo, login)
        if key not in cache:
            cache[key] = triage.author_role(repo, login, utype, json_runner)
        return cache[key]

    workable, blocked = classify(items, role_of)
    if args.json:
        print(json.dumps({"workable": workable, "blocked": blocked if args.show_blocked else len(blocked)},
                         ensure_ascii=False, indent=1))
    else:
        print(f"# Tickets exploitables ({len(workable)})")
        for row in workable:
            print(f"- {row['ref']} — {row['title']} ({row['reason']})")
        print(f"\n{len(blocked)} ticket(s) en attente de validation humaine (lecture seule).")
        if args.show_blocked:
            for row in blocked:
                print(f"- {row['ref']} — {row['title']} : {row['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
