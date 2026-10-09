## Purpose

Garantit que le manifest `features/<id>.json`, les pull requests, les gates CI et les déploiements tiennent le GitHub Project à jour automatiquement, sans double saisie, le manifest restant la source de vérité consommée par la CI.

## ADDED Requirements

### Requirement: Bloc github dans le manifest
Le schéma de manifest SHALL remplacer les blocs `jira` et `confluence` par un bloc obligatoire `github` contenant `issue` (référence `essensys-hub/<repo>#<n>` de l'issue Feature) et `project_item` (ID de l'item Project, nullable avant création). Un manifest contenant encore `jira` ou `confluence` SHALL être rejeté par `validate_feature_manifests.py` après la date de bascule.

#### Scenario: Manifest legacy après bascule
- **WHEN** un manifest contient un bloc `jira` et que la validation s'exécute après la date de bascule
- **THEN** la validation échoue avec un message indiquant de migrer vers le bloc `github`

#### Scenario: Manifest conforme
- **WHEN** un manifest déclare `github.issue = "essensys-hub/essensys-feature-lifecycle#42"`
- **THEN** la validation réussit et la gate peut résoudre l'issue Feature

### Requirement: Liaison PR obligatoire
Toute PR vers une branche protégée d'un dépôt Essensys SHALL contenir une ligne `Feature: <id>` correspondant à un manifest existant et au moins une référence `Closes #<n>` ou `Refs #<n>` vers une issue présente dans le Project. Les PR Dependabot et les PR étiquetées `chore/no-feature` SHALL être exemptées.

#### Scenario: PR sans référence
- **WHEN** une PR est ouverte sans ligne `Feature:`
- **THEN** le check `feature-gate` échoue et commente la PR avec le format attendu

#### Scenario: PR Dependabot
- **WHEN** Dependabot ouvre une PR de mise à jour
- **THEN** le check `feature-gate` passe sans exiger de `Feature:`

### Requirement: Transitions de statut automatiques
Le `Status` de l'item Feature SHALL évoluer automatiquement selon les événements : création du change OpenSpec → `Spec` ; tâches OpenSpec complètes et sub-issues créées → `Prêt` ; première PR liée ouverte → `En cours` ; toutes les PR liées mergées → `Test` ; checks E2E/UX verts → `Gate sécu` ; `security-gate` vert et déploiement local + OVH réussi → `Déployé` ; archive OpenSpec → `Archivé`. Un statut ne SHALL jamais régresser automatiquement ; seul un humain peut le faire reculer.

#### Scenario: Merge de la dernière PR
- **WHEN** la dernière PR liée à la Feature `x-2026-10-001` est mergée
- **THEN** l'item Feature passe à `Test` dans le Project

#### Scenario: Gate sécurité en échec
- **WHEN** `security-gate` échoue sur une PR liée
- **THEN** le statut ne change pas et l'item apparaît dans la vue « Gate sécu en échec »

### Requirement: Preuves de test liées à l'issue
Les résultats des campagnes de test (unit, intégration, E2E, matrice UX) SHALL être publiés comme checks de PR et archivés par `e2e-reports-archive`, avec un commentaire de synthèse sur l'issue Feature contenant le lien vers l'archive.

#### Scenario: Campagne E2E terminée
- **WHEN** le workflow E2E d'une PR liée se termine
- **THEN** l'issue Feature reçoit un commentaire avec le résultat et le lien vers le rapport archivé
