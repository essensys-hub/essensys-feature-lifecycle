## Purpose

Encadre la remise à zéro des tickets au démarrage du lifecycle GitHub Project et la décommission ordonnée de Jira, Xray et Confluence sans perte d'historique.

## ADDED Requirements

### Requirement: Remise à zéro au 2026-10-09
Les tickets existants au 2026-10-09 (Jira SCRUM et Projects GitHub #1–#6) NE SHALL PAS être migrés comme travail en cours : ils SHALL être passés à `Done` dans leur outil d'origine, et la production du nouveau lifecycle démarre à vide dans le Project #6. Un besoin encore pertinent SHALL être recréé via `/ticket`.

#### Scenario: Ancien ticket encore pertinent
- **WHEN** un mainteneur constate qu'un ancien ticket passé à `Done` reste d'actualité
- **THEN** il crée un nouveau ticket via `/ticket` en référençant l'ancien, plutôt que de rouvrir l'ancien

### Requirement: Archive de l'historique
Avant décommission, un export complet (Jira JSON, campagnes Xray, espace Confluence) SHALL être archivé dans `essensys-feature-lifecycle` (ou release asset) en format ouvert.

#### Scenario: Consultation d'un ancien ticket
- **WHEN** un contributeur cherche la clé `SCRUM-123` après décommission
- **THEN** il la retrouve dans l'archive versionnée

### Requirement: Décommission
Après bascule, aucun workflow, script ou skill Essensys NE SHALL appeler les API Jira, Xray ou Confluence.

#### Scenario: Recherche de références résiduelles
- **WHEN** on recherche `atlassian`, `jira` ou `confluence` dans les workflows et scripts actifs
- **THEN** seules l'archive et la documentation historique correspondent
