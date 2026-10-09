## Why

Le cycle de vie feature Essensys est éclaté entre Jira SCRUM (backlog, Xray), Confluence (doc miroir), GitHub (code, CI, gates) et `essensys-memory` (mémoire LLM). La traçabilité idée → déploiement repose sur des liens manuels entre outils, le support utilisateur n'a pas de canal structuré, et le passage en association loi 1901 (open source, coût nul, contributeurs externes) rend un outillage propriétaire payant inadapté. Décision : **tout le pilotage passe dans GitHub Project**, et **Claude Code y est connecté** pour créer/trier les tickets, faire avancer les features et piloter les tests de non-régression.

## What Changes

- Créer un **GitHub Project v2 unique** pour l'org `essensys-hub`, couvrant tous les dépôts, avec champs `Status` (Idée → Spec → Prêt → En cours → Test → Gate sécu → Déployé → Archivé), `Feature ID`, `Phase`, `Cible`, `Appareil`.
- Définir les **types d'issue org** `Feature`, `Task`, `Bug`, `Support` et le découpage par **sub-issues** (Feature dans `essensys-feature-lifecycle`, Tasks dans les dépôts cibles).
- **BREAKING** : le manifest `features/<id>.json` remplace les blocs `jira` et `confluence` par un bloc `github` (`issue`, `project_item`) ; le manifest reste la source de vérité des gates CI.
- **Synchronisation automatique** manifest / PR / deploy → champ `Status` du Project via Actions (GraphQL).
- **BREAKING** : `feature-gate` exige dans chaque PR une ligne `Feature: <id>` et un `Closes #<n>` / `Refs #<n>` vers une issue du Project.
- Remplacer les campagnes **Xray** par les checks de PR + archives `e2e-reports-archive` liées à l'issue Feature.
- Créer le dépôt public **`essensys-support`** : issue forms, Discussions, triage assisté par LLM (sans fermeture automatique), escalade Support → Bug en sub-issue, signalement des failles via Security Advisories privées.
- Alimenter **`essensys-memory`** par événements (feature archivée, support résolu, release) via PR relue par un humain ; accès agents via `essensys-mcp`.
- **Remise à zéro** : tous les tickets existants au 2026-10-09 passent à `Done` (pas de migration) ; le pilote du nouveau lifecycle est la **mise à jour de l'app Android** (`essensys-android-phone-apps`, alignement sur le portail actuel) pour un client. Puis **décommissionner** Jira, Xray et Confluence (`confluence-sync.yml`, `confluence_sync.py`, `post_security_gate_to_jira.py`).
- Connecter **Claude Code** au Project (gh CLI scope `project` + GitHub MCP toolset `projects`) et fournir des commandes `/ticket`, `/ticket-to-spec`, `/checkup`, `/feature-status`, `/nonreg` ; règle : toute modification passe par un ticket.
- Mettre en place une **campagne de non-régression** (nightly + PR) dont chaque échec ouvre ou met à jour un `Bug` dans le Project, et exiger un test de non-régression pour toute correction de `Bug`.
- Mettre à jour skills (`jira-xray-test-campaign` → `github-project-lifecycle`, `feature-manifest-orchestrator`, `feature-lifecycle-bootstrap`), README, AGENTS.md et docs.

## Capabilities

### New Capabilities

- `github-project-tracking`: Project v2 org, champs, types d'issue, hiérarchie Feature → sub-issues, transitions de `Status`.
- `project-sync-automation`: synchronisation automatique manifest / PR / deploy → Project et liaison PR ↔ issue exigée par la gate.
- `support-ticketing`: dépôt `essensys-support`, formulaires, triage LLM, escalade, canal sécurité privé.
- `memory-feed`: alimentation événementielle de `essensys-memory` par PR relue et exposition aux agents via `essensys-mcp`.
- `claude-code-project-integration`: accès de Claude Code au Project (lecture/écriture items, champs, sub-issues) et commandes dédiées tickets / features / non-régression.
- `regression-test-tracking`: suite de non-régression, liaison Bug ↔ test, ouverture automatique de Bug sur échec, vue Project dédiée.
- `jira-migration`: remise à zéro des tickets au 2026-10-09, archive et décommission Jira / Xray / Confluence.

### Modified Capabilities

<!-- Aucune spec principale n'existe encore dans openspec/specs : le contrat manifest et la feature-gate sont spécifiés ici en tant que nouvelles exigences de `project-sync-automation`. -->

## Impact

- `features/schema/feature.schema.json` (+ template bootstrap) et tous les manifests `features/*.json` des dépôts Essensys.
- `scripts/feature_lifecycle/check_feature_gate.py`, `validate_feature_manifests.py`, nouveaux scripts `project_sync.py`, `nonreg_report.py`, `check_pr_linkage.py`.
- `.github/workflows/feature-gate.yml`, nouveaux `project-sync.yml`, `support-triage.yml` ; suppression `confluence-sync.yml`.
- `.cursor/skills/*` (lifecycle, manifest, bootstrap, Jira), README, AGENTS.md, `docs/feature-lifecycle/`.
- Nouveau dépôt `essensys-hub/essensys-support` ; `essensys-memory/.github/workflows/brain-sync.yml` ; `essensys-mcp/brain_server.py`.
- Secrets org : GitHub App (ou PAT fine-grained) avec scope `project` + `issues`, clé API Anthropic pour le triage.
- `.claude/commands/` et `.claude/settings.json` de l'espace ESSENSYS ; config MCP GitHub (toolset `projects`).
- Suites de tests existantes : `go test ./...` (backends jumeaux), `test/test_chb3.py`, Playwright (UX matrix, no-armoire).
- Fin des abonnements Atlassian (Jira, Xray, Confluence).
