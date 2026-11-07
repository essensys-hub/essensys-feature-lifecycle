## 1. Cloud : noms des volets (essensys-user-portal-backend)

- [ ] 1.1 Ajouter le catalogue des 16 volets et stores (`id`, nom d'origine, ordre, voir design) et la validation du nom (réutiliser la règle des lumières : rogné, 1 à 40 caractères, sans contrôle ni `<` `>`) ; vérifier par des tests de domaine (16 identifiants exacts, `voletstore` garde ses guillemets, 40 accepté, 41 refusé, balise refusée, vide = remise à zéro, un identifiant de lumière est refusé)
- [ ] 1.2 Ajouter la migration idempotente `020_shutter_names.sql` (table `shutter_names`) et le magasin ; vérifier par un test de migration (rejouée deux fois, `light_names` inchangée) et des tests du magasin
- [ ] 1.3 Ajouter `GET /portal/shutters/names` ; vérifier par des tests (16 éléments sous la clé `shutters`, `null` par défaut, 403 sans armoire liée)
- [ ] 1.4 Ajouter `PUT /portal/admin/shutters/names/{id}` (administrateur de l'armoire, version, audit `shutter_name`, dry-run) ; vérifier par des tests de routage (admin_local de l'armoire accepté, user et autre armoire 403, remise à zéro, 400 `unknown_shutter` et `invalid_name`, dry-run sans écriture)
- [ ] 1.5 Ajouter `POST /gateway/shutters/names/sync` avec la fusion (plus grand `(updated_at, version, updated_by)`, égalité = valeur du cloud, futur borné à 5 minutes) ; vérifier par des tests (cloud plus récent, gateway plus récente, égalité, horloge dans le futur, 401 sans jeton)
- [ ] 1.6 Ajouter le test de non-régression `NR-backend-16` (renommer un volet ne change ni `GET /portal/lights/names` ni la table `light_names`) ; vérifier par `go test ./...` vert, `NR-backend-15` de #41 inclus

## 2. Gateway : noms des volets (essensys-server-backend, CM5)

- [ ] 2.1 Refactorer le magasin de fichier pour porter deux sections, `lights` et `shutters`, dans le même fichier et sous la même clé `light_names.path` (version du fichier 1, section absente = vide, écriture atomique inchangée, un seul verrou) ; l'écriture d'une section préserve l'autre et toute section inconnue ; vérifier par des tests (fichier de #41 relu et complété, écriture volet puis lumière sans perte, section inconnue conservée, relecture après redémarrage, chemin absent donne les noms d'origine et 503 à l'écriture) et par la non-régression de `NR-server-backend-28` et `NR-server-backend-29`
- [ ] 2.2 Ajouter le catalogue des 16 volets et la validation (mêmes cas que le cloud) ; vérifier par des tests (16 identifiants exacts, 40/41 caractères, balise, `unknown_shutter`)
- [ ] 2.3 Ajouter `GET /api/shutters/names` (utilisateur authentifié, ouvert si IAM désactivé) ; vérifier par des tests de routeur (lan_user 200, sans session 401, IAM désactivé 200, clé `shutters`)
- [ ] 2.4 Ajouter `PUT /api/admin/shutters/names/{id}` derrière `adminOnlyJSON`, avec audit `shutter_name` et dry-run ; vérifier par des tests de routeur (lan_admin accepté, lan_user 403, 400 invalides, dry-run sans écriture) en `NR-server-backend-30`
- [ ] 2.5 Ajouter la synchronisation dans les deux sens dans l'agent cloud (`POST /api/gateway/shutters/names/sync` à chaque cycle, indépendante de celle des lumières, synchro immédiate non bloquante après une écriture locale, reprise après coupure, tolérance à un cloud qui répond 404) ; vérifier par des tests avec un faux cloud (cloud plus récent, gateway plus récente, hors ligne puis retour, conflit, 404 sans effet sur les lumières) en `NR-server-backend-31`
- [ ] 2.6 Documenter la section `shutters` dans `config.yaml.example` et le README (même clé `light_names.path`, aucun nouveau chemin) ; vérifier par relecture, et confirmer qu'aucune nouvelle clé de configuration n'a été ajoutée (sinon arrêter et faire revoir la matrice : Ansible et Raspberry Pi redeviendraient concernés)

## 3. Portail cloud (essensys-user-portal-frontend)

- [ ] 3.1 Ajouter la lecture des noms (`GET /api/portal/shutters/names`, repli sur les noms d'origine) et la fonction d'affichage dans `ShuttersPage.tsx` ; vérifier par des tests de la logique
- [ ] 3.2 Afficher le nom personnalisé dans la liste des commandes (les deux groupes), la carte « Temps de course » et les messages « Ouvert », « Fermé » et « temps de course réglé » ; vérifier par Playwright (« Volet 1 Salon » renommé « Volet baie vitrée » apparaît dans la liste, dans « Temps de course » et dans le message)
- [ ] 3.3 Ajouter le champ « Nom » et le bouton « Nom d'origine » pour l'administrateur seulement ; vérifier par Playwright (renommer, remise à zéro, 41 caractères refusé, non-administrateur sans champ, `Store "nord"` affiché tel quel)
- [ ] 3.4 Ajouter les tests `@nr NR-portal-frontend-12` en mode `no-armoire` sur desktop, iPhone et iPad (aucune requête vers l'armoire, noms de lumières inchangés, nom de 40 caractères lisible)

## 4. Portail local (essensys-server-frontend)

- [ ] 4.1 Reprendre la logique du portail cloud avec `GET /api/shutters/names` ; vérifier par des tests de la logique
- [ ] 4.2 Afficher le nom personnalisé dans la liste, la carte « Temps de course » et les messages de la page Volets ; vérifier par Playwright
- [ ] 4.3 Ajouter le champ « Nom » et « Nom d'origine » pour `lan_admin` (ou tous si l'IAM LAN est désactivé) avec `PUT /api/admin/shutters/names/{id}` ; vérifier par Playwright
- [ ] 4.4 Ajouter `@nr NR-server-frontend-9` en mode `no-armoire`, l'inscrire dans le script `test:demo`, desktop, iPhone et iPad

## 5. App Android (essensys-android-phone-apps)

- [ ] 5.1 Ajouter la lecture des noms de volets (cloud et réseau local, repli sur les noms d'origine) et le nom affiché dans `ComfortRepository` ; vérifier par des tests unitaires (nom personnalisé, repli, nom spécial affiché tel quel, guillemets)
- [ ] 5.2 Afficher le nom partout dans `ShuttersScreen.kt` : liste des deux groupes, confirmations d'ouverture et de fermeture, carte « Temps de course » ; vérifier par des tests d'interface (les `testTag` `time-current-<id>` de `TravelTimeFlowTest` restent valables)
- [ ] 5.3 Ajouter le champ « Nom » et « Nom d'origine » pour l'administrateur avec les écritures cloud et local, et les messages d'erreur ; vérifier par des tests unitaires et instrumentés (`NR-android-26`, aucune commande vers l'armoire)
- [ ] 5.4 Préparer la version 2.7.0 (notes, tag `android-v2.7.0`) ; vérifier par `testDebugUnitTest`, `lintDebug` et `check_release_apk.py`

## 6. App iPhone (essensys-ios-phone-apps)

- [ ] 6.1 Ajouter la lecture des noms de volets (cloud et réseau local, repli sur les noms d'origine) et le nom affiché dans `ComfortRepository` ; vérifier par des tests unitaires
- [ ] 6.2 Afficher le nom partout dans `ControlScreens.swift` : liste des deux groupes, confirmations, carte « Temps de course » ; vérifier par XCUITest (iPhone SE inclus pour un nom de 40 caractères)
- [ ] 6.3 Ajouter le champ « Nom » et « Nom d'origine » pour l'administrateur avec les écritures cloud et local, et les messages d'erreur ; vérifier par tests unitaires et XCUITest (`NR-ios-26`)
- [ ] 6.4 Préparer la version 2.7.0 (`MARKETING_VERSION`, `CURRENT_PROJECT_VERSION`) ; vérifier par build et tests sur simulateur

## 7. Documentation (essensys-doc)

- [ ] 7.1 Rédiger la page « Renommer un volet ou un store » (fiche du volet, droits de l'administrateur, nom d'origine, synchronisation cloud et local, limites, écran « Temps de course ») et l'entrée de menu, ou étendre la page « Renommer une lumière » si la structure le justifie ; vérifier par `mkdocs build --strict`
- [ ] 7.2 Compléter le guide d'installation et de dépannage : le fichier des noms contient maintenant deux sections (`lights`, `shutters`), sauvegarde, 503 `names_unavailable`, retour arrière ; vérifier par recherche des anciens libellés

## 8. Mémoire (essensys-memory)

- [ ] 8.1 Compléter la synthèse « noms personnalisés » avec les volets (catalogue de 16, section `shutters` du même fichier, routes jumelles), mettre à jour index et log ; ne pas lancer les scripts de synchronisation (ils ajoutent des adresses du réseau local dans un dépôt public) ; vérifier par relecture

## 9. Qualité et déploiement (essensys-feature-lifecycle)

- [ ] 9.1 Faire un test de bout en bout sans armoire réelle (`NO_ARMOIRE=1`) : « Volet 1 Salon » renommé dans le cloud arrive sur la gateway, renommé sur la gateway arrive dans le cloud, conflit résolu, noms des lumières inchangés ; consigner le résultat sur #52
- [ ] 9.2 Lancer `/checkup` sur la Feature et poster le rapport ; vérifier par un rapport vert (build, lint, unitaires, `NR-*`, applicatifs, `feature-gate`, `security-gate`)
- [ ] 9.3 Déployer le cloud (migration `020`), puis la gateway CM5 (SHA épinglés, `--check --diff` d'abord, redémarrage du conteneur suffisant car aucun nouveau montage) ; vérifier par un `GET` des noms de volets et de lumières contre l'environnement réel, sans piloter l'armoire
- [ ] 9.4 Publier l'APK 2.7.0 (tag `android-v2.7.0`) ; vérifier par le téléchargement de l'APK depuis la release
- [ ] 9.5 Envoyer la build iPhone 2.7.0 sur TestFlight ; vérifier par la build traitée dans App Store Connect

## 10. Site support (essensys-support-site)

- [ ] 10.1 Mettre à jour la page `/android` (version 2.7.0, lien de l'APK) et le test `NR-site-5` après la publication de l'APK ; déployer avec `support_site_version` épinglé ; vérifier par `npm run build`, Playwright et le téléchargement de l'APK depuis la page publiée
