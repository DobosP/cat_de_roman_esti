package httpapi

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/json"
	"flag"
	"io"
	"net/http"
	"net/http/cookiejar"
	"net/http/httptest"
	"net/url"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/accounts"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/shared-go/authcore"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

var arcadeDatabase = flag.String("arcade.database", "", "explicit disposable native combined account/game database")

type arcadeFixture struct {
	game *Server
	pool *pgxpool.Pool
	web  *httptest.Server
	data *content.Content
}

func newArcadeFixture(t *testing.T) *arcadeFixture {
	t.Helper()
	if *arcadeDatabase == "" {
		t.Skip("explicit disposable -arcade.database required")
	}
	ctx := context.Background()
	base, err := pgxpool.New(ctx, *arcadeDatabase)
	if err != nil {
		t.Fatal("fixture database configuration invalid")
	}
	schema := "arcade_test_" + strings.ToLower(rand.Text())
	quoted := pgx.Identifier{schema}.Sanitize()
	if _, err = base.Exec(ctx, `CREATE SCHEMA `+quoted); err != nil {
		t.Fatal("fixture database unavailable")
	}
	cfg, err := pgxpool.ParseConfig(*arcadeDatabase)
	if err != nil {
		t.Fatal("fixture configuration invalid")
	}
	cfg.ConnConfig.RuntimeParams["search_path"] = schema
	cfg.MaxConns = 6
	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		pool.Close()
		_, _ = base.Exec(context.Background(), `DROP SCHEMA `+quoted+` CASCADE`)
		base.Close()
	})
	if err = accounts.Migrate(ctx, pool); err != nil {
		t.Fatal("native fixture migration failed")
	}
	data, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	game := New(data)
	game.allowedHosts = []string{"127.0.0.1"}
	web := httptest.NewUnstartedServer(game)
	public := "http://" + web.Listener.Addr().String()
	auth, err := authcore.New(authcore.Config{PublicURL: public}, accounts.NewStore(pool))
	if err != nil {
		t.Fatal(err)
	}
	service := accounts.New(pool, accounts.Config{Now: func() time.Time { return time.Date(2026, 10, 4, 12, 0, 0, 0, time.UTC) }, CategoryAllowed: game.KnownCategory}, auth)
	game.EnableAccounts(service, auth, public)
	web.Start()
	t.Cleanup(web.Close)
	return &arcadeFixture{game, pool, web, data}
}
func (f *arcadeFixture) client() *http.Client {
	jar, _ := cookiejar.New(nil)
	return &http.Client{Jar: jar, Timeout: 20 * time.Second}
}
func (f *arcadeFixture) request(t *testing.T, c *http.Client, method, path string, body any, csrf bool) (int, map[string]any, http.Header) {
	t.Helper()
	var raw []byte
	if body != nil {
		raw, _ = json.Marshal(body)
	}
	req, err := http.NewRequest(method, f.web.URL+path, bytes.NewReader(raw))
	if err != nil {
		t.Fatal("fixture request construction")
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Origin", f.web.URL)
	if csrf && c.Jar != nil {
		u, _ := url.Parse(f.web.URL)
		for _, cookie := range c.Jar.Cookies(u) {
			if cookie.Name == "csrftoken" {
				req.Header.Set("X-CSRFToken", cookie.Value)
			}
		}
	}
	res, err := c.Do(req)
	if err != nil {
		t.Fatal("fixture HTTP exchange failed")
	}
	defer res.Body.Close()
	bytes, err := io.ReadAll(res.Body)
	if err != nil {
		t.Fatal("fixture response unreadable")
	}
	out := map[string]any{}
	if len(bytes) > 0 && json.Unmarshal(bytes, &out) != nil {
		t.Fatal("fixture JSON response invalid")
	}
	return res.StatusCode, out, res.Header
}
func (f *arcadeFixture) register(t *testing.T, c *http.Client, name string) {
	t.Helper()
	status, _, _ := f.request(t, c, "GET", "/api/auth/csrf", nil, false)
	if status != 200 {
		t.Fatal("CSRF initialization", status)
	}
	status, _, _ = f.request(t, c, "POST", "/api/auth/signup", map[string]any{"username": name, "password": "synthetic-qualified-pass", "name": "Private fixture name"}, true)
	if status != 201 && status != 200 {
		t.Fatal("native signup", status)
	}
}
func (f *arcadeFixture) consent(t *testing.T, c *http.Client, alias string) {
	t.Helper()
	status, _, _ := f.request(t, c, "POST", "/api/me/consent", map[string]any{"birth_year": 1990, "accept_privacy": true, "accept_tos": true, "display_name": alias}, true)
	if status != 200 {
		t.Fatal("native consent", status)
	}
}
func (f *arcadeFixture) intruder(t *testing.T, body map[string]any) string {
	t.Helper()
	tiles := map[string]bool{}
	for _, tile := range body["tiles"].([]any) {
		tiles[tile.(map[string]any)["id"].(string)] = true
	}
	for _, board := range f.data.Boards {
		if board.Game != "intrusul" {
			continue
		}
		intruder, _ := board.Payload["intruder"].(string)
		if !tiles[intruder] {
			continue
		}
		raw, _ := json.Marshal(board.Payload["members"])
		var members []string
		_ = json.Unmarshal(raw, &members)
		match := len(members)+1 == len(tiles)
		for _, id := range members {
			match = match && tiles[id]
		}
		if match {
			return intruder
		}
	}
	t.Fatal("fixture board solution unavailable")
	return ""
}
func (f *arcadeFixture) count(t *testing.T, table string) int {
	t.Helper()
	var count int
	if err := f.pool.QueryRow(context.Background(), `SELECT count(*) FROM `+pgx.Identifier{table}.Sanitize()).Scan(&count); err != nil {
		t.Fatal("fixture count unavailable")
	}
	return count
}
func TestArcadeAuthenticatedOwnershipTerminalRankingExportAndErase(t *testing.T) {
	f := newArcadeFixture(t)
	a, b, anon := f.client(), f.client(), f.client()
	f.register(t, a, "arcade-owner")
	f.register(t, b, "arcade-other")
	f.consent(t, b, "Other alias")
	status, body, _ := f.request(t, a, "POST", prefix+"?seed=17", nil, true)
	if status != 200 {
		t.Fatal("authenticated game creation", status)
	}
	id := body["game_id"].(string)
	answer := f.intruder(t, body)
	status, won, _ := f.request(t, a, "POST", prefix+"/"+id+"/guess", map[string]any{"id": answer}, true)
	if status != 200 || won["won"] != true {
		t.Fatal("server terminal result", status)
	}
	if f.count(t, "cat_native_verified") != 0 {
		t.Fatal("unconsented result stored")
	}
	f.consent(t, a, "Arcade alias")
	status, _, headers := f.request(t, a, "GET", prefix+"/"+id, nil, false)
	if status != 200 || headers.Get("Cache-Control") != "no-store" {
		t.Fatal("owned result retry", status)
	}
	if f.count(t, "cat_native_verified") != 1 {
		t.Fatal("server result missing")
	}
	status, ranking, _ := f.request(t, anon, "GET", "/api/ranking?game=intrusul", nil, false)
	if status != 200 || len(ranking["entries"].([]any)) != 0 {
		t.Fatal("ranking opt-in bypass")
	}
	status, _, _ = f.request(t, a, "POST", "/api/me/profile", map[string]any{"show_on_ranking": true}, true)
	if status != 200 {
		t.Fatal("ranking opt-in", status)
	}
	status, ranking, _ = f.request(t, anon, "GET", "/api/ranking?game=intrusul", nil, false)
	if status != 200 || len(ranking["entries"].([]any)) != 1 {
		t.Fatal("verified ranking missing")
	}
	entry := ranking["entries"].([]any)[0].(map[string]any)
	if entry["name"] != "Arcade alias" || entry["score"] != float64(1000) || len(entry) != 4 {
		t.Fatal("ranking projection widened or wrong score")
	}
	for _, client := range []*http.Client{b, anon} {
		for _, method := range []string{"GET", "POST"} {
			path := prefix + "/" + id
			var input any
			if method == "POST" {
				path += "/guess"
				input = map[string]any{"id": answer}
			}
			status, _, _ = f.request(t, client, method, path, input, true)
			if status != 404 {
				t.Fatal("foreign game reachable", method, status)
			}
		}
	}
	status, _, _ = f.request(t, b, "POST", prefix+"?seed=21&previous_game_id="+id, nil, true)
	if status != 404 {
		t.Fatal("foreign owned game used as previous state")
	}
	spoof := map[string]any{"entries": []any{map[string]any{"game": "intrusul", "score": 1000, "detail": "Synthetic private note", "at": 1760000000000}}}
	status, _, _ = f.request(t, b, "POST", "/api/me/scores", spoof, true)
	if status != 200 {
		t.Fatal("private browser receipt", status)
	}
	status, ranking, _ = f.request(t, anon, "GET", "/api/ranking?game=intrusul", nil, false)
	if status != 200 || len(ranking["entries"].([]any)) != 1 {
		t.Fatal("browser score reached verified ranking")
	}
	status, export, _ := f.request(t, b, "GET", "/api/me/scores", nil, false)
	if status != 200 || len(export["entries"].([]any)) != 1 {
		t.Fatal("private self export missing")
	}
	status, export, _ = f.request(t, a, "GET", "/api/me/scores", nil, false)
	if status != 200 || len(export["entries"].([]any)) != 0 {
		t.Fatal("private export cross-user exposure")
	}
	status, _, _ = f.request(t, a, "POST", "/api/auth/logout", nil, true)
	if status != 200 {
		t.Fatal("logout", status)
	}
	status, _, _ = f.request(t, a, "GET", prefix+"/"+id, nil, false)
	if status != 404 {
		t.Fatal("logout released owned game")
	}
	f.request(t, a, "GET", "/api/auth/csrf", nil, false)
	status, _, _ = f.request(t, a, "POST", "/api/auth/login", map[string]any{"username": "arcade-owner", "password": "synthetic-qualified-pass"}, true)
	if status != 200 {
		t.Fatal("real native relogin", status)
	}
	status, _, _ = f.request(t, a, "GET", prefix+"/"+id, nil, false)
	if status != 200 {
		t.Fatal("owner did not regain own game", status)
	}
	status, _, _ = f.request(t, a, "POST", "/api/me/delete", map[string]any{}, true)
	if status != 200 {
		t.Fatal("erasure", status)
	}
	status, _, _ = f.request(t, b, "GET", prefix+"/"+id, nil, true)
	if status != 404 {
		t.Fatal("erased ownership became transferable")
	}
	var seals int
	if err := f.pool.QueryRow(context.Background(), `SELECT count(*) FROM cat_native_game_owners WHERE user_id IS NULL`).Scan(&seals); err != nil || seals != 1 {
		t.Fatal("anonymous erasure seal missing")
	}
	if f.count(t, "cat_native_verified") != 0 {
		t.Fatal("verified result survived erasure")
	}
}
func TestArcadeAnonymousClaimIsOneOwnerUnderConcurrentHTTPRequests(t *testing.T) {
	f := newArcadeFixture(t)
	anon, a, b := f.client(), f.client(), f.client()
	f.register(t, a, "claim-one")
	f.register(t, b, "claim-two")
	f.consent(t, a, "One alias")
	f.consent(t, b, "Two alias")
	status, body, _ := f.request(t, anon, "POST", prefix+"?seed=19", nil, false)
	if status != 200 {
		t.Fatal(status)
	}
	id := body["game_id"].(string)
	answer := f.intruder(t, body)
	status, _, _ = f.request(t, a, "GET", prefix+"/"+id, nil, false)
	if status != 200 || f.count(t, "cat_native_game_owners") != 0 {
		t.Fatal("GET without explicit CSRF claimed anonymous game")
	}
	status, _, _ = f.request(t, a, "POST", prefix+"/"+id+"/guess", map[string]any{"id": answer}, false)
	if status != 403 || f.count(t, "cat_native_game_owners") != 0 {
		t.Fatal("mutation without CSRF claimed game")
	}
	ready := make(chan struct{})
	results := make(chan int, 2)
	var wg sync.WaitGroup
	for _, client := range []*http.Client{a, b} {
		wg.Add(1)
		go func(c *http.Client) {
			defer wg.Done()
			<-ready
			code, _, _ := f.request(t, c, "POST", prefix+"/"+id+"/guess", map[string]any{"id": answer}, true)
			results <- code
		}(client)
	}
	close(ready)
	wg.Wait()
	close(results)
	counts := map[int]int{}
	for code := range results {
		counts[code]++
	}
	if counts[200] != 1 || counts[404] != 1 || f.count(t, "cat_native_game_owners") != 1 || f.count(t, "cat_native_verified") != 1 {
		t.Fatal("concurrent claim admitted multiple owners")
	}
	unknown := "00000000-0000-4000-8000-000000000000"
	status, _, _ = f.request(t, a, "POST", prefix+"/"+unknown+"/hint", nil, true)
	if status != 404 || f.count(t, "cat_native_game_owners") != 1 {
		t.Fatal("unknown game created ownership")
	}
	status, _, _ = f.request(t, anon, "GET", prefix+"/"+id, nil, false)
	if status != 404 {
		t.Fatal("anonymous caller accessed claimed game")
	}
}

func TestArcadeCuratedPlayedKeyUsesOwnedServerTerminalResult(t *testing.T) {
	f := newArcadeFixture(t)
	client := f.client()
	f.register(t, client, "curated-owner")
	f.consent(t, client, "Curated alias")
	status, body, _ := f.request(t, client, "POST", "/api/wordgames/conexiuni/games?seed=17&difficulty=normal", nil, true)
	if status != 200 {
		t.Fatal("curated game create", status)
	}
	id := body["game_id"].(string)
	progress := f.game.gameProgress("conexiuni", id)
	if progress.curated == "" {
		t.Fatal("curated fixture not selected")
	}
	var groups map[string]any
	for _, item := range f.data.PackItems {
		if item.Game == "conexiuni" && item.ID == progress.curated {
			groups = item.Payload["groups"].(map[string]any)
			break
		}
	}
	if len(groups) != 4 {
		t.Fatal("curated solution fixture unavailable")
	}
	for _, ids := range groups {
		status, body, _ = f.request(t, client, "POST", "/api/wordgames/conexiuni/games/"+id+"/guess", map[string]any{"ids": ids}, true)
		if status != 200 {
			t.Fatal("curated terminal action", status)
		}
	}
	if body["won"] != true || f.count(t, "cat_native_played") != 1 {
		t.Fatal("curated terminal key not recorded")
	}
	var stored string
	if err := f.pool.QueryRow(context.Background(), `SELECT pack_id FROM cat_native_played WHERE game='conexiuni'`).Scan(&stored); err != nil || stored != progress.curated {
		t.Fatal("curated identity projection drift")
	}
	status, next, _ := f.request(t, client, "POST", "/api/wordgames/conexiuni/games?seed=17&difficulty=normal", nil, true)
	if status != 200 {
		t.Fatal("curated exclusion create", status)
	}
	if f.game.gameProgress("conexiuni", next["game_id"].(string)).curated == progress.curated {
		t.Fatal("finished curated key not excluded")
	}
}
func TestArcadeTerminalClaimAndErasureRaceCannotRetainVerifiedIdentity(t *testing.T) {
	f := newArcadeFixture(t)
	client, anon := f.client(), f.client()
	f.register(t, client, "erasure-race-owner")
	f.consent(t, client, "Race alias")
	status, body, _ := f.request(t, client, "POST", prefix+"?seed=19", nil, true)
	if status != 200 {
		t.Fatal(status)
	}
	id := body["game_id"].(string)
	answer := f.intruder(t, body)
	ready := make(chan struct{})
	results := make(chan int, 2)
	var wg sync.WaitGroup
	for _, erase := range []bool{false, true} {
		wg.Add(1)
		go func(remove bool) {
			defer wg.Done()
			<-ready
			path, input := prefix+"/"+id+"/guess", any(map[string]any{"id": answer})
			if remove {
				path, input = "/api/me/delete", map[string]any{}
			}
			code, _, _ := f.request(t, client, "POST", path, input, true)
			results <- code
		}(erase)
	}
	close(ready)
	wg.Wait()
	close(results)
	for code := range results {
		if code != 200 && code != 404 && code != 403 {
			t.Fatal("claim/erasure race failed", code)
		}
	}
	if f.count(t, "cat_native_users") != 0 || f.count(t, "cat_native_verified") != 0 || f.count(t, "cat_native_profiles") != 0 {
		t.Fatal("erasure retained identity or server score")
	}
	status, _, _ = f.request(t, anon, "GET", prefix+"/"+id, nil, false)
	if status != 404 {
		t.Fatal("erased owned game disclosed")
	}
}

func TestArcadeOwnershipCapacityFailsClosedWithoutDisablingAnonymousCreation(t *testing.T) {
	f := newArcadeFixture(t)
	client, anon := f.client(), f.client()
	f.register(t, client, "capacity-owner")
	var user int64
	if err := f.pool.QueryRow(context.Background(), `SELECT id FROM cat_native_users WHERE username='capacity-owner'`).Scan(&user); err != nil {
		t.Fatal("fixture identity unavailable")
	}
	if _, err := f.pool.Exec(context.Background(), `INSERT INTO cat_native_game_owners(game,game_hash,user_id,expires_at) SELECT 'intrusul',lpad(to_hex(i),64,'0'),$1,now()+interval '1 day' FROM generate_series(1,6000)i`, user); err != nil {
		t.Fatal("bounded ownership fixture unavailable")
	}
	status, _, _ := f.request(t, client, "POST", prefix+"?seed=17", nil, true)
	if status != 503 || f.count(t, "cat_native_game_owners") != 6000 {
		t.Fatal("ownership hard cap ignored")
	}
	status, _, _ = f.request(t, anon, "POST", prefix+"?seed=17", nil, false)
	if status != 200 {
		t.Fatal("anonymous creation disabled by account capacity")
	}
	if _, err := f.pool.Exec(context.Background(), `UPDATE cat_native_game_owners SET expires_at=now()-interval '1 minute'`); err != nil {
		t.Fatal("expiry fixture unavailable")
	}
	status, body, _ := f.request(t, client, "POST", prefix+"?seed=19", nil, true)
	if status != 200 || f.count(t, "cat_native_game_owners") != 1 {
		t.Fatal("expired metadata not reclaimed")
	}
	var privateCount int
	if err := f.pool.QueryRow(context.Background(), `SELECT count(*) FROM cat_native_game_owners WHERE game_hash=$1`, body["game_id"]).Scan(&privateCount); err != nil || privateCount != 0 {
		t.Fatal("raw game capability persisted")
	}
}
