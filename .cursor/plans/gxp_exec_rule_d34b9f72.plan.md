---
name: gxp exec rule
overview: Add a new project rule `gxp-exec` codifying the GxP execution discipline (mandatory documented + automated dry-run; pre-requisites and run/install are GxP-controlled and generate deviations; dry-runs are preparatory, repeatable, and never generate deviations), and register it in the Skills Portal profile (publish script + README).
todos:
  - id: create-rule
    content: Create .cursor/rules/gxp-exec.mdc with frontmatter + GxP execution phases (dry-run vs pre-requisites/run-install, deviations policy)
    status: completed
  - id: register-publish
    content: Add gxp-exec ArtifactSpec (rule) after security-gate in publish_wise_feature_lifecycle_profile.py
    status: completed
  - id: update-readme
    content: "Update README counts: 22 artefacts, Rules (6) + new row, live-state items 22 (16 skills, 6 rules)"
    status: completed
  - id: verify
    content: Run manifest validator and a dry-run publish to confirm gxp-exec is registered and ordered
    status: completed
isProject: false
---

## GxP Execution Rule

Add a new rule `gxp-exec` and publish it as part of the `wise-feature-lifecycle` profile. Content in English (matches `security-gate.mdc`).

Recommended execution: a dedicated branch + PR (e.g. `feat/gxp-exec-rule`) to keep it separate from the in-flight Dependabot PR #2.

### 1. Create the rule file

New file `.cursor/rules/gxp-exec.mdc`, same frontmatter convention as [.cursor/rules/security-gate.mdc](.cursor/rules/security-gate.mdc):

- `description`: GxP execution discipline; mandatory documented + automated dry-run before any GxP run; pre-requisites and run/install are GxP-controlled (deviations apply); dry-runs preparatory, repeatable, never generate deviations when clearly labelled.
- `globs`: install/run/deploy scripts, `.github/workflows/**/*.y*ml`, `scripts/**/*.py`, runbook docs.
- `alwaysApply: false`.

Body sections:
- Phase table: Dry-run (not GxP, repeatable, never a deviation) vs Pre-requisites and Run/Install (GxP, controlled, deviations apply).
- Dry-run: mandatory before any GxP run, documented + automated (a `--dry-run`/`dry_run: true` flag, not manual), every artifact labelled `dry-run` (e.g. `[dry-run] would ...`), no mutation, no GxP record, no deviation.
- Pre-requisites (GxP): controlled; any anomaly opens a deviation with traceability.
- Run / Install (GxP): only after a successful labelled dry-run; any failure opens a deviation; record version/env/operator/evidence.
- Deviations: raised only by GxP phases, never by dry-runs; each fully traceable.
- Evidence: Git as source of truth; reference `gxp-unit-test-report-generator` for the CFR 21 Part 11 report format.

Anchor in the repo today: the publish workflow already exposes a `dry_run` input and emits `[dry-run] would ...`:

```42:46:.github/workflows/publish-wise-feature-lifecycle.yml
      dry_run:
        description: "Do not publish, only print actions"
        required: true
        default: true
        type: boolean
```

### 2. Register the rule in the publish profile

In [scripts/feature_lifecycle/publish_wise_feature_lifecycle_profile.py](scripts/feature_lifecycle/publish_wise_feature_lifecycle_profile.py), add an `ArtifactSpec` right after the `security-gate` rule (line 152), before the closing `]`:

```python
    ArtifactSpec(
        name="gxp-exec",
        artifact_type="rule",
        source_path=".cursor/rules/gxp-exec.mdc",
        description="Project rule for GxP execution: documented/automated dry-run, deviations on pre-requisites and run/install.",
    ),
```

The `order` is auto-assigned by enumeration, so `EXTERNAL_PROFILE_ITEMS` (`confluence-page-generator`, `git-secret-cleaner`) shift automatically. No other code change needed.

### 3. Update the README counts

In [README.md](README.md):
- Line 28 heading: `21 artefacts` -> `22 artefacts`.
- Line 51 `### Rules (5)` -> `### Rules (6)`, and add a table row: `| 6 | gxp-exec | GxP execution: dry-run, pre-requisites, run/install, deviations |`.
- Line 203 live-state row: `Items 21 (16 skills, 5 rules)` -> `22 (16 skills, 6 rules)`.

### 4. Verify

- `python3 scripts/feature_lifecycle/validate_feature_manifests.py` (should stay green; unaffected).
- Dry-run publish to confirm the new rule is picked up and ordered:
  `gh workflow run "Publish wise-feature-lifecycle" --ref <branch> -f environment=int -f version=1.1.0 -f dry_run=true`
  Expect `[dry-run] would publish rule gxp-exec` and 24 total profile items (22 local + 2 external).

### Out of scope / not changed
- `AGENTS.md` (statistical-programmer profile context, not the lifecycle rule list).
- No OpenSpec change created for this (standalone rule addition). Can add one on request.
- The frozen version changelog string in the publish script is left as-is unless you want it updated.
