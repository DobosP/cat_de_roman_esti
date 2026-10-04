package contexto

import (
	"math/big"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func TestAccountExclusionsDailyAndPrivateProgress(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	s := New(c)
	first, e := s.Create(big.NewInt(17), "normal", nil, "")
	if e != nil {
		t.Fatal(e)
	}
	firstID := first["game_id"].(string)
	curated, finished, won, score, found := s.Progress(firstID)
	if !found || curated == "" || finished || won || score != -1 {
		t.Fatal("invalid initial progress")
	}
	if _, ok := first["curated_id"]; ok {
		t.Fatal("public payload exposes private curated id")
	}
	second, e := s.CreateWithExclusions(big.NewInt(17), "normal", nil, "", map[string]bool{curated: true})
	if e != nil {
		t.Fatal(e)
	}
	other, _, _, _, _ := s.Progress(second["game_id"].(string))
	if other == "" || other == curated {
		t.Fatal("finished curated board repeated")
	}
	date := "2026-10-04"
	daily, e := s.Create(big.NewInt(17), "normal", &date, "")
	if e != nil {
		t.Fatal(e)
	}
	dailyID, _, _, _, _ := s.Progress(daily["game_id"].(string))
	dailyAgain, e := s.CreateWithExclusions(big.NewInt(99), "normal", &date, "", map[string]bool{dailyID: true})
	if e != nil {
		t.Fatal(e)
	}
	again, _, _, _, _ := s.Progress(dailyAgain["game_id"].(string))
	if again != dailyID {
		t.Fatal("account exclusions changed daily board")
	}
	if _, e = s.GiveUp(firstID); e != nil {
		t.Fatal(e)
	}
	_, finished, won, score, found = s.Progress(firstID)
	if !found || !finished || won || score != -1 {
		t.Fatal("give-up wrote verified score")
	}
	var target string
	s.store.Transaction(second["game_id"].(string), func(v *game) error { target = v.Target; return nil })
	result, e := s.Guess(second["game_id"].(string), target, "")
	if e != nil {
		t.Fatal(e)
	}
	_, finished, won, score, found = s.Progress(second["game_id"].(string))
	if !found || !finished || !won || score != result["score"] {
		t.Fatal("terminal score differs from authoritative result")
	}
	_, _, _, _, found = s.Progress("missing")
	if found {
		t.Fatal("missing session has progress")
	}
}
