<!-- Phase A (groupes 1–7) : harness Claude Code ↔ GitHub Project, prérequis du pilote Android.
     Phase B (groupes 8–10) : support public, mémoire, décommission — après le pilote. -->

## 1. Remise à zéro et Project #6

- [x] 1.1 Passer à `Done` tous les items non-Done des Projects #1, #2, #3 (`scripts/feature_lifecycle/reset_projects.sh`, dry-run par défaut) ; vérifier 0 item non-Done
- [x] 1.2 Écrire `scripts/feature_lifecycle/bootstrap_project.py` (dry-run par défaut, `--apply`) : renomme #6 en « Essensys Roadmap », ajoute les options `Status` (Idée, Spec, Prêt, En cours, Test, Gate sécu, Déployé, Archivé) et les champs `Feature ID`, `Phase`, `Cible`, `Appareil` ; vérifier le plan en dry-run puis `gh project field-list 6`
- [ ] 1.3 Créer le type d'issue org `Support` (admin org) ; vérifier via GraphQL `organization.issueTypes`
- [ ] 1.4 Créer les vues (Status, Roadmap par Phase, À trier, Gate sécu en échec, Non-régression) et l'auto-add des dépôts actifs ; vérifier visuellement
- [ ] 1.5 Fermer les Projects #1–#5 (sans suppression) ; vérifier `gh project list --owner essensys-hub`

## 2. Connexion Claude Code ↔ Project

- [x] 2.1 Ajouter les scopes `project` et `read:org` à `gh` (`gh auth refresh -s project,read:org`) ; vérifié le 2026-10-09 : `gh project list --owner essensys-hub` liste les 6 Projects
- [x] 2.2 Écrire `scripts/feature_lifecycle/check_claude_setup.sh` (scopes gh, accès Project #6, CLI openspec, adb/émulateur optionnels) ; vérifier qu'il sort OK sur le poste du mainteneur
- [x] 2.3 Écrire `claude/GOVERNANCE.md` (toute modification passe par un ticket, ticket → OpenSpec, checkup avant PR, garde-fous) et `scripts/install-claude.sh` qui installe commandes + import dans `ESSENSYS/CLAUDE.md` ; vérifier qu'une nouvelle session Claude Code liste les commandes
- [ ] 2.4 Activer le toolset `projects` du GitHub MCP dans la config Claude Code ESSENSYS ; vérifier un appel MCP de lecture du Project #6

## 3. Commandes Claude Code

- [ ] 3.1 `/ticket` : doublons, proposition type/dépôt/champs, création + ajout au Project après confirmation ; vérifier sur le ticket pilote Android
- [ ] 3.2 `/ticket-to-spec <issue>` : décision OpenSpec ou correctif trivial, change OpenSpec + manifest bloc `github`, `Feature ID`, sub-issues ; vérifier sur le ticket pilote
- [ ] 3.3 `/checkup [<Feature ID>|<repo>]` : build, lint, unit, NR, tests applicatifs (Playwright / émulateur Android / simulateur iOS), gates, rapport posté sur l'issue ; vérifier sur `essensys-android-phone-apps`
- [ ] 3.4 `/feature-status` et `/nonreg` ; vérifier sur le ticket pilote

## 4. Synchronisation Project et contrôles PR

- [x] 4.1 Implémenter `project_sync.py` (client GraphQL via `gh`, lecture/écriture des champs, machine d'états vers l'avant uniquement, parsing `Feature:` / `Closes #`) avec tests unitaires (`python3 -m unittest`)
- [x] 4.2 Implémenter `check_pr_linkage.py` (ligne `Feature:`, `Closes|Refs #n`, exemptions Dependabot / `chore/no-feature`, Bug ⇒ test `NR-*`) avec tests unitaires
- [ ] 4.3 Ajouter l'étape PR linkage à `feature-gate.yml` en mode `FEATURE_GATE_MODE=warn` ; vérifier sur une PR de test
- [ ] 4.4 Créer le workflow réutilisable `project-sync.yml` (PR ouverte/mergée, gates, deploy) ; vérifier sur la PR pilote que l'item avance
- [ ] 4.5 Ajouter `.github/pull_request_template.md` (Feature / Closes / checkup) au dépôt et au bootstrap ; vérifier sa présence

## 5. Manifest v2

- [x] 5.1 Schéma : bloc `github` (`issue`, `project_item`) ajouté, `jira` et `confluence` rendus optionnels (fenêtre de compat) ; vérifier `validate_feature_manifests.py` sur les manifests existants et un manifest v2
- [x] 5.2 Répercuter le schéma dans le template `feature-lifecycle-bootstrap` ; vérifier que les deux schémas sont identiques

## 6. Non-régression

- [x] 6.1 Documenter la convention `NR-<repo>-<n>` (Go, Kotlin/JUnit, Playwright `@nr`, pytest) dans `docs/feature-lifecycle/non-regression.md`
- [x] 6.2 Implémenter `nonreg_report.py` (JUnit XML Go / Gradle / pytest + JSON Playwright → rapport par `NR-*`, markdown + JSON) avec tests sur fixtures
- [x] 6.3 Implémenter `project_sync.py regression` (ouverture/commentaire Bug dédupliqué par `<!-- nr:... -->`, label `flaky`, proposition de fermeture après 3 verts) avec tests
- [ ] 6.4 Créer le workflow réutilisable `nonreg.yml` (PR + nightly, `NO_ARMOIRE=1`, archive) ; vérifier par `workflow_dispatch`
- [ ] 6.5 Taguer en `NR-*` les tests critiques existants (`test_chb3.py`, backends jumeaux, UX matrix, Android) ; vérifier que le rapport les liste

## 7. Documentation et skills

- [x] 7.1 Mettre à jour AGENTS.md et README : process Ticket (Project #6) → OpenSpec → Code → Checkup → Gates → Deploy ; vérifier `grep -i jira` limité aux mentions historiques
- [ ] 7.2 Remplacer le skill `jira-xray-test-campaign` par `github-project-lifecycle` ; mettre à jour `feature-manifest-orchestrator` et `feature-lifecycle-bootstrap`
- [ ] 7.3 Mettre à jour `essensys-memory/wiki/concepts/feature-lifecycle.md`

## 8. Support public (phase B)

- [ ] 8.1 Créer le dépôt public `essensys-support` (README, SECURITY.md → advisories privées, Discussions) ; vérifier Security → Report a vulnerability
- [ ] 8.2 Issue forms (panne armoire, install gateway, portail/compte, question) avec avertissement données sensibles ; vérifier par un ticket test
- [ ] 8.3 `support-triage.yml` (`claude-code-action`, `issues: write` seul, sans fermeture) ; vérifier sur 3 tickets test (nouveau, doublon, faille)
- [ ] 8.4 Escalade par label `escalade:<repo>` (Bug + lien + Project) ; vérifier sur un ticket test

## 9. Mémoire LLM (phase B)

- [ ] 9.1 Déclencheur `repository_dispatch` dans `essensys-memory/.github/workflows/brain-sync.yml` ouvrant une PR de synthèse ; vérifier par dispatch manuel
- [ ] 9.2 Protection de branche `main` d'`essensys-memory` (revue requise) ; vérifier le refus d'un push direct du bot
- [ ] 9.3 Émettre les dispatch (archive feature, support résolu, release) ; vérifier une PR mémoire générée pour le pilote
- [ ] 9.4 `essensys-mcp/brain_server.py` : recherche par `Feature ID` ; vérifier par appel MCP local

## 10. Généralisation et décommission (phase B)

- [ ] 10.1 GitHub App `essensys-lifecycle-bot` (permissions D3) et secrets org ; vérifier `gh api /orgs/essensys-hub/installations`
- [ ] 10.2 Propager via bootstrap (`project-sync`, `nonreg`, template PR, schéma v2) aux dépôts actifs ; vérifier `feature-gate` vert en warn
- [ ] 10.3 Passer `FEATURE_GATE_MODE=block` après une semaine sans faux positif ; vérifier qu'une PR sans `Feature:` est bloquée
- [ ] 10.4 Archiver Jira / Xray / Confluence puis supprimer `confluence-sync.yml`, `confluence_sync.py`, `post_security_gate_to_jira.py` et la compat `jira` ; vérifier `grep -rEi 'atlassian|jira|confluence' .github scripts` vide hors archive ; résilier Atlassian
