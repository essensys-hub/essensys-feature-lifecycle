# E2E sonnette-plages-push-2026-11-008 (#61, tâche 11.1)

Test de bout en bout de la chaîne **appui de sonnette → plage horaire → signalement au cloud → notification push**, sans armoire réelle (`NO_ARMOIRE=1`) et sans aucun appel réseau sortant.

```bash
e2e/sonnette-plages-push/run.sh          # code 0 = vert
KEEP=1 LOGDIR=/chemin/logs e2e/sonnette-plages-push/run.sh
```

Prérequis : `git`, `go`, un PostgreSQL local (`initdb`, `pg_ctl`, `createdb` ; `PG_BIN=` si hors `PATH`), les dépôts `essensys-server-backend`, `essensys-user-portal-backend` et les dépôts voisins de la gateway (`essensys-audit-collector`, `essensys-plugin-framework`, `essensys-plugin-sungrow`) sous `ESSENSYS_ROOT` (défaut `~/ESSENSYS`). Variables : `GATEWAY_REPO`, `CLOUD_REPO`, `GATEWAY_REF`, `CLOUD_REF` (défaut : branche `feat/sonnette-plages-push-2026-11-008`).

## Fonctionnement

`run.sh` extrait les deux dépôts avec `git archive` (aucune écriture dans les dépôts, ni stash ni checkout), copie un fichier de test dans `internal/e2e/` de chacun (les paquets `internal` ne sont pas importables d'un autre module), démarre un PostgreSQL jetable (socket Unix, `listen_addresses` vide), puis lance deux phases (`GOPROXY=off`) :

1. **gateway** (`gateway/e2e_gateway_test.go`) : vrai code gateway câblé comme `cmd/server/main.go` (flux d'événements UniFi par WebSocket, `DoorbellService`, routes `/api/doorbell/*` et `/api/admin/doorbell/*`, agent cloud). Faux : console UniFi (WebSocket TLS local), cloud (HTTPS local), armoire (client qui interroge `GET /api/myactions`). La requête réellement émise vers le cloud est écrite dans `ring-requests.json`.
2. **cloud** (`cloud/e2e_cloud_test.go`) : vrai routeur cloud, migrations 001 à 022 sur le vrai PostgreSQL, authentification de la gateway, `PUT /api/portal/push/devices`. Faux : FCM et APNs (serveurs `httptest`). Il **rejoue la requête capturée en phase 1** : c'est le lien entre les deux phases.

Les deux modules ne peuvent pas tourner dans un même processus (paquets `internal`, hub en HTTPS obligatoire côté gateway, points d'accès FCM/APNs non configurables par variable d'environnement côté cloud).

## Scénarios et assertions

| # | Phase | Assertions |
|---|---|---|
| 1 | gateway + cloud | appui dans la plage : l'armoire factice voit `606=128, 612=128` ×3 (salon, 3 clignotements) ; 1 POST `/api/gateway/doorbell/ring` avec jeton, `X-Gateway-ID`, MAC, corps `{ring_id, at}` ; le cloud répond `accepted`, `recipients=2` ; FCM (titre « Quelqu'un sonne », `data.ring_id`, `data.at`, `android.notification.tag` = `ring_id`, canal `doorbell`, priorité haute) ; APNs (titre, `ring_id`, `at`, `apns-collapse-id` = `ring_id`, topic, priorité 10) |
| 2 | gateway | hors plage (case inactive, puis grille « jamais ») : 0 ordre, 0 appel cloud, `GET /api/doorbell/status` → `ringing=true`, `in_window=false` |
| 3 | gateway + cloud | « add » + « update » du même événement UniFi → 1 seul POST ; même `ring_id` renvoyé au cloud → `recipients=0`, FCM/APNs inchangés, 1 ligne `doorbell_rings` |
| 4 | gateway | cloud en 502 : séquence complète en quelques dizaines de ms (avant la 2e tentative), 3 tentatives espacées de ~1 s puis ~3 s, abandon journalisé, rien d'autre |
| 5 | cloud | `doorbell_notify=false`, utilisateur lié à une autre gateway, utilisateur sans gateway : `recipients=0`, aucun appel fournisseur ; avec un utilisateur éligible en plus : seul son jeton est notifié |
| 6 | cloud | `gateway_state` de `GET /api/portal/session` : `none`, `online` (après `POST /api/gateway/heartbeat`), `offline` (silence de 5 min) |
| 7 | les deux | aucune valeur secrète (jetons gateway, clé UniFi, jetons d'appareil, JWT, clé APNs, MAC) dans les journaux ; `run.sh` refait la recherche (`grep -F`) sur les 4 journaux |

Complément : la migration 022 est rejouable (elle l'est à chaque démarrage du cloud).

## Choix de conception

- L'instant de l'essai est fixe (mardi 2026-11-03, 10 h 30 à Paris) et l'horloge du service est injectée : le test ne dépend pas de l'heure réelle. Il est dans le passé car le cloud ramène à son horloge un `at` postérieur de plus de 5 minutes.
- Le cloud limite à un appui par 10 s et par gateway (horloge réelle) : chaque scénario a donc son propre routeur.
- Les valeurs « secrètes » sont toutes factices (`e2e-…-not-a-real-secret`). Aucune adresse LAN ni secret réel dans ce dossier.
- Le scénario 4 dure ~4 s (attentes réelles de la gateway, 1 s + 3 s).

## Limites

Ne couvre pas : les apps Android/iPhone (tâches 7 à 10), les fournisseurs réels, l'essai réel de la tâche 11.4. Le lien gateway → cloud est une relecture de la requête réelle, pas une connexion TCP entre les deux binaires.
