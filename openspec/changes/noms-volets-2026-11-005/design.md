## Context

Les 16 volets et stores sont déjà identifiés par des `id` communs à `ShuttersPage.tsx` (deux portails), `IndexTable.kt` (Android) et `IndexTable.swift` (iPhone). Les noms des lumières (#41, `noms-lumieres-2026-11-004`) ont posé le modèle : droits administrateur, route cloud `/api/portal`, route gateway `/api/admin`, agent de synchronisation cloud ↔ gateway (`/api/gateway/*`, authentifié par `GatewayAuth`), fichier JSON de la gateway. Cette Feature le reprend à l'identique pour les volets, avec des routes jumelles.

## Décisions

1. **Identifiant** : l'`id` existant des clients (`volet1salon`…). Pas de nouvel identifiant.
2. **Routes jumelles, pas d'API générique** : `/shutters/names` à côté de `/lights/names`, mêmes droits, mêmes erreurs (sauf `unknown_shutter`), même dry-run, même règle de nom. Aucun client ni dépôt livré en #41 n'a besoin d'être modifié pour les lumières.
3. **Cloud = arbitre, deux sources d'écriture** : le portail cloud écrit dans le cloud ; le portail local et les apps en mode local écrivent dans la gateway. La gateway pousse et tire à chaque cycle de synchronisation ; le cloud fusionne.
4. **Fusion par volet** : on compare `(updated_at, version, updated_by)` dans cet ordre ; le plus grand gagne ; égalité parfaite = valeur du cloud. `updated_at` est en UTC (RFC 3339, millisecondes) posé par l'environnement qui accepte la modification ; le cloud ramène à son heure un `updated_at` plus de 5 minutes dans le futur. `version` = ancienne version + 1.
5. **Remise à zéro** : `name = null` est une valeur à part entière (version incrémentée), pour que la remise à zéro se propage.
6. **Stockage cloud** : nouvelle migration idempotente `020_shutter_names.sql`, table `shutter_names (machine_id, shutter_id, name, version, updated_at, updated_by)`, clé primaire `(machine_id, shutter_id)`, uniquement des créations gardées par `IF NOT EXISTS`. La table `light_names` n'est pas modifiée.
7. **Stockage gateway : même fichier, même clé.** Le fichier JSON désigné par `light_names.path` reçoit une seconde section à côté de `lights` :
   ```json
   {"version":1,
    "lights":{"dressing":{"name":"WC 3","version":2,"updated_at":"…","updated_by":"…"}},
    "shutters":{"volet1salon":{"name":"Volet baie vitrée","version":1,"updated_at":"…","updated_by":"…"}}}
   ```
   - `version` du fichier reste 1. Une section absente est vide.
   - L'écriture d'une section **MUST préserver** l'autre section et toute section inconnue (le code livré en #41 décode le fichier dans une structure qui ne connaît que `lights` : il doit être refactoré, par exemple en conservant les sections brutes). Écriture atomique inchangée (fichier temporaire puis renommage), un seul verrou en mémoire pour tout le fichier.
   - Sans chemin valide ou en cas d'échec d'écriture : la lecture renvoie les noms d'origine, l'écriture répond 503 `names_unavailable`.
   - **Conséquence : Raspberry Pi et Ansible ne sont pas concernés** (répertoire, montage, droits et clé `light_names.path` existent depuis #41). **Si l'implémentation introduit un autre chemin, une autre clé ou un autre fichier, ces deux briques redeviennent concernées** : la matrice du manifest doit alors être corrigée par un humain et les tâches Ansible (montage, clé de configuration) et Raspberry Pi (répertoire, droits) ajoutées avant de continuer.
8. **Droits** : cloud, même règle que les noms de lumières (rôle `admin_local` ou `admin_global` **avec l'armoire liée**) ; gateway, `adminOnlyJSON` (`lan_admin`, ouvert si l'IAM LAN est désactivé). Lecture : tout utilisateur authentifié de l'armoire.
9. **Aucune écriture dans l'armoire.**

## Catalogue des volets et stores (ordre d'affichage, `id` → nom d'origine)

Relevé le 2026-11-07 dans `IndexTable.kt` (Android), `IndexTable.swift` (iPhone), `ShuttersPage.tsx` (portail cloud et portail local) : **les 16 libellés sont identiques sur les quatre clients**, rien à arbitrer. Les indices de commande (`openIndex`, `closeIndex`, `mask`, `timeIndex`) ne font pas partie des noms et ne changent pas.

Groupe « Volets » (14, `Group.MAIN`) :

| # | `id` | Nom d'origine |
|---|---|---|
| 1 | `volet1salon` | Volet 1 Salon |
| 2 | `volet2salon` | Volet 2 Salon |
| 3 | `volet3salon` | Volet 3 Salon |
| 4 | `volet1salleamanger` | Volet 1 Salle à Manger |
| 5 | `volet2salleamanger` | Volet 2 Salle à Manger |
| 6 | `volet1cuisine` | Volet 1 Cuisine |
| 7 | `volet2cuisine` | Volet 2 Cuisine |
| 8 | `voletsdb` | Volet Salle de Bain 1 |
| 9 | `volet1gdchamb` | Volet 1 Grande Chambre |
| 10 | `volet2gdchamb` | Volet 2 Grande Chambre |
| 11 | `volet1ptchamb` | Volet Petite Chambre 1 |
| 12 | `volet2ptchamb` | Volet Petite Chambre 2 |
| 13 | `volet3ptchamb` | Volet Petite Chambre 3 |
| 14 | `voletbureau` | Volet Bureau |

Groupe « Éléments spéciaux » (2, `Group.SPECIAL`) :

| # | `id` | Nom d'origine |
|---|---|---|
| 15 | `voletstore` | Volet "Store" (guillemets droits `"` dans le nom) |
| 16 | `store` | Store (banne) |

Écart trouvé et tranché : le widget historique `ShutterControl.tsx` (V.1.0.0, présent dans les deux portails, importé nulle part dans les routes actuelles) n'a que 14 volets et nomme les deux derniers `Volet "Store"` et `Store` (sans « (banne) »). Il n'est **pas** une source du catalogue : la référence est `ShuttersPage.tsx`, Android et iPhone (`Store (banne)`). Le widget n'est pas modifié ; s'il est un jour réaffiché, il devra utiliser les noms affichés.

## Règle du nom

Identique aux lumières. Après suppression des espaces en début et fin : de 1 à 40 caractères Unicode, sans caractère de contrôle (U+0000 à U+001F, U+007F), sans `<` ni `>`. Les clients affichent le nom comme **texte brut** (jamais comme HTML). Un nom vide ou `null` signifie « revenir au nom d'origine ». Les guillemets sont permis (le nom d'origine de `voletstore` en contient).

## Contrat d'API (figé : tous les dépôts le suivent)

Objet commun `ShutterName`, même forme que `LightName` :

```json
{"id":"volet1salon","default":"Volet 1 Salon","name":"Volet baie vitrée","version":2,"updated_at":"2026-11-07T10:15:30.123Z"}
```

`name` est `null` quand aucun nom n'a été défini ; `version` vaut 0 et `updated_at` est `null` dans ce cas. Le nom affiché est `name` si non nul, sinon `default`.

| Surface | Route | Droits |
|---|---|---|
| Cloud, lecture | `GET /api/portal/shutters/names` → `200 {"shutters":[ShutterName…]}` (16 éléments, ordre du catalogue) | utilisateur de l'armoire liée |
| Cloud, écriture | `PUT /api/portal/admin/shutters/names/{id}` corps `{"name":"Volet baie vitrée"}` ou `{"name":null}` → `200 ShutterName` + `"status":"saved"` | administrateur de l'armoire |
| Cloud, synchro gateway | `POST /api/gateway/shutters/names/sync` corps `{"names":[{"id","name","version","updated_at"}…]}` (zéro à 16 éléments) → `200 {"shutters":[ShutterName…]}` (état fusionné complet) | `GatewayAuth` |
| Gateway, lecture | `GET /api/shutters/names` → `200 {"shutters":[ShutterName…]}` | tout utilisateur authentifié (IAM LAN) ; ouvert si IAM désactivé |
| Gateway, écriture | `PUT /api/admin/shutters/names/{id}` même corps et même réponse que le cloud | `adminOnlyJSON` |

Erreurs : `400 {"error":"unknown_shutter"}`, `400 {"error":"invalid_name"}`, `401`, `403 {"error":"forbidden"}`, `503 {"error":"names_unavailable"}` (gateway sans stockage). Mode essai à blanc : en-tête `X-Essensys-Test-Mode: dry-run` (cloud et gateway) ou `?test_mode=dry_run` (gateway) valide la requête, répond `"status":"dry_run"` et n'écrit rien. Tout changement est tracé (qui, quand, ancien et nouveau nom) : événement d'audit `shutter_name`.

Synchronisation gateway : à chaque cycle, l'agent envoie ses 16 entrées au cloud (`POST …/shutters/names/sync`, appel distinct de celui des lumières) et remplace sa section `shutters` par la réponse (pas d'écrasement d'un nom local plus récent : la fusion est faite par le cloud). L'échec d'une des deux synchronisations ne bloque pas l'autre. Après une écriture locale, une synchronisation immédiate est tentée sans bloquer la réponse. Hors ligne, la réplique locale fait foi et la synchronisation reprend au retour de la connexion. Une gateway qui n'a jamais vu le cloud envoie ses noms au premier contact.

## Libellés codés en dur à remplacer par le nom affiché (relevé au 2026-11-07)

Les lieux ci-dessous sont relevés dans les checkouts locaux des dépôts de clients, où le tableau d'origine est lu directement ; l'implémentation les confirme au moment de coder (les lignes ont pu bouger avec #41). Le nom affiché remplace `shutter.name` / `item.name` partout où il est lu.

| Client | Où le nom d'origine est codé | Usages à convertir |
|---|---|---|
| Portail cloud (`essensys-user-portal-frontend`) | `src/pages/ShuttersPage.tsx` : tableaux `shutters` et `stores` (lignes 19-37), champ `name` | ligne 154 (liste des commandes), ligne 196 (carte « Temps de course »), ligne 84 (message « temps de course réglé »), ligne 100 (message « Ouvert/Fermé »), ligne 70 (journal console, facultatif) |
| Portail local (`essensys-server-frontend`) | `src/pages/ShuttersPage.tsx` : mêmes lignes | mêmes usages |
| Android (`essensys-android-phone-apps`) | `data/control/IndexTable.kt` : `IndexTable.shutters` (lignes 79-94), champ `name` | `ui/screens/ShuttersScreen.kt` : `CommandRow(name = shutter.name)` (liste), `vm.send(…, shutter.name, …)` (confirmation ouvrir/fermer), `TravelTimeCard` `Text(shutter.name)` (écran « Temps de course »). Le test `TravelTimeFlowTest.kt` cible par `testTag` (`time-current-<id>`) : il reste valable |
| iPhone (`essensys-ios-phone-apps`) | `Data/Control/IndexTable.swift` : `IndexTable.shutters` (lignes 86-101), champ `name` | `UI/Screens/ControlScreens.swift` : `CommandRow(name: shutter.name)`, `model.send(label: shutter.name, …)` (confirmations), `TravelTimeCard` `Text(shutter.name)`. Tests `ParityUITests.swift` et `IndexTableTests.swift` à conserver (le nom d'origine reste dans la table) |

À ne **pas** remplacer (libellés génériques, pas des noms d'objets) : titres de cartes « Volets », « Volet Store et Store banne », « Volets & stores » / « Volets & Stores » (menu et tuiles), boutons « Tout ouvrir » / « Tout fermer » / « Ouvrir » / « Fermer », et les messages « Actuel : … s », « Non transmis (défaut usine : 120 s, store : 255 s) ». Il n'existe pas de libellé « Tous les volets » dans le code actuel : les groupes sont des cartes à titre fixe. Les confirmations de groupe (« Tout ouvrir ») ne citent aucun nom et restent telles quelles.

Le nom d'origine reste dans `IndexTable` (clé de repli et de test) ; seul l'affichage passe par une fonction `displayName(id)` alimentée par les noms lus.

## Risques et inconnus

- **Refactor du fichier gateway** : le code livré en #41 ne connaît que la section `lights` et la réécrirait sans `shutters` (et inversement). Test obligatoire : écrire une section ne modifie pas l'autre ni une section inconnue.
- **Retour arrière** : une gateway repassée en #41 effacerait la section `shutters` à sa prochaine écriture de lumière ; les noms de volets sont alors rétablis depuis le cloud à la synchronisation suivante (le cloud arbitre). À mentionner dans le runbook.
- Horloge de la gateway : une dérive de plus de 5 minutes fausse l'arbitrage (bornée côté cloud pour le futur uniquement). NTP est installé sur CM5.
- Une armoire par compte : un administrateur global qui a plusieurs armoires n'agit que sur celle qui est liée à son compte (sélecteur d'armoire : ticket séparé).
- Nom long dans l'écran « Temps de course » : le nom de 40 caractères doit tenir sur une ligne (retour à la ligne ou troncature avec nom complet accessible), à vérifier sur iPhone SE et sur iPad.
