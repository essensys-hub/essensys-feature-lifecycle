> Ticket : [essensys-hub/essensys-feature-lifecycle#55](https://github.com/essensys-hub/essensys-feature-lifecycle/issues/55). Feature ID : `affichage-objets-2026-11-006`.
> Feature répartie sur plusieurs dépôts. Ce change commun décrit tout le code ; il vit dans `essensys-feature-lifecycle`. Les dépôts d'applications et de portails portent en plus un change du même nom qui renvoie ici.
> Cousine de `noms-lumieres-2026-11-004` (#41) et `noms-volets-2026-11-005` (#52), toutes deux livrées : mêmes droits, mêmes erreurs, même fusion, même fichier côté gateway.

## Why

Toutes les installations n'ont pas les mêmes équipements. Le catalogue compte 33 lumières et 16 volets et stores ; certains n'existent pas ou ne sont pas utilisables chez un client, mais ils apparaissent quand même dans les listes, dans « Tout allumer / éteindre » et « Tout ouvrir / fermer », dans l'écran Temporisations et dans l'écran « Temps de course ». L'ordre d'affichage est aussi imposé par le catalogue. Après les noms personnalisés, l'administrateur de l'armoire doit pouvoir adapter la liste à sa maison.

## What Changes

- **Un document de disposition par armoire et par genre** (`lights`, `shutters`) : `{"order":[ids…],"disabled":[ids…],"version":n,"updated_at":"…","updated_by":"…"}`. Pas de champ par objet : un réordonnancement est une seule écriture, une seule version, et ne touche pas aux noms (#41 et #52 gardent leurs propres entrées).
- **Cloud** : table `object_layout` (migration `021_object_layout.sql`), routes jumelles `GET /api/portal/{lights|shutters}/layout` et `PUT /api/portal/admin/{lights|shutters}/layout`, point de synchronisation `POST /api/gateway/{lights|shutters}/layout/sync`. Les tables de noms ne sont pas touchées.
- **Gateway CM5** : deux sections de plus, `lights_layout` et `shutters_layout`, dans le **même fichier JSON** et sous la **même clé** `light_names.path` ; routes locales `GET /api/{lights|shutters}/layout` et `PUT /api/admin/{lights|shutters}/layout` ; synchronisation dans les deux sens avec le cloud.
- **Portail cloud, portail local, Android, iPhone** : un objet désactivé est masqué pour tous (listes, groupes, Temporisations, « Temps de course ») et aucune commande n'est envoyée pour lui ; l'ordre choisi s'applique dans chaque groupe. L'administrateur de l'armoire dispose d'un écran de gestion (interrupteur Activé/Désactivé, Monter/Descendre, « Ordre d'origine »).
- **Infrastructure** : aucune nouvelle clé de configuration, aucun nouveau chemin. Raspberry Pi et Ansible ne sont **pas** concernés (voir design).
- Documentation, mémoire, site support (page `/android`). L'armoire et le firmware ne changent pas : aucune disposition n'est écrite dans l'armoire.
- **Livraison** : cloud, puis gateway, puis portails ; APK 2.8.0 sur le site support ; build iPhone 2.8.0 sur TestFlight (la 2.7.0 est la dernière publiée).

## Capabilities

### New Capabilities

- `object-layout-cloud` : stockage, lecture, écriture et synchronisation des dispositions côté cloud.
- `object-layout-gateway` : sections du fichier, lecture, écriture et synchronisation côté gateway.
- `object-layout-clients` : filtrage et ordre appliqués partout, écran de gestion de l'administrateur, sur les quatre surfaces.

### Modified Capabilities

Aucune dans les specs publiées. Les noms (`light-names-*`, `shutter-names-*`) et les temporisations (#45) ne changent pas.

## Impact

- **essensys-user-portal-backend** : migration `021`, handlers, deux routes de synchronisation gateway.
- **essensys-server-backend** (branche V.1.3.0) : magasin de fichier (deux sections), routes, agent de synchronisation.
- **essensys-user-portal-frontend**, **essensys-server-frontend** : filtre, ordre, écran de gestion ; Playwright en mode `no-armoire`.
- **essensys-android-phone-apps** (2.8.0), **essensys-ios-phone-apps** (2.8.0), **essensys-support-site**.
- **essensys-doc**, **essensys-memory**.
- **Non concernés** : essensys-ansible, essensys-raspberry-install (même fichier, même clé, même répertoire que #41/#52), firmware.
- **Déploiement** : cloud (`deploy-portal-stack.yml`, la migration `021` se rejoue au démarrage), puis gateway CM5 (playbook ciblé, redémarrage du conteneur suffisant), puis portails, APK, TestFlight.
- **Legacy IoT** : aucun endpoint `serverinfos`, `mystatus`, `myactions` ni `done` n'est modifié ; aucune écriture dans la table d'échange.
- **Compatibilité** : une gateway ou une app qui ne connaît pas la disposition affiche tout le catalogue dans l'ordre d'origine. Une gateway restée à la version de #41 (avant le magasin à sections brutes) effacerait les sections de disposition à sa prochaine écriture (voir risques du design).
- **Hors périmètre** : scénarios et éditeur de scénarios (ils gardent le catalogue complet), chauffage, prises de sécurité, chauffe-eau, arrosage, pièces, sélecteur d'armoire (une armoire par compte), ordre des groupes eux-mêmes (principales, indirectes, volets, spéciaux), masquage par utilisateur.
