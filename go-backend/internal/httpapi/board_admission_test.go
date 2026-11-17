package httpapi

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"net/netip"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/boardstats"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
)

func admissionServer(t *testing.T) (*Server, *boardstats.Store, string, boardstats.Key) {
	t.Helper()
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	s := New(c)
	now := func() time.Time { return time.Date(2026, 11, 17, 12, 0, 0, 0, time.UTC) }
	dir := t.TempDir()
	store, err := boardstats.Open(dir, boardstats.Options{Now: now})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = store.Close() })
	s.EnableBoardComparison(store, now)
	board := catalog.New(c).PickDaily("intrusul", "2026-11-17", "")
	if board == nil {
		t.Fatal("expected reviewed daily board")
	}
	key := boardstats.Key{RulesVersion: gameapi.RulesVersion, ContentDigest: s.boardComparison.digest,
		Day: "2026-11-17", Game: "intrusul", BoardID: board.CatalogID}
	return s, store, dir, key
}

func seedAdmissionLosses(t *testing.T, store *boardstats.Store, key boardstats.Key) {
	t.Helper()
	for range 100 {
		if err := store.Record(key, boardstats.Loss, 0); err != nil {
			t.Fatal(err)
		}
	}
}

// Adapted from the review's TestCriticPctHundred. A terminal result must not
// obtain a comparison until its own sample has been admitted.
func TestBoardPlaceRequiresOwnAdmittedSample(t *testing.T) {
	for _, refusal := range []string{"limiter", "capacity", "snapshot-read", "closed"} {
		t.Run(refusal, func(t *testing.T) {
			s, store, dir, key := admissionServer(t)
			if refusal == "snapshot-read" {
				// A non-regular retained path is a real snapshot read failure.
				if err := os.Mkdir(filepath.Join(dir, "boardstats-"+key.Day+".json"), 0700); err != nil {
					t.Fatal(err)
				}
			} else {
				seedAdmissionLosses(t, store, key)
			}
			switch refusal {
			case "limiter":
				address := netip.MustParseAddr("192.0.2.9")
				for range roundLimit {
					if !s.boardComparison.limiter.allow(address, time.Now()) {
						t.Fatal("limiter exhausted before its declared limit")
					}
				}
			case "capacity":
				// Fill the per-board histogram without the winner's zero-step bucket.
				for steps := 1; ; steps++ {
					err := store.Record(key, boardstats.Win, steps)
					if err == boardstats.ErrCapacity {
						break
					}
					if err != nil || steps > 16384 {
						t.Fatalf("fill histogram: steps=%d error=%v", steps, err)
					}
				}
			case "closed":
				if err := store.Close(); err != nil {
					t.Fatal(err)
				}
			}
			base := "/api/wordgames/intrusul/games"
			start := boardCompareRequest(t, s, http.MethodPost, base+"?daily="+key.Day, "")
			board := catalog.New(s.content).PickDaily("intrusul", key.Day, "")
			arg, _ := json.Marshal(map[string]any{"id": board.Payload["intruder"]})
			path := base + "/" + start.GameID
			req := httptest.NewRequest(http.MethodPost, "http://localhost"+path+"/guess", nil)
			req.RemoteAddr = "192.0.2.9:443"
			// Keep the same request helper's JSON transport while choosing the client.
			response := admissionRequest(t, s, req, arg)
			if !response.Won || response.Place != nil {
				t.Fatalf("unadmitted winner received comparison: %+v", response)
			}
			// A fresh IP on a later read cannot turn a refused sample into placement.
			read := boardCompareRequest(t, s, http.MethodGet, path, "")
			if read.Place != nil {
				t.Fatalf("unadmitted saved winner received comparison: %+v", read.Place)
			}
		})
	}
}

func admissionRequest(t *testing.T, s *Server, req *http.Request, body []byte) boardHTTPReply {
	t.Helper()
	req.Body = http.NoBody
	if len(body) != 0 {
		req.Body = io.NopCloser(bytes.NewReader(body))
		req.ContentLength = int64(len(body))
	}
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	s.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("admission request returned %d: %s", w.Code, w.Body.String())
	}
	var reply boardHTTPReply
	if err := json.Unmarshal(w.Body.Bytes(), &reply); err != nil {
		t.Fatal(err)
	}
	return reply
}
