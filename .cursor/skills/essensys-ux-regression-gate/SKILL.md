---
name: essensys-ux-regression-gate
description: Use when adding, changing, reviewing, or gating ESSENSYS UI behavior. Enforces desktop+iPhone+iPad Playwright coverage, visual evidence, and no-armoire safety before completion.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [essensys, ux, playwright, regression, gate, no-armoire]
    related_skills: [playwright-from-spec, feature-manifest-orchestrator]
---

# ESSENSYS UX Regression Gate

## Overview

ESSENSYS frontends must not regress across device formats. This skill turns UX validation into a feature lifecycle gate: desktop, iPhone and iPad coverage is mandatory for every UI-facing feature, with Playwright evidence and no-armoire safety.

## When to Use

Use this skill when:

- changing React pages/components, CSS/layout, navigation, forms, dashboards, portals or admin screens;
- adding or reviewing Playwright specs;
- creating/updating `features/<id>.json` for a UI feature;
- fixing a feature gate failure about `tests.ux_matrix` or UX evidence;
- touching domotic controls that could send values to firmware, gateway, cloud relay, scenarios, shutters, lights or `/inject` endpoints.

## Required Manifest Fields

For UI features, add under `tests`:

```json
"ux_matrix": {
  "required": true,
  "devices": ["desktop", "iphone", "ipad"],
  "targets": ["support"],
  "required_projects": ["support-desktop", "support-iphone", "support-ipad"],
  "screenshots_required": true,
  "visual_regression_required": true,
  "no_armoire_required": true
},
"ux_evidence": {
  "playwright_report": null,
  "screenshots": [],
  "last_run_at": null,
  "devices_validated": [],
  "status": "not-run",
  "reviewer": null
}
```

When the matrix has actually run and passed, set `ux_evidence.status="passed"` and include `devices_validated: ["desktop", "iphone", "ipad"]` plus report/screenshot paths when available.

## Required Playwright Pattern

Add annotations near each suite header:

```ts
// @feature: <feature-id>
// @spec: openspec/changes/<change>/specs/<capability>/spec.md
// @devices: desktop,iphone,ipad
// @no-armoire
```

Write tests so they are project-agnostic and can run under project names such as `support-desktop`, `support-iphone`, `support-ipad`, `local-desktop`, `remote-iphone`, etc.

## No-Armoire Safety

For domotic UIs, tests must install a guard before interacting with controls:

- block or mock `/api/admin/inject`, `/api/portal/inject`, `/api/web/actions`, `/scenarios/*/launch`;
- require `X-Essensys-Test-Mode: dry-run` or `?test_mode=dry_run` for mutations;
- never point test URLs at a customer gateway or real armoire without explicit dry-run controls.

## Verification Commands

Lifecycle gate:

```bash
python3 scripts/feature_lifecycle/validate_feature_manifests.py
python3 scripts/feature_lifecycle/check_feature_gate.py --strict
```

Frontend matrix example:

```bash
npm run test:matrix -- --project=support-desktop --project=support-iphone --project=support-ipad
```

If the repo uses the ESSENSYS e2e package, also check:

```bash
npx playwright test --list
```

## Common Pitfalls

1. **Only testing Chromium desktop.** Not enough; iPhone and iPad must be declared and evidenced.
2. **Screenshots without assertions.** Use assertions plus screenshots/snapshots, not screenshots alone.
3. **No manifest update.** Tests are invisible to the lifecycle unless `features/<id>.json` declares them.
4. **No-armoire omitted.** Any domotic mutation path must be guarded or mocked.
5. **Evidence marked passed too early.** Only set `status=passed` after the matrix actually ran.

## Verification Checklist

- [ ] UI feature detected and `tests.ux_matrix.required=true`
- [ ] `desktop`, `iphone`, `ipad` present in devices
- [ ] required project names cover desktop/iPhone/iPad
- [ ] Playwright spec includes `@devices: desktop,iphone,ipad`
- [ ] `no_armoire_required=true` for domotic UI
- [ ] `check_feature_gate.py --strict` passes
- [ ] Frontend matrix command run or blocker reported
