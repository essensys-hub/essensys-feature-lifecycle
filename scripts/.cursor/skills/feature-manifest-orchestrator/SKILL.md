---
name: feature-manifest-orchestrator
description: Create or update `features/<id>.json` as the Git source of truth for a feature lifecycle. Use when the user asks to start a new feature from Jira, create a feature manifest, link an OpenSpec change to Jira, or migrate an existing feature into the lifecycle workflow.
---

# Feature Manifest Orchestrator

Create or update the feature manifest that anchors the lifecycle:

- Jira
- OpenSpec
- implementation paths
- docs
- tests
- Confluence
- security

The manifest format is defined by `features/schema/feature.schema.json`.

## Use this skill when

- The user says `new feature WPMTC-1234`
- The user asks to create `features/<id>.json`
- The user wants to migrate an existing OpenSpec change into the lifecycle
- A feature exists in code/docs/tests but has no manifest yet

## Workflow

Track progress with this checklist:

```text
Feature manifest orchestration:
- [ ] Step 1 - Resolve the feature id and branch name
- [ ] Step 2 - Read Jira context or fall back to TBD
- [ ] Step 3 - Read the OpenSpec change (or create it if asked)
- [ ] Step 4 - Map implementation, docs, tests, release paths
- [ ] Step 5 - Write or update features/<id>.json
- [ ] Step 6 - Validate with scripts/feature_lifecycle/validate_feature_manifests.py
- [ ] Step 7 - Summarize the remaining fields for a human to complete
```

## Step 1 - Resolve the feature id

- Reuse the OpenSpec change id when it exists, for example `add-files-viewer-tab`.
- Otherwise derive a kebab-case id from the Jira title or from the user request.
- Default branch name: `feat/<id>`.

## Step 2 - Read Jira context

- If the user gave a Jira key, invoke `jira-xray-test-campaign` first.
- Extract the ticket title and test plan if available.
- If Jira is not reachable, keep `jira.issue` with the provided key and set unknown fields to `null` or `TBD`.
- Never invent Jira content.

## Step 3 - Read the OpenSpec change

- If `openspec/changes/<id>/` already exists, read:
  - `.openspec.yaml`
  - `proposal.md`
  - `design.md`
  - `tasks.md`
  - `specs/**/spec.md`
- If the user explicitly asked to start a brand-new feature and no change exists, invoke `openspec-propose` first.

## Step 4 - Map repository evidence

Read the repository and collect:

- `implementation.paths`: code and test files that materially implement the feature
- `userguide.pages`: user-facing documentation pages
- `tests.playwright` / `tests.pytest` / `tests.testthat`: whichever applies
- `tests.coverage_must_test`: 3-6 concrete acceptance statements
- `release.paths`: changelog files that should mention the feature

Preferred evidence order:

1. OpenSpec `Impact` / `Capabilities`
2. `docs/features/*.md`
3. Test headers with `Spec ref:`
4. Changed code under `wise-skills-react/`, `api/`, `services/`, `cli/`, `go/`

## Step 5 - Write the manifest

- File path: `features/<id>.json`
- Always include the schema pointer:

```json
"$schema": "./schema/feature.schema.json"
```

- Use the schema as the only contract.
- Keep placeholders explicit:
  - `jira.issue: "TBD"` only when truly unknown
  - `pr_url: null`
  - `draft_page_id: null`
  - `published_page_id: null`

## Step 6 - Validate

Run:

```bash
python3 scripts/feature_lifecycle/validate_feature_manifests.py "features/<id>.json"
```

If validation fails, fix the manifest before returning.

## Step 7 - Human follow-up summary

Return a short summary with:

- the manifest path
- the resolved feature id
- the missing human-owned fields, such as:
  - Jira key or test plan
  - Confluence page ids
  - release tag
  - security mute justifications

## Guardrails

- Never create a manifest without validating it.
- Never invent files that do not exist in the repository.
- Never overwrite an existing manifest blindly; merge with current content.
- Prefer `null` or `TBD` over fabricated values.
- Keep `coverage_must_test` concrete and verifiable by real test titles.
