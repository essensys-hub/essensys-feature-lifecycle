# Feature Lifecycle — Quick Start

Git est la source de vérité, l'IA est l'orchestrateur. Trois contraintes : **sécurité**, **open source**, **traçabilité complète**.

- une feature = un manifest dans `features/<id>.json`
- doc, tests et mémoire liés depuis le manifest
- les gates de PR valident structure, sécurité et traçabilité

## Le process (résumé)

```
Idée → Jira (SCRUM) → OpenSpec → Issues & Tasks Jira → Code → Test×N → Gate sécurité → Deploy (local + OVH)
         └────────  Documentation · Revue/autocritique · Mémoire (essensys-memory)  continues ────────┘
```

## Je veux...

| Besoin | FR | EN |
|---|---|---|
| Démarrer un projet vide | [Démarrer un projet vide](init-empty-project.fr.md) | [Start an empty project](init-empty-project.en.md) |
| Ajouter le workflow à un projet existant | [Ajouter à un projet existant](init-existing-project.fr.md) | [Add to an existing project](init-existing-project.en.md) |
| Travailler au quotidien | [Workflow quotidien](daily-workflow.fr.md) | [Daily workflow](daily-workflow.en.md) |
| Comprendre pourquoi une PR est bloquée | [Dépannage](troubleshooting.fr.md) | [Troubleshooting](troubleshooting.en.md) |
| Orchestrer l'IA / passer en subagents | [Orchestration IA & subagents](ai-orchestration.md) | — |

> Gestion de projet : **Jira** (projet `SCRUM`). Le backlog et les tasks vivent dans Jira ; GitHub ne sert qu'au code et aux gates CI.

## Installation (skills + bootstrap)

Les skills et rules vivent dans `.cursor/` de ce dépôt (pas d'outil propriétaire). Deux étapes :

```bash
# 1. Installer les skills & rules dans Cursor (une fois)
git clone https://github.com/essensys-hub/essensys-feature-lifecycle.git
cd essensys-feature-lifecycle
./scripts/install-skills.sh --global          # ~/.cursor (tous les repos)
#   ou : ./scripts/install-skills.sh /chemin/repo   (un repo précis)

# 2. Initialiser le lifecycle dans le repo cible — dans Cursor :
#    bootstrap feature lifecycle              (repo existant, interactif)
#    bootstrap feature lifecycle - empty project   (repo vide)
```

Le **bootstrap** copie schéma de manifeste, gates CI (`feature-gate`, `security-gate`), hooks et doc de base — sans rien écraser sans confirmation.

Guides détaillés : [projet vide](init-empty-project.fr.md) · [projet existant](init-existing-project.fr.md).

## TL;DR

1. La feature part du backlog **Jira SCRUM** : <https://essensys-hub.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog>

2. Dans Cursor, on génère la spec :

```text
openspec propose <feature>
```

3. On découpe en epics/stories/tasks Jira :

```text
create jira tasks for this change
```

4. À chaque étape : tests, gate sécurité, doc, revue, et mise à jour de `essensys-memory`.

Plus de détail : [`../features/feature-lifecycle.md`](../features/feature-lifecycle.md) et [`../../AGENTS.md`](../../AGENTS.md).
