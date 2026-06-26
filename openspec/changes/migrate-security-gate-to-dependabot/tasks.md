## 1. Manifest schema + existing manifests

- [x] 1.1 In `features/schema/feature.schema.json`, edit the `security` block: remove required `codeguard_scan_id` / `codeguard_scan_url`, add `sca_tool` (string, default `"dependabot"`) and `dependabot_alerts_url` (nullable URI); keep `last_scan_at`, `cve_findings`, `secret_scan`, `muted_findings`, `threat_model_url`, `owner_security`.
- [x] 1.2 Ensure `muted_findings[]` items require `id`, `severity`, `justification_url` (uri), `expires_at` (date-time).
- [x] 1.3 Mirror the same change in the bootstrap template copy `.cursor/skills/feature-lifecycle-bootstrap/templates/features/schema/feature.schema.json`.
- [x] 1.4 Reconcile every existing `features/*.json` (`add-files-viewer-tab.json`, `e2e-reports-archive.json`, `add-config-artifact-type.json`) to the new `security` shape (set `sca_tool: "dependabot"`, add `dependabot_alerts_url`, drop `codeguard_*`).
- [x] 1.5 Run `python3 scripts/feature_lifecycle/validate_feature_manifests.py` and fix until green.

## 2. Dependabot config + security-gate workflow

- [x] 2.1 Create `.github/dependabot.yml` covering `pip` (`requirements*.txt`, `api/requirements-api.txt`), `npm` (JS package dirs), and `github-actions`, raising alerts and patch PRs.
- [x] 2.2 Update `.github/workflows/security-gate.yml` final "Fail on blocking findings" step message to point to `security-gate-triage` + Dependabot (remove the `codeguard-fix-or-mute` mention).
- [x] 2.3 (Per design D-open) Add an `actions/dependency-review-action` step to `security-gate.yml`, PR-scoped, blocking on high.
- [x] 2.4 Confirm blocking posture unchanged: high/critical still fail the job.

## 3. Security rule

- [x] 3.1 Rewrite `.cursor/rules/security-gate.mdc`: state SCA is GitHub-native (Dependabot + security-gate), "CodeGuard / Checkmarx One is no longer used".
- [x] 3.2 Replace the `docs/codeguard/**/*.md` glob and "store justifications under docs/codeguard/" guidance with Dependabot dismissal + manifest `muted_findings` traceability.
- [x] 3.3 Update the routing line to send triage to `security-gate-triage` only (drop `codeguard-fix-or-mute`).

## 4. Skill: security-gate-triage

- [x] 4.1 Rewrite `.cursor/skills/security-gate-triage/SKILL.md` frontmatter description to drop CodeGuard/Checkmarx.
- [x] 4.2 Set triage inputs to security-gate logs/artifacts + repo Dependabot alerts (`gh api repos/{owner}/{repo}/dependabot/alerts` or Security tab); remove `docs/codeguard/` and `codeguard-fix-or-mute` inputs.
- [x] 4.3 Document the fix policy (Dependabot `first_patched_version` for direct deps; `overrides`/constraints for transitive).
- [x] 4.4 Document the mute policy (Dependabot dismissal + `security.muted_findings[]` with `id`, `severity`, `justification_url`, `expires_at`; secrets never muted).
- [x] 4.5 Keep the guardrail: never deploy to eWise with open high/critical Dependabot alerts.

## 5. Skill: feature-lifecycle-bootstrap

- [x] 5.1 Remove `codeguard-pr.yml.tpl` from the Templates list in `SKILL.md`.
- [x] 5.2 Delete `.cursor/skills/feature-lifecycle-bootstrap/templates/.github/workflows/codeguard-pr.yml.tpl`.
- [x] 5.3 Create `.cursor/skills/feature-lifecycle-bootstrap/templates/.github/workflows/dependabot.yml.tpl` (generic Dependabot starter; note: real path is `.github/dependabot.yml`).
- [x] 5.4 Ensure the security stack listed is `security-gate.yml.tpl` + `dependabot.yml.tpl` + `security-gate.mdc.tpl`; update detection/install wording to "GitHub-native SCA (Dependabot)".
- [x] 5.5 Update the template `security-gate.mdc.tpl` to match the migrated rule (no CodeGuard).

## 6. Skill: deprecate codeguard-fix-or-mute

- [x] 6.1 Add a clear "DEPRECATED / RETIRED — CodeGuard abandoned" banner at the top of `.cursor/skills/codeguard-fix-or-mute/SKILL.md` redirecting to `security-gate-triage` + Dependabot.
- [x] 6.2 Preserve file history and its `reference.md` / `examples.md` (do not delete).

## 7. Residual reference sweep

- [x] 7.1 `README.md`: update rows for `security-gate-triage` and `codeguard-fix-or-mute` (mark the latter deprecated).
- [x] 7.2 `docs/features/feature-lifecycle.md`: replace CodeGuard mentions (`security-gate-triage` description, `codeguard-pr.yml`, `docs/codeguard/` exceptions) with Dependabot/security-gate equivalents.
- [x] 7.3 `docs/feature-lifecycle/daily-workflow.en.md` and `daily-workflow.fr.md`: replace "CodeGuard PR" wording with the Dependabot/security-gate step (terms only; keep FR body in French).
- [x] 7.4 `scripts/feature_lifecycle/publish_wise_feature_lifecycle_profile.py`: update the `security-gate-triage` description and the `codeguard-fix-or-mute` entry (mark deprecated).
- [x] 7.5 `scripts/feature_lifecycle/apply_branch_protection.sh`: replace the "Run CodeGuard on PR" required check with the security-gate / Dependabot equivalent.
- [x] 7.6 `scripts/page_tree.py`: relabel CodeGuard scan pages as archived (keep pointing at `docs/codeguard/` history).
- [x] 7.7 Confirm `AGENTS.md` and any other lifecycle path has no active CodeGuard reference.

## 8. Verification

- [x] 8.1 Run `python3 scripts/feature_lifecycle/validate_feature_manifests.py` — passes.
- [x] 8.2 Run `python3 scripts/feature_lifecycle/check_feature_gate.py` — passes.
- [x] 8.3 Run `grep -ri 'codeguard\|checkmarx\|cyber.ast' .` — only `docs/codeguard/**` history and the `codeguard-fix-or-mute` deprecation banner match.
- [x] 8.4 Confirm `feature-lifecycle-bootstrap` no longer offers a CodeGuard template and `security-gate-triage` describes a Dependabot-only fix/mute workflow.
