package alchimie_explore

import (
	"fmt"
	"math/rand/v2"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

// legacyInventoryUsage is the per-concept counting loop state() used before
// aac8eff, copied verbatim from aac8eff^ as the differential oracle.
func legacyInventoryUsage(s *exploreSession, cid string) (int, int, bool) {
	uses, remaining, ready := 0, 0, false
	for _, r := range s.world.Recipes {
		if r.Pair[0] != cid && r.Pair[1] != cid {
			continue
		}
		uses++
		if _, owned := s.owned[r.Result]; !owned {
			remaining++
			_, a := s.owned[r.Pair[0]]
			_, b := s.owned[r.Pair[1]]
			ready = ready || (a && b)
		}
	}
	return uses, remaining, ready
}

func requireLegacyInventory(t *testing.T, s *exploreSession, label string) {
	t.Helper()
	inv := s.state("legacy-diff")["inventory"].([]any)
	if len(inv) != len(s.order) {
		t.Fatalf("%s: inventory length %d, order length %d", label, len(inv), len(s.order))
	}
	for i, cid := range s.order {
		uses, remaining, ready := legacyInventoryUsage(s, cid)
		status := "depleted"
		if uses == 0 {
			status = "final"
		} else if remaining > 0 {
			status = "active"
		}
		item := inv[i].(map[string]any)
		if item["id"] != cid || item["status"] != status || item["ready"] != ready {
			t.Fatalf("%s: item %d %v differs from legacy %s/%v", label, i, item, status, ready)
		}
	}
}

// Adversarial worlds: self-pairs, duplicate recipes, ids outside the concept
// table, order entries without an owned key and duplicated order entries.
func TestStateInventoryMatchesLegacyCountingOnRandomWorlds(t *testing.T) {
	rng := rand.New(rand.NewPCG(20261011, 1))
	for iter := 0; iter < 3000; iter++ {
		n := 2 + rng.IntN(12)
		ids := make([]string, n+2)
		for i := range ids {
			ids[i] = fmt.Sprintf("c%02d", i)
		}
		w := &World{concepts: map[string]Concept{}, recipes: map[Pair]Recipe{}}
		for _, id := range ids[:n] {
			w.concepts[id] = Concept{ID: id, Label: id}
		}
		for r := rng.IntN(3 * n); r > 0; r-- {
			rec := Recipe{ID: fmt.Sprint(r), Pair: Pair{ids[rng.IntN(len(ids))], ids[rng.IntN(len(ids))]}, Result: ids[rng.IntN(len(ids))]}
			w.Recipes = append(w.Recipes, rec)
			if rng.IntN(4) == 0 {
				w.Recipes = append(w.Recipes, rec)
			}
		}
		s := &exploreSession{world: w, owned: map[string]*Pair{}, order: []string{}, discoveries: []Pair{}, unlocked: map[string]bool{}, empty: []Pair{}}
		for _, id := range ids {
			switch rng.IntN(4) {
			case 0:
				s.owned[id] = nil
				s.order = append(s.order, id)
			case 1:
				p := Pair{ids[0], ids[1]}
				s.owned[id] = &p
				s.order = append(s.order, id)
			case 2:
				s.order = append(s.order, id)
			}
		}
		if len(s.order) > 0 && rng.IntN(5) == 0 {
			s.order = append(s.order, s.order[0])
		}
		requireLegacyInventory(t, s, fmt.Sprint("random-", iter))
	}
}

// Bundled world: every state along a full useful() replay, without a goal and
// for the first three goals.
func TestStateInventoryMatchesLegacyCountingOnBundledReplay(t *testing.T) {
	data, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	w, err := decodeWorld(data.DiscoveryWorld)
	if err != nil {
		t.Fatal(err)
	}
	goals := []*string{nil}
	for i := 0; i < len(w.Goals) && i < 3; i++ {
		g := w.Goals[i].ID
		goals = append(goals, &g)
	}
	for gi, goal := range goals {
		game := fresh(w, goal)
		for step := 0; step <= MaxConcepts; step++ {
			requireLegacyInventory(t, game, fmt.Sprint("goal", gi, "-step", step))
			p := game.useful()
			if p == nil {
				break
			}
			if _, _, _, e := game.craft(*p); e != nil {
				t.Fatal(e.Detail)
			}
		}
	}
}
