package contexto

import (
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"testing"
)

// The lexical wave must resolve through actual guess handling and deduplicate
// synonyms/inflections against the existing concept, rather than charge each form.
func TestV12ReviewedSynonymsShareOneAttemptAndWinIdentity(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	cases := []struct {
		id    string
		forms []string
	}{
		{"n_v4via_lift", []string{"ascensor", "ASCENSOARE", "ascensorului"}},
		{"n_v4gas_rosie", []string{"tomată", "tomata", "tomate", "tomatelor"}},
		{"n_vioara", []string{"scripcă", "scripca", "scripci", "scripcilor"}},
		{"n_v4soc_magazin", []string{"prăvălie", "pravalie", "prăvălii", "prăvăliilor"}},
	}
	for _, row := range cases {
		t.Run(row.id, func(t *testing.T) {
			s := New(c)
			sid, createErr := s.store.Create(s.build("n_mihai_eminescu", "normal", nil, "literatura"))
			if createErr != nil {
				t.Fatal(createErr)
			}
			for _, text := range append(row.forms, s.g.Label(row.id)) {
				got, e := s.Guess(sid, text, "")
				if e != nil || got["ok"] != true || got["attempts"] != 1 || got["won"] != false {
					t.Fatalf("%q: %v %v", text, got, e)
				}
				if got["guess"].(map[string]any)["id"] != row.id {
					t.Fatalf("%q acquired wrong identity: %v", text, got)
				}
			}
			recovered, getErr := s.Get(sid)
			if getErr != nil || recovered["attempts"] != 1 || recovered["target"] != nil {
				t.Fatalf("recovery/answer privacy: %v %v", recovered, getErr)
			}
			winning, createErr := s.store.Create(s.build(row.id, "normal", nil, s.g.Node(row.id).Category))
			if createErr != nil {
				t.Fatal(createErr)
			}
			got, apiErr := s.Guess(winning, row.forms[0], "")
			if apiErr != nil || got["won"] != true || got["attempts"] != 1 {
				t.Fatalf("synonym win: %v %v", got, apiErr)
			}
		})
	}
	s := New(c)
	if s.g.Resolve("mâțe") != "n_v2sti_matematica" || s.g.Resolve("nădragi") != "" {
		t.Fatal("held forms stole an existing owner or became exact aliases")
	}
}
