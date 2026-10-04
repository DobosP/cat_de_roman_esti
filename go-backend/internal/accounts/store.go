package accounts

import (
	"context"
	"crypto/rand"
	_ "embed"
	"encoding/json"
	"errors"
	"strconv"
	"time"

	"github.com/DobosP/cat_de_roman_esti/shared-go/authcore"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"
)

//go:embed schema.sql
var schema string

type Store struct{ pool *pgxpool.Pool }

func NewStore(pool *pgxpool.Pool) *Store { return &Store{pool: pool} }

// Migrate imports existing Django-owned records exactly once under a database
// lock. Legacy tables remain available for rollback; Go never calls Django.
func Migrate(ctx context.Context, pool *pgxpool.Pool) error {
	tx, err := pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, "SELECT pg_advisory_xact_lock(71309010162026)"); err != nil {
		return err
	}
	if _, err = tx.Exec(ctx, schema); err != nil {
		return err
	}
	var done bool
	if err = tx.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM cat_native_migrations WHERE name='django-import-v1')").Scan(&done); err != nil {
		return err
	}
	if !done {
		imports := []struct{ table, query string }{
			{"auth_user", `INSERT INTO cat_native_users(id,username,password_hash,email,name,active,created) SELECT id,username,password,email,left(trim(first_name || ' ' || last_name),150),is_active,date_joined FROM auth_user ON CONFLICT(id) DO NOTHING`},
			{"socialaccount_socialaccount", `UPDATE cat_native_users u SET name=left(COALESCE(NULLIF(s.extra_data::jsonb->>'name',''),u.name),150), email=left(COALESCE(NULLIF(u.email,''),s.extra_data::jsonb->>'email',''),254),avatar=COALESCE(s.extra_data::jsonb->>'picture','') FROM socialaccount_socialaccount s WHERE s.user_id=u.id AND s.provider='google'; INSERT INTO cat_native_external(provider,subject,user_id) SELECT provider,uid,user_id FROM socialaccount_socialaccount WHERE provider IN ('google','facebook') ON CONFLICT(provider,subject) DO NOTHING`},
			{"accounts_profile", `INSERT INTO cat_native_profiles(user_id,birth_year,consent_completed,consent_version,is_minor,parental_consent_required,display_name,show_on_ranking,created,updated) SELECT user_id,birth_year,consent_completed,consent_version,is_minor,parental_consent_required,display_name,show_on_ranking,created,updated FROM accounts_profile ON CONFLICT(user_id) DO NOTHING`},
			{"accounts_consentrecord", `INSERT INTO cat_native_consents(user_id,document,version,text_hash,accepted_at) SELECT user_id,document,version,text_hash,accepted_at FROM accounts_consentrecord`},
			{"accounts_scoreentry", `INSERT INTO cat_native_scores(user_id,game,score,detail,at,puzzle_key,daily,difficulty,category,created) SELECT user_id,game,score,detail,at,puzzle_key,daily,difficulty,category,created FROM accounts_scoreentry ON CONFLICT(user_id,game,at,puzzle_key) DO NOTHING`},
			{"accounts_verifiedbest", `INSERT INTO cat_native_verified(user_id,game,score,updated) SELECT user_id,game,score,updated FROM accounts_verifiedbest ON CONFLICT(user_id,game) DO NOTHING`},
			{"accounts_playedpuzzle", `INSERT INTO cat_native_played(user_id,game,pack_id,finished_at) SELECT user_id,game,pack_id,finished_at FROM accounts_playedpuzzle ON CONFLICT(user_id,game,pack_id) DO NOTHING`},
		}
		for _, item := range imports {
			var exists bool
			if err = tx.QueryRow(ctx, "SELECT to_regclass($1) IS NOT NULL", item.table).Scan(&exists); err != nil {
				return err
			}
			if exists {
				if _, err = tx.Exec(ctx, item.query); err != nil {
					return err
				}
			}
		}
		// Legacy Django session signatures cannot be verified by the native
		// opaque-token scheme. Retire them rather than retain encoded identities.
		var legacySessions bool
		if err = tx.QueryRow(ctx, "SELECT to_regclass('django_session') IS NOT NULL").Scan(&legacySessions); err != nil {
			return err
		}
		if legacySessions {
			if _, err = tx.Exec(ctx, "DELETE FROM django_session"); err != nil {
				return err
			}
		}
		if _, err = tx.Exec(ctx, `INSERT INTO cat_native_profiles(user_id) SELECT id FROM cat_native_users ON CONFLICT(user_id) DO NOTHING; SELECT setval(pg_get_serial_sequence('cat_native_users','id'),GREATEST(COALESCE((SELECT max(id) FROM cat_native_users),0),1),(SELECT EXISTS(SELECT 1 FROM cat_native_users))); INSERT INTO cat_native_migrations(name) VALUES('django-import-v1')`); err != nil {
			return err
		}
	}
	return tx.Commit(ctx)
}

func userID(raw string) (int64, error) {
	id, err := strconv.ParseInt(raw, 10, 64)
	if err != nil || id < 1 {
		return 0, authcore.ErrNotFound
	}
	return id, nil
}
func randomIdentifier() string { return rand.Text() }

func storeError(err error) error {
	if errors.Is(err, pgx.ErrNoRows) {
		return authcore.ErrNotFound
	}
	var postgres *pgconn.PgError
	if errors.As(err, &postgres) && postgres.Code == "23505" {
		return authcore.ErrConflict
	}
	return err
}

func scanUser(row pgx.Row) (authcore.User, error) {
	var user authcore.User
	var id int64
	err := row.Scan(&id, &user.Username, &user.Email, &user.Name, &user.Avatar)
	user.ID = strconv.FormatInt(id, 10)
	return user, storeError(err)
}

func (s *Store) FindByUsername(ctx context.Context, name string) (authcore.User, string, error) {
	var user authcore.User
	var id int64
	var hash string
	err := s.pool.QueryRow(ctx, "SELECT id,username,email,name,avatar,password_hash FROM cat_native_users WHERE username=$1 AND active", name).Scan(&id, &user.Username, &user.Email, &user.Name, &user.Avatar, &hash)
	user.ID = strconv.FormatInt(id, 10)
	return user, hash, storeError(err)
}

func (s *Store) CreatePasswordUser(ctx context.Context, user authcore.User, hash string) (authcore.User, error) {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return authcore.User{}, err
	}
	defer tx.Rollback(ctx)
	user, err = scanUser(tx.QueryRow(ctx, "INSERT INTO cat_native_users(username,password_hash,email,name) VALUES($1,$2,$3,$4) RETURNING id,username,email,name,avatar", user.Username, hash, user.Email, user.Name))
	if err != nil {
		return authcore.User{}, err
	}
	id, _ := userID(user.ID)
	if _, err = tx.Exec(ctx, "INSERT INTO cat_native_profiles(user_id) VALUES($1)", id); err != nil {
		return authcore.User{}, err
	}
	return user, tx.Commit(ctx)
}

func (s *Store) FindOrCreateExternal(ctx context.Context, provider, subject string, profile authcore.User) (authcore.User, error) {
	if (provider != "google" && provider != "facebook") || subject == "" || len(subject) > 255 {
		return authcore.User{}, authcore.ErrNotFound
	}
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return authcore.User{}, err
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, "SELECT pg_advisory_xact_lock(hashtextextended($1,0))", provider+":"+subject); err != nil {
		return authcore.User{}, err
	}
	user, err := scanUser(tx.QueryRow(ctx, "SELECT u.id,u.username,u.email,u.name,u.avatar FROM cat_native_external e JOIN cat_native_users u ON u.id=e.user_id WHERE e.provider=$1 AND e.subject=$2 AND u.active", provider, subject))
	if err == nil {
		return user, tx.Commit(ctx)
	}
	if !errors.Is(err, authcore.ErrNotFound) {
		return authcore.User{}, err
	}
	// If an identity belongs to a disabled account, never create a replacement.
	var exists bool
	if err = tx.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM cat_native_external WHERE provider=$1 AND subject=$2)", provider, subject).Scan(&exists); err != nil {
		return authcore.User{}, err
	}
	if exists {
		return authcore.User{}, authcore.ErrNotFound
	}
	profile.Username = "oauth_" + provider + "_" + randomIdentifier()
	user, err = scanUser(tx.QueryRow(ctx, "INSERT INTO cat_native_users(username,email,name) VALUES($1,$2,$3) RETURNING id,username,email,name,avatar", profile.Username, profile.Email, profile.Name))
	if err != nil {
		return authcore.User{}, err
	}
	id, _ := userID(user.ID)
	if _, err = tx.Exec(ctx, "INSERT INTO cat_native_external(provider,subject,user_id) VALUES($1,$2,$3)", provider, subject, id); err != nil {
		return authcore.User{}, err
	}
	if _, err = tx.Exec(ctx, "INSERT INTO cat_native_profiles(user_id) VALUES($1)", id); err != nil {
		return authcore.User{}, err
	}
	return user, tx.Commit(ctx)
}

func (s *Store) CreateSession(ctx context.Context, session authcore.Session) error {
	id, err := userID(session.UserID)
	if err != nil {
		return err
	}
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	var locked int64
	if err = tx.QueryRow(ctx, "SELECT id FROM cat_native_users WHERE id=$1 AND active FOR UPDATE", id).Scan(&locked); err != nil {
		return storeError(err)
	}
	if _, err = tx.Exec(ctx, "DELETE FROM cat_native_sessions WHERE expires_at<=now()"); err != nil {
		return err
	}
	if _, err = tx.Exec(ctx, "INSERT INTO cat_native_sessions(token_hash,user_id,expires_at) VALUES($1,$2,$3)", session.TokenHash, id, session.ExpiresAt); err != nil {
		return err
	}
	if _, err = tx.Exec(ctx, "DELETE FROM cat_native_sessions WHERE user_id=$1 AND token_hash NOT IN (SELECT token_hash FROM cat_native_sessions WHERE user_id=$1 ORDER BY created DESC,token_hash DESC LIMIT 10)", id); err != nil {
		return err
	}
	return tx.Commit(ctx)
}

func (s *Store) GetSession(ctx context.Context, hash string, now time.Time) (authcore.User, error) {
	return scanUser(s.pool.QueryRow(ctx, "SELECT u.id,u.username,u.email,u.name,u.avatar FROM cat_native_sessions s JOIN cat_native_users u ON u.id=s.user_id WHERE s.token_hash=$1 AND s.expires_at>$2 AND u.active", hash, now))
}
func (s *Store) DeleteSession(ctx context.Context, hash string) error {
	_, err := s.pool.Exec(ctx, "DELETE FROM cat_native_sessions WHERE token_hash=$1", hash)
	return err
}

func (s *Store) CreateOAuthFlow(ctx context.Context, hash string, flow authcore.OAuthFlow) error {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, "SELECT pg_advisory_xact_lock(71309010162027)"); err != nil {
		return err
	}
	if _, err = tx.Exec(ctx, "DELETE FROM cat_native_oauth_flows WHERE expires_at<=now()"); err != nil {
		return err
	}
	var count int
	if err = tx.QueryRow(ctx, "SELECT count(*) FROM cat_native_oauth_flows").Scan(&count); err != nil {
		return err
	}
	if count >= 1024 {
		return authcore.ErrConflict
	}
	encoded, err := json.Marshal(flow)
	if err != nil {
		return err
	}
	if _, err = tx.Exec(ctx, "INSERT INTO cat_native_oauth_flows(state_hash,flow,expires_at) VALUES($1,$2,$3)", hash, encoded, flow.ExpiresAt); err != nil {
		return err
	}
	return tx.Commit(ctx)
}

func (s *Store) ConsumeOAuthFlow(ctx context.Context, hash string, now time.Time) (authcore.OAuthFlow, error) {
	var encoded []byte
	var expires time.Time
	var flow authcore.OAuthFlow
	err := s.pool.QueryRow(ctx, "DELETE FROM cat_native_oauth_flows WHERE state_hash=$1 RETURNING flow,expires_at", hash).Scan(&encoded, &expires)
	if err != nil {
		return flow, storeError(err)
	}
	if !expires.After(now) {
		return flow, authcore.ErrNotFound
	}
	if err = json.Unmarshal(encoded, &flow); err != nil {
		return flow, err
	}
	return flow, nil
}

func (s *Store) AllowAuthAttempt(ctx context.Context, key string, now time.Time) (bool, error) {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return false, err
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, "SELECT pg_advisory_xact_lock(71309010162028)"); err != nil {
		return false, err
	}
	if _, err = tx.Exec(ctx, "DELETE FROM cat_native_auth_attempts WHERE until<=$1", now); err != nil {
		return false, err
	}
	var count int
	if err = tx.QueryRow(ctx, "SELECT count(*) FROM cat_native_auth_attempts").Scan(&count); err != nil {
		return false, err
	}
	if count >= 4096 {
		var found bool
		if err = tx.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM cat_native_auth_attempts WHERE key_hash=$1)", key).Scan(&found); err != nil {
			return false, err
		}
		if !found {
			return false, nil
		}
	}
	var attempts int
	if err = tx.QueryRow(ctx, "INSERT INTO cat_native_auth_attempts(key_hash,count,until) VALUES($1,1,$2) ON CONFLICT(key_hash) DO UPDATE SET count=cat_native_auth_attempts.count+1 RETURNING count", key, now.Add(time.Minute)).Scan(&attempts); err != nil {
		return false, err
	}
	if err = tx.Commit(ctx); err != nil {
		return false, err
	}
	return attempts <= 10, nil
}

var _ authcore.Store = (*Store)(nil)
var _ authcore.OAuthFlowStore = (*Store)(nil)
var _ authcore.AuthAttemptStore = (*Store)(nil)
