package contentbuild

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

func TestHistoricalBuildCurrentEntryPointsAndMetadataStayStrict(t *testing.T) {
	root := source5HistoricalRoot(t)
	if RubricSHA256 != "159155390d188545ed71c1697a21b7e46b236a51a3aacaf3ab6351ee17afcc3a" || historicalBuildRubricSHA256 != "3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101" {
		t.Fatal("current and genuine historical rubric scopes differ")
	}
	if err := verifyRubric(root); err == nil || !strings.Contains(err.Error(), "reviewed rubric digest drift") {
		t.Fatal("current rubric validator accepted immutable old rubric", err)
	}
	if _, err := Build(root); err == nil {
		t.Fatal("current Build implicitly accepted a historical root")
	}
	if _, err := Load(root); err == nil {
		t.Fatal("current Load implicitly accepted a historical root")
	}
	if err := ValidateSources(root); err == nil {
		t.Fatal("current source validation implicitly accepted a historical root")
	}
	if err := Export(root, true); err == nil {
		t.Fatal("current export check implicitly accepted a historical root")
	}
	context, err := openHistoricalBuildContext(root, historicalBuildSource5)
	if err != nil {
		t.Fatal(err)
	}
	src, digests := map[string]map[string]any{}, map[string]any{}
	for _, name := range SourceNames {
		path := sourcePath(root, name)
		raw, err := context.snapshotBytes(path, 16<<20)
		if err != nil {
			t.Fatal(err)
		}
		src[name], err = decodeObject(raw)
		if err != nil {
			t.Fatal(err)
		}
		digests[name] = TextSHA256(raw)
	}
	c, err := parsedGraph(src["kg_sample.json"])
	if err != nil {
		t.Fatal(err)
	}
	rules, err := frozenRules()
	if err != nil {
		t.Fatal(err)
	}
	if _, err := validateRankings(src["board_rankings_v37.json"], src["games_pack.json"], digests); err == nil || !strings.Contains(err.Error(), "rubric_sha256") {
		t.Fatal("current rankings validator accepted historical rubric", err)
	}
	if err := validateDerived(src["derived_catalog_v38.json"], src["games_pack.json"], digests, rules); err == nil || !strings.Contains(err.Error(), "rubric_sha256") {
		t.Fatal("current derived validator accepted historical rubric", err)
	}
	if err := ValidateQuickCatalog(src["quick_games_v92.json"], src["derived_catalog_v38.json"], graph.New(c), digests); err == nil || !strings.Contains(err.Error(), "rubric_sha256") {
		t.Fatal("public current quick validator accepted historical rubric", err)
	}
	// Test-only pin scoping still cannot change the current rubric requirement.
	historicalSource45ReviewedPins(t)
	if _, err := Build(root); err == nil || !strings.Contains(err.Error(), "reviewed rubric digest drift") {
		t.Fatal("historical reviewed pins conferred current rubric authority", err)
	}
}

func TestHistoricalBuildPrivateSnapshotSurvivesTransientEditAndCloneMutation(t *testing.T) {
	root := source5HistoricalRoot(t)
	context, err := openHistoricalBuildContext(root, historicalBuildSource5)
	if err != nil {
		t.Fatal(err)
	}
	path := sourcePath(root, "quick_games_v92.json")
	original, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	defer func() {
		if err := os.WriteFile(path, original, 0600); err != nil {
			t.Error(err)
		}
	}()
	clone, err := context.snapshotBytes(path, 2<<20)
	if err != nil {
		t.Fatal(err)
	}
	clone[0] ^= 1
	if err := os.WriteFile(path, []byte("{\"transient\":true}\n"), 0600); err != nil {
		t.Fatal(err)
	}
	// These are the same reader functions used for every historical builder
	// source, digest, mirror and rubric read. Neither reopens mutable bytes.
	frozen, err := buildReadBytes(path, 2<<20, context)
	if err != nil || !bytes.Equal(frozen, original) {
		t.Fatal("transient filesystem or caller clone mutation reached snapshot", err)
	}
	object, err := buildReadObject(path, 2<<20, context)
	if err != nil || object["kind"] != "quick-content-catalog-v1" {
		t.Fatal("historical JSON reader used transient filesystem bytes", err)
	}
	object["kind"] = "caller mutation"
	again, err := buildReadObject(path, 2<<20, context)
	if err != nil || again["kind"] != "quick-content-catalog-v1" {
		t.Fatal("decoded caller mutation reached snapshot", err)
	}
	if output, err := context.build(); err == nil || output != nil {
		t.Fatal("stale context returned historical build bytes", err)
	}
	if err := os.WriteFile(path, original, 0600); err != nil {
		t.Fatal(err)
	}
	if err := context.verify(); err != nil {
		t.Fatal("restored exact historical root failed closure check", err)
	}
	frozen, err = context.snapshotBytes(path, 2<<20)
	if err != nil || !bytes.Equal(frozen, original) {
		t.Fatal("edit-and-undo changed private immutable snapshot", err)
	}
	if _, err := context.snapshotBytes(path, 1); err == nil {
		t.Fatal("snapshot ignored caller read bound")
	}
	if _, err := context.snapshotBytes(filepath.Join(filepath.Dir(root), "outside.json"), 2<<20); err == nil {
		t.Fatal("snapshot accepted path outside historical root")
	}
	if _, err := buildWithHistoricalContext(root+"-other", true, context); err == nil {
		t.Fatal("historical context was rebound to another root")
	}
}

func TestHistoricalBuildProfilesAndExactClosureRefuseChanges(t *testing.T) {
	root := source5HistoricalRoot(t)
	if _, err := openHistoricalBuildContext(root, historicalBuildProfile(255)); err == nil {
		t.Fatal("unknown historical profile accepted")
	}
	if _, err := openHistoricalBuildContext(root, historicalBuildSource4); err == nil {
		t.Fatal("Source5 closure accepted as Source4")
	}
	if _, err := openHistoricalBuildContext(root, historicalBuildOriginalSource6); err == nil {
		t.Fatal("Source5 closure accepted as original Source6")
	}
	if _, err := openHistoricalBuildContext(root, historicalBuildReviewedSource6); err == nil {
		t.Fatal("Source5 closure accepted as reviewed Source6")
	}
	if _, err := openHistoricalBuildContext(root+"/../"+filepath.Base(root), historicalBuildSource5); err == nil {
		t.Fatal("noncanonical historical root accepted")
	}
	t.Run("unknown member", func(t *testing.T) {
		path := filepath.Join(root, "unexpected.json")
		if err := os.WriteFile(path, []byte("{}\n"), 0600); err != nil {
			t.Fatal(err)
		}
		defer os.Remove(path)
		if _, err := openHistoricalBuildContext(root, historicalBuildSource5); err == nil {
			t.Fatal("historical closure accepted extra member")
		}
	})
	t.Run("missing member", func(t *testing.T) {
		path := sourcePath(root, "quick_games_v92.json")
		original, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		if err := os.Remove(path); err != nil {
			t.Fatal(err)
		}
		defer os.WriteFile(path, original, 0600)
		if _, err := openHistoricalBuildContext(root, historicalBuildSource5); err == nil {
			t.Fatal("historical closure accepted missing member")
		}
	})
	t.Run("symlink member", func(t *testing.T) {
		path := sourcePath(root, "quick_games_v92.json")
		original, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		outside := filepath.Join(t.TempDir(), "original-quick.json")
		if err := os.WriteFile(outside, original, 0600); err != nil {
			t.Fatal(err)
		}
		if err := os.Remove(path); err != nil {
			t.Fatal(err)
		}
		defer func() {
			_ = os.Remove(path)
			if err := os.WriteFile(path, original, 0600); err != nil {
				t.Error(err)
			}
		}()
		if err := os.Symlink(outside, path); err != nil {
			t.Fatal(err)
		}
		if _, err := openHistoricalBuildContext(root, historicalBuildSource5); err == nil {
			t.Fatal("historical closure accepted symlink to exact pinned bytes")
		}
	})
}
