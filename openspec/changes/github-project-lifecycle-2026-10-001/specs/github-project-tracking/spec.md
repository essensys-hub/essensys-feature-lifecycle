## Purpose

Fournit le point de pilotage unique du cycle de vie des features Essensys : un GitHub Project v2 au niveau de l'org `essensys-hub`, couvrant tous les dépôts, avec une hiérarchie Feature → sub-issues et un statut normalisé.

## ADDED Requirements

### Requirement: Project org unique
L'org `essensys-hub` SHALL disposer d'un unique GitHub Project v2 « Essensys Roadmap » qui agrège les issues de tous les dépôts Essensys actifs. Aucun autre outil de backlog ne SHALL être utilisé pour planifier une feature.

#### Scenario: Issue d'un dépôt cible visible dans le Project
- **WHEN** une issue `Task` est créée dans `essensys-server-backend` en sub-issue d'une `Feature`
- **THEN** elle apparaît dans le Project « Essensys Roadmap » avec le même `Feature ID` que sa Feature parente

### Requirement: Champs normalisés
Le Project SHALL exposer les champs : `Status` (single select : Idée, Spec, Prêt, En cours, Test, Gate sécu, Déployé, Archivé), `Feature ID` (texte, format `<slug>-AAAA-MM-NNN`), `Phase` (single select : 0 doc/install, 1, 2, 3), `Cible` (single select : gateway, cloud, firmware, mobile, infra, doc), `Appareil` (texte, ex. `SC944D`, `raspberry`).

#### Scenario: Item sans Feature ID
- **WHEN** un item de type `Feature` ou `Task` a un `Feature ID` vide depuis plus de 24 h
- **THEN** la vue « À trier » du Project le liste pour correction

### Requirement: Types d'issue org
L'org SHALL définir les types d'issue `Feature`, `Task`, `Bug` et `Support`. Une `Feature` SHALL vivre dans `essensys-feature-lifecycle` ; ses `Task` et `Bug` SHALL vivre dans les dépôts où le code change et SHALL être rattachés en sub-issues.

#### Scenario: Feature touchant les jumeaux backend
- **WHEN** une Feature impacte `essensys-server-backend` et `essensys-user-portal-backend`
- **THEN** elle possède au moins une sub-issue `Task` dans chacun des deux dépôts

### Requirement: Vues standard
Le Project SHALL fournir au minimum les vues : tableau par `Status`, roadmap par `Phase`, « Support à trier », « Gate sécu en échec ».

#### Scenario: Consultation de la roadmap
- **WHEN** un contributeur ouvre la vue roadmap
- **THEN** il voit les Features groupées par `Phase` avec leur `Status` courant
