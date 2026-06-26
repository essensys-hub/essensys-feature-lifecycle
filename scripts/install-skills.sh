#!/usr/bin/env bash
#
# install-skills.sh — Install the Essensys feature-lifecycle Cursor skills & rules.
#
# Les skills et rules vivent dans .cursor/ de ce dépôt (source de vérité).
# Ce script les copie vers un dépôt cible ou en global (~/.cursor) pour Cursor.
#
# Usage:
#   ./scripts/install-skills.sh                 # → ./.cursor (repo courant)
#   ./scripts/install-skills.sh /chemin/repo    # → <repo>/.cursor
#   ./scripts/install-skills.sh --global        # → ~/.cursor (tous les repos)
#   ./scripts/install-skills.sh --help
#
# Idempotent : remplace skills/rules existants du même nom, sans toucher au reste.

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  sed -n '2,14p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

case "${1:-}" in
  -h|--help) usage 0 ;;
  --global)  DEST_CURSOR="$HOME/.cursor" ;;
  "")        DEST_CURSOR="$(pwd)/.cursor" ;;
  *)         DEST_CURSOR="${1%/}/.cursor" ;;
esac

if [ ! -d "$SRC_DIR/.cursor/skills" ]; then
  echo "Erreur : $SRC_DIR/.cursor/skills introuvable (lancer depuis le dépôt essensys-feature-lifecycle)" >&2
  exit 1
fi

mkdir -p "$DEST_CURSOR/skills" "$DEST_CURSOR/rules"

copy() {
  if command -v rsync >/dev/null 2>&1; then
    rsync -a "$1"/ "$2"/
  else
    cp -R "$1"/. "$2"/
  fi
}

copy "$SRC_DIR/.cursor/skills" "$DEST_CURSOR/skills"
copy "$SRC_DIR/.cursor/rules"  "$DEST_CURSOR/rules"

skills_count="$(find "$DEST_CURSOR/skills" -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')"
rules_count="$(find "$DEST_CURSOR/rules" -maxdepth 1 -name '*.mdc' | wc -l | tr -d ' ')"

echo "Installé dans $DEST_CURSOR : ${skills_count} skills, ${rules_count} rules."
echo "Ouvre le dépôt cible dans Cursor, puis lance : bootstrap feature lifecycle"
