---
description: Transformer un ticket du Project #6 en change OpenSpec + manifest + sub-issues
argument-hint: <owner/repo#n | URL issue>
---

Ticket : $ARGUMENTS

Suis `essensys-feature-lifecycle/claude/GOVERNANCE.md`.

0. **Gate de tri** (Règle n°2) : `python3 essensys-feature-lifecycle/scripts/feature_lifecycle/triage_gate.py <ref>`. Si le code n'est pas 0, **s'arrêter** : afficher la raison et l'action attendue d'un mainteneur. Aucune écriture, aucun change, aucun commentaire.
1. **Lire** le ticket : `gh issue view <ref> --json title,body,labels,issueType,comments,url` et l'item Project (`project_sync.py status` si `Feature ID` déjà présent).
2. **Décider** OpenSpec ou correctif trivial :
   - Trivial (une PR, aucun comportement spécifié ne change) → poster en commentaire « Correctif trivial, pas d'OpenSpec : <raison> » (après confirmation) et s'arrêter.
   - Sinon continuer.
3. **Feature ID** : `<slug>-AAAA-MM-NNN` (NNN = prochain numéro du mois, chercher les changes et manifests existants dans les dépôts ESSENSYS). Le confirmer avec l'utilisateur.
3 bis. **Matrice des briques** : reprendre la section `## Briques` du ticket. Si elle manque ou si une des 11 briques (`cloud`, `portail-cloud`, `gateway-cm5`, `raspberry-pi`, `ansible`, `android`, `iphone`, `site-support`, `documentation`, `memoire`, `firmware`) n'est pas tranchée, **s'arrêter** et la faire compléter par l'utilisateur. Une brique « non concernée » exige une raison. Ne jamais déduire seul qu'une brique est hors périmètre.
4. **OpenSpec** dans le dépôt concerné (là où le code change) : invoquer le skill `openspec-propose` avec le Feature ID comme nom de change et le ticket comme description (lien vers l'issue dans proposal.md). Intégrer les exigences de test : tests unitaires, non-régression `NR-*`, tests applicatifs (Playwright/émulateur/simulateur).
5. **Manifest** `features/<Feature ID>.json` (skill `feature-manifest-orchestrator`) avec bloc `bricks` (les 11 briques : `scope` concerned/not-concerned, `reason`, `issue`, `delivered`) et bloc `github: { issue: "essensys-hub/<repo>#<n>", project_item: <id> }` ; valider avec `validate_feature_manifests.py` et `check_feature_gate.py --strict`.
6. **Project** (après confirmation) : type d'issue `Feature` si besoin, champ `Feature ID`, puis `python3 essensys-feature-lifecycle/scripts/feature_lifecycle/project_sync.py advance <Feature ID> spec-created --apply`.
7. **Sub-issues** (après confirmation) : une `Task` **par brique concernée** (jamais une brique concernée sans sub-issue : l'indiquer dans `bricks.<brique>.issue`), et `tasks.md` a au moins un groupe `## N.` par brique concernée ; sinon s'arrêter. Une `Task` par groupe `## N.` de `tasks.md`, dans le dépôt cible, rattachée en sub-issue (`gh api graphql` mutation `addSubIssue`), ajoutée au Project avec le même `Feature ID`. Écrire le numéro de sub-issue en fin de titre de groupe dans `tasks.md` (`## 2. Écran volets (#14)`).
8. Passer à `Prêt` (`advance <id> ready --apply`) et résumer : tableau des briques (concernée / raison / sub-issue), change, manifest, sub-issues, prochaine commande `/opsx:apply`.
