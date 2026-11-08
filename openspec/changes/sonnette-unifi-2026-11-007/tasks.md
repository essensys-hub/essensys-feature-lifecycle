## 1. Gateway : sonnette UniFi (essensys-server-backend) (#25)

- [ ] 1.1 Essai de faisabilité, sur la console réelle en lecture seule (sans identifiant dans le dépôt) : l'événement de sonnerie est-il exposé par l'API d'intégration (sinon repli par interrogation) ; cadence de lecture de l'armoire (délai entre deux ordres de lumière) ; ffmpeg présent ou non dans l'image de la CM5 ; consigner les résultats dans l'issue et ajuster la phase de clignotement ; vérifier par un compte rendu sur l'issue
- [ ] 1.2 Étendre `internal/unifi` (écoute des événements de la caméra de sonnette, reconnexion avec attente croissante, instantané) ; vérifier par des tests avec un faux serveur UniFi (sonnerie, autre caméra, console injoignable, reconnexion, aucune adresse ni clé dans les journaux)
- [ ] 1.3 Ajouter le service sonnette (état `ringing` 60 s, une séquence à la fois, anti-rafale, clignotement puis restauration, exclusion d'une lumière commandée à la main) ; vérifier par des tests de service avec une table d'échange simulée (séquence complète, rafale, commande manuelle, aucune lumière choisie)
- [ ] 1.4 Ajouter le magasin des réglages (section `doorbell` du fichier de `light_names.path`, sections brutes préservées, atomique) et `GET/PUT /api/admin/doorbell/settings` ; vérifier par des tests (valeurs par défaut, relecture après redémarrage, `unknown_light`, `invalid_blinks`, `unknown_camera`, 403 `lan_user`, 503 `names_unavailable`, toutes les sections coexistent)
- [ ] 1.5 Ajouter `GET /api/doorbell/status`, `GET /api/doorbell/stream` et `POST /api/admin/doorbell/test` (dry-run) ; vérifier par des tests de routeur (lan_user 200, sans session 401, IAM désactivé 200, flux 503 console injoignable, essai à sec sans écriture dans l'armoire)
- [ ] 1.6 Ajouter le test de non-régression `NR-server-backend-*` qui cite le ticket `#58`, le manifest et le change du dépôt ; vérifier par `go build`, `go vet`, `go test ./...`, `validate_feature_manifests.py` et `check_feature_gate.py --strict`

## 2. Portail local (essensys-server-frontend) (#18)

- [ ] 2.1 Ajouter la lecture de l'état, la fenêtre « Quelqu'un sonne » avec la vidéo (toutes pages, fermeture sans réouverture pour la même sonnerie) ; vérifier par des tests de la logique et Playwright (faux état `ringing`, désactivé, indisponible)
- [ ] 2.2 Ajouter l'écran « Sonnette » pour l'administrateur (activer, caméra, lumières avec noms personnalisés et sans les lumières masquées, clignotements, « Essayer », messages d'erreur) ; vérifier par Playwright (réglage, essai, non-administrateur sans écran)
- [ ] 2.3 Ajouter `@nr NR-server-frontend-*` en mode `no-armoire` et l'inscrire dans le script `test:demo`, desktop, iPhone et iPad

## 3. Ansible : CM5 (essensys-ansible) (#16)

- [ ] 3.1 Vérifier les variables `unifi_*` des rôles `raspberry_backend` et `raspberry_compose`, ajouter celles que la spec exige (identifiant de caméra si fourni par la configuration) et déployer la clé d'API par SOPS ; vérifier par un `--check --diff` propre et par la lecture du `config.yaml` rendu (aucun secret en clair)
- [ ] 3.2 Documenter dans le rôle l'activation d'UniFi et la recréation du conteneur au premier déploiement ; vérifier par relecture

## 4. Documentation (essensys-doc) (#31)

- [ ] 4.1 Rédiger la page « Sonnette UniFi » (prérequis UniFi, activation, choix des lumières, essai, droits, limites : instantanés environ une image par seconde, clignotement lent) et l'entrée de menu ; vérifier par `mkdocs build --strict`
- [ ] 4.2 Ajouter au guide d'installation et de dépannage la configuration UniFi de la CM5, la section `doorbell` du fichier, et les erreurs `doorbell_unavailable` et `names_unavailable` ; vérifier par recherche des anciens libellés

## 5. Mémoire (essensys-memory) (#32)

- [ ] 5.1 Ajouter une synthèse « sonnette UniFi » (événement, vidéo, clignotement et restauration, réglages dans le fichier existant, limites), la relier aux synthèses de noms et de disposition, mettre à jour index et log ; ne pas lancer les scripts de synchronisation (ils ajoutent des adresses du réseau local dans un dépôt public) ; vérifier par relecture

## 6. Qualité et déploiement (essensys-feature-lifecycle) (#59)

- [ ] 6.1 Faire un test de bout en bout avec un faux serveur UniFi, sans armoire réelle (`NO_ARMOIRE=1`) ; consigner le résultat sur #58
- [ ] 6.2 Lancer `/checkup` sur la Feature et poster le rapport ; vérifier par un rapport vert
- [ ] 6.3 Déployer la gateway CM5 et le portail local (SHA épinglés, `--check --diff` d'abord, recréation du conteneur) ; vérifier par `GET /api/doorbell/status` contre l'environnement réel
- [ ] 6.4 Essai réel par Nicolas (vraie sonnette, ses lumières) : vidéo affichée, clignotement, restauration ; consigner le résultat sur #58
