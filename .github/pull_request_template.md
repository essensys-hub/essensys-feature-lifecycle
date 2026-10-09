<!-- Gouvernance Essensys : toute PR est liée à un ticket du GitHub Project #6 (claude/GOVERNANCE.md). -->

Feature: <feature-id>   <!-- ex. android-portal-refresh-2026-10-001 ; PR hors feature : label chore/no-feature -->
Closes #<n>             <!-- ou Refs #<n> si la PR ne termine pas l'issue -->

## Intent

<!-- Ce que change la PR et pourquoi (lien OpenSpec si applicable). -->

## Vérification (`/checkup`)

- [ ] Build + lint
- [ ] Tests unitaires
- [ ] Non-régression (`NR-*`) — tout Bug corrigé a un test `NR-<repo>-<n>` référençant `#<bug>`
- [ ] Tests applicatifs (Playwright desktop/iPhone/iPad · émulateur Android · simulateur iOS), `no-armoire`
- [ ] Gates `feature-gate` + `security-gate`
- [ ] Doc / manifest / mémoire à jour (ou N/A)
