package alchimie

import (
	"encoding/json"
	"reflect"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func newBranchingLadderGame(t *testing.T) (*Service, string) {
	t.Helper()
	s := New(&content.Content{Nodes: []content.Node{
		{ID: "a", LabelRO: "first"}, {ID: "b", LabelRO: "second"}, {ID: "c", LabelRO: "third"},
		{ID: "d", LabelRO: "fourth"}, {ID: "e", LabelRO: "fifth"},
		{ID: "x", LabelRO: "detour"}, {ID: "y", LabelRO: "other result"},
		{ID: "z", LabelRO: "useful"}, {ID: "hidden", LabelRO: "known goal"},
	}})
	g := newGame([]string{"a", "b", "c", "d", "e"}, "hidden", &Projection{
		Recipes: map[Pair][]string{
			{"a", "b"}: {"z"}, {"c", "z"}: {"hidden"},
			{"c", "d"}: {"x"}, {"e", "x"}: {"y"}, {"b", "y"}: {"hidden"},
		},
		Par: 2,
	}, "usor", "", "")
	id, err := s.store.Create(g)
	if err != nil {
		t.Fatal(err)
	}
	return s, id
}

func TestAlchemyHintSubjectSurvivesAnotherDiscovery(t *testing.T) {
	s, id := newBranchingLadderGame(t)
	first, err := s.Hint(id)
	if err != nil || !reflect.DeepEqual(first["hint_output"], map[string]any{"label": "useful"}) {
		t.Fatalf("first subject: %#v, %v", first, err)
	}
	if _, err := s.Combine(id, "c", "d"); err != nil {
		t.Fatal(err)
	}
	before, _ := s.Get(id)
	if before["hint_level"] != 1 || before["hints_left"] != 2 || before["earned_hint"] != nil {
		t.Fatalf("resume after a different discovery: %#v", before)
	}
	for _, level := range []int{2, 3} {
		body, err := s.Hint(id)
		if err != nil || body["hint_level"] != level || body["steps"] != level {
			t.Fatalf("rung %d: %#v, %v", level, body, err)
		}
		if level == 2 && body["hint_ingredient"].(map[string]any)["id"] != "a" {
			t.Fatalf("rung 2 changed the first hint's subject: %#v", body["earned_hint"])
		}
		if level == 3 {
			pair := body["hint"].([]any)
			if pair[0].(map[string]any)["id"] != "a" || pair[1].(map[string]any)["id"] != "b" {
				t.Fatalf("rung 3 changed the first hint's subject: %#v", pair)
			}
		}
		raw, encodeErr := json.Marshal(body)
		if encodeErr != nil {
			t.Fatal(encodeErr)
		}
		if body["recipes"] != nil || body["routes"] != nil {
			t.Fatalf("rung %d exposed the private recipe book", level)
		}
		for _, hidden := range []string{`"id":"z"`, `"id":"y"`, `"hidden"`} {
			if strings.Contains(string(raw), hidden) {
				t.Fatalf("rung %d leaked %s", level, hidden)
			}
		}
	}
}

func TestAlchemySolvedHintSubjectEndsLadderAcrossReset(t *testing.T) {
	for _, solvePair := range []Pair{{"a", "b"}, {"c", "d"}} {
		t.Run(strings.Join(solvePair[:], "+"), func(t *testing.T) {
			s, id := newBranchingLadderGame(t)
			if solvePair != (Pair{"a", "b"}) {
				s.store.Transaction(id, func(g *gameSession) error {
					g.projection.Recipes[Pair{"a", "b"}] = []string{"z", "x"}
					g.projection.Recipes[Pair{"c", "d"}] = []string{"z"}
					return nil
				})
			}
			s.Hint(id)
			combined, err := s.Combine(id, solvePair[0], solvePair[1])
			if err != nil || combined["won"] != false || combined["hints_left"] != 0 {
				t.Fatalf("solving the hint subject should end the ladder: %#v, %v", combined, err)
			}
			for _, reset := range []bool{false, true} {
				if reset {
					if _, err := s.Reset(id); err != nil {
						t.Fatal(err)
					}
				}
				before, _ := s.Get(id)
				_, err := s.Hint(id)
				after, _ := s.Get(id)
				if err == nil || err.Status != 400 || before["hints_left"] != 0 || before["hint_level"] != 1 ||
					before["steps"] != 1 || !reflect.DeepEqual(before, after) {
					t.Fatalf("solved ladder changed after reset=%t: %#v -> %#v, %v", reset, before, after, err)
				}
			}
		})
	}
}

func TestAlchemyResetWaitsForPinnedRecipeIngredients(t *testing.T) {
	s, id := newBranchingLadderGame(t)
	s.Combine(id, "a", "b")
	first, err := s.Hint(id)
	if err != nil || first["hint_level"] != 2 || first["hint_ingredient"].(map[string]any)["id"] != "c" {
		t.Fatalf("first paid hint: %#v, %v", first, err)
	}
	before, _ := s.Reset(id)
	_, err = s.Hint(id)
	after, _ := s.Get(id)
	if err == nil || err.Status != 400 || before["hints_left"] != 0 || !reflect.DeepEqual(before, after) {
		t.Fatal("reset exposed a pinned recipe before its ingredients were owned")
	}
	s.Combine(id, "a", "b")
	third, err := s.Hint(id)
	if err != nil || third["hint_level"] != 3 || third["steps"] != 2 {
		t.Fatalf("restored recipe rung: %#v, %v", third, err)
	}
	pair := third["hint"].([]any)
	if pair[0].(map[string]any)["id"] != "c" || pair[1].(map[string]any)["id"] != "z" {
		t.Fatalf("reset changed the pinned recipe: %#v", pair)
	}
}

func TestAlchemyLadderAndLifetimePairsSurviveReset(t *testing.T) {
	s := New(&content.Content{
		Nodes: []content.Node{{ID: "a", LabelRO: "first"}, {ID: "b", LabelRO: "second"}, {ID: "c", LabelRO: "third"}, {ID: "x", LabelRO: "useful"}, {ID: "hidden", LabelRO: "known goal"}},
	})
	g := newGame([]string{"a", "b", "c"}, "hidden", &Projection{
		Recipes: map[Pair][]string{{"a", "b"}: {"x"}, {"c", "x"}: {"hidden"}},
		Par:     2,
	}, "usor", "", "")
	id, _ := s.store.Create(g)
	for level, kind := range []string{"output", "category", "pair"} {
		hint, err := s.Hint(id)
		if err != nil || hint["hint_level"] != level+1 || hint["steps"] != level+1 || hint["hint_kind"] != kind || hint["hint_stage"] != "pair" {
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
		case "category":
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
	if err != nil || before["hints_left"] != 2 || hint["hint_level"] != 2 || hint["hint_kind"] != "category" || hint["steps"] != 1 {
		t.Fatalf("already public rung charged a step: %#v -> %#v, %v", before, hint, err)
	}
}
