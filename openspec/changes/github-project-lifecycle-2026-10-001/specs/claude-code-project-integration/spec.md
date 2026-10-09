## Purpose

Permet à Claude Code (CLI, desktop, sessions cloud et GitHub Actions) de lire et d'écrire dans le GitHub Project Essensys pour gérer tickets, features et campagnes de non-régression sans quitter la session.

## ADDED Requirements

### Requirement: Accès Project depuis Claude Code
Une session Claude Code ouverte dans l'espace ESSENSYS SHALL pouvoir lister, créer et mettre à jour des items du Project (champs `Status`, `Feature ID`, `Phase`, `Cible`, `Appareil`), créer des issues typées et des sub-issues, via le GitHub MCP server (toolset `projects` activé) ou `gh` authentifié avec le scope `project`. Le setup SHALL être documenté et vérifiable par une commande unique.

#### Scenario: Vérification du setup
- **WHEN** le développeur exécute le script de vérification du setup
- **THEN** il obtient « OK » si `gh project list --owner essensys-hub` et l'appel MCP de lecture du Project réussissent, sinon la commande exacte de correction (ex. `gh auth refresh -s project`)

### Requirement: Commande /ticket
Claude Code SHALL fournir une commande `/ticket` qui, à partir d'une description libre, cherche les doublons, propose type (`Bug`, `Task`, `Support`), dépôt cible, `Feature ID` et champs, puis crée l'issue et l'ajoute au Project après confirmation de l'utilisateur.

#### Scenario: Création d'un bug
- **WHEN** l'utilisateur lance `/ticket les volets cuisine ne remontent plus depuis le portail`
- **THEN** Claude Code affiche les doublons trouvés et la proposition, et ne crée l'issue `Bug` qu'après validation

### Requirement: Toute modification passe par un ticket
Toute modification du projet Essensys (code, infra, doc produit) SHALL être rattachée à une issue du Project #6. Claude Code SHALL, avant de modifier un dépôt Essensys, identifier l'issue concernée ou proposer d'en créer une via `/ticket` ; les commits et PR SHALL référencer cette issue.

#### Scenario: Demande de modification sans ticket
- **WHEN** l'utilisateur demande à Claude Code une modification de code sans mentionner d'issue
- **THEN** Claude Code cherche une issue correspondante dans le Project et, à défaut, propose `/ticket` avant de modifier quoi que ce soit

### Requirement: Du ticket à l'OpenSpec
Claude Code SHALL fournir `/ticket-to-spec <issue>` qui, pour une issue nécessitant une évolution (Feature ou Bug non trivial), génère le change OpenSpec dans le dépôt concerné, le manifest `features/<id>.json` avec bloc `github`, renseigne `Feature ID` dans le Project, passe l'issue en type `Feature` si besoin et crée une sub-issue `Task` par groupe de tâches. Un correctif trivial (une PR, pas de changement de comportement spécifié) SHALL pouvoir être traité sans OpenSpec, la décision étant tracée en commentaire de l'issue.

#### Scenario: Ticket utilisateur nécessitant une évolution
- **WHEN** l'utilisateur lance `/ticket-to-spec essensys-hub/essensys-android-phone-apps#12`
- **THEN** un change OpenSpec et un manifest sont créés, l'item Project reçoit le `Feature ID` et passe à `Spec`, et les sub-issues sont créées après confirmation

### Requirement: Commande /checkup
Claude Code SHALL fournir `/checkup [<Feature ID>|<repo>]` qui vérifie, pour la feature ou le dépôt : build, lint, tests unitaires, tests de non-régression, tests applicatifs (Playwright pour le web, émulateur Android / simulateur iOS pour le mobile), gates (`feature-gate`, `security-gate`), et publie la synthèse en commentaire de l'issue Feature.

#### Scenario: Checkup de l'app Android
- **WHEN** l'utilisateur lance `/checkup essensys-android-phone-apps`
- **THEN** Claude Code exécute build, lint, tests unitaires Gradle et tests instrumentés sur émulateur, capture des écrans clés, et poste un rapport OK/KO par étape sur l'issue liée

### Requirement: Commande /feature-status
Claude Code SHALL fournir `/feature-status [<Feature ID>]` qui affiche, pour une feature ou pour toutes les features actives, le statut Project, les sub-issues ouvertes, les PR liées, l'état des gates et le dernier résultat de non-régression.

#### Scenario: Statut d'une feature
- **WHEN** l'utilisateur lance `/feature-status temporary-password-2026-09-040`
- **THEN** Claude Code affiche statut, sub-issues, PR et gates issus du Project et de la CI

### Requirement: Mise à jour du Project pendant le travail
Les skills OpenSpec (`propose`, `apply`, `archive`) exécutés dans Claude Code SHALL refléter leur effet dans le Project : création de la Feature et des sub-issues à la proposition, cochage / fermeture des sub-issues à l'implémentation, passage à `Archivé` à l'archive. Les transitions de statut gérées par la CI (D4) NE SHALL PAS être forcées manuellement par l'agent.

#### Scenario: Tâche terminée dans apply
- **WHEN** `opsx:apply` coche la tâche correspondant à une sub-issue
- **THEN** la sub-issue est fermée avec un commentaire référençant le commit

### Requirement: Garde-fous d'écriture
Claude Code NE SHALL PAS supprimer d'items ou d'issues, ni modifier les champs ou vues du Project, et SHALL demander confirmation avant toute création ou fermeture d'issue initiée en session interactive.

#### Scenario: Demande de suppression
- **WHEN** l'utilisateur demande à Claude Code de supprimer une issue
- **THEN** Claude Code propose de la fermer avec une raison, sans la supprimer
