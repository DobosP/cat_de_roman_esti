package contentrails

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
)

func readHistoricalRailsFile(t *testing.T, relative string, limit int64, expected string) []byte {
	t.Helper()
	f, err := os.Open(filepath.Join(rootPath(t), filepath.FromSlash(relative)))
	if err != nil {
		t.Fatal(err)
	}
	raw, err := io.ReadAll(io.LimitReader(f, limit+1))
	closeErr := f.Close()
	if err != nil || closeErr != nil || int64(len(raw)) > limit || digestBytes(raw) != expected {
		t.Fatalf("historical rail file identity/bound differs: %s (%v, %v)", relative, err, closeErr)
	}
	return raw
}

// World-only contract roots contain genuine Source5 inputs and the exact old
// author/review closure. They do not borrow current authority membership, rewrite
// reviewed pins, or make historical contentbuild.Load pass current serving pins.
func historicalSource5RailsRoot(t *testing.T) string {
	t.Helper()
	manifestRaw := readHistoricalRailsFile(t, "docs/reviews/v1-6-everyday-inputs/reference/historical-source5-context-manifest.json", 32<<10, "47d93bbae6a5a6f5eec031a09568c20e2f81887598cff9fff9120c9eeff2a48c")
	var manifest struct {
		Schema         string `json:"schema"`
		BaselineCommit string `json:"baseline_commit"`
		Entries        map[string]struct {
			Bytes  int64  `json:"bytes"`
			SHA256 string `json:"sha256"`
		} `json:"entries"`
	}
	if err := json.Unmarshal(manifestRaw, &manifest); err != nil {
		t.Fatal(err)
	}
	if manifest.Schema != "v1-6-immutable-source5-test-context-v1" || manifest.BaselineCommit != "6a2332795dc5fa2db3eb61e196ab7ab820e76caa" || len(manifest.Entries) != 12 {
		t.Fatal("historical rail context provenance differs")
	}
	allowed := map[string]bool{
		"go-backend/internal/content/bundled.json":                               true,
		"go-backend/internal/content/digest.go":                                  true,
		"docs/CRITIQUE_RUBRIC.md":                                                true,
		"docs/reviews/v1-4-time-links-and-predicates/native/world/proposal.json": true,
	}
	for _, name := range contentbuild.SourceNames {
		allowed["cat_de_roman_esti/fixtures/"+name] = true
	}
	if len(allowed) != len(manifest.Entries) {
		t.Fatal("historical rail source inventory differs")
	}
	compressed := readHistoricalRailsFile(t, "docs/reviews/v1-6-everyday-inputs/reference/historical-source5-context.tar.gz", 4<<20, "ffffa21ccf11f79d817c529123f2583824c62fefaabd17a5887e7ce809507e48")
	z, err := gzip.NewReader(bytes.NewReader(compressed))
	if err != nil {
		t.Fatal(err)
	}
	rawTar, err := io.ReadAll(io.LimitReader(z, (32<<20)+1))
	closeErr := z.Close()
	if err != nil || closeErr != nil || len(rawTar) != 14376960 || len(rawTar) > 32<<20 {
		t.Fatal("historical rail archive decompression/bound differs", err, closeErr)
	}
	files := map[string][]byte{}
	reader := tar.NewReader(bytes.NewReader(rawTar))
	for {
		header, err := reader.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			t.Fatal(err)
		}
		want, known := manifest.Entries[header.Name]
		if !known || !allowed[header.Name] || files[header.Name] != nil || header.Typeflag != tar.TypeReg || header.Size != want.Bytes || header.Size < 1 || header.Size > 16<<20 {
			t.Fatalf("historical rail archive member refused: %s", header.Name)
		}
		raw, err := io.ReadAll(io.LimitReader(reader, want.Bytes+1))
		if err != nil || int64(len(raw)) != want.Bytes || digestBytes(raw) != want.SHA256 {
			t.Fatalf("historical rail member bytes differ: %s (%v)", header.Name, err)
		}
		files[header.Name] = raw
	}
	if len(files) != len(manifest.Entries) {
		t.Fatal("historical rail archive incomplete")
	}
	bundle := files["go-backend/internal/content/bundled.json"]
	data, err := content.Decode(bundle)
	if err != nil || digestBytes(bundle) != "c1fff429992c69926aafb07f5b015f890a82c7c01cc5230107bdaf481bca5993" || digestBytes(files["go-backend/internal/content/digest.go"]) != "35f33cfeb67f234ceeee6e2a6ec08dabc036a383e46bbd48bf6d8b4287061ea2" || len(data.Sources) != 8 {
		t.Fatal("historical Source5 bundle/pin identity differs", err)
	}
	for _, name := range contentbuild.SourceNames {
		if contentbuild.TextSHA256(files["cat_de_roman_esti/fixtures/"+name]) != data.Sources[name] {
			t.Fatalf("historical Source5 fixture binding differs: %s", name)
		}
	}
	sourcePath := "go-backend/internal/contentrails/sources/authored-v5.json"
	sourceBytes := readHistoricalRailsFile(t, sourcePath, 4<<20, "22b7853e3f93c8a0093066d17f36194bef94e5b1156cf83381671ef23b3cb585")
	source5, err := decodeSource(sourceBytes, "444e4bc1dc9a55fbfccd5840e33975b3b672d9ea2f51ece88044d873653d79b1", 5)
	if err != nil {
		t.Fatal(err)
	}
	files[sourcePath] = sourceBytes
	documents := map[string]string{
		"docs/reviews/v1-5-hot-chocolate/native/world/candidate.json":      "2a30f2acbaa217a8c6c5dbcaab16acab7513491fbd094066bb49325b0d3e3e04",
		"docs/reviews/v1-5-hot-chocolate/native/world/factual-review.json": "f8e3f12d8ae85f20f060fc50b8e70d920b747ea3c07926345f517c7bd0e96945",
		"docs/reviews/v1-5-hot-chocolate/native/world/quality-review.json": "f19205e9ef18803e3e7c81f1245cf858b16ef5df553e704532d470d271883e69",
	}
	for _, source := range []*Source{sourceForTest(t), source5} {
		for _, key := range []string{"world_previous", "world_candidate", "world_factual", "world_quality"} {
			entry := object(object(source.Raw["archives"])[key])
			name, expected := text(entry["path"]), text(entry["sha256"])
			if !strings.HasPrefix(name, "docs/reviews/") || filepath.IsAbs(name) || strings.Contains(name, "..") || !validDigest(expected) {
				t.Fatal("historical World archive descriptor refused")
			}
			if previous, exists := documents[name]; exists && previous != expected {
				t.Fatal("conflicting historical World archive identity")
			}
			documents[name] = expected
		}
	}
	for name, expected := range documents {
		files[name] = readHistoricalRailsFile(t, name, 4<<20, expected)
	}
	// This exact reviewed proposal is also the immutable Source5 World fixture.
	// Supply it independently of which proposal the current authority references.
	world := files["cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json"]
	if digestBytes(world) != "196e0b72310e6ec7b9b18254b4b95a307d9ae7a9ecb97f3670b66f24ff071086" {
		t.Fatal("historical Source5 proposal identity differs")
	}
	files["docs/reviews/v1-5-hot-chocolate/native/world/proposal.json"] = world
	for _, name := range []string{"kg_sample.json", "games_pack.json", "release_reserve_v1.json"} {
		files["tests/fixtures/"+name] = files["cat_de_roman_esti/fixtures/"+name]
	}
	root := t.TempDir()
	for relative, raw := range files {
		path := filepath.Join(root, filepath.FromSlash(relative))
		if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, raw, 0600); err != nil {
			t.Fatal(err)
		}
	}
	return root
}
