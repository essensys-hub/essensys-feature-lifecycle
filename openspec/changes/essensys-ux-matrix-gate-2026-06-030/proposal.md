## Why

Les features UI ESSENSYS peuvent aujourd'hui passer le lifecycle avec un manifest valide et quelques tests E2E, sans preuve bloquante que les formats desktop, iPhone et iPad ont réellement été couverts. Cela laisse passer des régressions UX critiques : navigation mobile masquée, contrôles inaccessibles, layouts cassés tablette, ou actions domotiques testées sans garde `no-armoire`.

## What Changes

- Ajouter une gate UX multi-device au lifecycle feature.
- Étendre le manifest `features/<id>.json` pour déclarer `tests.ux_matrix` et `tests.ux_evidence`.
- Faire échouer `check_feature_gate.py --strict` quand une feature UI ne déclare pas au minimum desktop + iPhone + iPad.
- Vérifier que les tests Playwright déclarés contiennent la couverture device obligatoire via annotations/tags de test.
- Ajouter une workflow/template CI `ux-matrix-gate.yml` exécutable dans les frontends ESSENSYS.
- Ajouter une rule Cursor et un skill agent pour imposer la discipline UX matrix + no-armoire.
- Documenter cette gate dans README/docs et dans le bootstrap lifecycle.

## Capabilities

### New Capabilities

- `ux-matrix-gate`: gate bloquante pour les features UI : desktop, iPhone, iPad, evidence Playwright et garde no-armoire.

### Modified Capabilities

- `feature-manifest`: enrichit le contrat JSON Schema des manifests avec `tests.ux_matrix` et `tests.ux_evidence`.
- `feature-gate`: durcit `check_feature_gate.py` pour vérifier la déclaration UX et les annotations Playwright.
- `feature-lifecycle-bootstrap`: ajoute templates CI/rule pour propager la gate aux repos frontends.

## Impact

- `features/schema/feature.schema.json`
- `.cursor/skills/feature-lifecycle-bootstrap/templates/features/schema/feature.schema.json`
- `scripts/feature_lifecycle/check_feature_gate.py`
- `.github/workflows/feature-gate.yml`
- `.cursor/rules/essensys-ux-matrix-gate.mdc`
- `.cursor/skills/essensys-ux-regression-gate/SKILL.md`
- `.cursor/skills/playwright-from-spec/SKILL.md`
- `.cursor/skills/feature-lifecycle-bootstrap/templates/.github/workflows/ux-matrix-gate.yml.tpl`
- `.cursor/skills/feature-lifecycle-bootstrap/templates/.cursor/rules/essensys-ux-matrix-gate.mdc.tpl`
- README/docs lifecycle
