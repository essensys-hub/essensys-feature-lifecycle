# Gouvernance Essensys pour Claude Code

> Source : `essensys-feature-lifecycle/claude/GOVERNANCE.md`, importé par `ESSENSYS/CLAUDE.md` via `scripts/install-claude.sh`.
> Change de référence : `openspec/changes/github-project-lifecycle-2026-10-001`.

Le projet Essensys est piloté **uniquement** dans le GitHub Project **#6** de l'org `essensys-hub` (« Essensys Roadmap »). GitHub centralise les tickets, le code, les PR, les tests et les gates. Jira, Xray et Confluence sont legacy : ne plus les utiliser. Point de départ de la production : **2026-10-09**. Les tickets antérieurs sont clos et ne sont pas repris.

## Règle n°1 : pas de modification sans ticket

Avant de modifier un dépôt Essensys (code, infra, doc produit) :

1. Identifier l'issue du Project #6 concernée, avec `gh issue view`, `/feature-status` ou une recherche.
2. S'il n'y en a pas, **proposer `/ticket`** et attendre la création avant de modifier quoi que ce soit.
3. Les commits référencent l'issue (`feat(android): ... (#12)`). Les PR contiennent `Feature: <id>` et `Closes #<n>` ou `Refs #<n>`.

Exceptions sans ticket : la lecture et l'exploration, les fichiers de mémoire de l'agent, les brouillons dans le scratchpad.

## Du ticket à l'OpenSpec

- **Évolution, ou bug qui change un comportement spécifié** : passer par `/ticket-to-spec <issue>`. Cette commande crée le change OpenSpec, le manifest `features/<id>.json` (bloc `github`), le `Feature ID` dans le Project et les sub-issues.
- **Correctif trivial** (une PR, aucun comportement spécifié ne change) : pas d'OpenSpec. La décision est tracée en commentaire de l'issue.
- Le `Feature ID` suit le format `<slug>-AAAA-MM-NNN`. Il nomme à la fois le change OpenSpec et le manifest.

## Cycle et statuts

`Idée → Spec → Prêt → En cours → Test → Gate sécu → Déployé → Archivé`

- Les transitions sont **automatiques** : CI et skills OpenSpec, via `scripts/feature_lifecycle/project_sync.py`. Ne pas forcer un statut à la main pour « faire avancer ». Seul un humain fait reculer un statut.
- `opsx:apply` ferme les sub-issues des tâches cochées, avec un commentaire qui cite le commit.
- `opsx:archive` fait passer la feature à `Archivé`.

## Vérifier avant de livrer : `/checkup`

Aucune PR n'est prête sans un `/checkup` vert sur le dépôt ou la feature :

- build et lint ;
- tests unitaires et tests de non-régression (`NR-*`) ;
- tests applicatifs :
  - web : Playwright avec la matrice desktop, iPhone et iPad, en mode `no-armoire` ;
  - Android : émulateur ;
  - iOS : simulateur ;
- gates : `feature-gate` et `security-gate`.

Le rapport est posté sur l'issue Feature. Ne jamais piloter une armoire réelle pendant les tests.

## Non-régression

- Tout correctif d'un `Bug` ajoute un test `NR-<repo>-<n>` qui référence le Bug (`#<n>`).
- Un échec `NR-*` en nightly ouvre un `Bug` (label `regression`), ou le commente s'il existe déjà. Voir `docs/feature-lifecycle/non-regression.md`.

## Garde-fous d'écriture GitHub

- Ne jamais supprimer d'issue, d'item, de Project ni de champ. Fermer avec une raison à la place.
- Demander confirmation avant de créer ou de fermer une issue, et avant de commenter publiquement, en session interactive.
- Ne jamais modifier les champs ou les vues du Project #6. C'est le rôle de `bootstrap_project.py`, exécuté par un humain.
- Scripts : dry-run par défaut. `--apply` seulement après accord explicite.

## Commandes

| Commande | Rôle |
|---|---|
| `/ticket <description>` | Créer un ticket (Bug, Task, Feature ou Support) après recherche de doublons |
| `/ticket-to-spec <issue>` | Transformer un ticket en change OpenSpec, manifest et sub-issues |
| `/checkup [<Feature ID>\|<repo>]` | Vérifier build, tests, NR, app et gates, puis poster le rapport |
| `/feature-status [<Feature ID>]` | Afficher l'état d'une feature ou des features actives |
| `/nonreg` | Afficher le dernier rapport de non-régression et les Bugs `regression` |

Setup : `essensys-feature-lifecycle/scripts/feature_lifecycle/check_claude_setup.sh`.
