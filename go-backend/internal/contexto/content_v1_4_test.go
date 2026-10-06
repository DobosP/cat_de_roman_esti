package contexto

import (
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"math/big"
	"testing"
)

// A new qualified input family resolves to the same old device and charges one
// attempt; this does not approve Ceas as a hidden target or promise warm feedback.
func TestV14ClockSynonymInNaturallySelectedExistingGame(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	s := New(c)
	start, apiErr := s.Create(big.NewInt(23), "usor", nil, "viata_de_roman")
	if apiErr != nil || start["target"] != nil {
		t.Fatalf("create/private target: %v %v", start, apiErr)
	}
	sid := start["game_id"].(string)
	for _, text := range []string{"ceasornic", "CEASORNICE", "Ceas"} {
		got, e := s.Guess(sid, text, "")
		if e != nil || got["ok"] != true || got["attempts"] != 1 || got["won"] != false || got["target"] != nil {
			t.Fatalf("%q: %v %v", text, got, e)
		}
		guess := got["guess"].(map[string]any)
		if guess["id"] != "n_v24_time_day_ceas" || guess["rank"] != 2158 || guess["closeness"] != 8 {
			t.Fatalf("existing device feedback changed: %v", guess)
		}
	}
	recovered, e := s.Get(sid)
	if e != nil || recovered["attempts"] != 1 || recovered["target"] != nil {
		t.Fatalf("resume: %v %v", recovered, e)
	}
	won, e := s.Guess(sid, "Ușă", "")
	if e != nil || won["won"] != true || won["attempts"] != 2 || won["score"] != 940 {
		t.Fatalf("existing selected win: %v %v", won, e)
	}
	if s.g.Resolve("ceasornicul") != "" || s.g.Resolve("ceasornicele") != "" || s.g.Resolve("ceasornicului") != "" || s.g.Resolve("ceasornicelor") != "" {
		t.Fatal("unselected grammatical forms became exact aliases")
	}
}
