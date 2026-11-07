## 1. Cloud : temporisations (essensys-user-portal-backend) (#53)

- [ ] 1.1 Ajouter le catalogue `{id, libellé, clé}` des six lumières et la validation (identifiant connu, entier de 0 à 255) ; vérifier par des tests de domaine (six clés exactes 521, 555, 556, 557, 561, 562 ; 0 et 255 acceptés ; 256, -1, 7.5 et identifiant inconnu refusés)
- [ ] 1.2 Ajouter `GET /portal/lights/timers` (cache gateway, `null` si jamais lue) ; vérifier par des tests (valeur connue, clé absente donne `null`, jamais 0)
- [ ] 1.3 Ajouter `PUT /portal/admin/lights/timers/{id}` : contrôle « administrateur de cette armoire », file d'actions, mise à jour du cache, audit, dry-run ; vérifier par des tests de routage (admin_local de l'armoire accepté, admin_local d'une autre armoire, user, guest_local et support refusés en 403 sans action, dry-run sans action)
- [ ] 1.4 Ajouter la migration idempotente `018_lights_timers_sync_profile.sql` (plages `[[521,521],[555,557],[561,562]]`, pull et push) ; vérifier par un test de migration (rejouée deux fois sans doublon, aucun UPDATE ni DELETE)

## 2. Gateway : temporisations (essensys-server-backend, CM5 et Raspberry Pi) (#17)

- [ ] 2.1 Ajouter le catalogue des six lumières, la validation et les constantes de clés ; vérifier par des tests (mêmes cas que le cloud)
- [ ] 2.2 Ajouter `GET /api/admin/lights/timers` et les six clés à la rotation de lecture et au snapshot ; vérifier par des tests (valeur lue, clé jamais lue inconnue, présence dans la rotation)
- [ ] 2.3 Ajouter `PUT /api/admin/lights/timers/{id}` derrière `adminOnly`, avec file d'actions et audit ; vérifier par des tests de routeur (lan_admin accepté, lan_user 403, sans session 401, IAM LAN désactivé comme les autres routes, valeur hors plage 400)
- [ ] 2.4 Accepter les six clés dans le filtre de poussée vers le cloud ; vérifier par un test du filtre

## 3. Portail cloud (essensys-user-portal-frontend) (#39)

- [ ] 3.1 Ajouter la logique pure (catalogue, raccourcis 15, 30, 60, 0, validation de la valeur libre) et la lecture par `GET /portal/lights/timers` ; vérifier par des tests de la logique
- [ ] 3.2 Ajouter le menu « Temporisations » (section administration, filtré par rôle) et sa page ; vérifier par Playwright (six lumières, « inconnue » sans valeur, masqué pour un utilisateur simple)
- [ ] 3.3 Ajouter le panneau de réglage dans la fiche des six lumières de `LightingPage` ; vérifier par Playwright (Dressing : même valeur que le menu central, valeur libre 7, 300 refusé, aucune requête hors mode test)
- [ ] 3.4 Ajouter la session de démonstration à rôle et les tests `@nr NR-portal-frontend-10` en mode `no-armoire` sur desktop, iPhone et iPad

## 4. Portail local (essensys-server-frontend) (#10)

- [ ] 4.1 Reprendre la logique et l'API (`GET /api/admin/lights/timers`) du portail cloud ; vérifier par des tests de la logique
- [ ] 4.2 Ajouter l'entrée « Temporisations » dans le menu (visible pour `lan_admin`, ou tous si l'IAM LAN est désactivé) et sa page ; vérifier par Playwright (rôle admin et non admin)
- [ ] 4.3 Ajouter le réglage dans la fiche des six lumières ; vérifier par Playwright (valeur libre, hors ligne désactivé)
- [ ] 4.4 Ajouter `@nr NR-server-frontend-7` en mode `no-armoire`, l'inscrire dans le script `test:demo`, desktop, iPhone et iPad

## 5. Raspberry Pi (essensys-raspberry-install) (#20)

- [ ] 5.1 Vérifier que l'installation du Pi 4 (sans PostgreSQL) expose les nouvelles routes et lit les six clés ; vérifier par le test d'installation du dépôt et un relevé des routes sur l'image construite
- [ ] 5.2 Ajouter les clés 521, 561 et 562 à la documentation de maintenance `docs/maintenance/debug.md` ; vérifier par relecture du tableau des temps d'extinction

## 6. App Android (essensys-android-phone-apps) (#43)

- [ ] 6.1 Décoder le rôle à la connexion (cloud et LAN), le mémoriser dans `SessionState` (`isAdmin`) ; vérifier par des tests unitaires (admin, utilisateur simple, rôle absent donne non administrateur)
- [ ] 6.2 Ajouter le catalogue, les raccourcis et la validation (`LightTimer`), la lecture et l'écriture (`ComfortRepository`) cloud et LAN, et la relecture à 5, 10 et 20 s ; vérifier par des tests MockWebServer (NR-android-24 : clés, plage 0 à 255)
- [ ] 6.3 Ajouter l'écran « Temporisations » (nouvelle `Feature`, tuile d'accueil) et le réglage dans les lumières concernées ; vérifier par des tests instrumentés (liste, Dressing, valeur libre 7, 300 refusé, masqué pour un utilisateur simple)
- [ ] 6.4 Préparer la version 2.5.0 (notes, tag `android-v2.5.0`) ; vérifier par `testDebugUnitTest`, `lintDebug` et `check_release_apk.py`

## 7. App iPhone (essensys-ios-phone-apps) (#43)

- [ ] 7.1 Décoder le rôle (DTO, `AuthRepository`), mémoriser `isAdmin` dans `SessionState` sans persistance dans le trousseau (relu à chaque connexion) ; vérifier par des tests Swift Testing
- [ ] 7.2 Ajouter le catalogue, les raccourcis, la validation, la lecture et l'écriture (`ComfortRepository`) et la relecture à 5, 10 et 20 s ; vérifier par des tests (NR-ios-24)
- [ ] 7.3 Ajouter l'écran « Temporisations » (`Feature.lightTimers`, tuile) et le réglage dans les lumières concernées ; vérifier par XCUITest avec `UITestBackend` (liste, Dressing, valeur libre, masqué pour un utilisateur simple)
- [ ] 7.4 Préparer la version 2.5.0 (`MARKETING_VERSION`, `CURRENT_PROJECT_VERSION`) ; vérifier par build et tests sur simulateur

## 8. Site support (essensys-support-site) (#21)

- [ ] 8.1 Mettre à jour la page `/android` (version, taille, SHA-256 de l'APK 2.5.0) et le test `NR-site-5` ; vérifier par `npm run build` et Playwright
- [ ] 8.2 Ajouter l'entrée du catalogue sur les temporisations ; vérifier par le test du catalogue

## 9. Documentation (essensys-doc) (#23)

- [ ] 9.1 Rédiger la page de réglage des temporisations (menu central et fiche lumière, valeurs, limite de l'écran de l'armoire) et l'entrée du guide utilisateur ; vérifier par le build de la documentation
- [ ] 9.2 Corriger les clés de temporisation (521, 555 à 557, 561, 562) dans les pages d'installation et de dépannage ; vérifier par recherche des anciennes valeurs

## 10. Mémoire (essensys-memory) (#24)

- [ ] 10.1 Mettre à jour la fiche de la carte SC942C et la page de la table d'échange (cases 518, 534, 550), puis lancer `sync-sources.sh`, `extract-git-history.sh` et `update-roadmap.sh` ; vérifier par `openspec validate --strict` et la présence du change dans la roadmap

## 11. Qualité et déploiement (essensys-feature-lifecycle) (#46)

- [ ] 11.1 Faire le test sur banc (jamais sur une armoire réelle) : un réglage depuis une app s'applique et la lumière s'éteint après le délai, une valeur libre de 7 minutes n'est pas écrasée par l'écran de l'armoire ; consigner le résultat sur #45
- [ ] 11.2 Lancer `/checkup` sur la Feature et poster le rapport ; vérifier par un rapport vert
- [ ] 11.3 Déployer le cloud puis la gateway CM5 et Pi (SHA épinglés, `--check --diff` d'abord) ; vérifier par un `GET` des temporisations contre l'environnement réel, sans piloter d'armoire
- [ ] 11.4 Publier l'APK 2.5.0 (tag `android-v2.5.0`) et déployer la page `/android` du site support ; vérifier par le téléchargement de l'APK et la page publiée
- [ ] 11.5 Envoyer la build iPhone sur TestFlight ; vérifier par la build traitée dans App Store Connect
