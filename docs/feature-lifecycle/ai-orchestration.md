# Orchestration IA & subagents — proposition

> But : utiliser l'IA non pas comme un assistant ponctuel, mais comme un **orchestrateur** du cycle de vie feature Essensys, jusqu'à exécuter des étapes via des **subagents** autonomes — tout en gardant sécurité, open source et traçabilité au cœur.

Document de proposition. Les sections « Décisions à valider » listent ce qui reste à trancher avant industrialisation.

---

## 1. Pourquoi des subagents

Le process Essensys est long et linéaire (Jira → OpenSpec → tasks → code → tests → sécurité → doc → deploy → revue → mémoire). Le faire en un seul fil de chat :

- sature le contexte (perte d'information en fin de cycle),
- mélange les rôles (l'auteur du code ne devrait pas être seul juge de sa sécurité),
- empêche le parallélisme (les tasks indépendantes attendent les unes les autres).

Les **subagents** résolvent ces trois points : contexte isolé par tâche, séparation des rôles (auteur ≠ relecteur), exécution parallèle des tasks indépendantes.

---

## 2. Modèle d'orchestration cible

Un **agent orchestrateur** (chat principal) pilote des **subagents spécialisés**, un par étape ou par task. L'orchestrateur ne code pas : il découpe, délègue, agrège, et tranche.

```
                    ┌──────────────────────────────────────────────┐
                    │            Agent Orchestrateur                │
                    │  (lit Jira + OpenSpec, découpe, agrège)       │
                    └───────────────┬──────────────────────────────┘
        ┌───────────────┬───────────┼───────────────┬───────────────┐
        ▼               ▼           ▼               ▼               ▼
   ┌─────────┐    ┌─────────┐  ┌─────────┐    ┌──────────┐   ┌──────────┐
   │ spec-   │    │ code-   │  │ test-   │    │ security-│   │ doc +    │
   │ agent   │ →  │ agent   │→ │ agent   │ →  │ review   │ → │ memory   │
   │(OpenSpec)│    │(feature)│  │(Playwr.)│    │ (gate)   │   │ agent    │
   └─────────┘    └─────────┘  └─────────┘    └──────────┘   └──────────┘
        └──────────────  revue / autocritique à chaque handoff  ──────────┘
```

### Rôles proposés (mappés sur les skills existants)

| Subagent | Rôle | Skills / outils |
|---|---|---|
| **spec-agent** | Transforme un item de backlog Jira en change OpenSpec complet | `openspec-explore`, `openspec-propose` |
| **planner-agent** | Découpe l'OpenSpec en epics/stories/tasks Jira | `jira-xray-test-campaign` |
| **code-agent** (×N) | Implémente une task isolée | `software-architecture`, `angular-architect`, `feature-manifest-orchestrator` |
| **test-agent** | Génère et fait passer les tests | `playwright-from-spec`, `gxp-unit-test-report-generator` |
| **security-agent** | Gate sécurité indépendante (rôle séparé du code-agent) | `security-gate-triage`, security-review |
| **review-agent** | Revue & autocritique avant PR | Bugbot, review-security |
| **doc-memory-agent** | Doc continue + mise à jour `essensys-memory` | `feature-userguide-sync`, `second-brain-ingest` |

> Principe clé : **l'agent qui écrit le code n'est pas celui qui valide sa sécurité**. La séparation des rôles est une exigence, pas une commodité.

---

## 3. Découpage en phases (du manuel au piloté)

L'adoption se fait par paliers, pas d'un coup.

### Palier 0 — Aujourd'hui (manuel assisté)
Un humain enchaîne les prompts (`openspec propose`, `generate e2e tests`, …) dans un seul chat. L'IA assiste, l'humain orchestre.

### Palier 1 — Orchestrateur unique
Un seul chat « orchestrateur » lit Jira et l'OpenSpec, puis **délègue chaque étape à un subagent** (via le Task tool, une task Jira par subagent). L'humain valide les handoffs.

### Palier 2 — Subagents parallèles
Les tasks **indépendantes** (détectées via les dépendances de l'OpenSpec) sont exécutées en parallèle par plusieurs `code-agent`, chacun dans son worktree git isolé. L'orchestrateur agrège.

### Palier 3 — Boucle qualité automatique
`test-agent` → `security-agent` → `review-agent` s'enchaînent automatiquement après chaque code-agent ; échec = renvoi au code-agent avec le diagnostic. L'humain n'intervient qu'en arbitrage.

### Palier 4 — Mémoire et revue continues
`doc-memory-agent` tourne en continu : à chaque merge touchant protocole legacy / table d'échange / SC944D, il met à jour `essensys-memory` sans prompt explicite.

---

## 4. Contrats entre agents (pour la traçabilité)

Pour rester traçable, chaque handoff produit un artefact Git, jamais un état « en mémoire » :

| Handoff | Artefact produit | Validé par |
|---|---|---|
| Jira → spec-agent | change OpenSpec (`openspec/changes/<id>/`) | humain |
| spec-agent → planner | epics/stories/tasks liées dans Jira (SCRUM) | humain (palier ≤2) |
| planner → code-agent | branche + `features/<id>.json` | feature-gate |
| code-agent → test-agent | code + commits liés aux issues | tests verts |
| test-agent → security-agent | rapport de tests | security-gate |
| security-agent → review-agent | findings triés + manifest `security.*` | gate bloquante |
| review-agent → PR | PR avec checklist remplie | humain |
| merge → doc-memory-agent | doc + `essensys-memory` à jour | brain update |

Le **manifest `features/<id>.json`** reste le fil conducteur unique : chaque agent le lit et l'enrichit.

---

## 5. Garde-fous (sécurité / open source / traçabilité)

Non négociables, valables pour tout subagent :

- **Sécurité** : la gate sécurité est exécutée par un agent **distinct** de l'auteur ; aucun subagent ne peut la contourner ni muter un secret. Secrets via **SOPS + age** uniquement (cf. `AGENTS.md` → Secrets & SOPS). Un subagent qui appelle Jira lit `JIRA_SECRET` via `sops -d --extract` en variable d'env éphémère — jamais en clair dans un prompt, un log ou un transcript.
- **Open source** : tout subagent qui propose une dépendance doit justifier sa licence ; pas d'outil propriétaire. La gate SCA elle-même est open source — **gitleaks** (secrets) + **Trivy** (CVE deps + Docker/IaC) + Dependabot ; GitGuardian reste au plus un dashboard secrets optionnel, jamais la gate bloquante.
- **Traçabilité** : chaque action d'un subagent = un commit relié à une issue/task ; pas d'effet de bord hors Git. Les transcripts d'agents sont archivés (`transcripts/`).
- **Humain dans la boucle** : déploiement (local + OVH) et merge restent sous validation humaine jusqu'au palier 4 inclus.
- **Mémoire** : `essensys-memory` est consultée **avant** toute décision d'archi et mise à jour **après** ; un subagent ne décide pas d'archi sans lire le brain.

---

## 6. Mise en œuvre dans Cursor

Les briques existent déjà :

- **Task tool / subagents** : un subagent autonome par task Jira (l'orchestrateur lit le board SCRUM et délègue).
- **Worktrees isolés** : pour le parallélisme (palier 2), chaque code-agent dans sa branche/worktree.
- **Revue** : sous-agents `bugbot` et `security-review` pour le palier 3.
- **Mémoire** : `second-brain-ingest` pour le doc-memory-agent.

Prompts d'orchestration types :

```text
openspec propose <feature>          # spec-agent
create jira tasks for this change   # planner-agent
generate e2e tests for this feature # test-agent
triage security findings            # security-agent
update essensys-memory              # doc-memory-agent
```

---

## 7. Décisions à valider

1. **Granularité des subagents** : un par étape (7 rôles) ou un par task (N code-agents) ? → proposition : les deux, étape pour la pipeline, task pour le code.
2. **Niveau d'autonomie cible** : s'arrêter au palier 2 (parallélisme avec validation humaine) ou viser le palier 4 ?
3. **Politique de parallélisme** : nombre max de code-agents simultanés ; stratégie de merge des worktrees.
4. **Déploiement automatisé** : autorise-t-on un deploy-agent sur l'environnement **local** (jamais OVH sans humain) ?
5. **Modèles par rôle** : modèle « fort » pour spec/review, modèle « rapide » pour code/test ?
6. **Mémoire en continu** : seuils déclenchant un `update essensys-memory` automatique.

---

## 8. Prochaines étapes proposées

- [ ] Valider les rôles de subagents (§2) et les paliers (§3) avec l'équipe.
- [ ] Écrire un change OpenSpec « ai-orchestration » dans `essensys-memory/openspec/changes/`.
- [ ] Prototyper le palier 1 sur une petite feature réelle du backlog Jira.
- [ ] Mesurer : temps de cycle, taux de retours sécurité, complétude doc/mémoire.
- [ ] Décider du passage au palier 2 (parallélisme) selon les mesures.
