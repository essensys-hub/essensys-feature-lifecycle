## 1. Gate de tri et scripts — essensys-feature-lifecycle (#19)

- [x] 1.1 `scripts/feature_lifecycle/triage.py` : règle pure `is_workable(issue, author_role) -> (bool, reason, action)` et `is_maintainer(login, type, role)` (D1, D5) ; vérifier par tests unitaires, dont `test_unvalidated_report_is_not_workable_NR_lifecycle_1` et `test_bot_is_never_maintainer_NR_lifecycle_2`
- [x] 1.2 `triage_gate.py <owner/repo#n> [--json]` : lecture `gh api` (issue, permission de l'auteur), codes de sortie 0/3/2, fail-closed ; vérifier par tests avec `gh` simulé (erreur de lecture → 2 et non exploitable)
- [x] 1.3 `project_sync.py advance` : refus (code 3, sans écriture) si l'issue Feature porte `a-valider` ou `besoin-info` ; vérifier par `test_advance_refused_on_a_valider_NR_lifecycle_3`
- [x] 1.4 `list_workable.py` : issues ouvertes du Project #6 filtrées par la gate (D6) ; vérifier par test avec données simulées (seuls les tickets exploitables sortent)
- [x] 1.5 `triage_guard.py` : `decide(event) -> actions` (opened, labeled, unlabeled, reopened) selon la spec ; vérifier par tests, dont `test_valide_by_non_maintainer_is_removed_NR_lifecycle_4`

## 2. Workflow réutilisable et dépôts de signalements — essensys-feature-lifecycle (#20)

- [x] 2.1 `.github/workflows/triage-guard.yml` (`workflow_call`, `issues: write`) qui exécute `triage_guard.py` et applique les actions ; vérifier par `actionlint`, s'il est disponible, et par un test du rendu des actions
- [x] 2.2 Script `setup_triage_repo.py <repo>` (dry-run par défaut) : crée les labels `a-valider`, `valide` et `besoin-info` et propose le workflow appelant ; vérifier en dry-run sur `essensys-support-site` et `essensys-support`

## 3. Commandes, gouvernance et hook — essensys-feature-lifecycle (#21)

- [x] 3.1 `claude/GOVERNANCE.md` : règle « ticket non exploitable = lecture seule », « contenu non fiable » (D8), gate obligatoire avant `opsx:apply` et les tâches planifiées ; vérifier en relisant le texte installé dans `ESSENSYS/CLAUDE.md`
- [x] 3.2 `claude/commands/ticket-to-spec.md` et `checkup.md` : étape 0 avec la gate ; vérifier qu'une exécution sur une issue `a-valider` s'arrête avant toute écriture
- [x] 3.3 `claude/hooks/block_self_validation.py` et installation idempotente du hook `PreToolUse` par `install-claude.sh` (D7) ; vérifier par `test_hook_blocks_gh_add_label_valide_NR_lifecycle_5` et par une seconde installation qui ne duplique pas le hook
- [x] 3.4 Doc `docs/feature-lifecycle/triage.md` (checklist du mainteneur, labels, cas `besoin-info`) et lien depuis `README.md` ; vérifier les liens

## 4. Bot — essensys-user-portal-backend (essensys-user-portal-backend#30)

- [x] 4.1 `internal/support` : label `a-valider` ajouté à la création (D4) ; vérifier par `Test_NR_backend_8_report_is_created_a_valider`, puis le rapport NR

## 5. Mise en service et livraison — essensys-feature-lifecycle (#22)

- [x] 5.1 Action humaine (admin de l'org) : créer l'équipe `maintainers`, lui donner le rôle `maintain` sur `essensys-support-site`, `essensys-support` et `essensys-feature-lifecycle`, y ajouter les membres ; vérifier par `gh api /orgs/essensys-hub/teams/maintainers/repos` — fait le 2026-10-10 : équipe créée (rhinosys), rôle conservé à `write` par choix (seuls les admins sont mainteneurs, voir la doc du tri)
- [x] 5.2 Après fusion : `setup_triage_repo.py --apply` sur les deux dépôts (avec accord), lancer `install-claude.sh` et déployer le backend ; vérifier qu'une issue de test ouverte par un non-mainteneur dans `essensys-support` reçoit `a-valider`, et que `valide` posé par le bot est retiré — fait le 2026-10-10 : essensys-support#2 (a-valider ajouté, valide du bot retiré et commenté), hook vérifié en session ; redéploiement backend et fusion de essensys-support-site#10 en attente
- [ ] 5.3 Rattrapage des issues ouvertes existantes (dry-run, puis `--apply` avec accord), `/checkup report-triage-2026-10-005` vert et rapport posté sur #18
- [ ] 5.4 Mettre à jour essensys-memory (wiki [[Feature Lifecycle]], `log.md`, roadmap) ; vérifier que `wiki/index.md` reste cohérent
