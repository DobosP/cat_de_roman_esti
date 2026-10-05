package lant

import (
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"testing"
)

// A reviewed bidirectional relation must be a real legal move in either
// orientation and survive terminal GET; graph presence alone is insufficient.
func TestV12PedestrianSynonymLinkSupportsBothRealMoves(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	for _, pair := range [][2]string{{"n_v4geo_carare", "n_v4geo_poteca"}, {"n_v4geo_poteca", "n_v4geo_carare"}} {
		s := New(c)
		edge := s.g.Link(pair[0], pair[1])
		if edge == nil || edge.Relation != "synonym_of" || edge.IsDistractor || !edge.Bidirectional {
			t.Fatal("reviewed direct link absent or wrongly oriented")
		}
		sid, createErr := s.store.Create(&game{Start: pair[0], Target: pair[1], Difficulty: "usor", Category: "geografie", Optimal: 1, Chain: []string{pair[0]}})
		if createErr != nil {
			t.Fatal(createErr)
		}
		got, moveErr := s.Move(sid, s.g.Label(pair[1]))
		if moveErr != nil || got["ok"] != true || got["won"] != true || got["moves"] != 1 || got["score"] != 1000 {
			t.Fatalf("actual move: %v %v", got, moveErr)
		}
		recovered, getErr := s.Get(sid)
		if getErr != nil || recovered["won"] != true || recovered["moves"] != 1 {
			t.Fatalf("terminal resume: %v %v", recovered, getErr)
		}
	}
}
