## Purpose

Montrer si une gateway est présente, proposer l'option « Sonnette » dans les apps quand elle l'est, et recevoir la notification.

## ADDED Requirements

### Requirement: Présence de la gateway dans le portail cloud et les apps
Le portail cloud, Android et iPhone SHALL afficher l'état de la gateway à partir de `gateway_state` : « Gateway en ligne », « Gateway hors ligne » ou « Aucune gateway liée ». Un cloud ou une app qui ne renvoie pas le champ retombe sur le comportement actuel.

#### Scenario: Trois états
- **GIVEN** `gateway_state` valant `online`, `offline`, `none`
- **THEN** le libellé correspondant s'affiche dans chaque client

#### Scenario: Champ absent
- **GIVEN** une réponse sans `gateway_state`
- **THEN** l'affichage actuel (bloc `gateway`) est conservé

### Requirement: Option « Sonnette » dans Android et iPhone
Les apps SHALL afficher dans les réglages une option « Sonnette » seulement si `gateway_state != "none"`. Un interrupteur « Me prévenir quand quelqu'un sonne » demande la permission de notification du système (Android 13 et plus : `POST_NOTIFICATIONS` ; iPhone : autorisation de notification), enregistre l'appareil (`PUT /api/portal/push/devices`) avec `doorbell_notify=true` et le relit à chaque ouverture. Permission refusée : l'interrupteur revient à zéro avec un message renvoyant aux réglages du système. Une phrase d'aide précise que la sonnette doit être activée sur la gateway. À la déconnexion, l'appareil est supprimé (`DELETE`). Un utilisateur sans gateway liée ne voit pas l'option.

#### Scenario: Activation
- **GIVEN** une gateway liée et la permission accordée
- **WHEN** l'utilisateur active l'interrupteur
- **THEN** l'appareil est enregistré avec `doorbell_notify=true` et l'état reste activé après relance

#### Scenario: Permission refusée
- **WHEN** le système refuse la permission
- **THEN** l'interrupteur est désactivé et un message renvoie aux réglages du système

#### Scenario: Sans gateway
- **GIVEN** `gateway_state="none"`
- **THEN** l'option « Sonnette » n'apparaît pas

#### Scenario: Désactivation
- **WHEN** l'utilisateur coupe l'interrupteur
- **THEN** `doorbell_notify=false` est enregistré et les lumières ne sont pas concernées

#### Scenario: Déconnexion
- **WHEN** l'utilisateur se déconnecte
- **THEN** l'appareil est supprimé côté cloud

### Requirement: Réception de la notification
Android (canal `doorbell`, importance haute) et iPhone SHALL afficher la notification « Quelqu'un sonne » et ouvrir l'app (écran d'accueil) au toucher. Deux notifications de même `ring_id` n'en font qu'une. Aucune clé de compte de service ni clé APNs n'est dans une app ; Android ne contient que le fichier de configuration Firebase du projet, fourni à la compilation, et l'iPhone reçoit par APNs sans SDK Firebase.

#### Scenario: Réception app fermée
- **GIVEN** une notification de test (Android émulateur ; iPhone simulateur via `xcrun simctl push`)
- **THEN** la notification s'affiche et ouvre l'app au toucher

#### Scenario: Doublon
- **WHEN** deux messages de même `ring_id` arrivent
- **THEN** une seule notification est visible

### Requirement: Tests
Les tests applicatifs MUST s'exécuter sans armoire réelle ni fournisseur réel (cloud factice) : Playwright (matrice desktop, iPhone, iPad, mode `no-armoire`) pour le portail cloud, émulateur pour Android, simulateur pour iPhone. L'essai réel avec un téléphone physique est consigné par Nicolas.

#### Scenario: Matrice
- **WHEN** les tests Playwright s'exécutent
- **THEN** ils passent avec les trois états de la gateway
