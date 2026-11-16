package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"maps"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contexto"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

func TestReblindVerdictRule(t *testing.T) {
	for _, c := range []struct {
		won                    bool
		candidate, baseline, k int
		want                   string
	}{
		{true, 1, 1, 0, "win"},
		{true, 1, 40, 0, "win"},
		{false, 5, 5, 0, "no-worse"},
		{false, 4, 5, 0, "no-worse"},
		{false, 6, 5, 0, "worse"},
		// One candidate-only concept above the best guess explains one rank.
		{false, 6, 5, 1, "no-worse"},
		{false, 7, 5, 1, "worse"},
		{false, 8, 5, 3, "no-worse"},
		{false, 2, 1, 0, "worse"},
	} {
		if got := reblindVerdict(c.won, c.candidate, c.baseline, c.k); got != c.want {
			t.Errorf("won=%v candidate=%d baseline=%d k=%d: %s, want %s", c.won, c.candidate, c.baseline, c.k, got, c.want)
		}
	}
}

// reblindContent has the board "moved" on target tinta. The candidate adds
// the word nou next to the target and a shortcut from z through it.
func reblindContent(candidate bool) *content.Content {
	c := &content.Content{CategoryLabels: map[string]string{"life": "Life"}, NormalizedIndex: map[string]string{}}
	add := func(ids ...string) {
		for _, id := range ids {
			c.Nodes = append(c.Nodes, content.Node{ID: id, LabelRO: id})
			c.NormalizedIndex[id] = id
		}
	}
	link := func(src, dst string) { c.Edges = append(c.Edges, content.Edge{Src: src, Dst: dst, Strength: .8}) }
	add("tinta", "a", "b", "c", "z", "alta")
	link("a", "tinta")
	link("b", "a")
	link("c", "b")
	link("z", "c")
	if candidate {
		add("nou")
		link("nou", "tinta")
		link("z", "nou")
	}
	c.PackItems = []content.PackItem{
		servedBoard("contexto", "moved", map[string]any{"target": "tinta"}),
		servedBoard("contexto", "still", map[string]any{"target": "alta"}),
	}
	return c
}

func partsSHA(t *testing.T, c *content.Content, id string) string {
	t.Helper()
	s := services{data: c, g: graph.New(c), cald: contexto.New(c)}
	item, err := s.servedCald(id)
	if err != nil {
		t.Fatal(err)
	}
	view, err := s.packView(item)
	if err != nil {
		t.Fatal(err)
	}
	return hashFields(view.parts)
}

func TestPairedReblindReplaysNativeGuessesOnBothBuilds(t *testing.T) {
	before, after := reblindContent(false), reblindContent(true)
	play := func(guesses ...string) reblindCase {
		return reblindCase{key: boardKey{"contexto", "moved"}, before: partsSHA(t, before, "moved"),
			after: partsSHA(t, after, "moved"), thread: "critic", guesses: guesses}
	}
	type numbers struct {
		guesses, candidateScored, baselineScored, candidateBest, baselineBest, k int
		wonCandidate, wonBaseline, stock                                         bool
		verdict                                                                  string
	}
	for name, c := range map[string]struct {
		guesses []string
		want    numbers
	}{
		// nou outranks b in the candidate, so the same guess sits one rank lower.
		"k tolerance": {[]string{"b"}, numbers{1, 1, 1, 4, 3, 1, false, false, true, "no-worse"}},
		"same rank":   {[]string{"a"}, numbers{1, 1, 1, 2, 2, 0, false, false, true, "no-worse"}},
		// z now reaches the target through nou and overtakes c. k covers only nou.
		"worse":          {[]string{"c"}, numbers{1, 1, 1, 6, 4, 1, false, false, true, "worse"}},
		"new word guess": {[]string{"necunoscut", "nou", "b"}, numbers{3, 2, 1, 2, 3, 0, false, false, true, "no-worse"}},
		"win stops play": {[]string{"b", "tinta", "a"}, numbers{3, 2, 2, 1, 1, 0, true, true, false, "win"}},
	} {
		rows, err := compareReblind(before, after, []reblindCase{play(c.guesses...)})
		if err != nil || len(rows) != 1 {
			t.Fatalf("%s: %v %+v", name, err, rows)
		}
		r := rows[0]
		got := numbers{r.Guesses, r.CandidateScored, r.BaselineScored, r.CandidateBest, r.BaselineBest, r.K,
			r.WonCandidate, r.WonBaseline, r.StockQuality, r.Verdict}
		if got != c.want {
			t.Errorf("%s: %+v, want %+v", name, got, c.want)
		}
	}
	if _, err := compareReblind(before, after, []reblindCase{play("necunoscut")}); err == nil || !strings.Contains(err.Error(), "scored native guess") {
		t.Fatalf("a play without any scored guess must be refused: %v", err)
	}
	stale := play("b")
	stale.after = stale.before
	if _, err := compareReblind(before, after, []reblindCase{stale}); err == nil || !strings.Contains(err.Error(), "native bundle view") {
		t.Fatalf("a view hash from another bundle must be refused: %v", err)
	}
	held := reblindContent(true)
	held.PackItems[0].PilotEligible = false
	if _, err := compareReblind(before, held, []reblindCase{play("b")}); err == nil || !strings.Contains(err.Error(), "served Cald row") {
		t.Fatalf("an unserved board must be refused: %v", err)
	}
}

func TestPairedReblindReceiptBindsExactEvidence(t *testing.T) {
	before, after := reblindContent(false), reblindContent(true)
	beforeSHA, afterSHA := strings.Repeat("a", 64), strings.Repeat("b", 64)
	diff, err := compare(before, after)
	if err != nil {
		t.Fatal(err)
	}
	diff.BaselineSHA256, diff.CandidateSHA256 = beforeSHA, afterSHA
	if diff.DisturbedTotal != 1 || diff.Disturbed[0].ID != "moved" {
		t.Fatalf("fixture must disturb exactly the moved board: %+v", diff.Disturbed)
	}
	root := t.TempDir()
	write := func(name string, value any) fileRef {
		t.Helper()
		raw, ok := value.([]byte)
		if !ok {
			if raw, err = json.Marshal(value); err != nil {
				t.Fatal(err)
			}
		}
		path := filepath.Join(root, filepath.FromSlash(name))
		if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, raw, 0600); err != nil {
			t.Fatal(err)
		}
		return fileRef{name, contentbuild.SHA256(raw)}
	}
	transcript := func(overrides map[string]any) map[string]any {
		doc := map[string]any{"game": "contexto", "id": "moved", "view_sha256": diff.Disturbed[0].AfterSHA256,
			"thread_id": "blind-critic", "verdict": "fail", "play": []any{
				map[string]any{"guess": "b", "reason": "aproape"},
				map[string]any{"feedback": "Primul reper", "guess": map[string]any{"label": "b", "rank": 4}},
				map[string]any{"guess": "a"},
			}}
		for key, value := range overrides {
			doc[key] = value
		}
		return doc
	}
	diffRef := write("board-diff.json", diff)
	good := write("reblind/moved.json", transcript(nil))
	lists := 0
	list := func(boards ...map[string]any) string {
		lists++
		name := fmt.Sprintf("list-%d.json", lists)
		return filepath.Join(root, write(name, map[string]any{"schema": reblindInputSchema, "boards": boards}).Path)
	}
	board := func(id string, ref fileRef) map[string]any {
		return map[string]any{"game": "contexto", "id": id, "transcript": ref}
	}
	files := func(input string) reblindFiles {
		return reblindFiles{diff: filepath.Join(root, diffRef.Path), diffSHA: diffRef.SHA256, baselineCommit: strings.Repeat("1", 40),
			candidateCommit: strings.Repeat("2", 40), root: root, input: input}
	}
	receipt, err := files(list(board("moved", good))).compare(before, after, beforeSHA, afterSHA)
	if err != nil {
		t.Fatal(err)
	}
	row := receipt.Boards[0]
	if receipt.Schema != "cat-v5-board-reblind-compare-1" || receipt.Baseline != strings.Repeat("1", 40) || receipt.SHA != strings.Repeat("2", 40) ||
		receipt.BaselineSHA256 != beforeSHA || receipt.CandidateSHA256 != afterSHA || receipt.ViewDiffSHA256 != diffRef.SHA256 ||
		len(receipt.Boards) != 1 || row.boardKey != (boardKey{"contexto", "moved"}) ||
		row.ViewSHA256 != diff.Disturbed[0].AfterSHA256 || row.BaselineViewSHA256 != diff.Disturbed[0].BeforeSHA256 ||
		row.ThreadID != "blind-critic" || row.Transcript != good || row.Guesses != 2 || row.CandidateBest != 2 || row.BaselineBest != 2 ||
		row.Verdict != "no-worse" || !row.StockQuality || receipt.Totals["no-worse"] != 1 || receipt.Totals["stock_quality"] != 1 {
		t.Fatalf("unexpected receipt: %+v", receipt)
	}
	// scripts/content_v5/close_landing.py requires exactly these receipt members.
	members := func(value any) string {
		raw, err := json.Marshal(value)
		if err != nil {
			t.Fatal(err)
		}
		var decoded map[string]json.RawMessage
		if err := json.Unmarshal(raw, &decoded); err != nil {
			t.Fatal(err)
		}
		return strings.Join(slices.Sorted(maps.Keys(decoded)), " ")
	}
	if got := members(receipt); got != "baseline baseline_bundle_sha256 board_view_diff_sha256 boards candidate_bundle_sha256 schema sha totals" {
		t.Fatalf("receipt members changed without closeout: %s", got)
	}
	if got := members(row); got != "baseline_best_rank baseline_scored_guesses baseline_view_sha256 candidate_best_rank candidate_scored_guesses "+
		"game guesses id k stock_quality thread_id transcript verdict view_sha256 won_baseline won_candidate" {
		t.Fatalf("receipt row members changed without closeout: %s", got)
	}
	var first, second bytes.Buffer
	again, _ := files(list(board("moved", good))).compare(before, after, beforeSHA, afterSHA)
	if writeReport(receipt, &first) != nil || writeReport(again, &second) != nil || !bytes.Equal(first.Bytes(), second.Bytes()) ||
		strings.Contains(first.String(), "aproape") {
		t.Fatalf("receipt must be deterministic and hold no play text: %s", first.String())
	}

	tampered := good
	tampered.SHA256 = strings.Repeat("0", 64)
	otherView := write("reblind/other-view.json", transcript(map[string]any{"view_sha256": diff.Disturbed[0].BeforeSHA256}))
	extraField := write("reblind/extra.json", transcript(map[string]any{"note": "x"}))
	noGuess := write("reblind/no-guess.json", transcript(map[string]any{"play": []any{map[string]any{"feedback": "rece"}}}))
	still := write("reblind/still.json", transcript(map[string]any{"id": "still"}))
	duplicate := write("reblind/duplicate.json", []byte(`{"game":"contexto","game":"contexto"}`))
	oldDiff := *diff
	oldDiff.Schema = "cat-board-view-diff-1"
	oldRef := write("old-diff.json", &oldDiff)
	dryDiff := *diff
	dryDiff.DryRun = &dryRunResult{WordID: "nou", Limit: 10}
	dryRef := write("dry-diff.json", &dryDiff)
	for name, c := range map[string]struct {
		files reblindFiles
		sha   string
		want  string
	}{
		"tampered transcript": {files(list(board("moved", tampered))), afterSHA, "SHA-256 mismatch"},
		"other view":          {files(list(board("moved", otherView))), afterSHA, "another board or view"},
		"unknown member":      {files(list(board("moved", extraField))), afterSHA, "unknown field"},
		"duplicate member":    {files(list(board("moved", duplicate))), afterSHA, "duplicate"},
		"no typed guess":      {files(list(board("moved", noGuess))), afterSHA, "typed guesses"},
		"undisturbed board":   {files(list(board("still", still))), afterSHA, "not one disturbed existing Cald board"},
		"repeated board":      {files(list(board("moved", good), board("moved", otherView))), afterSHA, "not one disturbed existing Cald board"},
		"other game":          {files(list(map[string]any{"game": "lant", "id": "moved", "transcript": good})), afterSHA, "not one disturbed existing Cald board"},
		"path leaves root":    {files(list(board("moved", fileRef{"../moved.json", good.SHA256}))), afterSHA, "below the evidence root"},
		"empty list":          {files(list()), afterSHA, "1 to 512 boards"},
		"wrong candidate":     {files(list(board("moved", good))), strings.Repeat("c", 64), "these exact bundles"},
		"schema 1 diff": {reblindFiles{filepath.Join(root, oldRef.Path), oldRef.SHA256, strings.Repeat("1", 40), strings.Repeat("2", 40), root,
			list(board("moved", good))}, afterSHA, "these exact bundles"},
		"dry-run diff": {reblindFiles{filepath.Join(root, dryRef.Path), dryRef.SHA256, strings.Repeat("1", 40), strings.Repeat("2", 40), root,
			list(board("moved", good))}, afterSHA, "these exact bundles"},
		"changed diff": {reblindFiles{filepath.Join(root, diffRef.Path), strings.Repeat("0", 64), strings.Repeat("1", 40), strings.Repeat("2", 40), root,
			list(board("moved", good))}, afterSHA, "SHA-256 mismatch"},
		"short commit": {reblindFiles{filepath.Join(root, diffRef.Path), diffRef.SHA256, "abc", strings.Repeat("2", 40), root,
			list(board("moved", good))}, afterSHA, "full commit IDs"},
	} {
		if _, err := c.files.compare(before, after, beforeSHA, c.sha); err == nil || !strings.Contains(err.Error(), c.want) {
			t.Errorf("%s: expected refusal containing %q, got %v", name, c.want, err)
		}
	}
	// A symlinked transcript cannot stand in for a regular evidence file.
	if err := os.Symlink(filepath.Join(root, "reblind", "moved.json"), filepath.Join(root, "reblind", "link.json")); err == nil {
		linked := fileRef{"reblind/link.json", good.SHA256}
		if _, err := files(list(board("moved", linked))).compare(before, after, beforeSHA, afterSHA); err == nil {
			t.Error("a symlinked transcript was accepted")
		}
	}
}

func TestPairedReblindFlagsStaySeparateFromOtherModes(t *testing.T) {
	sha := strings.Repeat("a", 64)
	for name, args := range map[string][]string{
		"compare inputs without mode": {"--baseline", "b", "--baseline-sha256", sha, "--candidate", "c", "--candidate-sha256", sha, "--view-diff", "d"},
		"compare with dry run":        {"--baseline", "b", "--baseline-sha256", sha, "--one-word-dry-run", "--reblind-compare"},
	} {
		var out bytes.Buffer
		if err := run(args, &out, &out); err == nil || !strings.Contains(err.Error(), "paired re-blind inputs") || out.Len() != 0 {
			t.Errorf("%s: expected mode refusal without output, got %v", name, err)
		}
	}
	var out bytes.Buffer
	args := []string{"--baseline", "b", "--baseline-sha256", sha, "--reblind-compare"}
	if err := run(args, &out, &out); err == nil || !strings.Contains(err.Error(), "candidate bundle path") {
		t.Errorf("paired re-blind without a candidate bundle: %v", err)
	}
}
