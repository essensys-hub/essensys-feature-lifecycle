# Agent Context — essensys-feature-lifecycle

> Dépôt source de vérité du **cycle de vie feature Git-first d'Essensys** : skills, rules, workflows CI, hooks et schéma de manifestes feature.

Ce fichier configure le comportement des agents IA travaillant sur ce dépôt et sur tout l'écosystème Essensys.

---

## Qui nous sommes

**Essensys** — solution **domotique**. Nous concevons et opérons une plateforme IoT de bout en bout : firmware embarqué, gateways, backends, UIs et infrastructure.

Profil de l'équipe et des agents :

- **Expert électronique, IoT et embarqué** (firmware SC944D, boards PIC16F946, protocole legacy IoT, table d'échange k/v).
- **Sécurité avant tout** — la sécurité est un critère de blocage, jamais une option. Aucun secret en clair, gates sécurité obligatoires, principe du moindre privilège.
- **Open source obligatoire** — pas d'outil propriétaire, pas de dépendance fermée non justifiée. Toolchain libre (GCC, pas d'IDE propriétaire), formats ouverts, licences compatibles.
- **Traçabilité complète** — chaque feature est traçable depuis l'idée (Jira) jusqu'au déploiement, en passant par OpenSpec, issues/tasks, commits, tests, gates et docs.

> Nous ne sommes plus chez Sanofi. Toute référence Sanofi / wise / eWise / Confluence interne est legacy et doit être retirée si rencontrée.

---

## Process feature — bout en bout

Chaque feature suit cette chaîne. La **documentation**, la **revue / autocritique** et la **mise à jour de la mémoire projet** sont continues, pas des étapes finales.

```
Idée → Jira (SCRUM) → OpenSpec → Issues & Tasks Jira → Code → Test×N → Gate sécurité → Deploy (local + OVH)
         └──────────────  Documentation · Revue/autocritique · Mémoire (essensys-memory)  continues ──────────────┘
```

1. **Backlog** — une nouvelle feature est postée dans le projet **Jira SCRUM** : <https://essensys-hub.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog>.
2. **OpenSpec** — générer un change OpenSpec (`openspec-propose` / `/openspec-propose`) : proposal, design, specs, tasks. C'est le contrat de la feature.
3. **Issues & Tasks** — créer les epics / stories / tasks dans Jira, reliées au change OpenSpec (skill `jira-xray-test-campaign` pour le pan test). Le code reste sur GitHub ; chaque commit/PR référence la clé Jira (`SCRUM-123`).
4. **Code** — implémenter selon les specs. Toolchain open source uniquement.
5. **Test · Test · Test** — unitaires, intégration, E2E (Playwright pour les UIs). On ne livre rien sans tests verts.
6. **Gate sécurité** — open source : **gitleaks** (secrets) + **Trivy** (CVE deps + Docker/IaC) + Dependabot, via `security-gate.yml` et `security-gate-triage`. Bloquant. Pas de scanner propriétaire (GitGuardian = dashboard secrets optionnel au plus).
7. **Documentation continue** — la doc est mise à jour **tout au long** du projet, jamais à la fin (doc centralisée, doc install gateway, user guides).
8. **Deploy** — déploiement **local** (gateway / dev) **et OVH** (cloud).
9. **Revue & autocritique continues** — à chaque étape, relire, critiquer, corriger. Self-review avant toute PR ; Bugbot / security-review si pertinent.
10. **Mémoire projet** — mettre à jour **en permanence** `essensys-memory` (voir ci-dessous).

---

## Mémoire projet — `essensys-memory` (obligatoire)

Le vault `essensys-memory/` est la mémoire persistante du projet (legacy + modern). À consulter **avant** toute décision d'architecture et à mettre à jour **en continu**.

Mettre à jour quand :

1. Création ou clôture d'un change OpenSpec.
2. Merge touchant le protocole legacy IoT, la table d'échange, ou le firmware SC944D.
3. Nouveau dépôt ou changement de rôle d'un dépôt.
4. Décision d'architecture (ADR, design OpenSpec).

Comment :

```bash
cd ../essensys-memory
ESSENSYS_ROOT=/Users/nrineau/ESSENSYS ./scripts/sync-sources.sh
ESSENSYS_ROOT=/Users/nrineau/ESSENSYS ./scripts/extract-git-history.sh
ESSENSYS_ROOT=/Users/nrineau/ESSENSYS ./scripts/publish-roadmap-public.sh
# puis ingest sémantique : /second-brain-ingest
```

Pages wiki prioritaires : `wiki/synthesis/platform-overview.md`, `wiki/roadmap/index.md`, Dual Protocol, Table D'Échange.

OpenSpec : changes **métier** dans le dépôt concerné ; change **brain** dans `essensys-memory/openspec/changes/`.

---

## Secrets & SOPS

Aucun secret en clair. Tous les secrets de déploiement (et les **tokens API Jira / GitGuardian**) sont chiffrés avec **SOPS + age** dans `essensys-ansible/secrets/`.

| Secret | Variable SOPS | Fichier |
|---|---|---|
| Token API Jira (board SCRUM) | `JIRA_SECRET` | `essensys-ansible/secrets/cloud/essensys.sops.yaml` |
| Token API GitGuardian (ggshield, optionnel) | `gitguardian_token` | idem |
| Autres (DB, JWT, OAuth, SMTP, New Relic…) | `portal_*`, `vault_*` | idem |

Prérequis opérateur :

```bash
brew install sops age
export SOPS_AGE_KEY_FILE="$HOME/.config/sops/age/keys.txt"   # ou essensys-ansible/.age/keys.txt
```

Récupérer le token Jira pour un appel API / un skill :

```bash
cd essensys-ansible
export JIRA_SECRET="$(sops -d --extract '["JIRA_SECRET"]' secrets/cloud/essensys.sops.yaml)"
# ex. usage : curl -u "<email>:$JIRA_SECRET" https://essensys-hub.atlassian.net/rest/api/3/...
```

Récupérer le token GitGuardian (couche secrets **optionnelle**, non bloquante — la gate reste gitleaks) :

```bash
cd essensys-ansible
export GITGUARDIAN_API_KEY="$(sops -d --extract '["gitguardian_token"]' secrets/cloud/essensys.sops.yaml)"
# ex. usage : pipx run ggshield secret scan repo .   # ou : ggshield secret scan ci
```

Éditer le fichier (jamais en clair, jamais à la racine) :

```bash
cd essensys-ansible
sops secrets/cloud/essensys.sops.yaml   # chemin exact obligatoire
```

Règles : ne **jamais** committer la clé privée age ni un secret déchiffré ; exporter `JIRA_SECRET` / `GITGUARDIAN_API_KEY` en variable d'env éphémère (jamais les écrire dans un fichier versionné, un log ou un transcript). Doc canonique : `essensys-ansible/docs/secrets.md` et `essensys-ansible/secrets/README.md`. Brain : `essensys-memory/wiki/concepts/secrets-management.md`.

---

## Skills actifs

| Skill | Rôle |
|---|---|
| `feature-manifest-orchestrator` | Créer / valider `features/<id>.json` depuis Jira ou OpenSpec |
| `feature-userguide-sync` | Synchroniser `docs/features/*.md` avec manifest + code |
| `playwright-from-spec` | Générer les specs Playwright depuis OpenSpec |
| `feature-lifecycle-bootstrap` | Initialiser le lifecycle dans un repo vide ou existant |
| `security-gate-triage` | Trier secrets (gitleaks), CVE (Trivy), lint sécurité, alertes Dependabot |
| `jira-xray-test-campaign` | Gestion projet Jira + campagnes de test Xray (epics/stories/tasks, Test Plan/Execution) |
| `openspec-explore` / `propose` / `apply-change` / `archive-change` | Workflow OpenSpec |
| `software-architecture` | Guidance architecture qualité |
| `angular-architect` | Patterns front entreprise |
| `gxp-unit-test-report-generator` | Rapports de tests unitaires auditables (traçabilité) |
| `dry-run-install-procedure` | Procédures d'installation dry-run documentées |

Gestion de projet : **Jira** (projet `SCRUM`, <https://essensys-hub.atlassian.net>). Le backlog, les epics/stories/tasks et le suivi vivent dans Jira ; GitHub ne sert qu'au code, aux PR et aux gates CI.

### Rules

| Rule | Effet |
|---|---|
| `playwright-ui-tests` | Tests UI Playwright robustes |
| `release-changelog-auto` | Discipline changelog |
| `github-issue-done-commit-push` | Cycle de vie des issues GitHub (traçabilité commit ↔ issue) |
| `language` | Convention de langue assistant (français) |
| `security-gate` | Politique secrets / CVE / Dockerfile / workflows |
| `gxp-exec` | Exécution rigoureuse : dry-run, prérequis, écarts |
| `dry-run-install-doc` | Sync doc d'installation |

---

## Prompts utiles

```text
bootstrap feature lifecycle
new feature SCRUM-123
openspec propose <feature>
create jira tasks for this change
generate e2e tests for this feature
triage security findings
sync user guide for this feature
update essensys-memory
```

---

## Comportement de l'agent

### Toujours faire

- Partir du **backlog Jira (SCRUM)** et d'un **change OpenSpec** ; ne jamais coder une feature sans spec.
- Garder **doc, tests, manifest et mémoire** alignés en continu.
- Valider les manifests contre `features/schema/feature.schema.json` avant commit.
- Passer la **gate sécurité** (`security-gate-triage` + Dependabot) ; la traiter comme bloquante.
- Préférer / imposer des solutions **open source** ; justifier toute dépendance.
- Assurer la **traçabilité** : commit/PR ↔ clé Jira (`SCRUM-123`) ↔ task ↔ change OpenSpec.
- Pratiquer la **revue et l'autocritique** à chaque étape, pas seulement en fin de projet.
- Mettre à jour `essensys-memory` dès qu'un critère d'update est rempli.
- Respecter les jumeaux à synchroniser : `essensys-server-frontend` ↔ `essensys-user-portal-frontend`, `essensys-server-backend` ↔ `essensys-user-portal-backend`.

### Ne jamais faire

- Introduire un outil / une dépendance **propriétaire** ou un IDE fermé.
- Publier un **secret** dans le dépôt (utiliser SOPS, cf. section Secrets & SOPS). Le token Jira est `JIRA_SECRET` dans `essensys-ansible/secrets/cloud/essensys.sops.yaml`.
- Modifier les indices k/v du protocole legacy IoT ou la table d'échange sans mise à jour de la mémoire.
- Contourner une **gate CI** (feature ou sécurité).
- Livrer sans **tests** ni **documentation** à jour.
- Réintroduire des références **Sanofi / wise / eWise**.

### Checklist PR

- [ ] Change OpenSpec lié (ou N/A justifié)
- [ ] Issues / tasks Jira (SCRUM) mises à jour, clé Jira dans le titre de PR
- [ ] Tests verts (unit / intégration / E2E)
- [ ] Gate sécurité passée
- [ ] Documentation mise à jour
- [ ] Déploiement vérifié (local + OVH le cas échéant)
- [ ] Brain mis à jour (`essensys-memory`) ou N/A
