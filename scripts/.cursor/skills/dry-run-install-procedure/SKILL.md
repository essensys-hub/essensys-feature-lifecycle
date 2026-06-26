---
name: dry-run-install-procedure
description: Writes ultra-detailed dry-run Installation Procedure documents paired with eWise GxP Installation Procedures. Preparatory rehearsal only — repeatable, MODE DRY-RUN labelled, no deviation. Use when the user asks for dry-run install documentation, dry-run execution procedure, preparatory install runbook, workflow rehearsal with dry_run true or --dry-run, or updating doc_install/dry_run paired with gxp-install-procedure.
---

# Dry-Run Installation Procedure

Produces the **paired preparatory document** for an eWise component install pipeline. Complements the global `gxp-install-procedure` skill (concise GxP Confluence install doc) and the project `gxp-exec` rule (dry-run vs controlled phases).

## When to use

- User asks to document a **dry-run** / **rehearsal** of an install or publish pipeline.
- A GxP Installation Procedure exists (or is being created) and needs a **maximum-detail** dry-run counterpart.
- User mentions `dry_run: true`, `--dry-run`, preparatory install, or `doc_install/dry_run/`.

## Output rules

- **Language**: English only.
- **Tone**: imperative, action-oriented, **exhaustive operational detail** (opposite of `gxp-install-procedure` brevity).
- **Length**: no upper limit — include every workflow input, job, step, expected log line, artifact path, and mutation guard row.
- **Format**: GitHub-Flavored Markdown under `doc_install/dry_run/`.
- **Banner**: every document MUST start with `> **MODE: DRY-RUN**`.
- **No invented data**: use `MISSING` for unknown URLs, SHAs, or tag values.
- **No full workflow YAML listings** — mirror steps in tables (reference filename only).

## Output path

```
doc_install/dry_run/eWise - Dry-Run Installation Procedure - <Component name> - github.md
```

Paired GxP document (created by `gxp-install-procedure`):

```
doc_install/eWise - Installation Procedure - <Component name> - github.md
```

## Comparison with gxp-install-procedure

| Aspect | `gxp-install-procedure` | `dry-run-install-procedure` |
|---|---|---|
| Purpose | GxP Confluence install doc | Preparatory rehearsal — **no deviation** |
| Length | 60–120 lines | Ultra-precise, unbounded |
| Sections | 9 frozen GxP sections | Sections 1–5 GxP verbatim + 11 dry-run sections |
| Confluence | Default publish target | Git only unless user requests Confluence |

## Required sections (frozen order)

Sections **1–5** match `gxp-install-procedure` verbatim (`Purpose` through `Glossary`).

Then, in order:

1. `Document Control` — `MODE: DRY-RUN`, paired GxP path, run ID, Git ref, operator, UTC timestamp, automation command.
2. `Introduction` — preparatory only, repeatable, no deviation (`gxp-exec`).
3. `Prerequisites (read-only verification)` — table: check / how to verify / expected result.
4. `Automation Entry Point` — workflow file, trigger, runner, full `workflow_dispatch` inputs table.
5. `Pipeline Mirror (step-by-step)` — every job and step from the source workflow.
6. `Expected Actions` — per-step dry-run log pattern and exit code.
7. `Expected Outputs and Artifacts` — paths, retention, dry-run label flag.
8. `Mutation Guard` — systems that must not change during dry-run.
9. `Operator Verification Checklist` — numbered post-run checks.
10. `Traceability and Evidence` — rehearsal ticket attachments (not GxP deployment evidence).
11. `Sync with GxP Installation Procedure` — diff checklist for keeping docs aligned.

Use [template.md](template.md) as the scaffold.

## Workflow

```text
Dry-run install procedure:
- [ ] Step 1 - Locate paired GxP Installation Procedure (or run gxp-install-procedure first)
- [ ] Step 2 - Read source pipeline (.github/workflows/<name>.yml) — every job and step
- [ ] Step 3 - Copy template.md to doc_install/dry_run/...
- [ ] Step 4 - Fill all sections; mark gaps as MISSING
- [ ] Step 5 - Validate structure and MODE: DRY-RUN banner
- [ ] Step 6 - (Optional) Publish to Confluence only if user explicitly requests
```

1. **Pairing** — open `doc_install/eWise - Installation Procedure - <Component> - github.md`. If missing, run `gxp-install-procedure` or ask the user before proceeding.
2. **Pipeline mirror** — read the workflow referenced in the GxP doc; document every job, step, `if:`, `continue-on-error`, env/secret **names** (never values).
3. **Dry-run automation** — record the exact command or workflow dispatch with `dry_run: true` / `--dry-run`.
4. **Expected actions** — for publish-style scripts, expect `[dry-run] would ...` log lines (see `.github/workflows/publish-wise-feature-lifecycle.yml`).
5. **Validate**:

```bash
COMPONENT="<Component name>"
DOC="doc_install/dry_run/eWise - Dry-Run Installation Procedure - ${COMPONENT} - github.md"

rg -n '^## (Purpose|Author & Approver|Version History|Distribution List|Glossary|Document Control|Introduction|Prerequisites \(read-only verification\)|Automation Entry Point|Pipeline Mirror \(step-by-step\)|Expected Actions|Expected Outputs and Artifacts|Mutation Guard|Operator Verification Checklist|Traceability and Evidence|Sync with GxP Installation Procedure)$' \
  "$DOC" | wc -l
# Expected: 16

rg -n 'MODE: DRY-RUN' "$DOC"
```

## Reference implementation in this repo

- Workflow: `.github/workflows/publish-wise-feature-lifecycle.yml` (`dry_run` input, default `true`).
- Seed doc: `doc_install/dry_run/eWise - Dry-Run Installation Procedure - wise-feature-lifecycle profile - github.md`.

## Anti-patterns

- Omitting `MODE: DRY-RUN` banner or dry-run log expectations.
- Treating dry-run failure as a GxP deviation (deviations apply to pre-requisites and run/install only).
- Shortening step detail below the source workflow (new workflow step → new doc row).
- Inventing tag patterns, URLs, or secret values.
- Copying full workflow YAML into the document.

## Related skills and rules

- `gxp-install-procedure` — creates the paired GxP Installation Procedure.
- `gxp-exec` — phase discipline (dry-run vs pre-requisites vs run/install).
- `dry-run-install-doc` — rule enforcing paired doc maintenance.
