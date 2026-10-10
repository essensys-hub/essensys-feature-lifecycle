#!/usr/bin/env python3
"""Hook Claude Code PreToolUse : Claude ne pose jamais le label `valide` (report-triage-2026-10-005).

Les sessions Claude agissent avec le jeton GitHub de l'utilisateur : le workflow triage-guard
ne peut pas les distinguer d'un humain. Ce hook bloque donc, avant exécution, toute tentative
de poser `valide` par `gh`, par `gh api` ou par un outil MCP GitHub.
Code 2 = appel bloqué (message renvoyé à Claude), 0 = autorisé.
"""

from __future__ import annotations

import json
import re
import sys

VALIDE = re.compile(r"(?<![\w-])valide(?![\w-])", re.IGNORECASE)
ADD_LABEL = re.compile(r"--add-label(?:=|\s+)(\"[^\"]*\"|'[^']*'|\S+)", re.IGNORECASE)
GH_API_LABELS = re.compile(r"\bgh\s+api\b[^\n|;&]*\blabels\b", re.IGNORECASE)
MCP_WRITE = re.compile(r"(issue_write|update_issue|create_issue|add_labels?|labels?_write|issue_edit)", re.IGNORECASE)

MESSAGE = ("Bloqué (report-triage-2026-10-005) : Claude ne pose jamais le label `valide`. "
           "La validation d'un ticket est un acte humain : demande à un mainteneur de le relire "
           "et de poser `valide` lui-même dans GitHub.")


def blocks_bash(command: str) -> bool:
    for match in ADD_LABEL.finditer(command):
        if VALIDE.search(match.group(1)):
            return True
    if GH_API_LABELS.search(command) and VALIDE.search(command):
        return True
    return False


def blocks_mcp(tool_name: str, tool_input: object) -> bool:
    if not MCP_WRITE.search(tool_name):
        return False
    labels = tool_input.get("labels") if isinstance(tool_input, dict) else None
    blob = json.dumps(labels if labels is not None else tool_input, ensure_ascii=False)
    return bool(re.search(r"\"valide\"", blob, re.IGNORECASE))


def should_block(payload: dict) -> bool:
    tool = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    if tool == "Bash":
        return blocks_bash(str(tool_input.get("command", "")))
    if tool.startswith("mcp__"):
        return blocks_mcp(tool, tool_input)
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if should_block(payload):
        print(MESSAGE, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
