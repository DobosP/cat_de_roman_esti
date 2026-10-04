package lant

import (
	"math/big"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pack"
)

func TestAccountExclusionsDailyAndTerminalProgress(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	s := New(c)
	first, e := s.Create(big.NewInt(17), "normal", nil, "")
	if e != nil {
		t.Fatal(e)
	}
	curated, finished, won, score, found := s.Progress(first["game_id"].(string))
	if !found || curated == "" || finished || won || score != -1 {
		t.Fatal("invalid initial progress")
	}
	second, e := s.CreateWithExclusions(big.NewInt(17), "normal", nil, "", map[string]bool{curated: true})
	if e != nil {
		t.Fatal(e)
	}
	other, _, _, _, _ := s.Progress(second["game_id"].(string))
	if other == "" || other == curated {
		t.Fatal("finished curated board repeated")
	}
	all := map[string]bool{}
	for _, item := range s.pack.Pool("lant", pack.PickOptions{Difficulty: "usor"}) {
		all[item.ID] = true
	}
	exhausted, e := s.CreateWithExclusions(big.NewInt(17), "usor", nil, "", all)
	if e != nil {
		t.Fatal(e)
	}
	fallback, _, _, _, _ := s.Progress(exhausted["game_id"].(string))
	if fallback == "" {
		t.Fatal("exhausted easy shelf lost curated fallback")
	}
	date := "2026-10-04"
	daily, e := s.Create(big.NewInt(17), "normal", &date, "")
	if e != nil {
		t.Fatal(e)
	}
	dailyID, _, _, _, _ := s.Progress(daily["game_id"].(string))
	dailyAgain, e := s.CreateWithExclusions(big.NewInt(1), "normal", &date, "", map[string]bool{dailyID: true})
	if e != nil {
		t.Fatal(e)
	}
	again, _, _, _, _ := s.Progress(dailyAgain["game_id"].(string))
	if again != dailyID {
		t.Fatal("exclusions changed daily")
	}
	id := second["game_id"].(string)
	s.store.Transaction(id, func(v *game) error { v.Chain = append(v.Chain, v.Target); v.Won = true; return nil })
	state, e := s.Get(id)
	if e != nil {
		t.Fatal(e)
	}
	_, finished, won, score, found = s.Progress(id)
	if !found || !finished || !won || score != state["score"] {
		t.Fatal("terminal score differs from authoritative state")
	}
	_, _, _, _, found = s.Progress("missing")
	if found {
		t.Fatal("missing session has progress")
	}
}
