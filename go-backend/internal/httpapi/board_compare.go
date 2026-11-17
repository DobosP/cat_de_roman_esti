package httpapi

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/boardstats"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
)

type boardComparison struct {
	stats   *boardstats.Store
	digest  string
	now     func() time.Time
	limiter boardRoundLimiter
}

// EnableBoardComparison is called during startup with an open aggregate store.
func (s *Server) EnableBoardComparison(store *boardstats.Store, now func() time.Time) {
	if store == nil {
		return
	}
	if now == nil {
		now = time.Now
	}
	// All sealed source digests distinguish a new board catalog or ranking
	// from the same graph paired with different curated content.
	source, _ := json.Marshal(s.content.Sources)
	sum := sha256.Sum256(source)
	s.boardComparison = &boardComparison{
		stats: store, digest: hex.EncodeToString(sum[:]), now: now,
	}
	s.lant.EnableBoardGiveUp(func(day string) bool { return boardComparisonDay(now(), day) })
}

func boardComparisonDay(now time.Time, day string) bool {
	return day == now.Format(time.DateOnly) || day == now.AddDate(0, 0, -1).Format(time.DateOnly)
}

func boardStatsOutcome(outcome gameapi.TerminalOutcome) (boardstats.Outcome, bool) {
	switch outcome {
	case gameapi.TerminalWin:
		return boardstats.Win, true
	case gameapi.TerminalLoss:
		return boardstats.Loss, true
	case gameapi.TerminalGiveUp:
		return boardstats.GiveUp, true
	default:
		return 0, false
	}
}

func (s *Server) boardResponse(r *http.Request, game string) gameapi.TerminalResponse {
	c := s.boardComparison
	if c == nil || r.Method == http.MethodHead {
		return nil
	}
	return c.response(r, game, func(day string) bool { return boardComparisonDay(c.now(), day) })
}

func (c *boardComparison) requestDateWindow() func(string) bool {
	// The give-up action and terminal observer first use this clock while
	// holding the session lock. Both use that reading across midnight.
	now := sync.OnceValue(c.now)
	return func(day string) bool { return boardComparisonDay(now(), day) }
}

func (c *boardComparison) response(r *http.Request, game string, eligibleDay func(string) bool) gameapi.TerminalResponse {
	return func(body map[string]any, round gameapi.TerminalRound, first, admitted bool) bool {
		if !eligibleDay(round.Day) {
			return admitted
		}
		key := boardstats.Key{
			RulesVersion: gameapi.RulesVersion, ContentDigest: c.digest,
			Day: round.Day, Game: game, BoardID: round.BoardID,
		}
		if outcome, known := boardStatsOutcome(round.Outcome); first && known &&
			c.limiter.allow(boardClientAddress(r), time.Now()) {
			if err := c.stats.Record(key, outcome, round.Steps); err != nil {
				log.Printf("board comparison record: %v", err)
			} else {
				admitted = true
			}
		}
		if !admitted || round.Outcome != gameapi.TerminalWin || body["won"] != true || body["steps"] != round.Steps {
			return admitted
		}
		if place, show := c.stats.Place(key, round.Steps); show {
			body["place"] = place
		}
		return admitted
	}
}
