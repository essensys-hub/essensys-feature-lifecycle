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
| 5 | **Tests** | Unit, intégration, E2E (Playwright). Pour les UIs : gate UX desktop + iPhone + iPad obligatoire, avec no-armoire. Rien ne part sans tests verts. |
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
| `essensys-ux-regression-gate` | impose la non-régression UX desktop/iPhone/iPad et la preuve Playwright |
| `security-gate-triage` | traite les findings secrets/CVE/Dependabot |
| `jira-xray-test-campaign` | crée epics/stories/tasks Jira et campagnes de test Xray |
| `feature-gate.yml` | vérifie schéma, chemins, couverture, fraîcheur |
| `ux-matrix-gate.yml` | exécute la matrice Playwright desktop/iPhone/iPad dans les repos frontends |
| `security-gate.yml` | bloque sur secrets et findings Critical/High |

## Gate UX multi-device

Toute feature UI doit déclarer dans `features/<id>.json` :

- `tests.ux_matrix.required: true`
- `tests.ux_matrix.devices` contenant au minimum `desktop`, `iphone`, `ipad`
- `tests.ux_matrix.required_projects` couvrant ces formats, par exemple `support-desktop`, `support-iphone`, `support-ipad`
- `tests.ux_matrix.screenshots_required: true`
- `tests.ux_matrix.visual_regression_required: true`
- `tests.ux_matrix.no_armoire_required: true` dès qu'une UI peut déclencher une action domotique

Les specs Playwright doivent porter une annotation lisible par revue et gate :

```ts
// @feature: <id>
// @devices: desktop,iphone,ipad
// @no-armoire
```

`scripts/feature_lifecycle/check_feature_gate.py --strict` bloque une feature UI si la matrice ou les preuves minimales sont absentes.

## Fichiers clefs

- `features/schema/feature.schema.json`
- `features/*.json`
- `.github/workflows/feature-gate.yml`
- `.github/workflows/ux-matrix-gate.yml`
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
