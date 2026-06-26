# eWise - Dry-Run Installation Procedure - <COMPONENT_NAME> - github

> **MODE: DRY-RUN** — Preparatory rehearsal only. Repeatable. Generates **no deviation** and **no GxP record**.

## Purpose

The objective of this procedure is to detail the steps to be followed for
installing one or more infrastructure and application hardware and software
components related to eWise application.

## Author & Approver

| Meaning   | Firstname & Name                       | Project Role         | Approval date        |
|-----------|----------------------------------------|----------------------|----------------------|
| Author*   | <TEAM_NAME>                            | <AUTHOR_ROLE>        | See workflow history |
| Approver* | Refer to [eWise - Approvers](https://<your-org>.atlassian.net/wiki/spaces/WISE/pages/63980109964) (1) (2)   | IPL                  | See workflow history |

(1) the latest published version of [eWise - Approvers](https://<your-org>.atlassian.net/wiki/spaces/WISE/pages/63980109964) is applicable for the current document version.

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

Please refer to the [eWise - Glossary](https://<your-org>.atlassian.net/wiki/spaces/WISE/pages/63825219309) page.

## Document Control

| Field | Value |
|---|---|
| Execution mode | **DRY-RUN** (preparatory — no deviation) |
| Paired GxP Installation Procedure | `doc_install/eWise - Installation Procedure - <COMPONENT_NAME> - github.md` |
| Dry-run run ID | `<GITHUB_RUN_ID or MISSING>` |
| Git repository | `essensys-hub/<REPO>` |
| Git branch | `<BRANCH>` |
| Git commit SHA | `<SHA>` |
| Operator | `<OPERATOR_ID or MISSING>` |
| Timestamp (UTC) | `<ISO-8601>` |
| Automation command | `<e.g. gh workflow run ... -f dry_run=true>` |

## Introduction

This Dry-Run Installation Procedure documents a **preparatory rehearsal** of
the **<COMPONENT_NAME>** install/update pipeline. It mirrors the paired GxP
Installation Procedure but records **maximum operational detail** for operator
rehearsal.

- **Preparatory only**: may be executed unlimited times.
- **No deviation**: dry-run failures do not open GxP deviations (see `gxp-exec` rule).
- **No mutation**: controlled systems must not change when `dry_run` / `--dry-run` is active.
- **GxP install** (pre-requisites, then run/install) follows only after a successful labelled dry-run.

<ONE_TO_THREE_LINES_COMPONENT_SCOPE>

## Prerequisites (read-only verification)

Verify the following **before** starting the dry-run. Do **not** execute GxP install steps here.

| # | Check | How to verify | Expected result |
|---|-------|---------------|-----------------|
| 1 | Access to Git repository | `git remote -v` | `git@github.com:essensys-hub/<REPO>.git` |
| 2 | Workflow file present | `test -f .github/workflows/<WORKFLOW_FILE>` | File exists |
| 3 | Paired GxP procedure exists | `test -f doc_install/eWise\ -\ Installation\ Procedure\ -\ <COMPONENT_NAME>\ -\ github.md` | File exists or `MISSING` documented |
| 4 | Operator can trigger workflow | GitHub Actions → workflow permissions | `workflow_dispatch` allowed |
| 5 | Target environment configured | GitHub → Settings → Environments | `<ENV>` exists with expected protection |
| 6 | <ADDITIONAL_CHECK> | <HOW> | <EXPECTED> |

## Automation Entry Point

| Property | Value |
|---|---|
| Workflow file | `.github/workflows/<WORKFLOW_FILE>` |
| Workflow name | `<WORKFLOW_DISPLAY_NAME>` |
| Trigger | `workflow_dispatch` |
| Runner | `<RUNNER_LABEL>` |
| Container image | `<CONTAINER_IMAGE or N/A>` |
| GitHub Environment | `${{ inputs.environment }}` or `<ENV_BINDING>` |

### Workflow dispatch inputs

| Input | Type | Required | Default | Description |
|---|---|---|---|---|
| `<INPUT_NAME>` | `<choice|string|boolean>` | yes/no | `<DEFAULT>` | `<DESCRIPTION>` |

## Pipeline Mirror (step-by-step)

### Job: `<JOB_ID>`

| Property | Value |
|---|---|
| Runner | `<RUNNER>` |
| Environment | `<ENV or N/A>` |
| Container | `<IMAGE or N/A>` |
| Job-level `if:` | `<CONDITION or always>` |

#### Step: `<STEP_NAME_1>`

| Property | Value |
|---|---|
| Action / type | `<uses: ... or run:` |
| Condition `if:` | `<CONDITION or always>` |
| `continue-on-error` | `<true|false>` |
| Env vars referenced | `<NAMES_ONLY>` |
| Secrets referenced | `<NAMES_ONLY>` |
| Commands / behaviour | `<ONE_LINE_SUMMARY>` |

<!-- Repeat #### Step blocks for EVERY step in the workflow -->

## Expected Actions

For each step above, record the **expected dry-run behaviour** (log pattern and exit code).

| Step | Expected log pattern | Expected exit code |
|---|---|---|
| `<STEP_NAME_1>` | `[dry-run] would <ACTION>` or equivalent | `0` |
| `<STEP_NAME_2>` | `<PATTERN>` | `0` |

## Expected Outputs and Artifacts

| Artifact / output | Path or location | Dry-run labelled? | Retention |
|---|---|---|---|
| Console log | GitHub Actions run log | Yes (`MODE: DRY-RUN` in doc header) | Per GitHub retention |
| `<ARTIFACT_NAME>` | `<PATH>` | Yes | `<N days or N/A>` |

## Mutation Guard

The following **must not change** during a dry-run execution:

| System / dataset / environment | Why protected | How dry-run enforces |
|---|---|---|
| Skills Portal profile versions | Production artefact | `dry_run: true` / `--dry-run` skips API writes |
| `<SYSTEM_2>` | `<REASON>` | `<MECHANISM>` |

## Operator Verification Checklist

After the dry-run completes, verify:

1. GitHub Actions run status is **success** (or document expected soft-fail steps).
2. Log contains dry-run markers (`[dry-run] would ...` or documented equivalent).
3. No mutation guard row was violated (spot-check target environment).
4. Every workflow input used matches this document's Automation Entry Point table.
5. Artifact list matches **Expected Outputs and Artifacts**.
6. Record run URL: `https://github.com/essensys-hub/<REPO>/actions/runs/<RUN_ID>`.

## Traceability and Evidence

Attach to the **rehearsal ticket** (not GxP deployment evidence):

- GitHub Actions run URL (permanent link).
- Screenshot or log excerpt showing `MODE: DRY-RUN` context and dry-run log lines.
- Git commit SHA and branch used for the rehearsal.
- This document version (Git path + commit).

**Not** valid as GxP deployment sign-off — use the paired Installation Procedure and `gxp-exec` controlled phases for that.

## Sync with GxP Installation Procedure

Update this dry-run document **in the same PR** when any of the following change in the paired GxP Installation Procedure or source workflow:

- [ ] Workflow file path or name
- [ ] `workflow_dispatch` inputs (name, type, default, options)
- [ ] Job or step added, removed, or reordered
- [ ] Recognised tag patterns or version format
- [ ] Prerequisites or target environment names
- [ ] Rollback or verification steps

Run structural validation after edits:

```bash
rg -n '^## (Purpose|Author & Approver|Version History|Distribution List|Glossary|Document Control|Introduction|Prerequisites \(read-only verification\)|Automation Entry Point|Pipeline Mirror \(step-by-step\)|Expected Actions|Expected Outputs and Artifacts|Mutation Guard|Operator Verification Checklist|Traceability and Evidence|Sync with GxP Installation Procedure)$' \
  "doc_install/dry_run/eWise - Dry-Run Installation Procedure - <COMPONENT_NAME> - github.md" | wc -l
# Expected: 16

rg -n 'MODE: DRY-RUN' "doc_install/dry_run/eWise - Dry-Run Installation Procedure - <COMPONENT_NAME> - github.md"
```
