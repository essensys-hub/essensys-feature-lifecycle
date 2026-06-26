## Context

The wise feature lifecycle ships a security gate as part of its Cursor skills + GitHub workflows. Historically SCA/SAST was delegated to **CodeGuard / Checkmarx One (Cyber AST)**. CodeGuard is being retired, so SCA must become GitHub-native (Dependabot alerts + the in-repo `security-gate` workflow).

**Actual current state of this repo (verified, June 2026)** — important because the originating request assumed these were already migrated:

- `.github/workflows/security-gate.yml` runs gitleaks (secret scan), `npm audit`, `pip-audit`, `bandit`, and `eslint-plugin-security`. It does **not** run `actions/dependency-review-action`, and its final fail step still tells users to use `codeguard-fix-or-mute`.
- `.github/dependabot.yml` **does not exist**.
- `.cursor/rules/security-gate.mdc` still references CodeGuard, `docs/codeguard/`, and routes triage to `codeguard-fix-or-mute`; its glob list includes `docs/codeguard/**/*.md`.
- `features/schema/feature.schema.json` `security` block still **requires** `codeguard_scan_id` and `codeguard_scan_url`; it has no `sca_tool` / `dependabot_alerts_url`.
- Residual `codeguard|checkmarx|cyber.?ast` strings exist in `AGENTS.md`-adjacent docs, `README.md`, `docs/features/feature-lifecycle.md`, `docs/feature-lifecycle/daily-workflow.{en,fr}.md`, `scripts/feature_lifecycle/publish_wise_feature_lifecycle_profile.py`, `scripts/feature_lifecycle/apply_branch_protection.sh`, and `scripts/page_tree.py`.

So this change is a **full migration**, not a propagation of an already-finished one.

Stakeholders: lifecycle skill maintainers, security reviewers gating eWise deployments, feature owners who fill the manifest `security` block.

## Goals / Non-Goals

**Goals:**
- Single GitHub-native SCA story across schema, workflow, Dependabot config, skills, rules, docs, and scripts.
- `security-gate-triage` describes a Dependabot-only fix/mute workflow with Git traceability.
- `feature-lifecycle-bootstrap` no longer offers a CodeGuard template; it templates `security-gate.yml.tpl` + `dependabot.yml.tpl` + `security-gate.mdc.tpl`.
- `codeguard-fix-or-mute` is deprecated (banner + retained history), not deleted.
- Validators `validate_feature_manifests.py` and `check_feature_gate.py` keep passing after the schema change and manifest reconciliation.
- Acceptance grep returns only intentionally-archived/deprecated docs.

**Non-Goals:**
- Rewriting historical scan records under `docs/codeguard/` (kept archived/read-only).
- Changing the non-SCA security-gate scanners (gitleaks/bandit/eslint) beyond wording; this change does not re-architect secret scanning.
- Enabling Dependabot at the GitHub org/account level (an admin action outside the repo); the change ships config + docs only.
- Weakening the blocking posture: high/critical stays blocking.

## Decisions

**D1 — Treat the originating "canonical reference" as the target spec, and migrate the lagging files too.** The request named several files as already-migrated sources of truth. They are not. Rather than fail the acceptance criteria (which require a clean grep and a Dependabot-only triage), we bring `.cursor/rules/security-gate.mdc`, the `security-gate.yml` fail-step message, and the manifest schema to the described end-state. Alternative (only edit the 4 named skills) was rejected: it would leave the grep dirty and the schema still demanding `codeguard_scan_id`.

**D2 — Schema migration shape.** Replace required `codeguard_scan_id` / `codeguard_scan_url` with `sca_tool` (string enum-ish, default `"dependabot"`) and `dependabot_alerts_url` (nullable URI). Keep `cve_findings`, `secret_scan`, `muted_findings`, `threat_model_url`, `owner_security`. This is a **breaking** schema change, so existing `features/*.json` manifests must be reconciled in the same change to keep `validate_feature_manifests.py` green. Alternative (additive: keep codeguard fields optional) rejected — it leaves CodeGuard vocabulary in every new manifest and fails the grep.

**D3 — Mute = Dependabot alert dismissal recorded in the manifest.** A mute is a real Dependabot alert dismissal (with a dismiss reason) plus a `security.muted_findings[]` entry carrying `id`, `severity`, `justification_url`, `expires_at`. The `justification_url` MUST point to a real dismissal/justification (e.g. the alert URL or a tracked decision), never a fabricated link. Secrets are never muted.

**D4 — Dependabot config scope.** `.github/dependabot.yml` covers the ecosystems actually present in the repo (`pip` for `requirements*.txt`, `npm` for the JS packages, `github-actions`). The bootstrap `dependabot.yml.tpl` is a generic starter the bootstrap skill tailors per detected stack.

**D5 — Deprecation over deletion for `codeguard-fix-or-mute`.** Add a top banner marking it retired and redirecting to `security-gate-triage` + Dependabot; keep the file and its `reference.md`/`examples.md` for history. Alternative (delete) rejected: the request explicitly says do not delete history.

**D6 — Archive, don't rewrite, `docs/codeguard/`.** Past scan pages are records; leave them. The acceptance grep is expected to still match them, which is acceptable ("intentionally-archived"). `page_tree.py` may keep pointing at them under an "Archived" label.

## Risks / Trade-offs

- **[Breaking schema change orphans existing manifests]** → Reconcile all `features/*.json` in the same change and run `validate_feature_manifests.py` before finishing.
- **[Dependency-review-action is PR-only and needs the GitHub Dependency Graph]** → Document it as PR-scoped/blocking-high; do not rely on it for push/scheduled runs. Keep `pip-audit`/`npm audit` as the always-on blocking layer.
- **[Dependabot alerts require repo/org enablement]** → Treated as a documented admin prerequisite (Non-Goal to toggle it); the gate's blocking guardrail is enforced via triage policy + manifest, not by assuming alerts are on.
- **[Grep acceptance ambiguity]** → Define "intentionally-archived/deprecated" precisely: `docs/codeguard/**` history pages and the deprecation banner in `codeguard-fix-or-mute`. Everything else must be clean.
- **[Wording drift between EN skills and FR docs]** → Lifecycle skill/doc *content we author* is English per workspace convention; pre-existing FR doc bodies are updated in place (terms only), not translated wholesale.

## Migration Plan

1. Schema + manifests (D2): edit schema, reconcile `features/*.json`, run `validate_feature_manifests.py`.
2. Workflow + Dependabot (D4): add `.github/dependabot.yml`, fix `security-gate.yml` fail-step wording (optionally add dependency-review for PRs).
3. Rule: rewrite `.cursor/rules/security-gate.mdc` (GitHub-native, drop `docs/codeguard` glob → keep archived note).
4. Skills: rewrite `security-gate-triage`, update `feature-lifecycle-bootstrap` (+ add `dependabot.yml.tpl`, delete `codeguard-pr.yml.tpl`, fix template `security-gate.mdc.tpl`/schema copy), deprecate `codeguard-fix-or-mute`.
5. Sweep docs/scripts/README/AGENTS for residual terms.
6. Run both validators; run the acceptance grep.

Rollback: the change is doc/config-only and lives on a branch; revert the commit to restore CodeGuard wiring. No runtime data migration.

## Open Questions

- Should `security-gate.yml` additionally adopt `actions/dependency-review-action` now (the request's canonical description includes it), or keep the existing gitleaks/pip-audit/npm-audit stack and only fix wording? Default decision: add `dependency-review-action` for PRs as a blocking-high step, since it matches the stated target and is low-risk.
- Exact `sca_tool` value set — `"dependabot"` only, or an open string allowing future tools? Default: open string with documented default `"dependabot"`.
