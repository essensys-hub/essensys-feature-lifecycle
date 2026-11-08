> Ticket : [essensys-hub/essensys-feature-lifecycle#58](https://github.com/essensys-hub/essensys-feature-lifecycle/issues/58). Feature ID : `sonnette-unifi-2026-11-007`.
> Feature répartie sur la gateway CM5 (backend et portail local) et Ansible. Ce change commun décrit tout le code ; il vit dans `essensys-feature-lifecycle`.

## Why

L'installation dispose d'une sonnette connectée UniFi Protect avec caméra. Un visiteur qui sonne n'est signalé ni dans l'interface Essensys ni par les lumières de la maison. La CM5 sait déjà parler à UniFi Protect (clé d'API, liste des caméras, instantané, `internal/unifi`) mais ne réagit à aucun événement. Le besoin : que la CM5 réagisse à la sonnette, sans passer par le cloud.

## What Changes

- **Gateway (backend)** : un écouteur d'événements UniFi Protect détecte la pression de la sonnette ; un service « sonnette » mémorise l'événement (sonnerie en cours), fait clignoter les lumières choisies (elles finissent allumées) et protège contre les rafales. Réglages enregistrés dans une section `doorbell` du **même fichier** que les noms (`light_names.path`, aucune nouvelle clé de chemin). Routes locales : état et vidéo (utilisateur authentifié), réglages et essai (administrateur `lan_admin`).
- **Portail local (frontend)** : une fenêtre « Sonnette » s'affiche avec la vidéo quand la sonnette est pressée ; un écran de réglage pour l'administrateur (activer, lumières, nombre de clignotements, essai).
- **Ansible** : accès UniFi (clé d'API chiffrée) et paramètres de la sonnette déployés sur la CM5.
- **Documentation et mémoire** : installation, usage, dépannage ; synthèse.
- **Hors cloud** : aucune route cloud, aucun portail cloud, aucune app mobile.
- **Livraison** : gateway CM5, portail local, Ansible. Pas de nouvelle version d'APK ni de build iPhone.

## Capabilities

### New Capabilities

- `doorbell-gateway` : écoute UniFi, clignotement des lumières, réglages, vidéo, état, essai.
- `doorbell-portal` : fenêtre de sonnette avec vidéo et écran de réglage du portail local.

### Modified Capabilities

Aucune dans les specs publiées. Les commandes de lumières existantes, les noms (#41), la disposition (#55) et les temporisations (#45) ne changent pas.

## Impact

- **essensys-server-backend** (branche V.1.3.0) : service sonnette, extension de `internal/unifi`, routes, section `doorbell` du fichier des noms.
- **essensys-server-frontend** (branche V.1.3.0) : fenêtre de sonnette, écran de réglage, Playwright en mode `no-armoire`.
- **essensys-ansible** : variables `unifi_*` (déjà présentes, désactivées par défaut) et paramètres de la sonnette ; secrets chiffrés (SOPS).
- **essensys-doc**, **essensys-memory**.
- **Non concernés** : cloud, portail cloud, Raspberry Pi, Android, iPhone, site support, firmware.
- **Legacy IoT** : aucun endpoint `serverinfos`, `mystatus`, `myactions` ni `done` n'est modifié. Le clignotement écrit dans la table d'échange par le chemin déjà utilisé pour les commandes de lumières ; aucun test n'écrit dans une armoire réelle.
- **Compatibilité** : UniFi désactivé (état par défaut) : aucun changement de comportement.
- **Hors périmètre** : Android et iPhone, cloud, notifications push, enregistrement ou historique des vidéos, autres événements UniFi (mouvement, alarme), Raspberry Pi 4, ouverture de porte ou de portail.
