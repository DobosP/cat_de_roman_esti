package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

const repoRoot = "../../.."

func syntheticAnalyzer(t *testing.T) *analyzer {
	t.Helper()
	ids := []string{"p", "s", "a", "b", "t", "w", "u", "z"}
	nodes := make([]content.Node, 0, len(ids))
	index := map[string]string{}
	for _, id := range ids {
		nodes = append(nodes, content.Node{ID: id, LabelRO: "nod " + id})
		index["nod"+id] = id
	}
	edge := func(src, dst string) content.Edge { return content.Edge{Src: src, Dst: dst, Strength: 1} }
	board := func(id, start, target string, par int) content.PackItem {
		return content.PackItem{Game: "lant", ID: id, Status: "approved", PilotEligible: true,
			Payload: map[string]any{"start": start, "target": target, "optimal": float64(par)}}
	}
	return mustAnalyzer(t, &content.Content{
		Nodes: nodes, NormalizedIndex: index,
		Edges: []content.Edge{
			edge("p", "s"), edge("s", "a"), edge("s", "b"), edge("a", "t"), edge("b", "t"),
			edge("w", "b"), edge("u", "a"),
		},
		PackItems: []content.PackItem{
			board("full", "p", "t", 3), // p-s-a-t and p-s-b-t
			board("one", "w", "t", 2),  // w-b-t only
		},
	})
}

func mustAnalyzer(t *testing.T, c *content.Content) *analyzer {
	t.Helper()
	a, err := newAnalyzer(c)
	if err != nil {
		t.Fatal(err)
	}
	return a
}

func findMatch(t *testing.T, r result, id string) match {
	t.Helper()
	for _, m := range r.Matches {
		if m.BoardID == id {
			return m
		}
	}
	t.Fatalf("no match for %s in %+v", id, r.Matches)
	return match{}
}

func TestSyntheticSubpathAndPartialOverlap(t *testing.T) {
	a := syntheticAnalyzer(t)
	// s-a-t and s-b-t are both contiguous inside the routes of "full".
	r, err := a.compare(prospect{Start: "s", Target: "t"}, "")
	if err != nil {
		t.Fatal(err)
	}
	full := findMatch(t, r, "full")
	if !r.NearDuplicate || !full.Subpath || full.RoutesCovered != 2 || full.ProspectRoutes != 2 || full.BoardRoutes != 2 ||
		full.SharedSteps != 4 || strings.Join(full.SharedNodes, ",") != "a,b,s,t" || full.MenuOverlap.Share != 1 {
		t.Fatalf("full overlap not reported: %+v", r)
	}
	// "one" only contains s-b-t's tail (w-b-t): not every route is covered.
	one := findMatch(t, r, "one")
	if one.Subpath || one.RoutesCovered != 0 || one.SharedSteps != 1 {
		t.Fatalf("partial overlap must not be a sub-path: %+v", one)
	}
	if r.Matches[0].BoardID != "full" {
		t.Fatalf("sub-path matches must sort first: %+v", r.Matches)
	}
}

func TestSyntheticPartialRouteCoverage(t *testing.T) {
	a := syntheticAnalyzer(t)
	// u-a-t lies inside p-s-a-t only as the tail a-t, so the u start is not a sub-path.
	r, err := a.compare(prospect{Start: "u", Target: "t"}, "")
	if err != nil {
		t.Fatal(err)
	}
	if r.NearDuplicate || r.MatchesTotal == 0 {
		t.Fatalf("shared step but different start must not be near duplicate: %+v", r)
	}
	if m := findMatch(t, r, "full"); m.Subpath || m.SharedNodes[0] != "a" {
		t.Fatalf("unexpected match: %+v", m)
	}
}

func TestSyntheticDirectionAndExclusion(t *testing.T) {
	a := syntheticAnalyzer(t)
	// Moves are directed: t does not reach s, so the reverse prospect is refused.
	if _, err := a.compare(prospect{Start: "t", Target: "s"}, ""); err == nil {
		t.Fatal("expected unreachable reverse prospect to be refused")
	}
	// A served board compared with itself excluded is not flagged by itself.
	r, err := a.compare(prospect{Start: "p", Target: "t"}, "full")
	if err != nil {
		t.Fatal(err)
	}
	for _, m := range r.Matches {
		if m.BoardID == "full" {
			t.Fatal("excluded board was compared")
		}
	}
	// Without exclusion it is an exact duplicate of itself.
	r, err = a.compare(prospect{Start: "p", Target: "t"}, "")
	if err != nil || !r.NearDuplicate {
		t.Fatalf("exact duplicate must be flagged: %+v, %v", r, err)
	}
	bad := 1
	if _, err := a.compare(prospect{Start: "p", Target: "t", Par: &bad}, ""); err == nil {
		t.Fatal("par below the shortest distance must be refused")
	}
}

func TestRouteCapRefusesRatherThanTruncates(t *testing.T) {
	next := map[string][]string{}
	// 13 diamonds in series give 2^13 = 8192 shortest routes.
	prev := "n0"
	for i := range 13 {
		a, b, join := "a"+string(rune('A'+i)), "b"+string(rune('A'+i)), "n"+string(rune('1'+i))
		next[prev] = []string{a, b}
		next[a], next[b] = []string{join}, []string{join}
		prev = join
	}
	if _, err := enumerate(next, "n0", prev); err == nil {
		t.Fatal("expected the route cap to refuse")
	}
}

func TestParseListRejectsUnsafeInput(t *testing.T) {
	good := `[{"start":"a","target":"b"},{"start":"c","target":"d","par":3}]`
	if work, err := parseList([]byte(good)); err != nil || len(work) != 2 || *work[1].Par != 3 {
		t.Fatalf("good list rejected: %v", err)
	}
	many := "[" + strings.Repeat(`{"start":"a","target":"b"},`, maxProspects) + `{"start":"a","target":"b"}]`
	for name, raw := range map[string]string{
		"unknown field": `[{"start":"a","target":"b","x":1}]`,
		"duplicate key": `[{"start":"a","start":"c","target":"b"}]`,
		"trailing":      good + `[]`,
		"empty list":    `[]`,
		"missing id":    `[{"start":"a"}]`,
		"negative par":  `[{"start":"a","target":"b","par":-1}]`,
		"too many":      many,
		"not utf8":      "[{\"start\":\"\xff\",\"target\":\"b\"}]",
	} {
		if _, err := parseList([]byte(raw)); err == nil {
			t.Errorf("%s: accepted", name)
		}
	}
}

func runBundle(t *testing.T, args ...string) report {
	t.Helper()
	var out bytes.Buffer
	if err := run(append([]string{"--root", repoRoot}, args...), &out, &out); err != nil {
		t.Fatal(err)
	}
	var got report
	if err := json.Unmarshal(out.Bytes(), &got); err != nil {
		t.Fatal(err)
	}
	return got
}

func TestBundleFlagsTheOwnerQueueCase(t *testing.T) {
	got := runBundle(t, "--start", "n_transilvania", "--target", "n_muntii_apuseni")
	if got.Schema != "cat-lant-overlap-1" || len(got.BundleSHA256) != 64 || got.ServedBoards != 126 || len(got.Prospects) != 1 {
		t.Fatalf("unexpected report header: %+v", got)
	}
	p := got.Prospects[0]
	if !p.NearDuplicate || p.Matches[0].BoardID != "lt_geografie_239" || !p.Matches[0].Subpath || p.Matches[0].MenuOverlap.Share != 1 {
		t.Fatalf("lt_geografie_239 not flagged first: %+v", p)
	}
	again := runBundle(t, "--start", "n_transilvania", "--target", "n_muntii_apuseni")
	first, _ := json.Marshal(got)
	second, _ := json.Marshal(again)
	if !bytes.Equal(first, second) {
		t.Fatal("report is not deterministic")
	}
}

func TestBundleServedSanityIsNotAllFlagged(t *testing.T) {
	got := runBundle(t, "--served-sanity")
	s := got.Summary
	if s.Prospects != got.ServedBoards || s.NearDuplicates*2 >= s.Prospects {
		t.Fatalf("sanity summary should flag only a small minority: %+v", s)
	}
	for _, p := range got.Prospects {
		if p.NearDuplicate != (len(p.Matches) > 0 && p.Matches[0].Subpath) {
			t.Fatalf("near_duplicate disagrees with its top match: %+v", p)
		}
	}
}

func TestListFileAndFlagValidation(t *testing.T) {
	path := filepath.Join(t.TempDir(), "list.json")
	if err := os.WriteFile(path, []byte(`[{"start":"n_transilvania","target":"n_muntii_apuseni"}]`), 0o600); err != nil {
		t.Fatal(err)
	}
	got := runBundle(t, "--prospects", path)
	if got.Mode != "prospects" || got.Summary.NearDuplicates != 1 {
		t.Fatalf("list run: %+v", got.Summary)
	}
	link := filepath.Join(t.TempDir(), "link.json")
	if err := os.Symlink(path, link); err == nil {
		var out bytes.Buffer
		if run([]string{"--root", repoRoot, "--prospects", link}, &out, &out) == nil {
			t.Fatal("symlinked list accepted")
		}
	}
	for _, args := range [][]string{
		{}, {"--root", repoRoot}, {"--root", repoRoot, "--start", "a"},
		{"--root", repoRoot, "--served-sanity", "--start", "a", "--target", "b"},
		{"--root", repoRoot, "--start", "nope", "--target", "n_muntii_apuseni"},
	} {
		var out bytes.Buffer
		if run(args, &out, &out) == nil {
			t.Errorf("args %v accepted", args)
		}
	}
}
