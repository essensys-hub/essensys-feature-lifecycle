> Ticket : [essensys-hub/essensys-feature-lifecycle#45](https://github.com/essensys-hub/essensys-feature-lifecycle/issues/45). Feature ID : `lumieres-temporisees-2026-11-003`.
> Feature répartie sur plusieurs dépôts. Ce change commun décrit tout le code ; il vit dans `essensys-memory` parce qu'il couvre des dépôts sans dossier `openspec`. Les dépôts d'applications et de portails portent en plus un change du même nom qui renvoie ici.

## Why

L'armoire éteint déjà automatiquement certaines lumières après un délai (le BP stocke la durée dans la table d'échange, le boîtier la garde en EEPROM). Seul l'écran tactile de l'armoire permet de la régler (15 min, 30 min, 1 h, Jamais). Aucun portail et aucune app ne le permet : il faut être devant l'armoire.

## What Changes

- Six lumières ont un délai réglable : Dressing (clé 521), WC 1 (555), WC 2 (556), Service/buanderie (557), Annexe 1 (561), Annexe 2 (562). La valeur est un octet : 1 à 255 minutes, 0 = jamais.
- **Cloud** et **gateway** exposent une lecture et une écriture dédiées, validées (clé et plage), réservées à l'administrateur de l'armoire, auditées. Les six clés sont remontées dans le cache pour que la valeur courante soit connue (profil de synchro côté cloud, rotation de lecture côté gateway).
- **Portail cloud, portail local, app Android, app iPhone** : un menu « Temporisations » qui liste les six lumières, **et** le même réglage dans la fiche de chaque lumière. Raccourcis 15 min, 30 min, 1 h, Jamais, plus une valeur libre de 1 à 255 minutes. Masqué aux non-administrateurs.
- L'écran de l'armoire et le firmware ne changent pas. Une valeur libre (par exemple 7 min) n'est pas affichée par l'écran de l'armoire : à vérifier au banc qu'il ne l'écrase pas.
- Documentation (`debug.md` corrigé : clés 521, 561, 562), guide utilisateur, site support (page `/android`, APK 2.5.0), mémoire.
- **Livraison** : APK publié sur le site support, build iPhone envoyé sur TestFlight.

## Capabilities

### New Capabilities

- `light-timers-cloud` : lecture et écriture des temporisations via le cloud.
- `light-timers-gateway` : lecture et écriture des temporisations via la gateway (CM5 et Raspberry Pi).
- `light-timers-clients` : menu central et réglage par lumière sur les quatre surfaces.

### Modified Capabilities

Aucune (les specs existantes ne sont pas archivées sous `openspec/specs/`).

## Impact

- **essensys-user-portal-backend** (cloud) : nouveau handler, route sous `/portal/admin`, migration `018` (profil de synchro).
- **essensys-server-backend** (gateway, branche V.1.3.0) : nouveau handler, route `adminOnly`, rotation de lecture et snapshot, filtre de push cloud.
- **essensys-user-portal-frontend**, **essensys-server-frontend** : menu, page et fiche lumière ; tests Playwright en mode `no-armoire`.
- **essensys-android-phone-apps** (2.5.0), **essensys-ios-phone-apps** : écran, fiche lumière, notion d'administrateur (neuve), tests.
- **essensys-support-site**, **essensys-doc**, **essensys-raspberry-install** (doc), **essensys-memory**.
- **Déploiement** : cloud par `deploy-portal-stack.yml`, gateway par `install.gateway.yml` (**avant** les apps), puis APK sur le site support et TestFlight.
- **Legacy IoT** : aucun endpoint `serverinfos`, `mystatus`, `myactions` ni `done` n'est modifié. Les écritures utilisent les actions existantes de la table d'échange.
- **Compatibilité** : les apps actuelles ne connaissent pas les nouvelles routes ; leur comportement ne change pas.
