---
name: feature-lifecycle-bootstrap
description: Initialize or upgrade the feature lifecycle workflow in a repository. Use when the user asks to bootstrap a new project, add the lifecycle to an existing repo, install the Essensys feature-lifecycle stack, or remove ambiguity about which files and workflows must be created first.
---

# Feature Lifecycle Bootstrap

Install the lifecycle safely in a repo that may already contain code, docs, or CI.

## Modes

- `empty-project`: new repository, install the full starter set
- `existing-project`: detect what already exists, propose only the missing pieces

## Workflow

```text
Bootstrap feature lifecycle:
- [ ] Step 1 - Detect stack and current repo shape
- [ ] Step 2 - Show an install plan to the user
- [ ] Step 3 - Copy only the selected templates
- [ ] Step 4 - Validate manifests, hooks, and workflows
- [ ] Step 5 - Return the first three recommended prompts
```

## Detection checklist

Detect in parallel:

- `package.json` -> React / Node
- `requirements.txt` or `api/requirements-api.txt` -> Python
- `playwright.config.*` -> Playwright already present
- `openspec/` -> OpenSpec already present
- `features/` -> lifecycle already initialized
- `.github/dependabot.yml` -> GitHub-native SCA (Dependabot) already configured
- `.cursor/skills/` and `.cursor/rules/` -> project-specific AI assets already present
- `*.sas`, `*.R`, `*.Rmd` -> clinical SAS / R variants

## Templates

Copy from:

`/.cursor/skills/feature-lifecycle-bootstrap/templates/`

Key templates include:

- `features/schema/feature.schema.json`
- `.github/workflows/feature-gate.yml.tpl`
- `.github/workflows/security-gate.yml.tpl`
- `.github/workflows/dependabot.yml.tpl`
- `scripts/hooks/pre-commit.tpl`
- `.cursor/rules/feature-gate.mdc.tpl`
- `.cursor/rules/security-gate.mdc.tpl`
- `AGENTS.md.tpl`

The security stack is GitHub-native SCA (Dependabot): `security-gate.yml.tpl` +
`dependabot.yml.tpl` (installed as `.github/dependabot.yml`) + `security-gate.mdc.tpl`.

## Guardrails

- Interactive mode is mandatory for existing repositories.
- Never overwrite an existing file silently.
- If a file already exists, show a diff or create a migration note instead.
- Keep changes inside the known lifecycle paths only:
  - `features/`
  - `.github/workflows/`
  - `scripts/hooks/`
  - `.cursor/`
  - `docs/features/`
  - `docs/feature-lifecycle/`
  - `AGENTS.md`

## Post-install checks

Run after templating:

```bash
python3 scripts/feature_lifecycle/validate_feature_manifests.py
python3 scripts/feature_lifecycle/check_feature_gate.py
```

Then suggest these prompts:

1. `new feature SCRUM-123`
2. `sync user guide for this feature`
3. `generate e2e tests for this feature`
