package lant

import (
	"reflect"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func TestHopLadderCapsDisclosureAndUndoKeepsSteps(t *testing.T) {
	c := &content.Content{
		Nodes: []content.Node{{ID: "s", LabelRO: "start"}, {ID: "a", LabelRO: "first"}, {ID: "b", LabelRO: "second"}, {ID: "t", LabelRO: "target"}},
		Edges: []content.Edge{
			{Src: "s", Dst: "a", Strength: 1},
			{Src: "s", Dst: "b", Strength: .7},
			{Src: "a", Dst: "t", Strength: 1},
			{Src: "b", Dst: "t", Strength: .7},
		},
		NormalizedIndex: map[string]string{"start": "s", "first": "a", "second": "b", "target": "t"},
		LantCaptions:    map[string]string{"s\x00a": "indiciu de direcție"},
	}
	s := New(c)
	id, _ := s.store.Create(&game{Start: "s", Target: "t", Difficulty: "usor", Optimal: 2, Chain: []string{"s"}})
	for level, stage := range []string{"direction", "alternatives", "hop"} {
		hint, err := s.Hint(id)
		if err != nil || hint["hint_level"] != level+1 || hint["steps"] != level+1 || hint["stage"] != stage {
			t.Fatalf("rung %d: %#v, %v", level+1, hint, err)
		}
		switch stage {
		case "direction":
			if hint["hint"] != nil || hint["relation"] != "indiciu de direcție" || hint["alternatives_choices"] != nil || strings.Contains(hint["message"].(string), "first") {
				t.Fatalf("rung 1 leaked words: %#v", hint)
			}
		case "alternatives":
			choices := hint["alternatives_choices"].([]map[string]any)
			if hint["hint"] != nil || len(choices) != 2 || len(choices[0]) != 2 || len(choices[1]) != 2 || choices[0]["id"] != nil || choices[1]["id"] != nil {
				t.Fatalf("rung 2 should only contain two useful labels and relations: %#v", hint)
			}
		case "hop":
			if hint["hint"].(map[string]any)["id"] != "a" || hint["alternatives_choices"] != nil {
				t.Fatalf("rung 3 should reveal one hop only: %#v", hint)
			}
		}
	}
	before, _ := s.Get(id)
	_, err := s.Hint(id)
	after, _ := s.Get(id)
	if err == nil || err.Status != 400 || !reflect.DeepEqual(before, after) {
		t.Fatal("exhausted request changed the round")
	}
	s.Move(id, "first")
	s.Undo(id)
	s.Move(id, "first")
	s.Undo(id)
	detour, _ := s.Move(id, "second")
	undone, _ := s.Undo(id)
	s.Move(id, "second")
	won, _ := s.Move(id, "target")
	if detour["steps"] != 4 || undone["steps"] != 4 || won["steps"] != 6 || won["moves"] != 2 || won["score"] != 1000 || won["perfect"] != false {
		t.Fatalf("undo lowered the cumulative hop count: %#v / %#v / %#v", detour, undone, won)
	}
}
