package contexto

import (
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pack"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
	"math/big"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

// New vocabulary must give useful, nonwinning guesses for distinct existing
// objects and charge one attempt for a whole inflection family.
func TestV13EverydayFormsGiveOneWarmPrivateAttempt(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	cases := []struct {
		id, target string
		forms      []string
	}{
		{"n_v1_3_home_balama", "n_v4via_usa", []string{"balama", "BALAMAUA", "balamale", "balamalele", "balamalei", "balamalelor"}},
		{"n_v1_3_material_lemn", "n_v4sti_copac", []string{"lemn", "LEMNUL", "lemnului"}},
		{"n_v1_3_clothing_fermoar", "n_v23via_ghiozdan", []string{"fermoar", "FERMOARUL", "fermoare", "fermoarele", "fermoarului", "fermoarelor"}},
	}
	for _, row := range cases {
		t.Run(row.id, func(t *testing.T) {
			s := New(c)
			if s.g.Node(row.id) == nil {
				t.Fatal("new native vocabulary absent")
			}
			inbound := s.g.DistancesTo(row.id)
			if len(inbound) != 1 || inbound[row.id] != 0 {
				t.Fatalf("unreviewed hidden target became reachable: %v", inbound)
			}
			sid, createErr := s.store.Create(s.build(row.target, "normal", nil, ""))
			if createErr != nil {
				t.Fatal(createErr)
			}
			for _, text := range row.forms {
				got, apiErr := s.Guess(sid, text, "")
				if apiErr != nil || got["ok"] != true || got["attempts"] != 1 || got["won"] != false || got["target"] != nil {
					t.Fatalf("%q: %v %v", text, got, apiErr)
				}
				guess := got["guess"].(map[string]any)
				if guess["id"] != row.id || guess["distance"] != 1 || guess["rank"].(int) < 2 || guess["rank"].(int) > 5 || guess["closeness"].(int) < 90 {
					t.Fatalf("specific warm association lost: %v", guess)
				}
			}
			recovered, getErr := s.Get(sid)
			if getErr != nil || recovered["attempts"] != 1 || recovered["won"] != false || recovered["target"] != nil {
				t.Fatalf("private recovery: %v %v", recovered, getErr)
			}
			won, apiErr := s.Guess(sid, s.g.Label(row.target), "")
			if apiErr != nil || won["won"] != true || won["attempts"] != 2 {
				t.Fatalf("existing identity win changed: %v %v", won, apiErr)
			}
		})
	}
}

// Existing approved targets must still be naturally selectable with no exclusion
// override. The new vocabulary improves a real selected game's warm guesses.
func TestV13NaturallySelectedExistingTargetsAcceptSpecificNewGuesses(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	for _, row := range []struct{ target, guess, alias string }{
		{"n_v4via_usa", "balama", "balamalele"},
		{"n_v23via_ghiozdan", "fermoar", "fermoarele"},
	} {
		t.Run(row.target, func(t *testing.T) {
			s := New(c)
			var seed *big.Int
			for i := int64(0); i < 4096; i++ {
				trial := big.NewInt(i)
				chosen := s.pack.PickSeeded("contexto", pyrandom.New(trial), pack.PickOptions{Category: "viata_de_roman", Difficulty: "usor", FilteredShelfWeights: true})
				if chosen != nil && chosen.Payload["target"] == row.target {
					seed = trial
					break
				}
			}
			if seed == nil {
				t.Fatal("existing target lost natural eligible selection")
			}
			initial, apiErr := s.Create(seed, "usor", nil, "viata_de_roman")
			if apiErr != nil || initial["target"] != nil {
				t.Fatalf("natural create privacy: %v %v", initial, apiErr)
			}
			sid := initial["game_id"].(string)
			for _, text := range []string{row.guess, row.alias} {
				got, guessErr := s.Guess(sid, text, "")
				if guessErr != nil || got["ok"] != true || got["attempts"] != 1 || got["won"] != false || got["target"] != nil {
					t.Fatalf("natural selected warm guess: %v %v", got, guessErr)
				}
				guess := got["guess"].(map[string]any)
				if guess["distance"] != 1 || guess["rank"].(int) < 2 || guess["rank"].(int) > 5 || guess["closeness"].(int) < 90 {
					t.Fatalf("specific warm feedback changed: %v", guess)
				}
			}
			recovered, getErr := s.Get(sid)
			if getErr != nil || recovered["attempts"] != 1 || recovered["target"] != nil {
				t.Fatalf("natural resume privacy: %v %v", recovered, getErr)
			}
			won, guessErr := s.Guess(sid, s.g.Label(row.target), "")
			if guessErr != nil || won["won"] != true || won["attempts"] != 2 {
				t.Fatalf("naturally selected identity win: %v %v", won, guessErr)
			}
			t.Logf("naturally selected target %s at seed %s", row.target, seed.String())
		})
	}
}
