package accounts

import (
	"context"
	"errors"
	"strings"

	"github.com/jackc/pgx/v5"
)

// Finished excludes only stable curated ids, never mined keys or answers.
func (s *Service) Finished(ctx context.Context, user, game string) (map[string]bool, error) {
	result := map[string]bool{}
	if !validGame(game) {
		return result, errors.New("unsupported game")
	}
	id, err := userID(user)
	if err != nil {
		return result, err
	}
	p, err := s.profile(ctx, id)
	if err != nil {
		return result, err
	}
	if !p.canSave(s.config.ConsentVersion) {
		return result, nil
	}
	rows, err := s.pool.Query(ctx, "SELECT pack_id FROM cat_native_played WHERE user_id=$1 AND game=$2", id, game)
	if err != nil {
		return result, err
	}
	defer rows.Close()
	for rows.Next() {
		var pack string
		if err = rows.Scan(&pack); err != nil {
			return result, err
		}
		result[pack] = true
	}
	return result, rows.Err()
}

func (s *Service) RecordPlayed(ctx context.Context, user, game, packID string) error {
	if !validGame(game) || packID == "" || len(packID) > 64 || strings.ContainsAny(packID, "\r\n\x00") {
		return errors.New("invalid curated puzzle identity")
	}
	id, err := userID(user)
	if err != nil {
		return err
	}
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	p, err := lockedProfile(ctx, tx, id)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil
	}
	if err != nil {
		return err
	}
	if !p.canSave(s.config.ConsentVersion) {
		return nil
	}
	if _, err = tx.Exec(ctx, "INSERT INTO cat_native_played(user_id,game,pack_id) VALUES($1,$2,$3) ON CONFLICT(user_id,game,pack_id) DO NOTHING", id, game, packID); err != nil {
		return err
	}
	return tx.Commit(ctx)
}

// RecordVerifiedBest accepts only a server-derived terminal result. HTTP score
// upload handlers never call this method or write the public ranking table.
func (s *Service) RecordVerifiedBest(ctx context.Context, user, game string, score int) error {
	if !validGame(game) || score < 0 || score > 1000 {
		return errors.New("invalid verified game or score")
	}
	id, err := userID(user)
	if err != nil {
		return err
	}
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	p, err := lockedProfile(ctx, tx, id)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil
	}
	if err != nil {
		return err
	}
	if !p.canSave(s.config.ConsentVersion) {
		return nil
	}
	if _, err = tx.Exec(ctx, "INSERT INTO cat_native_verified(user_id,game,score) VALUES($1,$2,$3) ON CONFLICT(user_id,game) DO UPDATE SET score=EXCLUDED.score,updated=now() WHERE cat_native_verified.score<EXCLUDED.score", id, game, score); err != nil {
		return err
	}
	return tx.Commit(ctx)
}

// Erase both imported native rows and any rollback-era copies of this user's
// account. Identifiers below are fixed schema names, never caller input.
func eraseLegacy(ctx context.Context, tx pgx.Tx, id int64) error {
	queries := []struct{ table, query string }{
		{"socialaccount_socialtoken", `DELETE FROM socialaccount_socialtoken WHERE account_id IN (SELECT id FROM socialaccount_socialaccount WHERE user_id=$1)`},
		{"account_emailconfirmation", `DELETE FROM account_emailconfirmation WHERE email_address_id IN (SELECT id FROM account_emailaddress WHERE user_id=$1)`},
		{"accounts_profile", `DELETE FROM accounts_profile WHERE user_id=$1`},
		{"accounts_consentrecord", `DELETE FROM accounts_consentrecord WHERE user_id=$1`},
		{"accounts_scoreentry", `DELETE FROM accounts_scoreentry WHERE user_id=$1`},
		{"accounts_verifiedbest", `DELETE FROM accounts_verifiedbest WHERE user_id=$1`},
		{"accounts_playedpuzzle", `DELETE FROM accounts_playedpuzzle WHERE user_id=$1`},
		{"socialaccount_socialaccount", `DELETE FROM socialaccount_socialaccount WHERE user_id=$1`},
		{"account_emailaddress", `DELETE FROM account_emailaddress WHERE user_id=$1`},
		{"auth_user_groups", `DELETE FROM auth_user_groups WHERE user_id=$1`},
		{"auth_user_user_permissions", `DELETE FROM auth_user_user_permissions WHERE user_id=$1`},
		{"django_admin_log", `DELETE FROM django_admin_log WHERE user_id=$1`},
		{"auth_user", `DELETE FROM auth_user WHERE id=$1`},
	}
	for _, item := range queries {
		var exists bool
		if err := tx.QueryRow(ctx, "SELECT to_regclass($1) IS NOT NULL", item.table).Scan(&exists); err != nil {
			return err
		}
		if exists {
			if _, err := tx.Exec(ctx, item.query, id); err != nil {
				return err
			}
		}
	}
	return nil
}
