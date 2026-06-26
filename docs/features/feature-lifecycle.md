# Feature lifecycle Essensys

## Objectif

Industrialiser la livraison d'une feature domotique, avec Git comme source de vérité unique et l'IA comme orchestrateur, sous trois contraintes non négociables : **sécurité**, **open source**, **traçabilité complète**.

```
Idée → Jira (SCRUM) → OpenSpec → Issues & Tasks Jira → Code → Test×N → Gate sécurité → Deploy (local + OVH)
         └──────────  Documentation · Revue/autocritique · Mémoire (essensys-memory)  continues ──────────┘
```

Le pivot est un fichier versionné par feature :

```text
features/<id>.json
```

## Les étapes

| # | Étape | Détail |
|---|---|---|
| 1 | **Backlog** | La feature naît dans le projet **Jira SCRUM** (`essensys-hub.atlassian.net`). |
| 2 | **OpenSpec** | On génère un change (`openspec-propose`) : proposal, design, specs, tasks. |
| 3 | **Issues & Tasks** | On crée les epics/stories/tasks dans Jira, reliées au change ; les commits/PR GitHub portent la clé `SCRUM-123`. |
| 4 | **Code** | Implémentation selon les specs, toolchain open source uniquement. |
| 5 | **Tests** | Unit, intégration, E2E (Playwright). Rien ne part sans tests verts. |
| 6 | **Gate sécurité** | gitleaks + **Trivy** (CVE/IaC) + Dependabot via `security-gate.yml`. Bloquant. Open source. |
| 7 | **Documentation** | Mise à jour **tout au long**, jamais à la fin. |
| 8 | **Deploy** | Local (gateway / dev) **et** OVH (cloud). |
| 9 | **Revue / autocritique** | À chaque étape ; Bugbot / security-review avant PR. |
| 10 | **Mémoire** | `essensys-memory` mise à jour en permanence. |

## Ce que le workflow apporte

| Brique | Rôle |
|---|---|
| `feature-manifest-orchestrator` | crée ou met à jour le manifest depuis le Project / OpenSpec |
| `feature-userguide-sync` | met à jour la doc utilisateur |
| `playwright-from-spec` | relie OpenSpec aux tests E2E |
| `security-gate-triage` | traite les findings secrets/CVE/Dependabot |
| `jira-xray-test-campaign` | crée epics/stories/tasks Jira et campagnes de test Xray |
| `feature-gate.yml` | vérifie schéma, chemins, couverture, fraîcheur |
| `security-gate.yml` | bloque sur secrets et findings Critical/High |

## Fichiers clefs

- `features/schema/feature.schema.json`
- `features/*.json`
- `.github/workflows/feature-gate.yml`
- `.github/workflows/security-gate.yml`
- `.github/dependabot.yml`
- `scripts/hooks/pre-commit`
- `docs/feature-lifecycle/README.md`
- `docs/feature-lifecycle/ai-orchestration.md`

## Guide utilisateur

- [Feature lifecycle — quick start](../feature-lifecycle/README.md)
- [Démarrer un projet vide](../feature-lifecycle/init-empty-project.fr.md)
- [Ajouter à un projet existant](../feature-lifecycle/init-existing-project.fr.md)
- [Workflow quotidien](../feature-lifecycle/daily-workflow.fr.md)
- [Dépannage](../feature-lifecycle/troubleshooting.fr.md)
- [Orchestration IA & subagents](../feature-lifecycle/ai-orchestration.md)

## Conventions

- une feature = un manifest
- une PR = code + tests + sécurité + doc liés à cette feature
- pas de sync « magique » hors Git
- pas d'outil ni de dépendance propriétaire
- pas de secret en clair (SOPS / vault / Secrets Manager)
- les exceptions sécurité sont des dismissals d'alertes Dependabot, tracées dans `security.muted_findings[]` du manifest
- toute décision d'archi → mise à jour `essensys-memory`
