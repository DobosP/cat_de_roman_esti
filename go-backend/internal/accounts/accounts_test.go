package accounts

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/shared-go/authcore"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// The connection must point at a disposable local/CI PostgreSQL database.
// Credentials are not loaded from production files or printed by these tests.
var testDatabase = flag.String("accounts.database", "", "disposable PostgreSQL connection for native account integration tests")

type fixture struct {
	pool  *pgxpool.Pool
	store *Store
	auth  *authcore.Service
	app   *Service
}

func newFixture(t *testing.T, before func(*pgxpool.Pool)) *fixture {
	t.Helper()
	if *testDatabase == "" {
		t.Skip("native accounts integration needs -accounts.database disposable PostgreSQL")
	}
	ctx := context.Background()
	base, err := pgxpool.New(ctx, *testDatabase)
	if err != nil {
		t.Fatal("invalid disposable database configuration")
	}
	t.Cleanup(base.Close)
	schemaName := "cat_go_test_" + strings.ToLower(rand.Text())
	quoted := pgx.Identifier{schemaName}.Sanitize()
	if _, err = base.Exec(ctx, "CREATE SCHEMA "+quoted); err != nil {
		t.Fatal("disposable database unavailable")
	}
	t.Cleanup(func() { _, _ = base.Exec(context.Background(), "DROP SCHEMA "+quoted+" CASCADE") })
	config, err := pgxpool.ParseConfig(*testDatabase)
	if err != nil {
		t.Fatal("invalid disposable database configuration")
	}
	config.ConnConfig.RuntimeParams["search_path"] = schemaName
	config.MaxConns = 4
	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		t.Fatal("disposable pool initialization failed")
	}
	t.Cleanup(pool.Close)
	if before != nil {
		before(pool)
	}
	if err = Migrate(ctx, pool); err != nil {
		t.Fatalf("native schema migration: %v", err)
	}
	store := NewStore(pool)
	auth, err := authcore.New(authcore.Config{PublicURL: "https://app.example"}, store)
	if err != nil {
		t.Fatal(err)
	}
	app := New(pool, Config{Now: func() time.Time { return time.Date(2026, 10, 4, 12, 0, 0, 0, time.UTC) }, CategoryAllowed: func(category string) bool { return category == "muzica" || category == "gastronomie" }}, auth)
	return &fixture{pool, store, auth, app}
}

func (f *fixture) user(t *testing.T, name string) (authcore.User, *http.Cookie, *http.Cookie) {
	t.Helper()
	ctx := context.Background()
	user, err := f.store.CreatePasswordUser(ctx, authcore.User{Username: name, Email: name + "@example.com", Name: "Private Name"}, "!")
	if err != nil {
		t.Fatal(err)
	}
	token := rand.Text() + rand.Text()
	digest := sha256.Sum256([]byte(token))
	err = f.store.CreateSession(ctx, authcore.Session{TokenHash: hex.EncodeToString(digest[:]), UserID: user.ID, ExpiresAt: time.Now().Add(time.Hour)})
	if err != nil {
		t.Fatal(err)
	}
	return user, &http.Cookie{Name: "sessionid", Value: token}, &http.Cookie{Name: "csrftoken", Value: rand.Text() + rand.Text()}
}

func (f *fixture) request(method, path, body string, cookies ...*http.Cookie) *httptest.ResponseRecorder {
	r := httptest.NewRequest(method, "https://app.example"+path, strings.NewReader(body))
	if method == http.MethodPost {
		r.Header.Set("Origin", "https://app.example")
		r.Header.Set("Content-Type", "application/json")
	}
	for _, cookie := range cookies {
		r.AddCookie(cookie)
		if cookie.Name == "csrftoken" {
			r.Header.Set("X-CSRFToken", cookie.Value)
		}
	}
	out := httptest.NewRecorder()
	if !f.app.Handle(out, r) {
		panic("unhandled account test route")
	}
	return out
}

func bodyJSON(t *testing.T, response *httptest.ResponseRecorder) map[string]any {
	t.Helper()
	var out map[string]any
	if err := json.Unmarshal(response.Body.Bytes(), &out); err != nil {
		t.Fatalf("invalid response %s", response.Body)
	}
	return out
}

func (f *fixture) consent(t *testing.T, cookies ...*http.Cookie) {
	t.Helper()
	out := f.request(http.MethodPost, "/api/me/consent", `{"birth_year":1990,"accept_privacy":true,"accept_tos":true}`, cookies...)
	if out.Code != http.StatusOK {
		t.Fatalf("consent %d %s", out.Code, out.Body)
	}
}

func TestScoreValidationAndConsentProjection(t *testing.T) {
	service := New(nil, Config{CategoryAllowed: func(c string) bool { return c == "muzica" }}, nil)
	score, at := 1000, int64(1700000000000)
	for field, mutate := range map[string]func(*scoreEntry){"game": func(e *scoreEntry) { e.Game = "unknown" }, "score": func(e *scoreEntry) { v := 1001; e.Score = &v }, "at": func(e *scoreEntry) { v := int64(1); e.At = &v }, "detail": func(e *scoreEntry) { e.Detail = " " }, "daily": func(e *scoreEntry) { e.Daily = "2026-02-30" }, "difficulty": func(e *scoreEntry) { e.Difficulty = "extreme" }, "category": func(e *scoreEntry) { e.Category = "unknown" }, "puzzle_key": func(e *scoreEntry) { e.Puzzle = "a\nsecret" }} {
		e := scoreEntry{Game: "contexto", Score: &score, At: &at, Detail: "3 încercări"}
		mutate(&e)
		if got := service.validateScore(&e); got != field {
			t.Errorf("%s validation returned %q", field, got)
		}
	}
	p := profile{Completed: true, Version: "old", Display: "Public", Visible: true}
	payload := service.payload(authcore.User{ID: "1", Email: "private@example.com"}, p)
	if payload["can_save_progress"] != false || payload["show_on_ranking"] != false {
		t.Fatal("stale policy exposed ranking/progress")
	}
}

func TestNativeAccountConsentMinorHoldAndCSRF(t *testing.T) {
	f := newFixture(t, nil)
	user, session, csrf := f.user(t, "adult")
	out := f.request(http.MethodGet, "/api/me", "")
	if out.Code != http.StatusOK || bodyJSON(t, out)["authenticated"] != false || len(out.Result().Cookies()) == 0 {
		t.Fatal("anonymous me failed")
	}
	out = f.request(http.MethodGet, "/api/me", "", session)
	if bodyJSON(t, out)["user"].(map[string]any)["can_save_progress"] != false {
		t.Fatal("login granted consent")
	}
	f.consent(t, session, csrf)
	p, err := f.app.profile(context.Background(), mustID(t, user.ID))
	if err != nil || !p.canSave("2026-07-09") {
		t.Fatal("adult consent failed")
	}
	_, minorSession, minorCSRF := f.user(t, "minor")
	out = f.request(http.MethodPost, "/api/me/consent", `{"birth_year":2016,"accept_privacy":true,"accept_tos":true}`, minorSession, minorCSRF)
	if out.Code != http.StatusForbidden || bodyJSON(t, out)["status"] != "parental_consent_required" {
		t.Fatal("minor self consent permitted")
	}
	out = f.request(http.MethodPost, "/api/me/consent", `{"birth_year":1990,"accept_privacy":true,"accept_tos":true,"display_name":"Adult"}`, minorSession, minorCSRF)
	if out.Code != http.StatusForbidden {
		t.Fatal("minor hold was reset")
	}
	minor := bodyJSON(t, out)["user"].(map[string]any)
	if minor["can_save_progress"] != false || minor["display_name"] != "" {
		t.Fatal("minor resubmission changed protected state")
	}
	out = f.request(http.MethodPost, "/api/me/profile", `{"display_name":"Evil"}`, session)
	if out.Code != http.StatusForbidden {
		t.Fatal("CSRF-free write permitted")
	}
	out = f.request(http.MethodPost, "/api/me/profile", `{"display_name":"Adult","show_on_ranking":true}`, minorSession, minorCSRF)
	if out.Code != http.StatusForbidden {
		t.Fatal("minor profile visibility permitted")
	}
	out = f.request(http.MethodGet, "/api/me/scores", "", minorSession)
	if out.Code != http.StatusForbidden {
		t.Fatal("minor progress read permitted")
	}
}

func mustID(t *testing.T, id string) int64 {
	t.Helper()
	parsed, err := userID(id)
	if err != nil {
		t.Fatal(err)
	}
	return parsed
}

func TestNativePrivateScoresIsolationIdempotencyAndCap(t *testing.T) {
	f := newFixture(t, nil)
	user, session, csrf := f.user(t, "scores")
	f.consent(t, session, csrf)
	one := `{"entries":[{"game":"contexto","score":1000,"detail":"3 încercări","at":1700000000000,"category":"muzica"}]}`
	out := f.request(http.MethodPost, "/api/me/scores", one, session, csrf)
	if out.Code != http.StatusOK || bodyJSON(t, out)["saved"] != float64(1) {
		t.Fatalf("score upload %d %s", out.Code, out.Body)
	}
	out = f.request(http.MethodPost, "/api/me/scores", one, session, csrf)
	if bodyJSON(t, out)["saved"] != float64(0) {
		t.Fatal("upload not idempotent")
	}
	for batch := 0; batch < 6; batch++ {
		entries := []map[string]any{}
		for i := 0; i < 100; i++ {
			index := batch*100 + i
			entries = append(entries, map[string]any{"game": "contexto", "score": 500, "detail": "x", "at": 1700000000000 + index, "puzzle_key": fmt.Sprintf("p-%d", index)})
		}
		encoded, _ := json.Marshal(map[string]any{"entries": entries})
		out = f.request(http.MethodPost, "/api/me/scores", string(encoded), session, csrf)
		if out.Code != http.StatusOK {
			t.Fatalf("batch %d %s", out.Code, out.Body)
		}
	}
	var count int
	if err := f.pool.QueryRow(context.Background(), "SELECT count(*) FROM cat_native_scores WHERE user_id=$1", mustID(t, user.ID)).Scan(&count); err != nil || count != 500 {
		t.Fatal("unbounded scores", count, err)
	}
	var bests int
	_ = f.pool.QueryRow(context.Background(), "SELECT count(*) FROM cat_native_verified").Scan(&bests)
	if bests != 0 {
		t.Fatal("client history fed public ranking")
	}
	_, otherSession, otherCSRF := f.user(t, "other")
	f.consent(t, otherSession, otherCSRF)
	out = f.request(http.MethodGet, "/api/me/scores", "", otherSession)
	if len(bodyJSON(t, out)["entries"].([]any)) != 0 {
		t.Fatal("cross-user progress leak")
	}
	for _, patch := range []string{`{"entries":[{"game":"contexto","score":true,"detail":"x","at":1700000000000}]}`, `{"entries":[{"game":"contexto","score":1000,"detail":"x","at":1}]}`, `{"entries":[{"game":"contexto","score":1000,"detail":"x","at":1700000000000,"daily":"2026-02-30"}]}`} {
		out = f.request(http.MethodPost, "/api/me/scores", patch, session, csrf)
		if out.Code != http.StatusUnprocessableEntity {
			t.Fatalf("invalid metadata %d %s", out.Code, out.Body)
		}
	}
}

func TestNativeServerRankingTiesPrivacyAndMonotonicBest(t *testing.T) {
	f := newFixture(t, nil)
	var lowSession *http.Cookie
	for i, name := range []string{"Ana", "Bia", "Cora"} {
		user, session, csrf := f.user(t, strings.ToLower(name))
		f.consent(t, session, csrf)
		out := f.request(http.MethodPost, "/api/me/profile", `{"display_name":"`+name+`","show_on_ranking":true}`, session, csrf)
		if out.Code != http.StatusOK {
			t.Fatal(out.Body)
		}
		score := 800
		if i == 2 {
			score = 500
			lowSession = session
		}
		if err := f.app.RecordVerifiedBest(context.Background(), user.ID, "contexto", score); err != nil {
			t.Fatal(err)
		}
		if err := f.app.RecordVerifiedBest(context.Background(), user.ID, "contexto", 1); err != nil {
			t.Fatal(err)
		}
	}
	out := f.request(http.MethodGet, "/api/ranking?game=contexto", "")
	entries := bodyJSON(t, out)["entries"].([]any)
	if len(entries) != 3 {
		t.Fatal(entries)
	}
	for i, want := range []float64{1, 1, 3} {
		e := entries[i].(map[string]any)
		if e["rank"] != want || e["email"] != nil || e["avatar"] != nil {
			t.Fatal("ranking tie/privacy", e)
		}
	}
	out = f.request(http.MethodGet, "/api/ranking?game=contexto&limit=1", "", lowSession)
	body := bodyJSON(t, out)
	if len(body["entries"].([]any)) != 1 || body["me"].(map[string]any)["rank"] != float64(3) {
		t.Fatal("bounded own rank", body)
	}
}

func TestNativePlayedConsentGateAndConcurrentBest(t *testing.T) {
	f := newFixture(t, nil)
	user, session, csrf := f.user(t, "parallel")
	if err := f.app.RecordPlayed(context.Background(), user.ID, "contexto", "ctx-curated"); err != nil {
		t.Fatal(err)
	}
	finished, err := f.app.Finished(context.Background(), user.ID, "contexto")
	if err != nil || len(finished) != 0 {
		t.Fatal("recorded before consent")
	}
	f.consent(t, session, csrf)
	if err = f.app.RecordPlayed(context.Background(), user.ID, "contexto", "ctx-curated"); err != nil {
		t.Fatal(err)
	}
	finished, err = f.app.Finished(context.Background(), user.ID, "contexto")
	if err != nil || !finished["ctx-curated"] {
		t.Fatal("played round trip failed")
	}
	var wait sync.WaitGroup
	for score := 100; score <= 1000; score += 100 {
		wait.Add(1)
		go func(score int) {
			defer wait.Done()
			if err := f.app.RecordVerifiedBest(context.Background(), user.ID, "contexto", score); err != nil {
				t.Error(err)
			}
		}(score)
	}
	wait.Wait()
	var score int
	if err = f.pool.QueryRow(context.Background(), "SELECT score FROM cat_native_verified WHERE user_id=$1 AND game='contexto'", mustID(t, user.ID)).Scan(&score); err != nil || score != 1000 {
		t.Fatal("concurrent best lost", score, err)
	}
}

func TestNativeEraseRevokesAllAccountData(t *testing.T) {
	f := newFixture(t, nil)
	user, session, csrf := f.user(t, "delete")
	f.consent(t, session, csrf)
	_ = f.app.RecordPlayed(context.Background(), user.ID, "contexto", "ctx-curated")
	_ = f.app.RecordVerifiedBest(context.Background(), user.ID, "contexto", 700)
	out := f.request(http.MethodPost, "/api/me/delete", `{}`, session, csrf)
	if out.Code != http.StatusOK || bodyJSON(t, out)["ok"] != true {
		t.Fatalf("delete %d %s", out.Code, out.Body)
	}
	for _, table := range []string{"cat_native_profiles", "cat_native_consents", "cat_native_sessions", "cat_native_scores", "cat_native_played", "cat_native_verified"} {
		var count int
		err := f.pool.QueryRow(context.Background(), "SELECT count(*) FROM "+pgx.Identifier{table}.Sanitize()+" WHERE user_id=$1", mustID(t, user.ID)).Scan(&count)
		if err != nil || count != 0 {
			t.Error("un-erased rows", table, count, err)
		}
	}
	out = f.request(http.MethodGet, "/api/me", "", session)
	if bodyJSON(t, out)["authenticated"] != false {
		t.Fatal("erasure left session active")
	}
}

func TestNativeSharedOAuthSingleUseAndThrottle(t *testing.T) {
	f := newFixture(t, nil)
	flow := authcore.OAuthFlow{Provider: "google", BrowserHash: "browser", Verifier: "verifier", Nonce: "nonce", ExpiresAt: time.Now().Add(time.Minute)}
	hash := strings.Repeat("a", 64)
	if err := f.store.CreateOAuthFlow(context.Background(), hash, flow); err != nil {
		t.Fatal(err)
	}
	var wait sync.WaitGroup
	var mu sync.Mutex
	success := 0
	for i := 0; i < 8; i++ {
		wait.Add(1)
		go func() {
			defer wait.Done()
			_, err := f.store.ConsumeOAuthFlow(context.Background(), hash, time.Now())
			if err == nil {
				mu.Lock()
				success++
				mu.Unlock()
			} else if !errors.Is(err, authcore.ErrNotFound) {
				t.Error(err)
			}
		}()
	}
	wait.Wait()
	if success != 1 {
		t.Fatal("state was not atomic single-use", success)
	}
	key := strings.Repeat("b", 64)
	now := time.Now()
	for i := 0; i < 11; i++ {
		allowed, err := f.store.AllowAuthAttempt(context.Background(), key, now)
		if err != nil || allowed != (i < 10) {
			t.Fatal("shared throttle failed", i, allowed, err)
		}
	}
}

func TestNativeLegacyDjangoImportIsIdempotent(t *testing.T) {
	f := newFixture(t, func(pool *pgxpool.Pool) {
		_, err := pool.Exec(context.Background(), `CREATE TABLE auth_user(id bigint PRIMARY KEY,username text,password text,email text,first_name text,last_name text,is_active boolean,date_joined timestamptz); INSERT INTO auth_user VALUES(77,'legacy','pbkdf2_sha256$1000$django-test-salt$V9X3atZE8fGNP2JD7x37QLrK1IWf3ml9/hPcqE3LZ8I=','old@example.com','Legacy','Name',true,now()); CREATE TABLE socialaccount_socialaccount(id bigint,user_id bigint,provider text,uid text,extra_data jsonb); INSERT INTO socialaccount_socialaccount VALUES(1,77,'google','stable-subject','{"name":"Imported Name","picture":"https://images.example/avatar.png"}'); CREATE TABLE django_session(session_key text,session_data text); INSERT INTO django_session VALUES('old-session','encoded-identity');`)
		if err != nil {
			t.Fatal(err)
		}
	})
	user, hash, err := f.store.FindByUsername(context.Background(), "legacy")
	if err != nil || user.ID != "77" || user.Name != "Imported Name" || user.Avatar != "https://images.example/avatar.png" {
		t.Fatal("legacy user import", user, err)
	}
	valid, err := authcore.VerifyPassword(context.Background(), "correct horse battery", hash)
	if err != nil || !valid {
		t.Fatal("legacy hash broken")
	}
	external, err := f.store.FindOrCreateExternal(context.Background(), "google", "stable-subject", authcore.User{Email: "changed@example.com"})
	if err != nil || external.ID != user.ID {
		t.Fatal("legacy external identity broken")
	}
	if err = Migrate(context.Background(), f.pool); err != nil {
		t.Fatal(err)
	}
	var count int
	_ = f.pool.QueryRow(context.Background(), "SELECT count(*) FROM cat_native_users").Scan(&count)
	if count != 1 {
		t.Fatal("migration duplicated users")
	}
	_ = f.pool.QueryRow(context.Background(), "SELECT count(*) FROM django_session").Scan(&count)
	if count != 0 {
		t.Fatal("legacy sessions retained")
	}
	newUser, err := f.store.CreatePasswordUser(context.Background(), authcore.User{Username: "after"}, "!")
	if err != nil || mustID(t, newUser.ID) <= 77 {
		t.Fatal("native sequence did not advance")
	}
}

func TestNativeProfileVisibilityAndRenewedConsent(t *testing.T) {
	f := newFixture(t, nil)
	user, session, csrf := f.user(t, "policy")
	f.consent(t, session, csrf)
	out := f.request(http.MethodPost, "/api/me/profile", `{"show_on_ranking":true}`, session, csrf)
	if out.Code != http.StatusBadRequest {
		t.Fatal("implicit private name made public")
	}
	out = f.request(http.MethodPost, "/api/me/profile", `{"display_name":"  Ana  Pop  ","show_on_ranking":true}`, session, csrf)
	if out.Code != http.StatusOK || bodyJSON(t, out)["user"].(map[string]any)["ranking_name"] != "Ana Pop" {
		t.Fatal("nickname normalization")
	}
	out = f.request(http.MethodPost, "/api/me/profile", `{"display_name":"   "}`, session, csrf)
	if out.Code != http.StatusBadRequest {
		t.Fatal("blank nickname accepted")
	}
	if err := f.app.RecordVerifiedBest(context.Background(), user.ID, "contexto", 800); err != nil {
		t.Fatal(err)
	}
	f.app.config.ConsentVersion = "new-policy"
	out = f.request(http.MethodGet, "/api/me", "", session)
	payload := bodyJSON(t, out)["user"].(map[string]any)
	if payload["consent_completed"] != false || payload["show_on_ranking"] != false {
		t.Fatal("stale acceptance stayed active")
	}
	out = f.request(http.MethodGet, "/api/me/scores", "", session)
	if out.Code != http.StatusForbidden {
		t.Fatal("stale consent progress read")
	}
	out = f.request(http.MethodGet, "/api/ranking?game=contexto", "")
	if len(bodyJSON(t, out)["entries"].([]any)) != 0 {
		t.Fatal("stale consent public ranking")
	}
	out = f.request(http.MethodPost, "/api/me/profile", `{"display_name":"Changed","show_on_ranking":true}`, session, csrf)
	if out.Code != http.StatusForbidden {
		t.Fatal("stale public opt-in permitted")
	}
	p, err := f.app.profile(context.Background(), mustID(t, user.ID))
	if err != nil || p.Display != "Ana Pop" {
		t.Fatal("rejected profile transaction changed name")
	}
	f.consent(t, session, csrf)
	out = f.request(http.MethodGet, "/api/me", "", session)
	if bodyJSON(t, out)["user"].(map[string]any)["can_save_progress"] != true {
		t.Fatal("renewed consent did not reopen progress")
	}
}

func TestNativeStoreSessionExpiryDisabledIdentityAndCap(t *testing.T) {
	f := newFixture(t, nil)
	user, _, _ := f.user(t, "sessions")
	id := mustID(t, user.ID)
	for i := 0; i < 12; i++ {
		hash := fmt.Sprintf("%064d", i)
		if err := f.store.CreateSession(context.Background(), authcore.Session{TokenHash: hash, UserID: user.ID, ExpiresAt: time.Now().Add(time.Hour)}); err != nil {
			t.Fatal(err)
		}
	}
	var count int
	if err := f.pool.QueryRow(context.Background(), "SELECT count(*) FROM cat_native_sessions WHERE user_id=$1", id).Scan(&count); err != nil || count != 10 {
		t.Fatal("unbounded session count", count, err)
	}
	_, err := f.store.GetSession(context.Background(), fmt.Sprintf("%064d", 11), time.Now().Add(2*time.Hour))
	if !errors.Is(err, authcore.ErrNotFound) {
		t.Fatal("expired bearer accepted")
	}
	external, err := f.store.FindOrCreateExternal(context.Background(), "google", "same-email-subject", authcore.User{Email: user.Email})
	if err != nil || external.ID == user.ID {
		t.Fatal("native adapter linked by email")
	}
	if _, err = f.pool.Exec(context.Background(), "UPDATE cat_native_users SET active=false WHERE id=$1", mustID(t, external.ID)); err != nil {
		t.Fatal(err)
	}
	if _, err = f.store.FindOrCreateExternal(context.Background(), "google", "same-email-subject", authcore.User{Email: user.Email}); !errors.Is(err, authcore.ErrNotFound) {
		t.Fatal("disabled provider identity replaced")
	}
}

func TestNativeConsentInputAndLogoutContracts(t *testing.T) {
	f := newFixture(t, nil)
	user, session, csrf := f.user(t, "validation")
	for field, body := range map[string]string{"birth_year": `{"birth_year":1899,"accept_privacy":true,"accept_tos":true}`, "accept_privacy": `{"birth_year":1990,"accept_tos":true}`, "accept_tos": `{"birth_year":1990,"accept_privacy":true}`, "display_name": `{"birth_year":1990,"accept_privacy":true,"accept_tos":true,"display_name":"` + strings.Repeat("ă", 81) + `"}`} {
		out := f.request(http.MethodPost, "/api/me/consent", body, session, csrf)
		if out.Code != http.StatusUnprocessableEntity {
			t.Fatalf("invalid %s status %d", field, out.Code)
		}
	}
	out := f.request(http.MethodPost, "/api/me/consent", `{"birth_year":1990,"accept_privacy":true,"accept_tos":false}`, session, csrf)
	if out.Code != http.StatusBadRequest {
		t.Fatal("missing document acceptance allowed")
	}
	var count int
	if err := f.pool.QueryRow(context.Background(), "SELECT count(*) FROM cat_native_consents WHERE user_id=$1", mustID(t, user.ID)).Scan(&count); err != nil || count != 0 {
		t.Fatal("invalid acceptance created audit")
	}
	out = f.request(http.MethodPost, "/api/auth/logout", `{}`, session, csrf)
	if out.Code != http.StatusOK || bodyJSON(t, out)["ok"] != true {
		t.Fatal("logout payload differs")
	}
	out = f.request(http.MethodGet, "/api/me", "", session)
	if bodyJSON(t, out)["authenticated"] != false {
		t.Fatal("logout retained session")
	}
	out = f.request(http.MethodPost, "/api/auth/logout", `{}`, csrf)
	if out.Code != http.StatusForbidden {
		t.Fatal("anonymous logout contract differs")
	}
}

func TestNativeMigratedAccountPreservesAndErasesLegacyCopies(t *testing.T) {
	f := newFixture(t, func(pool *pgxpool.Pool) {
		_, err := pool.Exec(context.Background(), `
CREATE TABLE auth_user(id bigint PRIMARY KEY,username text,password text,email text,first_name text,last_name text,is_active boolean,date_joined timestamptz);
INSERT INTO auth_user VALUES(77,'migrated','!','old@example.com','Private','Name',true,now());
CREATE TABLE accounts_profile(user_id bigint REFERENCES auth_user(id),birth_year integer,consent_completed boolean,consent_version text,is_minor boolean,parental_consent_required boolean,display_name text,show_on_ranking boolean,created timestamptz,updated timestamptz);
INSERT INTO accounts_profile VALUES(77,1990,true,'2026-07-09',false,false,'Public Nickname',true,now(),now());
CREATE TABLE accounts_consentrecord(user_id bigint REFERENCES auth_user(id),document text,version text,text_hash text,accepted_at timestamptz);
INSERT INTO accounts_consentrecord VALUES(77,'privacy','2026-07-09','',now()),(77,'tos','2026-07-09','',now());
CREATE TABLE accounts_scoreentry(user_id bigint REFERENCES auth_user(id),game text,score integer,detail text,at bigint,puzzle_key text,daily text,difficulty text,category text,created timestamptz);
INSERT INTO accounts_scoreentry VALUES(77,'contexto',1000,'private uploaded copy',1700000000000,'curated-old','','normal','',now());
CREATE TABLE accounts_verifiedbest(user_id bigint REFERENCES auth_user(id),game text,score integer,updated timestamptz);
INSERT INTO accounts_verifiedbest VALUES(77,'contexto',600,now());
CREATE TABLE accounts_playedpuzzle(user_id bigint REFERENCES auth_user(id),game text,pack_id text,finished_at timestamptz);
INSERT INTO accounts_playedpuzzle VALUES(77,'contexto','curated-old',now());
CREATE TABLE socialaccount_socialaccount(id bigint PRIMARY KEY,user_id bigint REFERENCES auth_user(id),provider text,uid text,extra_data jsonb);
INSERT INTO socialaccount_socialaccount VALUES(1,77,'google','stable-subject','{}');
CREATE TABLE socialaccount_socialtoken(account_id bigint REFERENCES socialaccount_socialaccount(id));INSERT INTO socialaccount_socialtoken VALUES(1);
CREATE TABLE account_emailaddress(id bigint PRIMARY KEY,user_id bigint REFERENCES auth_user(id));INSERT INTO account_emailaddress VALUES(1,77);
CREATE TABLE account_emailconfirmation(email_address_id bigint REFERENCES account_emailaddress(id));INSERT INTO account_emailconfirmation VALUES(1);
CREATE TABLE auth_user_groups(user_id bigint REFERENCES auth_user(id));INSERT INTO auth_user_groups VALUES(77);
CREATE TABLE auth_user_user_permissions(user_id bigint REFERENCES auth_user(id));INSERT INTO auth_user_user_permissions VALUES(77);
CREATE TABLE django_admin_log(user_id bigint REFERENCES auth_user(id));INSERT INTO django_admin_log VALUES(77);
`)
		if err != nil {
			t.Fatal(err)
		}
	})
	user, _, err := f.store.FindByUsername(context.Background(), "migrated")
	if err != nil {
		t.Fatal(err)
	}
	token := rand.Text() + rand.Text()
	digest := sha256.Sum256([]byte(token))
	if err = f.store.CreateSession(context.Background(), authcore.Session{TokenHash: hex.EncodeToString(digest[:]), UserID: user.ID, ExpiresAt: time.Now().Add(time.Hour)}); err != nil {
		t.Fatal(err)
	}
	session := &http.Cookie{Name: "sessionid", Value: token}
	csrf := &http.Cookie{Name: "csrftoken", Value: rand.Text() + rand.Text()}
	out := f.request(http.MethodGet, "/api/me/scores", "", session)
	if out.Code != http.StatusOK || len(bodyJSON(t, out)["entries"].([]any)) != 1 {
		t.Fatal("private history migration failed")
	}
	finished, err := f.app.Finished(context.Background(), user.ID, "contexto")
	if err != nil || !finished["curated-old"] {
		t.Fatal("played history migration failed")
	}
	out = f.request(http.MethodGet, "/api/ranking?game=contexto", "")
	entries := bodyJSON(t, out)["entries"].([]any)
	if len(entries) != 1 || entries[0].(map[string]any)["score"] != float64(600) {
		t.Fatal("migration promoted browser score")
	}
	out = f.request(http.MethodPost, "/api/me/delete", `{}`, session, csrf)
	if out.Code != http.StatusOK {
		t.Fatalf("legacy erasure %d %s", out.Code, out.Body)
	}
	for _, table := range []string{"auth_user", "accounts_profile", "accounts_consentrecord", "accounts_scoreentry", "accounts_verifiedbest", "accounts_playedpuzzle", "socialaccount_socialaccount", "socialaccount_socialtoken", "account_emailaddress", "account_emailconfirmation", "auth_user_groups", "auth_user_user_permissions", "django_admin_log", "cat_native_users", "cat_native_external"} {
		var count int
		if err := f.pool.QueryRow(context.Background(), "SELECT count(*) FROM "+pgx.Identifier{table}.Sanitize()).Scan(&count); err != nil || count != 0 {
			t.Error("rollback copy survived erasure", table, count, err)
		}
	}
}
