## Contexte

La gateway embarque déjà un client UniFi Protect (`internal/unifi`, config `unifi:` avec `enabled`, `base_url`, `api_key`, `username`, `password`, routes `/api/unifi/cameras`). Elle ne reçoit aucun événement. Les commandes de lumières passent par des écritures dans la table d'échange (bits 605 à 622), comme pour les clients ; l'armoire les lit à son rythme.

## Décisions

1. **Source des événements** : l'API d'intégration UniFi Protect (clé d'API déjà supportée). La gateway ouvre une connexion d'événements vers la console et filtre l'événement de sonnette (`ring`) de la caméra choisie. Si l'API de la console ne fournit pas cet événement, repli : interrogation périodique de l'état de la sonnette (toutes les 2 s). **La première tâche est un essai de faisabilité** (voir tasks, 1.1) qui tranche entre les deux et consigne les messages réels (sans identifiant) ; la spec des routes ne change pas.
2. **Vidéo** : le navigateur ne lit pas le flux RTSPS de la console. Version 1 : la gateway sert une suite d'instantanés rafraîchis (environ une image par seconde, `multipart/x-mixed-replace` ou rafraîchissement d'image par le portail) à partir de `GetCameraSnapshot`, derrière l'authentification de la gateway ; la clé d'API ne quitte jamais la gateway. Si l'essai 1.1 montre qu'un transcodage (ffmpeg vers HLS) est disponible dans l'image de la CM5, il est préférable mais hors de ce ticket : il ferait l'objet d'une évolution.
3. **Réglages** : section `"doorbell"` dans le fichier de `light_names.path` : `{"enabled":bool,"camera_id":"…","lights":[ids],"blinks":n,"version":n,"updated_at":"…","updated_by":"…"}`. Les sections existantes sont préservées (même magasin à sections brutes que #55). Aucune synchronisation cloud (fonction locale). Par défaut : désactivé, aucune lumière, 5 clignotements.
4. **Clignotement** : pour chaque lumière choisie, la gateway lit son état courant, alterne allumé et éteint `blinks` fois (phase d'au moins 2 s, car l'armoire lit les ordres à son rythme : l'essai 1.1 mesure la cadence réelle), puis **restaure l'état d'origine**. Une seule séquence à la fois : une pression pendant une séquence est ignorée ; une pression dans les 30 s qui suivent le début d'une séquence ne relance pas de clignotement (la vidéo, elle, se réaffiche). Une commande manuelle de l'utilisateur sur une lumière en cours de clignotement l'exclut de la séquence (pas de restauration qui écraserait son ordre).
5. **Droits** : `GET /api/doorbell/status` et `GET /api/doorbell/stream` pour tout utilisateur authentifié (ouvert si l'IAM LAN est désactivé) ; `GET/PUT /api/admin/doorbell/settings` et `POST /api/admin/doorbell/test` derrière `adminOnlyJSON`. Réponses d'erreur : `unknown_light`, `unknown_camera`, `invalid_blinks`, `names_unavailable` (503), `doorbell_unavailable` (503, console injoignable ou UniFi désactivé).
6. **État** : `GET /api/doorbell/status` renvoie `{"enabled":bool,"available":bool,"ringing":bool,"ringing_until":"…","last_ring_at":"…"}`. Le portail l'interroge toutes les 2 s tant que la fenêtre est ouverte, toutes les 5 s sinon. `ringing` reste vrai 60 s après la pression.
7. **Essai** : `POST /api/admin/doorbell/test` simule une pression (vidéo et clignotement). En-tête `X-Essensys-Test-Mode: dry-run` : aucune écriture dans la table d'échange (même convention que #41, #52 et #55). Les tests automatiques n'écrivent jamais dans l'armoire.
8. **Isolation** : console injoignable ou UniFi désactivé : la gateway fonctionne normalement ; `available` vaut faux ; reconnexion automatique avec attente croissante (1 s à 60 s). Aucun identifiant ni adresse du réseau local n'est journalisé.
9. **Secrets et dépôts publics** : adresse de la console, clé d'API et identifiant de caméra vivent dans la configuration déployée par Ansible (SOPS) ou dans le fichier de la CM5 ; les dépôts, tests et documents n'utilisent que des exemples (`example.org`, plages RFC 5737).

## Risques

- L'API d'intégration de la console pourrait ne pas exposer l'événement de sonnette : repli par interrogation (décision 1).
- La cadence de lecture de l'armoire limite la vitesse de clignotement (décision 4). Le clignotement est lent, ce qui est assumé.
- Le clignotement écrit dans l'armoire réelle en production : seul l'essai administrateur et la vraie sonnette le déclenchent ; jamais les tests automatiques.
- Une lumière commandée manuellement pendant le clignotement : exclue de la séquence (décision 4).
- Instantanés environ 1 image par seconde : ce n'est pas une vidéo fluide ; à annoncer clairement dans la documentation.
