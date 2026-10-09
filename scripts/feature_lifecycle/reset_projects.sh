#!/usr/bin/env bash
#
# reset_projects.sh — Remise à zéro du 2026-10-09 : passe à Done tous les items non-Done
# des Projects legacy de l'org (statut Project uniquement, les issues ne sont pas fermées).
#
# Usage:
#   ./scripts/feature_lifecycle/reset_projects.sh            # dry-run : liste ce qui changerait
#   ./scripts/feature_lifecycle/reset_projects.sh --apply    # applique
#   PROJECTS="1 2 3 5" ./scripts/feature_lifecycle/reset_projects.sh --apply

set -euo pipefail

OWNER="${ESSENSYS_PROJECT_OWNER:-essensys-hub}"
PROJECTS="${PROJECTS:-1 2 3 5}"
APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

for n in $PROJECTS; do
  project_id="$(gh project view "$n" --owner "$OWNER" --format json -q .id)"
  read -r field_id done_id < <(gh project field-list "$n" --owner "$OWNER" --format json \
    -q '.fields[]|select(.name=="Status")|"\(.id) \(.options[]|select(.name=="Done")|.id)"')
  items="$(gh project item-list "$n" --owner "$OWNER" --limit 500 --format json \
    -q '.items[]|select(.status!="Done")|"\(.id)\t\(.status // "-")\t\(.title)"')"
  count=0
  while IFS=$'\t' read -r item status title; do
    [ -z "$item" ] && continue
    count=$((count + 1))
    if [ "$APPLY" -eq 1 ]; then
      gh project item-edit --id "$item" --project-id "$project_id" --field-id "$field_id" \
        --single-select-option-id "$done_id" >/dev/null
      echo "  #$n  $status → Done  $title"
    else
      echo "  [dry-run] #$n  $status → Done  $title"
    fi
  done <<<"$items"
  echo "Project #$n : $count item(s) $([ "$APPLY" -eq 1 ] && echo passés || echo à passer) à Done"
done
[ "$APPLY" -eq 0 ] && echo "Dry-run. Relancer avec --apply pour appliquer."
exit 0
