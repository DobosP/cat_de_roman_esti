package contentops

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
)

func repoRoot(t *testing.T) string {
	t.Helper()
	root, e := filepath.Abs("../../..")
	if e != nil {
		t.Fatal(e)
	}
	return root
}
func put(t *testing.T, path string, v any) {
	t.Helper()
	if e := os.MkdirAll(filepath.Dir(path), 0700); e != nil {
		t.Fatal(e)
	}
	var b []byte
	switch x := v.(type) {
	case []byte:
		b = x
	default:
		var e error
		b, e = render(x)
		if e != nil {
			t.Fatal(e)
		}
	}
	if e := os.WriteFile(path, b, 0600); e != nil {
		t.Fatal(e)
	}
}
func TestReviewedRankingParity(t *testing.T) {
	s, e := LoadSources(repoRoot(t))
	if e != nil {
		t.Fatal(e)
	}
	got, e := s.generateRankings()
	if e != nil {
		t.Fatal(e)
	}
	expected, _, e := read(filepath.Join(s.Root, fixtures+"board_rankings_v37.json"))
	if e != nil {
		t.Fatal(e)
	}
	if bytes.Equal(canonical(got), canonical(expected)) {
		return
	}
	actual, e := indexRows(array(got["boards"]), "native")
	if e != nil {
		t.Fatal(e)
	}
	want, e := indexRows(expected["boards"], "reference")
	if e != nil {
		t.Fatal(e)
	}
	n := 0
	for _, id := range keys(want) {
		w, a := copyObject(obj(want[id])), copyObject(obj(actual[id]))
		delete(w, "rank")
		delete(a, "rank")
		delete(w, "selection_weight")
		delete(a, "selection_weight")
		if !bytes.Equal(canonical(w), canonical(a)) {
			t.Errorf("%s expected %s got %s", id, canonical(want[id]), canonical(actual[id]))
			n++
			if n == 12 {
				break
			}
		}
	}
	t.Fatalf("ranking metadata expected %s got %s", canonical(expected["meta"]), canonical(got["meta"]))
}
func TestReviewedDerivedCatalogParity(t *testing.T) {
	s, e := LoadSources(repoRoot(t))
	if e != nil {
		t.Fatal(e)
	}
	if _, e = s.Derive(false); e != nil {
		t.Fatal(e)
	}
	if len(derivedSources) != 123 {
		t.Fatalf("source freeze count=%d", len(derivedSources))
	}
}
func TestDecodeRefusals(t *testing.T) {
	for _, blob := range []string{`{"id":1,"id":2}`, `{"a":{ "x":1,"x":2}}`, `{} {}`, `[]`, string([]byte{'{', '"', 'a', '"', ':', '"', 255, '"', '}'})} {
		if _, e := Decode([]byte(blob)); e == nil {
			t.Fatalf("accepted %q", blob)
		}
	}
	if _, e := Decode([]byte(`{"x":"ș","n":1.0}`)); e != nil {
		t.Fatal(e)
	}
}
func TestTransactionRollbackAndAbsentTargets(t *testing.T) {
	root := t.TempDir()
	a, b := filepath.Join(root, "a"), filepath.Join(root, "b")
	put(t, a, []byte("original a"))
	changes := map[string][]byte{a: []byte("new a"), b: []byte("new b")}
	err := transaction(root, changes, func() error { return errors.New("negative validator") }, nil)
	if err == nil {
		t.Fatal("red validator committed")
	}
	blob, e := os.ReadFile(a)
	if e != nil || string(blob) != "original a" {
		t.Fatal("existing bytes not restored")
	}
	if _, e = os.Stat(b); !os.IsNotExist(e) {
		t.Fatal("new transaction member left behind")
	}
	if _, e = os.Stat(filepath.Join(root, ".cat-content-ops.lock")); !os.IsNotExist(e) {
		t.Fatal("lock left behind")
	}
	err = transaction(root, changes, nil, func(i int) error {
		if i == 0 {
			return errors.New("injected second-write failure")
		}
		return nil
	})
	if err == nil {
		t.Fatal("injected write failure committed")
	}
	blob, _ = os.ReadFile(a)
	if string(blob) != "original a" {
		t.Fatal("mid-write rollback failed")
	}
}
func TestTransactionLockAndSymlinkRefusal(t *testing.T) {
	root := t.TempDir()
	a, b := filepath.Join(root, "a"), filepath.Join(root, "b")
	put(t, a, []byte("a"))
	if e := os.Symlink(a, b); e != nil {
		t.Fatal(e)
	}
	if e := Transaction(root, map[string][]byte{b: []byte("unsafe")}, nil); e == nil {
		t.Fatal("symlink mutated")
	}
	blob, _ := os.ReadFile(a)
	if string(blob) != "a" {
		t.Fatal("symlink target changed")
	}
	put(t, filepath.Join(root, ".cat-content-ops.lock"), []byte("locked"))
	if e := Transaction(root, map[string][]byte{a: []byte("race")}, nil); e == nil {
		t.Fatal("concurrent operator lock ignored")
	}
}
func syntheticSource(t *testing.T) *Sources {
	t.Helper()
	root := t.TempDir()
	for _, name := range []string{"go-backend/internal/contentops/critique.go", "go-backend/internal/contentops/surface.go", "go-backend/internal/contentops/audit.go", "go-backend/internal/graph/service.go", "go-backend/internal/alchimie/projection.go", "go-backend/internal/lant/service.go", "go-backend/internal/contentbuild/json.go", "go-backend/internal/contentbuild/rules_unicode15.json"} {
		blob, e := os.ReadFile(filepath.Join(repoRoot(t), name))
		if e != nil {
			t.Fatal(e)
		}
		put(t, filepath.Join(root, name), blob)
	}
	nodes := []any{}
	edges := []any{}
	for i := 0; i < 32; i++ {
		nodes = append(nodes, Object{"id": fmt.Sprintf("n_%02d", i), "label_ro": fmt.Sprintf("Nod %02d", i), "node_type": "concept", "category": "literatura", "salience": 0.9, "source": "synthetic", "redistributable": true, "aliases": []string{}, "tags": []string{}, "facets": Object{}})
	}
	kg := Object{"kg_nodes": nodes, "kg_edges": edges, "kg_puzzles": []any{}}
	put(t, filepath.Join(root, fixtures+"kg_sample.json"), kg)
	put(t, filepath.Join(root, "tests/fixtures/kg_sample.json"), kg)
	pack := Object{"meta": Object{"counts": Object{"conexiuni": 0, "contexto": 0, "lant": 0, "alchimie": 0}, "id_high_water": Object{"conexiuni": 900, "contexto": 900, "lant": 900, "alchimie": 900}}, "conexiuni": []any{}, "contexto": []any{}, "lant": []any{}, "alchimie": []any{}}
	for _, name := range packCopies {
		put(t, filepath.Join(root, name), pack)
	}
	put(t, filepath.Join(root, "docs/CRITIQUE_RUBRIC.md"), []byte("synthetic independent-review rubric\n"))
	empty := digest(nil)
	for _, game := range []string{"conexiuni", "lant"} {
		meta := Object{"count": 0, "initial_seed_gate_sha256": empty}
		if game == "conexiuni" {
			meta["group_count"] = 0
		} else {
			meta["initial_seed_id_set_sha256"] = empty
			meta["initial_seed_pack_sha256"] = empty
			meta["initial_seed_pack_commit"] = strings.Repeat("0", 40)
		}
		put(t, ledgerPath(root, game), Object{"schema_version": 1, "items": Object{}, "meta": meta})
	}
	s, e := LoadSources(root)
	if e != nil {
		t.Fatal(e)
	}
	return s
}
func board(start int) Object {
	groups, labels := Object{}, Object{}
	order := []string{}
	for i := 0; i < 4; i++ {
		key := fmt.Sprintf("g%d", i+1)
		ids := []string{}
		for j := 0; j < 4; j++ {
			ids = append(ids, fmt.Sprintf("n_%02d", start+4*i+j))
		}
		groups[key] = ids
		labels[key] = fmt.Sprintf("Categorie %d", i+1)
		order = append(order, ids...)
	}
	return Object{"id": "cx_literatura_901", "category": "literatura", "difficulty": "normal", "source": "ai", "status": "pending", "groups": groups, "group_labels": labels, "order": order}
}
func persistPack(t *testing.T, s *Sources, records ...Object) *Sources {
	t.Helper()
	rows := []any{}
	for _, r := range records {
		rows = append(rows, r)
	}
	s.Pack["conexiuni"] = rows
	refreshCounts(s.Pack)
	obj(s.Pack["meta"])["id_high_water"] = highWater(s.Pack)
	for _, name := range packCopies {
		put(t, filepath.Join(s.Root, name), s.Pack)
	}
	fresh, e := LoadSources(s.Root)
	if e != nil {
		t.Fatal(e)
	}
	return fresh
}
func reviewsFor(t *testing.T, s *Sources, ids []string, dir, verdict string) (string, string, string) {
	t.Helper()
	dossiers := filepath.Join(dir, "dossiers")
	if _, e := s.WriteDossiers(ids, "pending", "", dossiers, true, true); e != nil {
		t.Fatal(e)
	}
	live, e := s.Dossiers(ids, "pending", "")
	if e != nil {
		t.Fatal(e)
	}
	paths := []string{}
	for _, role := range []string{"analyst", "verifier"} {
		items := []Object{}
		for _, id := range ids {
			items = append(items, Object{"id": id, "game": "conexiuni", "verdict": verdict, "review_binding": live[id]["review_binding"], "rationale": "Synthetic mechanics review; no real content promotion.", "sources": []string{"https://example.test/synthetic"}})
		}
		path := filepath.Join(dir, role+".json")
		put(t, path, Object{"reviewer": "independent-" + role, "role": role, "input_ids": ids, "items": items})
		paths = append(paths, path)
	}
	return paths[0], paths[1], dossiers
}
func TestIndependentReviewPromotionAndLedgerDebt(t *testing.T) {
	s := persistPack(t, syntheticSource(t), board(0))
	ids := []string{"cx_literatura_901"}
	dir := t.TempDir()
	a, v, d := reviewsFor(t, s, ids, dir, "reject")
	gate := filepath.Join(dir, "gate")
	if _, e := s.BuildReview(a, v, d, "", gate, true); e != nil {
		t.Fatal(e)
	}
	if _, e := s.ApplyReview(gate, true); e != nil {
		t.Fatal(e)
	}
	fresh, e := LoadSources(s.Root)
	if e != nil {
		t.Fatal(e)
	}
	if len(array(fresh.Pack["conexiuni"])) != 0 || len(fresh.Rejections) != 1 {
		t.Fatal("reject did not remove stock and preserve debt")
	}
	candidate := board(0)
	candidate["id"] = "cx_literatura_902"
	fails := fresh.Findings(candidate, "conexiuni", map[string]bool{"cx_literatura_902": true})
	seen := map[string]bool{}
	for _, f := range fails {
		seen[str(f["check"])] = true
	}
	if !seen["duplicate_groups"] || !seen["board_reskin"] {
		t.Fatal("rejected novelty debt was forgotten")
	}
	if integer(obj(fresh.Pack["meta"])["id_high_water"].(map[string]any)["conexiuni"]) != 901 {
		t.Fatal("rejected ID high-water lost")
	}
}
func TestReviewNegativeBindingsAndIndependence(t *testing.T) {
	s := persistPack(t, syntheticSource(t), board(0))
	ids := []string{"cx_literatura_901"}
	dir := t.TempDir()
	a, v, d := reviewsFor(t, s, ids, dir, "promote")
	review, _, e := read(v)
	if e != nil {
		t.Fatal(e)
	}
	review["reviewer"] = "independent-analyst"
	put(t, v, review)
	if _, e = s.BuildReview(a, v, d, "", filepath.Join(dir, "same-reviewer"), false); e == nil {
		t.Fatal("same reviewer accepted")
	}
	review["reviewer"] = "independent-verifier"
	put(t, v, review)
	s, e = LoadSources(s.Root)
	if e != nil {
		t.Fatal(e)
	}
	gate := filepath.Join(dir, "gate")
	if _, e = s.BuildReview(a, v, d, "", gate, true); e != nil {
		t.Fatal(e)
	}
	artifact, _, e := read(filepath.Join(gate, "conexiuni_verdicts.json"))
	if e != nil {
		t.Fatal(e)
	}
	obj(artifact["coverage"])["verified"] = 0
	put(t, filepath.Join(gate, "conexiuni_verdicts.json"), artifact)
	original := append([]byte{}, s.PackBytes...)
	if _, e = s.ApplyReview(gate, true); e == nil {
		t.Fatal("unverified artifact accepted")
	}
	blob, _ := os.ReadFile(filepath.Join(s.Root, packCopies[0]))
	if !bytes.Equal(blob, original) {
		t.Fatal("negative apply changed pack")
	}
	if _, e = s.BuildReview(a, v, d, "", filepath.Join(dir, "fresh"), true); e != nil {
		t.Fatal(e)
	}
	put(t, filepath.Join(s.Root, "docs/CRITIQUE_RUBRIC.md"), []byte("changed rubric\n"))
	fresh, e := LoadSources(s.Root)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = fresh.ApplyReview(filepath.Join(dir, "fresh"), true); e == nil {
		t.Fatal("stale rubric-bound gate accepted")
	}
}
func TestSubmissionJSONLRefusalAndRollback(t *testing.T) {
	s := syntheticSource(t)
	queue := t.TempDir()
	entry := Object{"game": "conexiuni", "item": board(0), "author": "synthetic"}
	blob, e := renderQueue([]Object{entry})
	if e != nil {
		t.Fatal(e)
	}
	put(t, filepath.Join(queue, "submissions.jsonl"), blob)
	if _, e = s.Submissions("reject", queue, []string{"missing"}, "", true); e == nil {
		t.Fatal("unknown submission rejected")
	}
	if _, e = s.Submissions("promote", queue, []string{"cx_literatura_901"}, "", true); e == nil {
		t.Fatal("unreviewed submission approved")
	}
	if _, e = s.Submissions("stage", queue, []string{"cx_literatura_901"}, "", true); e != nil {
		t.Fatal(e)
	}
	remaining, _, e := readQueue(filepath.Join(queue, "submissions.jsonl"))
	if e != nil || len(remaining) != 1 {
		t.Fatal("stage must retain queued review provenance")
	}
	fresh, e := LoadSources(s.Root)
	if e != nil {
		t.Fatal(e)
	}
	if str(obj(array(fresh.Pack["conexiuni"])[0])["status"]) != "pending" {
		t.Fatal("submission served before approval")
	}
	before, _ := os.ReadFile(filepath.Join(queue, "submissions.jsonl"))
	if _, e = fresh.Submissions("reject", queue, []string{"cx_literatura_901"}, "", true); e == nil {
		t.Fatal("queue-only rejection of staged stock accepted")
	}
	after, _ := os.ReadFile(filepath.Join(queue, "submissions.jsonl"))
	if !bytes.Equal(before, after) {
		t.Fatal("refused staged rejection mutated queue")
	}
	unstaged := syntheticSource(t)
	other := t.TempDir()
	put(t, filepath.Join(other, "submissions.jsonl"), blob)
	if _, e = unstaged.Submissions("reject", other, []string{"cx_literatura_901"}, "", true); e != nil {
		t.Fatal(e)
	}
	rejected, _, e := readQueue(filepath.Join(other, "submissions-rejected.jsonl"))
	if e != nil || len(rejected) != 1 {
		t.Fatal("rejection audit lost")
	}

}

func candidateFiles(t *testing.T, s *Sources, dir string) (string, Object, Object, Object) {
	t.Helper()
	category := filepath.Join(dir, "literatura")
	r := board(0)
	groups := []Object{}
	for _, key := range keys(obj(r["groups"])) {
		groups = append(groups, Object{"tiles": obj(r["groups"])[key], "label": obj(r["group_labels"])[key]})
	}
	candidate := Object{"nodes": []any{}, "edges": []any{}, "conexiuni": []Object{{"difficulty": "normal", "groups": groups}}, "contexto": []any{}, "lant": []any{}, "alchimie": []any{}}
	put(t, filepath.Join(category, "candidates.json"), candidate)
	raw, e := os.ReadFile(filepath.Join(category, "candidates.json"))
	if e != nil {
		t.Fatal(e)
	}
	binding := "sha256:" + digest(raw)
	f := Object{"category": "literatura", "candidate_sha256": binding, "reviewer": "synthetic-factual", "coverage_note": "all raw references covered", "reviewed_refs": []string{"conexiuni[0]"}, "issues": []any{}}
	q := Object{"category": "literatura", "candidate_sha256": binding, "reviewer": "synthetic-quality", "coverage_note": "all raw references covered", "instances": []Object{{"ref": "conexiuni[0]", "verdict": "keep", "note": "synthetic mechanics only"}}}
	put(t, filepath.Join(category, "verify_factual.json"), f)
	put(t, filepath.Join(category, "verify_quality.json"), q)
	return category, candidate, f, q
}
func TestCandidateIndependentCoverageAndPendingStage(t *testing.T) {
	for _, mutate := range []string{"stale", "partial", "same-reviewer", "unresolved", "unknown-payload"} {
		t.Run(mutate, func(t *testing.T) {
			s := syntheticSource(t)
			dir := t.TempDir()
			category, c, f, q := candidateFiles(t, s, dir)
			switch mutate {
			case "stale":
				f["candidate_sha256"] = "sha256:" + strings.Repeat("0", 64)
			case "partial":
				f["reviewed_refs"] = []string{}
			case "same-reviewer":
				q["reviewer"] = f["reviewer"]
			case "unresolved":
				f["issues"] = []Object{{"ref": "conexiuni[0]", "severity": "fix", "issue": "not resolved"}}
			case "unknown-payload":
				groups := array(obj(array(c["conexiuni"])[0])["groups"])
				obj(groups[0])["tiles"] = []string{"absent", "n_01", "n_02", "n_03"}
				put(t, filepath.Join(category, "candidates.json"), c)
				raw, _ := os.ReadFile(filepath.Join(category, "candidates.json"))
				f["candidate_sha256"] = "sha256:" + digest(raw)
				q["candidate_sha256"] = f["candidate_sha256"]
			}
			put(t, filepath.Join(category, "verify_factual.json"), f)
			put(t, filepath.Join(category, "verify_quality.json"), q)
			before := append([]byte{}, s.PackBytes...)
			if _, e := s.Import(dir, true); e == nil {
				t.Fatal("invalid raw candidate batch imported")
			}
			after, _ := os.ReadFile(filepath.Join(s.Root, packCopies[0]))
			if !bytes.Equal(before, after) {
				t.Fatal("rejected preflight changed stock")
			}
		})
	}
	s := syntheticSource(t)
	dir := t.TempDir()
	candidateFiles(t, s, dir)
	if _, e := s.Import(dir, false); e != nil {
		t.Fatal(e)
	}
	before := append([]byte{}, s.PackBytes...)
	actual, _ := os.ReadFile(filepath.Join(s.Root, packCopies[0]))
	if !bytes.Equal(before, actual) {
		t.Fatal("read-only import changed source")
	}
	s, e := LoadSources(s.Root)
	if e != nil {
		t.Fatal(e)
	}
	receipt, e := s.Import(dir, true)
	if e != nil {
		t.Fatal(e)
	}
	if len(array(receipt["allocated"])) != 1 {
		t.Fatal("allocation receipt missing")
	}
	s, e = LoadSources(s.Root)
	if e != nil {
		t.Fatal(e)
	}
	r := obj(array(s.Pack["conexiuni"])[0])
	if str(r["id"]) != "cx_literatura_901" || str(r["status"]) != "pending" {
		t.Fatal("kept quality bypassed pending or reused ID")
	}
}
func TestSourceReadSetGuardAfterPreflight(t *testing.T) {
	root := t.TempDir()
	source, target := filepath.Join(root, "source"), filepath.Join(root, "target")
	put(t, source, []byte("reviewed-source"))
	put(t, target, []byte("original-target"))
	snap, e := takeSnapshot(source)
	if e != nil {
		t.Fatal(e)
	}
	put(t, source, []byte("concurrent valid update"))
	e = guardedTransaction(root, map[string][]byte{target: []byte("stale-plan")}, nil, nil, map[string]snapshot{source: snap})
	if e == nil {
		t.Fatal("stale preflight plan overwrote concurrent update")
	}
	blob, _ := os.ReadFile(target)
	if string(blob) != "original-target" {
		t.Fatal("source guard ran after mutation")
	}
}
func TestRejectedIDsStayReserved(t *testing.T) {
	s := persistPack(t, syntheticSource(t), board(0))
	dir := t.TempDir()
	a, v, d := reviewsFor(t, s, []string{"cx_literatura_901"}, dir, "reject")
	gate := filepath.Join(dir, "gate")
	if _, e := s.BuildReview(a, v, d, "", gate, true); e != nil {
		t.Fatal(e)
	}
	if _, e := s.ApplyReview(gate, true); e != nil {
		t.Fatal(e)
	}
	fresh, e := LoadSources(s.Root)
	if e != nil {
		t.Fatal(e)
	}
	water := obj(obj(fresh.Pack["meta"])["id_high_water"])
	water["conexiuni"] = 1
	for _, name := range packCopies {
		put(t, filepath.Join(s.Root, name), fresh.Pack)
	}
	fresh, e = LoadSources(s.Root)
	if e != nil {
		t.Fatal(e)
	}
	if integer(obj(obj(fresh.Pack["meta"])["id_high_water"])["conexiuni"]) < 901 {
		t.Fatal("historical suffix reservation lost")
	}
	queue := t.TempDir()
	blob, _ := renderQueue([]Object{{"game": "conexiuni", "item": board(0)}})
	put(t, filepath.Join(queue, "submissions.jsonl"), blob)
	if _, e = fresh.Submissions("stage", queue, []string{"cx_literatura_901"}, "", true); e == nil {
		t.Fatal("retired ID staged again")
	}
}
func alchimieSynthetic(t *testing.T) *Sources {
	t.Helper()
	s := syntheticSource(t)
	edges := []any{}
	for i, pair := range [][2]string{{"n_00", "n_05"}, {"n_01", "n_05"}, {"n_02", "n_06"}, {"n_03", "n_06"}, {"n_05", "n_07"}, {"n_06", "n_07"}} {
		edges = append(edges, Object{"id": fmt.Sprintf("e_%d", i), "src_id": pair[0], "dst_id": pair[1], "relation": "related_to", "label_ro": "legătură sintetică", "strength": .9, "bidirectional": false, "is_distractor": false, "source": "synthetic", "redistributable": true, "tags": []string{}, "facets": Object{}})
	}
	s.KG["kg_edges"] = edges
	put(t, filepath.Join(s.Root, fixtures+"kg_sample.json"), s.KG)
	put(t, filepath.Join(s.Root, "tests/fixtures/kg_sample.json"), s.KG)
	s.Pack["alchimie"] = []Object{{"id": "al_literatura_901", "category": "literatura", "difficulty": "normal", "source": "ai", "status": "pending", "seeds": []string{"n_00", "n_01", "n_02", "n_03", "n_04"}, "target": "n_07", "target_depth": 3}}
	refreshCounts(s.Pack)
	obj(s.Pack["meta"])["id_high_water"] = highWater(s.Pack)
	for _, name := range packCopies {
		put(t, filepath.Join(s.Root, name), s.Pack)
	}
	fresh, e := LoadSources(s.Root)
	if e != nil {
		t.Fatal(e)
	}
	return fresh
}
func TestProjectionAuditBindsLiveSparseRecipesAndRuntime(t *testing.T) {
	s := alchimieSynthetic(t)
	ids := []string{"al_literatura_901"}
	dir := t.TempDir()
	if _, e := s.WriteDossiers(ids, "pending", "alchimie", dir, true, true); e != nil {
		t.Fatal(e)
	}
	audit, e := s.AuditProjections(ids, dir, "", false)
	if e != nil {
		t.Fatal(e)
	}
	item := obj(array(audit["items"])[0])
	if integer(item["exact_action_par"]) != 3 || integer(item["projected_opening_pair_count"]) < 2 {
		t.Fatal("live projection mechanics missing")
	}
	dossiers, e := s.Dossiers(ids, "pending", "alchimie")
	if e != nil {
		t.Fatal(e)
	}
	blob, _ := render(audit)
	if e = s.validateProjection(blob, ids, dossiers); e != nil {
		t.Fatal(e)
	}
	item["projection_par"] = 2
	bad, _ := render(audit)
	if e = s.validateProjection(bad, ids, dossiers); e == nil {
		t.Fatal("tampered projection accepted")
	}
	put(t, filepath.Join(s.Root, "go-backend/internal/alchimie/projection.go"), []byte("changed native runtime\n"))
	fresh, e := LoadSources(s.Root)
	if e != nil {
		t.Fatal(e)
	}
	current, e := fresh.Dossiers(ids, "pending", "alchimie")
	if e != nil {
		t.Fatal(e)
	}
	if e = fresh.validateProjection(blob, ids, current); e == nil {
		t.Fatal("stale runtime projection evidence accepted")
	}
}
func TestApprovedDossierCensus(t *testing.T) {
	s, e := LoadSources(repoRoot(t))
	if e != nil {
		t.Fatal(e)
	}
	rows, _, e := indexPack(s.Pack)
	if e != nil {
		t.Fatal(e)
	}
	ids := []string{}
	all := []string{}
	for id := range rows {
		all = append(all, id)
	}
	sort.Strings(all)
	for _, id := range all {
		if str(rows[id]["status"]) == "approved" {
			ids = append(ids, id)
		}
	}
	dossiers, e := s.Dossiers(ids, "approved", "")
	if e != nil {
		t.Fatal(e)
	}
	if len(dossiers) != 709 {
		t.Fatalf("approved census count %d", len(dossiers))
	}
	for id, d := range dossiers {
		if str(d["review_source_version"]) != "native-contentops-v1" || !validBinding(str(d["review_binding"])) || str(d["review_binding"]) != binding(d) {
			t.Fatalf("unbound source-version dossier %s", id)
		}
	}
}

func TestCanonicalLiteralEscapesAndFiniteNumberRefusal(t *testing.T) {
	v := Object{"separator": "\u2028", "literal": `\u2028`, "html": "<>&", "literal_html": `\u003c`}
	blob := canonical(v)
	got, e := Decode(blob)
	if e != nil {
		t.Fatal(e)
	}
	for k, x := range v {
		if str(got[k]) != str(x) {
			t.Fatalf("canonical corrupted literal %s", k)
		}
	}
	if _, e = Decode([]byte(`{"n":1e9999}`)); e == nil {
		t.Fatal("overflow numeric binding accepted")
	}
}

func TestUnsafeDossierIDsAndQueueRejectAuditRefusal(t *testing.T) {
	for _, id := range []string{"../outside", "a/b", `a\b`, ".", "..", " leading"} {
		if safeID(id) {
			t.Fatalf("unsafe identifier accepted %q", id)
		}
	}
	s := syntheticSource(t)
	queue := t.TempDir()
	entry := Object{"game": "conexiuni", "item": board(0)}
	blob, _ := renderQueue([]Object{entry})
	put(t, filepath.Join(queue, "submissions.jsonl"), blob)
	put(t, filepath.Join(queue, "submissions-rejected.jsonl"), blob)
	if _, e := s.Submissions("stage", queue, []string{"cx_literatura_901"}, "", true); e == nil {
		t.Fatal("previously rejected queue identifier reused")
	}
}

func TestUnanimousPromotionAndProspectiveRejectDebt(t *testing.T) {
	t.Run("unanimous synthetic promotion", func(t *testing.T) {
		s := persistPack(t, syntheticSource(t), board(0))
		ids := []string{"cx_literatura_901"}
		dir := t.TempDir()
		a, v, d := reviewsFor(t, s, ids, dir, "promote")
		gate := filepath.Join(dir, "gate")
		if _, e := s.BuildReview(a, v, d, "", gate, true); e != nil {
			t.Fatal(e)
		}
		if _, e := s.ApplyReview(gate, true); e != nil {
			t.Fatal(e)
		}
		fresh, e := LoadSources(s.Root)
		if e != nil {
			t.Fatal(e)
		}
		if str(obj(array(fresh.Pack["conexiuni"])[0])["status"]) != "approved" {
			t.Fatal("unanimous synthetic gate did not approve")
		}
	})
	t.Run("same-batch rejects retained as novelty debt", func(t *testing.T) {
		other := board(0)
		other["id"] = "cx_literatura_902"
		s := persistPack(t, syntheticSource(t), board(0), other)
		ids := []string{"cx_literatura_901", "cx_literatura_902"}
		dir := t.TempDir()
		dossier := filepath.Join(dir, "dossiers")
		if _, e := s.WriteDossiers(ids, "pending", "", dossier, false, true); e != nil {
			t.Fatal(e)
		}
		live, e := s.Dossiers(ids, "pending", "")
		if e != nil {
			t.Fatal(e)
		}
		paths := []string{}
		for _, role := range []string{"analyst", "verifier"} {
			items := []Object{}
			for i, id := range ids {
				verdict := "promote"
				if i == 0 {
					verdict = "reject"
				}
				items = append(items, Object{"id": id, "game": "conexiuni", "verdict": verdict, "review_binding": live[id]["review_binding"], "rationale": "synthetic novelty-debt fixture", "sources": []string{"https://example.test/fixture"}})
			}
			path := filepath.Join(dir, role+".json")
			put(t, path, Object{"reviewer": "independent-" + role, "role": role, "input_ids": ids, "items": items})
			paths = append(paths, path)
		}
		gate := filepath.Join(dir, "gate")
		if _, e = s.BuildReview(paths[0], paths[1], dossier, "", gate, true); e != nil {
			t.Fatal(e)
		}
		before := append([]byte{}, s.PackBytes...)
		if _, e = s.ApplyReview(gate, true); e == nil {
			t.Fatal("same-batch rejection disappeared before promotion critique")
		}
		after, _ := os.ReadFile(filepath.Join(s.Root, packCopies[0]))
		if !bytes.Equal(before, after) {
			t.Fatal("failed prospective gate mutated stock")
		}
	})
}
func TestDeltaStableIdentitySchema(t *testing.T) {
	report, e := Delta(repoRoot(t), "HEAD")
	if e != nil {
		t.Fatal(e)
	}
	if integer(report["schema_version"]) != 1 || str(report["comparison"]) != "working_tree" || obj(report["synonyms"])["count"] != nil {
		t.Fatal("delta schema or synonym claim drift")
	}
	for _, key := range []string{"concepts", "forms", "connections", "puzzles"} {
		r := obj(report[key])
		if integer(r["added_count"]) != 0 || integer(r["removed_count"]) != 0 || integer(r["changed_count"]) != 0 {
			t.Fatalf("tooling-only branch changed real content %s", key)
		}
	}
	if !strings.Contains(DeltaText(report), "Alias data") {
		if !strings.Contains(DeltaText(report), "not necessarily new concepts or synonyms") {
			t.Fatal("text report omitted alias semantics")
		}
	}
	if _, e = Delta(repoRoot(t), "--all"); e == nil {
		t.Fatal("Git option injection accepted")
	}
}
func TestLedgerTamperingFailsClosed(t *testing.T) {
	s := syntheticSource(t)
	ledger, _, e := read(ledgerPath(s.Root, "lant"))
	if e != nil {
		t.Fatal(e)
	}
	obj(ledger["meta"])["initial_seed_pack_commit"] = strings.Repeat("g", 40)
	put(t, ledgerPath(s.Root, "lant"), ledger)
	if _, e = LoadSources(s.Root); e == nil {
		t.Fatal("nonhex initial seed commit accepted")
	}
}

func TestReviewCitationPortBounds(t *testing.T) {
	s := persistPack(t, syntheticSource(t), board(0))
	dir := t.TempDir()
	_, v, _ := reviewsFor(t, s, []string{"cx_literatura_901"}, dir, "keep")
	review, _, e := read(v)
	if e != nil {
		t.Fatal(e)
	}
	for _, source := range []string{"https://example.test:65536/factual", "https://example.test:0/factual", "https://user:password@example.test/factual"} {
		obj(array(review["items"])[0])["sources"] = []string{source}
		put(t, v, review)
		if _, _, e = readReview(v, "verifier"); e == nil {
			t.Fatalf("invalid citation accepted %s", source)
		}
	}
}
func TestSharedGuardedReadSetContract(t *testing.T) {
	root := t.TempDir()
	source, target := filepath.Join(root, "source"), filepath.Join(root, "target")
	put(t, source, []byte("frozen source"))
	put(t, target, []byte("old"))
	expected, e := CaptureReadSet([]string{source, target})
	if e != nil {
		t.Fatal(e)
	}
	if e = GuardedTransaction(root, map[string][]byte{target: []byte("reviewed change")}, expected, nil); e != nil {
		t.Fatal(e)
	}
	blob, _ := os.ReadFile(target)
	if string(blob) != "reviewed change" {
		t.Fatal("shared guarded installer failed")
	}
	if e = GuardedTransaction(root, map[string][]byte{target: []byte("stale")}, expected, nil); e == nil {
		t.Fatal("shared source/target baseline CAS accepted stale update")
	}
	if e = GuardedTransaction(root, nil, ReadSet{}, nil); e == nil {
		t.Fatal("missing immutable readset accepted")
	}
}

func TestMalformedPackMetadataRefusesBeforeReconciliation(t *testing.T) {
	for _, kind := range []string{"missing-meta", "null-meta", "array-meta", "missing-water", "null-water", "negative-contexto", "fractional-alchimie", "below-observed"} {
		t.Run(kind, func(t *testing.T) {
			s := syntheticSource(t)
			switch kind {
			case "missing-meta":
				delete(s.Pack, "meta")
			case "null-meta":
				s.Pack["meta"] = nil
			case "array-meta":
				s.Pack["meta"] = []any{}
			case "missing-water":
				delete(obj(s.Pack["meta"]), "id_high_water")
			case "null-water":
				obj(s.Pack["meta"])["id_high_water"] = nil
			case "negative-contexto":
				obj(obj(s.Pack["meta"])["id_high_water"])["contexto"] = -1
			case "fractional-alchimie":
				obj(obj(s.Pack["meta"])["id_high_water"])["alchimie"] = 1.5
			case "below-observed":
				s.Pack["conexiuni"] = []Object{board(0)}
				refreshCounts(s.Pack)
				obj(obj(s.Pack["meta"])["id_high_water"])["conexiuni"] = 900
			}
			for _, name := range packCopies {
				put(t, filepath.Join(s.Root, name), s.Pack)
			}
			if _, e := LoadSources(s.Root); e == nil {
				t.Fatal("malformed source metadata accepted")
			}
		})
	}
}

func TestPrivateReviewUnicodeCannotBeSilentlyRepaired(t *testing.T) {
	for _, raw := range []string{`{"reviewer":"\ud800"}`, `{"review_binding":"\udfff"}`, `{"meta":{"id_high_water":{"lant":"\ud800\u0041"}}}`} {
		if _, err := Decode([]byte(raw)); err == nil {
			t.Fatal("private review Unicode was repaired")
		}
	}
	if _, err := Decode([]byte(`{"reviewer":"literal \\ud800","label":"\ud83d\ude00"}`)); err != nil {
		t.Fatal(err)
	}
}

func TestNewRuntimeFileRefusesBeforeWriteAndRollsBack(t *testing.T) {
	s := syntheticSource(t)
	target := filepath.Join(s.Root, packCopies[0])
	before, err := os.ReadFile(target)
	if err != nil {
		t.Fatal(err)
	}
	newcomer := filepath.Join(s.Root, "go-backend/internal/graph/arrived.go")
	put(t, newcomer, []byte("package graph\n"))
	if err = s.commit(map[string][]byte{target: []byte("changed")}, nil); err == nil {
		t.Fatal("new runtime source ignored under lock")
	}
	after, _ := os.ReadFile(target)
	if !bytes.Equal(before, after) {
		t.Fatal("write occurred despite new runtime input")
	}
	if err = os.Remove(newcomer); err != nil {
		t.Fatal(err)
	}
	err = guardedTransactionWithInventory(s.Root, map[string][]byte{target: []byte("changed")}, nil, func(int) error { put(t, newcomer, []byte("package graph\n")); return nil }, s.Inputs, s.checkInventory)
	if err == nil {
		t.Fatal("postwrite runtime arrival accepted")
	}
	after, _ = os.ReadFile(target)
	if !bytes.Equal(before, after) {
		t.Fatal("new runtime source did not trigger rollback")
	}
}
