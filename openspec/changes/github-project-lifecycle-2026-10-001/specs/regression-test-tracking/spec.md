## Purpose

Garantit qu'aucune régression déjà corrigée ne revient sans être détectée : une suite de non-régression identifiée, exécutée en continu, dont les échecs sont automatiquement tracés comme `Bug` dans le GitHub Project.

## ADDED Requirements

### Requirement: Suite de non-régression identifiée
Chaque test de non-régression SHALL porter un identifiant stable `NR-<repo>-<n>` et une référence à l'issue d'origine (`Bug` ou `Feature`), sous forme d'annotation/tag (Go : nom ou commentaire de test ; Playwright : tag `@nr` + annotation ; Python : marqueur). La suite SHALL couvrir au minimum `go test ./...` des backends jumeaux, `test/test_chb3.py`, les tests Playwright UX matrix en mode `no-armoire`, et pour les apps mobiles les tests unitaires Gradle (JUnit) et instrumentés (émulateur) d'`essensys-android-phone-apps`. Le rapporteur SHALL accepter les formats JUnit XML (Go via gotestsum, Gradle, pytest) et JSON Playwright.

#### Scenario: Test sans référence
- **WHEN** un test est tagué `@nr` sans référence d'issue
- **THEN** la gate de non-régression échoue en le signalant

### Requirement: Correction de bug = test de non-régression
Une PR qui ferme une issue de type `Bug` SHALL ajouter ou modifier au moins un test de non-régression référençant ce Bug, sauf label `nr-exempt` justifié en commentaire.

#### Scenario: Fix sans test
- **WHEN** une PR `Closes #<bug>` ne contient aucun test tagué référençant ce Bug
- **THEN** le check `feature-gate` échoue avec un message demandant un test de non-régression

### Requirement: Exécution continue
La suite SHALL s'exécuter sur chaque PR (sous-ensemble des dépôts touchés) et chaque nuit sur l'ensemble, sans jamais piloter une armoire réelle (`no-armoire`). Les rapports SHALL être archivés via `e2e-reports-archive`.

#### Scenario: Nightly
- **WHEN** la campagne nocturne se termine
- **THEN** un rapport consolidé (passés / échoués / flaky par `NR-*`) est archivé et accessible depuis le Project

### Requirement: Échec tracé dans le Project
Un échec de test `NR-*` sur la branche principale ou en nightly SHALL ouvrir une issue `Bug` (label `regression`, `Status` = Idée, lien vers le rapport et l'issue d'origine) ou, si un Bug ouvert existe déjà pour ce `NR-*`, y ajouter un commentaire. Un test revenu au vert pendant 3 nightlies consécutives SHALL déclencher un commentaire proposant la fermeture, sans fermeture automatique.

#### Scenario: Régression récurrente
- **WHEN** `NR-server-backend-12` échoue deux nuits de suite
- **THEN** une seule issue `Bug` existe, avec deux commentaires d'échec

### Requirement: Vue non-régression
Le Project SHALL fournir une vue « Non-régression » listant les Bugs `regression` ouverts et le dernier état de la campagne, consultable aussi par la commande Claude Code `/nonreg`.

#### Scenario: Consultation depuis Claude Code
- **WHEN** l'utilisateur lance `/nonreg`
- **THEN** Claude Code affiche le dernier rapport nightly et les Bugs `regression` ouverts, et propose de lancer la suite locale sur les dépôts modifiés
