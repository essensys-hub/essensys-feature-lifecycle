## Purpose

Recevoir l'appui de la sonnette envoyé par une gateway et prévenir par notification push les utilisateurs liés à cette gateway qui l'ont demandé ; dire clairement si une gateway est présente.

## ADDED Requirements

### Requirement: Enregistrement des appareils
Le cloud SHALL enregistrer les appareils mobiles dans la table `push_devices` (migration 022) : `PUT /api/portal/push/devices` avec `{"platform","token","app_version","doorbell_notify"}` crée ou met à jour l'appareil de l'utilisateur authentifié (unicité `(platform, token)` : un jeton déjà enregistré passe à l'utilisateur courant). `platform` MUST valoir `android` ou `ios` (`400 invalid_platform`), le jeton MUST être non vide et au plus 4096 caractères (`400 invalid_token`). `DELETE /api/portal/push/devices/{id}` supprime l'appareil de l'utilisateur propriétaire (`204`), tout autre cas `404`. Aucune réponse ni journal ne contient de jeton.

#### Scenario: Enregistrement
- **WHEN** un utilisateur envoie un jeton Android valide
- **THEN** l'appareil existe avec `doorbell_notify` demandé et la réponse ne contient pas le jeton

#### Scenario: Même jeton, autre utilisateur
- **GIVEN** un jeton enregistré par A
- **WHEN** B enregistre le même jeton
- **THEN** l'appareil appartient à B seul

#### Scenario: Suppression d'un appareil d'autrui
- **WHEN** A supprime l'appareil de B
- **THEN** `404` et l'appareil subsiste

#### Scenario: Plateforme invalide
- **WHEN** `platform` vaut `windows`
- **THEN** `400 invalid_platform`

### Requirement: Préférence de notification
`GET /api/portal/doorbell/preferences` SHALL renvoyer `{"available","devices":[{"id","platform","doorbell_notify"}]}` pour l'utilisateur, `available` valant vrai si une gateway est liée (`gateway_state != "none"`). `doorbell_notify` vaut faux par défaut. Aucun jeton n'est renvoyé.

#### Scenario: Sans gateway liée
- **GIVEN** un utilisateur sans gateway liée
- **THEN** `available=false`

#### Scenario: Défaut
- **WHEN** un appareil est enregistré sans `doorbell_notify`
- **THEN** il ne reçoit aucune notification de sonnette

### Requirement: Réception de l'appui
`POST /api/gateway/doorbell/ring` (`GatewayAuth`) SHALL accepter `{"ring_id","at"}`, être idempotent sur `(gateway_id, ring_id)` et répondre `200 {"status":"accepted","recipients":n}` où `n` est le nombre d'appareils notifiés. Au plus un appui par 10 s et par gateway est traité (`429` au-delà). Avec l'en-tête `X-Essensys-Test-Mode: dry-run` : `"status":"dry_run"`, aucun envoi. Un `at` plus de 5 minutes dans le futur est ramené à l'heure du cloud.

#### Scenario: Appui reçu
- **GIVEN** un utilisateur lié à la gateway avec un appareil `doorbell_notify=true`
- **WHEN** la gateway envoie un appui
- **THEN** une notification part vers cet appareil et `recipients=1`

#### Scenario: Idempotence
- **WHEN** le même `ring_id` arrive deux fois
- **THEN** une seule notification est envoyée, les deux réponses sont `200`

#### Scenario: Utilisateur non lié ou préférence coupée
- **THEN** aucune notification pour un utilisateur lié à une autre gateway, ni pour un appareil `doorbell_notify=false`

#### Scenario: Gateway non authentifiée
- **WHEN** le jeton ou la MAC est faux
- **THEN** `401` et aucun traitement

#### Scenario: Essai à blanc
- **WHEN** l'en-tête `dry-run` est présent
- **THEN** `dry_run`, aucun appel à un fournisseur

### Requirement: Expéditeurs push
Le cloud SHALL envoyer les notifications par FCM HTTP v1 (Android) et APNs (iPhone) derrière une interface commune, configurés par variables d'environnement. Contenu : titre « Quelqu'un sonne », corps « Sonnette de votre maison », données `{"type":"doorbell","ring_id","at"}`, priorité haute. Fournisseur non configuré : l'appui est accepté, rien n'est envoyé, un seul message `push_unavailable` est journalisé. Jeton rejeté définitivement par le fournisseur (`UNREGISTERED`, `410`) : l'appareil est supprimé. Une panne d'un fournisseur ne bloque pas l'autre ni la réponse à la gateway.

#### Scenario: Android et iPhone
- **GIVEN** deux appareils (un par plateforme) avec fournisseurs factices
- **THEN** chaque fournisseur reçoit une requête au format attendu avec le titre, le corps et le `ring_id`

#### Scenario: Jeton périmé
- **GIVEN** un fournisseur factice qui répond `UNREGISTERED`
- **THEN** l'appareil est supprimé

#### Scenario: Fournisseur absent
- **GIVEN** aucune variable d'environnement
- **THEN** `200 accepted`, `recipients=0`, un seul message `push_unavailable`

#### Scenario: Fournisseur en panne
- **GIVEN** FCM factice en erreur 500
- **THEN** la notification iPhone part quand même et la gateway reçoit `200`

### Requirement: État de la gateway
`GET /api/portal/session` SHALL ajouter `gateway_state` : `"none"` (aucune gateway liée ou éligible), `"offline"` (dernier contact au-delà de `OnlineTimeout`), `"online"`. Le bloc `gateway` existant est conservé.

#### Scenario: Aucune gateway
- **THEN** `gateway_state="none"`

#### Scenario: En ligne puis hors ligne
- **GIVEN** une gateway liée dont le dernier battement a 30 s
- **THEN** `online` ; à 3 minutes : `offline`

### Requirement: Tests et déploiement
Les tests MUST utiliser des serveurs factices (`httptest`) pour FCM et APNs et ne jamais envoyer de notification réelle. Le test de non-régression `NR-backend-*` cite `#61`. La migration 022 est appliquée sur la base de production avant le code qui en dépend.

#### Scenario: Aucun envoi réel
- **WHEN** la suite de tests s'exécute
- **THEN** aucun appel réseau sortant hors serveurs de test
