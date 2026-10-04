package httpapi

import (
	"context"
	"encoding/json"
	"errors"
	"math"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/accounts"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/session"
	"github.com/DobosP/cat_de_roman_esti/shared-go/authcore"
	"github.com/jackc/pgx/v5"
)

type accountUserKey struct{}

func (s *Server) EnableAccounts(service *accounts.Service, auth *authcore.Service, publicOrigin string) {
	s.Accounts = service
	s.Auth = auth
	s.authOrigin = publicOrigin
	s.accountGameLifetime = accountGameTTL()
	s.authMux = http.NewServeMux()
	auth.Register(s.authMux, "/api/auth")
	s.authMux.Handle("GET /accounts/login/", auth.LoginPage("Cât de român ești?", "/"))
	for _, provider := range []string{"google", "facebook"} {
		s.authMux.HandleFunc("GET /accounts/"+provider+"/login/", func(w http.ResponseWriter, r *http.Request) {
			http.Redirect(w, r, "/api/auth/oauth/"+provider+"/start", http.StatusSeeOther)
		})
		s.authMux.HandleFunc("GET /accounts/"+provider+"/login/callback/", func(w http.ResponseWriter, r *http.Request) {
			r.SetPathValue("provider", provider)
			s.Auth.OAuthCallback(w, r)
		})
	}
}
func (s *Server) exclusions(r *http.Request, game string) map[string]bool {
	user, ok := r.Context().Value(accountUserKey{}).(authcore.User)
	if !ok || s.Accounts == nil {
		return nil
	}
	ids, err := s.Accounts.Finished(r.Context(), user.ID, game)
	if err != nil {
		return nil
	}
	return ids
}
func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if s.Accounts == nil {
		s.serveHTTP(w, r)
		return
	}
	w.Header().Set("X-Cat-Runtime", "go")
	if !validHost(r.Host, s.allowedHosts) {
		websiteBytes(w, r, 400, "text/html; charset=utf-8", []byte(badHostHTML))
		return
	}
	if r.ContentLength > MaxRequestBytes {
		write(w, r, 413, map[string]any{"detail": "Request body too large"})
		return
	}
	if s.Accounts.Handle(w, r) {
		return
	}
	if strings.HasPrefix(r.URL.Path, "/api/auth/") || strings.HasPrefix(r.URL.Path, "/accounts/") {
		s.authMux.ServeHTTP(w, r)
		return
	}
	user, err := s.Auth.Authenticate(r)
	if err != nil && !errors.Is(err, authcore.ErrNotFound) {
		write(w, r, 503, map[string]any{"detail": "Account service unavailable."})
		return
	}
	logged := err == nil
	if logged {
		r = r.WithContext(context.WithValue(r.Context(), accountUserKey{}, user))
	}
	game, id, creation, gamePath := accountGamePath(r.URL.Path)
	if !gamePath || r.Method == "OPTIONS" {
		s.serveHTTP(w, r)
		return
	}
	if logged && r.Method != "GET" && r.Method != "HEAD" && s.Auth.CheckCSRF(r) != nil {
		write(w, r, 403, map[string]any{"detail": "CSRF verification failed."})
		return
	}
	recorder := httptest.NewRecorder()
	copyResponse := func() {
		for key, values := range recorder.Header() {
			w.Header()[key] = append([]string(nil), values...)
		}
		if logged || id != "" {
			w.Header().Set("Cache-Control", "no-store")
			w.Header().Add("Vary", "Cookie")
		}
		w.WriteHeader(recorder.Code)
		_, _ = w.Write(recorder.Body.Bytes())
	}
	fail := func(err error) {
		if errors.Is(err, accounts.ErrGamePrivate) {
			write(w, r, 404, map[string]any{"detail": "Not Found"})
		} else {
			write(w, r, 503, map[string]any{"detail": "Account progress unavailable; retry this game."})
		}
	}
	if creation {
		previous := r.URL.Query().Get("previous_game_id")
		owner := ""
		if logged {
			owner = user.ID
		}
		if len(previous) == 36 {
			err = s.Accounts.GameAccess(r.Context(), owner, game, previous, false, s.accountGameLifetime, func() bool { return s.gameProgress(game, previous).found }, func(bool, pgx.Tx) error { s.serveHTTP(recorder, r); return nil })
			if err != nil {
				fail(err)
				return
			}
		} else {
			s.serveHTTP(recorder, r)
		}
		if logged && recorder.Code >= 200 && recorder.Code < 300 {
			var body struct {
				GameID string `json:"game_id"`
			}
			if json.Unmarshal(recorder.Body.Bytes(), &body) != nil || body.GameID == "" {
				write(w, r, 503, map[string]any{"detail": "Account game unavailable."})
				return
			}
			err = s.Accounts.GameAccess(r.Context(), user.ID, game, body.GameID, true, s.accountGameLifetime, func() bool { return s.gameProgress(game, body.GameID).found }, func(bool, pgx.Tx) error { return nil })
			if err != nil {
				fail(err)
				return
			}
		}
		copyResponse()
		return
	}
	owner := ""
	if logged {
		owner = user.ID
	}
	claim := logged && (r.Method != "GET" && r.Method != "HEAD" || s.Auth.CheckCSRF(r) == nil)
	err = s.Accounts.GameAccess(r.Context(), owner, game, id, claim, s.accountGameLifetime, func() bool { return s.gameProgress(game, id).found }, func(owned bool, tx pgx.Tx) error {
		s.serveHTTP(recorder, r)
		if owned && recorder.Code >= 200 && recorder.Code < 300 {
			return s.recordProgress(r.Context(), tx, user.ID, game, id)
		}
		return nil
	})
	if err != nil {
		fail(err)
		return
	}
	copyResponse()
}
func accountGamePath(path string) (game, id string, creation, handled bool) {
	if !strings.HasPrefix(path, "/api/wordgames/") {
		return
	}
	parts := strings.Split(strings.TrimPrefix(path, "/api/wordgames/"), "/")
	if len(parts) < 2 || parts[1] != "games" {
		return
	}
	game = parts[0]
	switch game {
	case "intrusul", "perechi", "conexiuni", "contexto", "lant", "alchimie":
	default:
		return "", "", false, false
	}
	if len(parts) == 2 {
		return game, "", true, true
	}
	if len(parts) > 4 || parts[2] == "" {
		return "", "", false, false
	}
	return game, parts[2], false, true
}

// Ownership outlives the configured game TTL so expiry cannot re-arm a live
// in-memory capability. Unsupported extreme account lifetimes fail at use.
func accountGameTTL() time.Duration {
	var raw *string
	if value, ok := os.LookupEnv("CAT_SESSION_TTL_SECONDS"); ok {
		raw = &value
	}
	cfg, err := session.ParseConfig(raw, nil)
	if err != nil {
		panic(err)
	}
	seconds := math.Max(60, cfg.TTLSeconds*2)
	if seconds > 365*24*3600 {
		panic("account game ownership TTL exceeds its bounded lifetime")
	}
	return time.Duration(math.Ceil(seconds * float64(time.Second)))
}

type terminalProgress struct {
	curated       string
	finished, won bool
	score         int
	found         bool
}

func (s *Server) gameProgress(game, id string) terminalProgress {
	var p terminalProgress
	p.score = -1
	switch game {
	case "contexto":
		p.curated, p.finished, p.won, p.score, p.found = s.contexto.Progress(id)
	case "lant":
		p.curated, p.finished, p.won, p.score, p.found = s.lant.Progress(id)
	case "conexiuni":
		p.curated, p.finished, p.won, p.score, p.found = s.conexiuni.Progress(id)
	case "alchimie":
		p.curated, p.finished, p.won, p.score, p.found = s.alchimie.Progress(id)
	case "intrusul":
		p.curated, p.finished, p.won, p.score, p.found = s.game.Progress(id)
	case "perechi":
		p.curated, p.finished, p.won, p.score, p.found = s.perechi.Progress(id)
	}
	return p
}
func (s *Server) recordProgress(ctx context.Context, tx pgx.Tx, user, game, id string) error {
	p := s.gameProgress(game, id)
	if !p.found || !p.finished {
		return nil
	}
	return s.Accounts.RecordOwnedTerminal(ctx, tx, user, game, id, p.curated, p.score)
}

func safeReturn(raw string) string {
	u, err := url.Parse(raw)
	if err != nil || u.IsAbs() || u.Host != "" || !strings.HasPrefix(raw, "/") || strings.HasPrefix(raw, "//") {
		return "/"
	}
	return raw
}

func (s *Server) KnownCategory(key string) bool { return s.content.CategoryLabels[key] != "" }
