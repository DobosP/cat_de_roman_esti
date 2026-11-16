package main

import (
	"fmt"
	"slices"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contexto"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/lant"
)

func TestQuickSelectabilityAcrossProfilesAndSourceHistory(t *testing.T) {
	boards := []content.Board{}
	add := func(game, category, id, source string, score int, starter bool) boardKey {
		boards = append(boards, content.Board{Game: game, Category: category, CatalogID: id,
			SourceID: source, OverallScore: score, StarterSafe: starter})
		return boardKey{game, id}
	}
	for i := 0; i < 5; i++ {
		id := fmt.Sprintf("i%d", i)
		add("intrusul", "blocked", id, id, 55, i == 0)
		if i < 4 {
			add("perechi", "open", id, id, 55, i == 0)
		}
	}
	preferred := add("intrusul", "blocked", "preferred", "same", 55, true)
	shared := add("intrusul", "blocked", "shared", "same", 54, true)
	tooMany := add("intrusul", "blocked", "ring-overflow", "other", 54, false)
	starter := add("intrusul", "blocked", "starter-open", "other", 54, true)
	four := add("perechi", "open", "four", "other", 54, false)
	empty := add("intrusul", "empty", "empty", "same", 54, false)
	got := quickSelectable(boards)
	for key, want := range map[boardKey]bool{preferred: true, shared: false, tooMany: false, starter: true, four: true, empty: true} {
		if got[key] != want {
			t.Errorf("%+v selectable = %v, want %v", key, got[key], want)
		}
	}
}

// servedBoard is an approved, selectable ranked row for a synthetic bundle.
func servedBoard(game, id string, payload map[string]any) content.PackItem {
	return content.PackItem{ID: id, Game: game, Status: "approved", Category: "life", Difficulty: "normal",
		PilotEligible: true, SelectionWeight: 1, Payload: payload}
}

func viewDelta(t *testing.T, before, after *content.Content, row content.PackItem) (parts, diagnostics []string) {
	t.Helper()
	left := services{data: before, g: graph.New(before), cald: contexto.New(before), lant: lant.New(before)}
	right := services{data: after, g: graph.New(after), cald: contexto.New(after), lant: lant.New(after)}
	old, err := left.packView(row)
	if err != nil {
		t.Fatal(err)
	}
	next, err := right.packView(row)
	if err != nil {
		t.Fatal(err)
	}
	return changedFields(old.parts, next.parts), changedFields(old.diagnostic, next.diagnostic)
}

func lantDetour(caption string, extra ...content.Edge) *content.Content {
	return &content.Content{
		Nodes: []content.Node{{ID: "s", LabelRO: "Start"}, {ID: "a", LabelRO: "A"},
			{ID: "t", LabelRO: "Target"}, {ID: "d", LabelRO: "Detour"},
			{ID: "e", LabelRO: "Next"}, {ID: "f", LabelRO: "Further"}, {ID: "g", LabelRO: "Last"}},
		Edges: append([]content.Edge{{Src: "s", Dst: "a", Strength: .8}, {Src: "a", Dst: "t", Strength: .8},
			{Src: "s", Dst: "d", Strength: .8}, {Src: "d", Dst: "e", Strength: .8},
			{Src: "e", Dst: "f", Strength: .8}, {Src: "f", Dst: "g", Strength: .8}, {Src: "g", Dst: "t", Strength: .8}}, extra...),
		LantCaptions:   map[string]string{"s\x00d": caption},
		CategoryLabels: map[string]string{"life": "Life"},
	}
}

func TestLanțMenuOnlyChangeIsListedButNotDisturbed(t *testing.T) {
	row := servedBoard("lant", "route", map[string]any{"start": "s", "target": "t", "optimal": float64(2)})
	before, after := lantDetour("Old detour"), lantDetour("New detour")
	parts, diagnostics := viewDelta(t, before, after, row)
	if len(parts) != 0 || len(diagnostics) != 1 || diagnostics[0] != "route_menus" {
		t.Fatalf("a detour caption must only be a diagnostic: %v %v", parts, diagnostics)
	}
	before.PackItems, after.PackItems = []content.PackItem{row}, []content.PackItem{row}
	got, err := compare(before, after)
	if err != nil {
		t.Fatal(err)
	}
	if got.DisturbedTotal != 0 || got.Games["lant"].Disturbed != 0 || len(got.Diagnostics) != 1 ||
		got.Diagnostics[0].boardKey != (boardKey{"lant", "route"}) || got.Diagnostics[0].Fields[0] != "route_menus" {
		t.Fatalf("menu-only change must be listed for replay and not disturbed: %+v", got)
	}
}

func TestLanțShortestRouteChangeIsDisturbed(t *testing.T) {
	row := servedBoard("lant", "route", map[string]any{"start": "s", "target": "t", "optimal": float64(2)})
	before := lantDetour("Detour")
	// A second two-step route through the old detour changes the shortest DAG.
	after := lantDetour("Detour", content.Edge{Src: "d", Dst: "t", Strength: .8})
	parts, _ := viewDelta(t, before, after, row)
	if len(parts) != 1 || parts[0] != "shortest_steps" {
		t.Fatalf("a new shortest branch must disturb the board: %v", parts)
	}
	before.PackItems, after.PackItems = []content.PackItem{row}, []content.PackItem{row}
	got, err := compare(before, after)
	if err != nil {
		t.Fatal(err)
	}
	if got.DisturbedTotal != 1 || got.Disturbed[0].boardKey != (boardKey{"lant", "route"}) ||
		got.Disturbed[0].Fields[0] != "shortest_steps" || got.Games["lant"].Disturbed != 1 {
		t.Fatalf("shortest-route change must be disturbed: %+v", got)
	}
}

func TestLanțIntermediateMenuCaptions(t *testing.T) {
	c := &content.Content{
		Nodes: []content.Node{{ID: "s", LabelRO: "Start"}, {ID: "a", LabelRO: "A"},
			{ID: "t", LabelRO: "Target"}, {ID: "d", LabelRO: "Detour"}, {ID: "e", LabelRO: "Next"}},
		Edges: []content.Edge{{Src: "s", Dst: "a", Strength: .8}, {Src: "a", Dst: "t", Strength: .8},
			{Src: "a", Dst: "d", Strength: .8}, {Src: "d", Dst: "e", Strength: .8}, {Src: "e", Dst: "t", Strength: .8}},
		LantCaptions: map[string]string{"a\x00d": "an intermediate detour"},
	}
	svc := lant.New(c)
	menus, err := svc.BoardRouteMenusForReview("s", "t", 2)
	if err != nil {
		t.Fatal(err)
	}
	if len(menus) != 2 || len(menus[0].Choices) != 1 || len(menus[1].Choices) != 2 ||
		menus[1].Prefix[1] != "a" || menus[1].Choices[0]["id"] != "d" ||
		menus[1].Choices[0]["relation"] != "an intermediate detour" {
		t.Fatalf("missing exact intermediate menu: %+v", menus)
	}
}

func TestLanțMenuBoundRefusesPartialOutput(t *testing.T) {
	c := &content.Content{Nodes: []content.Node{{ID: "s"}, {ID: "t"}}}
	previous := []string{"s"}
	for layer := 0; layer < 5; layer++ {
		next := []string{}
		for column := 0; column < 5; column++ {
			id := fmt.Sprintf("layer%d-%d", layer, column)
			c.Nodes = append(c.Nodes, content.Node{ID: id, LabelRO: id})
			next = append(next, id)
			for _, from := range previous {
				c.Edges = append(c.Edges, content.Edge{Src: from, Dst: id, Strength: .8})
			}
		}
		previous = next
	}
	for _, from := range previous {
		c.Edges = append(c.Edges, content.Edge{Src: from, Dst: "t", Strength: .8})
	}
	svc := lant.New(c)
	if menus, err := svc.BoardRouteMenusForReview("s", "t", 6); err == nil || menus != nil {
		t.Fatalf("over-bound route returned %d partial menus and %v", len(menus), err)
	}
}

// caldChain is a target with a chain of size concepts leading to it. Extra
// edges attach further concepts.
func caldChain(size int, extra ...content.Edge) *content.Content {
	c := &content.Content{
		Nodes:          []content.Node{{ID: "target", LabelRO: "Țintă"}},
		CategoryLabels: map[string]string{"life": "Life"},
	}
	previous := "target"
	for i := 0; i < size; i++ {
		id := fmt.Sprintf("n-%03d", i)
		c.Nodes = append(c.Nodes, content.Node{ID: id, LabelRO: id})
		c.Edges = append(c.Edges, content.Edge{Src: id, Dst: previous, Strength: .8})
		previous = id
	}
	for _, edge := range extra {
		c.Nodes = append(c.Nodes, content.Node{ID: edge.Src, LabelRO: edge.Src})
		c.Edges = append(c.Edges, edge)
	}
	return c
}

func TestCaldReachableCountOnlyChangeIsListedButNotDisturbed(t *testing.T) {
	row := servedBoard("contexto", "board", map[string]any{"target": "target"})
	// One distant word enlarges the population and leaves the top 100 intact.
	before, after := caldChain(100), caldChain(101)
	parts, diagnostics := viewDelta(t, before, after, row)
	if len(parts) != 0 || len(diagnostics) != 2 || diagnostics[0] != "reachable_count" || diagnostics[1] != "top_100_native_scores" {
		t.Fatalf("a larger word count must only be a diagnostic: %v %v", parts, diagnostics)
	}
	before.PackItems, after.PackItems = []content.PackItem{row}, []content.PackItem{row}
	got, err := compare(before, after)
	if err != nil {
		t.Fatal(err)
	}
	if got.Schema != "cat-board-view-diff-2" || got.DisturbedTotal != 0 || got.Games["contexto"].Disturbed != 0 ||
		len(got.Diagnostics) != 1 || got.Diagnostics[0].boardKey != (boardKey{"contexto", "board"}) ||
		len(got.Diagnostics[0].Fields) != 2 || got.Diagnostics[0].BeforeSHA256 == got.Diagnostics[0].AfterSHA256 {
		t.Fatalf("reachable_count-only change must be listed for replay and not disturbed: %+v", got)
	}
}

func TestCaldTop100OrderOrMembershipChangeIsDisturbed(t *testing.T) {
	row := servedBoard("contexto", "board", map[string]any{"target": "target"})
	order := func(c *content.Content) []string {
		top, _ := contexto.New(c).BoardTopForReview("target")
		ids := make([]string, len(top))
		for i, guess := range top {
			ids[i] = guess.ID
		}
		return ids
	}
	near := func(a, b float64) *content.Content {
		return caldChain(3, content.Edge{Src: "x", Dst: "target", Strength: a}, content.Edge{Src: "y", Dst: "target", Strength: b})
	}
	before, after := near(.9, .5), near(.5, .9)
	left, right := order(before), order(after)
	if slices.Equal(left, right) {
		t.Fatalf("fixture did not reorder the top 100: %v", left)
	}
	slices.Sort(left)
	slices.Sort(right)
	if !slices.Equal(left, right) {
		t.Fatalf("fixture changed top-100 membership: %v %v", left, right)
	}
	if parts, _ := viewDelta(t, before, after, row); len(parts) != 1 || parts[0] != "top_100_ids" {
		t.Fatalf("a top-100 order change must disturb the board: %v", parts)
	}

	// A new word next to the target enters a full top 100 and drops the last.
	before, after = caldChain(100), caldChain(100, content.Edge{Src: "new", Dst: "target", Strength: .8})
	if parts, _ := viewDelta(t, before, after, row); len(parts) != 1 || parts[0] != "top_100_ids" {
		t.Fatalf("a top-100 membership change must disturb the board: %v", parts)
	}
	before.PackItems, after.PackItems = []content.PackItem{row}, []content.PackItem{row}
	got, err := compare(before, after)
	if err != nil {
		t.Fatal(err)
	}
	if got.DisturbedTotal != 1 || got.Disturbed[0].boardKey != (boardKey{"contexto", "board"}) ||
		len(got.Disturbed[0].Fields) != 1 || got.Disturbed[0].Fields[0] != "top_100_ids" || len(got.Diagnostics) != 1 {
		t.Fatalf("top-100 change must be disturbed and listed: %+v", got)
	}
}

func TestLanțShortestCaptionChangeIsListedButNotDisturbed(t *testing.T) {
	makeContent := func(caption string) *content.Content {
		return &content.Content{
			Nodes:        []content.Node{{ID: "s", LabelRO: "Start"}, {ID: "a", LabelRO: "A"}, {ID: "t", LabelRO: "Target"}},
			Edges:        []content.Edge{{Src: "s", Dst: "a", Strength: .8}, {Src: "a", Dst: "t", Strength: .8}},
			LantCaptions: map[string]string{"a\x00t": caption},
		}
	}
	row := content.PackItem{Game: "lant", Difficulty: "normal",
		Payload: map[string]any{"start": "s", "target": "t", "optimal": float64(2)}}
	parts, diagnostics := viewDelta(t, makeContent("old caption"), makeContent("new caption"), row)
	if len(parts) != 0 || len(diagnostics) != 2 || diagnostics[0] != "route_captions" || diagnostics[1] != "route_menus" {
		t.Fatalf("a shortest-route caption must only be a diagnostic: %v %v", parts, diagnostics)
	}
}
