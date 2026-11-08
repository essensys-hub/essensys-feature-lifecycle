## Context

#58 a posé la sonnette sur la CM5 : événement UniFi (flux `ring` confirmé sur la console réelle le 2026-11-08), service `doorbell`, réglages dans la section `doorbell` du fichier `light_names.path`, routes `/api/doorbell/*` et `/api/admin/doorbell/*`. Cette Feature ajoute des plages horaires, un signalement au cloud et des notifications push, et clarifie la présence de la gateway.

Déjà en place côté cloud (constaté dans le code) : table `gateway_sessions` (`gateway_id`, `token_hash`, `machine_id`, `last_seen`), lien utilisateur → gateway (`linked_gateway_id`, `linked_machine_id`), `GatewayAuth` (jeton + MAC), `POST /api/gateway/heartbeat`, `GET /api/portal/gateway/status` (`{"online":bool}`, hors ligne après 2 minutes), `GET /api/portal/session` avec un bloc `gateway` seulement si la gateway est liée et éligible. Absent : tout enregistrement d'appareil mobile et tout envoi push. Dernière migration : 021.

## Décisions

1. **La gateway décide, le cloud relaie.** La plage est évaluée sur la CM5 à l'instant de l'appui (heure de l'événement UniFi). Le cloud ne connaît pas la grille et ne la synchronise pas : il envoie une notification pour chaque appui qu'il reçoit.
2. **Grille** : section `doorbell.schedule` du même fichier (aucune nouvelle clé de chemin) : `{"mode":"always"|"custom","timezone":"Europe/Paris","grid":["<24 caractères 0/1>" × 7]}`. `grid[0]` = lundi, `grid[6]` = dimanche ; le caractère `h` = heure locale `h` à `h+1`, `1` = active. Défaut : `mode=always` (comportement de #58 inchangé), fuseau `Europe/Paris`. `mode=custom` avec une grille vide de `1` : la sonnette ne réagit jamais (valide, affiché comme tel).
3. **Fuseau explicite** : le conteneur tourne en UTC. Le fuseau est un réglage (nom IANA validé par `time.LoadLocation`), la base de fuseaux est embarquée dans le binaire (`time/tzdata`). Changement d'heure géré par la bibliothèque.
4. **Hors plage** : ni clignotement, ni signalement au cloud. L'état local `ringing` et la fenêtre vidéo du portail local restent actifs (quelqu'un à la maison veut voir qui sonne) ; l'état expose `in_window` (booléen). Le bouton « Essayer » (dry-run, #58) ignore la plage. La plage n'arme pas l'anti-rafale de 30 s quand elle bloque.
5. **Signalement** : `POST /api/gateway/doorbell/ring` (`GatewayAuth`), corps `{"ring_id":"<id UniFi de l'événement ou UUID>","at":"2026-11-08T10:15:30.123Z"}`. Idempotent sur `(gateway_id, ring_id)` : un deuxième envoi répond 200 sans renvoyer de notification. Réponse `200 {"status":"accepted","recipients":n}`. La gateway tente 3 fois (attente 1 s, 3 s) en tâche de fond, abandonne après 60 s (une sonnerie ancienne ne sert plus), ne bloque jamais le clignotement et ne journalise ni jeton ni adresse.
6. **Destinataires** : les utilisateurs dont `linked_gateway_id` est la gateway appelante, qui ont au moins un appareil actif avec `doorbell_notify=true`. Défaut `false` (opt-in explicite par appareil).
7. **Appareils** (table `push_devices`, migration 022) : `id`, `user_id`, `platform` (`android`|`ios`), `token`, `app_version`, `doorbell_notify`, `created_at`, `updated_at`, `last_seen`, unicité `(platform, token)` (un jeton re-enregistré par un autre utilisateur passe à ce dernier). Jeton refusé par le fournisseur (`UNREGISTERED`, `410`) : l'appareil est supprimé. Le jeton n'est jamais journalisé ni renvoyé en lecture.
8. **Deux expéditeurs derrière une interface `PushSender`** : FCM HTTP v1 pour Android (compte de service), APNs avec clé `.p8` (HTTP/2, identifiants clé, équipe, `bundle id` `essensys.essensys-iphone`) pour l'iPhone. Configuration par variables d'environnement du backend cloud ; si elles manquent, l'expéditeur est désactivé : l'appui est accepté, aucune notification, un état `push_unavailable` est journalisé une fois (jamais d'erreur côté gateway). Contenu : titre « Quelqu'un sonne », corps « Sonnette de votre maison » (sans nom d'armoire ni image), données `{"type":"doorbell","ring_id","at"}`, repli `ring_id` pour dédoublonner côté appareil, priorité haute (Android canal `doorbell`, importance haute ; iPhone `time-sensitive` non requis, niveau actif par défaut).
9. **Droits** : enregistrement et préférence par tout utilisateur authentifié sur son propre compte ; aucune route ne lit les jetons d'autrui. L'administrateur de l'armoire règle la grille (gateway, `lan_admin`).
10. **Présence de la gateway** : `GET /api/portal/session` ajoute `gateway_state` : `"none"` (aucune gateway liée ou éligible), `"offline"`, `"online"` (reprend `OnlineTimeout`). Le bloc `gateway` existant est conservé (compatibilité). Les clients affichent « Aucune gateway liée » quand `gateway_state="none"`. Une app plus ancienne ignore le champ.
11. **Option « Sonnette » des apps** : visible seulement si `gateway_state != "none"`. L'interrupteur gère la permission du système (Android 13+ `POST_NOTIFICATIONS`, iPhone `requestAuthorization`), enregistre l'appareil et pose `doorbell_notify`. Refus de la permission : interrupteur remis à zéro avec un message qui renvoie aux réglages du système. Déconnexion : l'appareil est supprimé côté cloud.
12. **Aucune écriture dans l'armoire**, aucun legacy touché. Tests avec expéditeurs factices (serveurs `httptest`), jamais de notification réelle en test automatique.

## Contrat d'API (figé : tous les dépôts le suivent)

**Gateway (extension de #58)**

`GET/PUT /api/admin/doorbell/settings` : le corps gagne

```json
{"schedule":{"mode":"custom","timezone":"Europe/Paris","grid":["000000011111111111111100","…6 autres chaînes de 24 caractères…"]}}
```

`GET /api/doorbell/status` gagne `"in_window": true`. Erreurs : `400 {"error":"invalid_schedule"}` (mode inconnu, fuseau inconnu, grille qui n'a pas 7 chaînes de 24 caractères `0`/`1`). Un fichier sans `schedule` se lit comme `mode=always`.

**Cloud**

| Route | Droits | Corps → réponse |
|---|---|---|
| `POST /api/gateway/doorbell/ring` | `GatewayAuth` | `{"ring_id","at"}` → `200 {"status":"accepted","recipients":n}` ; `X-Essensys-Test-Mode: dry-run` → `"status":"dry_run"`, aucun envoi |
| `PUT /api/portal/push/devices` | utilisateur | `{"platform","token","app_version","doorbell_notify"}` → `200 {"id","platform","doorbell_notify"}` |
| `DELETE /api/portal/push/devices/{id}` | utilisateur propriétaire | `204` ; autre utilisateur ou inconnu : `404` |
| `GET /api/portal/doorbell/preferences` | utilisateur | `200 {"available":bool,"devices":[{"id","platform","doorbell_notify"}]}` (`available` = `gateway_state != "none"` ; jamais de jeton) |
| `GET /api/portal/session` | utilisateur | gagne `"gateway_state":"none"|"offline"|"online"` |

Erreurs : `400 {"error":"invalid_platform"}`, `{"error":"invalid_token"}` (vide ou plus de 4096 caractères), `401`, `404`, `429` sur le ring (plus d'un appui par 10 s et par gateway ; la gateway n'insiste pas).

## Risques et inconnus

- **Fournisseurs** : sans compte Firebase ni clé APNs fournis par Nicolas, aucune notification réelle. Le simulateur iPhone ne reçoit pas d'APNs réelles (test par `xcrun simctl push`) ; l'essai réel se fait sur un iPhone et un Android physiques.
- **Appareil éteint ou économie d'énergie** : la livraison push n'est pas garantie ; la notification ne remplace pas la sonnette physique. Documenté.
- **Réseau cloud coupé** : l'appui est abandonné après 60 s (pas de notification tardive) ; le clignotement local n'est jamais retardé.
- **Gateway sans sonnette configurée** : l'option « Sonnette » apparaît quand même (la présence suffit, choix du ticket) ; la notification n'arrive que si la sonnette est activée sur la gateway. Le texte d'aide de l'app le dit.
- **Une armoire par compte** : sélecteur d'armoire hors périmètre.
- **Horloge et fuseau** : un fuseau faux décale la plage ; le fuseau est affiché dans l'éditeur avec l'heure locale actuelle.
