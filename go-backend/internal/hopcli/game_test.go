package hopcli

import (
	"bufio"
	"bytes"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/roeduclient"
	"strings"
	"testing"
)

func synthetic(t *testing.T) *Bundle {
	t.Helper()
	nodes := []roeduclient.Record{}
	for _, id := range []string{"s", "a", "b", "t", "d", "x"} {
		nodes = append(nodes, roeduclient.Record{"id": id, "label_ro": id})
	}
	edges := []roeduclient.Record{}
	for _, p := range [][2]string{{"s", "a"}, {"a", "b"}, {"b", "t"}, {"s", "b"}, {"s", "d"}, {"d", "a"}} {
		edges = append(edges, roeduclient.Record{"id": p[0] + p[1], "src_id": p[0], "dst_id": p[1], "strength": 0.9, "label_ro": "link"})
	}
	edges = append(edges, roeduclient.Record{"id": "sx", "src_id": "s", "dst_id": "x", "strength": 1.0, "is_distractor": true})
	b, err := Parse(roeduclient.Bundle{Nodes: nodes, Edges: edges, Puzzles: []roeduclient.Record{{"id": "p", "start_id": "s", "target_id": "t", "optimal_hops": 3, "par": 3, "difficulty": "easy", "solution_path": []string{"s", "a", "b", "t"}, "hint_neighbors": []string{"a", "b", "t"}}}})
	if err != nil {
		t.Fatal(err)
	}
	return b
}
func TestLegacyMechanics(t *testing.T) {
	b := synthetic(t)
	g, err := New(b.Graph, b.Puzzles[0], " EASY ")
	if err != nil {
		t.Fatal(err)
	}
	if g.Score() != 0 || g.Undo().OK || g.Hop("s").OK || g.Hop("t").OK || g.Hop("x").OK {
		t.Fatal("invalid move changed fresh game")
	}
	if hints := g.Hints(); len(hints) != 1 || hints[0] != "a" {
		t.Fatal(hints)
	}
	if !g.Hop("d").OK {
		t.Fatal("detour")
	}
	if hints := g.Hints(); len(hints) != 1 || hints[0] != "a" {
		t.Fatal(hints)
	}
	for _, id := range []string{"a", "b", "t"} {
		if !g.Hop(id).OK {
			t.Fatal(id)
		}
	}
	if !g.Won() || g.Hops() != 4 || g.Score() != 900 || g.Hop("b").OK || len(g.Hints()) != 0 {
		t.Fatal(g.Summary())
	}
	if !g.Undo().OK || g.Won() {
		t.Fatal("undo win")
	}
	for g.Hops() > 0 {
		g.Undo()
	}
	for _, id := range []string{"a", "b", "t"} {
		g.Hop(id)
	}
	if g.Score() != 1000 {
		t.Fatal("undo failed perfect replay")
	}
	hard, _ := New(b.Graph, b.Puzzles[0], "hard")
	if !hard.Hop("x").OK || len(hard.Hints()) != 0 {
		t.Fatal("hard hides hints and keeps distractors")
	}
	if _, err = New(b.Graph, b.Puzzles[0], "nightmare"); err == nil {
		t.Fatal("mode accepted")
	}
}
func TestAllFrozenPuzzlesSolveWithoutSkips(t *testing.T) {
	b, err := ReadFixture("../../../cat_de_roman_esti/fixtures/kg_sample.json")
	if err != nil {
		t.Fatal(err)
	}
	if len(b.Puzzles) != 180 {
		t.Fatalf("unexpected frozen corpus: %d", len(b.Puzzles))
	}
	for _, p := range b.Puzzles {
		t.Run(p.ID, func(t *testing.T) {
			g, err := New(b.Graph, p, p.Difficulty)
			if err != nil {
				t.Fatal(err)
			}
			if len(p.SolutionPath) < 2 || p.SolutionPath[0] != p.StartID {
				t.Fatal("invalid frozen path")
			}
			for _, id := range p.SolutionPath[1:] {
				if !g.Hop(id).OK {
					t.Fatal(id)
				}
			}
			if !g.Won() || g.Hops() != p.OptimalHops || g.Hops() != p.Par || g.Score() != 1000 {
				t.Fatal(g.Summary())
			}
		})
	}
}
func TestInteractiveWinQuitEOFAndCap(t *testing.T) {
	b := synthetic(t)
	for _, input := range []string{"q\n", "", "bad\nbad\n"} {
		g, _ := New(b.Graph, b.Puzzles[0], "easy")
		var out bytes.Buffer
		summary := Play(g, bufio.NewScanner(strings.NewReader(input)), &out, 2)
		if summary["won"] != false || g.Hops() != 0 {
			t.Fatal(summary)
		}
	}
	g, _ := New(b.Graph, b.Puzzles[0], "easy")
	var input strings.Builder
	for _, id := range []string{"a", "b", "t"} {
		for i, n := range g.Options() {
			if n.ID == id {
				input.WriteString(string(rune('1'+i)) + "\n")
				break
			}
		}
		g.Hop(id)
	}
	g, _ = New(b.Graph, b.Puzzles[0], "easy")
	var out bytes.Buffer
	Play(g, bufio.NewScanner(strings.NewReader(input.String())), &out, 100)
	if !g.Won() || !strings.Contains(out.String(), "WIN!") {
		t.Fatal(out.String())
	}
}
func TestSmokeRefusesBadSolution(t *testing.T) {
	b := synthetic(t)
	if _, err := Smoke(b, "easy"); err != nil {
		t.Fatal(err)
	}
	b.Puzzles[0].SolutionPath = []string{"s", "t"}
	if _, err := Smoke(b, "easy"); err == nil {
		t.Fatal("illegal path accepted")
	}
}

func TestScoreFloorAndMissingEndpoints(t *testing.T) {
	b := synthetic(t)
	g, _ := New(b.Graph, b.Puzzles[0], "easy")
	for i := 0; i < 20; i++ {
		if !g.Hop("a").OK || !g.Hop("s").OK {
			t.Fatal("real cycle failed")
		}
	}
	for _, id := range []string{"a", "b", "t"} {
		g.Hop(id)
	}
	if g.Score() != 100 {
		t.Fatal("winning floor", g.Score())
	}
	p := b.Puzzles[0]
	p.StartID = "missing"
	if _, err := New(b.Graph, p, "easy"); err == nil {
		t.Fatal("missing start accepted")
	}
	p = b.Puzzles[0]
	p.TargetID = "missing"
	if _, err := New(b.Graph, p, "easy"); err == nil {
		t.Fatal("missing target accepted")
	}
}

func TestEmptyCategoryCannotPanicSelection(t *testing.T) {
	b := synthetic(t)
	cats := Categories(b)
	if len(cats) != 1 || cats[0] != "" {
		t.Fatal(cats)
	}
}
