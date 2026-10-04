package accounts

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"strconv"
	"strings"
	"time"
	"unicode"
	"unicode/utf8"

	"github.com/DobosP/cat_de_roman_esti/shared-go/authcore"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type Config struct {
	ConsentVersion  string
	MinAge          int
	DonateURL       string
	CategoryAllowed func(string) bool
	MaxRequestBytes int64
	Now             func() time.Time
}

type Service struct {
	pool   *pgxpool.Pool
	config Config
	auth   *authcore.Service
}

func New(pool *pgxpool.Pool, config Config, auth *authcore.Service) *Service {
	if config.ConsentVersion == "" {
		config.ConsentVersion = "2026-07-09"
	}
	if config.MinAge == 0 {
		config.MinAge = 16
	}
	if config.MaxRequestBytes == 0 {
		config.MaxRequestBytes = 64 << 10
	}
	if config.Now == nil {
		config.Now = time.Now
	}
	return &Service{pool: pool, config: config, auth: auth}
}

type profile struct {
	BirthYear *int
	Completed bool
	Version   string
	Minor     bool
	Parental  bool
	Display   string
	Visible   bool
}

func (p profile) canSave(version string) bool {
	return p.Completed && !p.Minor && !p.Parental && p.Version == version
}

func (s *Service) profile(ctx context.Context, id int64) (profile, error) {
	return readProfile(s.pool.QueryRow(ctx, "SELECT birth_year,consent_completed,consent_version,is_minor,parental_consent_required,display_name,show_on_ranking FROM cat_native_profiles WHERE user_id=$1", id))
}
func readProfile(row pgx.Row) (profile, error) {
	var p profile
	err := row.Scan(&p.BirthYear, &p.Completed, &p.Version, &p.Minor, &p.Parental, &p.Display, &p.Visible)
	return p, err
}
func lockedProfile(ctx context.Context, tx pgx.Tx, id int64) (profile, error) {
	return readProfile(tx.QueryRow(ctx, "SELECT birth_year,consent_completed,consent_version,is_minor,parental_consent_required,display_name,show_on_ranking FROM cat_native_profiles WHERE user_id=$1 FOR UPDATE", id))
}

func (s *Service) payload(user authcore.User, p profile) map[string]any {
	id, _ := userID(user.ID)
	current := p.canSave(s.config.ConsentVersion)
	ranking := strings.TrimSpace(p.Display)
	if ranking == "" {
		ranking = "Jucător"
	}
	name := p.Display
	if name == "" {
		name = user.Name
	}
	return map[string]any{"id": id, "email": user.Email, "name": name, "avatar": user.Avatar, "ranking_name": ranking, "display_name": p.Display, "show_on_ranking": p.Visible && current, "consent_completed": current, "can_save_progress": current, "is_minor": p.Minor, "parental_consent_required": p.Parental}
}

func accountSpace(r rune) bool { return unicode.IsSpace(r) || (r >= 28 && r <= 31) }
func cleanSpaces(value string) string {
	return strings.Join(strings.FieldsFunc(value, accountSpace), " ")
}
func strip(value string) string { return strings.TrimFunc(value, accountSpace) }

func (s *Service) Register(mux *http.ServeMux) {
	for _, path := range []string{"/api/me", "/api/me/consent", "/api/me/profile", "/api/me/scores", "/api/me/delete", "/api/ranking"} {
		mux.HandleFunc(path, func(w http.ResponseWriter, r *http.Request) { s.Handle(w, r) })
	}
}

func (s *Service) Handle(w http.ResponseWriter, r *http.Request) bool {
	switch r.URL.Path {
	case "/api/me":
		if r.Method == http.MethodGet {
			s.Me(w, r)
		} else {
			methodError(w, "GET")
		}
	case "/api/me/consent":
		if r.Method == http.MethodPost {
			s.Consent(w, r)
		} else {
			methodError(w, "POST")
		}
	case "/api/me/profile":
		if r.Method == http.MethodPost {
			s.Profile(w, r)
		} else {
			methodError(w, "POST")
		}
	case "/api/me/scores":
		if r.Method == http.MethodGet || r.Method == http.MethodPost {
			s.Scores(w, r)
		} else {
			methodError(w, "GET, POST")
		}
	case "/api/me/delete":
		if r.Method == http.MethodPost {
			s.Delete(w, r)
		} else {
			methodError(w, "POST")
		}
	case "/api/ranking":
		if r.Method == http.MethodGet {
			s.Ranking(w, r)
		} else {
			methodError(w, "GET")
		}
	case "/api/auth/logout":
		if r.Method == http.MethodPost {
			s.Logout(w, r)
		} else {
			methodError(w, "POST")
		}
	default:
		return false
	}
	return true
}

func (s *Service) authenticated(w http.ResponseWriter, r *http.Request, write bool) (authcore.User, int64, bool) {
	user, err := s.auth.Authenticate(r)
	if errors.Is(err, authcore.ErrNotFound) {
		accountError(w, http.StatusForbidden, "Authentication credentials were not provided.")
		return user, 0, false
	}
	if err != nil {
		accountError(w, http.StatusServiceUnavailable, "Accounts temporarily unavailable.")
		return user, 0, false
	}
	if write && s.auth.CheckCSRF(r) != nil {
		accountError(w, http.StatusForbidden, "CSRF verification failed.")
		return user, 0, false
	}
	id, err := userID(user.ID)
	if err != nil {
		accountError(w, http.StatusForbidden, "Authentication credentials were not provided.")
		return user, 0, false
	}
	return user, id, true
}

func (s *Service) Me(w http.ResponseWriter, r *http.Request) {
	s.auth.EnsureCSRF(w, r)
	base := map[string]any{"accounts_enabled": true, "min_self_consent_age": s.config.MinAge, "donate_url": s.config.DonateURL, "authenticated": false, "user": nil}
	user, err := s.auth.Authenticate(r)
	if errors.Is(err, authcore.ErrNotFound) {
		accountJSON(w, http.StatusOK, base)
		return
	}
	if err != nil {
		accountError(w, http.StatusServiceUnavailable, "Accounts temporarily unavailable.")
		return
	}
	id, err := userID(user.ID)
	if err != nil {
		accountError(w, http.StatusServiceUnavailable, "Accounts temporarily unavailable.")
		return
	}
	p, err := s.profile(r.Context(), id)
	if err != nil {
		accountError(w, http.StatusServiceUnavailable, "Accounts temporarily unavailable.")
		return
	}
	base["authenticated"] = true
	base["user"] = s.payload(user, p)
	accountJSON(w, http.StatusOK, base)
}

func (s *Service) decode(w http.ResponseWriter, r *http.Request, target any) bool {
	defer r.Body.Close()
	r.Body = http.MaxBytesReader(w, r.Body, s.config.MaxRequestBytes)
	decoder := json.NewDecoder(r.Body)
	if err := decoder.Decode(target); err != nil {
		var size *http.MaxBytesError
		if errors.As(err, &size) {
			accountError(w, http.StatusRequestEntityTooLarge, "Request body too large")
		} else {
			var kind *json.UnmarshalTypeError
			if errors.As(err, &kind) && kind.Field != "" {
				validationError(w, kind.Field)
			} else {
				accountError(w, http.StatusBadRequest, "Invalid JSON")
			}
		}
		return false
	}
	if err := decoder.Decode(&struct{}{}); err != io.EOF {
		var size *http.MaxBytesError
		if errors.As(err, &size) {
			accountError(w, http.StatusRequestEntityTooLarge, "Request body too large")
		} else {
			accountError(w, http.StatusBadRequest, "Invalid JSON")
		}
		return false
	}
	return true
}

type consentBody struct {
	BirthYear *int   `json:"birth_year"`
	Privacy   *bool  `json:"accept_privacy"`
	TOS       *bool  `json:"accept_tos"`
	Display   string `json:"display_name"`
}

func (s *Service) Consent(w http.ResponseWriter, r *http.Request) {
	user, id, ok := s.authenticated(w, r, true)
	if !ok {
		return
	}
	var body consentBody
	if !s.decode(w, r, &body) {
		return
	}
	if body.BirthYear == nil || *body.BirthYear < 1900 || *body.BirthYear > 2100 {
		validationError(w, "birth_year")
		return
	}
	if body.Privacy == nil {
		validationError(w, "accept_privacy")
		return
	}
	if body.TOS == nil {
		validationError(w, "accept_tos")
		return
	}
	if utf8.RuneCountInString(body.Display) > 80 {
		validationError(w, "display_name")
		return
	}
	if !*body.Privacy || !*body.TOS {
		accountError(w, http.StatusBadRequest, "Trebuie sa accepti politica de confidentialitate si termenii.")
		return
	}
	tx, err := s.pool.Begin(r.Context())
	if err != nil {
		unavailable(w)
		return
	}
	defer tx.Rollback(r.Context())
	p, err := lockedProfile(r.Context(), tx, id)
	if err != nil {
		unavailable(w)
		return
	}
	if p.Minor || p.Parental {
		s.parental(w, user, p)
		return
	}
	p.BirthYear = body.BirthYear
	if s.config.Now().Year()-*body.BirthYear < s.config.MinAge {
		p.Minor = true
		p.Parental = true
		p.Completed = false
		p.Version = ""
		if _, err = tx.Exec(r.Context(), "UPDATE cat_native_profiles SET birth_year=$2,is_minor=true,parental_consent_required=true,consent_completed=false,consent_version='',updated=now() WHERE user_id=$1", id, *body.BirthYear); err != nil {
			unavailable(w)
			return
		}
		if err = tx.Commit(r.Context()); err != nil {
			unavailable(w)
			return
		}
		s.parental(w, user, p)
		return
	}
	p.Completed = true
	p.Version = s.config.ConsentVersion
	p.Minor = false
	p.Parental = false
	chosen := cleanSpaces(body.Display)
	if chosen != "" {
		p.Display = chosen
	}
	if _, err = tx.Exec(r.Context(), "UPDATE cat_native_profiles SET birth_year=$2,consent_completed=true,consent_version=$3,is_minor=false,parental_consent_required=false,display_name=$4,updated=now() WHERE user_id=$1", id, *body.BirthYear, p.Version, p.Display); err != nil {
		unavailable(w)
		return
	}
	if _, err = tx.Exec(r.Context(), "INSERT INTO cat_native_consents(user_id,document,version) VALUES($1,'privacy',$2),($1,'tos',$2)", id, p.Version); err != nil {
		unavailable(w)
		return
	}
	if err = tx.Commit(r.Context()); err != nil {
		unavailable(w)
		return
	}
	accountJSON(w, http.StatusOK, map[string]any{"status": "ok", "user": s.payload(user, p)})
}

func (s *Service) parental(w http.ResponseWriter, user authcore.User, p profile) {
	accountJSON(w, http.StatusForbidden, map[string]any{"status": "parental_consent_required", "min_self_consent_age": s.config.MinAge, "user": s.payload(user, p)})
}

type profileBody struct {
	Display *string `json:"display_name"`
	Visible *bool   `json:"show_on_ranking"`
}

func (s *Service) Profile(w http.ResponseWriter, r *http.Request) {
	user, id, ok := s.authenticated(w, r, true)
	if !ok {
		return
	}
	var body profileBody
	if !s.decode(w, r, &body) {
		return
	}
	if body.Display != nil && utf8.RuneCountInString(*body.Display) > 80 {
		validationError(w, "display_name")
		return
	}
	tx, err := s.pool.Begin(r.Context())
	if err != nil {
		unavailable(w)
		return
	}
	defer tx.Rollback(r.Context())
	p, err := lockedProfile(r.Context(), tx, id)
	if err != nil {
		unavailable(w)
		return
	}
	if body.Display != nil {
		p.Display = cleanSpaces(*body.Display)
		if p.Display == "" {
			accountError(w, http.StatusBadRequest, "Numele din clasament nu poate fi gol.")
			return
		}
	}
	if body.Visible != nil {
		if *body.Visible && !p.canSave(s.config.ConsentVersion) {
			accountError(w, http.StatusForbidden, "Consimțământ valid necesar pentru clasament.")
			return
		}
		if *body.Visible && strings.TrimSpace(p.Display) == "" {
			accountError(w, http.StatusBadRequest, "Alege o poreclă înainte să apari în clasament.")
			return
		}
		p.Visible = *body.Visible
	}
	if body.Display != nil || body.Visible != nil {
		if _, err = tx.Exec(r.Context(), "UPDATE cat_native_profiles SET display_name=$2,show_on_ranking=$3,updated=now() WHERE user_id=$1", id, p.Display, p.Visible); err != nil {
			unavailable(w)
			return
		}
	}
	if err = tx.Commit(r.Context()); err != nil {
		unavailable(w)
		return
	}
	accountJSON(w, http.StatusOK, map[string]any{"status": "ok", "user": s.payload(user, p)})
}

type scoreEntry struct {
	Game       string `json:"game"`
	Score      *int   `json:"score"`
	Detail     string `json:"detail"`
	At         *int64 `json:"at"`
	Puzzle     string `json:"puzzle_key,omitempty"`
	Daily      string `json:"daily,omitempty"`
	Difficulty string `json:"difficulty,omitempty"`
	Category   string `json:"category,omitempty"`
}
type scoresBody struct {
	Entries []scoreEntry `json:"entries"`
}

func validGame(game string) bool {
	switch game {
	case "alchimie", "intrusul", "perechi", "conexiuni", "contexto", "lant":
		return true
	}
	return false
}

func (s *Service) validateScore(e *scoreEntry) string {
	if !validGame(e.Game) {
		return "game"
	}
	if e.Score == nil || *e.Score < 0 || *e.Score > 1000 {
		return "score"
	}
	if e.At == nil || *e.At < 946684800000 || *e.At > 4102444800000 {
		return "at"
	}
	if utf8.RuneCountInString(e.Detail) > 120 {
		return "detail"
	}
	e.Detail = cleanSpaces(e.Detail)
	if e.Detail == "" {
		return "detail"
	}
	if utf8.RuneCountInString(e.Puzzle) > 160 {
		return "puzzle_key"
	}
	e.Puzzle = strip(e.Puzzle)
	for _, char := range e.Puzzle {
		if char < 32 || char == 127 {
			return "puzzle_key"
		}
	}
	if utf8.RuneCountInString(e.Daily) > 10 {
		return "daily"
	}
	e.Daily = strip(e.Daily)
	if e.Daily != "" {
		parsed, err := time.Parse("2006-01-02", e.Daily)
		if err != nil || parsed.Format("2006-01-02") != e.Daily {
			return "daily"
		}
	}
	if utf8.RuneCountInString(e.Difficulty) > 20 {
		return "difficulty"
	}
	e.Difficulty = strip(e.Difficulty)
	if e.Difficulty != "" && e.Difficulty != "usor" && e.Difficulty != "normal" && e.Difficulty != "greu" {
		return "difficulty"
	}
	if utf8.RuneCountInString(e.Category) > 40 {
		return "category"
	}
	e.Category = strip(e.Category)
	if e.Category != "" && (s.config.CategoryAllowed == nil || !s.config.CategoryAllowed(e.Category)) {
		return "category"
	}
	return ""
}

func (s *Service) Scores(w http.ResponseWriter, r *http.Request) {
	_, id, ok := s.authenticated(w, r, r.Method == http.MethodPost)
	if !ok {
		return
	}
	if r.Method == http.MethodGet {
		p, err := s.profile(r.Context(), id)
		if err != nil {
			unavailable(w)
			return
		}
		if !p.canSave(s.config.ConsentVersion) {
			accountError(w, http.StatusForbidden, "Consent required before reading progress.")
			return
		}
		rows, err := s.pool.Query(r.Context(), "SELECT game,score,detail,at,puzzle_key,daily,difficulty,category FROM cat_native_scores WHERE user_id=$1 ORDER BY at DESC,id DESC LIMIT 500", id)
		if err != nil {
			unavailable(w)
			return
		}
		defer rows.Close()
		entries := []scoreEntry{}
		for rows.Next() {
			var e scoreEntry
			var score int
			var at int64
			if err = rows.Scan(&e.Game, &score, &e.Detail, &at, &e.Puzzle, &e.Daily, &e.Difficulty, &e.Category); err != nil {
				unavailable(w)
				return
			}
			e.Score = &score
			e.At = &at
			entries = append(entries, e)
		}
		if rows.Err() != nil {
			unavailable(w)
			return
		}
		accountJSON(w, http.StatusOK, map[string]any{"entries": entries})
		return
	}
	var body scoresBody
	if !s.decode(w, r, &body) {
		return
	}
	if body.Entries == nil || len(body.Entries) > 500 {
		validationError(w, "entries")
		return
	}
	for i := range body.Entries {
		if field := s.validateScore(&body.Entries[i]); field != "" {
			validationError(w, field)
			return
		}
	}
	tx, err := s.pool.Begin(r.Context())
	if err != nil {
		unavailable(w)
		return
	}
	defer tx.Rollback(r.Context())
	p, err := lockedProfile(r.Context(), tx, id)
	if err != nil {
		unavailable(w)
		return
	}
	if !p.canSave(s.config.ConsentVersion) {
		accountError(w, http.StatusForbidden, "Consent required before saving progress.")
		return
	}
	saved := int64(0)
	for _, e := range body.Entries {
		tag, err := tx.Exec(r.Context(), "INSERT INTO cat_native_scores(user_id,game,score,detail,at,puzzle_key,daily,difficulty,category) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9) ON CONFLICT(user_id,game,at,puzzle_key) DO NOTHING", id, e.Game, *e.Score, e.Detail, *e.At, e.Puzzle, e.Daily, e.Difficulty, e.Category)
		if err != nil {
			unavailable(w)
			return
		}
		saved += tag.RowsAffected()
	}
	if _, err = tx.Exec(r.Context(), "DELETE FROM cat_native_scores WHERE user_id=$1 AND id NOT IN (SELECT id FROM cat_native_scores WHERE user_id=$1 ORDER BY created DESC,id DESC LIMIT 500)", id); err != nil {
		unavailable(w)
		return
	}
	var total int
	if err = tx.QueryRow(r.Context(), "SELECT count(*) FROM cat_native_scores WHERE user_id=$1", id).Scan(&total); err != nil {
		unavailable(w)
		return
	}
	if err = tx.Commit(r.Context()); err != nil {
		unavailable(w)
		return
	}
	accountJSON(w, http.StatusOK, map[string]any{"saved": saved, "total": total})
}

func (s *Service) Delete(w http.ResponseWriter, r *http.Request) {
	_, id, ok := s.authenticated(w, r, true)
	if !ok {
		return
	}
	tx, err := s.pool.Begin(r.Context())
	if err != nil {
		unavailable(w)
		return
	}
	defer tx.Rollback(r.Context())
	if err = eraseLegacy(r.Context(), tx, id); err != nil {
		unavailable(w)
		return
	}
	if _, err = tx.Exec(r.Context(), "DELETE FROM cat_native_users WHERE id=$1", id); err != nil {
		unavailable(w)
		return
	}
	if err = tx.Commit(r.Context()); err != nil {
		unavailable(w)
		return
	}
	// The database cascade has already revoked every session; clear browser state.
	s.auth.ClearCookies(w)
	accountJSON(w, http.StatusOK, map[string]bool{"ok": true})
}

func (s *Service) Logout(w http.ResponseWriter, r *http.Request) {
	if _, _, ok := s.authenticated(w, r, true); !ok {
		return
	}
	if err := s.auth.RevokeSession(r); err != nil {
		unavailable(w)
		return
	}
	s.auth.ClearCookies(w)
	accountJSON(w, http.StatusOK, map[string]bool{"ok": true})
}

func (s *Service) Ranking(w http.ResponseWriter, r *http.Request) {
	game := strings.TrimSpace(r.URL.Query().Get("game"))
	if !validGame(game) {
		accountError(w, http.StatusBadRequest, "Alege unul dintre cele șase jocuri.")
		return
	}
	limit, err := strconv.Atoi(r.URL.Query().Get("limit"))
	if err != nil {
		limit = 50
	}
	if limit < 1 {
		limit = 1
	}
	if limit > 200 {
		limit = 200
	}
	var requester int64
	user, err := s.auth.Authenticate(r)
	if err == nil {
		requester, _ = userID(user.ID)
	} else if !errors.Is(err, authcore.ErrNotFound) {
		unavailable(w)
		return
	}
	query := `SELECT v.user_id,p.display_name,v.score FROM cat_native_verified v JOIN cat_native_profiles p ON p.user_id=v.user_id JOIN cat_native_users u ON u.id=v.user_id WHERE v.game=$1 AND p.consent_completed AND p.consent_version=$2 AND NOT p.is_minor AND NOT p.parental_consent_required AND p.show_on_ranking AND p.display_name<>'' AND u.active ORDER BY v.score DESC,v.user_id LIMIT $3`
	rows, err := s.pool.Query(r.Context(), query, game, s.config.ConsentVersion, limit)
	if err != nil {
		unavailable(w)
		return
	}
	defer rows.Close()
	entries := []map[string]any{}
	position, rank, previous := 0, 0, -1
	for rows.Next() {
		var id int64
		var name string
		var score int
		if err = rows.Scan(&id, &name, &score); err != nil {
			unavailable(w)
			return
		}
		position++
		if score != previous {
			rank = position
			previous = score
		}
		entries = append(entries, map[string]any{"rank": rank, "name": name, "score": score, "is_me": id == requester})
	}
	if rows.Err() != nil {
		unavailable(w)
		return
	}
	rows.Close()
	var me any = nil
	if requester > 0 {
		var score int
		var rank int64
		err = s.pool.QueryRow(r.Context(), `WITH eligible AS (SELECT v.user_id,v.score FROM cat_native_verified v JOIN cat_native_profiles p ON p.user_id=v.user_id JOIN cat_native_users u ON u.id=v.user_id WHERE v.game=$1 AND p.consent_completed AND p.consent_version=$2 AND NOT p.is_minor AND NOT p.parental_consent_required AND p.show_on_ranking AND p.display_name<>'' AND u.active) SELECT e.score,1+(SELECT count(*) FROM eligible WHERE score>e.score) FROM eligible e WHERE e.user_id=$3`, game, s.config.ConsentVersion, requester).Scan(&score, &rank)
		if err == nil {
			me = map[string]any{"rank": rank, "score": score}
		} else if !errors.Is(err, pgx.ErrNoRows) {
			unavailable(w)
			return
		}
	}
	accountJSON(w, http.StatusOK, map[string]any{"game": game, "entries": entries, "me": me})
}

func accountJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}
func accountError(w http.ResponseWriter, status int, detail string) {
	accountJSON(w, status, map[string]string{"detail": detail})
}
func unavailable(w http.ResponseWriter) {
	accountError(w, http.StatusServiceUnavailable, "Accounts temporarily unavailable.")
}
func methodError(w http.ResponseWriter, allow string) {
	w.Header().Set("Allow", allow)
	accountError(w, http.StatusMethodNotAllowed, "Method not allowed")
}
func validationError(w http.ResponseWriter, field string) {
	parts := strings.Split(field, ".")
	accountJSON(w, http.StatusUnprocessableEntity, map[string]any{"detail": []any{map[string]any{"loc": []string{"body", parts[len(parts)-1]}, "msg": "invalid value", "type": "value_error"}}})
}
