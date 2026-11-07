> Ticket : [essensys-hub/essensys-feature-lifecycle#52](https://github.com/essensys-hub/essensys-feature-lifecycle/issues/52). Feature ID : `noms-volets-2026-11-005`.
> Feature répartie sur plusieurs dépôts. Ce change commun décrit tout le code ; il vit dans `essensys-feature-lifecycle`. Les dépôts d'applications et de portails portent en plus un change du même nom qui renvoie ici.
> Jumelle de `noms-lumieres-2026-11-004` (#41, livrée) : même mécanique, routes et stockage jumeaux.

## Why

Les noms des volets et stores (« Volet 1 Salon », « Volet Petite Chambre 3 », « Store (banne) »…) sont codés en dur dans les deux portails, l'app Android et l'app iPhone. Quand l'usage réel d'un volet ne correspond plus à son nom, l'administrateur de l'armoire ne peut pas l'adapter, alors qu'il le peut déjà pour les lumières.

## What Changes

- **16 volets et stores** renommables, identifiés par les identifiants déjà communs aux quatre clients (`volet1salon`… `store`). Un nom par objet, sans propagation vers la pièce.
- **Cloud** : stockage par armoire (nouvelle table `shutter_names`, migration `020`), lecture pour tout utilisateur de l'armoire, écriture réservée à l'administrateur de l'armoire, arbitrage des conflits (dernier écrit gagne, versionné), point de synchronisation avec la gateway. Routes jumelles `/shutters/names`, la table `light_names` n'est pas touchée.
- **Gateway CM5** : seconde section `shutters` dans le **même fichier JSON** et sous la **même clé** `light_names.path` que les lumières ; lecture pour tout utilisateur du réseau local, écriture réservée à `lan_admin`, synchronisation dans les deux sens avec le cloud, fonctionnement hors ligne. Les noms des lumières restent intacts.
- **Portail cloud, portail local, Android, iPhone** : le nom personnalisé est affiché partout où le volet apparaît (écran Volets, fiche, écran « Temps de course » (#18), confirmations et messages de dernière action) ; l'administrateur le modifie depuis la fiche du volet.
- **Infrastructure** : aucune. Le répertoire et le montage en écriture du fichier existent déjà (#41). Raspberry Pi et Ansible ne sont **pas** concernés tant que le chemin reste `light_names.path` (voir design).
- Documentation, mémoire. L'armoire et le firmware ne changent pas : aucun nom n'est écrit dans l'armoire.
- **Livraison** : cloud, puis gateway, puis portails ; APK 2.7.0 sur le site support ; build iPhone 2.7.0 sur TestFlight (la 2.6.0 est la dernière publiée).

## Capabilities

### New Capabilities

- `shutter-names-cloud` : stockage, lecture, écriture et synchronisation des noms côté cloud.
- `shutter-names-gateway` : section du fichier, lecture, écriture et synchronisation côté gateway.
- `shutter-names-clients` : affichage partout et modification par l'administrateur sur les quatre surfaces.

### Modified Capabilities

Aucune dans les specs publiées. Le comportement des noms de lumières (`light-names-*`) ne change pas ; seul le code du fichier gateway est refactoré pour préserver la section voisine.

## Impact

- **essensys-user-portal-backend** : migration `020`, handlers, route de synchronisation gateway.
- **essensys-server-backend** (branche V.1.3.0) : magasin de fichier (section `shutters`), routes, agent de synchronisation.
- **essensys-user-portal-frontend**, **essensys-server-frontend** : affichage et édition ; tests Playwright en mode `no-armoire`.
- **essensys-android-phone-apps** (2.7.0), **essensys-ios-phone-apps** (2.7.0), **essensys-support-site**.
- **essensys-doc**, **essensys-memory**.
- **Non concernés** : essensys-ansible, essensys-raspberry-install (même fichier, même clé, même répertoire que #41), firmware.
- **Déploiement** : cloud (`deploy-portal-stack.yml`, la migration `020` se rejoue au démarrage), gateway CM5 (playbook ciblé, redémarrage du conteneur suffisant : aucun nouveau montage), puis portails, APK, TestFlight.
- **Legacy IoT** : aucun endpoint `serverinfos`, `mystatus`, `myactions` ni `done` n'est modifié ; aucune écriture dans la table d'échange.
- **Compatibilité** : les clients actuels ignorent les nouvelles routes et gardent les noms d'origine ; une gateway ancienne qui réécrit le fichier ne connaît pas la section `shutters` (voir risques du design).
- **Hors périmètre** : chauffage, prises de sécurité, chauffe-eau, arrosage, scénarios, pièces et propagation ; sélecteur d'armoire (une armoire par compte).
