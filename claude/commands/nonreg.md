---
description: Dernier état de la non-régression Essensys (rapport nightly + Bugs regression) et lancement local
argument-hint: [<repo>]
---

Cible : $ARGUMENTS

1. Dernier nightly : `gh run list --workflow nonreg.yml --limit 1 --json databaseId,conclusion,createdAt,url` dans les dépôts concernés (ou tous les dépôts actifs) ; télécharger l'artefact `nonreg-report` (`gh run download <id> -n nonreg-report`) et afficher les totaux + tests en échec.
2. Bugs ouverts : `gh search issues --owner essensys-hub --state open --label regression` (+ label `flaky`).
3. Proposer de lancer la suite NR **locale** sur les dépôts modifiés (`git status` dans `ESSENSYS/*`) via les commandes de `/checkup` filtrées sur `NR-*`, puis `nonreg_report.py`.
4. Pour un Bug `regression` déjà résolu (3 nightlies verts), proposer — sans fermer — de le clore après confirmation.

Lecture seule par défaut. Toute création/commentaire d'issue passe par `project_sync.py regression` en dry-run, puis `--apply` après confirmation.
