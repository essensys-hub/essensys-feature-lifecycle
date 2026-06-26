#!/usr/bin/env bash
# sync_transcripts.sh — Mirror Cursor agent transcripts into the repo so they
# can be versioned alongside the code.
#
# Source : Cursor's per-project transcripts directory (lives outside the repo).
# Target : <repo-root>/transcripts/  (versioned, see .gitignore).
#
# The script is idempotent — re-running it only adds new or modified
# transcripts. It also strips a few well-known secret patterns before writing
# anything into the repo (best-effort, not a substitute for a real secret
# scanner). Use SCRUB=0 to disable the scrub pass.
#
# Usage:
#   scripts/sync_transcripts.sh           # default (sync + scrub + index)
#   SCRUB=0 scripts/sync_transcripts.sh   # raw copy, no scrub
#   DRY_RUN=1 scripts/sync_transcripts.sh # show what would be copied
#
# Called automatically by scripts/hooks/pre-commit when the hook is installed.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
DST="${REPO_ROOT}/transcripts"
SRC="${HOME}/.cursor/projects/Users-I0438973-Projects-SkillsEwise-skills-portal/agent-transcripts"

DRY_RUN="${DRY_RUN:-0}"
SCRUB="${SCRUB:-1}"

log() { printf '[sync-transcripts] %s\n' "$*" >&2; }

if [ ! -d "${SRC}" ]; then
  log "Source directory not found: ${SRC}"
  log "Nothing to sync — exiting cleanly."
  exit 0
fi

mkdir -p "${DST}"

count_new=0
count_updated=0
count_skipped=0

# Optional curation: when transcripts/.allowlist exists, only the UUIDs listed
# in it (one per line, comments with '#' allowed) are synced. This keeps the
# repo focused on the chats that are relevant to the project rather than every
# transcript Cursor has ever produced under this project key.
ALLOWLIST="${DST}/.allowlist"
have_allowlist=0
allowed_uuids=""
if [ -f "${ALLOWLIST}" ]; then
  have_allowlist=1
  allowed_uuids="$(grep -vE '^[[:space:]]*(#|$)' "${ALLOWLIST}" | tr -d ' \t\r')"
  log "Allowlist active — $(printf '%s\n' "${allowed_uuids}" | grep -c . | tr -d ' ') transcript(s) will be considered."
fi

# Cursor stores transcripts as <uuid>/<uuid>.jsonl. We flatten that layout
# into transcripts/<uuid>.jsonl so the index stays simple. NUL-delimited list
# is used to support paths with spaces and stay compatible with macOS bash 3.
src_count=0
while IFS= read -r -d '' src_file; do
  src_count=$((src_count + 1))
  base="$(basename "${src_file}")"
  uuid="${base%.jsonl}"
  if [ "${have_allowlist}" = "1" ]; then
    if ! printf '%s\n' "${allowed_uuids}" | grep -Fxq "${uuid}"; then
      count_skipped=$((count_skipped + 1))
      continue
    fi
  fi
  dst_file="${DST}/${base}"

  if [ -f "${dst_file}" ] && cmp -s "${src_file}" "${dst_file}"; then
    count_skipped=$((count_skipped + 1))
    continue
  fi

  if [ "${DRY_RUN}" = "1" ]; then
    if [ -f "${dst_file}" ]; then
      log "[dry-run] WOULD UPDATE ${base}"
    else
      log "[dry-run] WOULD ADD    ${base}"
    fi
    continue
  fi

  tmp="$(mktemp)"
  trap 'rm -f "${tmp}"' EXIT

  if [ "${SCRUB}" = "1" ]; then
    # Best-effort redaction of common secret shapes. We replace, not delete,
    # so the transcript stays readable (line numbers preserved). Transcripts
    # are JSONL: one JSON record per line, with newlines escaped as \n inside
    # strings. PEM blocks therefore appear as a single line containing
    # literal "\n" sequences — both forms are matched below.
    LC_ALL=C sed -E \
      -e 's/(AKIA[0-9A-Z]{16})/<AWS-ACCESS-KEY-REDACTED>/g' \
      -e 's/(ASIA[0-9A-Z]{16})/<AWS-TEMP-ACCESS-KEY-REDACTED>/g' \
      -e 's/"(SECRET_KEY[A-Z0-9_]*)"[[:space:]]*:[[:space:]]*"[^"]+"/"\1": "<REDACTED>"/g' \
      -e 's/"(ACCESS_KEY[A-Z0-9_]*)"[[:space:]]*:[[:space:]]*"[^"]+"/"\1": "<REDACTED>"/g' \
      -e 's/"(AWS_SESSION_TOKEN)"[[:space:]]*:[[:space:]]*"[^"]+"/"\1": "<REDACTED>"/g' \
      -e 's/(ghp_[A-Za-z0-9]{36,})/<GITHUB-PAT-REDACTED>/g' \
      -e 's/(github_pat_[A-Za-z0-9_]{20,})/<GITHUB-PAT-REDACTED>/g' \
      -e 's/(gho_[A-Za-z0-9]{36,})/<GITHUB-OAUTH-REDACTED>/g' \
      -e 's/(glpat-[A-Za-z0-9_-]{20,})/<GITLAB-PAT-REDACTED>/g' \
      -e 's/(xox[abprs]-[A-Za-z0-9-]{10,})/<SLACK-TOKEN-REDACTED>/g' \
      -e 's/(eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,})/<JWT-REDACTED>/g' \
      -e 's/-----BEGIN [A-Z ]+ PRIVATE KEY-----[^-]*-----END [A-Z ]+ PRIVATE KEY-----/<PRIVATE-KEY-REDACTED>/g' \
      -e 's/-----BEGIN [A-Z ]+ PRIVATE KEY-----(\\n[^"]*)?-----END [A-Z ]+ PRIVATE KEY-----/<PRIVATE-KEY-REDACTED>/g' \
      "${src_file}" > "${tmp}"
  else
    cp "${src_file}" "${tmp}"
  fi

  if [ -f "${dst_file}" ]; then
    if ! cmp -s "${tmp}" "${dst_file}"; then
      mv "${tmp}" "${dst_file}"
      count_updated=$((count_updated + 1))
    else
      rm -f "${tmp}"
      count_skipped=$((count_skipped + 1))
    fi
  else
    mv "${tmp}" "${dst_file}"
    count_new=$((count_new + 1))
  fi
  trap - EXIT
done < <(find "${SRC}" -mindepth 1 -maxdepth 3 -type f -name '*.jsonl' -print0 2>/dev/null)

if [ "${src_count}" -eq 0 ]; then
  log "No .jsonl found in source — nothing to sync."
fi

# Refresh INDEX.md so reviewers can browse the transcripts from GitHub.
if [ "${DRY_RUN}" != "1" ]; then
  index="${DST}/INDEX.md"
  {
    echo "# Cursor Agent Transcripts — Index"
    echo
    echo "_Auto-generated by \`scripts/sync_transcripts.sh\` — do not edit manually._"
    echo
    echo "| File | First line | Lines | Size |"
    echo "|------|------------|-------|------|"
    for f in "${DST}"/*.jsonl; do
      [ -e "${f}" ] || continue
      name="$(basename "${f}")"
      lines="$(wc -l <"${f}" | tr -d ' ')"
      size="$(wc -c <"${f}" | tr -d ' ')"
      # Extract a human-readable title from the first JSONL record if any.
      title="$(head -n1 "${f}" 2>/dev/null \
        | python3 -c 'import json,sys
try:
    d=json.loads(sys.stdin.read())
    t=d.get("title") or d.get("name") or d.get("subject") or ""
    if isinstance(t,str): print(t[:60])
except Exception:
    pass' 2>/dev/null || true)"
      [ -z "${title}" ] && title="(no title)"
      printf '| [%s](./%s) | %s | %s | %s |\n' "${name}" "${name}" "${title}" "${lines}" "${size}"
    done
  } > "${index}"
fi

log "Sync complete — added ${count_new}, updated ${count_updated}, unchanged ${count_skipped}."
