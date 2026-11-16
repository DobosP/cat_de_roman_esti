package alchimie

import (
	"reflect"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func TestAlchemyLadderAndLifetimePairsSurviveReset(t *testing.T) {
	s := New(&content.Content{
		Nodes: []content.Node{{ID: "a", LabelRO: "first"}, {ID: "b", LabelRO: "second"}, {ID: "c", LabelRO: "third"}, {ID: "x", LabelRO: "useful"}, {ID: "hidden", LabelRO: "known goal"}},
	})
	g := newGame([]string{"a", "b", "c"}, "hidden", &Projection{
		Recipes: map[Pair][]string{{"a", "b"}: {"x"}, {"c", "x"}: {"hidden"}},
		Par:     2,
	}, "usor", "", "")
	id, _ := s.store.Create(g)
	for level, kind := range []string{"output", "ingredient", "pair"} {
		hint, err := s.Hint(id)
		if err != nil || hint["hint_level"] != level+1 || hint["steps"] != level+1 || hint["hint_kind"] != kind {
			t.Fatalf("rung %d: %#v, %v", level+1, hint, err)
		}
		stored := hint["earned_hint"].(map[string]any)
		if hint["target"].(map[string]any)["id"] != nil || strings.Contains(hint["message"].(string), "hidden") {
			t.Fatal("hidden target leaked")
		}
		switch kind {
		case "output":
			if hint["hint"] != nil || hint["hint_ingredient"] != nil || len(stored) != 4 || !reflect.DeepEqual(hint["hint_output"], map[string]any{"label": "useful"}) {
				t.Fatalf("rung 1 revealed more than the useful output label: %#v", stored)
			}
		case "ingredient":
			if hint["hint"] != nil || hint["hint_output"] != nil || len(stored) != 5 || hint["hint_ingredient"].(map[string]any)["id"] != "a" {
				t.Fatalf("rung 2 revealed more than one ingredient: %#v", stored)
			}
		case "pair":
			pair := hint["hint"].([]any)
			if hint["hint_ingredient"] != nil || hint["hint_output"] != nil || len(stored) != 4 || len(pair) != 2 || pair[0].(map[string]any)["id"] != "a" || pair[1].(map[string]any)["id"] != "b" {
				t.Fatalf("rung 3 did not reveal exactly one pair: %#v", stored)
			}
		}
	}
	before, _ := s.Get(id)
	_, err := s.Hint(id)
	after, _ := s.Get(id)
	if err == nil || err.Status != 400 || !reflect.DeepEqual(before, after) {
		t.Fatal("exhausted request changed the round")
	}
	s.Combine(id, "a", "c")
	s.Combine(id, "a", "b")
	fruitless, _ := s.Combine(id, "b", "c")
	repeat, _ := s.Combine(id, "c", "b")
	reset, _ := s.Reset(id)
	recraft, _ := s.Combine(id, "a", "b")
	won, _ := s.Combine(id, "x", "c")
	if fruitless["steps"] != 4 || repeat["steps"] != 4 || reset["steps"] != 4 || reset["hints_left"] != 0 || reset["hint_level"] != 3 || recraft["steps"] != 4 || won["steps"] != 5 || won["perfect"] != false || won["score"] != 1000 {
		t.Fatalf("steps or legacy score after reset: %#v -> %#v -> %#v", fruitless, reset, won)
	}
	if strings.Contains(won["share"].(string), "pct") {
		t.Fatal("share included a point score")
	}
}

func TestAlchemySkipsAlreadyPublicGoalOutput(t *testing.T) {
	s := New(&content.Content{})
	g := newGame([]string{"a", "b"}, "target", &Projection{Recipes: map[Pair][]string{{"a", "b"}: {"target"}}, Par: 1}, "usor", "", "")
	id, _ := s.store.Create(g)
	before, _ := s.Get(id)
	hint, err := s.Hint(id)
	if err != nil || before["hints_left"] != 2 || hint["hint_level"] != 2 || hint["hint_kind"] != "ingredient" || hint["steps"] != 1 {
		t.Fatalf("already public rung charged a step: %#v -> %#v, %v", before, hint, err)
	}
}
