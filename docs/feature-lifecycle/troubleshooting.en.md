# Troubleshooting

When a PR is blocked, use the shortest path first.

## My PR is blocked by feature-gate

Read the PR comment, then ask Cursor:

```text
create feature manifest
```

or:

```text
sync user guide for this feature
```

## My PR is blocked by security-gate

In Cursor:

```text
triage security findings
```

Always start with secrets and Critical/High findings. The security gate is blocking by design. It is fully open source: **gitleaks** (secrets), **Trivy** (CVE deps + Docker/IaC) and Dependabot. The Trivy report lives in `.artifacts/security-gate/trivy.json`; to mute an unfixable CVE, add a justified entry to `.trivyignore` and record it in `security.muted_findings[]`.

## A secret leaked

Never mute a secret. Run the history scrub skill, then **rotate** the secret. Store secrets via SOPS / Ansible vault / Secrets Manager — never in clear text.

## The user guide is stale

Documentation sync is not automatic. Run:

```text
sync user guide for this feature
```

## My Jira tasks don't sync

Check:

- the OpenSpec change exists and its tasks are up to date
- Jira (SCRUM) tasks are linked to the `features/<id>.json` manifest
- the Jira key `SCRUM-123` appears in the PR title / commits
- re-run `create jira tasks for this change`

## Jira API returns 401 / 403

The API token lives in SOPS. Check:

- `SOPS_AGE_KEY_FILE` points to your private age key
- the token decrypts:

```bash
cd essensys-ansible
export JIRA_SECRET="$(sops -d --extract '["JIRA_SECRET"]' secrets/cloud/essensys.sops.yaml)"
[ -n "$JIRA_SECRET" ] && echo "token OK"
```

- the call uses `-u "<email>:$JIRA_SECRET"` (Atlassian Cloud Basic auth)
- if the token expired: regenerate it in Atlassian, then `sops secrets/cloud/essensys.sops.yaml` to replace it. Never in clear text in Git.

## Deployment fails (local or OVH)

- Local: check the `essensys-ansible` inventory and roles
- OVH: check the reverse proxy (Traefik/Nginx) and deployment secrets
- See the gateway installation docs

## I forgot to update the memory

Any architecture decision or merge touching the legacy IoT protocol / exchange table / SC944D firmware must trigger:

```text
update essensys-memory
```

## I want to remove the lifecycle

Use the bootstrap flow in reverse and review the diff before deleting files.
