#!/usr/bin/env python3
"""Garde-fou des labels de tri, exécuté par le workflow réutilisable triage-guard (report-triage-2026-10-005).

- ouverture / réouverture par un non-mainteneur → `a-valider` ;
- `valide` posé par un non-mainteneur (ou un bot) → retiré, avec un commentaire ;
- `valide` posé par un mainteneur → retire `a-valider` et `besoin-info` ;
- `valide` retiré d'un ticket extérieur ouvert → `a-valider` revient.

Usage (Actions) : triage_guard.py --event-path "$GITHUB_EVENT_PATH" [--apply]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any, Callable

import triage

REFUSED_COMMENT = (
    "Le label `valide` a été retiré : seul un membre de l'équipe mainteneurs peut valider un ticket. "
    "Un mainteneur va relire ce ticket."
)


@dataclass
class GuardAction:
    op: str  # add_label | remove_label | comment
    value: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def decide(event: dict[str, Any], *, sender_role: str, author_role: str) -> list[GuardAction]:
    """Décision pure à partir d'un événement `issues` de GitHub et des rôles déjà résolus."""
    action = event.get("action")
    issue = event.get("issue") or {}
    labels = {label.get("name", "").lower() for label in issue.get("labels") or []}
    author = issue.get("user") or {}
    sender = event.get("sender") or {}
    author_maint = triage.is_maintainer(author.get("login"), author.get("type"), author_role)
    sender_maint = triage.is_maintainer(sender.get("login"), sender.get("type"), sender_role)
    is_open = (issue.get("state") or "open").lower() == "open"
    out: list[GuardAction] = []

    if action in ("opened", "reopened"):
        if not author_maint and triage.VALIDE not in labels and triage.A_VALIDER not in labels:
            out.append(GuardAction("add_label", triage.A_VALIDER))
        return out

    changed = ((event.get("label") or {}).get("name") or "").lower()
    if action == "labeled" and changed == triage.VALIDE:
        if not sender_maint:
            out.append(GuardAction("remove_label", triage.VALIDE))
            out.append(GuardAction("comment", REFUSED_COMMENT))
            if not author_maint and triage.A_VALIDER not in labels:
                out.append(GuardAction("add_label", triage.A_VALIDER))
        else:
            for blocking in triage.BLOCKING_LABELS:
                if blocking in labels:
                    out.append(GuardAction("remove_label", blocking))
        return out

    if action == "unlabeled" and changed == triage.VALIDE and is_open:
        if not author_maint and triage.A_VALIDER not in labels:
            out.append(GuardAction("add_label", triage.A_VALIDER))
    return out


# --------------------------------------------------------------------------- exécution dans Actions

def gh(args: list[str]) -> None:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise triage.ReadError((proc.stderr or proc.stdout).strip()[:300])


def apply(repo: str, number: int, actions: list[GuardAction], runner: Callable[[list[str]], None] = gh) -> None:
    for act in actions:
        if act.op == "add_label":
            runner(["issue", "edit", str(number), "-R", repo, "--add-label", act.value])
        elif act.op == "remove_label":
            runner(["issue", "edit", str(number), "-R", repo, "--remove-label", act.value])
        elif act.op == "comment":
            runner(["issue", "comment", str(number), "-R", repo, "--body", act.value])


def main(argv: list[str] | None = None, json_runner: triage.JsonRunner = triage.gh_json,
         gh_runner: Callable[[list[str]], None] = gh) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--event-path", required=True)
    parser.add_argument("--apply", action="store_true", help="appliquer (sinon affiche seulement)")
    args = parser.parse_args(argv)
    with open(args.event_path, encoding="utf-8") as handle:
        event = json.load(handle)
    if "issue" not in event or (event.get("issue") or {}).get("pull_request"):
        print("Pas un événement d'issue : rien à faire.")
        return 0
    repo = (event.get("repository") or {}).get("full_name", "")
    issue = event["issue"]
    author, sender = issue.get("user") or {}, event.get("sender") or {}
    a_role = triage.author_role(repo, author.get("login", ""), author.get("type"), json_runner)
    s_role = triage.author_role(repo, sender.get("login", ""), sender.get("type"), json_runner)
    actions = decide(event, sender_role=s_role, author_role=a_role)
    print(json.dumps({"repo": repo, "issue": issue.get("number"), "event": event.get("action"),
                      "label": (event.get("label") or {}).get("name"), "author_role": a_role,
                      "sender_role": s_role, "actions": [a.to_dict() for a in actions]}, ensure_ascii=False))
    if args.apply and actions:
        apply(repo, issue["number"], actions, gh_runner)
    return 0


if __name__ == "__main__":
    sys.exit(main())
