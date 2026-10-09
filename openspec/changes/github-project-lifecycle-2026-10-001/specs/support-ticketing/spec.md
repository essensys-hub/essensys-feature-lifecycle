## Purpose

Offre aux utilisateurs et installateurs Essensys un canal de support public et structuré sur GitHub, avec triage assisté par LLM et escalade traçable vers le backlog, sans exposer de données sensibles.

## ADDED Requirements

### Requirement: Dépôt de support public
L'org SHALL disposer d'un dépôt public `essensys-support` avec Discussions activées (catégories Q&A, Idées, Annonces) et des issue forms : panne armoire, installation gateway, portail / compte, question. Les forms SHALL collecter version firmware, carte (SC9xx), mode (gateway local / cloud) et logs, et SHALL afficher un avertissement interdisant d'y coller mots de passe, tokens, adresse postale ou IP publique.

#### Scenario: Ouverture d'un ticket panne
- **WHEN** un utilisateur ouvre le form « panne armoire »
- **THEN** l'issue créée porte le type `Support`, le label `triage` et les champs structurés renseignés

### Requirement: Triage assisté sans fermeture automatique
À l'ouverture d'un ticket, un agent LLM SHALL ajouter des labels (composant, gravité), signaler les doublons probables, chercher les réponses connues dans `essensys-memory` et le site support, et poster une proposition de réponse marquée comme générée. L'agent NE SHALL PAS fermer, verrouiller ni supprimer un ticket.

#### Scenario: Doublon détecté
- **WHEN** un ticket décrit un problème déjà ouvert
- **THEN** l'agent commente avec le lien du ticket existant et ajoute le label `doublon-probable`, le ticket restant ouvert

### Requirement: Escalade vers le backlog
Un mainteneur SHALL pouvoir escalader un ticket confirmé : une issue `Bug` est créée dans le dépôt concerné, rattachée en sub-issue de la Feature existante si elle est identifiée, ajoutée au Project, et le ticket support référence ce Bug.

#### Scenario: Escalade d'un bug portail
- **WHEN** un mainteneur applique le label `escalade:essensys-user-portal-backend`
- **THEN** une issue `Bug` est créée dans ce dépôt, liée au ticket et visible dans le Project

### Requirement: Canal sécurité privé
Les vulnérabilités SHALL être signalées via les Security Advisories privées de GitHub. Un ticket public décrivant une vulnérabilité SHALL être signalé par l'agent de triage aux mainteneurs pour transfert vers une advisory privée.

#### Scenario: Faille postée publiquement
- **WHEN** un ticket public décrit une faille exploitable
- **THEN** l'agent ajoute le label `securite-a-masquer` et notifie les mainteneurs, sans répéter les détails dans son commentaire

### Requirement: Résolution capitalisée
À la fermeture d'un ticket `Support` résolu, un événement SHALL être émis vers `memory-feed` pour proposer une entrée FAQ.

#### Scenario: Ticket résolu
- **WHEN** un mainteneur ferme un ticket avec la raison « completed »
- **THEN** une PR de proposition d'entrée FAQ est ouverte sur `essensys-memory`
