---
name: github-project-lifecycle
description: Gestion projet Essensys dans le GitHub Project essensys-hub #6 — tickets (Bug/Task/Feature/Support), passage ticket → OpenSpec, sub-issues, statuts, checkup et non-régression. Utiliser dès qu'il est question de ticket, backlog, issue, sprint, statut de feature, campagne de test ou non-régression. Remplace jira-xray-test-campaign.
---

# GitHub Project lifecycle (Essensys)

Source de vérité : `claude/GOVERNANCE.md` de ce dépôt. Change : `openspec/changes/github-project-lifecycle-2026-10-001`.

## Principes

- **Un seul Project** : `essensys-hub` #6 « Essensys Roadmap ». Pas de Jira/Xray/Confluence (legacy, tickets clos au 2026-10-09).
- **Pas de modification sans ticket** ; commits `(#n)`, PR `Feature: <id>` + `Closes #n`.
- **Manifest** `features/<id>.json` = vérité CI, bloc `github: {issue, project_item}`.
- **Statuts** `Idée → Spec → Prêt → En cours → Test → Gate sécu → Déployé → Archivé`, avancés par `scripts/feature_lifecycle/project_sync.py` (jamais de recul automatique).
- **Écritures GitHub** : dry-run d'abord, confirmation explicite, jamais de suppression.

## Recettes

| Besoin | Action |
|---|---|
| Nouveau besoin / bug | `/ticket <description>` (Claude Code) ou `gh issue create` + `gh project item-add 6 --owner essensys-hub --url …` |
| Ticket → spec | `/ticket-to-spec owner/repo#n` : OpenSpec + manifest + `Feature ID` + sub-issues (une par groupe de `tasks.md`) |
| Avancer un statut | `python3 scripts/feature_lifecycle/project_sync.py advance <id> <event> [--apply]` |
| État | `/feature-status [<id>]` ou `project_sync.py status <id>` |
| Campagne de test | `/checkup [<id>|<repo>]` : build, lint, unit, NR, app (Playwright / émulateur Android / simulateur iOS), gates → rapport sur l'issue |
| Non-régression | convention `NR-<repo>-<n>` + `#issue` (`docs/feature-lifecycle/non-regression.md`), `nonreg_report.py`, workflow `nonreg.yml`, `/nonreg` |
| Configurer le Project | `bootstrap_project.py` (dry-run, puis `--apply` par un humain) |
| Setup poste | `scripts/feature_lifecycle/check_claude_setup.sh` ; harness : `scripts/install-claude.sh` |
