---
description: Enforce ESSENSYS UX non-regression on desktop, iPhone and iPad for every UI-facing feature. Apply when editing frontend pages/components, Playwright specs, feature manifests, or UX evidence.
globs:
  - "src/pages/**/*.tsx"
  - "src/components/**/*.tsx"
  - "**/*.css"
  - "**/*.scss"
  - "e2e/**/*.ts"
  - "tests/e2e/**/*.ts"
  - "features/*.json"
alwaysApply: false
---

# ESSENSYS UX Matrix Gate

Any UI-facing ESSENSYS feature must prove non-regression on desktop, iPhone and iPad.

Before done:

```bash
python3 scripts/feature_lifecycle/validate_feature_manifests.py
python3 scripts/feature_lifecycle/check_feature_gate.py --strict
npm run test:matrix -- --project=support-desktop --project=support-iphone --project=support-ipad
```

Feature manifests must declare `tests.ux_matrix.required=true`, `devices: [desktop, iphone, ipad]`, matching `required_projects`, screenshot/visual-regression requirements, and `no_armoire_required=true` for domotic UI.

Playwright specs should include:

```ts
// @feature: <feature-id>
// @devices: desktop,iphone,ipad
// @no-armoire
```

Block or mock real mutations to `/api/admin/inject`, `/api/portal/inject`, `/api/web/actions`, and `/scenarios/*/launch` unless explicit dry-run is active.
