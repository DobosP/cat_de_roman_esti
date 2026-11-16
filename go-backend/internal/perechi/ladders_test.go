package perechi

import (
	"reflect"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func TestPairLadderRevealsOnlyEarnedPairInformation(t *testing.T) {
	s := New(&content.Content{CategoryLabels: map[string]string{"theme": "Temă"}})
	g := &gameSession{
		boardCategory: "theme",
		hinted:        -1,
		pairs:         []pair{{[]string{"a", "b"}, "Legătură privată"}, {[]string{"c", "d"}, "Alta"}, {[]string{"e", "f"}, "A treia"}, {[]string{"g", "h"}, "A patra"}},
		order:         []string{"a", "b", "c", "d", "e", "f", "g", "h"},
	}
	id, _ := s.store.Create(g)
	for level := 1; level <= 3; level++ {
		body, err := s.Hint(id)
		if err != nil || body["hint_level"] != level || body["steps"] != level || body["remaining_mistakes"] != 6 || body["solution"] != nil {
			t.Fatalf("rung %d: %#v, %v", level, body, err)
		}
		if level < 3 {
			want := []string{"Temă", "Legătură privată"}[level-1]
			clue := body["clue"].(map[string]string)
			hint := body["hint"].(map[string]any)
			if len(hint["tiles"].([]map[string]string)) != 0 || hint["label"] != want || clue["label"] != want || len(clue) != 2 {
				t.Fatalf("rung %d exposed the wrong fields: %#v", level, body)
			}
		} else if hinted := body["hint"].(map[string]any); len(hinted["tiles"].([]map[string]string)) != 2 || len(hinted) != 2 {
			t.Fatalf("rung 3 must mark only its two tiles: %#v", hinted)
		}
	}
	before, _ := s.Get(id)
	_, err := s.Hint(id)
	after, _ := s.Get(id)
	if err == nil || err.Status != 400 || !reflect.DeepEqual(before, after) {
		t.Fatal("exhausted request changed the round")
	}
	wrong, _ := s.Match(id, []string{"a", "c"})
	repeated, _ := s.Match(id, []string{"c", "a"})
	if wrong["steps"] != 4 || repeated["steps"] != 4 || repeated["repeated"] != true {
		t.Fatal("wrong pair must cost only one step")
	}
}

func TestLastPairMembershipIsAlreadyPublic(t *testing.T) {
	s := New(&content.Content{})
	g := &gameSession{
		hinted: 0, hintLevel: 2, hintsUsed: 2, solved: []int{1, 2, 3},
		pairs: []pair{
			{[]string{"a", "b"}, "Legătură privată"}, {[]string{"c", "d"}, "Alta"},
			{[]string{"e", "f"}, "A treia"}, {[]string{"g", "h"}, "A patra"},
		},
		order: []string{"a", "b", "c", "d", "e", "f", "g", "h"},
	}
	id, _ := s.store.Create(g)
	before, _ := s.Get(id)
	_, err := s.Hint(id)
	after, _ := s.Get(id)
	if err == nil || err.Status != 400 || !reflect.DeepEqual(before, after) {
		t.Fatal("already-known membership must be rejected without mutation")
	}
	if after["hints_left"] != 0 || after["steps"] != 2 || after["hint"] != nil {
		t.Fatalf("last pair could still be marked: %#v", after)
	}
}

func TestSolvingHintedPairDoesNotRetargetRemainingRungs(t *testing.T) {
	s := New(&content.Content{CategoryLabels: map[string]string{"theme": "Temă"}})
	g := &gameSession{
		boardCategory: "theme",
		hinted:        -1,
		pairs:         []pair{{[]string{"a", "b"}, "Legătura întâi"}, {[]string{"c", "d"}, "Altă legătură"}, {[]string{"e", "f"}, "A treia"}, {[]string{"g", "h"}, "A patra"}},
		order:         []string{"a", "b", "c", "d", "e", "f", "g", "h"},
	}
	id, _ := s.store.Create(g)
	if hint, err := s.Hint(id); err != nil || hint["hint_level"] != 1 || hint["hints_left"] != 2 {
		t.Fatalf("first rung: %#v, %v", hint, err)
	}
	solved, err := s.Match(id, []string{"a", "b"})
	if err != nil || solved["correct"] != true || solved["hints_left"] != 0 || solved["steps"] != 1 {
		t.Fatalf("solving the hinted pair must exhaust only its ladder: %#v, %v", solved, err)
	}
	before, _ := s.Get(id)
	_, err = s.Hint(id)
	after, _ := s.Get(id)
	if err == nil || err.Status != 400 || !reflect.DeepEqual(before, after) {
		t.Fatalf("the ladder retargeted or mutated after the subject was solved: %#v, %v", after, err)
	}
}
