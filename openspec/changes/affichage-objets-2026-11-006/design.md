## Context

Les 33 lumières et les 16 volets et stores sont déjà identifiés par des `id` communs aux quatre clients (portail cloud, portail local, Android `IndexTable.kt`, iPhone `IndexTable.swift`) et aux dépôts serveur. Les Features #41 (`noms-lumieres-2026-11-004`) et #52 (`noms-volets-2026-11-005`) ont posé le modèle : droits administrateur, route cloud `/api/portal`, route gateway `/api/admin`, agent de synchronisation cloud ↔ gateway (`/api/gateway/*`, authentifié par `GatewayAuth`), fichier JSON de la gateway sous la clé `light_names.path`, magasin à sections brutes (livré en #52). Cette Feature les reprend avec des routes jumelles, mais avec un **document par genre** au lieu d'une entrée par objet.

Relevé du code livré (2026-11-07) :

- Cloud (`essensys-user-portal-backend`, main `4ccc2f6`) : `internal/domain/lights_names.go` et `shutters_names.go` (catalogues, `NormalizeLightName`, `CanWriteLightNames` / `CanWriteShutterNames`, `LightNameNewer`, `ClampLightNameTime`), `internal/handlers/light_names.go` et `shutter_names.go`, `internal/data/*_names_store.go`, routes dans `internal/portal/routes.go` (lecture `r.Get("/shutters/names")` ligne 30 ; écriture dans `r.Route("/admin")` ligne 47) et `internal/gateway/routes.go` (ligne 23, `r.With(auth).Post("/shutters/names/sync")`). Dernière migration : `020_shutter_names.sql`. Dernier test de non-régression : `NR-backend-16`.
- Gateway (`essensys-server-backend`, branche V.1.3.0 `daaebb9`) : `internal/core/light_names.go` (magasin `LightNameStore`, `namesDoc map[string]json.RawMessage` avec `section()` / `setSection()`, sections `lights` et `shutters`) et `shutter_names.go`, `internal/api/handlers_light_names.go` et `handlers_shutter_names.go`, `internal/api/router.go` (lignes 88-89 : `protect(...)` pour la lecture, `adminOnlyJSON(...)` pour l'écriture), `internal/cloudsync/light_names_sync.go` / `shutter_names_sync.go` (`syncNames` lance les deux synchronisations l'une après l'autre ; l'échec de l'une ne bloque pas l'autre), `cmd/server/main.go` (lignes 154-160 : un seul `lightNames` partagé), `config.yaml.example` (clé `light_names`, ligne 83). Dernier test : `NR-server-backend-31`.
- Clients : voir « Endroits à filtrer et à ordonner » plus bas. Derniers tests : `NR-portal-frontend-12`, `NR-server-frontend-9`, `NR-android-26`, `NR-ios-26`.

## Décisions

1. **Un document par armoire et par genre.** Deux genres : `lights` (33 identifiants) et `shutters` (16). Document :
   ```json
   {"order":["salon","entree"],"disabled":["wc2"],"version":3,"updated_at":"2026-11-07T10:15:30.123Z","updated_by":"admin-local"}
   ```
   - `order` : liste d'identifiants du catalogue du genre, sans doublon. `disabled` : sous-ensemble du catalogue, sans doublon. Tous les objets peuvent être désactivés.
   - Version 0 et `updated_at` nul = disposition par défaut (`order` vide, `disabled` vide) : ordre du catalogue, rien de désactivé.
   - **Tolérance des clients (MUST)** : un `order` incomplet ou contenant d'anciens identifiants est accepté. Les identifiants connus absents de `order` sont ajoutés à la fin, dans l'ordre du catalogue ; les identifiants inconnus (dans `order` ou `disabled`) sont ignorés.
   - Raison du document unique : un réordonnancement est atomique (une version) et n'entre pas en conflit avec les noms.
2. **Ordre effectif et affichage.** Fonction commune aux quatre clients, `effectiveLayout(catalogue, layout)` :
   1. `ordered` = les identifiants de `layout.order` qui sont dans le catalogue (premier exemplaire seulement), puis les identifiants du catalogue absents de `order`, dans l'ordre du catalogue ;
   2. `disabled` = `layout.disabled` ∩ catalogue ;
   3. liste d'un groupe d'affichage (`MAIN`, `INDIRECT`, `SPECIAL`) = éléments de `ordered` de ce groupe qui ne sont pas dans `disabled` ;
   4. liste de l'écran de gestion = tous les éléments de `ordered`, avec leur état.
   L'ordre est global dans le document (les 33 ou 16 identifiants) mais n'est appliqué qu'à l'intérieur de chaque groupe d'affichage : un identifiant n'est jamais déplacé d'un groupe à l'autre. « Monter » / « Descendre » échange l'élément avec son voisin **du même groupe** dans `ordered`. Les écrans qui n'ont pas de groupes (Temporisations, « Temps de course ») suivent l'ordre global filtré. **Exception pour Temporisations** : tant que l'ordre effectif des lumières est identique à l'ordre du catalogue d'origine (aucun réordonnancement enregistré, y compris après `reset`), l'écran Temporisations garde l'ordre propre de son catalogue (Dressing, WC 1, WC 2, Pièce de service, Annexe 1, Annexe 2), filtré par les objets désactivés ; dès que l'ordre effectif diffère de celui du catalogue, il suit l'ordre global filtré. Le critère est la comparaison avec le catalogue, jamais un `order` vide, car les clients envoient toujours un `order` complet.
3. **Routes jumelles pour les deux genres**, sans API générique multi-genres (même choix que #52).

   | Surface | Route | Droits |
   |---|---|---|
   | Cloud, lecture | `GET /api/portal/{lights\|shutters}/layout` | utilisateur de l'armoire liée |
   | Cloud, écriture | `PUT /api/portal/admin/{lights\|shutters}/layout` | administrateur de l'armoire (`admin_local` ou `admin_global` avec l'armoire liée) |
   | Cloud, synchro gateway | `POST /api/gateway/{lights\|shutters}/layout/sync` | `GatewayAuth` |
   | Gateway, lecture | `GET /api/{lights\|shutters}/layout` | tout utilisateur authentifié ; ouvert si l'IAM LAN est désactivé |
   | Gateway, écriture | `PUT /api/admin/{lights\|shutters}/layout` | `adminOnlyJSON` (`lan_admin`, ouvert si IAM LAN désactivé) |

4. **Écriture.** Corps `{"order":[…],"disabled":[…]}` : les deux clés sont obligatoires ; ou `{"reset":true}` : revient à la disposition par défaut (`order` et `disabled` vides). L'écriture est faite à la version `n+1` (y compris pour `reset`, pour que le retour au défaut se propage). L'écriture remplace le document entier. Le serveur valide, il ne complète pas `order` (un `order` incomplet est accepté tel quel). Les clients, eux, envoient toujours `order` complet.
5. **Fusion cloud ↔ gateway, document entier.** On compare `(updated_at, version, updated_by)` dans cet ordre ; le plus grand gagne ; égalité parfaite = valeur du cloud. `updated_at` est en UTC (RFC 3339, millisecondes) posé par l'environnement qui accepte la modification ; le cloud ramène à son heure un `updated_at` plus de 5 minutes dans le futur (`ClampLightNameTime`). Il n'y a pas de fusion champ par champ : deux modifications simultanées donnent partout la même valeur, celle du document le plus récent.
6. **Stockage cloud.** Nouvelle migration idempotente `021_object_layout.sql` :
   ```sql
   CREATE TABLE IF NOT EXISTS object_layout (
       machine_id INT NOT NULL,
       kind TEXT NOT NULL,                 -- 'lights' ou 'shutters'
       order_json TEXT NOT NULL DEFAULT '[]',
       disabled_json TEXT NOT NULL DEFAULT '[]',
       version INT NOT NULL DEFAULT 0,
       updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       updated_by TEXT NOT NULL DEFAULT '',
       PRIMARY KEY (machine_id, kind)
   );
   ```
   Uniquement des créations gardées par `IF NOT EXISTS` (le binaire rejoue toutes les migrations à chaque démarrage). Les tables `light_names` et `shutter_names` ne sont pas modifiées. `kind` est borné à `lights` / `shutters` par le code.
7. **Stockage gateway : même fichier, même clé, deux sections.**
   ```json
   {"version":1,
    "lights":{"dressing":{"name":"WC 3","version":2,"updated_at":"…","updated_by":"…"}},
    "shutters":{"volet1salon":{"name":"Volet baie vitrée","version":1,"updated_at":"…","updated_by":"…"}},
    "lights_layout":{"order":["salon"],"disabled":["wc2"],"version":3,"updated_at":"…","updated_by":"…"},
    "shutters_layout":{"order":[],"disabled":["voletbureau"],"version":1,"updated_at":"…","updated_by":"…"}}
   ```
   - `version` du fichier reste 1. Une section absente = disposition par défaut.
   - Les sections `lights_layout` et `shutters_layout` sont des **objets**, pas des tables d'entrées : le code ne doit pas les décoder avec `namesDoc.section()` (qui produit une table `map[string]lightNameEntry`) ; il ajoute un décodeur dédié et une écriture `setRaw`, sous le même verrou et avec la même écriture atomique (fichier temporaire puis renommage). Écrire une section préserve toutes les autres, connues ou non.
   - Sans chemin valide ou en cas d'échec d'écriture : la lecture renvoie la disposition par défaut, l'écriture répond 503 `names_unavailable` (code réutilisé).
   - **Conséquence : Raspberry Pi et Ansible ne sont pas concernés** (répertoire, montage, droits et clé `light_names.path` existent depuis #41). **Si l'implémentation introduit un autre chemin, une autre clé ou un autre fichier, ces deux briques redeviennent concernées** : la matrice du manifest doit alors être corrigée par un humain et les tâches Ansible (montage, clé de configuration) et Raspberry Pi (répertoire, droits) ajoutées avant de continuer.
8. **Comportement des clients pour un objet désactivé** : masqué pour tous les utilisateurs dans les listes (lumières principales, indirectes, volets, store et éléments spéciaux), dans « Tout allumer / éteindre » et « Tout ouvrir / fermer » (les commandes de groupe n'incluent **pas** les objets désactivés), dans l'écran Temporisations et dans l'écran « Temps de course ». Aucune commande n'est envoyée pour cet objet depuis les clients. Si un groupe n'a plus aucun objet actif, ses boutons de groupe sont masqués et un texte « Aucune lumière activée » / « Aucun volet activé » est affiché (aucune commande vide). Les scénarios et l'éditeur de scénarios gardent le catalogue complet (hors périmètre). Lecture impossible ou ancien serveur (404) : catalogue complet dans l'ordre d'origine, sans message bloquant.
9. **Écran de gestion (administrateur de l'armoire seulement).** Liste **tous** les objets du genre, désactivés compris, dans l'ordre effectif, avec le nom affiché (nom personnalisé de #41/#52), un interrupteur Activé/Désactivé et des boutons Monter/Descendre (désactivés en tête et en queue de groupe) ; bouton « Ordre d'origine » (reset) ; un seul bouton « Enregistrer » qui envoie une écriture. Les modifications restent locales à l'écran jusqu'à l'enregistrement. Le non-administrateur ne voit ni l'écran ni le bouton d'accès. Le masquage de l'écran est une commodité : le serveur reste la protection (403).
10. **Aucune écriture dans l'armoire.** Les dispositions ne sont ni lues ni écrites dans la table d'échange.

## Contrat d'API (figé : tous les dépôts le suivent)

Document commun `ObjectLayout`, identique pour `lights` et `shutters` :

```json
{"order":["salon","entree","terrasse"],"disabled":["wc2"],"version":3,"updated_at":"2026-11-07T10:15:30.123Z"}
```

Disposition par défaut (rien d'enregistré) : `{"order":[],"disabled":[],"version":0,"updated_at":null}`.

Les réponses destinées aux clients (`GET`, `PUT`) **ne contiennent pas** `updated_by` (le cloud y stocke l'adresse e-mail de l'administrateur : elle n'est pas exposée aux autres utilisateurs de l'armoire). Les échanges de synchronisation gateway ↔ cloud et le fichier de la gateway le contiennent, puisque la fusion le compare.

| Appel | Corps | Réponse |
|---|---|---|
| `GET /api/portal/lights/layout` (cloud) ; `GET /api/lights/layout` (gateway) | néant | `200 ObjectLayout` |
| `PUT /api/portal/admin/lights/layout` (cloud) ; `PUT /api/admin/lights/layout` (gateway) | `{"order":[…],"disabled":[…]}` ou `{"reset":true}` | `200 ObjectLayout` + `"status":"saved"` |
| `POST /api/gateway/lights/layout/sync` (cloud) | document de la gateway : `{"order":[…],"disabled":[…],"version":n,"updated_at":"…","updated_by":"…"}` (`version` 0 : rien à envoyer) | `200` état fusionné complet : `{"order":[…],"disabled":[…],"version":n,"updated_at":"…","updated_by":"…"}` |

Les routes `shutters` sont identiques en remplaçant `lights` par `shutters`. Exemples :

```http
PUT /api/portal/admin/shutters/layout
{"order":["volet2salon","volet1salon"],"disabled":["voletbureau","store"]}
→ 200 {"order":["volet2salon","volet1salon"],"disabled":["voletbureau","store"],"version":1,"updated_at":"2026-11-07T10:15:30.123Z","status":"saved"}

PUT /api/admin/lights/layout
{"reset":true}
→ 200 {"order":[],"disabled":[],"version":4,"updated_at":"2026-11-07T10:20:00.000Z","status":"saved"}
```

Erreurs (mêmes codes que #41 et #52) :

| Code | Corps | Cas |
|---|---|---|
| 400 | `{"error":"unknown_light"}` / `{"error":"unknown_shutter"}` | identifiant hors catalogue du genre dans `order` ou `disabled` (y compris un identifiant de l'autre genre) |
| 400 | `{"error":"invalid_layout"}` | JSON illisible, clé `order` ou `disabled` absente (hors `reset`), valeur qui n'est pas une liste de chaînes, doublon dans `order` ou dans `disabled`, corps de plus de 16 Ko |
| 400 | `{"error":"invalid_body"}` | corps de synchronisation illisible ou de plus de 64 Ko |
| 401 | | pas de session (cloud, ou gateway avec IAM LAN actif) ; jeton gateway invalide pour la synchronisation |
| 403 | `{"error":"forbidden"}` | écriture par un non-administrateur de l'armoire ; lecture sans armoire liée (cloud) |
| 503 | `{"error":"names_unavailable"}` | stockage indisponible (gateway sans chemin valide ; cloud : erreur de base) |

Mode essai à blanc : en-tête `X-Essensys-Test-Mode: dry-run` (cloud et gateway) ou `?test_mode=dry_run` (gateway) valide la requête, répond `"status":"dry_run"` avec le document qui aurait été enregistré (sans incrémenter la version) et n'écrit rien. Tout changement est tracé (qui, quand, ancien et nouveau document) : événement d'audit `object_layout` (champ `kind`).

Synchronisation gateway : à chaque cycle l'agent envoie ses deux documents au cloud (deux appels `POST …/lights/layout/sync` et `POST …/shutters/layout/sync`, distincts de ceux des noms) et remplace ses sections par la réponse. Le cloud fusionne (décision 5) ; la gateway n'écrase donc jamais un document local plus récent. L'échec d'un des quatre appels (noms de lumières, noms de volets, dispositions) ne bloque pas les autres. Après une écriture locale, une synchronisation immédiate est tentée sans bloquer la réponse. Hors ligne, la réplique locale fait foi et la synchronisation reprend au retour de la connexion. Un cloud qui répond 404 (route pas encore déployée) ne perturbe rien d'autre. Une gateway qui n'a jamais vu le cloud envoie son document au premier contact.

## Catalogue des lumières (33, ordre d'origine, groupe)

Relevé dans `internal/core/light_names.go` (gateway, `lightNameCatalogue`) et dans `IndexTable.kt` lignes 43-75 (Android) ; les portails (`mainLights`, `indirectLights`) et l'iPhone (`IndexTable.swift` ligne 49) portent les mêmes identifiants dans le même ordre.

Groupe « Éclairage principal » (`MAIN`, 21) : `terrasse`, `entree`, `escalier`, `deg1`, `deg2`, `pieceserv`, `ann1`, `ann2`, `salon`, `sam`, `cuisine`, `sdb1`, `sdb2`, `wc1`, `wc2`, `bureau`, `gdchamb`, `ptchamb1`, `ptchamb2`, `ptchamb3`, `dressing`.

Groupe « Éclairage indirect » (`INDIRECT`, 12) : `isalonind`, `isalonind2`, `icuisine`, `isdb1`, `isdb2`, `igdchamb1`, `igdchamb2`, `iptchamb1`, `iptchamb2`, `iptchamb22`, `iptchamb3`, `idressing`.

## Catalogue des volets et stores (16, ordre d'origine, groupe)

Identique à `noms-volets-2026-11-005` (`IndexTable.kt` lignes 79-94, `IndexTable.swift` ligne 85).

Groupe « Volets » (`MAIN`, 14) : `volet1salon`, `volet2salon`, `volet3salon`, `volet1salleamanger`, `volet2salleamanger`, `volet1cuisine`, `volet2cuisine`, `voletsdb`, `volet1gdchamb`, `volet2gdchamb`, `volet1ptchamb`, `volet2ptchamb`, `volet3ptchamb`, `voletbureau`.

Groupe « Éléments spéciaux » (`SPECIAL`, 2) : `voletstore`, `store`.

## Endroits à filtrer et à ordonner (relevé au 2026-11-07)

Les lignes sont celles de `origin/main` (portail cloud, Android, iPhone) et de la branche V.1.3.0 (portail local, qui n'est pas sur `main`). Elles peuvent avoir bougé : l'implémentation les confirme. Principe : filtrer et ordonner **une fois**, à l'endroit où la liste d'un groupe est construite à partir du catalogue ; les boutons de groupe et les lignes individuelles reçoivent alors la même liste, donc un objet désactivé ne peut pas être commandé par un groupe.

| Client | Fichier et lignes | À changer |
|---|---|---|
| Portail cloud, lumières | `src/pages/LightingPage.tsx` : tableaux `mainLights` (24) et `indirectLights` (48) ; `handleGroupAction(lights, …)` (101) boucle sur la liste reçue ; `renderLightControls(lights, groupName)` (129) : boutons « Tout allumer / éteindre » (134, 142) et `lights.map` (153) ; appels aux lignes 288 (`mainLights`) et 292 (`indirectLights`) | passer `layoutLights(mainLights)` et `layoutLights(indirectLights)` aux appels 288 et 292 (une seule liste filtrée et ordonnée alimente groupe et lignes) ; groupe vide : texte et boutons masqués |
| Portail cloud, volets | `src/pages/ShuttersPage.tsx` : tableaux `shutters` (22) et `stores` (39), `allShutters` (44) ; chargement des temps de course `getExchangeValues(allShutters.map(…))` (63) ; `handleGroupAction(items, …)` (117) ; `items.map` (158) ; `renderTimeSettings` (223) avec `allShutters.map` (231) ; appels lignes 303 (`shutters`) et 307 (`stores`) | filtrer/ordonner aux appels 303 et 307 ; construire `allShutters` (44) à partir des deux listes filtrées (écran « Temps de course ») ; la lecture des temps (63) peut rester complète ou se limiter aux actifs, aucune écriture ne doit partir pour un désactivé |
| Portail cloud, Temporisations | `src/pages/LightTimersPage.tsx` : `LIGHT_TIMER_CATALOG.map` (47) ; catalogue dans `src/lights/lightTimers.ts` (16) | filtrer les entrées désactivées et suivre l'ordre global |
| Portail cloud, nouveaux fichiers | `src/lights/lightLayout.ts` (+ `useLightLayout.ts`), `src/shutters/shutterLayout.ts` (+ `useShutterLayout.ts`) : fonction `effectiveLayout`, lecture `GET /api/portal/{lights\|shutters}/layout`, écriture ; composant d'écran de gestion | à créer (même organisation que `lightNames.ts` / `useLightNames.ts`) |
| Portail local, lumières | `src/pages/LightingPage.tsx` : `mainLights` (23), `indirectLights` (47), `handleGroupAction` (97), `renderLightControls` (125), `lights.map` (149), appels 227 et 231 | idem portail cloud |
| Portail local, volets | `src/pages/ShuttersPage.tsx` : `shutters` (21), `stores` (38), `allShutters` (43), chargement des temps (60), `handleGroupAction` (114), `items.map` (155), `renderTimeSettings` (185) avec `allShutters.map` (193), appels 261 et 265 | idem portail cloud |
| Portail local, Temporisations | `src/pages/LightTimersPage.tsx` : `LIGHT_TIMERS.map` (49) ; catalogue `src/lights/lightTimers.ts` (19) | idem portail cloud |
| Android, catalogue | `data/control/IndexTable.kt` : `IndexTable.lights` (43-75, `Group.MAIN` / `Group.INDIRECT`), `IndexTable.shutters` (79-94, `Group.MAIN` / `Group.SPECIAL`) ; l'enum `Group` est à la ligne 13 | nouveaux fichiers `data/control/ObjectLayout.kt` (modèle, `effective`, validation) ; l'ordre d'origine du tableau ne change pas (clé de repli et de test) |
| Android, lumières | `ui/screens/LightingScreen.kt` : groupes aux lignes 53-54, `IndexTable.lights.filter { it.group == group }` (56), `vm.send("group-$group-$on", …, lights.map { it.command(on) })` (60), `lights.forEach` (67) | remplacer la ligne 56 par la liste filtrée et ordonnée (groupe et lignes partagent `lights`) ; groupe vide : texte, boutons masqués |
| Android, volets | `ui/screens/ShuttersScreen.kt` : lecture des temps `IndexTable.shutters.map { it.travelTimeIndex }` (53), groupes (59-60), `IndexTable.shutters.filter { it.group == group }` (62), `vm.send("group-$group-$open", …)` (66), `items.forEach` (73), `TravelTimeCard(…)` (91) et sa boucle `IndexTable.shutters.forEach` (106) | idem lumières ; la boucle (106) et la lecture (53) utilisent la liste des volets actifs, ordre global |
| Android, Temporisations | `ui/screens/LightTimerScreens.kt` : `LightTimer.entries.forEach` (49) ; énumération dans `data/control/LightTimer.kt` | filtrer par identifiant actif, ordre global |
| Android, état | `ui/screens/LightNamesViewModel.kt` et `ShutterNamesViewModel.kt` (modèle à suivre) ; `data/control/ComfortRepository.kt` (`readLightNames` ligne 75, `readShutterNames` ligne 117 : modèles pour `readLightLayout` / `readShutterLayout`, cloud et local) | nouveaux `LightLayoutViewModel`, `ShutterLayoutViewModel` ; écran de gestion en feuille depuis `LightingScreen` / `ShuttersScreen` |
| iPhone, catalogue | `Data/Control/IndexTable.swift` : `enum Group` (18), `IndexTable.lights` (49), `IndexTable.shutters` (85) | nouveaux `Data/Control/ObjectLayout.swift` ; ordre d'origine inchangé |
| iPhone, lumières | `UI/Screens/ControlScreens.swift` : `IndexTable.lights.filter { $0.group == group }` (64), `GroupActions` / `model.send(key: "group-…", injections: lights.map …)` (66-67), `ForEach(lights)` (69) | liste filtrée et ordonnée en (64) |
| iPhone, volets | `UI/Screens/ControlScreens.swift` : `IndexTable.shutters.filter { $0.group == group }` (106), `ForEach(items)` (111), `TravelTimeCard` : `ForEach(IndexTable.shutters)` (146) ; `UI/ControlModel.swift` : lecture des temps `IndexTable.shutters.map(\.travelTimeIndex)` (74) | idem ; (146) et (74) sur les volets actifs |
| iPhone, Temporisations | `UI/Screens/LightTimersScreen.swift` : `ForEach(IndexTable.lightTimers)` (31) ; catalogue `Data/Control/LightTimers.swift` (19) | filtrer et suivre l'ordre global |
| iPhone, état | `UI/FeatureModels.swift` : modèles de noms (`displayName`, lignes 428 et 497) à suivre pour `LightLayoutModel` / `ShutterLayoutModel` ; `Debug/UITestBackend.swift` (198, 236) à compléter par les routes de disposition ; écran de gestion en feuille | |

Ne pas filtrer : l'éditeur de scénarios et les scénarios (catalogue complet), le widget historique `ShutterControl.tsx` non routé, les libellés génériques (« Volets », « Tout ouvrir », titres de cartes). Les confirmations de groupe (« Tout allumer ») ne citent aucun nom et restent telles quelles.

## Rétro-compatibilité et ordre de déploiement

- Un client qui lit un 404 (cloud ou gateway sans la route) ou qui échoue à lire affiche le **catalogue complet dans l'ordre d'origine**, sans message bloquant. Si une disposition a déjà été lue avec succès pendant la session, la dernière valeur lue est conservée en cas d'échec ultérieur (un objet masqué ne réapparaît pas à cause d'une coupure passagère).
- Un client ancien ignore les nouvelles routes : il affiche tout le catalogue, sans erreur.
- **Ordre de déploiement : cloud, puis gateway, puis portails, APK, TestFlight.** La gateway tolère un cloud qui répond 404 sur les routes de disposition.
- **Risque : gateway restée à la version de #41 (avant le magasin à sections brutes, livré en #52).** Cette version décode le fichier dans une structure qui ne connaît que `lights` : à sa prochaine écriture de nom de lumière elle effacerait `shutters`, `lights_layout` et `shutters_layout`. Une gateway de version #52 conserve les sections inconnues. Conséquences : (1) ne pas déployer ni activer le cloud pour une gateway qui n'a pas #52 ; (2) en cas de retour arrière de la gateway vers #41 ou plus ancien, les dispositions locales sont perdues à la prochaine écriture locale, mais elles sont rétablies depuis le cloud à la synchronisation suivante (le cloud arbitre) ; (3) mentionner ce point dans le runbook (documentation, tâche 7.2).
- Une gateway de version #52 sans #55 conserve les sections de disposition sans les lire ni les servir : ses clients locaux affichent tout le catalogue.

## Règle du nom

Inchangée (#41, #52). L'écran de gestion affiche le nom personnalisé quand il existe, sinon le nom d'origine, rendu comme texte brut.

## Risques et inconnus

- **Horloge de la gateway** : une dérive de plus de 5 minutes fausse l'arbitrage (bornée côté cloud pour le futur uniquement). NTP est installé sur CM5.
- **Dernier écrit gagne sur le document entier** : un administrateur local hors ligne qui désactive une lumière écrase, à son retour, un réordonnancement fait entre-temps dans le cloud si son horodatage est plus récent. Acceptable (réglage rare, une personne), à documenter.
- **Tout désactivé** : permis. Les groupes sont alors vides, l'administrateur garde l'écran de gestion.
- **Objet désactivé encore actif ailleurs** : un objet désactivé reste commandable par les scénarios déjà enregistrés (hors périmètre) et par l'armoire elle-même.
- **Une armoire par compte** : un administrateur global qui a plusieurs armoires n'agit que sur celle qui est liée à son compte.
- **Taille** : au plus 33 + 33 identifiants par document, quelques centaines d'octets ; limites de corps à 16 Ko (écriture) et 64 Ko (synchronisation).
- **Nom long dans l'écran de gestion** : un nom de 40 caractères ne doit pas masquer l'interrupteur ni les boutons Monter/Descendre (iPhone SE, iPad).
