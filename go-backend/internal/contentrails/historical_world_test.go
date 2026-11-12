package contentrails

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
)

func TestHistoricalWorldContextGenuineManifest12AndClosure27(t *testing.T) {
	root := historicalSource5RailsRoot(t)
	c, err := OpenHistoricalWorldContext(root, HistoricalSource5World)
	if err != nil {
		t.Fatal(err)
	}
	manifestRaw := readHistoricalRailsFile(t, "docs/reviews/v1-6-everyday-inputs/reference/historical-source5-context-manifest.json", 32<<10, "47d93bbae6a5a6f5eec031a09568c20e2f81887598cff9fff9120c9eeff2a48c")
	var manifest struct {
		Entries map[string]struct {
			Bytes  int64  `json:"bytes"`
			SHA256 string `json:"sha256"`
		} `json:"entries"`
	}
	if err := json.Unmarshal(manifestRaw, &manifest); err != nil {
		t.Fatal(err)
	}
	if len(manifest.Entries) != 12 || len(source5HistoricalWorldMembers()) != 27 {
		t.Fatal("genuine immutable profile membership changed")
	}
	for path, original := range manifest.Entries {
		member, ok := source5HistoricalWorldMembers()[path]
		if !ok || member.bytes != original.Bytes || member.sha != original.SHA256 {
			t.Fatal("historical profile differs from genuine manifest", path)
		}
	}
	s, err := LoadSource(filepath.Join(root, "go-backend/internal/contentrails/sources/authored-v5.json"))
	if err != nil {
		t.Fatal(err)
	}
	dir := filepath.Join(root, "docs/reviews/v1-5-hot-chocolate/native/world")
	proposal, err := c.ReconstructProposal(s, filepath.Join(dir, "candidate.json"), filepath.Join(dir, "factual-review.json"), filepath.Join(dir, "quality-review.json"), true)
	if err != nil {
		t.Fatal(err)
	}
	b, err := Render(proposal)
	if err != nil || digestBytes(b) != "196e0b72310e6ec7b9b18254b4b95a307d9ae7a9ecb97f3670b66f24ff071086" {
		t.Fatal("genuine Source5 exact proposal reconstruction changed", err)
	}
}

func TestHistoricalWorldContextDefaultCurrentPathNeverFallsBack(t *testing.T) {
	const old = "3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101"
	if contentbuild.RubricSHA256 == old {
		t.Fatal("run this control with the reviewed current rubric transition")
	}
	root := historicalSource5RailsRoot(t)
	if _, err := bindings(root); err == nil || !strings.Contains(err.Error(), "review rubric drift") {
		t.Fatal("default current bindings silently accepted historical rubric", err)
	}
	if _, err := Candidate(root, sourceForTest(t), "world", false); err == nil || !strings.Contains(err.Error(), "review rubric drift") {
		t.Fatal("default current candidate silently selected historical compatibility", err)
	}
	current := t.TempDir()
	for _, name := range contentbuild.SourceNames {
		b, err := os.ReadFile(filepath.Join(rootPath(t), "cat_de_roman_esti/fixtures", name))
		if err != nil {
			t.Fatal(err)
		}
		path := filepath.Join(current, "cat_de_roman_esti/fixtures", name)
		if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	oldRubric, err := os.ReadFile(filepath.Join(root, "docs/CRITIQUE_RUBRIC.md"))
	if err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(current, "docs"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(current, "docs/CRITIQUE_RUBRIC.md"), oldRubric, 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := bindings(current); err == nil {
		t.Fatal("current sources plus only an old rubric bypassed strict current binding")
	}
	if _, err := OpenHistoricalWorldContext(current, HistoricalSource5World); err == nil {
		t.Fatal("current/mixed root passed genuine historical profile")
	}
}

func TestHistoricalWorldContextExplicitSource4VariantOnly(t *testing.T) {
	root, s := historicalWorldRoot(t)
	c, err := OpenHistoricalWorldContext(root, HistoricalSource4WorldOnSource5KG)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := c.Candidate(s); err != nil {
		t.Fatal("genuine explicit Source4 variant refused", err)
	}
	if _, err := OpenHistoricalWorldContext(root, HistoricalSource5World); err == nil {
		t.Fatal("Source4 world silently treated as Source5 world")
	}
	if _, err := OpenHistoricalWorldContext(historicalSource5RailsRoot(t), HistoricalSource4WorldOnSource5KG); err == nil {
		t.Fatal("Source5 world silently treated as Source4 world")
	}
}

func TestHistoricalWorldContextUnknownMixedStaleAndAliasesRefuse(t *testing.T) {
	for _, mutation := range []struct {
		name   string
		path   string
		change func(string) error
	}{
		{"unknown-member", "unregistered.json", func(p string) error { return os.WriteFile(p, []byte("{}\n"), 0600) }},
		{"missing-member", "go-backend/internal/content/digest.go", os.Remove},
		{"old-root-new-rubric", "docs/CRITIQUE_RUBRIC.md", func(p string) error { return os.WriteFile(p, []byte("changed current rubric\n"), 0600) }},
		{"mixed-kg", "cat_de_roman_esti/fixtures/kg_sample.json", func(p string) error {
			b, err := os.ReadFile(filepath.Join(rootPath(t), "cat_de_roman_esti/fixtures/kg_sample.json"))
			if err != nil {
				return err
			}
			return os.WriteFile(p, b, 0600)
		}},
		{"stale-bundle", "go-backend/internal/content/bundled.json", func(p string) error { return os.WriteFile(p, []byte("{}\n"), 0600) }},
		{"symlink-member", "go-backend/internal/content/digest.go", func(p string) error {
			if err := os.Remove(p); err != nil {
				return err
			}
			return os.Symlink("bundled.json", p)
		}},
	} {
		t.Run(mutation.name, func(t *testing.T) {
			root := historicalSource5RailsRoot(t)
			c, err := OpenHistoricalWorldContext(root, HistoricalSource5World)
			if err != nil {
				t.Fatal(err)
			}
			if err := mutation.change(filepath.Join(root, mutation.path)); err != nil {
				t.Fatal(err)
			}
			if _, err := OpenHistoricalWorldContext(root, HistoricalSource5World); err == nil {
				t.Fatal("changed historical context reopened")
			}
			if _, err := c.Candidate(sourceForTest(t)); err == nil {
				t.Fatal("context trusted stale validation after member changed")
			}
		})
	}
	root := historicalSource5RailsRoot(t)
	if _, err := OpenHistoricalWorldContext(root, HistoricalWorldProfile(99)); err == nil {
		t.Fatal("unknown historical profile accepted")
	}
	c, err := OpenHistoricalWorldContext(root, HistoricalSource5World)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := c.bindings(t.TempDir()); err == nil {
		t.Fatal("context applied to another root")
	}
	s := sourceForTest(t)
	changed := &Source{Raw: clone(s.Raw).(map[string]any), SHA256: s.SHA256, Version: s.Version}
	object(changed.Raw["world"])["starters"] = []any{"forged-old-source"}
	if _, err := c.Candidate(changed); err == nil {
		t.Fatal("forged source SHA hid changed source semantics")
	}
	before, err := os.ReadFile(filepath.Join(root, "docs/CRITIQUE_RUBRIC.md"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := c.ReconstructProposal(s, filepath.Join(rootPath(t), "docs/reviews/v1-5-hot-chocolate/native/world/candidate.json"), "wrong", "wrong", true); err == nil {
		t.Fatal("external/unregistered proposal inputs accepted")
	}
	after, err := os.ReadFile(filepath.Join(root, "docs/CRITIQUE_RUBRIC.md"))
	if err != nil || !bytes.Equal(before, after) {
		t.Fatal("read-only historical context wrote rubric", err)
	}
}

func TestHistoricalWorldContextSnapshotCoversEveryReconstructionRead(t *testing.T) {
	root := historicalSource5RailsRoot(t)
	c, err := OpenHistoricalWorldContext(root, HistoricalSource5World)
	if err != nil {
		t.Fatal(err)
	}
	s, err := LoadSource(filepath.Join(root, "go-backend/internal/contentrails/sources/authored-v5.json"))
	if err != nil {
		t.Fatal(err)
	}
	selected, err := c.selectedSource(s)
	if err != nil {
		t.Fatal(err)
	}
	dir := filepath.Join(root, "docs/reviews/v1-5-hot-chocolate/native/world")
	cp, fp, qp := filepath.Join(dir, "candidate.json"), filepath.Join(dir, "factual-review.json"), filepath.Join(dir, "quality-review.json")
	// All actual graph/archive/fixture/candidate/review/source reads used by
	// both public operations are attacked together after the snapshot is open.
	// Their original bytes are restored before the final permanent-stale check.
	// Private reconstruction must use frozen bytes even while working paths
	// contain invalid JSON; the public operation must refuse permanent drift.
	relatives := []string{
		"cat_de_roman_esti/fixtures/kg_sample.json",
		"cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json",
		"docs/CRITIQUE_RUBRIC.md",
		"go-backend/internal/contentrails/sources/authored-v5.json",
		"docs/reviews/v1-4-time-links-and-predicates/native/world/candidate.json",
		"docs/reviews/v1-5-hot-chocolate/native/world/candidate.json",
		"docs/reviews/v1-5-hot-chocolate/native/world/factual-review.json",
		"docs/reviews/v1-5-hot-chocolate/native/world/quality-review.json",
	}
	original := map[string][]byte{}
	for _, relative := range relatives {
		p := filepath.Join(root, relative)
		b, err := os.ReadFile(p)
		if err != nil {
			t.Fatal(err)
		}
		original[relative] = b
		if err := os.WriteFile(p, []byte("INVALID transient working bytes"), 0600); err != nil {
			t.Fatal(err)
		}
	}
	defer func() {
		for relative, b := range original {
			if err := os.WriteFile(filepath.Join(root, relative), b, 0600); err != nil {
				t.Error(err)
			}
		}
	}()
	if _, err := c.ReconstructProposal(s, cp, fp, qp, true); err == nil {
		t.Fatal("public historical operation accepted permanently changed working files")
	}
	proposal, err := buildProposalForContext(root, selected, "world", cp, fp, qp, true, c)
	if err != nil {
		t.Fatal("a historical reconstruction path reopened unverified working bytes", err)
	}
	b, err := Render(proposal)
	if err != nil || digestBytes(b) != "196e0b72310e6ec7b9b18254b4b95a307d9ae7a9ecb97f3670b66f24ff071086" {
		t.Fatal("transient files changed frozen Source5 reconstruction", err)
	}
	for relative, b := range original {
		if err := os.WriteFile(filepath.Join(root, relative), b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	if err := c.verify(); err != nil {
		t.Fatal("restored genuine root differs", err)
	}
	actual, err := c.ReconstructProposal(s, cp, fp, qp, true)
	if err != nil {
		t.Fatal(err)
	}
	b, err = Render(actual)
	if err != nil || digestBytes(b) != "196e0b72310e6ec7b9b18254b4b95a307d9ae7a9ecb97f3670b66f24ff071086" {
		t.Fatal("restored public reconstruction differs", err)
	}
}

func TestHistoricalWorldContextFrozenBytesAndSelectedSourceNeverAliasCallers(t *testing.T) {
	root := historicalSource5RailsRoot(t)
	c, err := OpenHistoricalWorldContext(root, HistoricalSource5World)
	if err != nil {
		t.Fatal(err)
	}
	const relative = "cat_de_roman_esti/fixtures/kg_sample.json"
	a, err := c.snapshotBytes(relative, 16<<20)
	if err != nil {
		t.Fatal(err)
	}
	wanted := digestBytes(a)
	a[0] ^= 1
	b, err := c.snapshotBytes(relative, 16<<20)
	if err != nil || digestBytes(b) != wanted {
		t.Fatal("snapshot bytes exposed mutable private storage", err)
	}
	s := sourceForTest(t)
	selected, err := c.selectedSource(s)
	if err != nil {
		t.Fatal(err)
	}
	before := digest(s.Raw)
	object(selected.Raw["world"])["starters"] = []any{"changed caller-owned selected copy"}
	if digest(s.Raw) != before {
		t.Fatal("selected source aliases caller source")
	}
	again, err := c.selectedSource(s)
	if err != nil || digest(again.Raw) != before {
		t.Fatal("selected source mutation reached pinned source storage", err)
	}
	obj, err := worldReadObject(filepath.Join(root, "docs/reviews/v1-5-hot-chocolate/native/world/factual-review.json"), c)
	if err != nil {
		t.Fatal(err)
	}
	old := digest(obj)
	obj["reviewer"] = "changed caller-owned decoded copy"
	obj, err = worldReadObject(filepath.Join(root, "docs/reviews/v1-5-hot-chocolate/native/world/factual-review.json"), c)
	if err != nil || digest(obj) != old {
		t.Fatal("decoded review mutation reached frozen bytes", err)
	}
}
