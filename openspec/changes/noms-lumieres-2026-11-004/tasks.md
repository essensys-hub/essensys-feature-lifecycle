## 1. Cloud : noms des lumières (essensys-user-portal-backend) (#55)

- [ ] 1.1 Ajouter le catalogue des 33 lumières (`id`, nom d'origine, ordre) et la validation du nom (rogné, 1 à 40 caractères, sans contrôle ni `<` `>`) ; vérifier par des tests de domaine (33 identifiants exacts, 40 accepté, 41 refusé, balise refusée, vide = remise à zéro)
- [ ] 1.2 Ajouter la migration idempotente `019_light_names.sql` et le magasin `light_names` ; vérifier par un test de migration (rejouée deux fois) et des tests du magasin
- [ ] 1.3 Ajouter `GET /portal/lights/names` ; vérifier par des tests (33 éléments, `null` par défaut, 403 sans armoire liée)
- [ ] 1.4 Ajouter `PUT /portal/admin/lights/names/{id}` (administrateur de l'armoire, version, audit `light_name`, dry-run) ; vérifier par des tests de routage (admin_local de l'armoire accepté, user et autre armoire 403, remise à zéro, 400 `unknown_light` et `invalid_name`)
- [ ] 1.5 Ajouter `POST /gateway/lights/names/sync` avec la fusion (plus grand `(updated_at, version, updated_by)`, futur borné à 5 minutes) ; vérifier par des tests (cloud plus récent, gateway plus récente, égalité, horloge dans le futur, 401 sans jeton)

## 2. Gateway : noms des lumières (essensys-server-backend, CM5 et Raspberry Pi) (#19)

- [ ] 2.1 Ajouter le catalogue et la validation (mêmes cas que le cloud) et le magasin de fichier atomique (`light_names.path`) ; vérifier par des tests (relecture après redémarrage, écriture atomique, chemin absent donne les noms d'origine et 503 à l'écriture)
- [ ] 2.2 Ajouter `GET /api/lights/names` (utilisateur authentifié, ouvert si IAM désactivé) ; vérifier par des tests de routeur (lan_user 200, sans session 401, IAM désactivé 200)
- [ ] 2.3 Ajouter `PUT /api/admin/lights/names/{id}` derrière `adminOnlyJSON`, avec audit et dry-run ; vérifier par des tests de routeur (lan_admin accepté, lan_user 403, 400 invalides)
- [ ] 2.4 Ajouter la synchronisation dans les deux sens dans l'agent cloud (`POST /api/gateway/lights/names/sync` à chaque cycle, synchro immédiate non bloquante après une écriture locale, reprise après coupure) ; vérifier par des tests avec un faux cloud (cloud plus récent, gateway plus récente, hors ligne puis retour, conflit)

## 3. Portail cloud (essensys-user-portal-frontend) (#41)

- [ ] 3.1 Ajouter la lecture des noms (`GET /api/portal/lights/names`, repli sur les noms d'origine) et la fonction d'affichage ; vérifier par des tests de la logique
- [ ] 3.2 Afficher le nom personnalisé dans les listes d'éclairage, la fiche, l'écran Temporisations et les messages de dernière action ; vérifier par Playwright (« Dressing » renommé « WC 3 » apparaît dans la liste et dans Temporisations)
- [ ] 3.3 Ajouter le champ « Nom » et le bouton « Nom d'origine » dans la fiche, pour l'administrateur seulement ; vérifier par Playwright (renommer, remise à zéro, 41 caractères refusé, non-administrateur sans champ)
- [ ] 3.4 Ajouter les tests `@nr NR-portal-frontend-11` en mode `no-armoire` sur desktop, iPhone et iPad (aucune requête vers l'armoire)

## 4. Portail local (essensys-server-frontend) (#12)

- [ ] 4.1 Reprendre la logique du portail cloud avec `GET /api/lights/names` ; vérifier par des tests de la logique
- [ ] 4.2 Afficher le nom personnalisé dans les listes, la fiche, l'écran Temporisations et le tableau de bord ; vérifier par Playwright
- [ ] 4.3 Ajouter le champ « Nom » et « Nom d'origine » pour `lan_admin` (ou tous si l'IAM LAN est désactivé) avec `PUT /api/admin/lights/names/{id}` ; vérifier par Playwright
- [ ] 4.4 Ajouter `@nr NR-server-frontend-8` en mode `no-armoire`, l'inscrire dans le script `test:demo`, desktop, iPhone et iPad

## 5. Ansible : CM5 (essensys-ansible) (#14)

- [ ] 5.1 Créer le répertoire des noms en écriture sur la CM5, le monter dans le conteneur backend et poser la clé `light_names.path` dans `config.yaml` (rôles `raspberry_backend` et compose) ; vérifier par un `--check --diff` propre et par la lecture du compose rendu (montage en écriture, répertoire dédié, jamais `config.yaml` en écriture)
- [ ] 5.2 Documenter dans le rôle que le conteneur doit être recréé (et non redémarré) au premier déploiement ; vérifier par la tâche ou la note correspondante

## 6. Raspberry Pi 4 (essensys-raspberry-install) (#22)

- [ ] 6.1 Créer le répertoire des noms, poser `light_names.path` dans la configuration et donner les droits d'écriture au service, dans les scripts d'installation et de mise à jour du Pi 4 (sans PostgreSQL) ; vérifier par le test d'installation du dépôt
- [ ] 6.2 Documenter le stockage des noms et la sauvegarde du fichier dans `docs/maintenance/` ; vérifier par relecture

## 7. App Android (essensys-android-phone-apps) (#45)

- [ ] 7.1 Ajouter la lecture des noms (cloud et réseau local, repli sur les noms d'origine) et le nom affiché dans `ComfortRepository` ; vérifier par des tests unitaires (nom personnalisé, repli, nom spécial affiché tel quel)
- [ ] 7.2 Afficher le nom partout : listes d'éclairage, fiche, écran Temporisations, éditeur de scénarios, confirmations ; vérifier par des tests d'interface
- [ ] 7.3 Ajouter le champ « Nom » et « Nom d'origine » pour l'administrateur avec les écritures cloud et local, et les messages d'erreur ; vérifier par des tests unitaires et instrumentés (`NR-android-25`)
- [ ] 7.4 Préparer la version 2.6.0 (notes, tag `android-v2.6.0`) ; vérifier par `testDebugUnitTest`, `lintDebug` et `check_release_apk.py`

## 8. App iPhone (essensys-ios-phone-apps) (#45)

- [ ] 8.1 Ajouter la lecture des noms (cloud et réseau local, repli sur les noms d'origine) et le nom affiché dans `ComfortRepository` ; vérifier par des tests unitaires
- [ ] 8.2 Afficher le nom partout : listes d'éclairage, fiche, écran Temporisations, éditeur de scénarios, confirmations ; vérifier par XCUITest
- [ ] 8.3 Ajouter le champ « Nom » et « Nom d'origine » pour l'administrateur avec les écritures cloud et local, et les messages d'erreur ; vérifier par tests unitaires et XCUITest (`NR-ios-25`)
- [ ] 8.4 Préparer la version 2.6.0 (`MARKETING_VERSION`, `CURRENT_PROJECT_VERSION`) ; vérifier par build et tests sur simulateur

## 9. Documentation (essensys-doc) (#25)

- [ ] 9.1 Rédiger la page « Renommer une lumière » (fiche de la lumière, droits de l'administrateur, nom d'origine, synchronisation cloud et local, limites) et l'entrée de menu ; vérifier par `mkdocs build --strict`
- [ ] 9.2 Ajouter au guide d'installation et de dépannage le fichier des noms de la gateway (emplacement, sauvegarde, 503 `names_unavailable`) ; vérifier par recherche des anciens libellés

## 10. Mémoire (essensys-memory) (#26)

- [ ] 10.1 Ajouter une synthèse « noms personnalisés des lumières » (modèle de droits, fusion, stockage), mettre à jour index et log ; ne pas lancer les scripts de synchronisation (ils ajoutent des adresses du réseau local dans un dépôt public) ; vérifier par relecture

## 11. Qualité et déploiement (essensys-feature-lifecycle) (#50)

- [ ] 11.1 Faire un test de bout en bout sans armoire réelle : « Dressing » renommé « WC 3 » dans le cloud arrive sur la gateway, renommé sur la gateway arrive dans le cloud, conflit résolu ; consigner le résultat sur #41
- [ ] 11.2 Lancer `/checkup` sur la Feature et poster le rapport ; vérifier par un rapport vert
- [ ] 11.3 Déployer le cloud, puis la gateway CM5 (SHA épinglés, `--check --diff` d'abord, recréation du conteneur) ; vérifier par un `GET` des noms contre l'environnement réel, sans piloter l'armoire
- [ ] 11.4 Publier l'APK 2.6.0 (tag `android-v2.6.0`) ; vérifier par le téléchargement de l'APK depuis la release
- [ ] 11.5 Envoyer la build iPhone 2.6.0 sur TestFlight ; vérifier par la build traitée dans App Store Connect

## 12. Site support (essensys-support-site) (#23)

- [ ] 12.1 Mettre à jour la page `/android` (version 2.6.0, lien de l'APK) et le test `NR-site-5` après la publication de l'APK ; déployer avec `support_site_version` épinglé ; vérifier par `npm run build`, Playwright et le téléchargement de l'APK depuis la page publiée
