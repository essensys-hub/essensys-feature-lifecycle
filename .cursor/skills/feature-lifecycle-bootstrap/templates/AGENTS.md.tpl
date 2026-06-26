# Agent Context — Feature Lifecycle

This repository uses a Git-first feature lifecycle:

- `features/<id>.json` is the source of truth
- OpenSpec, docs, tests, security, and release notes link back to the manifest
- `feature-gate` and `security-gate` run automatically on PRs

## Install the skills

```bash
git clone https://github.com/essensys-hub/essensys-feature-lifecycle.git
cd essensys-feature-lifecycle
./scripts/install-skills.sh --global   # or: ./scripts/install-skills.sh /path/to/this-repo
```

## Recommended prompts

```text
bootstrap feature lifecycle
new feature SCRUM-123
sync user guide for this feature
generate e2e tests for this feature
triage security findings
```
