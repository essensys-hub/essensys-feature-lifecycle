# Essensys - Dry-Run Installation Procedure - feature-lifecycle profile - github

> **MODE: DRY-RUN** — Preparatory rehearsal only. Repeatable. Generates **no deviation** and **no controlled record**.

## Purpose

The objective of this procedure is to detail the steps to be followed for
publishing the Essensys feature-lifecycle Cursor profile (skills + rules).

## Author & Approver

| Meaning   | Firstname & Name                       | Project Role         | Approval date        |
|-----------|----------------------------------------|----------------------|----------------------|
| Author*   | Essensys                               | Technical author     | See workflow history |
| Approver* | Refer to the Essensys approvers list (1) (2)   | Lead                  | See workflow history |

(1) the latest published version of the Essensys approvers list is applicable for the current document version.

(2) This document lists the names of approvers and backups.

*\*Approvers agree with the content of the document and ensure it will be
applicable within their domain of expertise.*

## Version History

| Version                                            | Approval Date        | Modification        |
|----------------------------------------------------|----------------------|---------------------|
| V1 (See Workflow history for Confluence version)   | See Workflow history | Document creation   |

## Distribution List

| Firstname & Name        | Rationale   |
|-------------------------|-------------|
| Technical team members  | Information |

## Glossary

Please refer to the Essensys glossary (`essensys-memory/wiki/`).

## Document Control

| Field | Value |
|---|---|
| Execution mode | **DRY-RUN** (preparatory — no deviation) |
| Paired Installation Procedure | `doc_install/Essensys - Installation Procedure - feature-lifecycle profile - github.md` (**MISSING** — create via `gxp-install-procedure` before controlled install) |
| Dry-run run ID | Record from GitHub Actions after execution |
| Git repository | `essensys-hub/essensys-feature-lifecycle` |
| Git branch | `main` or feature branch under test |
| Git commit SHA | Record at rehearsal time |
| Operator | GitHub user triggering `workflow_dispatch` |
| Timestamp (UTC) | Record at rehearsal time |
| Automation command | `gh workflow run "Publish wise-feature-lifecycle" --ref <branch> -f environment=int -f version=1.1.0 -f dry_run=true` |

## Introduction

This Dry-Run Installation Procedure documents a **preparatory rehearsal** of
publishing the **wise-feature-lifecycle** Cursor profile (skills + rules) to the
Skills Portal API across INT, UAT, or PROD.

- **Preparatory only**: may be executed unlimited times with `dry_run: true`.
- **No deviation**: dry-run failures do not open GxP deviations (`gxp-exec` rule).
- **No mutation**: when `dry_run` is `true`, the publish script prints `[dry-run] would ...` and performs **no** Skills Portal API writes.
- **GxP install** (pre-requisites verification, then real publish with `dry_run: false`) follows only after successful labelled dry-runs per target environment.

The source pipeline is `.github/workflows/publish-wise-feature-lifecycle.yml`.
The publish script is `scripts/feature_lifecycle/publish_wise_feature_lifecycle_profile.py`.

## Prerequisites (read-only verification)

Verify the following **before** starting the dry-run. Do **not** execute a real publish.

| # | Check | How to verify | Expected result |
|---|-------|---------------|-----------------|
| 1 | Repository access | `git remote -v` | `git@github.com:essensys-hub/essensys-feature-lifecycle.git` |
| 2 | Workflow file present | `test -f .github/workflows/publish-wise-feature-lifecycle.yml` | File exists |
| 3 | Publish script present | `test -f scripts/feature_lifecycle/publish_wise_feature_lifecycle_profile.py` | File exists |
| 4 | Workflow dispatch permission | GitHub → Actions → Publish wise-feature-lifecycle | `workflow_dispatch` enabled |
| 5 | INT environment | GitHub → Settings → Environments → `int` | Exists; no approval gate |
| 6 | UAT environment | GitHub → Settings → Environments → `uat` | Exists; required reviewers configured |
| 7 | PROD environment | GitHub → Settings → Environments → `prod` | Exists; required reviewers configured |
| 8 | AWS OIDC role trust | Workflow assumes the configured GitHub Actions role | Repo matches the OIDC trust policy whitelist |
| 9 | Secrets Manager secret | Secret id `essensys-feature-lifecycle` | Contains `SKILLS_API_HOST_{INT,UAT,PROD}` and `SKILLS_API_KEY_{INT,UAT,PROD}` |
| 10 | Target branch checked out | Workflow `actions/checkout@v4` on selected ref | Matches `--ref` used in `gh workflow run` |

## Automation Entry Point

| Property | Value |
|---|---|
| Workflow file | `.github/workflows/publish-wise-feature-lifecycle.yml` |
| Workflow name | `Publish wise-feature-lifecycle` |
| Trigger | `workflow_dispatch` only |
| Runner | `ubuntu-latest` |
| Container image | `python:3.11-slim` |
| GitHub Environment | `${{ inputs.environment }}` (`int`, `uat`, or `prod`) |

### Workflow dispatch inputs

| Input | Type | Required | Default | Description |
|---|---|---|---|---|
| `environment` | choice (`int`, `uat`, `prod`) | yes | `int` | Target Skills Portal environment; selects `SKILLS_API_HOST_*` / `SKILLS_API_KEY_*` pair |
| `version` | string | yes | `1.0.0` | Profile and artifact version string passed to publish script |
| `dry_run` | boolean | yes | `true` | When `true`, publish script runs with `--dry-run` (no API writes) |

### Workflow-level environment variables

| Name | Value |
|---|---|
| `AWS_REGION` | `eu-west-1` |
| `CENTRAL_SECRET_ID` | `essensys-feature-lifecycle` |
| `IAM_ROLE` | `arn:aws:iam::<account>:role/<github-actions-role>` |

### Workflow permissions

| Permission | Value |
|---|---|
| `id-token` | `write` (OIDC for AWS) |
| `contents` | `read` |

## Pipeline Mirror (step-by-step)

### Job: `publish`

| Property | Value |
|---|---|
| Runner | `ubuntu-latest` |
| Environment | `${{ inputs.environment }}` |
| Container | `python:3.11-slim` |
| Job-level `if:` | always (none) |

#### Step: `— (removed: corporate root CA setup)`

| Property | Value |
|---|---|
| Action / type | `uses:` composite action |
| Condition `if:` | always |
| `continue-on-error` | false |
| Env vars referenced | none |
| Secrets referenced | none |
| Commands / behaviour | Installs corporate root CA in container for TLS to internal services (optional) |

#### Step: `Install AWS CLI (curl + unzip)`

| Property | Value |
|---|---|
| Action / type | `uses:` composite action |
| Condition `if:` | always |
| `continue-on-error` | false |
| Env vars referenced | none |
| Secrets referenced | none |
| Commands / behaviour | Installs AWS CLI in container |

#### Step: `actions/checkout@v4`

| Property | Value |
|---|---|
| Action / type | `uses:` checkout |
| Condition `if:` | always |
| `continue-on-error` | false |
| Env vars referenced | none |
| Secrets referenced | `GITHUB_TOKEN` (implicit) |
| Commands / behaviour | Checks out workflow ref (branch/tag) into workspace |

#### Step: `Install jq`

| Property | Value |
|---|---|
| Action / type | `run:` shell |
| Condition `if:` | always |
| `continue-on-error` | false |
| Working directory | `/` |
| Env vars referenced | none |
| Secrets referenced | none |
| Commands / behaviour | `apt-get update`; install `jq`; clean apt lists |

#### Step: `Configure AWS credentials`

| Property | Value |
|---|---|
| Action / type | `uses: aws-actions/configure-aws-credentials@v4` |
| Condition `if:` | always |
| `continue-on-error` | false |
| Env vars referenced | `IAM_ROLE`, `AWS_REGION` (workflow `env`) |
| Secrets referenced | OIDC (no static AWS keys) |
| Commands / behaviour | Assumes the configured GitHub Actions role via GitHub OIDC |

#### Step: `Load Skills Portal API credentials`

| Property | Value |
|---|---|
| Action / type | `run:` shell |
| Condition `if:` | always |
| `continue-on-error` | false |
| Env vars referenced | `TARGET_ENV` ← `inputs.environment`, `CENTRAL_SECRET_ID` |
| Secrets referenced | AWS Secrets Manager via assumed role |
| Commands / behaviour | Fetches secret JSON; extracts `SKILLS_API_HOST_<ENV>` and `SKILLS_API_KEY_<ENV>`; masks API key; sets `SKILLS_API_URL`, `SKILLS_API_KEY`, `TARGET_ENV_UPPER` in `GITHUB_ENV`; deletes `/tmp/secret.json` |

#### Step: `Install publication dependencies`

| Property | Value |
|---|---|
| Action / type | `run:` shell |
| Condition `if:` | always |
| `continue-on-error` | false |
| Env vars referenced | none |
| Secrets referenced | none |
| Commands / behaviour | `pip install requests` |

#### Step: `Publish lifecycle artifacts and profile`

| Property | Value |
|---|---|
| Action / type | `run:` shell |
| Condition `if:` | always |
| `continue-on-error` | false |
| Env vars referenced | `SKILLS_API_URL`, `SKILLS_API_KEY` |
| Secrets referenced | `SKILLS_API_KEY` (from prior step, masked) |
| Commands / behaviour | If `inputs.dry_run` is `true`, runs `publish_wise_feature_lifecycle_profile.py` with `--dry-run`; else runs without flag for real API writes |

## Expected Actions

| Step | Expected log pattern | Expected exit code |
|---|---|---|
| setup-root-ca | Action completes without TLS errors | 0 |
| install-aws-cli | `aws` available in PATH | 0 |
| checkout | Repository files present including `scripts/feature_lifecycle/` | 0 |
| Install jq | `jq --version` succeeds | 0 |
| Configure AWS credentials | OIDC assume-role success | 0 |
| Load Skills Portal API credentials | `Resolved target: <ENV> -> https://<host> (key length N)` — no secret values in log | 0 |
| Install publication dependencies | `Successfully installed requests` | 0 |
| Publish lifecycle artifacts and profile (`dry_run=true`) | Multiple lines `[dry-run] would publish skill <name>` and `[dry-run] would publish rule <name>`; `[dry-run] would patch profile 2: ...`; `[dry-run] would create profile version: ...`; `[dry-run] would publish profile wise-feature-lifecycle version <version>` | 0 |
| Publish lifecycle artifacts and profile (`dry_run=false`) | `[ok]` / HTTP success lines; **no** `[dry-run] would` prefix | 0 |

### Publish script dry-run lines (representative)

When `dry_run: true`, `publish_wise_feature_lifecycle_profile.py` emits lines such as:

- `[dry-run] would publish skill feature-manifest-orchestrator`
- `[dry-run] would publish rule gxp-exec`
- `[dry-run] would publish skill dry-run-install-procedure`
- `[dry-run] would publish rule dry-run-install-doc`
- `[dry-run] would create profile version: {"version": "<version>", ...}` (24 local items + 2 external)
- `[dry-run] would publish profile wise-feature-lifecycle version <version>`

## Expected Outputs and Artifacts

| Artifact / output | Path or location | Dry-run labelled? | Retention |
|---|---|---|---|
| GitHub Actions run log | `https://github.com/essensys-hub/essensys-feature-lifecycle/actions/runs/<RUN_ID>` | Yes (document header + `dry_run` input) | GitHub retention policy |
| Console: resolved API host | Step log line `Resolved target: ...` | Yes | In run log only |
| Skills Portal profile state | INT/UAT/PROD API | **Unchanged** when `dry_run=true` | N/A for dry-run |
| Skills Portal artefact versions | INT/UAT/PROD API | **Unchanged** when `dry_run=true` | N/A for dry-run |
| Local `/tmp/secret.json` | Ephemeral in runner | Deleted in credential step | Job lifetime |

## Mutation Guard

| System / dataset / environment | Why protected | How dry-run enforces |
|---|---|---|
| Skills Portal profile `wise-feature-lifecycle` | Production team profile | `--dry-run` skips `POST`/`PATCH` to profile API |
| Skills Portal skill/rule artefact versions | Published Cursor assets | `--dry-run` skips artefact upload endpoints |
| Skills Portal profile version records | Versioned install state | `--dry-run` skips profile version creation |
| AWS Secrets Manager secret | Credential store | Read-only fetch; no write API called |
| Git repository | Source of truth | Checkout only; workflow does not push |

## Operator Verification Checklist

After the dry-run completes, verify:

1. GitHub Actions run status is **success** (green).
2. Workflow input `dry_run` was **`true`** in the run summary.
3. Log contains `[dry-run] would publish` for every expected skill and rule (currently 14 skills + 7 rules local).
4. Log contains `[dry-run] would publish profile wise-feature-lifecycle version <version>`.
5. Log contains **no** unmasked `SKILLS_API_KEY` value (only `::add-mask::` behaviour).
6. Skills Portal UI for target environment shows **no new** profile version matching the rehearsal (INT/UAT/PROD spot-check).
7. Record run URL in rehearsal ticket.
8. Repeat dry-run for each target environment (`int`, then `uat`, then `prod`) before real publish; UAT/PROD dry-runs may still pause on environment protection if misconfigured — document outcome.

## Traceability and Evidence

Attach to the **rehearsal ticket** (not GxP deployment evidence):

- GitHub Actions run URL.
- Screenshot of workflow inputs showing `dry_run: true`.
- Log excerpt with `[dry-run] would publish profile ...` line.
- Git branch and commit SHA used (`--ref`).
- This document path and commit: `doc_install/dry_run/Essensys - Dry-Run Installation Procedure - feature-lifecycle profile - github.md`.

**Not** valid as GxP deployment sign-off — use the paired GxP Installation Procedure and controlled pre-requisites / run-install phases.

## Sync with GxP Installation Procedure

Update this dry-run document **in the same PR** when any of the following change:

- [ ] `.github/workflows/publish-wise-feature-lifecycle.yml` (inputs, jobs, steps, env, IAM role, secret id)
- [ ] `scripts/feature_lifecycle/publish_wise_feature_lifecycle_profile.py` (`LOCAL_ARTIFACTS` list, dry-run log format)
- [ ] Paired GxP Installation Procedure (when created under `doc_install/`)
- [ ] Skills Portal environment names or approval gates (INT/UAT/PROD)
- [ ] README profile artefact counts (skills/rules)

Run structural validation after edits:

```bash
DOC="doc_install/dry_run/Essensys - Dry-Run Installation Procedure - feature-lifecycle profile - github.md"

rg -n '^## (Purpose|Author & Approver|Version History|Distribution List|Glossary|Document Control|Introduction|Prerequisites \(read-only verification\)|Automation Entry Point|Pipeline Mirror \(step-by-step\)|Expected Actions|Expected Outputs and Artifacts|Mutation Guard|Operator Verification Checklist|Traceability and Evidence|Sync with GxP Installation Procedure)$' \
  "$DOC" | wc -l
# Expected: 16

rg -n 'MODE: DRY-RUN' "$DOC"
```
