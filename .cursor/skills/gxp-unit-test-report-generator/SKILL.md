---
name: gxp-unit-test-report-generator
description: Generates standardized, audit-ready GxP unit test reports for Clinical Data Science (Python pytest and R testthat), with traceability, data lineage, compliance checks, Git storage metadata, and Confluence publication status. Use when the user asks for a unit test report, audit report, CFR 21 Part 11 evidence, CI/CD test analysis, or test result publication workflow.
---

# GxP Unit Test Report Generator

## Purpose

Produce a deterministic, audit-friendly Markdown report from unit test results with full traceability for:
- code version
- data version (hashes)
- execution context
- storage and publication workflow

Scope: Clinical R&D / Data Science, GxP, CFR 21 Part 11, CI/CD, Python (`pytest`) and R (`testthat`).

## Required Inputs

Collect these before writing the report. If any item is missing, keep the section and mark it explicitly as `MISSING`.

- Test framework and raw outputs (`pytest`, `testthat`, CI logs)
- Git commit SHA and branch
- Version tag (release/build tag)
- Git repository URL
- Report destination path
- Dataset identifiers + hashes (SHA256 preferred)
- Execution context (pipeline ID, runner/image, OS, Python/R versions, timestamp, timezone)
- Previous run reference (if available) for change/flaky analysis
- Confluence target info (space, page title, URL/status)

## Output Contract (strict)

Always generate Markdown with exactly these sections in this order:

1. Metadata
2. Test Summary
3. Coverage
4. Test Details
5. Data Lineage
6. Deviations
7. Compliance Checks
8. Audit Trail
9. Report Storage & Publication

Use unambiguous language. Prefer tables for evidence fields.

## Generation Workflow

Copy this checklist and track completion:

```text
Task Progress:
- [ ] Parse test inputs
- [ ] Validate traceability completeness
- [ ] Compute summary metrics
- [ ] Build failure/deviation details
- [ ] Add compliance checks
- [ ] Add audit trail and publication metadata
- [ ] Run final consistency checks
```

### Step 1: Parse and normalize

- Parse `pytest` and/or `testthat` outputs.
- Normalize to common fields:
  - suite
  - test case
  - status (`PASSED`, `FAILED`, `SKIPPED`, `XFAIL`, `FLAKY_SUSPECTED`)
  - duration
  - expected
  - actual
  - error/stack trace reference

### Step 2: Enforce traceability

- Confirm:
  - commit SHA present
  - data hashes present for all datasets used
  - execution context present
- Missing fields must be:
  - listed in **Deviations**
  - flagged in **Compliance Checks** as `NON_COMPLIANT`

### Step 3: Compute summary and coverage

- Report totals by status and framework.
- Coverage:
  - include measured value and tool source if available.
  - if unavailable, set value to `MISSING` and add compliance flag.

### Step 4: Build test details and failures

- For each non-passing test, include:
  - test ID
  - expected vs actual
  - error evidence
  - suspected cause
  - remediation suggestion
- Also include top unstable tests (flaky candidates):
  - changed outcomes across runs
  - intermittent failures
  - high variance duration

### Step 5: Add data lineage

- For each dataset/artifact:
  - name
  - version
  - SHA256 hash
  - source location
  - retrieval timestamp
- Never omit hashes silently.

### Step 6: Storage and publication

- Git section must include:
  - repository URL
  - report file path
  - commit ID
  - version tag
- Add immutability evidence:
  - unique filename (timestamp/tag/commit suffix)
  - overwrite policy (`no overwrite`)
- Confluence section must include:
  - space name
  - page title
  - page URL
  - publication status (`PUBLISHED`, `PENDING`, `FAILED`)
- Ensure Git/Confluence version consistency (same commit/tag references).

## Report Template

Use this template exactly:

```markdown
# Unit Test Report - <project_or_pipeline_name>

## 1. Metadata
| Field | Value |
|---|---|
| Report ID | <unique-id> |
| Generated At (UTC) | <timestamp> |
| Framework(s) | <pytest/testthat> |
| Environment | <ci-runner/image/os> |
| Trigger | <push/pr/schedule/manual> |
| Pipeline Run ID | <id> |
| Git Repository URL | <url> |
| Branch | <branch> |
| Commit ID | <sha> |
| Version Tag | <tag or MISSING> |

## 2. Test Summary
| Metric | Value |
|---|---|
| Total Tests | <n> |
| Passed | <n> |
| Failed | <n> |
| Skipped | <n> |
| XFail | <n> |
| Duration (s) | <n> |
| Overall Status | <PASS/FAIL> |

## 3. Coverage
| Scope | Coverage | Tool | Threshold | Status |
|---|---:|---|---:|---|
| Python | <value or MISSING> | <pytest-cov/MISSING> | <threshold> | <OK/WARN/FAIL> |
| R | <value or MISSING> | <covr/MISSING> | <threshold> | <OK/WARN/FAIL> |

## 4. Test Details
### 4.1 Failed Tests
| Test ID | Framework | Expected | Actual | Evidence | Suggested Fix |
|---|---|---|---|---|---|
| <id> | <pytest/testthat> | <expected> | <actual> | <log/link> | <action> |

### 4.2 Flaky Test Suspects
| Test ID | Signal | Current Run | Previous Runs | Recommendation |
|---|---|---|---|---|
| <id> | <intermittent/high variance> | <status> | <summary/MISSING> | <action> |

## 5. Data Lineage
| Dataset/Artifact | Version | SHA256 | Source | Retrieved At (UTC) |
|---|---|---|---|---|
| <name> | <version> | <hash or MISSING> | <location> | <timestamp> |

## 6. Deviations
| ID | Type | Description | Impact | CAPA/Owner | Due Date | Status |
|---|---|---|---|---|---|---|
| <dev-id> | <traceability/data/test> | <description> | <impact> | <owner> | <date> | <open/closed> |

## 7. Compliance Checks
| Check | Requirement | Result | Evidence |
|---|---|---|---|
| Code Traceability | Commit ID + tag present | <COMPLIANT/NON_COMPLIANT> | <evidence> |
| Data Traceability | Hashes for all datasets | <COMPLIANT/NON_COMPLIANT> | <evidence> |
| Expected vs Actual | Recorded for failures | <COMPLIANT/NON_COMPLIANT> | <evidence> |
| Auditability | Execution context captured | <COMPLIANT/NON_COMPLIANT> | <evidence> |
| Publication Consistency | Git and Confluence versions aligned | <COMPLIANT/NON_COMPLIANT> | <evidence> |

## 8. Audit Trail
| Event Time (UTC) | Actor/System | Action | Artifact | Evidence |
|---|---|---|---|---|
| <timestamp> | <ci/user/service> | <executed tests/generated report/committed/published> | <path/url> | <log/hash> |

## 9. Report Storage & Publication
### 9.1 Git Storage
- Repository URL: `<url>`
- Report Path: `<path>`
- Commit ID: `<sha>`
- Version Tag: `<tag>`
- Immutability: `<unique naming + no overwrite policy>`

### 9.2 Confluence Publication
- Space Name: `<space>`
- Page Title: `<title>`
- Page URL: `<url or MISSING>`
- Publication Status: `<PUBLISHED/PENDING/FAILED>`
- Version Consistency Check: `<PASS/FAIL + details>`
```

## Decision Rules

- If any mandatory traceability item is missing, set overall compliance to `NON_COMPLIANT`.
- Never infer missing hashes or metadata.
- Never use ambiguous wording like "likely" for compliance conclusions.
- Keep expected vs actual explicit for each failed test.

## Bonus Analysis Rules

When data is available, append concise recommendations:

- Failing tests:
  - probable root cause class
  - targeted remediation
- Flaky tests:
  - quarantine candidate
  - retry policy recommendation
  - deterministic fixture recommendations
- Coverage:
  - lowest-risk, highest-impact coverage gaps first
- Previous run comparison:
  - delta pass/fail
  - new failures
  - resolved failures

If previous run data is unavailable, state: `Previous run comparison: MISSING`.
