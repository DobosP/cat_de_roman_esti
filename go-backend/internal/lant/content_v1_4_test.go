package lant

import (
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"testing"
)

// Controlled duration-start paths exercise the actual Move/Get API; no new
// curated selection, hidden target or earned numeric public caption is claimed.
func TestV14DirectedDurationHopsAndPreservedPrivateState(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	for _, row := range []struct {
		start, target string
		moves         []string
	}{
		{"n_v24_time_day_ora", "n_v29_time_units_minut", []string{"Minut"}},
		{"n_v24_time_day_zi", "n_v24_time_day_ora", []string{"Oră"}},
		{"n_v24_time_day_zi", "n_v29_time_units_secunda", []string{"Oră", "Minut", "Secundă"}},
	} {
		t.Run(row.start+"-"+row.target, func(t *testing.T) {
			s := New(c)
			if s.g.DistancesTo(row.target)[row.start] != len(row.moves) {
				t.Fatal("specific directed shortest distance changed")
			}
			sid, e := s.store.Create(&game{Start: row.start, Target: row.target, Difficulty: "usor", Category: "societate", Optimal: len(row.moves), Chain: []string{row.start}})
			if e != nil {
				t.Fatal(e)
			}
			for i, text := range row.moves {
				got, err := s.Move(sid, text)
				if err != nil || got["ok"] != true || got["moves"] != i+1 || got["won"] != (i == len(row.moves)-1) {
					t.Fatalf("move: %v %v", got, err)
				}
				if i == len(row.moves)-1 && got["score"] != 1000 {
					t.Fatal("optimal score changed")
				}
			}
			got, err := s.Get(sid)
			if err != nil || got["won"] != true || got["moves"] != len(row.moves) {
				t.Fatalf("terminal resume: %v %v", got, err)
			}
			if s.short("n_v24_time_day_ora", "n_v29_time_units_minut") != "legătură directă" || s.short("n_v24_time_day_zi", "n_v24_time_day_ora") != "legătură directă" {
				t.Fatal("unreviewed numeric public caption appeared")
			}
		})
	}
}
