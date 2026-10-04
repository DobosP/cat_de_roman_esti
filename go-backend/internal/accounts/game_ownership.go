package accounts

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"time"

	"github.com/DobosP/cat_de_roman_esti/shared-go/authcore"
	"github.com/jackc/pgx/v5"
)

var ErrGamePrivate = errors.New("game is not accessible")
var ErrGameCapacity = errors.New("account game ownership capacity reached")

const maxOwnedGames = 6000

func gameDigest(game, id string) (string, error) {
	if !validGame(game) || len(id) != 36 {
		return "", ErrGamePrivate
	}
	for i, c := range id {
		if i == 8 || i == 13 || i == 18 || i == 23 {
			if c != '-' {
				return "", ErrGamePrivate
			}
		} else if !(c >= '0' && c <= '9' || c >= 'a' && c <= 'f') {
			return "", ErrGamePrivate
		}
	}
	sum := sha256.Sum256([]byte(game + ":" + id))
	return hex.EncodeToString(sum[:]), nil
}

// GameAccess holds a database lock across authorization and the game operation.
// This serializes a first authenticated claim against anonymous requests and
// other claimants before either can inspect, mutate or credit an owned session.
// Erasure removes the owner FK but leaves a short-lived anonymous seal, which
// prevents a still-live game from being credited to someone else.
func (s *Service) GameAccess(ctx context.Context, user, game, id string, claim bool, ttl time.Duration, known func() bool, action func(bool, pgx.Tx) error) error {
	digest, err := gameDigest(game, id)
	if err != nil {
		return err
	}
	if ttl < time.Minute || ttl > 365*24*time.Hour {
		return errors.New("invalid ownership lifetime")
	}
	var actor int64
	if user != "" {
		actor, err = userID(user)
		if err != nil {
			return ErrGamePrivate
		}
	}
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	if _, err = tx.Exec(ctx, `SET LOCAL statement_timeout='5s'`); err != nil {
		return err
	}
	if actor > 0 {
		var active bool
		if err = tx.QueryRow(ctx, `SELECT active FROM cat_native_users WHERE id=$1 FOR KEY SHARE`, actor).Scan(&active); err != nil {
			return ErrGamePrivate
		}
		if !active {
			return ErrGamePrivate
		}
	}
	if _, err = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(hashtextextended($1,0))`, digest); err != nil {
		return err
	}
	var owner *int64
	var expires time.Time
	err = tx.QueryRow(ctx, `SELECT user_id,expires_at FROM cat_native_game_owners WHERE game=$1 AND game_hash=$2`, game, digest).Scan(&owner, &expires)
	owned := false
	now := time.Now()
	if err == nil {
		if owner == nil || actor == 0 || *owner != actor {
			return ErrGamePrivate
		}
		if known == nil || !known() {
			return ErrGamePrivate
		}

		owned = true
	} else if !errors.Is(err, pgx.ErrNoRows) {
		return err
	} else if actor > 0 && claim {
		if known == nil || !known() {
			return ErrGamePrivate
		}
		if _, err = tx.Exec(ctx, `SELECT pg_advisory_xact_lock(7130901042026)`); err != nil {
			return err
		}
		if _, err = tx.Exec(ctx, `DELETE FROM cat_native_game_owners WHERE expires_at<$1`, now); err != nil {
			return err
		}
		var count int
		if err = tx.QueryRow(ctx, `SELECT count(*) FROM cat_native_game_owners`).Scan(&count); err != nil {
			return err
		}
		if count >= maxOwnedGames {
			return ErrGameCapacity
		}
		var active bool
		if err = tx.QueryRow(ctx, `SELECT active FROM cat_native_users WHERE id=$1`, actor).Scan(&active); err != nil || !active {
			if err == nil {
				err = ErrGamePrivate
			}
			return err
		}
		if _, err = tx.Exec(ctx, `INSERT INTO cat_native_game_owners(game,game_hash,user_id,expires_at) VALUES($1,$2,$3,$4)`, game, digest, actor, now.Add(ttl)); err != nil {
			return err
		}
		owned = true
	}
	if owned {
		var active bool
		if err = tx.QueryRow(ctx, `SELECT active FROM cat_native_users WHERE id=$1`, actor).Scan(&active); err != nil {
			return err
		}
		if !active {
			return ErrGamePrivate
		}
	}
	if err = action(owned, tx); err != nil {
		return err
	}
	if owned {
		if _, err = tx.Exec(ctx, `UPDATE cat_native_game_owners SET expires_at=$3 WHERE game=$1 AND game_hash=$2`, game, digest, now.Add(ttl)); err != nil {
			return err
		}
	}
	return tx.Commit(ctx)
}

// RecordOwnedTerminal commits the server result in the ownership transaction;
// client score-upload endpoints never call it. Private finished keys and public
// verified bests remain consent-gated and self-scoped.
func (s *Service) RecordOwnedTerminal(ctx context.Context, tx pgx.Tx, user, game, id, curated string, score int) error {
	actor, err := userID(user)
	if err != nil {
		return err
	}
	digest, err := gameDigest(game, id)
	if err != nil {
		return err
	}
	var owner *int64
	if err = tx.QueryRow(ctx, `SELECT user_id FROM cat_native_game_owners WHERE game=$1 AND game_hash=$2`, game, digest).Scan(&owner); err != nil {
		return err
	}
	if owner == nil || *owner != actor {
		return ErrGamePrivate
	}
	p, err := lockedProfile(ctx, tx, actor)
	if errors.Is(err, pgx.ErrNoRows) {
		return authcore.ErrNotFound
	}
	if err != nil {
		return err
	}
	if !p.canSave(s.config.ConsentVersion) {
		return nil
	}
	if curated != "" {
		if len(curated) > 64 {
			return fmt.Errorf("invalid curated identity")
		}
		if _, err = tx.Exec(ctx, `INSERT INTO cat_native_played(user_id,game,pack_id) VALUES($1,$2,$3) ON CONFLICT(user_id,game,pack_id) DO NOTHING`, actor, game, curated); err != nil {
			return err
		}
	}
	if score >= 0 {
		if score > 1000 {
			return errors.New("invalid server result")
		}
		if _, err = tx.Exec(ctx, `INSERT INTO cat_native_verified(user_id,game,score) VALUES($1,$2,$3) ON CONFLICT(user_id,game) DO UPDATE SET score=EXCLUDED.score,updated=now() WHERE cat_native_verified.score<EXCLUDED.score`, actor, game, score); err != nil {
			return err
		}
	}
	return nil
}
