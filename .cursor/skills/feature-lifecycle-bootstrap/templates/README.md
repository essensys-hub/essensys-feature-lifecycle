# Feature lifecycle bootstrap templates

These files are the starter set copied by `feature-lifecycle-bootstrap`.

## Goal

Install the smallest useful lifecycle stack in another repository:

- manifest schema
- PR workflows
- local Git hook
- AI rules
- starter docs
- agent context

## Files

- `features/schema/feature.schema.json`
- `.github/workflows/feature-gate.yml.tpl`
- `.github/workflows/security-gate.yml.tpl`
- `.github/workflows/dependabot.yml.tpl` (installed as `.github/dependabot.yml`)
- `scripts/hooks/pre-commit.tpl`
- `.cursor/rules/feature-gate.mdc.tpl`
- `.cursor/rules/security-gate.mdc.tpl`
- `AGENTS.md.tpl`
- `docs/features/README.md.tpl`

The bootstrap skill should adapt paths and commands to the detected stack before writing them.
