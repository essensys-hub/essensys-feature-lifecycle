# Tasks — essensys-ux-matrix-gate-2026-06-030

## Phase 1 — Contract

- [x] 1.1 Extend `features/schema/feature.schema.json` with `tests.ux_matrix` and `tests.ux_evidence`.
- [x] 1.2 Mirror the schema extension into bootstrap template `templates/features/schema/feature.schema.json`.

## Phase 2 — Gate implementation

- [x] 2.1 Add UI-feature detection to `scripts/feature_lifecycle/check_feature_gate.py`.
- [x] 2.2 Add blocking checks for mandatory desktop/iPhone/iPad UX matrix.
- [x] 2.3 Add Playwright annotation/project evidence checks.
- [x] 2.4 Add no-armoire required check for ESSENSYS UI features.
- [x] 2.5 Add local tests/sample manifests for positive and negative gate behavior if practical.

## Phase 3 — CI/rules/skills/templates

- [x] 3.1 Add `.cursor/rules/essensys-ux-matrix-gate.mdc`.
- [x] 3.2 Add `.cursor/skills/essensys-ux-regression-gate/SKILL.md`.
- [x] 3.3 Update `.cursor/skills/playwright-from-spec/SKILL.md` to require UX matrix annotations.
- [x] 3.4 Add bootstrap templates for UX matrix rule and GitHub workflow.
- [x] 3.5 Update README/docs to mention the gate.

## Phase 4 — Validation

- [x] 4.1 Run JSON schema validation for manifests/templates.
- [x] 4.2 Run `python3 scripts/feature_lifecycle/check_feature_gate.py --strict --mirror-repo`.
- [x] 4.3 Run `openspec validate essensys-ux-matrix-gate-2026-06-030 --strict`.
- [x] 4.4 Sync `essensys-memory` OKF/wiki per workspace rule.
