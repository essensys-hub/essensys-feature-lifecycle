## Context

Les 33 lumières sont déjà identifiées par des `id` communs à `LightingPage.tsx` (deux portails), `IndexTable.kt` (Android) et `IndexTable.swift` (iPhone). Les temporisations (#45) ont posé le modèle : droits administrateur, route cloud `/api/portal`, route gateway `/api/admin`, agent de synchronisation cloud ↔ gateway (`/api/gateway/*`, authentifié par `GatewayAuth`).

## Décisions

1. **Identifiant** : l'`id` existant des clients (`dressing`…). Pas de nouvel identifiant.
2. **Cloud = arbitre, deux sources d'écriture** : le portail cloud écrit dans le cloud ; le portail local et les apps en mode local écrivent dans la gateway. La gateway pousse et tire à chaque cycle de synchronisation ; le cloud fusionne.
3. **Fusion par lumière** : on compare `(updated_at, version, updated_by)` dans cet ordre ; le plus grand gagne. `updated_at` est en UTC (RFC 3339, millisecondes) posé par l'environnement qui accepte la modification ; le cloud refuse (ramène à l'heure du cloud) un `updated_at` plus de 5 minutes dans le futur (horloge de gateway fausse). `version` = ancienne version + 1.
4. **Remise à zéro** : `name = null` est une valeur à part entière (version incrémentée), pour que la remise à zéro se propage.
5. **Stockage gateway** : fichier JSON unique, écriture atomique (fichier temporaire puis renommage), verrou en mémoire. Chemin par la clé de configuration `light_names.path`. Sans chemin valide ou en cas d'échec d'écriture : la lecture renvoie les noms d'origine, l'écriture répond 503 `names_unavailable`.
6. **Droits** : cloud, même règle que les temporisations (rôle `admin_local` ou `admin_global` **avec l'armoire liée**) ; gateway, `adminOnlyJSON` (`lan_admin`, ouvert si l'IAM LAN est désactivé). Lecture : tout utilisateur authentifié de l'armoire.
7. **Aucune écriture dans l'armoire.**

## Catalogue des lumières (ordre d'affichage, `id` → nom d'origine)

Principales : `terrasse` Terrasse · `entree` Entrée · `escalier` Escalier · `deg1` Dégagement 1 · `deg2` Dégagement 2 · `pieceserv` Pièce de service · `ann1` Annexe 1 · `ann2` Annexe 2 · `salon` Salon · `sam` Salle à Manger · `cuisine` Cuisine · `sdb1` Salle de Bain 1 · `sdb2` Salle de Bain 2 · `wc1` WC 1 · `wc2` WC 2 · `bureau` Bureau · `gdchamb` Grande Chambre · `ptchamb1` Petite Chambre 1 · `ptchamb2` Petite Chambre 2 · `ptchamb3` Petite Chambre 3 · `dressing` Dressing.

Indirectes : `isalonind` Salon (indirect 1) · `isalonind2` Salon (indirect 2) · `icuisine` Cuisine (plans de travail) · `isdb1` Salle de Bain 1 (miroir) · `isdb2` Salle de Bain 2 (miroir) · `igdchamb1` Grande Chambre (chevet 1) · `igdchamb2` Grande Chambre (chevet 2) · `iptchamb1` Petite Chambre 1 (chevet 1) · `iptchamb2` Petite Chambre 1 (chevet 2) · `iptchamb22` Petite Chambre 2 (chevet) · `iptchamb3` Petite Chambre 3 (chevet) · `idressing` Dressing (placards).

## Règle du nom

Après suppression des espaces en début et fin : de 1 à 40 caractères Unicode, sans caractère de contrôle (U+0000 à U+001F, U+007F), sans `<` ni `>`. Les clients affichent le nom comme **texte brut** (jamais comme HTML). Un nom vide ou `null` signifie « revenir au nom d'origine ».

## Contrat d'API (figé : tous les dépôts le suivent)

Objet commun `LightName` :

```json
{"id":"dressing","default":"Dressing","name":"WC 3","version":2,"updated_at":"2026-11-07T10:15:30.123Z"}
```

`name` est `null` quand aucun nom n'a été défini ; `version` vaut 0 et `updated_at` est `null` dans ce cas. Le nom affiché est `name` si non nul, sinon `default`.

| Surface | Route | Droits |
|---|---|---|
| Cloud, lecture | `GET /api/portal/lights/names` → `200 {"lights":[LightName…]}` (33 éléments, ordre du catalogue) | utilisateur de l'armoire liée |
| Cloud, écriture | `PUT /api/portal/admin/lights/names/{id}` corps `{"name":"WC 3"}` ou `{"name":null}` → `200 LightName` + `"status":"saved"` | administrateur de l'armoire |
| Cloud, synchro gateway | `POST /api/gateway/lights/names/sync` corps `{"names":[{"id","name","version","updated_at"}…]}` (zéro à 33 éléments) → `200 {"lights":[LightName…]}` (état fusionné complet) | `GatewayAuth` |
| Gateway, lecture | `GET /api/lights/names` → `200 {"lights":[LightName…]}` | tout utilisateur authentifié (IAM LAN) ; ouvert si IAM désactivé |
| Gateway, écriture | `PUT /api/admin/lights/names/{id}` même corps et même réponse que le cloud | `adminOnlyJSON` |

Erreurs : `400 {"error":"unknown_light"}`, `400 {"error":"invalid_name"}`, `401`, `403 {"error":"forbidden"}`, `503 {"error":"names_unavailable"}` (gateway sans stockage). Mode essai à blanc : en-tête `X-Essensys-Test-Mode: dry-run` (cloud et gateway) ou `?test_mode=dry_run` (gateway) valide la requête, répond `"status":"dry_run"` et n'écrit rien. Tout changement est tracé (qui, quand, ancien et nouveau nom) : événement d'audit `light_name`.

Synchronisation gateway : à chaque cycle, l'agent envoie ses 33 entrées au cloud (`POST …/sync`) et remplace sa réplique par la réponse (pas d'écrasement d'un nom local plus récent : la fusion est faite par le cloud). Après une écriture locale, une synchronisation immédiate est tentée sans bloquer la réponse. Hors ligne, la réplique locale fait foi et la synchronisation reprend au retour de la connexion. Une gateway qui n'a jamais vu le cloud envoie ses noms au premier contact.

## Risques et inconnus

- Horloge de la gateway : une dérive de plus de 5 minutes fausse l'arbitrage (bornée côté cloud pour le futur uniquement). NTP est installé sur CM5 et Pi.
- Le conteneur backend de la CM5 ne monte que `config.yaml` en lecture seule : un répertoire dédié en écriture et la **recréation** du conteneur sont nécessaires (`docker restart` ne suffit pas).
- Une armoire par compte : un administrateur global qui a plusieurs armoires n'agit que sur celle qui est liée à son compte (sélecteur d'armoire : ticket suivant).
- Le menu Temporisations (#45) affiche aujourd'hui des libellés d'origine : il doit utiliser les noms personnalisés (les libellés renvoyés par les routes `/lights/timers` restent d'origine).
