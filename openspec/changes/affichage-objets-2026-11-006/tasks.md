## 1. Cloud : disposition des objets (essensys-user-portal-backend)

- [ ] 1.1 Ajouter le modèle de disposition (`ObjectLayout`), la validation (identifiants du catalogue du genre, pas de doublon dans `order` ni dans `disabled`, `unknown_light` / `unknown_shutter` / `invalid_layout`, `reset`) et la fonction `effective` ; vérifier par des tests de domaine (33 et 16 identifiants exacts, doublon refusé, identifiant de l'autre genre refusé, `order` incomplet accepté, tout désactivé accepté, `reset` donne le défaut)
- [ ] 1.2 Ajouter la migration idempotente `021_object_layout.sql` (table `object_layout`, clé `(machine_id, kind)`) et le magasin ; vérifier par un test de migration (rejouée deux fois, `light_names` et `shutter_names` inchangées) et des tests du magasin (lecture du défaut, écriture à la version `n+1`)
- [ ] 1.3 Ajouter `GET /portal/lights/layout` et `GET /portal/shutters/layout` ; vérifier par des tests (disposition par défaut `version` 0 et `updated_at` nul, pas de champ `updated_by`, 403 sans armoire liée, genres indépendants)
- [ ] 1.4 Ajouter `PUT /portal/admin/lights/layout` et `PUT /portal/admin/shutters/layout` (administrateur de l'armoire, version `n+1`, audit `object_layout`, dry-run, `reset`) ; vérifier par des tests de routage (admin_local de l'armoire accepté, user et autre armoire 403, 400 `unknown_light` / `unknown_shutter` / `invalid_layout`, dry-run sans écriture ni version, `reset` incrémente la version)
- [ ] 1.5 Ajouter `POST /gateway/lights/layout/sync` et `POST /gateway/shutters/layout/sync` avec la fusion du document entier (plus grand `(updated_at, version, updated_by)`, égalité = valeur du cloud, futur borné à 5 minutes) ; vérifier par des tests (cloud plus récent, gateway plus récente, égalité, horloge dans le futur, document de version 0 ignoré, identifiant inconnu ignoré, 401 sans jeton)
- [ ] 1.6 Ajouter le test de non-régression `NR-backend-17` (désactiver et réordonner ne change ni `GET /portal/lights/names`, ni `GET /portal/shutters/names`, ni les tables de noms) ; vérifier par `go test ./...` vert, `NR-backend-15` et `NR-backend-16` inclus

## 2. Gateway : disposition des objets (essensys-server-backend, CM5)

- [ ] 2.1 Ajouter au magasin de fichier les sections `lights_layout` et `shutters_layout` (objets, décodeur dédié, sans passer par `namesDoc.section()`), même fichier, même clé `light_names.path`, même verrou, écriture atomique inchangée ; vérifier par des tests (fichier de #52 relu et complété, écriture de chaque section sans perte des quatre autres ni d'une section inconnue, relecture après redémarrage, chemin absent donne la disposition par défaut et 503 `names_unavailable` à l'écriture) et par la non-régression de `NR-server-backend-28` à `NR-server-backend-31`
- [ ] 2.2 Ajouter le modèle, la validation et `effective` (mêmes cas que le cloud, catalogues de 33 lumières et 16 volets) ; vérifier par des tests de domaine
- [ ] 2.3 Ajouter `GET /api/lights/layout` et `GET /api/shutters/layout` (utilisateur authentifié, ouvert si IAM désactivé, sans `updated_by`) ; vérifier par des tests de routeur (lan_user 200, sans session 401, IAM désactivé 200, défaut `version` 0)
- [ ] 2.4 Ajouter `PUT /api/admin/lights/layout` et `PUT /api/admin/shutters/layout` derrière `adminOnlyJSON`, avec audit `object_layout`, `reset` et dry-run ; vérifier par des tests de routeur (lan_admin accepté, lan_user 403, 400 invalides, dry-run sans écriture) en `NR-server-backend-32`
- [ ] 2.5 Ajouter la synchronisation dans les deux sens dans l'agent cloud (deux appels `POST /api/gateway/{lights|shutters}/layout/sync` à chaque cycle, indépendants de ceux des noms, synchro immédiate non bloquante après une écriture locale, reprise après coupure, tolérance à un cloud qui répond 404) ; vérifier par des tests avec un faux cloud (cloud plus récent, gateway plus récente, hors ligne puis retour, conflit, 404 sans effet sur les noms) en `NR-server-backend-33`
- [ ] 2.6 Documenter les sections `lights_layout` et `shutters_layout` dans `config.yaml.example` et le README (même clé `light_names.path`, aucun nouveau chemin) ; vérifier par relecture, et confirmer qu'aucune nouvelle clé de configuration n'a été ajoutée (sinon arrêter et faire revoir la matrice : Ansible et Raspberry Pi redeviendraient concernés)

## 3. Portail cloud (essensys-user-portal-frontend)

- [ ] 3.1 Ajouter `src/lights/lightLayout.ts` et `src/shutters/shutterLayout.ts` (fonction `effectiveLayout`, lecture `GET /api/portal/{lights|shutters}/layout`, repli sur le catalogue complet au 404 ou à l'échec, conservation de la dernière lecture) et leurs hooks ; vérifier par des tests de la logique (ordre incomplet, identifiant inconnu, doublon, tout désactivé, 404)
- [ ] 3.2 Filtrer et ordonner aux appels de `LightingPage.tsx` (lignes 288 et 292) et `ShuttersPage.tsx` (lignes 303 et 307), construire `allShutters` (ligne 44) et la carte « Temps de course » (ligne 231) à partir des volets actifs, filtrer `LightTimersPage.tsx` (ligne 47) ; vérifier par Playwright (lumière désactivée absente de la liste, de « Tout allumer » (requêtes inspectées) et de Temporisations ; volet désactivé absent de la liste, de « Tout ouvrir » et de « Temps de course » ; groupe vide)
- [ ] 3.3 Ajouter l'écran de gestion (administrateur seulement : interrupteur, Monter/Descendre, « Ordre d'origine », « Enregistrer » en une écriture `PUT /api/portal/admin/{lights|shutters}/layout`, erreurs 400/403/503) ; vérifier par Playwright (désactiver, réactiver, réordonner, reset, non-administrateur sans bouton ni objets masqués, nom personnalisé affiché dans l'écran)
- [ ] 3.4 Ajouter les tests `@nr NR-portal-frontend-13` en mode `no-armoire` sur desktop, iPhone et iPad (aucune requête vers l'armoire, noms de lumières et de volets inchangés, scénarios sur catalogue complet, nom de 40 caractères lisible)

## 4. Portail local (essensys-server-frontend)

- [ ] 4.1 Reprendre la logique du portail cloud avec `GET /api/{lights|shutters}/layout` ; vérifier par des tests de la logique
- [ ] 4.2 Filtrer et ordonner aux appels de `LightingPage.tsx` (lignes 227 et 231) et `ShuttersPage.tsx` (lignes 261 et 265), `allShutters` (ligne 43), « Temps de course » (ligne 193) et `LightTimersPage.tsx` (ligne 49) ; vérifier par Playwright
- [ ] 4.3 Ajouter l'écran de gestion pour `lan_admin` (ou tous si l'IAM LAN est désactivé) avec `PUT /api/admin/{lights|shutters}/layout` ; vérifier par Playwright
- [ ] 4.4 Ajouter `@nr NR-server-frontend-10` en mode `no-armoire`, l'inscrire dans le script `test:demo`, desktop, iPhone et iPad

## 5. App Android (essensys-android-phone-apps)

- [ ] 5.1 Ajouter `ObjectLayout.kt` (modèle, `effective`, validation), `readLightLayout` / `readShutterLayout` dans `ComfortRepository` (cloud et réseau local, repli sur le catalogue complet) et les `LightLayoutViewModel` / `ShutterLayoutViewModel` ; vérifier par des tests unitaires (ordre incomplet, identifiant inconnu, 404, tout désactivé, dernière lecture conservée)
- [ ] 5.2 Filtrer et ordonner `LightingScreen.kt` (ligne 56, groupe et lignes partagent la liste), `ShuttersScreen.kt` (lignes 53, 62, 106 : liste, lecture des temps, carte « Temps de course ») et `LightTimerScreens.kt` (ligne 49) ; vérifier par des tests d'interface (lumière désactivée absente de la liste, de « Tout allumer » (commandes inspectées) et des Temporisations ; volet désactivé absent de « Temps de course » ; `testTag` `time-current-<id>` de `TravelTimeFlowTest` inchangés pour les volets actifs)
- [ ] 5.3 Ajouter l'écran de gestion pour l'administrateur (interrupteur, Monter/Descendre, « Ordre d'origine », « Enregistrer », écritures cloud et local, messages d'erreur) ; vérifier par des tests unitaires et instrumentés (`NR-android-27`, aucune commande vers l'armoire, non-administrateur sans accès)
- [ ] 5.4 Préparer la version 2.8.0 (notes, tag `android-v2.8.0`) ; vérifier par `testDebugUnitTest`, `lintDebug` et `check_release_apk.py`

## 6. App iPhone (essensys-ios-phone-apps)

- [ ] 6.1 Ajouter `ObjectLayout.swift` (modèle, `effective`, validation), la lecture des dispositions (cloud et réseau local, repli sur le catalogue complet) et `LightLayoutModel` / `ShutterLayoutModel` dans `FeatureModels.swift`, et compléter `UITestBackend.swift` ; vérifier par des tests unitaires
- [ ] 6.2 Filtrer et ordonner `ControlScreens.swift` (lignes 64, 106 et 146), `ControlModel.swift` (ligne 74) et `LightTimersScreen.swift` (ligne 31) ; vérifier par XCUITest (objet désactivé absent des listes, des groupes et de « Temps de course » ; ordre appliqué ; `IndexTableTests.swift` et `ParityUITests.swift` inchangés)
- [ ] 6.3 Ajouter l'écran de gestion pour l'administrateur avec les écritures cloud et local et les messages d'erreur ; vérifier par tests unitaires et XCUITest (`NR-ios-27`, iPhone SE inclus pour un nom de 40 caractères, non-administrateur sans accès)
- [ ] 6.4 Préparer la version 2.8.0 (`MARKETING_VERSION`, `CURRENT_PROJECT_VERSION`) ; vérifier par build et tests sur simulateur

## 7. Documentation (essensys-doc)

- [ ] 7.1 Rédiger la page « Activer, désactiver et ordonner les lumières et les volets » (écran de gestion, droits de l'administrateur, effet sur les groupes, Temporisations et « Temps de course », synchronisation cloud et local, ordre d'origine, limites : scénarios non filtrés) et l'entrée de menu, en lien avec `renommer-lumiere.md` et `renommer-volet.md` ; vérifier par `mkdocs build --strict`
- [ ] 7.2 Compléter le guide d'installation et de dépannage (`noms-lumieres-gateway.md`) : le fichier contient maintenant quatre sections (`lights`, `shutters`, `lights_layout`, `shutters_layout`), sauvegarde, 503 `names_unavailable`, ordre de déploiement (cloud puis gateway), risque d'une gateway restée à la version de #41 (sections effacées, rétablies depuis le cloud), retour arrière ; vérifier par recherche des anciens libellés

## 8. Mémoire (essensys-memory)

- [ ] 8.1 Ajouter une synthèse « affichage des objets » (document par genre, routes jumelles, fusion du document entier, deux sections du même fichier, règle de repli), la relier aux synthèses de noms, mettre à jour index et log ; ne pas lancer les scripts de synchronisation (ils ajoutent des adresses du réseau local dans un dépôt public) ; vérifier par relecture

## 9. Qualité et déploiement (essensys-feature-lifecycle)

- [ ] 9.1 Faire un test de bout en bout sans armoire réelle (`NO_ARMOIRE=1`) : une lumière désactivée et un volet réordonné dans le cloud arrivent sur la gateway et les clients, l'inverse depuis la gateway, conflit résolu sur le document entier, noms inchangés, scénarios sur catalogue complet ; consigner le résultat sur #55
- [ ] 9.2 Lancer `/checkup` sur la Feature et poster le rapport ; vérifier par un rapport vert (build, lint, unitaires, `NR-*`, applicatifs, `feature-gate`, `security-gate`)
- [ ] 9.3 Déployer le cloud (migration `021`), puis la gateway CM5 (SHA épinglés, `--check --diff` d'abord, vérifier au préalable que la gateway est en version #52 au moins, redémarrage du conteneur suffisant car aucun nouveau montage) ; vérifier par un `GET` des dispositions et des noms contre l'environnement réel, sans piloter l'armoire
- [ ] 9.4 Publier l'APK 2.8.0 (tag `android-v2.8.0`) ; vérifier par le téléchargement de l'APK depuis la release
- [ ] 9.5 Envoyer la build iPhone 2.8.0 sur TestFlight ; vérifier par la build traitée dans App Store Connect

## 10. Site support (essensys-support-site)

- [ ] 10.1 Mettre à jour la page `/android` (version 2.8.0, lien de l'APK) et le test `NR-site-*` existant de cette page après la publication de l'APK ; déployer avec `support_site_version` épinglé ; vérifier par `npm run build`, Playwright et le téléchargement de l'APK depuis la page publiée
