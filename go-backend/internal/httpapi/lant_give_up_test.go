package httpapi

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/boardstats"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
)

func lantGiveUpRequest(t *testing.T, s *Server, method, path, body string, wantStatus int) map[string]any {
	t.Helper()
	r := httptest.NewRequest(method, "http://localhost"+path, strings.NewReader(body))
	r.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != wantStatus {
		t.Fatalf("%s %s: status %d wanted %d, response %s", method, path, w.Code, wantStatus, w.Body)
	}
	var result map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &result); err != nil {
		t.Fatal(err)
	}
	return result
}

func TestLantGiveUpHTTPReceiptAndOneAggregateSample(t *testing.T) {
	const games = "/api/wordgames/lant/games"
	const day = "2026-11-16"
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	s := New(c)
	start := func(query string) (map[string]any, string) {
		body := lantGiveUpRequest(t, s, http.MethodPost, games+query, "", http.StatusOK)
		return body, games + "/" + body["game_id"].(string)
	}

	first, unavailable := start("?daily=" + day)
	if _, present := first["can_report_give_up"]; present {
		t.Fatal("disabled feature advertised give-up")
	}
	if _, present := first["gave_up"]; present {
		t.Fatal("disabled feature changed the Lanț payload")
	}
	refused := lantGiveUpRequest(t, s, http.MethodPost, unavailable+"/giveup", "", http.StatusNotFound)
	if refused["detail"] != "Not Found" {
		t.Fatalf("disabled route changed response: %#v", refused)
	}
	stillLive := lantGiveUpRequest(t, s, http.MethodGet, unavailable, "", http.StatusOK)
	if !reflect.DeepEqual(first, stillLive) {
		t.Fatal("disabled give-up changed the session")
	}

	now := time.Date(2026, 11, 16, 12, 0, 0, 0, time.UTC)
	clock := func() time.Time { return now }
	store, err := boardstats.Open(t.TempDir(), boardstats.Options{Now: clock})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := store.Close(); err != nil {
			t.Error(err)
		}
	})
	s.EnableBoardComparison(store, clock)
	for _, query := range []string{"?seed=42", "?daily=2026-11-14"} {
		ineligible, path := start(query)
		if _, present := ineligible["can_report_give_up"]; present {
			t.Fatalf("ineligible board %s advertised give-up", query)
		}
		refused := lantGiveUpRequest(t, s, http.MethodPost, path+"/giveup", "", http.StatusNotFound)
		if refused["detail"] != "Not Found" {
			t.Fatalf("ineligible route changed response: %#v", refused)
		}
	}
	live, path := start("?daily=" + day)
	if live["can_report_give_up"] != true {
		t.Fatalf("reviewed daily did not advertise give-up: %#v", live)
	}
	for _, request := range []struct{ method, suffix string }{{http.MethodGet, ""}, {http.MethodPost, "/undo"}} {
		state := lantGiveUpRequest(t, s, request.method, path+request.suffix, "", http.StatusOK)
		if state["can_report_give_up"] != true {
			t.Fatalf("live full state lost capability on %s: %#v", request.suffix, state)
		}
	}
	receipt := lantGiveUpRequest(t, s, http.MethodPost, path+"/giveup", "", http.StatusOK)
	if receipt["gave_up"] != true || receipt["won"] != false || receipt["perfect"] != false || receipt["hints_left"] != float64(0) ||
		receipt["steps"] != live["steps"] || len(receipt["choices"].([]any)) != 0 || receipt["score"] != nil || receipt["place"] != nil || receipt["can_report_give_up"] != nil {
		t.Fatalf("unexpected terminal receipt: %#v", receipt)
	}
	for _, request := range []struct{ method, suffix string }{{http.MethodPost, "/giveup"}, {http.MethodGet, ""}, {http.MethodPost, "/undo"}} {
		state := lantGiveUpRequest(t, s, request.method, path+request.suffix, "", http.StatusOK)
		if !reflect.DeepEqual(state, receipt) {
			t.Fatalf("terminal receipt changed on %s: %#v", request.suffix, state)
		}
	}
	lantGiveUpRequest(t, s, http.MethodPost, path+"/move", `{"text":"test"}`, http.StatusBadRequest)
	lantGiveUpRequest(t, s, http.MethodPost, path+"/hint", "", http.StatusBadRequest)
	terminal, found := s.lant.BoardTerminal(receipt["game_id"].(string), nil)
	if !found || terminal.Outcome != gameapi.TerminalGiveUp || terminal.Day != day {
		t.Fatalf("server terminal outcome is %+v, found=%t", terminal, found)
	}
	key := boardstats.Key{
		RulesVersion: gameapi.RulesVersion, ContentDigest: s.boardComparison.digest,
		Day: day, Game: "lant", BoardID: terminal.BoardID,
	}
	for range 99 {
		if err := store.Record(key, boardstats.Win, 0); err != nil {
			t.Fatal(err)
		}
	}
	if place, show := store.Place(key, 0); !show || place.Rounds != 100 || place.BetterThanPct != 1 {
		t.Fatalf("expected one sampled give-up, place %+v shown=%t", place, show)
	}
}

func TestLantGiveUpHTTPCountsAdmittedRoundAcrossMidnight(t *testing.T) {
	const games = "/api/wordgames/lant/games"
	const day = "2026-11-15"
	location := time.FixedZone("EET", 2*60*60)
	beforeMidnight := time.Date(2026, 11, 16, 23, 59, 59, 0, location)
	afterMidnight := beforeMidnight.Add(time.Second)
	allowClockRollover := false
	routeClockReads := 0
	clock := func() time.Time {
		if allowClockRollover {
			routeClockReads++
			if routeClockReads > 1 {
				return afterMidnight
			}
		}
		return beforeMidnight
	}

	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	s := New(c)
	store, err := boardstats.Open(t.TempDir(), boardstats.Options{Now: func() time.Time { return afterMidnight }})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := store.Close(); err != nil {
			t.Error(err)
		}
	})
	s.EnableBoardComparison(store, clock)
	round := lantGiveUpRequest(t, s, http.MethodPost, games+"?daily="+day, "", http.StatusOK)
	id := round["game_id"].(string)
	if round["can_report_give_up"] != true {
		t.Fatalf("yesterday's board was ineligible before midnight: %#v", round)
	}
	allowClockRollover = true
	receipt := lantGiveUpRequest(t, s, http.MethodPost, games+"/"+id+"/giveup", "", http.StatusOK)
	if receipt["gave_up"] != true || routeClockReads != 1 {
		t.Fatalf("admission and recording should share one clock read, got %d with receipt %#v", routeClockReads, receipt)
	}
	terminal, found := s.lant.BoardTerminal(id, nil)
	if !found {
		t.Fatal("receipt had no terminal round")
	}
	key := boardstats.Key{RulesVersion: gameapi.RulesVersion, ContentDigest: s.boardComparison.digest, Day: day, Game: "lant", BoardID: terminal.BoardID}
	for range 99 {
		if err := store.Record(key, boardstats.Win, 0); err != nil {
			t.Fatal(err)
		}
	}
	if place, show := store.Place(key, 0); !show || place.Rounds != 100 || place.BetterThanPct != 1 {
		t.Fatalf("admitted give-up was not counted, place %+v shown=%t", place, show)
	}
}
