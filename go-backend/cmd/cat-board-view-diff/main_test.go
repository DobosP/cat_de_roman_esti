package main

import (
	"bytes"
	"encoding/json"
	"maps"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/lant"
)

const bundledPath = "../../internal/content/bundled.json"

func TestExactBundleReplay(t *testing.T) {
	blob, err := os.ReadFile(bundledPath)
	if err != nil {
		t.Fatal(err)
	}
	sha := contentbuild.SHA256(blob)
	args := []string{"--baseline", bundledPath, "--baseline-sha256", sha, "--candidate", bundledPath, "--candidate-sha256", sha}
	var out bytes.Buffer
	if err := run(args, &out, &out); err != nil {
		t.Fatal(err)
	}
	var got report
	if err := json.Unmarshal(out.Bytes(), &got); err != nil {
		t.Fatal(err)
	}
	if got.Schema != "cat-board-view-diff-2" || got.BaselineSHA256 != sha || got.CandidateSHA256 != sha ||
		len(got.Games) != 6 || len(got.Added)+len(got.Disturbed)+len(got.SelectionChanges)+len(got.Diagnostics) != 0 || got.DisturbedTotal != 0 {
		t.Fatalf("unexpected replay report: %s", out.String())
	}
	expected := map[string][3]int{
		"alchimie": {68, 80, 12}, "conexiuni": {95, 257, 162}, "contexto": {257, 265, 8},
		"intrusul": {201, 0, 0}, "lant": {126, 126, 0}, "perechi": {176, 0, 0},
	}
	for game, want := range expected {
		count := got.Games[game]
		if count == nil || [3]int{count.Baseline, count.BaselineApproved, count.BaselineExcluded} != want || count.Baseline != count.Candidate {
			t.Fatalf("%s: %+v, expected %v", game, count, want)
		}
	}

	if got.Games["intrusul"].BaselineQuickStored != 226 || got.Games["intrusul"].BaselineQuickUnreachable != 25 ||
		got.Games["perechi"].BaselineQuickStored != 192 || got.Games["perechi"].BaselineQuickUnreachable != 16 {
		t.Fatalf("wrong Quick shelf scope: %+v %+v", got.Games["intrusul"], got.Games["perechi"])
	}

	out.Reset()
	args[3] = strings.Repeat("0", 64)
	if err := run(args, &out, &out); err == nil || !strings.Contains(err.Error(), "SHA-256 mismatch") || out.Len() != 0 {
		t.Fatalf("expected digest refusal without report, got %v and %s", err, out.String())
	}
}

func TestDuplicateJSONRefusedWithMatchingDigest(t *testing.T) {
	raw := []byte(`{"schema_version":2,"schema_version":2}`)
	file := filepath.Join(t.TempDir(), "bundle.json")
	if err := os.WriteFile(file, raw, 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := loadBundle(file, contentbuild.SHA256(raw)); err == nil || !strings.Contains(err.Error(), "duplicate JSON object key") {
		t.Fatalf("expected duplicate JSON key refusal, got %v", err)
	}
}

func TestBoardUnionAndDisturbanceAccounting(t *testing.T) {
	key := func(game, id string) boardKey { return boardKey{game, id} }
	view := func(id, selection, diagnostics string) boardView {
		return boardView{map[string]string{"visible": id}, map[string]any{"selection_weight": selection}, map[string]string{"score": diagnostics}}
	}
	before := inventory{boards: map[boardKey]boardView{
		key("alchimie", "same"):  view("old", "1", "a"),
		key("contexto", "same"):  view("stable", "2", "a"),
		key("intrusul", "gone"):  view("visible", "1", "a"),
		key("lant", "same"):      view("old", "1", "a"),
		key("perechi", "weight"): view("stable", "1", "a"),
	}}
	after := inventory{boards: map[boardKey]boardView{
		key("alchimie", "same"):   view("new", "1", "a"),
		key("conexiuni", "added"): view("visible", "1", "a"),
		key("contexto", "same"):   view("stable", "2", "b"),
		key("lant", "same"):       view("new", "1", "a"),
		key("perechi", "weight"):  view("stable", "2", "a"),
	}}
	got := compareInventories(before, after)
	if got.DisturbedTotal != 3 || len(got.Added) != 1 || len(got.SelectionChanges) != 1 || len(got.Diagnostics) != 1 {
		t.Fatalf("unexpected report: %+v", got)
	}
	if got.Disturbed[0].Game != "alchimie" || got.Disturbed[1].Kind != "removed" ||
		got.Disturbed[1].Game != "intrusul" || got.Disturbed[2].Game != "lant" {
		t.Fatalf("wrong disturbed list: %+v", got.Disturbed)
	}
	if got.Games["contexto"].Disturbed != 0 || got.Games["perechi"].Disturbed != 0 || got.Games["intrusul"].Removed != 1 {
		t.Fatalf("wrong per-game counts: %+v", got.Games)
	}
}

func TestLanțIncludesEveryDirectedShortestBranchAndCaption(t *testing.T) {
	c := &content.Content{
		Nodes: []content.Node{{ID: "s"}, {ID: "a"}, {ID: "b"}, {ID: "c"}, {ID: "t"}, {ID: "z"}},
		Edges: []content.Edge{
			{Src: "s", Dst: "a"}, {Src: "s", Dst: "b"}, {Src: "s", Dst: "c"},
			{Src: "a", Dst: "t"}, {Src: "b", Dst: "t"}, {Src: "t", Dst: "c"},
			{Src: "s", Dst: "z", IsDistractor: true}, {Src: "z", Dst: "t"},
		},
		LantCaptions: map[string]string{"a\x00t": "leads to", "s\x00b": "o descriere mai lungă pentru relația dintre cuvinte"},
	}
	svc := lant.New(c)
	length, steps := svc.BoardShortestRoutesForReview("s", "t")
	if length != 2 || len(steps) != 4 ||
		steps[0].From != "a" || steps[0].To != "t" || steps[0].Caption != "leads to" ||
		steps[1].From != "b" || steps[1].To != "t" ||
		steps[2].From != "s" || steps[2].To != "a" ||
		steps[3].From != "s" || steps[3].To != "b" || steps[3].ShortCaption == steps[3].Caption {
		t.Fatalf("wrong DAG or captions: %d, %+v", length, steps)
	}
	if reverse, edges := svc.BoardShortestRoutesForReview("t", "s"); reverse != -1 || len(edges) != 0 {
		t.Fatalf("unexpected reverse route: %d, %+v", reverse, edges)
	}
}

func TestAdditiveWordContract(t *testing.T) {
	before := &content.Content{
		Nodes:   []content.Node{{ID: "a"}, {ID: "b"}, {ID: "c"}, {ID: "d"}},
		Edges:   []content.Edge{{ID: "ab", Src: "a", Dst: "b"}},
		Sources: map[string]string{"games_pack.json": "exact"},
	}
	after := &content.Content{
		Nodes: append(slices.Clone(before.Nodes), content.Node{ID: "word", NodeType: "concept"}),
		Edges: append(slices.Clone(before.Edges), content.Edge{ID: "aw", Src: "a", Dst: "word"},
			content.Edge{ID: "bw", Src: "b", Dst: "word"}, content.Edge{ID: "cw", Src: "c", Dst: "word"},
			content.Edge{ID: "dw", Src: "d", Dst: "word"}),
		Sources: maps.Clone(before.Sources),
	}
	after.Nodes[0].Degree++
	word, err := additiveWord(before, after)
	if err != nil || word != "word" {
		t.Fatalf("valid one-word graph rejected: %q, %v", word, err)
	}
	after.Edges[0].Relation = "changed"
	if _, err := additiveWord(before, after); err == nil {
		t.Fatal("dry run accepted a rewrite to an existing edge")
	}
	after.Edges[0].Relation = ""
	after.Edges[1].Src = "b"
	after.Edges[1].Dst = "c"
	if _, err := additiveWord(before, after); err == nil {
		t.Fatal("dry run accepted an added edge not connected to the word")
	}
}
