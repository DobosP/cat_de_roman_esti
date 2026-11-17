package lant

import (
	"sync"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
)

func TestLantGiveUpAndWinningMoveProduceOneTerminalOutcome(t *testing.T) {
	s := New(&content.Content{
		Nodes:           []content.Node{{ID: "s", LabelRO: "start"}, {ID: "t", LabelRO: "target"}},
		Edges:           []content.Edge{{Src: "s", Dst: "t", Strength: 1}},
		NormalizedIndex: map[string]string{"start": "s", "target": "t"},
	})
	day := "2026-11-16"
	eligibleDay := func(candidate string) bool { return candidate == day }
	s.EnableBoardGiveUp(eligibleDay)
	for range 16 {
		id, err := s.store.Create(&game{Start: "s", Target: "t", Difficulty: "usor", Optimal: 1,
			Chain: []string{"s"}, Daily: &day, CuratedID: "reviewed", Hops: 2, HintsUsed: 2})
		if err != nil {
			t.Fatal(err)
		}
		start := make(chan struct{})
		first := make(chan gameapi.TerminalRound, 2)
		observe := func(_ map[string]any, round gameapi.TerminalRound, firstObservation, admitted bool) bool {
			if firstObservation {
				if admitted {
					t.Error("first observation was already admitted")
				}
				first <- round
			}
			return true
		}
		var moveErr, giveUpErr *gameapi.Error
		var actions sync.WaitGroup
		actions.Go(func() {
			<-start
			_, moveErr = s.MoveInputWithTerminal(id, func() (string, *gameapi.Error) { return "target", nil }, observe)
		})
		actions.Go(func() {
			<-start
			_, giveUpErr = s.GiveUpWithTerminal(id, eligibleDay, observe)
		})
		close(start)
		actions.Wait()
		if len(first) != 1 {
			t.Fatalf("racing actions produced %d samples", len(first))
		}
		round := <-first
		resume, lookupErr := s.Get(id)
		if lookupErr != nil || round.BoardID != "reviewed" || round.Day != day || resume["steps"] != round.Steps {
			t.Fatalf("resume %#v (%v), observation %+v", resume, lookupErr, round)
		}
		switch round.Outcome {
		case gameapi.TerminalWin:
			if moveErr != nil || giveUpErr == nil || giveUpErr.Status != 409 || resume["won"] != true || resume["gave_up"] != nil {
				t.Fatalf("win receipt %#v, move %v, give-up %v", resume, moveErr, giveUpErr)
			}
		case gameapi.TerminalGiveUp:
			if giveUpErr != nil || moveErr == nil || moveErr.Status != 400 || resume["won"] != false || resume["gave_up"] != true || round.Steps != 3 {
				t.Fatalf("give-up receipt %#v, move %v, give-up %v", resume, moveErr, giveUpErr)
			}
			if _, finished, won, score, found := s.Progress(id); !found || finished || won || score != -1 {
				t.Fatalf("give-up became account progress: found=%t finished=%t won=%t score=%d", found, finished, won, score)
			}
		default:
			t.Fatalf("unexpected observation: %+v", round)
		}
	}
}
