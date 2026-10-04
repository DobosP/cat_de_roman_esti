package conexiuni

import (
	"math/big"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func TestAccountExclusionsDailyAndTerminalProgress(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	s := New(c)
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
	groups := [][]string{}
	s.store.Transaction(id, func(v *gameSession) error {
		for _, members := range v.groups {
			groups = append(groups, append([]string{}, members...))
		}
		return nil
	})
	var state map[string]any
	for _, members := range groups {
		state, e = s.Guess(id, members)
		if e != nil {
			t.Fatal(e)
		}
	}
	_, finished, won, score, found = s.Progress(id)
	if !found || !finished || !won || score != state["score"] {
		t.Fatal("terminal score differs")
	}
	s.store.Transaction(first["game_id"].(string), func(v *gameSession) error { v.lost = true; v.mistakes = 4; return nil })
	_, finished, won, score, _ = s.Progress(first["game_id"].(string))
	if !finished || won || score != 0 {
		t.Fatal("loss progress differs from Django")
	}
}
