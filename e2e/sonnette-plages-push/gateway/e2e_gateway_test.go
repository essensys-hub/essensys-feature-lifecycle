// Côté gateway du test de bout en bout de la Feature sonnette-plages-push-2026-11-008 (#61, tâche 11.1).
//
// Ce fichier est COPIÉ par run.sh dans internal/e2e/ d'une extraction de essensys-server-backend
// (git archive) : il n'est pas compilé dans ce dépôt. Il fait tourner le vrai code de la gateway :
// source d'événements UniFi par WebSocket (StreamSource), DoorbellService, DoorbellSupervisor,
// routes /api/doorbell/* et /api/admin/doorbell/*, agent cloud (NotifyDoorbellRing), file d'actions
// de la table d'échange (GET /api/myactions, ce que lirait l'armoire).
//
// Faux : la console UniFi (serveur WebSocket local), le cloud (serveur HTTPS local), l'armoire (un
// client qui interroge /api/myactions). Aucune armoire réelle, aucun appel réseau sortant.
package e2e

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/essensys-hub/essensys-server-backend/internal/api"
	"github.com/essensys-hub/essensys-server-backend/internal/cloudsync"
	"github.com/essensys-hub/essensys-server-backend/internal/config"
	"github.com/essensys-hub/essensys-server-backend/internal/core"
	"github.com/essensys-hub/essensys-server-backend/internal/data"
	"github.com/essensys-hub/essensys-server-backend/internal/laniam"
	"github.com/essensys-hub/essensys-server-backend/internal/middleware"
	"github.com/essensys-hub/essensys-server-backend/internal/models"
	"github.com/essensys-hub/essensys-server-backend/internal/unifi"
	"github.com/essensys-hub/essensys-server-backend/pkg/protocol"
	"github.com/gorilla/websocket"
)

// Valeurs factices : aucune n'est un secret réel. Elles sont écrites dans secrets.txt pour que
// run.sh vérifie qu'aucune ne se retrouve dans un journal (scénario 7).
const (
	gwID        = "gw-e2e-sonnette"
	gwToken     = "e2e-gateway-token-not-a-real-secret"
	gwEth0      = "00:00:5e:00:53:01" // plage de documentation
	gwEth1      = "00:00:5e:00:53:02"
	unifiAPIKey = "e2e-unifi-api-key-not-a-real-secret"
	camera      = "cam-sonnette-e2e"
)

// Instant fixe de l'essai : mardi 2026-11-03, 10 h 30 à Paris (09 h 30 UTC, heure d'hiver). Dans le passé : le cloud ramène à
// son horloge un « at » postérieur de plus de 5 minutes. grid[1] = mardi,
// le caractère 10 = la case 10 h-11 h.
var t0 = time.Date(2026, 11, 3, 9, 30, 0, 0, time.UTC)

// ---------------------------------------------------------------------------------------------
// Faux cloud (HTTPS local) : enregistre les signalements et répond selon le mode.

type ringReq struct {
	Method  string            `json:"method"`
	Path    string            `json:"path"`
	Headers map[string]string `json:"headers"`
	Body    string            `json:"body"`
	At      time.Time         `json:"-"`
}

type fakeCloud struct {
	srv  *httptest.Server
	mu   sync.Mutex
	reqs []ringReq
	down atomic.Bool // vrai : répond 502
}

func newFakeCloud(t *testing.T) *fakeCloud {
	t.Helper()
	f := &fakeCloud{}
	f.srv = httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		h := map[string]string{}
		for _, k := range []string{"Authorization", "X-Gateway-Id", "X-Gateway-Eth0-Mac", "X-Gateway-Eth1-Mac", "Content-Type"} {
			if v := r.Header.Get(k); v != "" {
				h[k] = v
			}
		}
		f.mu.Lock()
		f.reqs = append(f.reqs, ringReq{Method: r.Method, Path: r.URL.Path, Headers: h, Body: string(raw), At: time.Now()})
		f.mu.Unlock()
		if f.down.Load() {
			w.WriteHeader(http.StatusBadGateway)
			return
		}
		_, _ = w.Write([]byte(`{"status":"accepted","recipients":0}`))
	}))
	t.Cleanup(f.srv.Close)
	return f
}

func (f *fakeCloud) snapshot() []ringReq {
	f.mu.Lock()
	defer f.mu.Unlock()
	return append([]ringReq(nil), f.reqs...)
}

// ---------------------------------------------------------------------------------------------
// Fausse console UniFi : serveur WebSocket (TLS) du flux d'événements.

type fakeUniFi struct {
	srv   *httptest.Server
	conns atomic.Int32
	out   chan string
}

func newFakeUniFi(t *testing.T) *fakeUniFi {
	t.Helper()
	f := &fakeUniFi{out: make(chan string, 16)}
	up := websocket.Upgrader{}
	f.srv = httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/proxy/protect/integration/v1/subscribe/events" || r.Header.Get("X-API-Key") != unifiAPIKey {
			http.NotFound(w, r)
			return
		}
		c, err := up.Upgrade(w, r, nil)
		if err != nil {
			return
		}
		defer c.Close()
		f.conns.Add(1)
		defer f.conns.Add(-1)
		for msg := range f.out {
			if c.WriteMessage(websocket.TextMessage, []byte(msg)) != nil {
				return
			}
		}
	}))
	t.Cleanup(func() { f.srv.CloseClientConnections(); f.srv.Close() })
	return f
}

// ring envoie les messages « add » puis « update » d'un même événement (la console les envoie tous
// deux : le dédoublonnage est du ressort de la gateway).
func (f *fakeUniFi) ring(id string, at time.Time) {
	for _, typ := range []string{"add", "update"} {
		f.out <- fmt.Sprintf(`{"type":%q,"item":{"id":%q,"modelKey":"event","type":"ring","device":%q,"start":%d}}`,
			typ, id, camera, at.UnixMilli())
	}
}

// ---------------------------------------------------------------------------------------------
// Fausse armoire : interroge GET /api/myactions comme le ferait le boîtier et note chaque ordre.

type fakeArmoire struct {
	mu     sync.Mutex
	orders []string // un ordre par action : « indice=valeur » des lumières (indices 605 à 616) non nulles
	times  []time.Time
	stop   chan struct{}
	done   chan struct{}
}

func startArmoire(t *testing.T, h http.Handler) *fakeArmoire {
	a := &fakeArmoire{stop: make(chan struct{}), done: make(chan struct{})}
	go func() {
		defer close(a.done)
		seen := map[string]bool{}
		for {
			select {
			case <-a.stop:
				return
			case <-time.After(25 * time.Millisecond):
			}
			rec := httptest.NewRecorder()
			h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/myactions", nil))
			var resp protocol.ActionsResponse
			if json.Unmarshal(rec.Body.Bytes(), &resp) != nil {
				continue
			}
			a.mu.Lock()
			for _, act := range resp.Actions {
				// Sans acquittement (POST /api/mystatus), la file renvoie les mêmes actions : on dédoublonne par GUID.
				if seen[act.GUID] {
					continue
				}
				seen[act.GUID] = true
				var parts []string
				for _, kv := range act.Params {
					if kv.K >= 605 && kv.K <= 616 && kv.V != "0" {
						parts = append(parts, fmt.Sprintf("%d=%s", kv.K, kv.V))
					}
				}
				a.orders = append(a.orders, strings.Join(parts, "+"))
				a.times = append(a.times, time.Now())
			}
			a.mu.Unlock()
		}
	}()
	t.Cleanup(func() { close(a.stop); <-a.done })
	return a
}

func (a *fakeArmoire) count() int { a.mu.Lock(); defer a.mu.Unlock(); return len(a.orders) }

func (a *fakeArmoire) keys() []string {
	a.mu.Lock()
	defer a.mu.Unlock()
	return append([]string(nil), a.orders...)
}

// ---------------------------------------------------------------------------------------------
// Banc : la gateway câblée comme cmd/server/main.go, à la différence des sources faux.

type rig struct {
	t       *testing.T
	router  http.Handler
	svc     *core.DoorbellService
	cookies map[string]*http.Cookie
	cloud   *fakeCloud
	console *fakeUniFi
	armoire *fakeArmoire
	clock   atomic.Int64 // UnixNano de l'horloge du service
}

func (r *rig) setClock(t time.Time) { r.clock.Store(t.UnixNano()) }

func trustTLS(t *testing.T, certs ...*x509.Certificate) {
	t.Helper()
	pool := x509.NewCertPool()
	for _, c := range certs {
		pool.AddCert(c)
	}
	prev := http.DefaultTransport
	http.DefaultTransport = &http.Transport{TLSClientConfig: &tls.Config{RootCAs: pool, MinVersion: tls.VersionTLS12}}
	t.Cleanup(func() { http.DefaultTransport = prev })
}

func newRig(t *testing.T) *rig {
	t.Helper()
	r := &rig{t: t, cookies: map[string]*http.Cookie{}}
	r.cloud = newFakeCloud(t)
	r.console = newFakeUniFi(t)
	// L'agent cloud utilise http.DefaultTransport : on lui fait faire confiance au certificat du faux cloud.
	trustTLS(t, r.cloud.srv.Certificate())

	store := data.NewMemoryStore() // table d'échange en mémoire : aucune armoire
	names := core.NewLightNameStore(filepath.Join(t.TempDir(), "light-names.json"))
	as := core.NewActionService(store)
	r.svc = core.NewDoorbellService(names, core.ExchangeDoorbellWriter{Actions: as, Store: store})
	r.svc.Phase = 5 * time.Millisecond
	r.setClock(t0)
	r.svc.Now = func() time.Time { return time.Unix(0, r.clock.Load()).UTC() }
	t.Cleanup(r.svc.Close)

	agent := cloudsync.NewAgent(cloudsync.Config{
		Enabled: true, HubURL: r.cloud.srv.URL, GatewayID: gwID, GatewayToken: gwToken,
		Eth0MAC: gwEth0, Eth1MAC: gwEth1,
	}, as, store, nil)
	r.svc.Notifier = agent.NotifyDoorbellRing

	dh := api.NewDoorbellHandler(r.svc, names)
	dh.Cameras = func() ([]unifi.Camera, error) { return []unifi.Camera{{ID: camera, Name: "Sonnette"}}, nil }
	dh.Snapshot = func(string) ([]byte, error) { return []byte("\xff\xd8\xff\xe0"), nil }

	// Même branchement que main.go : source par flux d'événements sur la (fausse) console.
	src := unifi.NewStreamSource(config.UniFiConfig{Enabled: true, BaseURL: r.console.srv.URL, APIKey: unifiAPIKey})
	sup := core.NewDoorbellSupervisor(r.svc, src)
	dh.OnSettingsChanged = sup.Reconfigure
	ctx, cancel := context.WithCancel(context.Background())
	sup.Start(ctx)
	t.Cleanup(func() { cancel(); sup.Stop() })

	h := api.NewHandler(as, core.NewStatusService(store), store, nil, nil, config.ArmoireConfig{})
	sessions := laniam.NewSessionStore(1)
	for i, role := range []string{models.LanRoleAdmin, models.LanRoleUser} {
		sess, err := sessions.CreateSession(&models.LanUser{ID: i + 1, Email: role + "@example.org", Role: role})
		if err != nil {
			t.Fatal(err)
		}
		r.cookies[role] = &http.Cookie{Name: middleware.LanSessionCookie, Value: sess.ID}
	}
	r.router = api.NewRouter(api.RouterConfig{Handler: h, DoorbellHandler: dh, LanSessionStore: sessions, LanIAMEnabled: true, Store: store})
	r.armoire = startArmoire(t, r.router)
	return r
}

func (r *rig) do(method, path, body, role string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(method, path, strings.NewReader(body))
	if c, ok := r.cookies[role]; ok {
		req.AddCookie(c)
	}
	rec := httptest.NewRecorder()
	r.router.ServeHTTP(rec, req)
	return rec
}

func (r *rig) saveSettings(scheduleJSON string) {
	r.t.Helper()
	body := `{"enabled":true,"camera_id":"` + camera + `","lights":["salon"],"blinks":3,"schedule":` + scheduleJSON + `}`
	if rec := r.do(http.MethodPut, "/api/admin/doorbell/settings", body, models.LanRoleAdmin); rec.Code != http.StatusOK {
		r.t.Fatalf("PUT settings : %d %s", rec.Code, rec.Body.String())
	}
}

func (r *rig) status() map[string]any {
	r.t.Helper()
	rec := r.do(http.MethodGet, "/api/doorbell/status", "", models.LanRoleUser)
	if rec.Code != http.StatusOK {
		r.t.Fatalf("GET status : %d %s", rec.Code, rec.Body.String())
	}
	var m map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &m); err != nil {
		r.t.Fatal(err)
	}
	return m
}

// waitReady attend que la console ait une connexion d'écoute et que le service la déclare disponible.
func (r *rig) waitReady() {
	r.t.Helper()
	waitFor(r.t, "écoute UniFi établie", 10*time.Second, func() bool {
		return r.console.conns.Load() == 1 && r.status()["available"] == true
	})
}

func waitFor(t *testing.T, what string, d time.Duration, cond func() bool) {
	t.Helper()
	end := time.Now().Add(d)
	for time.Now().Before(end) {
		if cond() {
			return
		}
		time.Sleep(5 * time.Millisecond)
	}
	t.Fatalf("délai dépassé : %s", what)
}

// settle laisse passer le temps d'une éventuelle réaction (négatifs) et attend les tâches de fond.
func (r *rig) settle() {
	time.Sleep(300 * time.Millisecond)
	r.svc.WaitIdle()
}

func gridWith(tuesday10 byte, others byte) string {
	rows := make([]string, 7)
	for d := range rows {
		b := []byte(strings.Repeat(string(others), 24))
		if d == 1 {
			b[10] = tuesday10
		}
		rows[d] = `"` + string(b) + `"`
	}
	return "[" + strings.Join(rows, ",") + "]"
}

func schedule(mode, grid string) string {
	return `{"mode":"` + mode + `","timezone":"Europe/Paris","grid":` + grid + `}`
}

// Ordres attendus pour la lumière « salon » (606=128 : extinction, 612=128 : allumage), 3
// clignotements : éteint/allumé trois fois, le dernier ordre allume.
var salonSequence = []string{"606=128", "612=128", "606=128", "612=128", "606=128", "612=128"}

// ---------------------------------------------------------------------------------------------
// Scénarios

var (
	logBuf    syncBuffer
	artifacts struct {
		mu    sync.Mutex
		rings []ringReq
	}
)

type syncBuffer struct {
	mu sync.Mutex
	b  strings.Builder
}

func (s *syncBuffer) Write(p []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.b.Write(p)
}
func (s *syncBuffer) String() string { s.mu.Lock(); defer s.mu.Unlock(); return s.b.String() }

func TestMain(m *testing.M) {
	log.SetOutput(io.MultiWriter(&logBuf, os.Stderr))
	code := m.Run()
	if dir := os.Getenv("E2E_LOGDIR"); dir != "" {
		_ = os.WriteFile(filepath.Join(dir, "gateway-app.log"), []byte(logBuf.String()), 0o644)
		_ = os.WriteFile(filepath.Join(dir, "gateway-secrets.txt"), []byte(gwToken+"\n"+unifiAPIKey+"\n"), 0o644)
	}
	if dir := os.Getenv("E2E_ARTIFACTS"); dir != "" {
		artifacts.mu.Lock()
		raw, _ := json.MarshalIndent(artifacts.rings, "", "  ")
		artifacts.mu.Unlock()
		_ = os.WriteFile(filepath.Join(dir, "ring-requests.json"), raw, 0o644)
	}
	os.Exit(code)
}

// Scénarios 1 et 3 (côté gateway) : appui dans la plage, avec « add » et « update » du même événement.
func TestE2E_Gateway_S1_AppuiDansLaPlage(t *testing.T) {
	r := newRig(t)
	// Plage personnalisée : seule la case de l'essai (mardi 10 h) est active, les autres inactives.
	r.saveSettings(schedule("custom", gridWith('1', '0')))
	r.waitReady()
	if !r.status()["in_window"].(bool) {
		t.Fatal("in_window doit être vrai à l'instant de l'essai")
	}

	r.console.ring("evt-e2e-in-1", t0)
	waitFor(t, "séquence de clignotement complète", 10*time.Second, func() bool { return r.armoire.count() >= len(salonSequence) })
	r.settle()

	if got := r.armoire.keys(); fmt.Sprint(got) != fmt.Sprint(salonSequence) {
		t.Fatalf("ordres vus par l'armoire factice : %v, attendu %v", got, salonSequence)
	}
	reqs := r.cloud.snapshot()
	if len(reqs) != 1 {
		t.Fatalf("1 seul signalement au cloud attendu (add + update dédoublonnés), %d reçus", len(reqs))
	}
	q := reqs[0]
	if q.Method != http.MethodPost || q.Path != "/api/gateway/doorbell/ring" {
		t.Fatalf("requête : %s %s", q.Method, q.Path)
	}
	if q.Headers["Authorization"] != "Bearer "+gwToken || q.Headers["X-Gateway-Id"] != gwID || q.Headers["X-Gateway-Eth0-Mac"] != gwEth0 {
		t.Fatalf("authentification de la gateway : %v", q.Headers)
	}
	var body map[string]string
	if err := json.Unmarshal([]byte(q.Body), &body); err != nil {
		t.Fatal(err)
	}
	if body["ring_id"] != "evt-e2e-in-1" || body["at"] != "2026-11-03T09:30:00.000Z" || len(body) != 2 {
		t.Fatalf("corps du signalement : %s", q.Body)
	}
	st := r.status()
	if st["ringing"] != true || st["in_window"] != true {
		t.Fatalf("état : %v", st)
	}
	artifacts.mu.Lock()
	artifacts.rings = append(artifacts.rings, q)
	artifacts.mu.Unlock()
	t.Logf("S1 gateway : ordres %v, 1 POST %s ring_id=%s at=%s", r.armoire.keys(), q.Path, body["ring_id"], body["at"])
}

// Scénario 2 : appui hors plage, deux variantes (case inactive, grille « jamais »).
func TestE2E_Gateway_S2_AppuiHorsPlage(t *testing.T) {
	cases := []struct{ name, sched string }{
		{"case inactive", schedule("custom", gridWith('0', '1'))},
		{"grille jamais", schedule("custom", gridWith('0', '0'))},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			r := newRig(t)
			r.saveSettings(c.sched)
			r.waitReady()
			if r.status()["in_window"] != false {
				t.Fatalf("in_window doit être faux : %v", r.status())
			}
			r.console.ring("evt-e2e-out-"+strings.ReplaceAll(c.name, " ", "-"), t0)
			waitFor(t, "ringing=true", 5*time.Second, func() bool { return r.status()["ringing"] == true })
			r.settle()
			if n := r.armoire.count(); n != 0 {
				t.Fatalf("aucun clignotement attendu, %d ordres : %v", n, r.armoire.keys())
			}
			if n := len(r.cloud.snapshot()); n != 0 {
				t.Fatalf("aucun appel au cloud attendu, %d reçus", n)
			}
			st := r.status()
			if st["ringing"] != true || st["in_window"] != false {
				t.Fatalf("GET /api/doorbell/status : %v", st)
			}
			t.Logf("S2 gateway (%s) : 0 ordre, 0 appel cloud, status ringing=true in_window=false", c.name)
		})
	}
}

// Scénario 4 : cloud injoignable (502). Le clignotement n'attend pas ; 3 tentatives, puis abandon.
func TestE2E_Gateway_S4_CloudInjoignable(t *testing.T) {
	r := newRig(t)
	r.cloud.down.Store(true)
	r.saveSettings(schedule("always", gridWith('1', '1')))
	r.waitReady()

	start := time.Now()
	r.console.ring("evt-e2e-down-1", t0)
	waitFor(t, "séquence de clignotement", 10*time.Second, func() bool { return r.armoire.count() >= len(salonSequence) })
	seqDone := time.Since(start)
	waitFor(t, "3 tentatives", 20*time.Second, func() bool { return len(r.cloud.snapshot()) >= 3 })
	r.settle() // attend la fin de NotifyDoorbellRing (abandon)

	reqs := r.cloud.snapshot()
	if len(reqs) != 3 {
		t.Fatalf("3 tentatives exactement attendues, %d", len(reqs))
	}
	if fmt.Sprint(r.armoire.keys()) != fmt.Sprint(salonSequence) {
		t.Fatalf("ordres : %v", r.armoire.keys())
	}
	// Le clignotement a fini bien avant la 2e tentative (attente de 1 s) : il n'a pas été retardé.
	if !r.armoire.times[len(salonSequence)-1].Before(reqs[1].At) {
		t.Fatal("le clignotement doit être terminé avant la 2e tentative")
	}
	if d := reqs[1].At.Sub(reqs[0].At); d < 900*time.Millisecond || d > 2*time.Second {
		t.Fatalf("attente avant la 2e tentative : %s (attendu ~1 s)", d)
	}
	if d := reqs[2].At.Sub(reqs[1].At); d < 2900*time.Millisecond || d > 5*time.Second {
		t.Fatalf("attente avant la 3e tentative : %s (attendu ~3 s)", d)
	}
	if !strings.Contains(logBuf.String(), "signalement au cloud abandonné après 3 tentatives") {
		t.Fatal("l'abandon doit être journalisé")
	}
	t.Logf("S4 gateway : séquence complète en %s, 3 tentatives (+%s, +%s), abandon journalisé",
		seqDone.Round(time.Millisecond), reqs[1].At.Sub(reqs[0].At).Round(10*time.Millisecond), reqs[2].At.Sub(reqs[1].At).Round(10*time.Millisecond))
}

// Scénario 7 (côté gateway) : ni jeton, ni clé d'API UniFi, ni adresse des serveurs factices dans les journaux.
func TestE2E_Gateway_S7_AucunSecretDansLesJournaux(t *testing.T) {
	// Joue après les autres (ordre des fonctions du fichier) : le tampon contient tous leurs journaux.
	logs := logBuf.String()
	if logs == "" {
		t.Fatal("aucun journal capturé")
	}
	for _, s := range []string{gwToken, unifiAPIKey, gwEth0, gwEth1, "127.0.0.1"} {
		if strings.Contains(logs, s) {
			t.Fatalf("le journal de la gateway contient %q", s)
		}
	}
	t.Logf("S7 gateway : %d octets de journal, aucun jeton, clé, MAC ni adresse", len(logs))
}
