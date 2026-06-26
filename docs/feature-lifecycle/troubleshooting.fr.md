# Dépannage

Quand une PR est bloquée, voici le chemin le plus court.

## Ma PR est bloquée par feature-gate

Relis le commentaire PR puis demande :

```text
create feature manifest
```

ou :

```text
sync user guide for this feature
```

## Ma PR est bloquée par security-gate

Dans Cursor :

```text
triage security findings
```

Commence toujours par les secrets et les Critical/High. La gate sécurité est bloquante par design. Elle est 100% open source : **gitleaks** (secrets), **Trivy** (CVE deps + Docker/IaC) et Dependabot. Le rapport Trivy est dans l'artefact `.artifacts/security-gate/trivy.json` ; pour muter un CVE non corrigeable, ajoute une entrée justifiée dans `.trivyignore` et trace-la dans `security.muted_findings[]`.

## Un secret a fuité

Ne mute jamais un secret. Lance le nettoyage d'historique avec le skill adapté, puis fais la **rotation** du secret. Stocke les secrets via SOPS / vault Ansible / Secrets Manager — jamais en clair.

## Le guide utilisateur n'est pas à jour

Le sync doc n'est pas automatique. Lance :

```text
sync user guide for this feature
```

## Mes tasks Jira ne se synchronisent pas

Vérifie :

- que le change OpenSpec existe et que ses tasks sont à jour
- que les tasks Jira (SCRUM) sont bien reliées au manifest `features/<id>.json`
- que la clé Jira `SCRUM-123` figure dans le titre de PR / les commits
- relance `create jira tasks for this change`

## L'API Jira renvoie 401 / 403

Le token API est dans SOPS. Vérifie :

- `SOPS_AGE_KEY_FILE` pointe sur ta clé age privée
- le token se déchiffre :

```bash
cd essensys-ansible
export JIRA_SECRET="$(sops -d --extract '["JIRA_SECRET"]' secrets/cloud/essensys.sops.yaml)"
[ -n "$JIRA_SECRET" ] && echo "token OK"
```

- l'appel utilise bien `-u "<email>:$JIRA_SECRET"` (Basic auth Atlassian Cloud)
- si le token a expiré : le régénérer dans Atlassian, puis `sops secrets/cloud/essensys.sops.yaml` pour le remplacer. Jamais en clair dans Git.

## Le déploiement échoue (local ou OVH)

- Local : vérifie l'inventaire et les rôles `essensys-ansible`
- OVH : vérifie le reverse proxy (Traefik/Nginx) et les secrets de déploiement
- Consulte la doc d'installation gateway

## J'ai oublié de mettre à jour la mémoire

Toute décision d'archi ou tout merge touchant le protocole legacy IoT / table d'échange / firmware SC944D doit déclencher :

```text
update essensys-memory
```

## Je veux désinstaller le lifecycle

Utilise le bootstrap en sens inverse et relis le diff avant suppression.
