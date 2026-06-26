---
name: security-gate-triage
description: Triage findings emitted by the local security gate, Trivy, and GitHub Dependabot. Use when a PR is blocked by secrets, CVEs, Trivy, dependency-review, pip-audit, npm audit, or a Dependabot alert, and the user needs a safe fix-or-mute workflow with Git traceability.
---

# Security Gate Triage

This skill orchestrates the first response to a blocked PR. Software Composition Analysis (SCA) is **open source**: **Trivy** (CVE deps + Docker/IaC) plus GitHub-native Dependabot alerts, run by the `security-gate` workflow. Secret scanning is **gitleaks**. No proprietary scanner (no CodeGuard/Checkmarx); GitGuardian is only an optional secrets dashboard.

## Use this skill when

- The user says `triage security findings`
- A PR is blocked by `security-gate`
- The user mentions a leaked secret, a CVE, a Dependabot alert, or a mute request

## Workflow

```text
Security gate triage:
- [ ] Step 1 - Read the latest security-gate artifacts and the repo Dependabot alerts
- [ ] Step 2 - Classify each finding (true positive, false positive, accepted risk)
- [ ] Step 3 - Fix secrets and Critical/High findings first
- [ ] Step 4 - For accepted risk, dismiss the Dependabot alert with a reason
- [ ] Step 5 - Update the feature manifest security section
```

## Inputs

Primary sources:

- `.artifacts/security-gate/*.json` (gitleaks, **trivy.json**, dependency-review, pip-audit, npm audit, bandit, eslint-security)
- GitHub Actions artifacts from the `security-gate` workflow
- Repository Dependabot alerts:
  - `gh api repos/{owner}/{repo}/dependabot/alerts` (filter with `--jq` on `state`, `security_vulnerability.severity`)
  - or the GitHub **Security → Dependabot alerts** tab

## Decision policy

- **Secrets**: never mute, never defer. Scrub Git history and rotate the secret.
- **Critical / High CVEs**: fix first, or temporarily mute with documented justification and expiry.
- **pip-audit / npm audit / dependency-review**: confirm the alert is real, then fix per the policy below.

### Fix policy

- **Direct dependency**: bump to at least the Dependabot `first_patched_version` and update the lockfile, keeping the dependency pinned.
- **Transitive dependency** (no direct upgrade path): pin a safe version via npm `overrides` (Node) or a pip constraint (Python).

### Mute policy

- A "mute" is a **Dependabot alert dismissal** (or a documented **Trivy `.trivyignore`** entry with the CVE id) with a reason (e.g. `tolerable_risk`, `no_bandwidth`, `inaccurate`), recorded in the feature manifest `security.muted_findings[]` with `id`, `severity`, `justification_url`, and `expires_at`.
- The `justification_url` MUST point to the real dismissal/justification (the alert URL or a tracked decision). Never fabricate it.
- Secrets are never muted.

## Guardrails

- Never fabricate a justification URL.
- Every mute points to a real Dependabot alert dismissal or a documented `.trivyignore` entry.
- Never deploy (local or OVH) while open High or Critical CVEs (Trivy / Dependabot) exist.
- Update `features/<id>.json -> security` only after reading the latest findings.
- Do not commit automatically; always leave a reviewable diff.
