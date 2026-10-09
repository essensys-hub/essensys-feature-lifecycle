#!/usr/bin/env bash
#
# check_claude_setup.sh — Vérifie que le poste peut piloter Essensys via Claude Code + GitHub Project #6.
#
# Usage: ./scripts/feature_lifecycle/check_claude_setup.sh
# Sortie 0 si tous les prérequis bloquants sont OK ; les outils mobiles sont optionnels (WARN).

set -uo pipefail

OWNER="${ESSENSYS_PROJECT_OWNER:-essensys-hub}"
PROJECT="${ESSENSYS_PROJECT_NUMBER:-6}"
WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ANDROID_SDK="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
fail=0

ok()   { printf '  [OK]   %s\n' "$1"; }
warn() { printf '  [WARN] %s\n         → %s\n' "$1" "$2"; }
ko()   { printf '  [KO]   %s\n         → %s\n' "$1" "$2"; fail=1; }

echo "GitHub"
if ! command -v gh >/dev/null 2>&1; then
  ko "gh CLI absent" "brew install gh && gh auth login"
else
  scopes="$(gh auth status 2>&1 | grep -i 'token scopes' || true)"
  for s in project read:org repo workflow; do
    if grep -q "'$s'" <<<"$scopes"; then ok "scope gh '$s'"; else ko "scope gh '$s' manquant" "gh auth refresh -s $s"; fi
  done
  if title="$(gh project view "$PROJECT" --owner "$OWNER" --format json -q .title 2>/dev/null)"; then
    ok "Project #$PROJECT accessible ($title)"
  else
    ko "Project #$PROJECT inaccessible" "gh auth refresh -s project,read:org"
  fi
fi

echo "Harness Claude Code"
for c in ticket ticket-to-spec checkup feature-status nonreg; do
  if [ -f "$WORKSPACE/.claude/commands/$c.md" ]; then ok "commande /$c"; else ko "commande /$c absente" "essensys-feature-lifecycle/scripts/install-claude.sh"; fi
done
if grep -q 'essensys-governance:begin' "$WORKSPACE/CLAUDE.md" 2>/dev/null; then ok "gouvernance importée dans CLAUDE.md"; else ko "gouvernance non importée" "essensys-feature-lifecycle/scripts/install-claude.sh"; fi
if command -v openspec >/dev/null 2>&1; then ok "openspec CLI"; else ko "openspec CLI absent" "npm i -g @fission-ai/openspec"; fi
if command -v python3 >/dev/null 2>&1; then ok "python3"; else ko "python3 absent" "brew install python"; fi

echo "Tests applicatifs (optionnels)"
if [ -x "$ANDROID_SDK/platform-tools/adb" ]; then ok "adb ($ANDROID_SDK/platform-tools)"; else warn "adb absent" "installer Android SDK platform-tools"; fi
if [ -x "$ANDROID_SDK/emulator/emulator" ]; then
  avds="$("$ANDROID_SDK/emulator/emulator" -list-avds 2>/dev/null | tr '\n' ' ')"
  if [ -n "$avds" ]; then ok "émulateur Android (AVD : $avds)"; else warn "aucun AVD Android" "avdmanager create avd -n essensys-pixel -k 'system-images;android-35;google_apis;arm64-v8a' -d pixel_7"; fi
else
  warn "émulateur Android absent" "sdkmanager emulator"
fi
if command -v xcrun >/dev/null 2>&1 && xcrun --find simctl >/dev/null 2>&1; then ok "simulateur iOS"; else warn "simulateur iOS indisponible" "installer Xcode"; fi
if command -v npx >/dev/null 2>&1; then ok "npx (Playwright)"; else warn "npx absent" "brew install node"; fi
if command -v gotestsum >/dev/null 2>&1; then ok "gotestsum (JUnit Go)"; else warn "gotestsum absent" "go install gotest.tools/gotestsum@latest"; fi

echo
if [ "$fail" -eq 0 ]; then echo "OK — Claude Code peut piloter Essensys via le Project #$PROJECT."; else echo "KO — corriger les points ci-dessus."; fi
exit "$fail"
