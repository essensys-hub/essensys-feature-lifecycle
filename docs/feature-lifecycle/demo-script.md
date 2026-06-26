# Demo script — 10 minutes

Démo du cycle de vie feature Essensys.

## Déroulé

1. Montrer `docs/feature-lifecycle/README.md` et le schéma du process.
2. Partir d'un item du backlog **Jira SCRUM** : <https://essensys-hub.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog>
3. Générer la spec :

```text
openspec propose <feature>
```

4. Montrer le change OpenSpec généré et le manifest `features/<id>.json`.
5. Découper en tasks Jira :

```text
create jira tasks for this change
```

6. Montrer la boucle qualité :

```text
generate e2e tests for this feature
triage security findings
sync user guide for this feature
```

7. Ouvrir les workflows :

- `.github/workflows/feature-gate.yml`
- `.github/workflows/security-gate.yml`

8. Mettre à jour la mémoire :

```text
update essensys-memory
```

## Critères de succès

- l'équipe comprend que Git reste la source de vérité et le manifest le pivot
- la gate sécurité est comprise comme bloquante dès le départ
- la chaîne Jira → OpenSpec → tasks Jira est claire
- doc, revue et mémoire sont perçues comme **continues**
- l'équipe peut répéter le workflow sans guidage verbal supplémentaire
