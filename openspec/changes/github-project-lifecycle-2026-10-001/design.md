## Context

Voir `proposal.md` (Why). État actuel :
- `features/schema/feature.schema.json` impose les blocs `jira` (`issue`, `test_plan`) et `confluence` ; `check_feature_gate.py` / `validate_feature_manifests.py` les consomment ; le template bootstrap en propage une copie dans les autres dépôts.
- Workflows : `feature-gate.yml`, `security-gate.yml`, `confluence-sync.yml`, `publish-wise-feature-lifecycle.yml` ; scripts `confluence_sync.py`, `post_security_gate_to_jira.py`.
- `essensys-memory` a un workflow `brain-sync.yml` (push + cron hebdo) ; `essensys-mcp` expose déjà un `brain_server.py`.
- ~40 dépôts dans l'org `essensys-hub`, mainteneur principal unique.

## Goals / Non-Goals

**Goals:**
- Un seul endroit pour piloter (Project), un seul contrat CI (manifest), une seule mémoire (essensys-memory).
- Zéro double saisie : les transitions courantes sont automatiques.
- Bascule réversible tant que Jira n'est pas résilié.

**Non-Goals:**
- Pas d'outil de support tiers (Zendesk, Freshdesk) ni de helpdesk privé.
- Pas de synchronisation bidirectionnelle Jira ↔ GitHub pendant la transition (import ponctuel uniquement).
- Pas de refonte des gates sécurité/UX existantes au-delà du remplacement de la cible Jira.

## Decisions

### D1 — Manifest = vérité CI, Project = vue de pilotage
Le manifest reste la seule chose que la CI lit ; le Project est mis à jour par la CI, jamais l'inverse (sauf champs purement de planification : `Phase`, priorité, assignation).
*Alternative écartée* : Project comme source de vérité lue par la CI → appels API GraphQL dans chaque gate, quota et fragilité, et perte de la versionnée Git.

### D2 — Bloc `github` remplace `jira` + `confluence`, avec fenêtre de compatibilité
Schéma v2 : `github: { issue: "essensys-hub/<repo>#<n>", project_item: string|null }`. Pendant 30 jours après la bascule, le validateur accepte `jira` en warning ; ensuite erreur. `confluence` est supprimé (la doc vit déjà dans les dépôts et le support-site).
*Alternative écartée* : garder `jira.issue` en y mettant une URL GitHub → nom trompeur, dette.

### D3 — Authentification : GitHub App org « essensys-lifecycle-bot »
Permissions : Projects (org, RW), Issues (RW), Pull requests (R), Contents (R ; RW uniquement sur `essensys-memory` pour ouvrir des PR). Token obtenu via `actions/create-github-app-token`. Secrets `LIFECYCLE_APP_ID` / `LIFECYCLE_APP_KEY` au niveau org.
*Alternative écartée* : PAT personnel → lié au compte du fondateur, incompatible avec la gouvernance associative.

### D4 — Sync : workflow réutilisable `project-sync.yml`
Un workflow `workflow_call` dans `essensys-feature-lifecycle`, appelé par chaque dépôt sur `pull_request` (opened/closed), `workflow_run` (security-gate, E2E, deploy) et `release`. Il exécute `scripts/feature_lifecycle/project_sync.py` qui : lit la ligne `Feature:` de la PR → manifest → item Project, calcule le statut cible, n'applique que les transitions **vers l'avant** (D-spec « jamais de régression auto »). Le bootstrap installe l'appel dans les dépôts.
*Alternative écartée* : workflows intégrés du Project (auto-add, item closed) → insuffisants pour la logique multi-PR / gate / deploy ; on garde toutefois l'auto-add natif par dépôt.

### D5 — Hiérarchie via sub-issues natives + issue types org
Sub-issues GitHub (cross-repo supportées) plutôt que tasklists ou labels `epic:*`. `openspec-propose` (via `feature-manifest-orchestrator`) crée la Feature puis une Task par groupe `## N.` de `tasks.md` dans le dépôt cible déclaré.

### D6 — Support : dépôt public + `anthropics/claude-code-action`
Triage sur `issues: opened` avec prompt restreint (labels, doublons, réponse proposée) et permissions `issues: write` uniquement, pas `contents: write`. L'escalade est déclenchée par un label `escalade:<repo>` posé par un humain, traité par `project_sync.py escalate`.
*Alternative écartée* : triage automatique avec fermeture → risque de faux positifs vis-à-vis d'utilisateurs non techniques.

### D7 — Memory feed : `repository_dispatch` vers `essensys-memory`
Les dépôts émettent `repository_dispatch` (`feature-archived`, `support-resolved`, `release-published`) ; `brain-sync.yml` gagne un déclencheur `repository_dispatch` qui génère la synthèse (LLM) et ouvre une PR. Branch protection sur `main` d'`essensys-memory` impose la revue.

### D8 — Pas de migration : remise à zéro au 2026-10-09
Tous les tickets existants (Jira SCRUM, Projects #1–#6) passent à `Done` ; seul l'historique est archivé. Le Project #6 démarre vide, le premier ticket est le pilote Android. *Alternative écartée* : script de migration Jira → GitHub → coût élevé pour des tickets largement obsolètes ; un besoin encore vivant est recréé via `/ticket`.

### D9 — Claude Code connecté par deux canaux complémentaires
- **GitHub MCP server** (déjà branché dans les sessions) avec le toolset `projects` activé : lecture/écriture des items et champs en langage naturel.
- **`gh` CLI** avec scopes `project` + `read:org` (aujourd'hui absent : `gh auth refresh -s project`) : utilisé par les commandes et scripts pour les opérations déterministes (`gh project item-edit`, GraphQL).
- **Commandes** versionnées dans `essensys-feature-lifecycle/claude/commands/` et installées dans `ESSENSYS/.claude/commands/` par `scripts/install-claude.sh` (le dossier ESSENSYS n'est pas un dépôt git) : `/ticket`, `/ticket-to-spec`, `/checkup`, `/feature-status`, `/nonreg`. Elles délèguent la logique déterministe à `project_sync.py` (même code que la CI → un seul comportement).
- **Règles de gouvernance** dans `claude/GOVERNANCE.md`, importées par `ESSENSYS/CLAUDE.md` (`@essensys-feature-lifecycle/claude/GOVERNANCE.md`) : toute modification passe par un ticket du Project #6.
- **Hors session interactive** : `anthropics/claude-code-action` dans les workflows (triage support, synthèse nightly), avec le token de la GitHub App (D3).
- Script `scripts/feature_lifecycle/check_claude_setup.sh` qui vérifie scopes `gh`, toolset MCP et accès Project.
*Alternative écartée* : un MCP maison « essensys-project » → duplication du MCP GitHub officiel ; `essensys-mcp` reste dédié à la mémoire.

### D10 — Non-régression : tag `NR-*` + reporter commun
- Convention d'identifiant `NR-<repo>-<n>` + référence issue, portée par tag Playwright (`@nr`, annotation `issue`), commentaire `// NR: NR-server-backend-12 #123` en Go, marqueur pytest `@pytest.mark.nr(id, issue)`.
- Un script `nonreg_report.py` normalise les sorties (JUnit XML Go via `gotestsum`, Playwright JSON, pytest JUnit) en un rapport unique par `NR-*`.
- Workflow `nonreg.yml` : sur PR (dépôts touchés) et nightly (`schedule`, tous dépôts, matrice) ; toujours `NO_ARMOIRE=1`.
- `project_sync.py regression` ouvre/commente les `Bug` en dédupliquant par le marqueur `<!-- nr:NR-... -->` dans le corps.
*Alternative écartée* : outil de test management externe (TestRail, Xray) → contraire au choix GitHub-only et open source.

### D11 — Réutiliser le Project #6 et consolider l'existant
Constat au 2026-10-09 : 6 Projects org (#1 ESSENSYS WEB SERVER 1 item, #2 Gateway local 15, #3 raspberry pi install 22, #4 template vide, #5 Firmware Build Pipeline 12, #6 « @essensys issue tracking » vide). Types d'issue org existants : `Task`, `Bug`, `Feature` — `Support` manquant.
Décision : renommer #6 en « Essensys Roadmap » et lui ajouter les champs ; les items de #1/#2/#3/#5 sont passés à `Done` sur place (D8) puis ces Projects sont fermés (pas de suppression). Créer seulement le type `Support`.

## Risks / Trade-offs

- [Quota GraphQL / rate limit sur 40 dépôts] → token GitHub App (quota par installation), sync uniquement sur événements, pas de polling.
- [Sub-issues / issue types encore évolutifs côté GitHub] → encapsuler les appels dans `project_sync.py` ; fallback label `type:*` si l'API change.
- [Triage LLM qui hallucine une réponse] → réponse marquée « proposition générée », jamais de fermeture, lien obligatoire vers la source wiki.
- [Données personnelles dans les tickets publics] → avertissement dans les forms, label `securite-a-masquer`, possibilité de masquer un commentaire ; mémoire distillée sans PII.
- [Breaking change manifest sur tous les dépôts] → fenêtre de compatibilité 30 j + script `migrate_manifests.py` qui réécrit `jira` → `github`.
- [Perte de capacités Xray (traçabilité exigences ↔ tests)] → lien spec OpenSpec ↔ test Playwright déjà porté par le manifest (`tests`) et `playwright-from-spec`.

- [Tests flaky qui inondent le Project de Bugs] → déduplication par `NR-*`, label `flaky` après 2 alternances vert/rouge, jamais plus d'une issue par test.
- [Agent Claude Code qui modifie trop le Project] → garde-fous (pas de suppression, confirmation avant création/fermeture), token bot à permissions minimales en CI.

## Baseline production (2026-10-09)

L'état de l'org au 2026-10-09 est le **point de départ de la production** du lifecycle GitHub : Projects #1–#6 et leurs items tels quels, types d'issue `Task`/`Bug`/`Feature`, Jira SCRUM encore actif, `gh` du mainteneur connecté avec le scope `project`. Toute migration (D11, Jira) part de cet instantané ; rien n'est réécrit rétroactivement avant cette date.

## Migration Plan

0. Connecter Claude Code (scopes `gh`, toolset MCP `projects`, `check_claude_setup.sh`) — prérequis de tout le reste.
1. Créer GitHub App, issue types, Project et champs (scriptés, `scripts/feature_lifecycle/bootstrap_project.py`).
2. Livrer schéma v2 + validateur avec compatibilité `jira` en warning ; `migrate_manifests.py` sur tous les dépôts.
3. Déployer `project-sync.yml` + `feature-gate` durcie en mode **warning** une semaine, puis bloquant.
4. Passer tous les tickets existants à `Done` (D8) ; exporter et archiver Jira / Xray / Confluence.
5. Créer `essensys-support`, activer le triage.
6. Étendre `brain-sync.yml` (dispatch) et `essensys-mcp`.
7. Après 30 j sans incident : supprimer `confluence-sync.yml`, scripts Jira, compat `jira` ; résilier Atlassian.

Rollback : jusqu'à l'étape 7, Jira reste en lecture seule et la gate peut repasser en warning via variable `FEATURE_GATE_MODE=warn`.

## Open Questions

- Nom définitif du Project et granularité de `Phase` au-delà de 3 (ajustable sans impact sur les specs).
- Durée exacte de rétention des archives Atlassian (dépend du bureau de l'association).
