package alchimie_explore

import "testing"

func inventoryUsageWorld(t *testing.T, starters []string) *World {
	t.Helper()
	if starters == nil {
		starters = []string{"a", "b", "h", "z"}
	}
	concepts := []any{}
	for _, id := range []string{"a", "b", "c", "d", "e", "f", "g", "h", "z"} {
		concepts = append(concepts, map[string]any{"id": id, "label": id, "description": "synthetic " + id})
	}
	world, err := decodeWorld(map[string]any{
		"world": map[string]any{
			"id": "inventory-usage-synthetic", "title": "Synthetic inventory", "description": "Test only", "starter_ids": starters,
		},
		"concepts": concepts,
		"recipes": []any{
			map[string]any{"id": "ab", "pair": []string{"a", "b"}, "result": "d"},
			map[string]any{"id": "ac", "pair": []string{"a", "c"}, "result": "e"},
			map[string]any{"id": "bd", "pair": []string{"b", "d"}, "result": "f"},
			map[string]any{"id": "ch", "pair": []string{"c", "h"}, "result": "g"},
		},
		"unlocks": []any{
			map[string]any{"id": "supply-c", "after_discoveries": 1, "concept_ids": []string{"c"}, "title": "Synthetic supply"},
		},
	})
	if err != nil {
		t.Fatal("valid synthetic inventory world refused", err)
	}
	return world
}

type inventoryUsageExpected struct {
	id, status string
	ready      bool
}

func requireInventoryUsage(t *testing.T, state map[string]any, expected []inventoryUsageExpected) {
	t.Helper()
	items, ok := state["inventory"].([]any)
	if !ok || items == nil || len(items) != len(expected) {
		t.Fatalf("inventory shape/length differs: %T / %d", state["inventory"], len(items))
	}
	for index, want := range expected {
		item, ok := items[index].(map[string]any)
		if !ok || item["id"] != want.id || item["status"] != want.status || item["ready"] != want.ready {
			t.Fatalf("inventory item %d differs: got %v, want %+v", index, item, want)
		}
	}
}

func craftInventoryUsage(t *testing.T, game *exploreSession, pairs []Pair) {
	t.Helper()
	for _, input := range pairs {
		result, discovered, _, err := game.craft(input)
		if err != nil || !discovered || result == "" {
			t.Fatalf("synthetic inventory setup craft %v refused: %q / %v / %v", input, result, discovered, err)
		}
	}
}

func TestStateInventoryUsage(t *testing.T) {
	cases := []struct {
		name     string
		starters []string
		crafts   []Pair
		expected []inventoryUsageExpected
	}{
		{
			name:     "starters-one-partner-missing",
			expected: []inventoryUsageExpected{
				{"a", "active", true}, {"b", "active", true}, {"h", "active", false}, {"z", "final", false},
			},
		},
		{
			name:     "discovery-unlocks-nil-parent-ingredients",
			crafts:   []Pair{{"a", "b"}},
			expected: []inventoryUsageExpected{
				{"a", "active", true}, {"b", "active", true}, {"h", "active", true}, {"z", "final", false},
				{"d", "active", true}, {"c", "active", true},
			},
		},
		{
			name:     "known-and-unowned-results",
			crafts:   []Pair{{"a", "b"}, {"a", "c"}},
			expected: []inventoryUsageExpected{
				{"a", "depleted", false}, {"b", "active", true}, {"h", "active", true}, {"z", "final", false},
				{"d", "active", true}, {"c", "active", true}, {"e", "final", false},
			},
		},
		{
			name:     "all-recipe-results-known",
			crafts:   []Pair{{"a", "b"}, {"a", "c"}, {"b", "d"}, {"c", "h"}},
			expected: []inventoryUsageExpected{
				{"a", "depleted", false}, {"b", "depleted", false}, {"h", "depleted", false}, {"z", "final", false},
				{"d", "depleted", false}, {"c", "depleted", false}, {"e", "final", false}, {"f", "final", false}, {"g", "final", false},
			},
		},
		{
			name:     "nil-parent-result-key-present",
			starters: []string{"a", "b", "h", "z", "d"},
			expected: []inventoryUsageExpected{
				{"a", "active", false}, {"b", "active", true}, {"h", "active", false}, {"z", "final", false}, {"d", "active", true},
			},
		},
	}
	for _, item := range cases {
		t.Run(item.name, func(t *testing.T) {
			game := fresh(inventoryUsageWorld(t, item.starters), nil)
			craftInventoryUsage(t, game, item.crafts)
			requireInventoryUsage(t, game.state("synthetic-session"), item.expected)
		})
	}
}

func TestStateInventoryOrderIndependentOfOwnedKeys(t *testing.T) {
	game := fresh(inventoryUsageWorld(t, nil), nil)
	craftInventoryUsage(t, game, []Pair{{"a", "b"}})
	// The counting projection retains the old membership semantics even if an
	// internal order entry lacks an owned key. This grants no new restore input.
	delete(game.owned, "h")
	requireInventoryUsage(t, game.state("synthetic-session"), []inventoryUsageExpected{
		{"a", "active", true}, {"b", "active", true}, {"h", "active", false}, {"z", "final", false},
		{"d", "active", true}, {"c", "active", true},
	})
}

func TestStateInventoryEmptyOrder(t *testing.T) {
	game := fresh(inventoryUsageWorld(t, nil), nil)
	game.order = nil
	state := game.state("synthetic-session")
	requireInventoryUsage(t, state, []inventoryUsageExpected{})
	if state["game_id"] != "synthetic-session" || state["mode"] != "explore" || state["discovered_count"] != 0 {
		t.Fatal("empty inventory projection changed other public fields")
	}
}

func TestStateInventoryOutputDoesNotRetainDerivedFacts(t *testing.T) {
	game := fresh(inventoryUsageWorld(t, nil), nil)
	first := game.state("synthetic-session")
	item := first["inventory"].([]any)[0].(map[string]any)
	item["status"], item["ready"] = "changed-return-value", false
	requireInventoryUsage(t, game.state("synthetic-session"), []inventoryUsageExpected{
		{"a", "active", true}, {"b", "active", true}, {"h", "active", false}, {"z", "final", false},
	})
	craftInventoryUsage(t, game, []Pair{{"a", "b"}})
	requireInventoryUsage(t, game.state("synthetic-session"), []inventoryUsageExpected{
		{"a", "active", true}, {"b", "active", true}, {"h", "active", true}, {"z", "final", false},
		{"d", "active", true}, {"c", "active", true},
	})
}
