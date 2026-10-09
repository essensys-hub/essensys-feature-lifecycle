---
description: État d'une feature Essensys (ou de toutes les features actives) depuis le GitHub Project #6
argument-hint: [<Feature ID>]
---

Feature : $ARGUMENTS

- Avec un Feature ID : `python3 essensys-feature-lifecycle/scripts/feature_lifecycle/project_sync.py status <id>` puis, pour l'issue liée : sub-issues (`gh issue view --json subIssues` ou GraphQL `subIssues`), PR liées (`gh pr list --search "Feature: <id>" --state all` sur les dépôts concernés), checks (`gh pr checks`), dernier commentaire `<!-- checkup -->` et dernier rapport NR.
- Sans argument : `gh project item-list 6 --owner essensys-hub --format json --limit 200`, ne garder que les items dont `Status` ∉ {Archivé, Done}, grouper par `Status`, puis `Phase`.

Afficher un tableau compact (statut, sub-issues ouvertes/total, PR ouvertes, gates, dernier checkup) et signaler les anomalies : item sans `Feature ID`, statut incohérent (PR mergées mais `En cours`), gate rouge, NR en échec. Lecture seule : ne rien modifier.
