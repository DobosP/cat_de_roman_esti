//go:build linux

package contentbuild

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"
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
	rootAlias := filepath.Join(t.TempDir(), "root-alias")
	if err := os.Symlink(root, rootAlias); err != nil {
		t.Fatal(err)
	}
	aliasInside := filepath.Join(root, "prospective-alias-should-not-exist.json")
	if err := WriteProspectiveLantCaptions(rootAlias, sourcePath(root, "kg_sample.json"), sourcePath(root, "games_pack.json"), aliasInside); err == nil || !strings.Contains(err.Error(), "outside repository root") {
		t.Fatalf("symlink-aliased root bypassed repository boundary: %v", err)
	}
	if _, err := os.Lstat(aliasInside); !os.IsNotExist(err) {
		t.Fatalf("root-alias refusal wrote inside repository: %v", err)
	}
	finalAlias := filepath.Join(t.TempDir(), "preview.json")
	if err := os.Symlink(filepath.Join(t.TempDir(), "target.json"), finalAlias); err != nil {
		t.Fatal(err)
	}
	if err := WriteProspectiveLantCaptions(root, sourcePath(root, "kg_sample.json"), sourcePath(root, "games_pack.json"), finalAlias); err == nil {
		t.Fatal("symlink output file accepted")
	}
	linkedKG := filepath.Join(t.TempDir(), "kg.json")
	if err := os.Symlink(sourcePath(root, "kg_sample.json"), linkedKG); err != nil {
		t.Fatal(err)
	}
	if _, err := BuildProspectiveLantCaptions(root, linkedKG, sourcePath(root, "games_pack.json")); err == nil || !strings.Contains(err.Error(), "canonical without symlinks") {
		t.Fatalf("symlinked source accepted: %v", err)
	}
}

func TestProspectiveInputsRejectSymlinkedAncestors(t *testing.T) {
	root := repoRoot(t)
	for _, tc := range []struct {
		name string
		kg   bool
	}{
		{name: "kg", kg: true},
		{name: "pack", kg: false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			realParent := t.TempDir()
			name := "games_pack.json"
			if tc.kg {
				name = "kg_sample.json"
			}
			data, err := os.ReadFile(sourcePath(root, name))
			if err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(realParent, name), data, 0o600); err != nil {
				t.Fatal(err)
			}
			aliasParent := filepath.Join(t.TempDir(), "alias")
			if err := os.Symlink(realParent, aliasParent); err != nil {
				t.Fatal(err)
			}
			kgPath := sourcePath(root, "kg_sample.json")
			packPath := sourcePath(root, "games_pack.json")
			if tc.kg {
				kgPath = filepath.Join(aliasParent, name)
			} else {
				packPath = filepath.Join(aliasParent, name)
			}
			if _, err := BuildProspectiveLantCaptions(root, kgPath, packPath); err == nil || !strings.Contains(err.Error(), "canonical without symlinks") {
				t.Fatalf("symlinked %s ancestor accepted: %v", tc.name, err)
			}
		})
	}
}

func TestReadDirectBindsOpenedDescriptorAcrossAncestorReplacement(t *testing.T) {
	parent := t.TempDir()
	path := filepath.Join(parent, "source.json")
	original := []byte("original descriptor bytes")
	if err := os.WriteFile(path, original, 0o600); err != nil {
		t.Fatal(err)
	}
	moved := parent + "-moved"
	t.Cleanup(func() { _ = os.RemoveAll(moved) })
	got, err := readDirectAfterOpen(path, 1<<20, func() error {
		if err := os.Rename(parent, moved); err != nil {
			return err
		}
		if err := os.Mkdir(parent, 0o700); err != nil {
			return err
		}
		return os.WriteFile(path, []byte("replacement bytes"), 0o600)
	})
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, original) {
		t.Fatalf("read bytes from replacement path: %q", got)
	}
}

func TestProspectiveFinalCreateResolvesWholePathAfterParentRelocation(t *testing.T) {
	root := repoRoot(t)
	outside := t.TempDir()
	parent := filepath.Join(outside, "approved-parent")
	if err := os.Mkdir(parent, 0o700); err != nil {
		t.Fatal(err)
	}
	out := filepath.Join(parent, "preview.json")
	var moved string
	err := writeProspectiveLantCaptionsBeforeCreate(root, sourcePath(root, "kg_sample.json"), sourcePath(root, "games_pack.json"), out, func() error {
		protectedRoot, err := os.MkdirTemp(root, ".prospective-relocation-test-")
		if err != nil {
			return err
		}
		t.Cleanup(func() { _ = os.RemoveAll(protectedRoot) })
		moved = filepath.Join(protectedRoot, "relocated-parent")
		if err := os.Rename(parent, moved); err != nil {
			return err
		}
		return os.Mkdir(parent, 0o700)
	})
	if errors.Is(err, syscall.EXDEV) {
		t.Skip("relocation needs TMPDIR on the checkout filesystem")
	}
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(out); err != nil {
		t.Fatalf("replacement outside path did not receive output: %v", err)
	}
	if _, err := os.Lstat(filepath.Join(moved, "preview.json")); !os.IsNotExist(err) {
		t.Fatalf("output was created in relocated repository parent: %v", err)
	}
}

func TestProspectiveProducerClosureIsProductionComplete(t *testing.T) {
	root := repoRoot(t)
	paths, err := nativeProducerPaths(root)
	if err != nil {
		t.Fatal(err)
	}
	got := map[string]bool{}
	for _, path := range paths {
		rel, err := filepath.Rel(root, path)
		if err != nil {
			t.Fatal(err)
		}
		rel = filepath.ToSlash(rel)
		got[rel] = true
		if strings.HasSuffix(rel, "_test.go") {
			t.Fatalf("test file entered producer identity: %s", rel)
		}
	}
	for _, required := range []string{
		"go-backend/go.mod",
		"go-backend/go.sum",
		"go-backend/cmd/cat-content/main.go",
		"go-backend/internal/content/content.go",
		"go-backend/internal/contentbuild/rules_provenance.json",
		"go-backend/internal/contentbuild/rules_unicode15.json",
		"go-backend/internal/graph/service.go",
		"go-backend/internal/strictjson/validate.go",
	} {
		if !got[required] {
			t.Errorf("producer closure omitted %s", required)
		}
	}
	if got[excludedServingEmbed] {
		t.Fatalf("semantically unused installed serving bundle entered prospective identity: %s", excludedServingEmbed)
	}
}

func TestReadDirectRefusesFIFOWithoutBlocking(t *testing.T) {
	path := filepath.Join(t.TempDir(), "kg.json")
	if err := syscall.Mkfifo(path, 0o600); err != nil {
		t.Fatal(err)
	}
	done := make(chan error, 1)
	go func() {
		_, err := readDirect(path, 1<<20)
		done <- err
	}()
	select {
	case err := <-done:
		if err == nil || !strings.Contains(err.Error(), "not a regular file") {
			t.Fatalf("FIFO input was not refused as a non-regular file: %v", err)
		}
	case <-time.After(5 * time.Second):
		t.Fatal("FIFO input blocked instead of being refused")
	}
}

func TestGoListEnvPinsLocalToolchain(t *testing.T) {
	t.Setenv("GOTOOLCHAIN", "auto")
	var toolchains []string
	for _, item := range cleanGoListEnv() {
		if strings.HasPrefix(item, "GOTOOLCHAIN=") {
			toolchains = append(toolchains, item)
		}
	}
	if len(toolchains) != 1 || toolchains[0] != "GOTOOLCHAIN=local" {
		t.Fatalf("go list environment must pin exactly GOTOOLCHAIN=local, got %v", toolchains)
	}
}
