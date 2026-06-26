## Why

The wise feature lifecycle still wires its security gate to **CodeGuard / Checkmarx One (Cyber AST)** for Software Composition Analysis (SCA) and SAST. CodeGuard is being abandoned, and a GitHub-native model already partially exists in this repo (the `security-gate` workflow plus a `security` block in the feature manifest). The lifecycle assets (skills, rules, templates, schema, docs, scripts) are inconsistent: some still reference `codeguard`/`checkmarx`, no `dependabot.yml` exists yet, and the manifest schema still mandates `codeguard_scan_id` / `codeguard_scan_url`. We must converge the entire lifecycle on **Dependabot alerts + the `security-gate` workflow** so triage, bootstrap, manifests, and docs describe a single, GitHub-native SCA story.

## What Changes

- Make Dependabot the canonical SCA tool of the lifecycle: `security` manifest block gains `sca_tool` (default `"dependabot"`) and `dependabot_alerts_url`. **BREAKING**: removes the mandatory `codeguard_scan_id` / `codeguard_scan_url` fields from the manifest schema.
- Add `.github/dependabot.yml` (and a `dependabot.yml.tpl` bootstrap template) that raises alerts and patch PRs.
- Rewrite `.cursor/skills/security-gate-triage/SKILL.md` so triage inputs are the `security-gate` job logs/artifacts and the repo Dependabot alerts; fix policy uses Dependabot `first_patched_version` (direct deps) or `overrides`/constraints (transitive); mute policy is a Dependabot alert dismissal recorded in `security.muted_findings[]`.
- Update `.cursor/skills/feature-lifecycle-bootstrap/SKILL.md`: drop the `codeguard-pr.yml.tpl` template, ensure the security stack is `security-gate.yml.tpl` + `dependabot.yml.tpl` + `security-gate.mdc.tpl`, and reword detection/install as "GitHub-native SCA (Dependabot)".
- Deprecate `.cursor/skills/codeguard-fix-or-mute/SKILL.md` with a retirement banner pointing to `security-gate-triage` + Dependabot (history preserved, not deleted).
- Bring the already-named "canonical" assets to the described target state where they still reference CodeGuard: `.cursor/rules/security-gate.mdc`, `.github/workflows/security-gate.yml` (fail-step message), and the bootstrap template variants.
- Sweep residual `codeguard|checkmarx|cyber.?ast` references across `AGENTS.md`, `docs/`, `README.md`, and `scripts/feature_lifecycle/`, replacing them with the Dependabot / `security-gate` equivalents. Historical scan pages under `docs/codeguard/` stay archived/read-only.

## Capabilities

### New Capabilities
- `security-gate-sca`: The GitHub-native Software Composition Analysis model for the feature lifecycle — what the `security-gate` workflow must run, how Dependabot alerts feed triage, how findings are fixed or muted, how the feature manifest records security state, and the blocking guardrails enforced before eWise deployment.

### Modified Capabilities
<!-- None: openspec/specs/ currently contains no published specs; this is the first capability for the lifecycle security model. -->

## Impact

- **Schema / manifests**: `features/schema/feature.schema.json` `security` block (and the bootstrap template copy); existing manifests under `features/*.json` must be reconciled to the new required fields.
- **Workflows**: `.github/workflows/security-gate.yml`, new `.github/dependabot.yml`.
- **Cursor assets**: `.cursor/skills/security-gate-triage/`, `.cursor/skills/feature-lifecycle-bootstrap/` (+ `templates/`), `.cursor/skills/codeguard-fix-or-mute/`, `.cursor/rules/security-gate.mdc`.
- **Docs**: `AGENTS.md`, `README.md`, `docs/features/feature-lifecycle.md`, `docs/feature-lifecycle/daily-workflow.{en,fr}.md`; `docs/codeguard/` kept archived.
- **Scripts**: `scripts/feature_lifecycle/publish_wise_feature_lifecycle_profile.py`, `apply_branch_protection.sh`, `page_tree.py`; validators `validate_feature_manifests.py` and `check_feature_gate.py` must still pass.
- **No security regression**: high/critical findings stay blocking; mutes require a real Dependabot dismissal/justification.
