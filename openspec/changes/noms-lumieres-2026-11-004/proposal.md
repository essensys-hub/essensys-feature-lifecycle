> Ticket : [essensys-hub/essensys-feature-lifecycle#41](https://github.com/essensys-hub/essensys-feature-lifecycle/issues/41). Feature ID : `noms-lumieres-2026-11-004`.
> Feature répartie sur plusieurs dépôts. Ce change commun décrit tout le code ; il vit dans `essensys-feature-lifecycle`. Les dépôts d'applications et de portails portent en plus un change du même nom qui renvoie ici.

## Why

Les noms des lumières (« Dressing », « WC 1 », « Petite Chambre 3 »…) sont codés en dur dans les backends et dans les quatre clients. Quand l'usage réel d'une lumière ne correspond plus à son nom (la lumière « Dressing » sert de WC 3), l'administrateur de l'armoire ne peut pas l'adapter.

Une première tentative (ticket #41, change `noms-personnalises-2026-11-002`) visait 77 objets, les pièces et leur propagation en une seule livraison ; elle a été suspendue. Cette Feature est la première tranche : **les lumières seulement**, mais sur **toutes** les briques concernées.

## What Changes

- **33 lumières** renommables (21 principales, 12 indirectes), identifiées par les identifiants déjà communs aux quatre clients (`dressing`, `wc1`, `ann1`…). Un nom par lumière, sans propagation vers sa pièce.
- **Cloud** : stockage par armoire (table `light_names`), lecture pour tout utilisateur de l'armoire, écriture réservée à l'administrateur de l'armoire, arbitrage des conflits (dernier écrit gagne, versionné), point de synchronisation avec la gateway.
- **Gateway (CM5 et Raspberry Pi)** : réplique dans un fichier (le Pi 4 n'a pas PostgreSQL), lecture pour tout utilisateur du réseau local, écriture réservée à `lan_admin`, synchronisation dans les deux sens avec le cloud, fonctionnement hors ligne.
- **Portail cloud, portail local, Android, iPhone** : le nom personnalisé est affiché partout où la lumière apparaît (listes, fiche, écran Temporisations, éditeur de scénarios, confirmations) ; l'administrateur le modifie depuis la fiche de la lumière.
- **Infrastructure** : un répertoire en écriture pour le fichier des noms sur la CM5 (Ansible) et sur le Raspberry Pi 4 (`essensys-raspberry-install`).
- Documentation, mémoire. L'armoire et le firmware ne changent pas : aucun nom n'est écrit dans l'armoire.
- **Livraison** : cloud, puis gateway, puis portails ; APK 2.6.0 sur le site support ; build iPhone 2.6.0 sur TestFlight.

## Capabilities

### New Capabilities

- `light-names-cloud` : stockage, lecture, écriture et synchronisation des noms côté cloud.
- `light-names-gateway` : réplique, lecture, écriture et synchronisation côté gateway.
- `light-names-clients` : affichage partout et modification par l'administrateur sur les quatre surfaces.

### Modified Capabilities

Aucune.

## Impact

- **essensys-user-portal-backend** : migration `019`, handlers, route de synchronisation gateway.
- **essensys-server-backend** (branche V.1.3.0) : magasin de fichier, routes, agent de synchronisation.
- **essensys-user-portal-frontend**, **essensys-server-frontend** : affichage et édition ; tests Playwright en mode `no-armoire`.
- **essensys-android-phone-apps** (2.6.0), **essensys-ios-phone-apps** (2.6.0).
- **essensys-ansible** (CM5), **essensys-raspberry-install** (Pi 4), **essensys-doc**, **essensys-memory**.
- **Déploiement** : cloud (`deploy-portal-stack.yml`), gateway CM5 (playbook ciblé, nouveau montage en écriture : le conteneur doit être **recréé**, pas seulement redémarré), puis portails, APK, TestFlight.
- **Legacy IoT** : aucun endpoint `serverinfos`, `mystatus`, `myactions` ni `done` n'est modifié ; aucune écriture dans la table d'échange.
- **Compatibilité** : les clients actuels ignorent les nouvelles routes et gardent les noms d'origine.
- **Hors périmètre (tickets suivants)** : volets, chauffage, prises, chauffe-eau, arrosage, scénarios, pièces et propagation ; sélecteur d'armoire et lien explicite administrateur–armoire (une armoire par compte pour l'instant).
