package httpapi

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/boardstats"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
)

type boardHTTPReply struct {
	GameID string            `json:"game_id"`
	Won    bool              `json:"won"`
	Place  *boardstats.Place `json:"place"`
}

func boardCompareRequest(t *testing.T, s *Server, method, path, body string) boardHTTPReply {
	t.Helper()
	req := httptest.NewRequest(method, "http://localhost"+path, strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	s.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("%s %s: status %d", method, path, w.Code)
	}
	var result boardHTTPReply
	if err := json.Unmarshal(w.Body.Bytes(), &result); err != nil {
		t.Fatal(err)
	}
	return result
}

func finishComparisonBoard(t *testing.T, s *Server, day string) boardHTTPReply {
	t.Helper()
	const base = "/api/wordgames/intrusul/games"
	board := catalog.New(s.content).PickDaily("intrusul", day, "")
	if board == nil {
		t.Fatalf("no reviewed Intrusul board for %s", day)
	}
	start := boardCompareRequest(t, s, http.MethodPost, base+"?daily="+day, "")
	argument, _ := json.Marshal(map[string]any{"id": board.Payload["intruder"]})
	final := boardCompareRequest(t, s, http.MethodPost, base+"/"+start.GameID+"/guess", string(argument))
	if !final.Won {
		t.Fatal("answer for the reviewed daily board must win")
	}
	return final
}

func TestBoardComparisonThresholdAndSingleTerminalSample(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	s := New(c)
	const day = "2026-11-16"
	now := func() time.Time { return time.Date(2026, 11, 16, 12, 0, 0, 0, time.UTC) }

	off := finishComparisonBoard(t, s, day)
	if off.Place != nil {
		t.Fatal("place leaked while the feature was off")
	}

	store, err := boardstats.Open(t.TempDir(), boardstats.Options{Now: now})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := store.Close(); err != nil {
			t.Error(err)
		}
	})
	s.EnableBoardComparison(store, now)
	key := boardstats.Key{
		RulesVersion: gameapi.RulesVersion, ContentDigest: s.boardComparison.digest,
		Day: day, Game: "intrusul", BoardID: catalog.New(c).PickDaily("intrusul", day, "").CatalogID,
	}
	for i := 0; i < 98; i++ {
		if err := store.Record(key, boardstats.Loss, 3); err != nil {
			t.Fatal(err)
		}
	}
	beforeEnablePath := "/api/wordgames/intrusul/games/" + off.GameID
	head := httptest.NewRecorder()
	s.ServeHTTP(head, httptest.NewRequest(http.MethodHead, "http://localhost"+beforeEnablePath, nil))
	if head.Code != http.StatusOK || head.Body.Len() != 0 {
		t.Fatalf("HEAD returned status %d and %d bytes", head.Code, head.Body.Len())
	}

	final := finishComparisonBoard(t, s, day)
	if final.Place != nil {
		t.Fatal("99 completed rounds are below the display threshold")
	}
	if err := store.Record(key, boardstats.GiveUp, 0); err != nil {
		t.Fatal(err)
	}
	path := "/api/wordgames/intrusul/games/" + final.GameID
	for i := 0; i < 3; i++ {
		replay := boardCompareRequest(t, s, http.MethodGet, path, "")
		if replay.Place == nil || replay.Place.Rounds != 100 || replay.Place.BetterThanPct != 99 {
			t.Fatalf("unexpected place or repeat contribution: %+v", replay.Place)
		}
	}
}

func TestBoardComparisonDateWindow(t *testing.T) {
	now := time.Date(2026, 11, 16, 12, 0, 0, 0, time.UTC)
	for day, eligible := range map[string]bool{
		"2026-11-14": false, "2026-11-15": true, "2026-11-16": true, "2026-11-17": false, "bad": false,
	} {
		if boardComparisonDay(now, day) != eligible {
			t.Fatalf("date %q eligibility differs", day)
		}
	}
}
