## Purpose

Permettre à l'administrateur de choisir quand la sonnette est active (clignotement et notification) et signaler les appuis valides au cloud.

## ADDED Requirements

### Requirement: Grille de plages horaires
La gateway SHALL enregistrer dans la section `doorbell.schedule` du fichier des noms (`light_names.path`, aucune nouvelle clé de chemin) un mode (`always` ou `custom`), un fuseau IANA et une grille de 7 chaînes de 24 caractères `0`/`1` (lundi en premier, caractère `h` = heure locale `h` à `h+1`). Sans section, le mode vaut `always` et le fuseau `Europe/Paris`. `PUT /api/admin/doorbell/settings` MUST refuser avec `400 {"error":"invalid_schedule"}` un mode inconnu, un fuseau inconnu ou une grille mal formée, et conserver les autres sections du fichier.

#### Scenario: Valeurs par défaut
- **GIVEN** un fichier sans `schedule`
- **WHEN** l'administrateur lit les réglages
- **THEN** `mode=always`, fuseau `Europe/Paris`, grille entièrement active

#### Scenario: Enregistrement et relecture
- **WHEN** l'administrateur enregistre une grille valide puis la gateway redémarre
- **THEN** la même grille est relue et les noms, volets et disposition du fichier sont inchangés

#### Scenario: Grille invalide
- **WHEN** la grille a 6 lignes, ou une ligne de 23 caractères, ou un caractère `2`
- **THEN** réponse `400 invalid_schedule` et aucun changement

#### Scenario: Fuseau inconnu
- **WHEN** le fuseau est `Mars/Olympus`
- **THEN** réponse `400 invalid_schedule`

### Requirement: Évaluation de la plage à l'appui
À chaque appui, le service sonnette SHALL convertir l'heure de l'événement dans le fuseau réglé et lire la case correspondante. Case active (ou `mode=always`) : comportement de #58 (clignotement) et signalement au cloud. Case inactive : ni clignotement, ni signalement, et l'anti-rafale n'est pas armé. L'état local `ringing` et la vidéo du portail local restent actifs ; `GET /api/doorbell/status` MUST exposer `in_window`. « Essayer » ignore la plage.

#### Scenario: Dans la plage
- **GIVEN** une case active pour mardi 14 h
- **WHEN** l'appui a lieu mardi 14 h 05 (heure locale)
- **THEN** les lumières clignotent et le cloud est prévenu

#### Scenario: Hors plage
- **GIVEN** une case inactive pour mardi 3 h
- **WHEN** l'appui a lieu mardi 3 h 10
- **THEN** aucune lumière ne clignote, aucun appel au cloud, `ringing=true`, `in_window=false`

#### Scenario: Changement d'heure
- **GIVEN** le fuseau `Europe/Paris` et le passage à l'heure d'été
- **WHEN** l'appui a lieu à 2 h 30 locale le jour du changement
- **THEN** la case évaluée est celle de l'heure locale réelle (pas de décalage d'une heure)

#### Scenario: Mode toujours
- **GIVEN** `mode=always` et une grille quelconque
- **THEN** la grille est ignorée

#### Scenario: Essai
- **GIVEN** une case inactive
- **WHEN** l'administrateur lance « Essayer »
- **THEN** la séquence s'exécute à sec comme dans #58

### Requirement: Signalement au cloud
Dans la plage, la gateway SHALL envoyer `POST /api/gateway/doorbell/ring` (`GatewayAuth` : jeton, identifiant et MAC de la configuration cloud) avec `{"ring_id","at"}`, en tâche de fond : 3 tentatives (attentes 1 s puis 3 s), abandon après 60 s, sans jamais retarder le clignotement. Aucun jeton ni adresse n'est journalisé. Cloud non configuré ou désactivé : aucun envoi, aucune erreur.

#### Scenario: Cloud joignable
- **WHEN** un appui valide a lieu
- **THEN** un seul appel part avec le `ring_id` de l'événement

#### Scenario: Cloud injoignable
- **GIVEN** un cloud qui ne répond pas
- **WHEN** un appui valide a lieu
- **THEN** le clignotement démarre sans attente, trois tentatives échouent, l'envoi est abandonné après 60 s et aucun jeton n'apparaît dans les journaux

#### Scenario: Cloud non configuré
- **GIVEN** aucune configuration cloud
- **THEN** aucun appel et aucun message d'erreur

#### Scenario: Rafale
- **WHEN** deux appuis ont lieu en moins de 30 s
- **THEN** un seul signalement part (même règle que le clignotement)

### Requirement: Droits et audit
L'écriture de la grille MUST être réservée à `lan_admin` (ouverte si l'IAM LAN est désactivé), lecture pour tout utilisateur authentifié sauf `updated_by`. Chaque changement est tracé dans l'audit (`doorbell_schedule`). Aucune écriture dans l'armoire. Les tests s'exécutent sans armoire réelle.

#### Scenario: Utilisateur LAN
- **WHEN** un `lan_user` envoie `PUT` des réglages
- **THEN** réponse `403`

#### Scenario: Aucune armoire
- **WHEN** les tests tournent avec `NO_ARMOIRE=1`
- **THEN** aucune commande ne part vers une armoire
