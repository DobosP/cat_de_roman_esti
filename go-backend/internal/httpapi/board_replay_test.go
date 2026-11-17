package httpapi_test

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/boardstats"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/browserplan"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pack"
)

// Adapts the supplied review's all-six terminal journey without adding private
// solution accessors to production game services.
func TestDailyReplayNeverContributesOrReceivesPlace(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	sources, err := json.Marshal(c.Sources)
	if err != nil {
		t.Fatal(err)
	}
	digest := sha256.Sum256(sources)
	const day = "2026-11-17"
	for _, game := range browserplan.Games {
		t.Run(game, func(t *testing.T) {
			s := httpapi.New(c)
			now := func() time.Time { return time.Date(2026, 11, 17, 12, 0, 0, 0, time.UTC) }
			store, err := boardstats.Open(t.TempDir(), boardstats.Options{Now: now})
			if err != nil {
				t.Fatal(err)
			}
			t.Cleanup(func() { _ = store.Close() })
			s.EnableBoardComparison(store, now)
			boardID := ""
			if game == "intrusul" || game == "perechi" {
				board := catalog.New(c).PickDaily(game, day, "")
				if board != nil {
					boardID = board.CatalogID
				}
			} else {
				board := pack.New(c).PickDaily(game, day, pack.PickOptions{Difficulty: "usor", FilteredShelfWeights: game == "contexto"})
				if board != nil {
					boardID = board.ID
				}
			}
			if boardID == "" {
				t.Fatal("expected reviewed daily board")
			}
			key := boardstats.Key{RulesVersion: gameapi.RulesVersion, ContentDigest: hex.EncodeToString(digest[:]),
				Day: day, Game: game, BoardID: boardID}
			for range 100 {
				if err := store.Record(key, boardstats.Loss, 0); err != nil {
					t.Fatal(err)
				}
			}
			plan, err := browserplan.Solution(c, game, "", day)
			if err != nil {
				t.Fatal(err)
			}
			call := func(method, path string, payload any) map[string]any {
				t.Helper()
				raw, err := json.Marshal(payload)
				if err != nil {
					t.Fatal(err)
				}
				req := httptest.NewRequest(method, "http://localhost"+path, strings.NewReader(string(raw)))
				req.Header.Set("Content-Type", "application/json")
				w := httptest.NewRecorder()
				s.ServeHTTP(w, req)
				if w.Code != 200 {
					t.Fatalf("%s %s: %d %s", method, path, w.Code, w.Body.String())
				}
				var body map[string]any
				if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
					t.Fatal(err)
				}
				return body
			}
			base := "/api/wordgames/" + game + "/games"
			for _, replay := range []bool{true, false} {
				flag := "false"
				if replay {
					flag = "true"
				}
				state := call(http.MethodPost, base+"?daily="+day+"&replay="+flag, nil)
				path := base + "/" + state["game_id"].(string)
				for _, step := range plan.Steps {
					state = call(http.MethodPost, path+"/"+step.Action, step.Payload)
				}
				if state["won"] != true {
					t.Fatal("private daily journey did not finish")
				}
				for _, response := range []map[string]any{state, call(http.MethodGet, path, nil)} {
					if (response["place"] == nil) != replay {
						t.Fatalf("replay=%t: unexpected place %+v", replay, response["place"])
					}
				}
				place, shown := store.Place(key, 0)
				expected := uint64(101)
				if replay {
					expected = 100
				}
				if !shown || place.Rounds != expected {
					t.Fatalf("replay=%t aggregate=%+v, expected %d rounds", replay, place, expected)
				}
			}
		})
	}
}
