---
name: playwright-from-spec
description: Generate or review Playwright coverage from `features/<id>.json` and the linked OpenSpec files. Use when a user asks to add E2E tests for a feature, check Playwright coverage, or fix a PR failing the feature gate because tests are missing or too weak.
---

# Playwright From Spec

Translate feature requirements into concrete Playwright specs.

## Use this skill when

- The user says `generate e2e tests for this feature`
- A PR adds UI behavior and the related spec is missing
- The feature gate warns that `coverage_must_test` is not reflected in E2E titles

## Workflow

```text
Playwright from spec:
- [ ] Step 1 - Read features/<id>.json
- [ ] Step 2 - Read the linked OpenSpec files and existing Playwright spec
- [ ] Step 3 - Map coverage_must_test to concrete test titles
- [ ] Step 4 - Add or update the spec with stable selectors
- [ ] Step 5 - Re-run the feature gate checks
```

## Mandatory rules

- Follow `.cursor/rules/playwright-ui-tests.mdc`.
- Prefer `data-testid` first.
- Use `getByRole()` only when the visible label is stable across i18n.
- Add `@feature: <id>`, `@spec: <openspec path>`, and `@devices: desktop,iphone,ipad` comments near the suite header for UI features.
- Keep smoke-safe read-only tests tagged with `@smoke` when appropriate.
- For ESSENSYS domotic UI tests, enforce a `no-armoire` guard before exercising buttons or controls that could send values to firmware, gateway, cloud relay, scenarios, shutters, lights or `/inject` endpoints. Use `@no-armoire` in the spec header.
- For UI features, update `features/<id>.json` with `tests.ux_matrix` covering desktop, iphone, ipad and evidence placeholders under `tests.ux_evidence`.

## Explicit anti-patterns

Never generate tests like:

- `expect(page).toBeTruthy()`
- raw CSS selectors such as `.btn-danger`
- `:nth-child(...)` selectors

## Output contract

- Update only the spec files listed in `tests.playwright`, or create the missing target file in that same location.
- Keep titles close to `tests.coverage_must_test` so `scripts/feature_lifecycle/check_feature_gate.py` can match them.
- Do not auto-commit; leave a reviewable diff.
