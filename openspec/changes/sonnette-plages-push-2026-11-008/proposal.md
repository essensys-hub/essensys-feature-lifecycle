> Ticket : [essensys-hub/essensys-feature-lifecycle#61](https://github.com/essensys-hub/essensys-feature-lifecycle/issues/61). Feature ID : `sonnette-plages-push-2026-11-008`. Prolonge `sonnette-unifi-2026-11-007` (#58).
> Feature répartie sur la gateway CM5 (backend et portail local), le cloud (backend et portail), Ansible, Android, iPhone, le site support, la documentation et la mémoire. Ce change commun décrit tout le code ; il vit dans `essensys-feature-lifecycle`.

## Why

La sonnette UniFi (#58) clignote à toute heure et ne prévient que sur le réseau de la maison. Trois manques : choisir quand elle est active (pas la nuit), être prévenu sur le téléphone même hors du Wi-Fi, et savoir si une gateway est présente côté cloud et dans les apps. Aucune notification push n'existe aujourd'hui dans les apps ni dans le cloud (seul l'e-mail SMTP).

## What Changes

- **Gateway (backend)** : une grille de plages horaires (7 jours × 24 heures, fuseau réglable) dans la section `doorbell` du même fichier que les noms. Hors plage, un appui ne fait ni clignoter les lumières ni prévenir le cloud. Dans la plage, la gateway signale l'appui au cloud (`POST /api/gateway/doorbell/ring`, `GatewayAuth`), sans bloquer le clignotement.
- **Portail local (frontend)** : éditeur de la grille dans l'écran « Sonnette » (administrateur), présélections, indication « dans la plage maintenant ».
- **Cloud (backend)** : enregistrement des appareils mobiles (jeton push), préférence « me prévenir de la sonnette » par appareil, réception de l'appui, envoi des notifications (FCM pour Android, APNs pour iPhone), état de présence de la gateway précisé (`gateway_state`). Migration 022.
- **Portail cloud (frontend)** : afficher explicitement « Aucune gateway liée » ou son état (en ligne, hors ligne).
- **Ansible** : secrets des fournisseurs de notification (SOPS) transmis au backend cloud.
- **Android et iPhone** : demande de permission de notification, enregistrement de l'appareil, interrupteur « Sonnette » (visible seulement si une gateway est liée), réception et ouverture sur l'appui.
- **Site support, documentation, mémoire** : page `/android` (nouvelle version), page d'usage, synthèse.
- **Livraison** : cloud de production, gateway CM5, portail local, nouvelle version Android (APK) et nouveau build iPhone.

## Capabilities

### New Capabilities

- `doorbell-schedule-gateway` : grille horaire, évaluation à l'appui, signalement au cloud.
- `doorbell-push-cloud` : appareils, préférences, réception de l'appui, envoi des notifications, état de la gateway.
- `doorbell-clients` : portail cloud, Android et iPhone (permission, interrupteur, présence, réception).

### Modified Capabilities

Aucune dans les specs publiées. `doorbell-gateway` et `doorbell-portal` (#58) restent valables : les réglages et routes de #58 gagnent un champ `schedule` (compatible) ; sans plage définie, le comportement de #58 est inchangé (toujours actif).

## Impact

- **essensys-server-backend** (V.1.3.0) : section `schedule`, évaluation, client cloud pour l'appui ; **essensys-server-frontend** (V.1.3.0) : éditeur de grille.
- **essensys-user-portal-backend** : migration 022, routes `/api/portal/push/*`, `/api/portal/doorbell/preferences`, `/api/gateway/doorbell/ring`, expéditeurs FCM et APNs, `gateway_state` dans `GET /api/portal/session` ; **essensys-user-portal-frontend** : affichage de la gateway.
- **essensys-ansible** : variables et secrets des notifications.
- **essensys-android-phone-apps**, **essensys-ios-phone-apps** : permission, enregistrement, réglage, réception.
- **essensys-support-site** (page `/android`), **essensys-doc**, **essensys-memory**.
- **Non concernés** : Raspberry Pi, firmware.
- **Legacy IoT** : aucun endpoint `serverinfos`, `mystatus`, `myactions` ni `done` n'est modifié ; aucune écriture dans l'armoire.
- **Prérequis hors code** : un projet Firebase (compte de service) et une clé Apple APNs, fournis par Nicolas via SOPS. Sans eux, le cloud accepte l'appui et n'envoie rien (fournisseur désactivé).
- **Hors périmètre** : vidéo dans les apps ou dans la notification, réponse audio, historique des appuis, plusieurs sonnettes, sélecteur d'armoire, notifications autres que la sonnette.
