## Context

Faits relevés dans le code (explorations du 2026-11-06, firmware BP 099-37 et boîtier BA 1.7) :

- La table d'échange a, par boîtier, 16 cases de temporisation : `Lampes_PDV_Temps` = 518, `Lampes_CHB_Temps` = 534, `Lampes_PDE_Temps` = 550 (valeurs compilées depuis `TableEchange.h`). La case d'une lumière est la base du boîtier plus l'index de sa sortie.
- Mapping retenu, recoupé avec les masques de scénarios du BP et `TableReference.json` de l'écran : Dressing = pièces de vie, sortie 3 → **521** ; WC 1 = pièces d'eau, sortie 5 → **555** ; WC 2 → **556** ; Service → **557** ; Annexe 1 = sortie 11 → **561** ; Annexe 2 = sortie 12 → **562**.
- Valeur : un octet non signé (`uc_`), 0 à 255 minutes. Le boîtier arme un compteur de `minutes × 60 × 0,994` secondes ; 0 laisse la lumière allumée. Les cases sont en lecture-écriture pour le serveur.
- L'écran tactile (`StpEclT.4FN`) compare la valeur avec 15, 30, 60 et 0 (lecture du binaire, à confirmer au banc).
- Aucun backend, portail ou app ne connaît ces clés. Aucune des deux apps ne gère le rôle de l'utilisateur. Le cloud n'a aucun contrôle de rôle dans ses handlers. La gateway ne protège les routes de la table d'échange que par la session LAN.

## Goals / Non-Goals

**Goals :** régler les six délais depuis les quatre surfaces, en local comme via le cloud, avec une valeur identique partout ; réservé à l'administrateur de l'armoire ; jamais de commande sur une armoire réelle dans les tests.

**Non-Goals :** modifier le firmware ou l'écran de l'armoire ; régler d'autres temporisations (volets, chauffe-eau, arrosage) ; ajouter d'autres lumières que les six (les autres cases sont « non utilisé » dans le BP).

## Decisions

1. **Routes dédiées plutôt que l'injection générique.** L'injection ne valide ni la clé ni la plage, et ne contrôle pas le rôle. Chaque backend expose `GET` (les six valeurs) et `PUT` (une lumière, `{minutes}`) : cloud `GET /portal/lights/timers` et `PUT /portal/admin/lights/timers/{id}` ; gateway `GET /api/admin/lights/timers` et `PUT /api/admin/lights/timers/{id}` derrière `adminOnly`. L'identifiant est `dressing`, `wc1`, `wc2`, `pieceserv`, `ann1` ou `ann2` (les identifiants déjà utilisés par les apps et les portails).
2. **Catalogue unique** `{id, libellé, clé}` côté backend, renvoyé par le `GET` : les clients n'en dupliquent que les libellés.
3. **Validation côté serveur** : identifiant connu, `minutes` entier de 0 à 255, sinon 400. L'écriture passe par la file d'actions existante (une action à une clé, hors plage 605–623, donc sans complément de bloc).
4. **Rôle administrateur.** Cloud : `admin_local` de cette armoire (`LinkedMachineID`) ; `admin_global` accepté seulement avec une armoire liée. Gateway : `lan_admin`, et, comme partout, tout utilisateur quand l'IAM LAN est désactivé. 403 pour les autres. Côté clients : le rôle est décodé à la connexion, mémorisé dans la session et sert à masquer le menu et le réglage. Le masquage n'est pas une protection : la protection est celle du serveur.
5. **Lecture.** Gateway : les six clés entrent dans la rotation de lecture et le snapshot (comme la clé 440) ; une clé jamais lue est « inconnue », jamais 0. Cloud : migration idempotente `018` (profil de synchro `[[521,521],[555,557],[561,562]]`, pull et push) pour que la gateway remonte les valeurs ; le cache est aussi mis à jour par l'écriture.
6. **Interface.** Raccourcis 15 min, 30 min, 1 h, Jamais, plus « Autre » (1 à 255). Une valeur courante non raccourcie s'affiche telle quelle (« 7 min »). Après un envoi, relecture à 5, 10 et 20 s comme pour les prises de sécurité. Mode test : commande validée mais non exécutée.
7. **Deux endroits.** Un menu « Temporisations » (liste des six) et le même composant dans la fiche de chaque lumière (panneau repliable sur les portails, ligne ou feuille dans les apps).

## Contrat d'API (identique cloud et gateway)

Chemins : cloud `GET /api/portal/lights/timers` et `PUT /api/portal/admin/lights/timers/{id}` ; gateway `GET /api/admin/lights/timers` et `PUT /api/admin/lights/timers/{id}`. Les clients ajoutent le préfixe de leur mode (cloud ou LAN) comme pour l'injection.

`GET` répond 200 :

```json
{"timers":[
  {"id":"dressing","label":"Dressing","key":521,"minutes":15},
  {"id":"wc1","label":"WC 1","key":555,"minutes":null},
  {"id":"wc2","label":"WC 2","key":556,"minutes":0},
  {"id":"pieceserv","label":"Service","key":557,"minutes":60},
  {"id":"ann1","label":"Annexe 1","key":561,"minutes":null},
  {"id":"ann2","label":"Annexe 2","key":562,"minutes":7}
]}
```

Ordre fixe : dressing, wc1, wc2, pieceserv, ann1, ann2. `minutes` est un entier 0 à 255, ou `null` si la valeur n'a jamais été lue (jamais 0 par défaut). `0` signifie « jamais ».

`PUT` reçoit `{"minutes": 30}` et répond 200 `{"id":"wc2","minutes":30,"status":"queued"}` (`"dry_run"` avec le mode test, rien n'est mis en file). Erreurs : 400 `{"error":"invalid_minutes"}` ou `{"error":"unknown_light"}`, 401 sans session, 403 `{"error":"forbidden"}` si l'appelant n'est pas administrateur de l'armoire.

## Risks / Trade-offs

- **Écran de l'armoire et valeur libre.** Il ne coche aucune case pour 7 min, et peut écraser la valeur à la validation. Mitigation : test sur banc obligatoire avant déploiement ; sinon limiter la valeur libre.
- **Clés 561 et 562 et PDV.** Les commentaires du BP les marquent « non utilisées ». Le code du boîtier les applique pourtant à ses 13 relais. À confirmer au banc.
- **Version du BP en production** non comparée à la 099-37.
- **Portail cloud sans Playwright de rôle** : le test du cas non-administrateur demande une session de démonstration à rôle.
- **Les prises de sécurité (feature précédente) ne sont pas dans les checkouts des portails** : les branches de base sont `main` (cloud) et `V.1.3.0` (local) ; aucune dépendance au code des prises.

## Migration Plan

Déployer dans l'ordre : cloud (migration 018), gateway CM5 et Pi, puis portails, puis APK (site support) et TestFlight. Retour arrière : les routes sont additives, les apps actuelles les ignorent.

## Open Questions

- Comportement exact de l'écran de l'armoire avec une valeur hors des quatre choix (test banc).
