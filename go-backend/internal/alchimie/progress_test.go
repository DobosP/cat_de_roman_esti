package alchimie

import (
	"math/big"
	"testing"
)

func TestAccountExclusionsDailyAndTerminalProgress(t *testing.T) {
	s := load(t)
	first, e := s.Create(big.NewInt(17), "", "", "normal")
	if e != nil {
		t.Fatal(e)
	}
	curated, finished, won, score, found := s.Progress(first["game_id"].(string))
	if !found || curated == "" || finished || won || score != -1 {
		t.Fatal("invalid initial progress")
	}
	second, e := s.CreateWithExclusions(big.NewInt(17), "", "", "normal", map[string]bool{curated: true})
	if e != nil {
		t.Fatal(e)
	}
	id := second["game_id"].(string)
	other, _, _, _, _ := s.Progress(id)
	if other == "" || other == curated {
		t.Fatal("finished curated board repeated")
	}
	date := "2026-10-04"
	daily, e := s.Create(big.NewInt(17), date, "", "normal")
	if e != nil {
		t.Fatal(e)
	}
	dailyID, _, _, _, _ := s.Progress(daily["game_id"].(string))
	dailyAgain, e := s.CreateWithExclusions(big.NewInt(1), date, "", "normal", map[string]bool{dailyID: true})
	if e != nil {
		t.Fatal(e)
	}
	again, _, _, _, _ := s.Progress(dailyAgain["game_id"].(string))
	if again != dailyID {
		t.Fatal("exclusions changed daily")
	}
	s.store.Transaction(id, func(v *gameSession) error { v.add(v.target, nil); v.moves = v.projection.Par; return nil })
	state, e := s.Get(id)
	if e != nil {
		t.Fatal(e)
	}
	_, finished, won, score, found = s.Progress(id)
	if !found || !finished || !won || score != state["score"] {
		t.Fatal("terminal score differs")
	}
	_, _, _, _, found = s.Progress("missing")
	if found {
		t.Fatal("missing session has progress")
	}
}
