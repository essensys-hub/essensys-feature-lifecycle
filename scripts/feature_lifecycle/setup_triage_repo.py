#!/usr/bin/env python3
"""Prépare un dépôt qui reçoit des signalements (report-triage-2026-10-005). Dry-run par défaut.

- crée ou met à jour les labels `a-valider`, `valide`, `besoin-info` ;
- écrit le workflow appelant `.github/workflows/triage-guard.yml` dans un checkout local (--checkout).

Usage : setup_triage_repo.py essensys-hub/essensys-support [--checkout CHEMIN] [--apply]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

LABELS = {
    "a-valider": ("FBCA04", "À relire par un mainteneur avant tout travail (signalement ou issue de tiers)"),
    "valide": ("0E8A16", "Validé par un mainteneur : Claude peut travailler sur ce ticket"),
    "besoin-info": ("BFD4F2", "En attente d'informations de la personne qui a signalé"),
}

CALLER_WORKFLOW = """name: Triage Guard

# Validation humaine des tickets venus de l'extérieur (report-triage-2026-10-005).
# Logique : essensys-feature-lifecycle/.github/workflows/triage-guard.yml

on:
  issues:
    types: [opened, reopened, labeled, unlabeled]

permissions:
  issues: write
  contents: read

jobs:
  triage:
    uses: essensys-hub/essensys-feature-lifecycle/.github/workflows/triage-guard.yml@main
"""


def plan(repo: str) -> list[list[str]]:
    return [["label", "create", name, "-R", repo, "--color", color, "--description", desc, "--force"]
            for name, (color, desc) in LABELS.items()]


def main(argv: list[str] | None = None, runner=subprocess.run) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo")
    parser.add_argument("--checkout", help="checkout local du dépôt où écrire le workflow appelant")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    for cmd in plan(args.repo):
        if args.apply:
            proc = runner(["gh", *cmd], capture_output=True, text=True, check=False)
            print(("ok  " if proc.returncode == 0 else "ERR ") + " ".join(cmd[:3]))
        else:
            print("[dry-run] gh " + " ".join(cmd[:3]) + f" -R {args.repo}")
    if args.checkout:
        target = Path(args.checkout) / ".github" / "workflows" / "triage-guard.yml"
        if args.apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(CALLER_WORKFLOW, encoding="utf-8")
            print(f"écrit {target}")
        else:
            print(f"[dry-run] écrirait {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
