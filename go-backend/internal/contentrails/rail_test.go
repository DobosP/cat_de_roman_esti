package contentrails

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func rootPath(t *testing.T) string {
	t.Helper()
	root, err := filepath.Abs("../../..")
	if err != nil {
		t.Fatal(err)
	}
	return root
}
func sourceForTest(t *testing.T) *Source {
	t.Helper()
	s, err := LoadSource("")
	if err != nil {
		t.Fatal(err)
	}
	return s
}
func writeJSONTest(t *testing.T, path string, v any) {
	t.Helper()
	b, err := Render(v)
	if err != nil {
		t.Fatal(err)
	}
	if err = os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(path, b, 0600); err != nil {
		t.Fatal(err)
	}
}
func TestAllFourBaselineArtifactsRebuiltFromAuthoredInputsExactBytes(t *testing.T) {
	results, err := CheckAll(rootPath(t), sourceForTest(t))
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 4 {
		t.Fatal("incomplete builder coverage")
	}
	for _, r := range results {
		if !r.OK || !r.ExactBytes || !r.SemanticExact || r.RebuiltSHA256 != r.ArtifactSHA256 {
			t.Fatal(r)
		}
	}
}
func TestNativeAuditsNaturalSelectionGoalsRecipesAndEveryHistoricalPrefix(t *testing.T) {
	root := rootPath(t)
	quick, err := fixture(root, "quick_games_v92.json")
	if err != nil {
		t.Fatal(err)
	}
	q, err := auditQuick(context.Background(), root, quick)
	if err != nil {
		t.Fatal(err)
	}
	if len(rows(q["replays"])) != 85 || q["core_boards_preserved"] != true {
		t.Fatal("quick audit coverage")
	}
	worldRoot, _ := historicalWorldRoot(t)
	world, err := fixture(worldRoot, "alchimie_discovery_world_v92.json")
	if err != nil {
		t.Fatal(err)
	}
	w, err := auditWorld(worldRoot, world)
	if err != nil {
		t.Fatal(err)
	}
	if len(rows(w["goal_replays"])) != 33 || len(rows(w["compatible_save_replays"])) != 9 || integer(w["historical_prefixes"]) != 1009 {
		t.Fatal("world audit coverage")
	}
	ext, err := fixture(root, "alchimie_recipe_extensions_v92.json")
	if err != nil {
		t.Fatal(err)
	}
	e, err := auditExtensions(root, ext)
	if err != nil {
		t.Fatal(err)
	}
	if integer(e["boards_replayed"]) != 27 || integer(e["additions_replayed"]) != 49 {
		t.Fatal("extension audit coverage")
	}
}
func TestStrictPrivateSourceAndReviewJSON(t *testing.T) {
	dir := t.TempDir()
	for i, raw := range []string{`{"schema":"x","schema":"y"}`, `{"x":"\ud800"}`, `{"x":"\udc00"}`, `{"x":1e999}`, `{} {}`, `{"x":` + strings.Repeat("[", 65) + "0" + strings.Repeat("]", 65) + "}", string([]byte{'{', '"', 'x', '"', ':', '"', 255, '"', '}'})} {
		path := filepath.Join(dir, fmt.Sprintf("bad-%d.json", i))
		if err := os.WriteFile(path, []byte(raw), 0600); err != nil {
			t.Fatal(err)
		}
		if _, err := Read(path); err == nil {
			t.Fatal("malformed private JSON accepted", i)
		}
	}
	path := filepath.Join(dir, "valid.json")
	if err := os.WriteFile(path, []byte(`{"x":"\\ud800","y":"\ud83d\ude42"}`), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := Read(path); err != nil {
		t.Fatal(err)
	}
}
func sourceV2(t *testing.T, dir string) *Source {
	t.Helper()
	s := sourceForTest(t)
	raw := clone(s.Raw).(map[string]any)
	raw["version"] = 2
	raw["parent_source_sha256"] = AuthoredSHA256
	first := object(rows(object(raw["quick"])["boards"])[0])
	first["rationale"] = text(first["rationale"]) + " Synthetic fixture-only reviewed annotation."
	path := filepath.Join(dir, "source-v2.json")
	writeJSONTest(t, path, raw)
	next, err := LoadSource(path)
	if err != nil {
		t.Fatal(err)
	}
	return next
}
func TestSourceShapeAndVersionParentRefuseBeforeConstruction(t *testing.T) {
	s := sourceForTest(t)
	dir := t.TempDir()
	mutations := []func(map[string]any){func(m map[string]any) { m["version"] = 1 }, func(m map[string]any) { m["version"] = json.Number("2.1") }, func(m map[string]any) { m["parent_source_sha256"] = strings.Repeat("0", 64) }, func(m map[string]any) { object(m["world"])["world"] = nil }, func(m map[string]any) { object(m["world"])["starters"] = nil }, func(m map[string]any) { object(m["world"])["recipes"] = nil }, func(m map[string]any) { object(m["world"])["unlocks"] = nil }, func(m map[string]any) { object(m["world"])["goals"] = nil }, func(m map[string]any) { object(m["quick"])["boards"] = nil }, func(m map[string]any) { object(m["extensions"])["boards"] = nil }, func(m map[string]any) { object(m["extensions"])["candidates"] = nil }, func(m map[string]any) { object(m["archives"])["world_previous"] = nil }}
	for i, mutate := range mutations {
		raw := clone(s.Raw).(map[string]any)
		raw["version"] = 2
		raw["parent_source_sha256"] = AuthoredSHA256
		mutate(raw)
		path := filepath.Join(dir, fmt.Sprintf("source-%d.json", i))
		writeJSONTest(t, path, raw)
		if _, err := LoadSource(path); err == nil {
			t.Fatal("malformed source accepted", i)
		}
	}
	next := sourceV2(t, dir)
	if next.Version != 2 || next.SHA256 == AuthoredSHA256 {
		t.Fatal("valid version transition absent")
	}
}
func syntheticReviews(t *testing.T, dir, rail string, candidate map[string]any, candidateSHA string) []string {
	t.Helper()
	field := "boards"
	if rail == "world" {
		field = "recipes"
	}
	if rail == "extensions" {
		field = "candidates"
	}
	paths := []string{}
	for _, role := range []string{"factual", "quality"} {
		items := []any{}
		for _, v := range rows(candidate[field]) {
			items = append(items, map[string]any{"id": object(v)["id"], "verdict": "accept", "rationale": "Synthetic fixture-only operator contract judgment.", "sources": []any{"https://example.invalid/fixture"}})
		}
		review := map[string]any{"kind": reviewKind(rail), "role": role, "reviewer": "synthetic-" + role, "candidate_sha256": candidateSHA, "items": items}
		path := filepath.Join(dir, role+".json")
		writeJSONTest(t, path, review)
		paths = append(paths, path)
	}
	return paths
}
func TestCompleteIndependentJudgmentsSourcesAndCandidateBinding(t *testing.T) {
	root := rootPath(t)
	dir := t.TempDir()
	s := sourceV2(t, dir)
	candidate, err := Candidate(root, s, "quick", false)
	if err != nil {
		t.Fatal(err)
	}
	raw, _ := Render(candidate)
	sha := digestBytes(raw)
	paths := syntheticReviews(t, dir, "quick", candidate, sha)
	if _, err = readReviews(root, "quick", sha, candidate, paths); err != nil {
		t.Fatal(err)
	}
	quality, err := Read(paths[1])
	if err != nil {
		t.Fatal(err)
	}
	mutations := []func(map[string]any){func(m map[string]any) { m["reviewer"] = "synthetic-factual" }, func(m map[string]any) { m["candidate_sha256"] = strings.Repeat("0", 64) }, func(m map[string]any) { m["items"] = rows(m["items"])[1:] }, func(m map[string]any) { object(rows(m["items"])[0])["sources"] = map[string]any{} }, func(m map[string]any) { object(rows(m["items"])[0])["sources"] = nil }, func(m map[string]any) { object(rows(m["items"])[0])["unknown"] = true }, func(m map[string]any) {
		object(rows(m["items"])[0])["sources"] = []any{"https://example.invalid:65536/x"}
	}}
	for i, mutate := range mutations {
		bad := clone(quality).(map[string]any)
		mutate(bad)
		path := filepath.Join(dir, fmt.Sprintf("quality-bad-%d.json", i))
		writeJSONTest(t, path, bad)
		if _, err = readReviews(root, "quick", sha, candidate, []string{paths[0], path}); err == nil {
			t.Fatal("invalid semantic judgment accepted", i)
		}
	}
}
func TestHistoricalWorldTransitionsKeepCurrentBooksAndRefuseChangedRecipes(t *testing.T) {
	root, _ := historicalWorldRoot(t)
	s := sourceForTest(t)
	next, err := Candidate(root, s, "world", false)
	if err != nil {
		t.Fatal(err)
	}
	if len(rows(next["compatible_versions"])) != 9 {
		t.Fatal("current historical books dropped")
	}
	old, err := archive(root, s, "world_candidate")
	if err != nil {
		t.Fatal(err)
	}
	changed := clone(next).(map[string]any)
	object(rows(changed["recipes"])[0])["result"] = "synthetic-changed"
	if _, err := compatibleVersions(old, changed, strings.Repeat("a", 64)); err == nil {
		t.Fatal("historical recipe overwrite accepted")
	}
	changed = clone(next).(map[string]any)
	changed["unlocks"] = rows(changed["unlocks"])[1:]
	if _, err := compatibleVersions(old, changed, strings.Repeat("a", 64)); err == nil {
		t.Fatal("historical supply removal accepted")
	}
}
func cloneRoot(t *testing.T) (string, *Source) {
	t.Helper()
	root := rootPath(t)
	s := sourceForTest(t)
	paths, err := inputReadPaths(root, s)
	if err != nil {
		t.Fatal(err)
	}
	target := t.TempDir()
	for _, path := range paths {
		relative, err := filepath.Rel(root, path)
		if err != nil || strings.HasPrefix(relative, "..") {
			t.Fatal("copy escaped source root")
		}
		blob, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		dest := filepath.Join(target, relative)
		if err = os.MkdirAll(filepath.Dir(dest), 0700); err != nil {
			t.Fatal(err)
		}
		if err = os.WriteFile(dest, blob, 0644); err != nil {
			t.Fatal(err)
		}
	}
	return target, s
}
func TestSyntheticVersionTwoInstallBoundReviewsAuditAndServingPinRefusal(t *testing.T) {
	root, _ := cloneRoot(t)
	dir := t.TempDir()
	s := sourceV2(t, dir)
	candidate, err := Candidate(root, s, "quick", false)
	if err != nil {
		t.Fatal(err)
	}
	candidatePath := filepath.Join(dir, "candidate.json")
	writeJSONTest(t, candidatePath, candidate)
	blob, _ := Render(candidate)
	paths := syntheticReviews(t, dir, "quick", candidate, digestBytes(blob))
	proposal, err := BuildProposal(root, s, "quick", candidatePath, paths[0], paths[1])
	if err != nil {
		t.Fatal(err)
	}
	proposalPath := filepath.Join(dir, "proposal.json")
	writeJSONTest(t, proposalPath, proposal)
	audit, err := Audit(context.Background(), root, "quick", proposal)
	if err != nil {
		t.Fatal(err)
	}
	auditPath := filepath.Join(dir, "audit.json")
	writeJSONTest(t, auditPath, audit)
	proposalBytes, _ := Render(proposal)
	auditBytes, _ := Render(audit)
	pin := digestBytes(proposalBytes)
	finalPaths := []string{}
	for _, role := range []string{"factual", "quality"} {
		path := filepath.Join(dir, "final-"+role+".json")
		writeJSONTest(t, path, map[string]any{"kind": FinalKind("quick"), "role": role, "reviewer": "synthetic-" + role, "catalog_sha256": pin, "audit_sha256": digestBytes(auditBytes), "verdict": "accept", "rationale": "Synthetic fixture-only final judgment."})
		finalPaths = append(finalPaths, path)
	}
	if err = ConfirmFinal(root, "quick", proposal, proposalPath, auditPath, finalPaths[0], finalPaths[1], pin); err != nil {
		t.Fatal(err)
	}
	for i, mutate := range []func(map[string]any){func(m map[string]any) { m["kind"] = "world-audit" }, func(m map[string]any) { m["verdict"] = "reject"; m["passed"] = true }, func(m map[string]any) { m["runtime_sources"] = nil }, func(m map[string]any) { m["source_bindings"] = map[string]any{} }} {
		bad := clone(audit).(map[string]any)
		mutate(bad)
		path := filepath.Join(dir, fmt.Sprintf("audit-bad-%d.json", i))
		writeJSONTest(t, path, bad)
		if err = ConfirmFinal(root, "quick", proposal, proposalPath, path, finalPaths[0], finalPaths[1], pin); err == nil {
			t.Fatal("invalid final audit accepted", i)
		}
	}
	target, _ := ArtifactPath(root, "quick")
	old, err := os.ReadFile(target)
	if err != nil {
		t.Fatal(err)
	}
	if bytes.Equal(old, proposalBytes) {
		t.Fatal("transition must actually change artifact")
	}
	if err = InstallProposal(root, s, "quick", candidatePath, paths[0], paths[1], proposalPath, auditPath, finalPaths[0], finalPaths[1], pin, filepath.Join(dir, "source-v2.json")); err != nil {
		t.Fatal(err)
	}
	newBytes, err := os.ReadFile(target)
	if err != nil || !bytes.Equal(newBytes, proposalBytes) {
		t.Fatal("signed fixture transition absent")
	}
	if err = contentbuild.ValidateSources(root); err == nil {
		t.Fatal("staged catalog activated export without explicit reviewed pin/code transition")
	}
	if _, err = os.Stat(filepath.Join(root, "tests/fixtures/quick_games_v92.json")); !os.IsNotExist(err) {
		t.Fatal("undeclared mirror created")
	}
	if _, err = os.Stat(filepath.Join(root, ".cat-content-ops.lock")); !os.IsNotExist(err) {
		t.Fatal("operator lock retained")
	}
}
func TestSharedGuardedTransactionsRollbackAndRefuseStaleReadsets(t *testing.T) {
	root := t.TempDir()
	a, b, input := filepath.Join(root, "a.json"), filepath.Join(root, "b.json"), filepath.Join(root, "source.json")
	for path, blob := range map[string]string{a: "original-a", b: "original-b", input: "original-source"} {
		if err := os.WriteFile(path, []byte(blob), 0640); err != nil {
			t.Fatal(err)
		}
	}
	readset, err := contentops.CaptureReadSet([]string{a, b, input})
	if err != nil {
		t.Fatal(err)
	}
	changes := map[string][]byte{a: []byte("changed-a"), b: []byte("changed-b")}
	if err = contentops.GuardedTransaction(root, changes, readset, func() error { return fmt.Errorf("synthetic postgate failure") }); err == nil {
		t.Fatal("failed postgate accepted")
	}
	for path, want := range map[string]string{a: "original-a", b: "original-b"} {
		got, _ := os.ReadFile(path)
		info, _ := os.Stat(path)
		if string(got) != want || info.Mode().Perm() != 0640 {
			t.Fatal("byte/mode rollback failed")
		}
	}
	if err = os.WriteFile(input, []byte("changed-source"), 0640); err != nil {
		t.Fatal(err)
	}
	if err = contentops.GuardedTransaction(root, changes, readset, nil); err == nil {
		t.Fatal("stale source readset accepted")
	}
	newTarget := filepath.Join(root, "new.json")
	fresh, err := contentops.CaptureReadSet([]string{newTarget, input})
	if err != nil {
		t.Fatal(err)
	}
	if err = contentops.GuardedTransaction(root, map[string][]byte{newTarget: []byte("new")}, fresh, func() error { return fmt.Errorf("rollback new file") }); err == nil {
		t.Fatal("failure accepted")
	}
	if _, err = os.Stat(newTarget); !os.IsNotExist(err) {
		t.Fatal("new file not rolled back")
	}
}
func TestOutputCannotFollowSymlinkOrOverwriteFixtures(t *testing.T) {
	root := t.TempDir()
	protected := filepath.Join(root, "cat_de_roman_esti/fixtures")
	if err := os.MkdirAll(protected, 0700); err != nil {
		t.Fatal(err)
	}
	target := filepath.Join(protected, "fixture.json")
	if err := os.WriteFile(target, []byte("original"), 0600); err != nil {
		t.Fatal(err)
	}
	link := filepath.Join(root, "link")
	if err := os.Symlink(protected, link); err != nil {
		t.Fatal(err)
	}
	if err := WriteOutputs([]string{filepath.Join(link, "fixture.json")}, []byte("changed")); err == nil {
		t.Fatal("symlink parent accepted")
	}
	got, _ := os.ReadFile(target)
	if string(got) != "original" {
		t.Fatal("protected fixture changed")
	}
	if err := ProtectedOutput(root, target); err == nil {
		t.Fatal("fixture output accepted")
	}
}

func TestSecondWorldTransitionRefusesStalePreviousArchive(t *testing.T) {
	root, s := historicalWorldRoot(t)
	previous, err := archive(root, s, "world_candidate")
	if err != nil {
		t.Fatal(err)
	}
	if err = previousMatchesCurrent(root, previous); err != nil {
		t.Fatal(err)
	}
	path, _ := ArtifactPath(root, "world")
	current, err := Read(path)
	if err != nil {
		t.Fatal(err)
	}
	older, err := archive(root, s, "world_previous")
	if err != nil {
		t.Fatal(err)
	}
	current["compatible_versions"] = rows(older["compatible_versions"])
	writeJSONTest(t, path, current)
	if err = previousMatchesCurrent(root, previous); err == nil {
		t.Fatal("stale previous history accepted for second transition")
	}
}

func TestRuntimeManifestIncludesRuleReceiptAndNewFileInvalidatesApproval(t *testing.T) {
	root, _ := cloneRoot(t)
	before, err := RuntimeHashes(root)
	if err != nil {
		t.Fatal(err)
	}
	included := false
	for _, v := range before {
		if object(v)["path"] == "go-backend/internal/contentbuild/rules_provenance.json" {
			included = true
		}
	}
	if !included {
		t.Fatal("frozen Unicode/source rule receipt omitted")
	}
	path := filepath.Join(root, "go-backend/internal/graph/new_runtime.go")
	if err = os.WriteFile(path, []byte("package graph\n"), 0644); err != nil {
		t.Fatal(err)
	}
	after, err := RuntimeHashes(root)
	if err != nil {
		t.Fatal(err)
	}
	if same(before, after) {
		t.Fatal("new runtime file escaped inventory binding")
	}
}
func TestLoadedCustomSourceCASRefusesChangedFlagFile(t *testing.T) {
	root := rootPath(t)
	dir := t.TempDir()
	s := sourceV2(t, dir)
	path := filepath.Join(dir, "source-v2.json")
	if err := validateLoadedSource(root, s, path); err != nil {
		t.Fatal(err)
	}
	changed := clone(s.Raw).(map[string]any)
	object(rows(object(changed["quick"])["boards"])[0])["rationale"] = "changed after source load"
	writeJSONTest(t, path, changed)
	if err := validateLoadedSource(root, s, path); err == nil {
		t.Fatal("stale loaded source object accepted")
	}
	if err := InstallProposal(root, s, "quick", "", "", "", "", "", "", "", "", path); err == nil {
		t.Fatal("stale source flag accepted by installation")
	}
}
