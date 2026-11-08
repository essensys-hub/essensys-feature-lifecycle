## 1. Gateway : plages horaires et signalement (essensys-server-backend)

- [ ] 1.1 Ajouter `schedule` aux réglages `doorbell` (mode, fuseau, grille ; défaut `always`, `Europe/Paris` ; embarquer `time/tzdata`) et l'erreur `invalid_schedule` ; vérifier par des tests (défauts, relecture après redémarrage, grille à 6 lignes, ligne de 23 caractères, caractère `2`, fuseau inconnu, autres sections du fichier préservées, 403 `lan_user`)
- [ ] 1.2 Évaluer la plage à l'appui dans le service sonnette (heure de l'événement dans le fuseau, changement d'heure, hors plage : ni clignotement ni signalement ni anti-rafale armé, `ringing` conservé, `in_window` dans l'état, « Essayer » ignore la plage) ; vérifier par des tests de service avec horloge simulée
- [ ] 1.3 Ajouter le client cloud du signalement (`POST /api/gateway/doorbell/ring`, `GatewayAuth` depuis `cfg.Cloud`, 3 tentatives, abandon après 60 s, en tâche de fond, aucun jeton ni adresse journalisé, cloud non configuré : aucun appel) ; vérifier par des tests avec un faux cloud (succès, injoignable, jeton refusé, rafale, non configuré)
- [ ] 1.4 Ajouter l'événement d'audit `doorbell_schedule` et le test de non-régression `NR-server-backend-*` qui cite `#61` ; vérifier par `go build`, `go vet`, `go test ./...`, `validate_feature_manifests.py` et `check_feature_gate.py --strict`

## 2. Portail local : éditeur de plages (essensys-server-frontend)

- [ ] 2.1 Ajouter l'éditeur de grille dans l'écran « Sonnette » (7 × 24, clic et glisser, clavier, présélections « Toujours », « Jour seulement 7 h-22 h », « Jamais », choix du fuseau, indication de la case actuelle, message `invalid_schedule` en français) ; vérifier par des tests de la logique et Playwright (désactivé pour un non-administrateur, enregistrement, relecture)
- [ ] 2.2 Afficher `in_window` (la fenêtre vidéo reste active hors plage, avec la mention « hors plage : pas de clignotement ni de notification ») ; ajouter `@nr NR-server-frontend-*` en mode `no-armoire` dans `test:demo`, desktop, iPhone et iPad

## 3. Cloud : appareils, appui, notifications (essensys-user-portal-backend)

- [ ] 3.1 Ajouter la migration `022_push_devices.sql` (table `push_devices`, unicité `(platform, token)`) et les routes `PUT /api/portal/push/devices`, `DELETE /api/portal/push/devices/{id}`, `GET /api/portal/doorbell/preferences` ; vérifier par des tests (enregistrement, jeton repris par un autre utilisateur, suppression d'autrui en `404`, `invalid_platform`, `invalid_token`, aucun jeton en réponse ni en journal)
- [ ] 3.2 Ajouter l'interface `PushSender` et les expéditeurs FCM HTTP v1 et APNs (variables d'environnement, désactivés si absentes, jeton périmé supprimé, panne isolée) ; vérifier par des tests avec serveurs `httptest` (format des requêtes, `UNREGISTERED`, 500, fournisseur absent)
- [ ] 3.3 Ajouter `POST /api/gateway/doorbell/ring` (`GatewayAuth`, idempotence `(gateway_id, ring_id)`, limite 1 par 10 s, destinataires = utilisateurs liés avec `doorbell_notify=true`, `dry-run`, `at` futur borné) ; vérifier par des tests (appui reçu, idempotence, autre gateway, préférence coupée, `401`, `429`, `dry_run`)
- [ ] 3.4 Ajouter `gateway_state` à `GET /api/portal/session` ; vérifier par des tests (`none`, `online` à 30 s, `offline` à 3 min, bloc `gateway` conservé)
- [ ] 3.5 Ajouter le test de non-régression `NR-backend-*` qui cite `#61` ; vérifier par `go build`, `go vet`, `go test ./...` et les gates

## 4. Portail cloud : présence de la gateway (essensys-user-portal-frontend)

- [ ] 4.1 Afficher l'état de la gateway (« en ligne », « hors ligne », « Aucune gateway liée ») dans `PortalContextPanel` à partir de `gateway_state`, avec repli sur le comportement actuel si le champ manque ; vérifier par Playwright (matrice desktop, iPhone, iPad, `no-armoire`, trois états, champ absent) et `@nr NR-portal-frontend-*`

## 5. Ansible : secrets des notifications (essensys-ansible)

- [ ] 5.1 Passer au backend cloud les variables des fournisseurs (compte de service FCM, clé APNs `.p8`, identifiant de clé, équipe, `bundle id`, environnement APNs) depuis SOPS, sans jamais les écrire en clair ni les afficher en `--diff` ; vérifier par un `--check --diff` propre et un test hors ligne avec de fausses valeurs
- [ ] 5.2 Documenter dans le rôle la création du projet Firebase et de la clé APNs (étapes de Nicolas, sans valeur) ; vérifier par relecture

## 6. Android (essensys-android-phone-apps)

- [ ] 6.1 Ajouter la réception push (service de messages, canal `doorbell` à importance haute, permission `POST_NOTIFICATIONS` sur Android 13+, dédoublonnage par `ring_id`, ouverture de l'app au toucher) ; vérifier par des tests unitaires et par l'émulateur (notification de test, app fermée)
- [ ] 6.2 Ajouter l'option « Sonnette » dans les réglages (visible si `gateway_state != "none"`, interrupteur, permission refusée, aide, enregistrement et suppression de l'appareil, affichage « Aucune gateway liée ») ; vérifier par des tests unitaires, instrumentés et `NR-android-*`

## 7. iPhone (essensys-ios-phone-apps)

- [ ] 7.1 Ajouter la réception push APNs (capacité Notifications, autorisation, enregistrement du jeton, dédoublonnage par `ring_id`, ouverture au toucher) ; vérifier par des tests unitaires et par le simulateur (`xcrun simctl push`)
- [ ] 7.2 Ajouter l'option « Sonnette » dans les réglages (visible si `gateway_state != "none"`, interrupteur, autorisation refusée, aide, enregistrement et suppression de l'appareil, affichage « Aucune gateway liée ») ; vérifier par des tests unitaires, UI et `NR-ios-*`

## 8. Site support (essensys-support-site)

- [ ] 8.1 Mettre à jour la page `/android` (nouvelle version de l'APK) et la version de l'app iPhone ; vérifier par `npm run build` et relecture

## 9. Documentation (essensys-doc)

- [ ] 9.1 Compléter la page « Sonnette UniFi » (plages horaires, notifications, présence de la gateway, limites : pas de garantie de livraison, hors plage la vidéo locale reste affichée) et ajouter la page d'installation des fournisseurs (Firebase, APNs) ; vérifier par `mkdocs build --strict`

## 10. Mémoire (essensys-memory)

- [ ] 10.1 Compléter la synthèse « sonnette UniFi » (plages, signalement, push, `gateway_state`), mettre à jour index et log ; ne pas lancer les scripts de synchronisation ; vérifier par relecture

## 11. Qualité et déploiement (essensys-feature-lifecycle)

- [ ] 11.1 Faire un test de bout en bout avec faux UniFi, faux cloud et faux fournisseurs, sans armoire réelle (`NO_ARMOIRE=1`) ; consigner le résultat sur #61
- [ ] 11.2 Lancer `/checkup` sur la Feature et poster le rapport ; vérifier par un rapport vert
- [ ] 11.3 Déployer dans l'ordre : migration 022 et cloud, portail cloud, gateway CM5 et portail local, Ansible, puis publier l'APK et le build iPhone ; vérifier chaque étape par des contrôles en lecture seule
- [ ] 11.4 Essai réel par Nicolas (vraie sonnette, Android et iPhone physiques, dans et hors plage, hors Wi-Fi) ; consigner le résultat sur #61
