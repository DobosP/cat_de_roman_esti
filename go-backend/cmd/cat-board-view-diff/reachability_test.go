package main

import (
	"fmt"
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

func TestLanțOpeningOnlyCaptionChangeUsesS7ButNotDryRun(t *testing.T) {
	makeContent := func(caption string) *content.Content {
		return &content.Content{
			Nodes: []content.Node{{ID: "s", LabelRO: "Start"}, {ID: "a", LabelRO: "A"},
				{ID: "t", LabelRO: "Target"}, {ID: "d", LabelRO: "Detour"},
				{ID: "e", LabelRO: "Next"}, {ID: "f", LabelRO: "Further"}, {ID: "g", LabelRO: "Last"}},
			Edges: []content.Edge{{Src: "s", Dst: "a", Strength: .8}, {Src: "a", Dst: "t", Strength: .8},
				{Src: "s", Dst: "d", Strength: .8}, {Src: "d", Dst: "e", Strength: .8},
				{Src: "e", Dst: "f", Strength: .8}, {Src: "f", Dst: "g", Strength: .8}, {Src: "g", Dst: "t", Strength: .8}},
			LantCaptions:   map[string]string{"s\x00d": caption},
			CategoryLabels: map[string]string{"life": "Life"},
		}
	}
	row := content.PackItem{Game: "lant", Category: "life", Difficulty: "normal",
		Payload: map[string]any{"start": "s", "target": "t", "optimal": float64(2)}}
	before := makeContent("Old detour")
	after := makeContent("New detour")
	for _, dry := range []bool{false, true} {
		left := services{data: before, g: graph.New(before), lant: lant.New(before)}
		right := services{data: after, g: graph.New(after), lant: lant.New(after)}
		old, err := left.packView(row, dry)
		if err != nil {
			t.Fatal(err)
		}
		next, err := right.packView(row, dry)
		if err != nil {
			t.Fatal(err)
		}
		where := changedFields(old.parts, next.parts)
		diagnostics := changedFields(old.diagnostic, next.diagnostic)
		if dry && (len(where) != 0 || len(diagnostics) != 1 || diagnostics[0] != "route_menus") {
			t.Fatalf("dry-run counted a detour caption: %v %v", where, diagnostics)
		}
		if !dry && (len(where) != 1 || where[0] != "route_menus" || len(diagnostics) != 0) {
			t.Fatalf("S7 missed the displayed detour caption: %v %v", where, diagnostics)
		}
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

func TestCaldSameIDsChangedDenominatorUsesS7ButNotDryRun(t *testing.T) {
	makeContent := func(extra bool) *content.Content {
		c := &content.Content{
			Nodes:          []content.Node{{ID: "target", LabelRO: "Țintă"}},
			CategoryLabels: map[string]string{"life": "Life"},
		}
		previous := "target"
		size := 100
		if extra {
			size++
		}
		for i := 0; i < size; i++ {
			id := fmt.Sprintf("n-%03d", i)
			c.Nodes = append(c.Nodes, content.Node{ID: id, LabelRO: id})
			c.Edges = append(c.Edges, content.Edge{Src: id, Dst: previous, Strength: .8})
			previous = id
		}
		return c
	}
	row := content.PackItem{Game: "contexto", Category: "life", Difficulty: "normal", Payload: map[string]any{"target": "target"}}
	a, b := makeContent(false), makeContent(true)
	left, right := services{data: a, g: graph.New(a), cald: contexto.New(a)}, services{data: b, g: graph.New(b), cald: contexto.New(b)}
	for _, dry := range []bool{false, true} {
		old, err := left.packView(row, dry)
		if err != nil {
			t.Fatal(err)
		}
		next, err := right.packView(row, dry)
		if err != nil {
			t.Fatal(err)
		}
		fields := changedFields(old.parts, next.parts)
		diagnostic := changedFields(old.diagnostic, next.diagnostic)
		if dry && (len(fields) != 0 || len(diagnostic) != 2) {
			t.Fatalf("unexpected dry feedback delta: %v %v", fields, diagnostic)
		}
		if !dry && (len(fields) != 2 || fields[0] != "reachable_count" || fields[1] != "top_100_native_scores") {
			t.Fatalf("S7 missed the displayed Cald feedback delta: %v", fields)
		}
	}
}

func TestLanțShortestCaptionUsesS7ButNotDryRun(t *testing.T) {
	makeContent := func(caption string) *content.Content {
		return &content.Content{
			Nodes:        []content.Node{{ID: "s", LabelRO: "Start"}, {ID: "a", LabelRO: "A"}, {ID: "t", LabelRO: "Target"}},
			Edges:        []content.Edge{{Src: "s", Dst: "a", Strength: .8}, {Src: "a", Dst: "t", Strength: .8}},
			LantCaptions: map[string]string{"a\x00t": caption},
		}
	}
	row := content.PackItem{Game: "lant", Difficulty: "normal",
		Payload: map[string]any{"start": "s", "target": "t", "optimal": float64(2)}}
	a, b := makeContent("old caption"), makeContent("new caption")
	left, right := services{data: a, g: graph.New(a), lant: lant.New(a)}, services{data: b, g: graph.New(b), lant: lant.New(b)}
	for _, dry := range []bool{false, true} {
		old, err := left.packView(row, dry)
		if err != nil {
			t.Fatal(err)
		}
		next, err := right.packView(row, dry)
		if err != nil {
			t.Fatal(err)
		}
		fields := changedFields(old.parts, next.parts)
		diagnostic := changedFields(old.diagnostic, next.diagnostic)
		if dry && (len(fields) != 0 || len(diagnostic) != 2) {
			t.Fatalf("unexpected dry shortest caption delta: %v %v", fields, diagnostic)
		}
		if !dry && (len(fields) != 2 || fields[0] != "route_captions" || fields[1] != "route_menus") {
			t.Fatalf("S7 missed displayed shortest caption: %v", fields)
		}
	}
}
