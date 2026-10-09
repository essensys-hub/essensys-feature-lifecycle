## Purpose

Maintient `essensys-memory` comme mémoire distillée et fiable pour les agents LLM, alimentée par les événements GitHub du lifecycle et toujours relue par un humain avant intégration.

## ADDED Requirements

### Requirement: Alimentation événementielle
Les événements suivants SHALL déclencher une proposition de mise à jour de `essensys-memory` : archive d'un change OpenSpec (page concept + entités + ligne de timeline), fermeture « completed » d'un ticket Support (entrée FAQ), publication d'une release (page `wiki/releases/`).

#### Scenario: Feature archivée
- **WHEN** une Feature passe à `Archivé`
- **THEN** une PR est ouverte sur `essensys-memory` mettant à jour `wiki/concepts/`, `wiki/log.md` et la timeline, avec lien vers l'issue Feature

### Requirement: Revue humaine obligatoire
Aucune écriture automatisée NE SHALL être poussée directement sur la branche principale de `essensys-memory` ; toute modification passe par une PR approuvée par un mainteneur.

#### Scenario: Tentative de push direct
- **WHEN** le workflow d'alimentation tente un push sur `main`
- **THEN** la protection de branche le refuse et seule la PR est créée

### Requirement: Mémoire distillée, pas copie
Les entrées de mémoire SHALL résumer décisions, comportements et pièges, avec un lien vers l'issue / PR source, et NE SHALL PAS recopier intégralement les fils d'issues ni contenir de données personnelles ou secrets.

#### Scenario: Ticket contenant des données personnelles
- **WHEN** un ticket résolu contient un nom ou une adresse d'utilisateur
- **THEN** l'entrée FAQ proposée n'en contient aucune trace

### Requirement: Accès agents
`essensys-mcp` SHALL exposer la recherche dans le wiki `essensys-memory` et la lecture des manifests `features/*.json`, et les `AGENTS.md` des dépôts SHALL référencer ce point d'entrée.

#### Scenario: Agent cherchant une feature
- **WHEN** un agent interroge `essensys-mcp` avec un `Feature ID`
- **THEN** il obtient le manifest, l'issue Feature liée et les pages wiki associées
