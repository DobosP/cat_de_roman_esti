package lant

import (
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

// Controlled new-start playthroughs test the real move API. They do not add a
// curated round or assert that normal curated selection chooses these starts.
func TestV13OutwardMovesWinResumeAndRefuseReverse(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	for _, pair := range [][2]string{
		{"n_v1_3_home_balama", "n_v4via_usa"},
		{"n_v1_3_material_lemn", "n_v32_workshop_cut_fierastrau"},
		{"n_v1_3_clothing_fermoar", "n_v23via_ghiozdan"},
	} {
		t.Run(pair[0], func(t *testing.T) {
			s := New(c)
			edge := s.g.Link(pair[0], pair[1])
			if edge == nil || edge.IsDistractor || edge.Bidirectional || s.g.Link(pair[1], pair[0]) != nil {
				t.Fatal("reviewed outward direction changed")
			}
			if s.short(pair[0], pair[1]) != "legătură directă" {
				t.Fatal("unreviewed route caption added")
			}
			sid, createErr := s.store.Create(&game{Start: pair[0], Target: pair[1], Difficulty: "usor", Category: "viata_de_roman", Optimal: 1, Chain: []string{pair[0]}})
			if createErr != nil {
				t.Fatal(createErr)
			}
			got, moveErr := s.Move(sid, s.g.Label(pair[1]))
			if moveErr != nil || got["ok"] != true || got["won"] != true || got["moves"] != 1 || got["score"] != 1000 {
				t.Fatalf("outward move: %v %v", got, moveErr)
			}
			recovered, getErr := s.Get(sid)
			if getErr != nil || recovered["won"] != true || recovered["moves"] != 1 {
				t.Fatalf("terminal recovery: %v %v", recovered, getErr)
			}
			reverse, createErr := s.store.Create(&game{Start: pair[1], Target: "n_v4soc_casa", Difficulty: "usor", Category: "viata_de_roman", Optimal: 2, Chain: []string{pair[1]}})
			if createErr != nil {
				t.Fatal(createErr)
			}
			refused, moveErr := s.Move(reverse, s.g.Label(pair[0]))
			if moveErr != nil || refused["ok"] != false {
				t.Fatalf("reverse relation incorrectly inferred: %v %v", refused, moveErr)
			}
			unchanged, getErr := s.Get(reverse)
			if getErr != nil || unchanged["moves"] != 0 {
				t.Fatalf("refused reverse mutated session: %v %v", unchanged, getErr)
			}
		})
	}
}
