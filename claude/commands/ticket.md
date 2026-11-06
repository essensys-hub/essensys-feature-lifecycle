---
description: Créer un ticket Essensys (Bug/Task/Feature/Support) dans le GitHub Project #6 après recherche de doublons
argument-hint: <description libre du besoin ou du problème>
---

Crée un ticket dans le GitHub Project **#6** de `essensys-hub` en suivant `essensys-feature-lifecycle/claude/GOVERNANCE.md`.

Demande : $ARGUMENTS

1. **Comprendre** : si la demande est vague, pose au plus 2 questions (symptôme, version/appareil, local gateway ou cloud).
2. **Doublons** : `gh search issues --owner essensys-hub --state open "<mots-clés>"` + `python3 essensys-feature-lifecycle/scripts/feature_lifecycle/project_sync.py status <feature-id>` si une feature est évoquée. Montre les candidats.
3. **Proposer** (sans rien créer) un tableau :
   - Type : `Bug` (régression/défaut), `Task` (travail technique), `Feature` (évolution), `Support` (question utilisateur)
   - Dépôt cible (`Feature` → `essensys-feature-lifecycle` ; sinon le dépôt où le code change ; jumeaux → une Task par jumeau)
   - Titre (impératif, ≤ 80 car.), corps (contexte, critères d'acceptation vérifiables, appareil/version), champs Project : `Phase`, `Cible` (gateway/cloud/firmware/mobile/infra/doc), `Appareil`
   - **Matrice des briques** (obligatoire pour une `Feature`, jamais de « je verrai plus tard ») : une ligne par brique, `concernée` ou `non concernée + raison`, à faire valider par l'utilisateur. Briques : `cloud` (user-portal-backend), `portail-cloud` (user-portal-frontend), `gateway-cm5` (server-backend + server-frontend), `raspberry-pi` (raspberry-install), `ansible`, `android`, `iphone`, `site-support`, `documentation`, `memoire`, `firmware`. Pour décider, chercher dans la doc et le code si le sujet existe déjà dans la brique. Une brique non tranchée bloque la création.
   - Besoin d'OpenSpec ? (oui si évolution ou changement de comportement spécifié → enchaîner `/ticket-to-spec`)
4. **Après confirmation explicite** seulement :
   - `gh issue create --repo essensys-hub/<repo> --title ... --body-file ...` puis type d'issue via GraphQL `updateIssueIssueType` si besoin
   - Écrire la matrice dans le corps du ticket (section `## Briques`, un tableau brique / concernée / raison).
   - `gh project item-add 6 --owner essensys-hub --url <issue-url>` et renseigner les champs (`gh project item-edit`)
5. Affiche l'URL et propose l'étape suivante (`/ticket-to-spec`, ou correctif trivial direct).

Ne jamais coller de secrets, mots de passe, IP publiques ou adresses d'utilisateurs dans un ticket.
