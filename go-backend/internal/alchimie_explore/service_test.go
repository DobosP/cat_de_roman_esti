package alchimie_explore

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"os"
	"testing"
)

func golden(t *testing.T) map[string]any {
	t.Helper()
	raw, e := os.ReadFile("../alchimie/testdata/python_parity.json")
	if e != nil {
		t.Fatal(e)
	}
	var g map[string]any
	if e = json.Unmarshal(raw, &g); e != nil {
		t.Fatal(e)
	}
	return g
}
func load(t *testing.T) *Service {
	t.Helper()
	data, e := content.Load()
	if e != nil {
		t.Fatal(e)
	}
	s := New(data)
	if s.loadError != nil {
		t.Fatal(s.loadError)
	}
	return s
}
func digest(p map[string]any) string {
	p["game_id"] = "<session>"
	var b bytes.Buffer
	e := json.NewEncoder(&b)
	e.SetEscapeHTML(false)
	_ = e.Encode(p)
	return fmt.Sprintf("%x", sha256.Sum256(bytes.TrimSuffix(b.Bytes(), []byte("\n"))))
}
func TestAllDiscoveryCraftsSupplyTiersHintsAndCompletionParity(t *testing.T) {
	s := load(t)
	id := ""
	for index, raw := range golden(t)["explore"].([]any) {
		r := raw.(map[string]any)
		var p map[string]any
		var e *Error
		switch r["action"] {
		case "create":
			goal := r["goal"].(string)
			p, e = s.Create(nil, &goal)
			if e == nil {
				id = p["game_id"].(string)
			}
		case "hint":
			p, e = s.Hint(id)
		case "combine":
			p, e = s.Combine(id, r["a"].(string), r["b"].(string))
		}
		if e != nil {
			t.Fatalf("step%d: %s", index, e)
		}
		if actual := digest(p); actual != r["hash"] {
			raw, _ := json.Marshal(p)
			t.Fatalf("step%d %s differs hash=%s\n%s", index, r["action"], actual, raw)
		}
	}
}
func TestCurrentAndAllArchivedMechanicsRestoreParity(t *testing.T) {
	s := load(t)
	for index, raw := range golden(t)["restores"].([]any) {
		r := raw.(map[string]any)
		var goal *string
		if value, ok := r["goal"].(string); ok {
			goal = &value
		}
		p, e := s.Create(r["progress"].(map[string]any), goal)
		if e != nil {
			t.Fatalf("restore%d: %s", index, e)
		}
		if digest(p) != r["hash"] {
			t.Fatalf("restore%d differs", index)
		}
	}
}
func TestRestoreCannotInventAndRepeatsDoNotSpendCapacity(t *testing.T) {
	s := load(t)
	progress := map[string]any{"world_id": s.world.Info.ID, "recipe_hash": s.world.Hash, "discoveries": []any{[]any{"unknown", "other"}}}
	if _, e := s.Create(progress, nil); e == nil || e.Status != 400 {
		t.Fatal("unknown ingredient accepted")
	}
	progress["world_id"] = "other"
	if _, e := s.Create(progress, nil); e == nil || e.Status != 409 {
		t.Fatal("unknown world accepted")
	}
	if s.store.Len() != 0 {
		t.Fatal("invalid restore allocated state")
	}
	p, e := s.Create(nil, nil)
	if e != nil {
		t.Fatal(e)
	}
	id := p["game_id"].(string)
	var candidate Pair
	found := false
	for _, a := range s.world.Info.Starters {
		for _, b := range s.world.Info.Starters {
			if a != b {
				q := pair(a, b)
				if _, ok := s.world.recipes[q]; !ok {
					candidate = q
					found = true
					break
				}
			}
		}
		if found {
			break
		}
	}
	if !found {
		t.Fatal("no miss fixture")
	}
	for i := 0; i < 140; i++ {
		p, e = s.Combine(id, candidate[0], candidate[1])
		if e != nil {
			t.Fatal(e)
		}
	}
	if p["discovered_count"] != 0 || len(p["empty_pairs"].([]Pair)) != 1 {
		t.Fatal("miss/repeat mutates progress")
	}
}

func TestGoalChangesGuidanceAndObservedEmptyMemoryIsBounded(t *testing.T) {
	s := load(t)
	p, e := s.Create(nil, nil)
	if e != nil {
		t.Fatal(e)
	}
	id := p["game_id"].(string)
	progress := fmt.Sprint(p["progress"])
	for _, goal := range s.world.Goals {
		g := goal.ID
		p, e = s.Goal(id, &g)
		if e != nil {
			t.Fatal(e)
		}
		if p["hint"] != nil || fmt.Sprint(p["progress"]) != progress {
			t.Fatal("goal changed recipes/progress")
		}
	}
	called := false
	if _, e = s.CombineInput("missing", func() (string, string, *Error) { called = true; return "", "", nil }); e == nil || e.Status != 404 || called {
		t.Fatal("missing pair lookup before validation")
	}
	if _, e = s.GoalInput("missing", func() (*string, *Error) { called = true; return nil, nil }); e == nil || e.Status != 404 || called {
		t.Fatal("missing goal lookup before validation")
	}
	// Test the FIFO cap directly on a fully earned collection: all 251 owned concepts
	// are valid ingredients, but observations still retain only 128 failed pairs.
	_, _ = s.store.Transaction(id, func(g *exploreSession) error {
		for _, c := range g.world.Concepts {
			g.add(c.ID, nil)
		}
		return nil
	})
	missed := []Pair{}
	for i, a := range s.world.Concepts {
		for _, b := range s.world.Concepts[i+1:] {
			q := pair(a.ID, b.ID)
			if _, ok := s.world.recipes[q]; !ok {
				missed = append(missed, q)
				if len(missed) == 129 {
					break
				}
			}
		}
		if len(missed) == 129 {
			break
		}
	}
	for _, q := range missed {
		p, e = s.Combine(id, q[0], q[1])
		if e != nil {
			t.Fatal(e)
		}
	}
	observed := p["empty_pairs"].([]Pair)
	if len(observed) != 128 || observed[0] != missed[1] || observed[127] != missed[128] {
		t.Fatal("observation FIFO cap differs")
	}
}
