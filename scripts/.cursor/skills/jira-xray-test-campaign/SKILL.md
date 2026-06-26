---
name: jira-xray-test-campaign
description: Crée et maintient des campagnes de test Jira/Xray sur Atlassian Cloud, incluant découverte du projet, JQL, Test Plan, Test Execution, Test Set et liaisons Xray. Utiliser quand l'utilisateur mentionne Jira, Xray, campagne de test, Test Plan, Test Execution, Test Set, ou veut préparer/exécuter une campagne de tests dans ce projet.
---

# Jira + Xray Test Campaign

Skill pour concevoir puis exécuter des campagnes de test Jira/Xray sur Atlassian Cloud.

## Prerequisite

Avant tout appel Jira ou Confluence, lire le skill `jira-confluence-api`.

Pour les opérations Xray Cloud, utiliser en plus l'auth Xray dediee (`client_id` / `client_secret`), car Xray n'utilise pas les memes endpoints que Jira REST.

## Two modes

1. `design-mode`
   - clarifie le besoin
   - inspecte le projet Jira/Xray
   - propose la structure de campagne, la convention de nommage, les JQL, et les payloads
   - aucune action destructive

2. `execution-mode`
   - cree ou met a jour les Tests, Test Plan, Test Execution et Test Set
   - relie les objets Jira/Xray
   - publie un recapitulatif avec les cles creees / reusees

Toujours commencer en `design-mode`, puis demander confirmation avant creation/mise a jour.

## Model de campagne

Par defaut, modeliser une "campagne de test" Xray comme suit :

- `Test Plan` = conteneur principal de la campagne
- `Test Execution` = execution par environnement / build / cycle
- `Test` = cas de test reusable
- `Test Set` = regroupement optionnel par theme, composant ou lot
- `Precondition` = optionnel, si le projet l'utilise

Si le projet a un type d'issue custom nomme "Campaign" ou equivalent, le verifier d'abord via Jira avant de l'utiliser.

## Questions de cadrage

Si l'utilisateur n'a pas donne ces infos, commencer par les demander :

1. Projet Jira ?
   - ex: `WPMTC`

2. Nom court de la campagne ?
   - ex: `SITC`, `SIT`, `UAT`, `Release 1.4.1`

3. Portee ?
   - Tests deja existants a reutiliser
   - Tests a creer
   - Mix des deux

4. Structure d'execution ?
   - une seule `Test Execution`
   - une par environnement
   - une par sprint / lot / composant

5. Traceabilite voulue ?
   - lier aux Stories
   - lier aux Bugs
   - lier aux Releases / Fix Versions
   - labels / composants / assignee

6. Mode ?
   - `design-only`
   - `create-or-update`

## Workflow

Copier cette checklist et suivre les etapes :

```text
Campaign Progress:
- [ ] Step 1: Discover Jira/Xray project configuration
- [ ] Step 2: Search existing tests and test assets
- [ ] Step 3: Propose campaign structure and naming
- [ ] Step 4: Confirm creation/update scope with user
- [ ] Step 5: Create or update Test Plan / Test Execution / Test Set
- [ ] Step 6: Link tests and validate counts
- [ ] Step 7: Return campaign summary and next actions
```

### Step 1 - Discover project configuration

Verifier avant creation :

- cle projet Jira
- noms exacts des issue types: `Test`, `Test Plan`, `Test Execution`, `Test Set`
- champs obligatoires
- custom fields Xray utilises par le projet
- convention de labels / components / fixVersion

Ne jamais supposer que tous les projets Xray ont exactement les memes types ou champs.

### Step 2 - Search existing assets

Toujours commencer par rechercher l'existant.

JQL de base :

- Tests contenant un mot-cle :
  - `project = WPMTC AND issuetype = Test AND textfields ~ "SITC"`
- Plans existants :
  - `project = WPMTC AND issuetype = "Test Plan" AND summary ~ "SITC"`
- Executions existantes :
  - `project = WPMTC AND issuetype = "Test Execution" AND summary ~ "SITC"`

Si une campagne existe deja, privilegier la mise a jour plutot que la recreation.

### Step 3 - Propose structure

Avant tout changement, fournir un mini plan :

- `Test Plan` propose
- `Test Execution` proposees
- `Test Set` optionnels
- Tests existants a reutiliser
- Tests manquants a creer
- JQL de verification

### Step 4 - Confirm scope

Demander confirmation explicite avant creation/mise a jour avec effet de bord.

Exemple de confirmation :

```text
Ready to create:
- 1 Test Plan
- 2 Test Executions
- 14 links to existing Tests
- 3 new Tests
```

### Step 5 - Create / update

Ordre recommande :

1. creer / mettre a jour les `Test`
2. creer le `Test Plan`
3. creer les `Test Execution`
4. ajouter les Tests au `Test Plan`
5. ajouter les `Test Execution` au `Test Plan`
6. ajouter les Tests aux `Test Execution` si necessaire

Pour Xray Cloud, privilegier GraphQL quand il faut manipuler les relations Xray.

### Step 6 - Validate

Toujours verifier apres action :

- nombre de Tests dans le `Test Plan`
- nombre de `Test Execution` rattachees
- presence des labels / fixVersion / components attendus
- liens Jira/Xray resolves

### Step 7 - Return summary

Toujours finir avec :

- issues creees
- issues reutilisees
- liens effectues
- JQL de verification
- points restants manuels

## Auth and endpoints

### Jira Cloud

Utiliser le skill `jira-confluence-api` pour :

- `cloudId`
- auth `Basic` ou `Bearer`
- URLs `https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/...`

### Xray Cloud

Utiliser des variables dediees, par exemple :

```dotenv
XRAY_CLIENT_ID=...
XRAY_CLIENT_SECRET=...
XRAY_BASE_URL=https://eu.xray.cloud.getxray.app
```

Authentification :

- `POST {XRAY_BASE_URL}/api/v2/authenticate`
- body JSON avec `client_id` et `client_secret`
- reponse = token bearer Xray

GraphQL :

- `POST {XRAY_BASE_URL}/api/v2/graphql`
- header `Authorization: Bearer <xray-token>`

## Important safety rules

- Ne jamais creer d'issues Jira/Xray sans confirmation utilisateur
- Ne jamais supposer les noms des issue types ou des champs custom
- Ne jamais ecraser un Test Plan existant sans lister ce qui va changer
- Ne jamais logger les secrets Jira, Xray, `.env`, headers `Authorization`
- Toujours preferer une strategie `search -> preview -> confirm -> mutate -> verify`

## Output template

Utiliser ce format dans la reponse finale :

```markdown
## Campaign Summary

**Project:** WPMTC
**Campaign key:** SITC

### Created
- Test Plan: WPMTC-123
- Test Execution: WPMTC-124

### Reused
- Tests: WPMTC-5774, WPMTC-5778

### JQL checks
- `project = WPMTC AND issuetype = "Test Plan" AND issue = WPMTC-123`
- `project = WPMTC AND issuetype = Test AND textfields ~ "SITC"`

### Remaining actions
- Confirm assignee on WPMTC-124
- Add missing precondition for login test
```

## Additional resources

- Pour les details API et scopes: voir [reference.md](reference.md)
- Pour des exemples de campagne SITC / WPMTC: voir [examples.md](examples.md)
