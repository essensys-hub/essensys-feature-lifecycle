// Côté cloud du test de bout en bout de la Feature sonnette-plages-push-2026-11-008 (#61, tâche 11.1).
//
// Ce fichier est COPIÉ par run.sh dans internal/e2e/ d'une extraction de essensys-user-portal-backend
// (git archive) : il n'est pas compilé dans ce dépôt. Il fait tourner le vrai cloud : routeur complet,
// migrations 001 à 022 rejouées sur un vrai PostgreSQL local (socket Unix, aucune écoute réseau),
// authentification de la gateway, enregistrement des appareils, envoi push.
//
// Faux : FCM et APNs (serveurs httptest locaux). L'appui n'est pas fabriqué : le test rejoue la requête
// réellement émise par la gateway lors de la phase gateway (E2E_ARTIFACTS/ring-requests.json).
package e2e

import (
	"bytes"
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/essensys-hub/essensys-user-portal-backend/internal/api"
	"github.com/essensys-hub/essensys-user-portal-backend/internal/config"
	"github.com/essensys-hub/essensys-user-portal-backend/internal/data"
	"github.com/essensys-hub/essensys-user-portal-backend/internal/domain"
	"github.com/essensys-hub/essensys-user-portal-backend/internal/middleware"
	"github.com/essensys-hub/essensys-user-portal-backend/internal/push"
	chimw "github.com/go-chi/chi/v5/middleware"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

// Valeurs factices (aucune n'est un secret réel), écrites dans secrets.txt pour le contrôle des journaux.
const (
	jwtSecret = "e2e-jwt-secret-not-real-0123456789abcdef"
	gwToken   = "e2e-gateway-token-not-a-real-secret" // même valeur que la phase gateway
	gwID      = "gw-e2e-sonnette"
	gwEth0    = "00:00:5e:00:53:01"
	gwEth1    = "00:00:5e:00:53:02"
	otherGW   = "gw-e2e-autre"

	androidTok  = "e2e-android-device-token-aaaaaaaaaaaaaaaa"
	iosTok      = "e2e-ios-device-token-bbbbbbbbbbbbbbbbbbbb"
	androidTok2 = "e2e-android-device-token-cccccccccccccccc"
	iosTok2     = "e2e-ios-device-token-dddddddddddddddddd"
	androidTok3 = "e2e-android-device-token-eeeeeeeeeeeeeeee"
)

var (
	logBuf  syncBuffer
	secrets = []string{jwtSecret, gwToken, androidTok, iosTok, androidTok2, iosTok2, androidTok3}
	p8PEM   string
)

type syncBuffer struct {
	mu sync.Mutex
	b  bytes.Buffer
}

func (s *syncBuffer) Write(p []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.b.Write(p)
}
func (s *syncBuffer) String() string { s.mu.Lock(); defer s.mu.Unlock(); return s.b.String() }

func TestMain(m *testing.M) {
	// Tous les journaux (log standard et journal d'accès de chi) vont dans le tampon, puis dans un fichier.
	log.SetOutput(io.MultiWriter(&logBuf, os.Stderr))
	chimw.DefaultLogger = chimw.RequestLogger(&chimw.DefaultLogFormatter{Logger: log.New(io.MultiWriter(&logBuf, os.Stderr), "", log.LstdFlags)})
	key, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	der, _ := x509.MarshalPKCS8PrivateKey(key)
	p8PEM = string(pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: der}))
	code := m.Run()
	if dir := os.Getenv("E2E_LOGDIR"); dir != "" {
		_ = os.WriteFile(filepath.Join(dir, "cloud-app.log"), []byte(logBuf.String()), 0o644)
		all := append(append([]string(nil), secrets...), base64Body(p8PEM))
		_ = os.WriteFile(filepath.Join(dir, "cloud-secrets.txt"), []byte(strings.Join(all, "\n")+"\n"), 0o644)
	}
	os.Exit(code)
}

// base64Body renvoie le corps base64 (première ligne) d'une clé PEM, pour la chercher dans les journaux.
func base64Body(p string) string {
	lines := strings.Split(strings.TrimSpace(p), "\n")
	return strings.TrimSpace(lines[1])
}

// ---------------------------------------------------------------------------------------------
// Base PostgreSQL locale

var (
	dbOnce sync.Once
	db     *sqlx.DB
	dbErr  error
)

func openDB(t *testing.T) *sqlx.DB {
	t.Helper()
	dbOnce.Do(func() {
		host := os.Getenv("E2E_PG_HOST") // dossier de la socket Unix
		if host == "" {
			dbErr = fmt.Errorf("E2E_PG_HOST non défini : lancer le test par run.sh (PostgreSQL local requis)")
			return
		}
		dsn := fmt.Sprintf("host=%s port=%s user=%s dbname=%s sslmode=disable",
			host, envOr("E2E_PG_PORT", "5432"), envOr("E2E_PG_USER", "e2e"), envOr("E2E_PG_DB", "e2e"))
		var err error
		if db, err = sqlx.Connect("postgres", dsn); err != nil {
			dbErr = fmt.Errorf("connexion PostgreSQL : %w", err)
			return
		}
		// Base de production : la table users existe déjà avant les migrations (010 la modifie). On la
		// crée donc d'abord, puis on rejoue les migrations en ordre comme cmd/server/main.go.
		if err := data.NewUserStore(db).EnsureTableExists(); err != nil {
			dbErr = fmt.Errorf("table users : %w", err)
			return
		}
		paths, _ := filepath.Glob("../../migrations/*.sql")
		sort.Strings(paths)
		if len(paths) < 22 {
			dbErr = fmt.Errorf("migrations introuvables (%d)", len(paths))
			return
		}
		store := data.NewPortalStore(db)
		for _, p := range paths {
			if err := store.RunMigrations(p); err != nil {
				dbErr = fmt.Errorf("migrations : %w", err)
				return
			}
			// La migration 011 (antérieure à la Feature) échoue sur une table machines vide (setval(0)) :
			// la base de production a des armoires. On en pose une, comme la production.
			if strings.HasPrefix(filepath.Base(p), "003_") {
				if _, err := db.Exec(`INSERT INTO machines (hashed_pkey, client_id) VALUES ('e2e-machine', '3') ON CONFLICT DO NOTHING`); err != nil {
					dbErr = fmt.Errorf("armoire de test : %w", err)
					return
				}
			}
		}
		if err := data.NewUserStore(db).EnsureTableExists(); err != nil { // main.go le rejoue après les migrations
			dbErr = fmt.Errorf("table users : %w", err)
		}
	})
	if dbErr != nil {
		t.Fatal(dbErr)
	}
	return db
}

func envOr(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

// reset vide les tables que les scénarios remplissent.
func reset(t *testing.T) *sqlx.DB {
	t.Helper()
	d := openDB(t)
	if _, err := d.Exec(`TRUNCATE push_devices, doorbell_rings, gateway_sessions, users RESTART IDENTITY CASCADE`); err != nil {
		t.Fatal(err)
	}
	return d
}

// ---------------------------------------------------------------------------------------------
// Faux fournisseurs

type call struct {
	Path   string
	Header http.Header
	Body   map[string]any
}

type fakeProvider struct {
	mu    sync.Mutex
	calls []call
	srv   *httptest.Server
}

func newFakeProvider(t *testing.T, tls bool) *fakeProvider {
	t.Helper()
	f := &fakeProvider{}
	h := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var m map[string]any
		_ = json.NewDecoder(r.Body).Decode(&m)
		f.mu.Lock()
		f.calls = append(f.calls, call{Path: r.URL.Path, Header: r.Header.Clone(), Body: m})
		f.mu.Unlock()
		if !tls {
			_, _ = io.WriteString(w, `{}`)
		}
	})
	if tls {
		f.srv = httptest.NewTLSServer(h)
	} else {
		f.srv = httptest.NewServer(h)
	}
	t.Cleanup(f.srv.Close)
	return f
}

func (f *fakeProvider) all() []call {
	f.mu.Lock()
	defer f.mu.Unlock()
	return append([]call(nil), f.calls...)
}

func dispatcher(t *testing.T, fcm, apns *fakeProvider) *push.Dispatcher {
	t.Helper()
	s, err := push.NewAPNsSender(push.APNsConfig{KeyP8: p8PEM, KeyID: "KEYID", TeamID: "TEAMID", BundleID: "essensys.essensys-iphone"})
	if err != nil {
		t.Fatal(err)
	}
	return &push.Dispatcher{
		Android: push.NewFCMSenderWithClient(fcm.srv.URL, "demo-project", fcm.srv.Client()),
		IOS:     s.WithEndpoint(apns.srv.URL, apns.srv.Client()),
	}
}

// ---------------------------------------------------------------------------------------------
// Banc cloud : routeur complet sur la vraie base ; un routeur neuf par scénario (limiteur d'appuis neuf).

type env struct {
	t       *testing.T
	d       *sqlx.DB
	handler http.Handler
	fcm     *fakeProvider
	apns    *fakeProvider
	jwts    map[string]string
}

func newEnv(t *testing.T) *env {
	t.Helper()
	t.Setenv("NEW_RELIC_ENABLED", "false")
	t.Setenv("JWT_SECRET", jwtSecret)
	d := reset(t)
	e := &env{t: t, d: d, fcm: newFakeProvider(t, false), apns: newFakeProvider(t, true), jwts: map[string]string{}}
	cfg := config.Config{ConsolidatedMode: true, ExchangeStaleTTL: 120 * time.Second, CORSOrigin: "https://mon.essensys.fr", JWTSecret: jwtSecret}
	e.handler = api.NewRouter(data.NewPortalStore(d), data.NewUserStore(d), nil, data.NewAdminInventoryStore(d), nil, nil, nil, nil, nil, cfg,
		api.WithPush(dispatcher(t, e.fcm, e.apns)))
	return e
}

func (e *env) req(method, path, body string, hdr map[string]string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(method, path, strings.NewReader(body))
	for k, v := range hdr {
		req.Header.Set(k, v)
	}
	rec := httptest.NewRecorder()
	e.handler.ServeHTTP(rec, req)
	return rec
}

// user crée un utilisateur (lié à gateway si non vide) et mémorise son JWT.
func (e *env) user(email, gateway string) {
	e.t.Helper()
	us := data.NewUserStore(e.d)
	u := &domain.User{Email: email, PasswordHash: "x", Role: domain.RoleUser, Provider: domain.ProviderEmail, CreatedAt: time.Now(), LastLogin: time.Now()}
	if err := us.CreateUser(u); err != nil {
		e.t.Fatal(err)
	}
	if gateway != "" {
		m := 3
		if err := us.UpdateUserLinks(u.ID, &m, &gateway, nil); err != nil {
			e.t.Fatal(err)
		}
	}
	tok, err := middleware.GenerateJWT(email, domain.RoleUser, time.Now().Add(time.Hour))
	if err != nil {
		e.t.Fatal(err)
	}
	e.jwts[email] = tok
	secrets = append(secrets, tok)
}

func (e *env) auth(email string) map[string]string {
	return map[string]string{"Authorization": "Bearer " + e.jwts[email]}
}

// device enregistre un appareil par la vraie route PUT /api/portal/push/devices.
func (e *env) device(email, platform, token string, notify bool) {
	e.t.Helper()
	body := fmt.Sprintf(`{"platform":%q,"token":%q,"app_version":"2.3.0","doorbell_notify":%v}`, platform, token, notify)
	rec := e.req(http.MethodPut, "/api/portal/push/devices", body, e.auth(email))
	if rec.Code != http.StatusOK || strings.Contains(rec.Body.String(), token) {
		e.t.Fatalf("PUT push/devices : %d %s", rec.Code, rec.Body.String())
	}
}

// gateway enregistre la session de la gateway (jeton, MAC) comme le fait la liaison réelle.
func (e *env) gateway(id string) {
	e.t.Helper()
	err := data.NewPortalStore(e.d).RegisterGatewaySession(context.Background(), data.GatewayRegistration{GatewayID: id, Token: gwToken, MachineID: 3, Eth0MAC: gwEth0, Eth1MAC: gwEth1})
	if err != nil {
		e.t.Fatal(err)
	}
}

func gwHeaders(id string) map[string]string {
	return map[string]string{"Authorization": "Bearer " + gwToken, "X-Gateway-ID": id, "X-Gateway-Eth0-MAC": gwEth0, "X-Gateway-Eth1-MAC": gwEth1, "Content-Type": "application/json"}
}

func (e *env) ring(gateway, body string) (int, string, int) {
	rec := e.req(http.MethodPost, "/api/gateway/doorbell/ring", body, gwHeaders(gateway))
	var out struct {
		Status     string `json:"status"`
		Recipients int    `json:"recipients"`
	}
	_ = json.Unmarshal(rec.Body.Bytes(), &out)
	return rec.Code, out.Status, out.Recipients
}

// capturedRing lit la requête réellement émise par la gateway.
func capturedRing(t *testing.T) (gateway, body string) {
	t.Helper()
	dir := os.Getenv("E2E_ARTIFACTS")
	raw, err := os.ReadFile(filepath.Join(dir, "ring-requests.json"))
	if err != nil {
		t.Fatalf("requête de la gateway introuvable (%v) : lancer d'abord la phase gateway (run.sh)", err)
	}
	var reqs []struct {
		Path    string            `json:"path"`
		Headers map[string]string `json:"headers"`
		Body    string            `json:"body"`
	}
	if err := json.Unmarshal(raw, &reqs); err != nil || len(reqs) == 0 {
		t.Fatalf("ring-requests.json illisible ou vide : %v", err)
	}
	r := reqs[0]
	if r.Path != "/api/gateway/doorbell/ring" || r.Headers["Authorization"] != "Bearer "+gwToken || r.Headers["X-Gateway-Eth0-Mac"] != gwEth0 {
		t.Fatalf("la requête de la gateway ne correspond pas aux identifiants du banc : %v", r.Headers)
	}
	return r.Headers["X-Gateway-Id"], r.Body
}

func tokensOf(f *fakeProvider, platform string) []string {
	var out []string
	for _, c := range f.all() {
		if platform == "ios" {
			out = append(out, strings.TrimPrefix(c.Path, "/3/device/"))
		} else if m, ok := c.Body["message"].(map[string]any); ok {
			out = append(out, m["token"].(string))
		}
	}
	return out
}

// ---------------------------------------------------------------------------------------------
// Scénarios

// Scénarios 1 et 3 (côté cloud) : la requête réelle de la gateway notifie Android et iPhone, une seule fois.
func TestE2E_Cloud_S1_S3_NotificationsEtDedoublonnage(t *testing.T) {
	e := newEnv(t)
	e.gateway(gwID)
	e.user("a@example.org", gwID)
	e.device("a@example.org", "android", androidTok, true)
	e.device("a@example.org", "ios", iosTok, true)

	gw, body := capturedRing(t)
	var parsed map[string]string
	_ = json.Unmarshal([]byte(body), &parsed)
	ringID, at := parsed["ring_id"], parsed["at"]

	code, st, n := e.ring(gw, body)
	if code != 200 || st != "accepted" || n != 2 {
		t.Fatalf("POST /api/gateway/doorbell/ring : %d %q recipients=%d", code, st, n)
	}
	fc, ac := e.fcm.all(), e.apns.all()
	if len(fc) != 1 || len(ac) != 1 {
		t.Fatalf("1 notification FCM et 1 APNs attendues : fcm=%d apns=%d", len(fc), len(ac))
	}
	wantAt, _ := time.Parse(time.RFC3339Nano, at)
	sameInstant := func(s any) bool {
		g, err := time.Parse(time.RFC3339Nano, fmt.Sprint(s))
		return err == nil && g.Equal(wantAt)
	}

	// FCM
	m := fc[0].Body["message"].(map[string]any)
	notif, dd, andr := m["notification"].(map[string]any), m["data"].(map[string]any), m["android"].(map[string]any)
	an := andr["notification"].(map[string]any)
	if fc[0].Path != "/v1/projects/demo-project/messages:send" || m["token"] != androidTok ||
		notif["title"] != "Quelqu'un sonne" || dd["type"] != "doorbell" || dd["ring_id"] != ringID || !sameInstant(dd["at"]) ||
		an["tag"] != ringID || an["channel_id"] != "doorbell" || andr["priority"] != "HIGH" {
		t.Fatalf("corps FCM inattendu : %v", m)
	}
	// APNs
	a := ac[0]
	alert := a.Body["aps"].(map[string]any)["alert"].(map[string]any)
	if a.Path != "/3/device/"+iosTok || alert["title"] != "Quelqu'un sonne" || a.Body["type"] != "doorbell" ||
		a.Body["ring_id"] != ringID || !sameInstant(a.Body["at"]) ||
		a.Header.Get("apns-collapse-id") != ringID || a.Header.Get("apns-topic") != "essensys.essensys-iphone" ||
		a.Header.Get("apns-push-type") != "alert" || a.Header.Get("apns-priority") != "10" ||
		!strings.HasPrefix(a.Header.Get("authorization"), "bearer ") {
		t.Fatalf("requête APNs inattendue : %v %v %v", a.Path, a.Header, a.Body)
	}
	t.Logf("S1 cloud : accepted recipients=2 ; FCM titre=%q ring_id=%s tag=%s ; APNs collapse-id=%s", notif["title"], dd["ring_id"], an["tag"], a.Header.Get("apns-collapse-id"))

	// Scénario 3 : le même ring_id renvoyé (retentative de la gateway) ne notifie plus.
	code, st, n = e.ring(gw, body)
	if code != 200 || st != "accepted" || n != 0 {
		t.Fatalf("doublon : %d %q recipients=%d", code, st, n)
	}
	var rows int
	_ = e.d.Get(&rows, `SELECT COUNT(*) FROM doorbell_rings WHERE gateway_id = $1 AND ring_id = $2`, gwID, ringID)
	if len(e.fcm.all()) != 1 || len(e.apns.all()) != 1 || rows != 1 {
		t.Fatalf("une seule notification attendue : fcm=%d apns=%d lignes doorbell_rings=%d", len(e.fcm.all()), len(e.apns.all()), rows)
	}
	t.Logf("S3 cloud : 2e envoi du même ring_id -> 200 recipients=0, FCM=1 APNs=1 (inchangés), 1 ligne doorbell_rings")
}

// Scénario 5 : seuls les appareils des utilisateurs liés à la gateway appelante, avec doorbell_notify, sont notifiés.
func TestE2E_Cloud_S5_Destinataires(t *testing.T) {
	// (i) aucun destinataire éligible : préférence désactivée, autre gateway, aucune gateway.
	e := newEnv(t)
	e.gateway(gwID)
	e.user("off@example.org", gwID)
	e.device("off@example.org", "android", androidTok2, false)
	e.user("autre@example.org", otherGW)
	e.device("autre@example.org", "ios", iosTok2, true)
	e.user("sans@example.org", "")
	e.device("sans@example.org", "android", androidTok3, true)
	code, st, n := e.ring(gwID, `{"ring_id":"ring-e2e-5a","at":"2026-11-10T09:30:00.000Z"}`)
	if code != 200 || st != "accepted" || n != 0 || len(e.fcm.all())+len(e.apns.all()) != 0 {
		t.Fatalf("(i) %d %q recipients=%d fcm=%d apns=%d", code, st, n, len(e.fcm.all()), len(e.apns.all()))
	}
	t.Logf("S5 cloud (i) : doorbell_notify=false / autre gateway / non lié -> recipients=0, aucun appel fournisseur")

	// (ii) avec un utilisateur éligible en plus : seul son appareil est notifié (nouveau routeur, nouveau limiteur).
	e2 := newEnv(t)
	e2.gateway(gwID)
	e2.user("a@example.org", gwID)
	e2.device("a@example.org", "android", androidTok, true)
	e2.user("off@example.org", gwID)
	e2.device("off@example.org", "ios", iosTok2, false)
	e2.user("autre@example.org", otherGW)
	e2.device("autre@example.org", "android", androidTok3, true)
	code, st, n = e2.ring(gwID, `{"ring_id":"ring-e2e-5b","at":"2026-11-10T09:30:00.000Z"}`)
	got := append(tokensOf(e2.fcm, "android"), tokensOf(e2.apns, "ios")...)
	if code != 200 || n != 1 || len(got) != 1 || got[0] != androidTok {
		t.Fatalf("(ii) %d %q recipients=%d jetons notifiés=%v", code, st, n, got)
	}
	t.Logf("S5 cloud (ii) : un seul appareil notifié (celui de l'utilisateur lié avec doorbell_notify=true)")
}

// Scénario 6 : gateway_state dans GET /api/portal/session.
func TestE2E_Cloud_S6_GatewayState(t *testing.T) {
	e := newEnv(t)
	state := func(email string) string {
		rec := e.req(http.MethodGet, "/api/portal/session", "", e.auth(email))
		if rec.Code != 200 {
			t.Fatalf("GET /api/portal/session : %d %s", rec.Code, rec.Body.String())
		}
		var out struct {
			GatewayState string `json:"gateway_state"`
		}
		_ = json.Unmarshal(rec.Body.Bytes(), &out)
		return out.GatewayState
	}
	e.gateway(gwID)
	e.user("none@example.org", "")
	e.user("on@example.org", gwID)

	if s := state("none@example.org"); s != "none" {
		t.Fatalf("aucune gateway liée : %q", s)
	}
	// Battement réel : POST /api/gateway/heartbeat (jeton + MAC), puis en ligne.
	if rec := e.req(http.MethodPost, "/api/gateway/heartbeat", "{}", gwHeaders(gwID)); rec.Code/100 != 2 {
		t.Fatalf("heartbeat : %d %s", rec.Code, rec.Body.String())
	}
	if s := state("on@example.org"); s != "online" {
		t.Fatalf("gateway qui bat : %q", s)
	}
	// Plus de battement depuis plus de 2 minutes : hors ligne.
	if _, err := e.d.Exec(`UPDATE gateway_sessions SET last_seen = NOW() - INTERVAL '5 minutes' WHERE gateway_id = $1`, gwID); err != nil {
		t.Fatal(err)
	}
	if s := state("on@example.org"); s != "offline" {
		t.Fatalf("gateway silencieuse : %q", s)
	}
	t.Logf("S6 cloud : none / online (après heartbeat) / offline (silence 5 min)")
}

// Migration 022 : rejouable à chaque démarrage (déjà jouée par openDB) et tables présentes.
func TestE2E_Cloud_Migration022Rejouable(t *testing.T) {
	d := openDB(t)
	if err := data.NewPortalStore(d).RunMigrations("../../migrations/022_push_devices.sql"); err != nil {
		t.Fatalf("rejeu de 022 : %v", err)
	}
	for _, tbl := range []string{"push_devices", "doorbell_rings"} {
		var n int
		if err := d.Get(&n, `SELECT COUNT(*) FROM information_schema.tables WHERE table_name = $1`, tbl); err != nil || n != 1 {
			t.Fatalf("table %s absente (%v)", tbl, err)
		}
	}
	t.Logf("022 : push_devices et doorbell_rings présentes, rejeu sans erreur")
}

// Scénario 7 (côté cloud) : aucun secret dans les journaux du cloud (log standard + journal d'accès).
func TestE2E_Cloud_S7_AucunSecretDansLesJournaux(t *testing.T) {
	logs := logBuf.String()
	if logs == "" {
		t.Fatal("aucun journal capturé")
	}
	for _, s := range append(append([]string(nil), secrets...), base64Body(p8PEM), "PRIVATE KEY") {
		if strings.Contains(logs, s) {
			t.Fatalf("le journal du cloud contient une valeur secrète : %.12s…", s)
		}
	}
	t.Logf("S7 cloud : %d octets de journal, aucun jeton d'appareil, JWT, jeton gateway ni clé APNs", len(logs))
}
