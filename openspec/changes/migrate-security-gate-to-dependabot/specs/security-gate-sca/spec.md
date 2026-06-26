## ADDED Requirements

### Requirement: GitHub-native SCA tooling

The feature lifecycle SHALL use GitHub-native Software Composition Analysis. The `security-gate` workflow and Dependabot alerts are the only sanctioned SCA sources. CodeGuard / Checkmarx One (Cyber AST) MUST NOT be referenced as an active tool anywhere in the lifecycle paths, except in intentionally-archived history under `docs/codeguard/` and the deprecation banner of the retired `codeguard-fix-or-mute` skill.

#### Scenario: Active SCA is Dependabot plus security-gate

- **WHEN** a maintainer inspects the lifecycle security stack
- **THEN** SCA is provided by `.github/dependabot.yml` alerts plus the `security-gate` workflow (secret scan, dependency audit for pip and npm, optional dependency-review for PRs)
- **AND** no active workflow, skill, rule, or doc instructs the use of CodeGuard / Checkmarx / Cyber AST

#### Scenario: Residual reference sweep

- **WHEN** running `grep -ri 'codeguard\|checkmarx\|cyber.ast' .` across the project
- **THEN** the only matches are under `docs/codeguard/**` (archived scan records) or the deprecation banner inside `.cursor/skills/codeguard-fix-or-mute/`

### Requirement: Feature manifest security block records GitHub-native SCA state

The `security` object in `features/schema/feature.schema.json` SHALL describe GitHub-native SCA. It MUST include `sca_tool` (default `"dependabot"`) and `dependabot_alerts_url`, and MUST retain `cve_findings`, `secret_scan`, `muted_findings`, `threat_model_url`, and `owner_security`. It MUST NOT require `codeguard_scan_id` or `codeguard_scan_url`.

#### Scenario: New manifest validates against migrated schema

- **WHEN** a feature manifest sets `security.sca_tool` to `"dependabot"` and omits any `codeguard_*` field
- **THEN** `python3 scripts/feature_lifecycle/validate_feature_manifests.py` passes for that manifest

#### Scenario: Existing manifests reconciled

- **WHEN** the schema migration lands
- **THEN** every existing `features/*.json` manifest is updated to the new `security` shape
- **AND** `validate_feature_manifests.py` and `check_feature_gate.py` both pass

### Requirement: Triage workflow is Dependabot-only

The `security-gate-triage` skill SHALL describe a triage workflow whose inputs are the `security-gate` job logs/artifacts (detect-secrets/gitleaks, dependency-review, pip-audit, npm audit) and the repository Dependabot alerts (via `gh api .../dependabot/alerts` or the Security tab). It MUST NOT reference CodeGuard, Checkmarx, `codeguard-fix-or-mute`, or `docs/codeguard/` as triage inputs.

#### Scenario: Triage reads Dependabot alerts

- **WHEN** a PR is blocked by the `security-gate`
- **THEN** the skill directs the user to read the security-gate artifacts and the repo Dependabot alerts
- **AND** classifies each finding (true positive / false positive / accepted risk)

### Requirement: Dependency fix policy

Dependency findings SHALL be resolved by bumping a direct dependency to the Dependabot `first_patched_version`, or for transitive dependencies via npm `overrides` / pip constraints. The fix MUST keep dependencies pinned.

#### Scenario: Direct dependency bump

- **WHEN** a Dependabot alert reports a direct dependency CVE with a `first_patched_version`
- **THEN** the dependency is bumped to at least that version and the lockfile is updated

#### Scenario: Transitive dependency override

- **WHEN** a vulnerable package is a transitive dependency with no direct upgrade path
- **THEN** the fix pins a safe version via npm `overrides` (Node) or a pip constraint (Python)

### Requirement: Mute policy via Dependabot dismissal

A "mute" SHALL be a Dependabot alert dismissal with a documented reason, recorded in the feature manifest `security.muted_findings[]` with `id`, `severity`, `justification_url`, and `expires_at`. The `justification_url` MUST point to a real dismissal/justification and MUST NOT be fabricated. Secrets MUST NEVER be muted.

#### Scenario: CVE muted with traceability

- **WHEN** a reviewer accepts the risk of a non-secret finding
- **THEN** the Dependabot alert is dismissed with a reason
- **AND** a `security.muted_findings[]` entry is added with a real `justification_url` and an `expires_at`

#### Scenario: Secret is never muted

- **WHEN** a secret is detected
- **THEN** it is never added to `muted_findings`
- **AND** the Git history is scrubbed and the secret rotated

### Requirement: Blocking deployment guardrail

The lifecycle SHALL NOT deploy to eWise while open high or critical Dependabot alerts exist. High and critical findings stay blocking; they are fixed or formally muted before deployment.

#### Scenario: Open critical blocks deployment

- **WHEN** an open high or critical Dependabot alert exists for the feature
- **THEN** deployment to eWise is blocked until the alert is fixed or formally muted with justification

### Requirement: Bootstrap templates the GitHub-native security stack

The `feature-lifecycle-bootstrap` skill SHALL template the security stack as `security-gate.yml.tpl` + `dependabot.yml.tpl` + `security-gate.mdc.tpl`, and MUST NOT offer a `codeguard-pr.yml.tpl` template.

#### Scenario: Bootstrap install plan excludes CodeGuard

- **WHEN** the bootstrap skill lists security templates to install
- **THEN** the list contains `security-gate.yml.tpl`, `dependabot.yml.tpl`, and `security-gate.mdc.tpl`
- **AND** does not contain `codeguard-pr.yml.tpl`
- **AND** the detection/install wording reads "GitHub-native SCA (Dependabot)"

## REMOVED Requirements

### Requirement: CodeGuard fix-or-mute triage

**Reason**: CodeGuard / Checkmarx One (Cyber AST) is retired; SCA is now GitHub-native (Dependabot + security-gate).
**Migration**: Use the `security-gate-triage` skill with Dependabot alerts. The `codeguard-fix-or-mute` skill is kept only as deprecated history with a banner redirecting to `security-gate-triage`; manifest security state moves from `codeguard_scan_id`/`codeguard_scan_url` to `sca_tool`/`dependabot_alerts_url`.
