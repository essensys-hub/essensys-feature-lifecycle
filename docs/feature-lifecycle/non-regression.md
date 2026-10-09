# Non-régression Essensys

> Change : `openspec/changes/github-project-lifecycle-2026-10-001` (capability `regression-test-tracking`).

Un test de non-régression (NR) protège un comportement déjà livré ou un bug déjà corrigé. On l'identifie par un identifiant stable et on le relie toujours à l'issue d'origine dans le GitHub Project #6.

## Convention

- **Identifiant** : `NR-<repo-court>-<n>`, par exemple `NR-server-backend-12`, `NR-android-3` ou `NR-portal-frontend-7`. Le `<n>` est incrémental par dépôt et ne se réutilise jamais.
- **Référence** : `#<issue>` pour une issue du même dépôt, ou `essensys-hub/<repo>#<n>`.
- Un test marqué NR **sans** référence d'issue fait échouer le rapport (`nonreg_report.py` sort avec le code 1).

### Go (backends jumeaux)

```go
// NR: NR-server-backend-12 #45
func TestInjectKeepsLegacyIndex_NR_server_backend_12(t *testing.T) { ... }
```

Pour obtenir du JUnit XML : `gotestsum --junitfile .artifacts/go-junit.xml ./...`.

### Kotlin / JUnit (Android)

```kotlin
// NR: NR-android-3 essensys-hub/essensys-android-phone-apps#12
@Test
fun shutterAllDown_sendsKitchenAndLiving_NR_android_3() { ... }
```

En Kotlin et en Go, un nom de test ne peut pas contenir `-` : on écrit l'identifiant `NR_android_3` dans le nom, et `nonreg_report.py` le normalise en `NR-android-3`. Le JUnit XML ne contient pas les commentaires : l'issue se lit dans le commentaire `// NR:` grâce à `--sources app/src`.

Gradle écrit les rapports dans `app/build/test-results/testDebugUnitTest/*.xml` pour les tests unitaires. Les tests instrumentés sur émulateur (`connectedDebugAndroidTest`) écrivent dans `app/build/outputs/androidTest-results/connected/**/*.xml`.

### Playwright (frontends)

```ts
test('volets cuisine remontent', {
  tag: ['@nr', '@NR-portal-frontend-7'],
  annotation: { type: 'issue', description: 'essensys-hub/essensys-user-portal-frontend#31' },
}, async ({ page }) => { ... });
```

Utiliser le reporter `json` : `npx playwright test --grep @nr --reporter=json > .artifacts/pw.json`. Toujours en mode `NO_ARMOIRE=1`.

### Python (pytest)

```python
@pytest.mark.nr("NR-server-backend-20", "#52")
def test_chb3_scenario_playback(): ...
```

Ou bien un commentaire `# NR: NR-server-backend-20 #52` au-dessus du test. Pour le JUnit XML : `pytest --junitxml=.artifacts/pytest.xml`.

## Règles

1. **Corriger un bug implique d'ajouter un test NR.** Une PR qui ferme une issue de type `Bug` doit modifier au moins un fichier contenant `NR-` et `#<bug>` sur la même ligne. Sinon, il faut le label `nr-exempt` avec une justification en commentaire. C'est vérifié par `check_pr_linkage.py` dans `feature-gate`.
2. **Exécution continue** : la suite tourne sur chaque PR et chaque nuit, via le workflow réutilisable `.github/workflows/nonreg.yml`.
3. **Un échec devient un Bug** : en nightly ou sur `main`, `project_sync.py regression` ouvre un `Bug` (label `regression`, marqueur `<!-- nr:NR-… -->`). Si un Bug ouvert existe déjà pour ce test, il le commente au lieu d'en créer un autre.
4. **Tests instables** : après 2 alternances vert/rouge, le test reçoit le label `flaky`. Au bout de 3 nightlies vertes, un commentaire propose la fermeture du Bug. La fermeture automatique n'existe pas.

## Lancer en local

Utiliser `/checkup <repo>` ou `/nonreg` dans Claude Code. On peut aussi lancer à la main :

```bash
python3 essensys-feature-lifecycle/scripts/feature_lifecycle/nonreg_report.py \
  --out .artifacts/nonreg.json --markdown .artifacts/nonreg.md \
  --sources app/src \
  app/build/test-results/**/*.xml
```
