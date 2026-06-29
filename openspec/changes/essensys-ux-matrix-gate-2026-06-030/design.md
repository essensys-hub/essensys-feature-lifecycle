## Context

Le lifecycle ESSENSYS possède déjà un `feature-gate` qui valide les manifests et la couverture déclarative. Il ne force pas encore une validation UX multi-device réellement bloquante. La mémoire `essensys-memory` contient déjà la vision cible dans `essensys-ui-multi-device-testing`, mais le contrat n'est pas intégré au profil source `essensys-feature-lifecycle`.

## Design

### Manifest contract

Ajouter deux champs optionnels sous `tests` :

```json
"ux_matrix": {
  "required": true,
  "devices": ["desktop", "iphone", "ipad"],
  "targets": ["local", "remote", "support"],
  "required_projects": ["support-desktop", "support-iphone", "support-ipad"],
  "screenshots_required": true,
  "visual_regression_required": true,
  "no_armoire_required": true
},
"ux_evidence": {
  "playwright_report": "playwright-report/index.html",
  "screenshots": ["e2e/artifacts/screenshots/..."],
  "last_run_at": "2026-06-28T00:00:00Z",
  "devices_validated": ["desktop", "iphone", "ipad"],
  "status": "passed"
}
```

`ux_matrix` devient obligatoire par gate lorsque la feature est détectée comme UI.

### UI detection

`check_feature_gate.py` considère une feature comme UI si l'une des conditions est vraie :

- `implementation.primary_surface` vaut `react-user`, `react-admin`, ou `mixed`.
- `implementation.paths`, `tests.playwright`, `userguide.screenshots`, ou `release.surfaces` mentionnent frontend/UI : `src/pages`, `src/components`, `.tsx`, `.jsx`, `playwright`, `e2e`, `frontend`, `portal`, `ui`.

### Blocking checks

En mode `--strict`, les erreurs bloquent si une feature UI :

- n'a pas `tests.ux_matrix.required=true` ;
- ne contient pas au minimum `desktop`, `iphone`, `ipad` dans `devices` ;
- n'a aucun `required_projects` couvrant ces devices ;
- n'a pas `no_armoire_required=true` pour les surfaces domotiques ;
- ne référence pas de tests Playwright ;
- ne contient pas d'annotation/titre test permettant de prouver la matrix : `@device: desktop`, `@device: iphone`, `@device: ipad`, `@devices: desktop,iphone,ipad`, project names ou équivalents.

### CI execution

Le profil fournit un template `ux-matrix-gate.yml.tpl` à installer dans les frontends. Le workflow doit :

1. installer Node et dépendances ;
2. installer Playwright ;
3. lister les projects ;
4. exécuter les projects desktop/iPhone/iPad requis ;
5. uploader rapport Playwright et screenshots ;
6. échouer si les tests ou artifacts requis manquent.

### No-armoire safety

La rule et le skill imposent `no-armoire` : aucune mutation vers `/api/admin/inject`, `/api/portal/inject`, `/api/web/actions` ou `/scenarios/*/launch` ne doit atteindre une armoire réelle sans dry-run explicite.

## Non-goals

- Ne pas imposer Lost Pixel en dépendance CI obligatoire.
- Ne pas forcer Android ou écran domotique dans la gate minimale ; ils restent recommandés ou requis par feature spécifique.
- Ne pas exécuter Playwright depuis `essensys-feature-lifecycle` lui-même, car le profil source n'est pas un frontend.
