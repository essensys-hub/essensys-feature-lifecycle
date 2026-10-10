#!/usr/bin/env python3
"""Gate de tri : un ticket est-il exploitable par Claude ? (report-triage-2026-10-005)

Usage : triage_gate.py <owner/repo#n | URL> [--json]
Codes de sortie : 0 exploitable, 3 non exploitable, 2 lecture impossible (traité comme non exploitable).
"""

from __future__ import annotations

import argparse
import json
import sys

import triage


def main(argv: list[str] | None = None, runner: triage.JsonRunner = triage.gh_json) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ref", help="owner/repo#n ou URL de l'issue")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        info, verdict = triage.check(args.ref, runner)
    except (triage.ReadError, ValueError, KeyError) as exc:
        info = {"ref": args.ref}
        verdict = triage.Verdict(False, f"lecture impossible : {exc}", "réessayer ; en cas de doute, ne rien faire")
        code = triage.EXIT_READ_ERROR
    else:
        code = triage.EXIT_WORKABLE if verdict.workable else triage.EXIT_NOT_WORKABLE
    if args.json:
        print(json.dumps({**info, **verdict.to_dict(), "exit_code": code}, ensure_ascii=False))
    else:
        mark = "✅ exploitable" if verdict.workable else "⛔ non exploitable"
        print(f"{info['ref']} : {mark} — {verdict.reason}")
        if verdict.action:
            print(f"Action attendue : {verdict.action}")
    return code


if __name__ == "__main__":
    sys.exit(main())
