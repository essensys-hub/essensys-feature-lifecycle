## Purpose

Montrer la vidéo de la sonnette dans le portail local de la CM5 quand elle sonne, et permettre à l'administrateur de régler la fonction.

## ADDED Requirements

### Requirement: Fenêtre de sonnette
Le portail local SHALL interroger `GET /api/doorbell/status` et, quand `ringing=true`, afficher une fenêtre « Quelqu'un sonne » avec la vidéo issue de `GET /api/doorbell/stream`, quelle que soit la page ouverte. La fenêtre MUST pouvoir être fermée ; elle ne se rouvre pas pour la même sonnerie. Fonction désactivée ou `available=false` : aucune fenêtre.

#### Scenario: Sonnerie
- **GIVEN** un faux état `ringing=true`
- **WHEN** le portail interroge l'état
- **THEN** la fenêtre s'affiche avec la vidéo

#### Scenario: Fermeture
- **WHEN** l'utilisateur ferme la fenêtre
- **THEN** elle ne se rouvre pas pour la même sonnerie, et se rouvre pour la suivante

#### Scenario: Fonction désactivée
- **GIVEN** `enabled=false` ou `available=false`
- **THEN** aucune fenêtre et aucune requête vidéo

### Requirement: Écran de réglage
Le portail local SHALL proposer à `lan_admin` (ou à tous si l'IAM LAN est désactivé) un écran « Sonnette » : activer ou désactiver, choisir la caméra, choisir les lumières parmi le catalogue (noms personnalisés #41 affichés, lumières masquées #55 non proposées), nombre de clignotements, bouton « Essayer ». Les erreurs de la gateway sont affichées en français. Un utilisateur non administrateur ne voit pas l'écran.

#### Scenario: Réglage
- **WHEN** l'administrateur choisit deux lumières, 3 clignotements et enregistre
- **THEN** la requête `PUT` correspondante part et les valeurs sont relues à l'ouverture

#### Scenario: Non-administrateur
- **WHEN** un `lan_user` ouvre le portail
- **THEN** il ne voit pas l'écran de réglage

#### Scenario: Essai
- **WHEN** l'administrateur touche « Essayer »
- **THEN** la fenêtre de sonnerie s'affiche (essai à sec en mode `no-armoire`)

### Requirement: Mode no-armoire
Les tests applicatifs MUST s'exécuter en mode `no-armoire` : aucune requête vers l'armoire ni vers une console UniFi réelle.

#### Scenario: Matrice d'appareils
- **WHEN** les tests Playwright s'exécutent sur desktop, iPhone et iPad
- **THEN** ils passent sans aucune requête vers l'armoire (`@nr NR-server-frontend-*`)
