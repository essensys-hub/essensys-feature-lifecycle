# ux-matrix-gate

## ADDED Requirements

### Requirement: UI features declare UX matrix

Every UI-facing feature manifest MUST declare a UX matrix when implementation paths or surfaces indicate React/frontend/user interface changes.

#### Scenario: React feature without UX matrix is blocked

- **GIVEN** a feature manifest has `implementation.primary_surface` equal to `react-user`, `react-admin`, or `mixed`
- **WHEN** `scripts/feature_lifecycle/check_feature_gate.py --strict` runs
- **THEN** the gate fails if `tests.ux_matrix.required` is not `true`

#### Scenario: Frontend path without UX matrix is blocked

- **GIVEN** a feature manifest contains implementation paths under `src/pages`, `src/components`, frontend, portal, or Playwright/e2e paths
- **WHEN** the feature gate runs in strict mode
- **THEN** the gate requires `tests.ux_matrix`

### Requirement: Minimum mandatory devices

The UX matrix MUST cover at least desktop, iPhone and iPad.

#### Scenario: Missing iPhone blocks the gate

- **GIVEN** a UI feature manifest declares `tests.ux_matrix.devices` without `iphone`
- **WHEN** the feature gate runs in strict mode
- **THEN** the gate fails with an explicit missing device error

#### Scenario: Required projects cover mandatory devices

- **GIVEN** a UI feature manifest declares `tests.ux_matrix.required_projects`
- **WHEN** the feature gate runs
- **THEN** at least one required project name or explicit device declaration covers each of `desktop`, `iphone`, and `ipad`

### Requirement: Playwright evidence and annotations

A UI feature MUST have Playwright tests and evidence annotations that make device coverage auditable.

#### Scenario: Tests missing device annotations produce a blocking error

- **GIVEN** a UI feature declares Playwright specs
- **WHEN** no declared spec contains `@device: desktop`, `@device: iphone`, `@device: ipad`, `@devices: desktop,iphone,ipad`, or matching project/device text
- **THEN** the feature gate fails in strict mode

#### Scenario: UX evidence records validated devices

- **GIVEN** a UI feature has `tests.ux_evidence.status` set to `passed`
- **WHEN** the feature gate checks the manifest
- **THEN** `tests.ux_evidence.devices_validated` contains desktop, iPhone and iPad

### Requirement: No-armoire guard for domotic UI tests

ESSENSYS domotic UI tests MUST declare and enforce `no_armoire_required=true`.

#### Scenario: Domotic UI feature lacks no-armoire guard

- **GIVEN** a UI feature touches ESSENSYS domotic frontend/backend paths
- **WHEN** `tests.ux_matrix.no_armoire_required` is absent or false
- **THEN** the feature gate fails with a no-armoire guard error

### Requirement: Bootstrap propagates UX matrix gate

The lifecycle bootstrap MUST provide templates for the UX matrix rule and CI workflow.

#### Scenario: Frontend repo bootstrap includes UX matrix assets

- **GIVEN** a repository is bootstrapped and detected as frontend/UI-capable
- **WHEN** lifecycle templates are copied
- **THEN** `.cursor/rules/essensys-ux-matrix-gate.mdc` and `.github/workflows/ux-matrix-gate.yml` templates are available for installation
