#!/usr/bin/env bash
# Test de bout en bout de la Feature sonnette-plages-push-2026-11-008 (#61, tâche 11.1).
# Sans armoire réelle (NO_ARMOIRE=1), sans appel réseau sortant. Voir README.md.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ESSENSYS_ROOT="${ESSENSYS_ROOT:-$HOME/ESSENSYS}"
GATEWAY_REPO="${GATEWAY_REPO:-$ESSENSYS_ROOT/essensys-server-backend}"
CLOUD_REPO="${CLOUD_REPO:-$ESSENSYS_ROOT/essensys-user-portal-backend}"
GATEWAY_REF="${GATEWAY_REF:-feat/sonnette-plages-push-2026-11-008}"
CLOUD_REF="${CLOUD_REF:-feat/sonnette-plages-push-2026-11-008}"
PG_BIN="${PG_BIN:-$(dirname "$(command -v initdb 2>/dev/null || echo /opt/homebrew/opt/postgresql@15/bin/initdb)")}"
KEEP="${KEEP:-0}"

for b in git go grep; do command -v "$b" >/dev/null || { echo "outil manquant : $b" >&2; exit 2; }; done
for b in initdb pg_ctl createdb; do [ -x "$PG_BIN/$b" ] || { echo "PostgreSQL local requis ($b introuvable dans $PG_BIN ; PG_BIN=...)" >&2; exit 2; }; done

WORK="$(mktemp -d "${TMPDIR:-/tmp}/essensys-e2e.XXXXXX")"
# La socket Unix de PostgreSQL a une limite de chemin (~100 caractères) : dossier court sous /tmp.
PGROOT="$(mktemp -d /tmp/essensys-e2e-pg.XXXXXX)"
LOGDIR="${LOGDIR:-$WORK/logs}"; ART="$WORK/artifacts"
mkdir -p "$LOGDIR" "$ART"

cleanup() {
  "$PG_BIN/pg_ctl" -D "$PGROOT/data" -m immediate stop >/dev/null 2>&1 || true
  rm -rf "$PGROOT"
  if [ "$KEEP" = 1 ]; then echo "Fichiers conservés : $WORK"; else [ "$LOGDIR" = "$WORK/logs" ] && rm -rf "$WORK" || rm -rf "$WORK/gw-root" "$WORK/cloud" "$ART"; fi
}
trap cleanup EXIT

export LC_ALL=C LANG=C NO_ARMOIRE=1 GOPROXY=off GOFLAGS=-mod=mod GOTOOLCHAIN=local
export E2E_LOGDIR="$LOGDIR" E2E_ARTIFACTS="$ART"

echo "== Extraction ($GATEWAY_REF, $CLOUD_REF) =="
# La gateway a des « replace » vers des dépôts voisins (../essensys-audit-collector, ...) : on les relie.
GWROOT="$WORK/gw-root"; mkdir -p "$GWROOT/essensys-server-backend"
for d in essensys-audit-collector essensys-plugin-framework essensys-plugin-sungrow; do ln -s "$ESSENSYS_ROOT/$d" "$GWROOT/$d"; done
git -C "$GATEWAY_REPO" archive "$GATEWAY_REF" | tar -x -C "$GWROOT/essensys-server-backend"
mkdir -p "$GWROOT/essensys-server-backend/internal/e2e"
cp "$HERE/gateway/e2e_gateway_test.go" "$GWROOT/essensys-server-backend/internal/e2e/"
CLOUDDIR="$WORK/cloud"; mkdir -p "$CLOUDDIR/internal/e2e"
git -C "$CLOUD_REPO" archive "$CLOUD_REF" | tar -x -C "$CLOUDDIR"
cp "$HERE/cloud/e2e_cloud_test.go" "$CLOUDDIR/internal/e2e/"
echo "gateway : $(git -C "$GATEWAY_REPO" rev-parse --short "$GATEWAY_REF")   cloud : $(git -C "$CLOUD_REPO" rev-parse --short "$CLOUD_REF")"

echo "== PostgreSQL local (socket Unix, aucune écoute réseau) =="
"$PG_BIN/initdb" -D "$PGROOT/data" -U e2e -A trust --no-sync --locale=C -E UTF8 >/dev/null
"$PG_BIN/pg_ctl" -D "$PGROOT/data" -l "$LOGDIR/postgres.log" -w start \
  -o "-c listen_addresses= -c unix_socket_directories=$PGROOT -c fsync=off -c port=54329" >/dev/null
"$PG_BIN/createdb" -h "$PGROOT" -p 54329 -U e2e e2e
export E2E_PG_HOST="$PGROOT" E2E_PG_PORT=54329 E2E_PG_USER=e2e E2E_PG_DB=e2e

status=0
echo "== Phase gateway (vrai code gateway, fausse console UniFi, faux cloud, fausse armoire) =="
(cd "$GWROOT/essensys-server-backend" && go test -count=1 -v ./internal/e2e/ ) >"$LOGDIR/gateway-stdout.log" 2>&1 || status=1
grep -E "^(=== RUN|--- |\s+--- |PASS|FAIL|ok)|e2e_gateway_test.go" "$LOGDIR/gateway-stdout.log" | grep -v "=== RUN" || true

echo "== Phase cloud (vrai cloud + PostgreSQL, faux FCM/APNs, requête rejouée de la gateway) =="
(cd "$CLOUDDIR" && go test -count=1 -v ./internal/e2e/ ) >"$LOGDIR/cloud-stdout.log" 2>&1 || status=1
grep -E "^(--- |\s+--- |PASS|FAIL|ok)|e2e_cloud_test.go" "$LOGDIR/cloud-stdout.log" | grep -v "=== RUN" || true

echo "== Scénario 7 : aucun secret dans les journaux des deux serveurs =="
cat "$LOGDIR"/gateway-secrets.txt "$LOGDIR"/cloud-secrets.txt 2>/dev/null | grep -v '^$' | sort -u >"$LOGDIR/all-secrets.txt" || true
n=$(wc -l <"$LOGDIR/all-secrets.txt" | tr -d ' ')
if [ "$n" -lt 5 ]; then echo "ECHEC : liste de secrets de contrôle incomplète ($n)"; status=1; fi
hits=0
for f in "$LOGDIR"/gateway-stdout.log "$LOGDIR"/gateway-app.log "$LOGDIR"/cloud-stdout.log "$LOGDIR"/cloud-app.log; do
  [ -s "$f" ] || { echo "ECHEC : journal absent ou vide : $(basename "$f")"; status=1; continue; }
  if grep -F -n -f "$LOGDIR/all-secrets.txt" "$f" | cut -c1-80; then hits=1; fi
  echo "  $(basename "$f") : $(wc -c <"$f" | tr -d ' ') octets, $n valeurs de contrôle"
done
[ "$hits" = 0 ] && echo "OK : aucune valeur secrète dans les 4 journaux" || { echo "ECHEC : secret trouvé dans un journal"; status=1; }

if [ "$status" = 0 ]; then echo "== RESULTAT : VERT =="; else echo "== RESULTAT : ROUGE (voir $LOGDIR) =="; KEEP=1; fi
exit "$status"
