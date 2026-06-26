---
name: feature-userguide-sync
description: Update or create the user-facing documentation linked from `features/<id>.json`. Use when the user asks to sync a feature user guide, refresh docs after implementation, or check whether `docs/features/*.md` is still aligned with the code.
---

# Feature User Guide Sync

Keep the user guide aligned with the feature manifest and the implementation.

## Use this skill when

- The user says `sync user guide for this feature`
- The code changed and `docs/features/<name>.md` must be refreshed
- A feature manifest exists but the user guide is missing or stale

## Workflow

```text
User guide sync:
- [ ] Step 1 - Read features/<id>.json
- [ ] Step 2 - Read implementation paths and current docs page
- [ ] Step 3 - Check i18n keys declared in the manifest
- [ ] Step 4 - Update only docs/features/<name>.md and docs/features/assets/
- [ ] Step 5 - Re-check freshness with scripts/feature_lifecycle/check_feature_gate.py
```

## Required structure

For a French feature page, keep these sections in this order:

1. `# <Feature name>`
2. `## Objectif`
3. `## Où le trouver`
4. `## Fonctionnalités`
5. `## Permissions`
6. `## Limites connues`
7. `## Liens`

If the existing page already has useful custom text, preserve it.

## Required checks

- Read `features/<id>.json` first.
- Read every path listed under:
  - `implementation.paths`
  - `userguide.pages`
  - `userguide.screenshots`
- Verify every key in `userguide.i18n_keys` exists in `wise-skills-react/src/i18n/*.json` when the feature touches the React app.
- Prefer screenshots already stored under `docs/features/assets/`.

## Guardrails

- Never edit files outside:
  - `docs/features/<name>.md`
  - `docs/features/assets/`
- Never invent UI labels or routes that are not present in code.
- Prefer short user-facing prose over architecture details.
- Keep Git as the source of truth; Confluence publication happens later.
