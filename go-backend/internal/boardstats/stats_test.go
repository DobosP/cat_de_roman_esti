package boardstats

import (
	"errors"
	"fmt"
	"strings"
	"sync"
	"testing"
	"time"
)

const digest = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

func testDay(day int) time.Time {
	return time.Date(2026, time.November, day, 12, 0, 0, 0, time.FixedZone("server", 2*3600))
}

func testKey(day int) Key {
	return Key{
		RulesVersion: 2, ContentDigest: digest, Day: testDay(day).Format(time.DateOnly),
		Game: "intrusul", BoardID: "catalog_1",
	}
}

func openTest(t *testing.T, dir string, options Options) *Store {
	t.Helper()
	s, err := Open(dir, options)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := s.Close(); err != nil {
			t.Errorf("close board stats: %v", err)
		}
	})
	return s
}

func recordN(t *testing.T, s *Store, key Key, outcome Outcome, steps, n int) {
	t.Helper()
	for range n {
		if err := s.Record(key, outcome, steps); err != nil {
			t.Fatal(err)
		}
	}
}

func TestPlaceStartsAt100AndExcludesTiedWins(t *testing.T) {
	key := testKey(16)
	s := openTest(t, t.TempDir(), Options{Now: func() time.Time { return testDay(16) }})
	recordN(t, s, key, Win, 0, 5)
	recordN(t, s, key, Win, 1, 5)
	recordN(t, s, key, Win, 2, 40)
	recordN(t, s, key, Win, 3, 20)
	recordN(t, s, key, Loss, 0, 20)
	recordN(t, s, key, GiveUp, 0, 9)
	if value, ok := s.Place(key, 0); ok {
		t.Fatalf("placement before the minimum: %+v", value)
	}
	recordN(t, s, key, GiveUp, 0, 1)
	for _, row := range []struct {
		steps int
		pct   int
		tier  Tier
	}{
		{steps: 0, pct: 95, tier: Perfect},
		{steps: 1, pct: 90, tier: Top10},
		{steps: 2, pct: 50, tier: TopHalf},
		{steps: 3, pct: 30, tier: Completed},
		{steps: 4, pct: 30, tier: Completed},
	} {
		want := Place{BetterThanPct: row.pct, Tier: row.tier, Rounds: 100}
		got, ok := s.Place(key, row.steps)
		if !ok || got != want {
			t.Errorf("%d steps: place = %+v, %t; want %+v", row.steps, got, ok, want)
		}
	}
	recordN(t, s, key, Win, 1, 1)
	if got, ok := s.Place(key, 1); !ok || got != (Place{BetterThanPct: 89, Tier: TopHalf, Rounds: 101}) {
		t.Fatalf("89.1%% must floor below Top 10: %+v, %t", got, ok)
	}
}

func TestKeysSeparateContentRulesDateGameAndBoard(t *testing.T) {
	key := testKey(16)
	s := openTest(t, t.TempDir(), Options{Now: func() time.Time { return testDay(16) }})
	recordN(t, s, key, Loss, 0, MinimumRounds)
	for _, other := range []Key{
		{RulesVersion: 1, ContentDigest: key.ContentDigest, Day: key.Day, Game: key.Game, BoardID: key.BoardID},
		{RulesVersion: 2, ContentDigest: strings.Repeat("f", 64), Day: key.Day, Game: key.Game, BoardID: key.BoardID},
		{RulesVersion: 2, ContentDigest: key.ContentDigest, Day: testKey(15).Day, Game: key.Game, BoardID: key.BoardID},
		{RulesVersion: 2, ContentDigest: key.ContentDigest, Day: key.Day, Game: "perechi", BoardID: key.BoardID},
		{RulesVersion: 2, ContentDigest: key.ContentDigest, Day: key.Day, Game: key.Game, BoardID: "catalog_2"},
	} {
		recordN(t, s, other, Win, 1, 1)
		if _, ok := s.Place(other, 1); ok {
			t.Fatalf("counts leaked between boards: %+v", other)
		}
	}
}

func TestBoundsRejectOnlyNewBucketsOrBoards(t *testing.T) {
	dir := t.TempDir()
	options := Options{Now: func() time.Time { return testDay(16) }}
	s := openTest(t, dir, options)
	key := testKey(16)
	for index := range maxBucketsPerDay / maxBucketsPerBoard {
		key.BoardID = fmt.Sprintf("catalog_%d", index)
		for steps := range maxBucketsPerBoard {
			if err := s.Record(key, Win, steps); err != nil {
				t.Fatal(err)
			}
		}
	}
	if err := s.Record(key, Win, maxBucketsPerBoard); !errors.Is(err, ErrCapacity) {
		t.Fatalf("extra bucket: %v", err)
	}

	for index := maxBucketsPerDay / maxBucketsPerBoard; index < maxBoardsPerDay; index++ {
		key.BoardID = fmt.Sprintf("catalog_%d", index)
		recordN(t, s, key, Loss, 0, 1)
	}
	got, ok := s.Place(key, 0)
	if ok {
		t.Fatalf("one loss unexpectedly crossed threshold: %+v", got)
	}
	if err := s.Record(key, Win, 0); !errors.Is(err, ErrCapacity) {
		t.Fatalf("first bucket on existing loss-only board above day limit: %v", err)
	}
	key.BoardID = "catalog_overflow"
	if err := s.Record(key, Loss, 0); !errors.Is(err, ErrCapacity) {
		t.Fatalf("extra board: %v", err)
	}
	key.BoardID = "catalog_0"
	recordN(t, s, key, Win, 1, 1)
	recordN(t, s, key, GiveUp, 0, 1)
	if err := s.Close(); err != nil {
		t.Fatal(err)
	}
	s = openTest(t, dir, options)
	place, ok := s.Place(key, 1)
	if !ok || place.Rounds != maxBucketsPerBoard+2 {
		t.Fatalf("bounded counts after reload: %+v, %t", place, ok)
	}
}

func TestFinalFlushWithConcurrentRecorders(t *testing.T) {
	dir := t.TempDir()
	options := Options{Now: func() time.Time { return testDay(16) }}
	s := openTest(t, dir, options)
	key := testKey(16)
	const workers, repeats = 5, 40
	var wg sync.WaitGroup
	for step := range workers {
		wg.Go(func() {
			for range repeats {
				if err := s.Record(key, Win, step+1); err != nil {
					t.Error(err)
				}
			}
			if err := s.Flush(); err != nil {
				t.Error(err)
			}
		})
	}
	wg.Wait()
	if err := s.Close(); err != nil {
		t.Fatal(err)
	}
	if err := s.Record(key, Loss, 0); !errors.Is(err, ErrClosed) {
		t.Fatalf("closed record: %v", err)
	}
	if err := s.Flush(); !errors.Is(err, ErrClosed) {
		t.Fatalf("closed flush: %v", err)
	}
	if _, ok := s.Place(key, 1); ok {
		t.Fatal("closed store returned a place")
	}
	s = openTest(t, dir, options)
	want := Place{BetterThanPct: 40, Tier: Completed, Rounds: workers * repeats}
	if got, ok := s.Place(key, 3); !ok || got != want {
		t.Fatalf("concurrent place after reload: %+v, %t; want %+v", got, ok, want)
	}
}
