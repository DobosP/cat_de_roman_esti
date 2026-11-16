package conexiuni

import (
	"reflect"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func TestGroupLadderRevealsOnlyEarnedGroupInformation(t *testing.T) {
	s := New(&content.Content{})
	g := newSession(map[string][]string{
		"first": {"a", "b", "c", "d"}, "second": {"e", "f", "g", "h"},
		"third": {"i", "j", "k", "l"}, "fourth": {"m", "n", "o", "p"},
	}, []string{"a", "e", "i", "m", "b", "f", "j", "n", "c", "g", "k", "o", "d", "h", "l", "p"}, "usor", "", "", map[string]string{"first": "Cuvinte ascunse"})
	id, _ := s.store.Create(g)
	wrong := []string{"a", "b", "c", "e"}
	oneAway, _ := s.Guess(id, wrong)
	if oneAway["steps"] != 1 || oneAway["one_away"] != true {
		t.Fatal("one-away counts as a wrong group")
	}
	if _, err := s.Guess(id, []string{"e", "a", "b", "c"}); err == nil || err.Status != 409 {
		t.Fatal("repeated combination was accepted")
	}
	for level := 1; level <= 3; level++ {
		body, err := s.Clue(id)
		if err != nil || body["hint_level"] != level || body["steps"] != level+1 || body["lives"] != 3 || body["solution"] != nil {
			t.Fatalf("rung %d: %#v, %v", level, body, err)
		}
		clue := body["clue"].(map[string]any)
		switch level {
		case 1:
			if clue["pattern"] != "C______ A______" || len(clue) != 2 {
				t.Fatalf("rung 1 exposed more than the redaction: %#v", clue)
			}
		case 2:
			if clue["label"] != "Cuvinte ascunse" || clue["pattern"] != "" || len(clue) != 3 {
				t.Fatalf("rung 2 exposed more than the full label: %#v", clue)
			}
		case 3:
			if clue["tile"].(map[string]string)["id"] != "a" || clue["pattern"] != "" || len(clue) != 3 {
				t.Fatalf("rung 3 did not identify exactly one member: %#v", clue)
			}
		}
	}
	before, _ := s.Get(id)
	_, err := s.Clue(id)
	after, _ := s.Get(id)
	if err == nil || err.Status != 400 || !reflect.DeepEqual(before, after) {
		t.Fatal("exhausted request changed the round")
	}
}

func TestLastGroupMembershipIsAlreadyPublic(t *testing.T) {
	s := New(&content.Content{})
	g := newSession(map[string][]string{
		"first": {"a", "b", "c", "d"}, "second": {"e", "f", "g", "h"},
		"third": {"i", "j", "k", "l"}, "fourth": {"m", "n", "o", "p"},
	}, []string{"a", "e", "i", "m", "b", "f", "j", "n", "c", "g", "k", "o", "d", "h", "l", "p"}, "usor", "", "", map[string]string{"first": "Cuvinte ascunse"})
	g.clued, g.hintLevel = "first", 2
	g.clues = []clue{s.clueFor(g, "first", 1), s.clueFor(g, "first", 2)}
	g.solved = []string{"fourth", "second", "third"}
	id, _ := s.store.Create(g)
	before, _ := s.Get(id)
	_, err := s.Clue(id)
	after, _ := s.Get(id)
	if err == nil || err.Status != 400 || !reflect.DeepEqual(before, after) {
		t.Fatal("already-known group membership must be rejected without mutation")
	}
	if after["hints_left"] != 0 || after["steps"] != 2 || after["clue_available"] != false {
		t.Fatalf("last group could still be marked: %#v", after)
	}
}

func TestSolvingHintedGroupDoesNotRetargetRemainingRungs(t *testing.T) {
	s := New(&content.Content{})
	groups := map[string][]string{
		"first": {"a", "b", "c", "d"}, "second": {"e", "f", "g", "h"},
		"third": {"i", "j", "k", "l"}, "fourth": {"m", "n", "o", "p"},
	}
	g := newSession(groups, []string{"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p"},
		"usor", "", "", map[string]string{"first": "Cuvinte ascunse", "fourth": "Alte cuvinte"})
	id, _ := s.store.Create(g)
	if hint, err := s.Clue(id); err != nil || hint["hint_level"] != 1 || hint["hints_left"] != 2 {
		t.Fatalf("first rung: %#v, %v", hint, err)
	}
	solved, err := s.Guess(id, groups["first"])
	if err != nil || solved["correct"] != true || solved["hints_left"] != 0 || solved["steps"] != 1 {
		t.Fatalf("solving the hinted group must exhaust only its ladder: %#v, %v", solved, err)
	}
	before, _ := s.Get(id)
	_, err = s.Clue(id)
	after, _ := s.Get(id)
	if err == nil || err.Status != 400 || !reflect.DeepEqual(before, after) {
		t.Fatalf("the ladder retargeted or mutated after the subject was solved: %#v, %v", after, err)
	}
}
