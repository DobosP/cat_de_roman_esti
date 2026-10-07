package contentrails

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Old contract tests retain their original literal assertions against the exact
// archived Source4 world and its matching KG. Only this private test root receives
// historical bytes; current serving pins and loaders are never changed.
func historicalWorldRoot(t *testing.T) (string, *Source) {
	t.Helper()
	root := historicalSource5RailsRoot(t)
	s := sourceForTest(t)
	raw, err := os.ReadFile(filepath.Join(rootPath(t), "docs/reviews/v1-4-time-links-and-predicates/native/world/proposal.json"))
	if err != nil || digestBytes(raw) != "0d10180a3ad7cd88ba642cd1326fcbf78a2e398af8643a75f9e1b1d789909cef" {
		t.Fatal("authentic Source4 world archive changed", err)
	}
	path, err := ArtifactPath(root, "world")
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	return root, s
}

func TestInstalledWorldReconstructionAfterRecipeTransition(t *testing.T) {
	root := historicalSource5RailsRoot(t)
	s, err := LoadSource(filepath.Join(root, "go-backend/internal/contentrails/sources/authored-v5.json"))
	if err != nil {
		t.Fatal(err)
	}
	dir := filepath.Join(root, "docs/reviews/v1-5-hot-chocolate/native/world")
	candidate, factual, quality := filepath.Join(dir, "candidate.json"), filepath.Join(dir, "factual-review.json"), filepath.Join(dir, "quality-review.json")
	if _, err = Candidate(root, s, "world", false); err == nil || !strings.Contains(err.Error(), "previous immutable archive is stale") {
		t.Fatal("public staging accepted an already-completed mechanics transition", err)
	}
	if _, err = BuildProposal(root, s, "world", candidate, factual, quality); err == nil {
		t.Fatal("public proposal bypassed the unchanged staging predecessor guard")
	}
	proposal, err := buildInstalledProposal(root, s, "world", candidate, factual, quality)
	if err != nil {
		t.Fatal(err)
	}
	actual, err := os.ReadFile(filepath.Join(dir, "proposal.json"))
	if err != nil {
		t.Fatal(err)
	}
	rebuilt, err := Render(proposal)
	if err != nil || digestBytes(actual) != "196e0b72310e6ec7b9b18254b4b95a307d9ae7a9ecb97f3670b66f24ff071086" || !bytes.Equal(rebuilt, actual) {
		t.Fatal("installed reconstruction changed the reviewed exact Source5 proposal", err)
	}
	audit, err := auditWorld(root, proposal)
	if err != nil {
		t.Fatal(err)
	}
	if len(rows(audit["goal_replays"])) != 33 || len(rows(audit["compatible_save_replays"])) != 10 || integer(audit["historical_prefixes"]) != 1156 || integer(object(audit["metrics"])["recipes"]) != 352 {
		t.Fatal("current Source5 goal/recipe/full historical coverage changed", audit["metrics"])
	}
	for _, mutation := range []struct {
		name   string
		change func(map[string]any)
	}{
		{"world-id", func(m map[string]any) { object(m["world"])["id"] = "wrong-world" }},
		{"recipe-result", func(m map[string]any) { object(rows(m["recipes"])[0])["result"] = "wrong-result" }},
		{"history-removal", func(m map[string]any) { m["compatible_versions"] = rows(m["compatible_versions"])[1:] }},
		{"history-mutation", func(m map[string]any) {
			object(rows(m["compatible_versions"])[0])["recipe_hash"] = strings.Repeat("0", 64)
		}},
	} {
		t.Run(mutation.name, func(t *testing.T) {
			temp := historicalSource5RailsRoot(t)
			current, err := fixture(temp, "alchimie_discovery_world_v92.json")
			if err != nil {
				t.Fatal(err)
			}
			mutation.change(current)
			path, _ := ArtifactPath(temp, "world")
			writeJSONTest(t, path, current)
			if _, err = buildInstalledProposal(temp, s, "world", candidate, factual, quality); err == nil || !strings.Contains(err.Error(), "installed world differs") {
				t.Fatal("installed reconstruction accepted changed mechanics/history", err)
			}
		})
	}
}
