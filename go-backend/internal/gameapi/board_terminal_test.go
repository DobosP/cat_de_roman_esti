package gameapi

import (
	"sync"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/session"
)

type observedGame struct {
	round       TerminalRound
	observation TerminalObservation
}

func newObservationStore(t *testing.T) *session.Store[*observedGame] {
	t.Helper()
	store, err := session.NewWithOptions[*observedGame](time.Hour, 16, time.Now)
	if err != nil {
		t.Fatal(err)
	}
	return store
}

func addObservedGame(t *testing.T, store *session.Store[*observedGame], round TerminalRound) string {
	t.Helper()
	id, err := store.Create(&observedGame{round: round})
	if err != nil {
		t.Fatal(err)
	}
	return id
}

func inspectObservation(game *observedGame) (TerminalRound, *TerminalObservation) {
	return game.round, &game.observation
}

func TestBoardTerminalConcurrentReadsObserveExactlyOnce(t *testing.T) {
	store := newObservationStore(t)
	want := TerminalRound{BoardID: "reviewed", Day: "2026-11-16", Steps: 2, Outcome: TerminalWin}
	id := addObservedGame(t, store, want)

	if got, ok := ObserveBoardTerminal(store, id, nil, inspectObservation); !ok || got != want {
		t.Fatalf("read = %+v, %t", got, ok)
	}
	observed := make(chan TerminalRound, 16)
	var callers sync.WaitGroup
	for range cap(observed) {
		callers.Go(func() {
			got, ok := ObserveBoardTerminal(store, id, func(round TerminalRound) {
				observed <- round
			}, inspectObservation)
			if !ok || got != want {
				t.Errorf("concurrent read = %+v, %t", got, ok)
			}
		})
	}
	callers.Wait()
	close(observed)
	if len(observed) != 1 || <-observed != want {
		t.Fatal("expected one exact observation")
	}
}

func TestBoardTerminalIgnoresLiveFreeAndMinedRounds(t *testing.T) {
	store := newObservationStore(t)
	ids := []string{
		"missing",
		addObservedGame(t, store, TerminalRound{BoardID: "reviewed", Day: "2026-11-16"}),
		addObservedGame(t, store, TerminalRound{BoardID: "reviewed", Outcome: TerminalLoss}),
		addObservedGame(t, store, TerminalRound{Day: "2026-11-16", Outcome: TerminalGiveUp}),
	}
	for _, id := range ids {
		got, ok := ObserveBoardTerminal(store, id, func(TerminalRound) {
			t.Fatal("ineligible round was observed")
		}, inspectObservation)
		if ok || got != (TerminalRound{}) {
			t.Fatalf("ineligible read = %+v, %t", got, ok)
		}
	}
}

func TestBoardTerminalKeepsOriginalSampleAfterLegacyReset(t *testing.T) {
	store := newObservationStore(t)
	want := TerminalRound{BoardID: "reviewed", Day: "2026-11-16", Steps: 2, Outcome: TerminalWin}
	id := addObservedGame(t, store, want)
	if got, ok := ObserveBoardTerminal(store, id, func(TerminalRound) {}, inspectObservation); !ok || got != want {
		t.Fatalf("initial sample = %+v, %t", got, ok)
	}

	store.Transaction(id, func(game *observedGame) error {
		game.round.Outcome = ""
		return nil
	})
	if _, ok := ObserveBoardTerminal(store, id, nil, inspectObservation); ok {
		t.Fatal("reopened round reported as terminal")
	}

	store.Transaction(id, func(game *observedGame) error {
		game.round.Outcome = TerminalWin
		game.round.Steps = 7
		return nil
	})
	got, ok := ObserveBoardTerminal(store, id, func(TerminalRound) {
		t.Fatal("reset should not count another sample")
	}, inspectObservation)
	if !ok || got != want {
		t.Fatalf("stored sample = %+v, %t", got, ok)
	}
}

func TestBoardTerminalResponseCapturesWhileActionPinsSession(t *testing.T) {
	store, err := session.NewWithOptions[*observedGame](time.Hour, 1, time.Now)
	if err != nil {
		t.Fatal(err)
	}
	start := TerminalRound{BoardID: "reviewed", Day: "2026-11-16"}
	id := addObservedGame(t, store, start)
	observations := 0
	terminal := func(body map[string]any, result TerminalRound, first bool) {
		observations++
		if !first || body["won"] != true || result.Outcome != TerminalWin {
			t.Fatalf("terminal callback saw %+v with first=%t and response %v", result, first, body)
		}
		if _, err := store.Create(&observedGame{}); err != session.ErrCapacity {
			t.Fatalf("live terminal transaction became evictable: %v", err)
		}
	}
	finish := WithTerminalResponse(terminal, inspectObservation, func(game *observedGame) (map[string]any, *Error) {
		game.round.Outcome = TerminalWin
		return map[string]any{"won": true}, nil
	})
	store.Transaction(id, func(game *observedGame) error {
		finish(game)
		return nil
	})
	store.Transaction(id, func(game *observedGame) error {
		game.round = start // Legacy reset can reopen after the action returns.
		return nil
	})
	if observations != 1 {
		t.Fatalf("terminal response observed %d times", observations)
	}
	if _, ok := ObserveBoardTerminal(store, id, nil, inspectObservation); ok {
		t.Fatal("reset should report a live game")
	}
}
