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

func observationStore(t *testing.T, capacity int) *session.Store[*observedGame] {
	t.Helper()
	store, err := session.NewWithOptions[*observedGame](time.Hour, capacity, time.Now)
	if err != nil {
		t.Fatal(err)
	}
	return store
}

func inspectObservation(game *observedGame) (TerminalRound, *TerminalObservation) {
	return game.round, &game.observation
}

func TestBoardTerminalConcurrentResponsesObserveExactlyOnce(t *testing.T) {
	store := observationStore(t, 16)
	want := TerminalRound{BoardID: "reviewed", Day: "2026-11-17", Steps: 2, Outcome: TerminalWin}
	id, err := store.Create(&observedGame{round: want})
	if err != nil {
		t.Fatal(err)
	}
	admissions := 0
	respond := func(body map[string]any, round TerminalRound, first, admitted bool) bool {
		if round != want {
			t.Errorf("round %+v, expected %+v", round, want)
		}
		if first {
			if admitted {
				t.Error("first sample already admitted")
			}
			admissions++
		} else if !admitted {
			t.Error("lost the original successful admission")
		}
		return true
	}
	action := WithTerminalResponse(respond, inspectObservation, func(*observedGame) (map[string]any, *Error) {
		return map[string]any{"won": true}, nil
	})
	var callers sync.WaitGroup
	for range 16 {
		callers.Go(func() {
			store.Transaction(id, func(game *observedGame) error { action(game); return nil })
		})
	}
	callers.Wait()
	if admissions != 1 {
		t.Fatalf("admitted %d samples", admissions)
	}
}

func TestBoardTerminalIgnoresLiveFreeMinedAndReplayRounds(t *testing.T) {
	want := TerminalRound{BoardID: "reviewed", Day: "2026-11-17", Outcome: TerminalWin}
	for _, test := range []struct {
		name string
		game observedGame
	}{
		{"live", observedGame{round: TerminalRound{BoardID: "reviewed", Day: want.Day}}},
		{"free", observedGame{round: TerminalRound{BoardID: "reviewed", Outcome: TerminalLoss}}},
		{"mined", observedGame{round: TerminalRound{Day: want.Day, Outcome: TerminalGiveUp}}},
		{"replay", observedGame{round: want, observation: TerminalObservation{Replay: true}}},
	} {
		t.Run(test.name, func(t *testing.T) {
			action := WithTerminalResponse(func(map[string]any, TerminalRound, bool, bool) bool {
				t.Fatal("ineligible round reached aggregate callback")
				return false
			}, inspectObservation, func(*observedGame) (map[string]any, *Error) {
				return map[string]any{"won": true}, nil
			})
			action(&test.game)
			if test.game.observation.first != nil {
				t.Fatal("ineligible round consumed an observation")
			}
		})
	}
}

func TestBoardTerminalKeepsOriginalOutcomeAndRefusalAfterReset(t *testing.T) {
	want := TerminalRound{BoardID: "reviewed", Day: "2026-11-17", Steps: 2, Outcome: TerminalWin}
	game := &observedGame{round: want}
	calls := 0
	action := WithTerminalResponse(func(body map[string]any, round TerminalRound, first, admitted bool) bool {
		calls++
		if round != want || admitted || first != (calls == 1) {
			t.Fatalf("changed admission or original outcome: %+v first=%t admitted=%t", round, first, admitted)
		}
		return false // A refused sample never becomes admitted on a repeated read.
	}, inspectObservation, func(*observedGame) (map[string]any, *Error) {
		return map[string]any{"won": true}, nil
	})
	action(game)
	game.round.Outcome = ""
	action(game)
	if calls != 1 {
		t.Fatal("live reset reached the terminal observer")
	}
	game.round.Outcome, game.round.Steps = TerminalWin, 7
	action(game)
	action(game)
	if calls != 3 {
		t.Fatalf("expected three terminal responses, got %d", calls)
	}
}

func TestBoardTerminalResponseCapturesWhileActionPinsSession(t *testing.T) {
	store := observationStore(t, 1)
	id, err := store.Create(&observedGame{round: TerminalRound{BoardID: "reviewed", Day: "2026-11-17"}})
	if err != nil {
		t.Fatal(err)
	}
	observations := 0
	respond := func(body map[string]any, round TerminalRound, first, admitted bool) bool {
		observations++
		if !first || admitted || body["won"] != true || round.Outcome != TerminalWin {
			t.Fatalf("wrong pinned terminal response: %+v", round)
		}
		if _, err := store.Create(&observedGame{}); err != session.ErrCapacity {
			t.Fatalf("terminal session became evictable: %v", err)
		}
		return true
	}
	finish := WithTerminalResponse(respond, inspectObservation, func(game *observedGame) (map[string]any, *Error) {
		game.round.Outcome = TerminalWin
		return map[string]any{"won": true}, nil
	})
	store.Transaction(id, func(game *observedGame) error { finish(game); return nil })
	if observations != 1 {
		t.Fatalf("got %d observations", observations)
	}
}
