# essensys-feature-lifecycle

> Dépôt source de vérité du **cycle de vie feature Git-first d'Essensys** : skills, rules, workflows CI, hooks et schéma de manifestes.
>
> Voir [`AGENTS.md`](AGENTS.md) pour l'identité, les principes (sécurité, open source, traçabilité) et le process complet.

Essensys — solution **domotique**, expertise électronique / IoT / embarqué. Trois exigences non négociables :

- **Sécurité** : critère bloquant, jamais optionnel.
- **Open source** : toolchain et dépendances libres, formats ouverts.
- **Traçabilité complète** : de l'idée au déploiement, tout est relié dans Git.

---

## Le process feature, de bout en bout

La doc, la revue/autocritique et la mise à jour de la mémoire (`essensys-memory`) sont **continues** — pas des étapes finales.

```
Idée → Jira (SCRUM) → OpenSpec → Issues & Tasks Jira → Code → Test×N → Gate sécurité → Deploy (local + OVH)
         └──────────  Documentation · Revue/autocritique · Mémoire (essensys-memory)  continues ──────────┘
```

| # | Étape | Outil / artefact |
|---|---|---|
| 1 | Backlog | Projet **Jira SCRUM** → <https://essensys-hub.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog> |
| 2 | Spec | Change OpenSpec (`openspec-propose`) : proposal, design, specs, tasks |
| 3 | Découpage | Epics / stories / tasks dans Jira (`jira-xray-test-campaign`) |
| 4 | Code | Implémentation selon les specs, toolchain open source |
| 5 | Tests | Unit / intégration / E2E + gate UX desktop/iPhone/iPad obligatoire pour les UIs (Playwright + no-armoire) |
| 6 | Sécurité | open source : gitleaks (secrets) + Trivy (CVE/IaC) + Dependabot, via `security-gate.yml` (bloquant) |
| 7 | Doc | Mise à jour **continue** (doc centralisée, install, user guides) |
| 8 | Deploy | Local (gateway / dev) **et** OVH (cloud) |
| 9 | Revue | Autocritique à chaque étape + Bugbot / security-review |
| 10 | Mémoire | Mise à jour permanente de `essensys-memory` |

Le pivot reste **un manifest versionné par feature**, validé par JSON Schema et consommé par chaque gate CI :

```text
features/<id>.json   ←   source de vérité de la feature
```

Narratif détaillé : [`docs/features/feature-lifecycle.md`](docs/features/feature-lifecycle.md).
Guides équipe : [`docs/feature-lifecycle/`](docs/feature-lifecycle/).
Orchestration IA / subagents : [`docs/feature-lifecycle/ai-orchestration.md`](docs/feature-lifecycle/ai-orchestration.md).

---

## Contenu du profil (24 artefacts)

### Skills (15) — `.cursor/skills/<name>/SKILL.md`

| # | Skill | Rôle |
|---|---|---|
| 1 | `feature-manifest-orchestrator`  | Créer / mettre à jour `features/<id>.json` depuis Jira ou OpenSpec |
| 2 | `feature-userguide-sync`         | Synchroniser `docs/features/*.md` avec manifest + code |
| 3 | `playwright-from-spec`           | Générer les squelettes Playwright depuis OpenSpec |
| 4 | `feature-lifecycle-bootstrap`    | Initialiser le lifecycle dans un repo vide ou existant |
| 5 | `security-gate-triage`           | Trier secrets, CVE, lint sécurité, alertes Dependabot |
| 6 | `jira-xray-test-campaign`        | Gestion projet Jira (epics/stories/tasks) + campagnes de test Xray |
| 7 | `openspec-explore`               | Explorer le besoin avant de coder |
| 8 | `openspec-propose`               | Proposer un nouveau change OpenSpec |
| 9 | `openspec-apply-change`          | Implémenter les tasks OpenSpec |
| 10 | `openspec-archive-change`       | Archiver un change terminé |
| 11 | `software-architecture`         | Guidance architecture qualité |
| 12 | `angular-architect`             | Patterns front entreprise |
| 13 | `gxp-unit-test-report-generator`| Rapports de tests unitaires auditables |
| 14 | `dry-run-install-procedure`     | Procédures d'installation dry-run documentées |
| 15 | `essensys-ux-regression-gate`  | Gate UX desktop/iPhone/iPad + no-armoire pour frontends |

### Rules (8) — `.cursor/rules/<name>.mdc`

| # | Rule | Portée |
|---|---|---|
| 1 | `playwright-ui-tests`           | Tests UI Playwright robustes |
| 2 | `release-changelog-auto`        | Discipline changelog |
| 3 | `github-issue-done-commit-push` | Cycle de vie des issues GitHub (commit ↔ issue) |
| 4 | `language`                      | Convention de langue (français) |
| 5 | `security-gate`                 | Politique secrets / CVE / Dockerfile / workflows |
| 6 | `gxp-exec`                      | Exécution rigoureuse : dry-run, prérequis, écarts |
| 7 | `dry-run-install-doc`           | Sync des docs d'installation dry-run |
| 8 | `essensys-ux-matrix-gate`      | Non-régression UX desktop/iPhone/iPad obligatoire |

---

## Arborescence du dépôt

```
essensys-feature-lifecycle/
├── AGENTS.md                                  ← contexte agent (identité + process)
├── .env.example                               ← template env (copier vers .env)
├── .env                                       ← valeurs réelles, gitignored
│
├── .cursor/
│   ├── skills/<15 dossiers>/SKILL.md          ← skills du profil
│   └── rules/<8 fichiers>.mdc                 ← rules du profil
│
├── .github/workflows/
│   ├── feature-gate.yml                       ← schéma, chemins, couverture, fraîcheur
│   ├── ux-matrix-gate.yml                     ← template/gate UX desktop+iPhone+iPad pour frontends
│   ├── security-gate.yml                      ← gitleaks, audit deps, lint sécurité
│   └── publish-wise-feature-lifecycle.yml     ← publication du profil (Skills Portal)
│
├── features/
│   ├── schema/feature.schema.json             ← JSON Schema 2020-12
│   └── *.json                                 ← manifests de features
│
├── scripts/
│   ├── hooks/pre-commit                       ← lint schéma + gitleaks (warning)
│   └── feature_lifecycle/                     ← validation, gate, publication
│
└── docs/
    ├── features/feature-lifecycle.md          ← méta-doc du process
    └── feature-lifecycle/                     ← guides équipe (FR + EN)
```

---

## Démarrage rapide (dev local)

```bash
git clone https://github.com/essensys-hub/essensys-feature-lifecycle.git
cd essensys-feature-lifecycle

cp .env.example .env           # renseigner les valeurs locales

# Valider tous les manifests contre le schéma
python3 scripts/feature_lifecycle/validate_feature_manifests.py features/
```

Dans Cursor, suivre le process :

```text
openspec propose <feature>
create jira tasks for this change
generate e2e tests for this feature
triage security findings
sync user guide for this feature
update essensys-memory
```

---

## Déploiement

Les features sont déployées sur **deux cibles** :

| Cible | Rôle | Outillage |
|---|---|---|
| **Local** | Gateway / environnement de dev | Ansible (`essensys-ansible`), Docker Compose |
| **OVH** | Cloud (backends, portail, sites publics) | Ansible / Docker, reverse proxy Traefik/Nginx |

La publication du **profil de skills** (ce dépôt) reste assurée par `publish-wise-feature-lifecycle.yml` (cf. `doc_install/`), avec gate d'approbation GitHub Environments sur les cibles protégées.

---

## Secrets (SOPS + age)

Aucun secret en clair. Les secrets — dont le **token API Jira** `JIRA_SECRET` et le **token GitGuardian** `gitguardian_token` (ggshield, optionnel) — sont chiffrés avec SOPS + age dans `essensys-ansible/secrets/cloud/essensys.sops.yaml`.

```bash
cd ../essensys-ansible
export SOPS_AGE_KEY_FILE="$HOME/.config/sops/age/keys.txt"
export JIRA_SECRET="$(sops -d --extract '["JIRA_SECRET"]' secrets/cloud/essensys.sops.yaml)"
export GITGUARDIAN_API_KEY="$(sops -d --extract '["gitguardian_token"]' secrets/cloud/essensys.sops.yaml)"
```

Détails et règles : `AGENTS.md` → section **Secrets & SOPS** ; doc canonique `essensys-ansible/docs/secrets.md`.

---

## Mémoire projet

Toute décision d'architecture et tout merge touchant le protocole legacy IoT, la table d'échange ou le firmware SC944D **doit** mettre à jour `essensys-memory` (voir `AGENTS.md` → section Mémoire projet).

---

## Provenance

Fork Essensys d'un profil de cycle de vie feature Git-first. Historique d'origine conservé dans les tags Git.
