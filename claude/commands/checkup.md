---
description: Vérifier une feature ou un dépôt Essensys (build, lint, unit, non-régression, app, gates) et publier le rapport sur l'issue
argument-hint: [<Feature ID> | <repo>]  (défaut : dépôt courant)
---

Cible : $ARGUMENTS

Suis `essensys-feature-lifecycle/claude/GOVERNANCE.md`. Exécute réellement chaque étape, ne suppose jamais un résultat. **Jamais d'armoire réelle** : `NO_ARMOIRE=1`, serveurs mock/locaux uniquement.

1. **Résoudre la cible** : Feature ID → manifest (`features/<id>.json`, champ `github.issue`, `implementation.paths` → dépôts) ; repo → dossier `ESSENSYS/<repo>` ; issue liée = issue Feature (ou dernière issue ouverte du Project pour ce dépôt, à confirmer).
2. **Détecter la pile** et lancer, en notant OK/KO/N.A. + durée + extrait d'erreur :

   | Pile | Build / lint | Unit | Non-régression | App |
   |---|---|---|---|---|
   | Go (`go.mod`) | `go build ./...`, `go vet ./...`, `gofmt -l .` | `go test ./...` (via `gotestsum --junitfile` si dispo) | tests `NR-*` du rapport | `test/test_server.sh` si serveur local |
   | Node/Vite (`package.json`) | `npm run build`, `npm run lint` | `npm test` si défini | Playwright `--grep @nr` | Playwright matrice desktop/iphone/ipad |
   | Android (`gradlew`) | `./gradlew assembleDebug lintDebug` | `./gradlew testDebugUnitTest` | JUnit `NR-*` | émulateur : `emulator -avd <avd> -no-window` (AVD existant, sinon le signaler), `./gradlew connectedDebugAndroidTest`, puis installer l'APK, lancer l'app et capturer les écrans clés (`adb exec-out screencap -p`) |
   | iOS (`*.xcodeproj`) | `xcodebuild build` | `xcodebuild test` | XCTest `NR-*` | simulateur iOS (outil simulateur Claude Code) |
   | Python | `python3 -m compileall` | `pytest` / `unittest` | marqueur `nr` | — |

   Outils Android : `~/Library/Android/sdk/{platform-tools,emulator,cmdline-tools/latest/bin}` (les ajouter au PATH si absents).
3. **Rapport NR** : `python3 essensys-feature-lifecycle/scripts/feature_lifecycle/nonreg_report.py --out .artifacts/nonreg.json --markdown .artifacts/nonreg.md <junit/json>`.
4. **Gates** : `validate_feature_manifests.py`, `check_feature_gate.py --strict`, et si une PR est ouverte `gh pr checks` (feature-gate, security-gate). Sinon `gitleaks detect --no-git` si installé.
5. **Rapport** markdown : tableau étape/statut/durée, captures (chemins), écarts vs critères d'acceptation du ticket, verdict global (VERT seulement si tout OK ou N.A. justifié).
6. Montre le rapport ; **après confirmation**, poste-le en commentaire de l'issue (`gh issue comment ... --body-file`) avec le marqueur `<!-- checkup -->` (mettre à jour le commentaire existant plutôt qu'en ajouter un). Si VERT et toutes les PR liées mergées : `project_sync.py advance <id> tests-passed --apply`.
