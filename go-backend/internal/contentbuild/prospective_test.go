package contentbuild

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func writeObject(t *testing.T, path string, value map[string]any) {
	t.Helper()
	b, err := Canonical(value)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, append(b, '\n'), 0o600); err != nil {
		t.Fatal(err)
	}
}

func TestProspectiveLantCaptionsMatchServingBuildAtBaseline(t *testing.T) {
	root := repoRoot(t)
	b, err := BuildProspectiveLantCaptions(root, sourcePath(root, "kg_sample.json"), sourcePath(root, "games_pack.json"))
	if err != nil {
		t.Fatal(err)
	}
	preview, err := decodeObject(b)
	if err != nil {
		t.Fatal(err)
	}
	servingBytes, err := Build(root)
	if err != nil {
		t.Fatal(err)
	}
	serving, err := decodeObject(servingBytes)
	if err != nil {
		t.Fatal(err)
	}
	if preview["schema"] != prospectiveLantCaptionSchema || preview["purpose"] != "unapproved_native_preview_only" || preview["game"] != "lant" {
		t.Fatal("preview identity drift")
	}
	if !equal(preview["captions"], serving["lant_captions"]) {
		t.Fatal("prospective captions differ from serving Build derivation")
	}
	if int(number(object(preview["counts"])["directed_edges"])) != len(object(preview["captions"])) {
		t.Fatal("caption count binding differs")
	}
	for _, forbidden := range []string{"nodes", "edges", "boards", "pack_items", "lant_captions"} {
		if _, ok := preview[forbidden]; ok {
			t.Fatalf("preview became a serving-like bundle: %s", forbidden)
		}
	}
}

func TestProspectiveLantCaptionsRejectInvalidFixtureAndPack(t *testing.T) {
	root := repoRoot(t)
	kg := source(t, "kg_sample.json")
	pack := source(t, "games_pack.json")
	t.Run("fixture", func(t *testing.T) {
		bad := clone(t, kg)
		object(array(bad["kg_nodes"])[0])["difficulty_tier"] = "invalid"
		kgPath := filepath.Join(t.TempDir(), "kg.json")
		writeObject(t, kgPath, bad)
		if _, err := BuildProspectiveLantCaptions(root, kgPath, sourcePath(root, "games_pack.json")); err == nil || !strings.Contains(err.Error(), "fixture invalid") {
			t.Fatalf("invalid fixture accepted: %v", err)
		}
	})
	t.Run("pack", func(t *testing.T) {
		bad := clone(t, pack)
		object(object(bad["meta"])["counts"])["lant"] = 0
		packPath := filepath.Join(t.TempDir(), "pack.json")
		writeObject(t, packPath, bad)
		if _, err := BuildProspectiveLantCaptions(root, sourcePath(root, "kg_sample.json"), packPath); err == nil || !strings.Contains(err.Error(), "pack invalid") {
			t.Fatalf("invalid pack accepted: %v", err)
		}
	})
}

func TestFullBuildStillRejectsProspectiveSourcePinDrift(t *testing.T) {
	current := repoRoot(t)
	root := t.TempDir()
	for _, name := range SourceNames {
		b, err := os.ReadFile(sourcePath(current, name))
		if err != nil {
			t.Fatal(err)
		}
		path := sourcePath(root, name)
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			t.Fatal(err)
		}
		if name == "kg_sample.json" {
			kg, err := decodeObject(b)
			if err != nil {
				t.Fatal(err)
			}
			object(kg["meta"])["build_version"] = "unapproved-prospective-test"
			writeObject(t, path, kg)
			writeObject(t, filepath.Join(root, "tests", "fixtures", name), kg)
			continue
		}
		if err := os.WriteFile(path, b, 0o600); err != nil {
			t.Fatal(err)
		}
		if name == "games_pack.json" {
			mirror := filepath.Join(root, "tests", "fixtures", name)
			if err := os.MkdirAll(filepath.Dir(mirror), 0o755); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(mirror, b, 0o600); err != nil {
				t.Fatal(err)
			}
		}
	}
	rubric, err := os.ReadFile(filepath.Join(current, "docs", "CRITIQUE_RUBRIC.md"))
	if err != nil {
		t.Fatal(err)
	}
	rubricPath := filepath.Join(root, "docs", "CRITIQUE_RUBRIC.md")
	if err := os.MkdirAll(filepath.Dir(rubricPath), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(rubricPath, rubric, 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := Build(root); err == nil || !strings.Contains(err.Error(), "board rankings: source binding drift: kg_sha256") {
		t.Fatalf("full Build did not retain source-pin refusal: %v", err)
	}
}

func TestProspectiveLantCaptionWriteIsOutsideRootAndExclusive(t *testing.T) {
	root := repoRoot(t)
	inside := filepath.Join(root, "prospective-should-not-exist.json")
	if err := WriteProspectiveLantCaptions(root, sourcePath(root, "kg_sample.json"), sourcePath(root, "games_pack.json"), inside); err == nil {
		t.Fatal("preview wrote inside repository source root")
	}
	out := filepath.Join(t.TempDir(), "preview.json")
	if err := WriteProspectiveLantCaptions(root, sourcePath(root, "kg_sample.json"), sourcePath(root, "games_pack.json"), out); err != nil {
		t.Fatal(err)
	}
	first, err := os.ReadFile(out)
	if err != nil || len(first) == 0 {
		t.Fatal("preview output missing", err)
	}
	if err := WriteProspectiveLantCaptions(root, sourcePath(root, "kg_sample.json"), sourcePath(root, "games_pack.json"), out); err == nil {
		t.Fatal("preview overwrote existing output")
	}
	after, err := os.ReadFile(out)
	if err != nil || !bytes.Equal(first, after) {
		t.Fatal("existing preview changed", err)
	}
	realParent := t.TempDir()
	linkParent := filepath.Join(t.TempDir(), "linked-parent")
	if err := os.Symlink(realParent, linkParent); err != nil {
		t.Fatal(err)
	}
	if err := WriteProspectiveLantCaptions(root, sourcePath(root, "kg_sample.json"), sourcePath(root, "games_pack.json"), filepath.Join(linkParent, "preview.json")); err == nil || !strings.Contains(err.Error(), "must not traverse symlinks") {
		t.Fatalf("symlinked output parent accepted: %v", err)
	}
	linkedKG := filepath.Join(t.TempDir(), "kg.json")
	if err := os.Symlink(sourcePath(root, "kg_sample.json"), linkedKG); err != nil {
		t.Fatal(err)
	}
	if _, err := BuildProspectiveLantCaptions(root, linkedKG, sourcePath(root, "games_pack.json")); err == nil || !strings.Contains(err.Error(), "direct regular file") {
		t.Fatalf("symlinked source accepted: %v", err)
	}
}
