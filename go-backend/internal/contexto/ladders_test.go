package contexto

import (
	"fmt"
	"reflect"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func TestWarmLadderHidesTargetAndKeepsRanksBounded(t *testing.T) {
	const targetID = "hidden-id"
	const targetLabel = "secret word"
	c := &content.Content{
		CategoryLabels:  map[string]string{"category": "Tema"},
		Nodes:           []content.Node{{ID: targetID, LabelRO: targetLabel, Category: "category"}},
		NormalizedIndex: map[string]string{targetLabel: targetID},
	}
	previous := targetID
	for i := 1; i <= 151; i++ {
		id, label := fmt.Sprintf("node-%03d", i), fmt.Sprintf("label-%03d", i)
		c.Nodes = append(c.Nodes, content.Node{ID: id, LabelRO: label, Salience: 1})
		c.Edges = append(c.Edges, content.Edge{Src: id, Dst: previous, Strength: 1})
		c.NormalizedIndex[label] = id
		previous = id
	}
	s := New(c)
	g := s.build(targetID, "usor", nil, "")
	id, _ := s.store.Create(g)
	var warmRank int
	for level := 1; level <= 3; level++ {
		body, err := s.Clue(id)
		if err != nil || body["hint_level"] != level || body["steps"] != level || body["hints_left"] != 3-level || body["attempts"] != 0 {
			t.Fatalf("rung %d: %#v, %v", level, body, err)
		}
		for _, key := range []string{"perfect", "target", "solution"} {
			if _, ok := body[key]; ok {
				t.Fatalf("unexpected %s in body", key)
			}
		}
		if printed := fmt.Sprint(body); strings.Contains(printed, targetID) || strings.Contains(printed, targetLabel) {
			t.Fatalf("private target leaked: %s", printed)
		}
		if level == 1 {
			if body["clue_kind"] != "category" || body["word"] != nil || body["warm_clue"] != nil {
				t.Fatalf("rung 1 revealed more than category: %#v", body)
			}
		} else {
			word := body["word"].(map[string]any)
			rank := word["rank"].(int)
			maxRank := []int{0, 0, 150, min(25, warmRank-1)}[level]
			if len(word) != 3 || rank <= 1 || rank > maxRank {
				t.Fatalf("rung %d disclosed unexpected warm word: %#v", level, word)
			}
			warmRank = rank
		}
	}
	before, _ := s.Get(id)
	_, err := s.Clue(id)
	after, _ := s.Get(id)
	if err == nil || err.Status != 400 || !reflect.DeepEqual(before, after) {
		t.Fatal("exhausted request changed the round")
	}
	first, _ := s.Guess(id, "label-151", "")
	repeated, _ := s.Guess(id, "label-151", "")
	unknown, _ := s.Guess(id, "zzqqzzzq", "")
	won, _ := s.Guess(id, targetLabel, "")
	if first["steps"] != 4 || repeated["steps"] != 4 || unknown["steps"] != 4 || won["steps"] != 5 || won["won"] != true {
		t.Fatalf("only distinct accepted guesses, including the winner, cost steps")
	}
}
