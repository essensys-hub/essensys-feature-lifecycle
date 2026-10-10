#!/usr/bin/env bash
#
# install-claude.sh — Install the Essensys Claude Code harness (commandes + gouvernance).
#
# Les commandes et la gouvernance vivent dans claude/ de ce dépôt (source de vérité).
# Ce script les installe dans l'espace de travail ESSENSYS (parent de ce dépôt par défaut) :
#   - <workspace>/.claude/commands/*.md       (copie des commandes)
#   - <workspace>/CLAUDE.md                   (bloc d'import @…/claude/GOVERNANCE.md)
#   - <workspace>/.claude/hooks/*.py          (hooks, ex. block_self_validation.py)
#   - <workspace>/.claude/settings.json       (hook PreToolUse fusionné, autres réglages conservés)
#
# Usage:
#   ./scripts/install-claude.sh                 # → workspace = dossier parent
#   ./scripts/install-claude.sh /chemin/ESSENSYS
#   ./scripts/install-claude.sh --help
#
# Idempotent : remplace les commandes du même nom et le bloc délimité dans CLAUDE.md.

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

case "${1:-}" in
  -h|--help) usage 0 ;;
  "")        WORKSPACE="$(cd "$SRC_DIR/.." && pwd)" ;;
  *)         WORKSPACE="$(cd "$1" && pwd)" ;;
esac

if [ ! -f "$SRC_DIR/claude/GOVERNANCE.md" ]; then
  echo "Erreur : $SRC_DIR/claude/GOVERNANCE.md introuvable" >&2
  exit 1
fi

mkdir -p "$WORKSPACE/.claude/commands"
cp "$SRC_DIR"/claude/commands/*.md "$WORKSPACE/.claude/commands/"

REL_SRC="$(python3 -c 'import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' "$SRC_DIR" "$WORKSPACE")"
BEGIN="<!-- essensys-governance:begin -->"
END="<!-- essensys-governance:end -->"
BLOCK="$BEGIN
@$REL_SRC/claude/GOVERNANCE.md
$END"

CLAUDE_MD="$WORKSPACE/CLAUDE.md"
touch "$CLAUDE_MD"
if grep -q "$BEGIN" "$CLAUDE_MD"; then
  python3 - "$CLAUDE_MD" "$BEGIN" "$END" "$BLOCK" <<'PY'
import re, sys
path, begin, end, block = sys.argv[1:]
text = open(path, encoding="utf-8").read()
text = re.sub(re.escape(begin) + r".*?" + re.escape(end), lambda _: block, text, flags=re.S)
open(path, "w", encoding="utf-8").write(text)
PY
else
  { [ -s "$CLAUDE_MD" ] && echo; echo "$BLOCK"; } >> "$CLAUDE_MD"
fi

# Hook PreToolUse : Claude ne pose jamais le label `valide` (report-triage-2026-10-005).
mkdir -p "$WORKSPACE/.claude/hooks"
cp "$SRC_DIR"/claude/hooks/*.py "$WORKSPACE/.claude/hooks/"
python3 - "$WORKSPACE/.claude/settings.json" <<'PY'
import json, os, sys
path = sys.argv[1]
settings = {}
if os.path.exists(path) and os.path.getsize(path) > 0:
    with open(path, encoding="utf-8") as handle:
        settings = json.load(handle)
command = 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/block_self_validation.py"'
pre = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
present = any(h.get("command") == command for entry in pre for h in entry.get("hooks", []))
if not present:
    pre.append({"matcher": "Bash|mcp__.*", "hooks": [{"type": "command", "command": command}]})
with open(path, "w", encoding="utf-8") as handle:
    json.dump(settings, handle, indent=2, ensure_ascii=False)
    handle.write("\n")
PY

count="$(ls "$SRC_DIR"/claude/commands/*.md | wc -l | tr -d ' ')"
echo "Installé dans $WORKSPACE : ${count} commandes (.claude/commands), gouvernance importée dans CLAUDE.md, hook block_self_validation (.claude/settings.json)."
echo "Vérifier le setup : $SRC_DIR/scripts/feature_lifecycle/check_claude_setup.sh"
