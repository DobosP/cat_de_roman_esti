package contentbuild

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"testing"
)

// These are literal git 59a9a568 bytes, not regenerated current inputs. Source6
// needs only its eight sources, rubric, bundle and pin; the separate Source5
// context retains its own prior World proposal.
const source6ContextArchive = "docs/reviews/gui-source6-runtime-requalification/reference/historical-source6-context.tar.gz"
const source6ContextManifest = "docs/reviews/gui-source6-runtime-requalification/reference/historical-source6-context-manifest.json"
const source6ContextArchiveSHA256 = "42457e0b95db3df7ff1361663d0866b16a15686ffa45d298c0d897ff74d148a6"
const source6ContextManifestSHA256 = "85060d2de045d667cbae26a142d21223b9c3d3c506aa1dac8f55551b6bea156a"

func source6HistoricalRoot(t *testing.T) string {
	t.Helper()
	manifestRaw := readHistoricalContextFile(t, source6ContextManifest, 32<<10, source6ContextManifestSHA256)
	var manifest struct {
		Schema         string `json:"schema"`
		BaselineCommit string `json:"baseline_commit"`
		Entries        map[string]struct {
			Bytes   int64  `json:"bytes"`
			SHA256  string `json:"sha256"`
			GitMode string `json:"git_mode"`
		} `json:"entries"`
		Mirrors map[string]string `json:"materialized_mirrors"`
	}
	if err := json.Unmarshal(manifestRaw, &manifest); err != nil {
		t.Fatal(err)
	}
	if manifest.Schema != "gui-immutable-source6-test-context-v1" || manifest.BaselineCommit != "59a9a568c445654f69215d735091c9b3e0405831" || len(manifest.Entries) != 11 {
		t.Fatal("historical Source6 manifest provenance differs")
	}
	allowed := map[string]bool{
		"go-backend/internal/content/bundled.json": true,
		"go-backend/internal/content/digest.go":    true,
		"docs/CRITIQUE_RUBRIC.md":                  true,
	}
	for _, name := range SourceNames {
		allowed["cat_de_roman_esti/fixtures/"+name] = true
	}
	if len(allowed) != len(manifest.Entries) {
		t.Fatal("historical Source6 source inventory differs")
	}
	mirrors := map[string]string{
		"tests/fixtures/kg_sample.json":  "cat_de_roman_esti/fixtures/kg_sample.json",
		"tests/fixtures/games_pack.json": "cat_de_roman_esti/fixtures/games_pack.json",
	}
	if len(manifest.Mirrors) != len(mirrors) {
		t.Fatal("historical Source6 fixture mirror inventory differs")
	}
	for target, source := range mirrors {
		if manifest.Mirrors[target] != source {
			t.Fatalf("historical Source6 fixture mirror differs: %s", target)
		}
	}
	compressed := readHistoricalContextFile(t, source6ContextArchive, 4<<20, source6ContextArchiveSHA256)
	z, err := gzip.NewReader(bytes.NewReader(compressed))
	if err != nil {
		t.Fatal(err)
	}
	rawTar, err := io.ReadAll(io.LimitReader(z, (32<<20)+1))
	closeErr := z.Close()
	if err != nil || closeErr != nil || len(rawTar) > 32<<20 {
		t.Fatal("historical Source6 decompression or byte bound differs", err, closeErr)
	}
	files := make(map[string][]byte, len(manifest.Entries))
	archive := tar.NewReader(bytes.NewReader(rawTar))
	for {
		header, err := archive.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			t.Fatal(err)
		}
		want, known := manifest.Entries[header.Name]
		if !known || !allowed[header.Name] || files[header.Name] != nil || header.Typeflag != tar.TypeReg || header.Mode != 0644 || header.Linkname != "" || want.GitMode != "100644" || header.Size != want.Bytes || header.Size < 1 || header.Size > 16<<20 {
			t.Fatalf("historical Source6 archive member differs: %s", header.Name)
		}
		raw, err := io.ReadAll(io.LimitReader(archive, want.Bytes+1))
		if err != nil || int64(len(raw)) != want.Bytes || SHA256(raw) != want.SHA256 {
			t.Fatalf("historical Source6 member bytes differ: %s (%v)", header.Name, err)
		}
		files[header.Name] = raw
	}
	if len(files) != len(manifest.Entries) {
		t.Fatal("historical Source6 archive is incomplete")
	}
	bundle, err := decodeObject(files["go-backend/internal/content/bundled.json"])
	if err != nil {
		t.Fatal(err)
	}
	if SHA256(files["go-backend/internal/content/bundled.json"]) != "e0cfe93de076f14a782dc6377b2655d4ef10f86ada1560ae1202bb06dbfdf877" || SHA256(files["go-backend/internal/content/digest.go"]) != "c0bededc869ef4c719d55ab22b7c3fbf6fa973eb972b912860d8dddf92c34b4d" || len(object(bundle["sources"])) != 8 {
		t.Fatal("historical Source6 bundle/pin identity differs")
	}
	for _, name := range SourceNames {
		if TextSHA256(files["cat_de_roman_esti/fixtures/"+name]) != object(bundle["sources"])[name] {
			t.Fatalf("historical Source6 source binding differs: %s", name)
		}
	}
	root := t.TempDir()
	write := func(relative string, raw []byte) {
		path := filepath.Join(root, filepath.FromSlash(relative))
		if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, raw, 0600); err != nil {
			t.Fatal(err)
		}
	}
	for name, raw := range files {
		write(name, raw)
	}
	for target, source := range mirrors {
		write(target, files[source])
	}
	return root
}

// Setenv makes this historical scope nonparallel using testing's process-global
// guard. Only this test map changes: real Build still validates all eight pinned
// sources, and cleanup restores production authority even after Fatal. No
// background Build/Load goroutines overlap these nonparallel contentbuild tests.
func historicalSource6ReviewedPins(t *testing.T) {
	t.Helper()
	t.Setenv("CAT_CONTENTBUILD_HISTORICAL_TEST_CONTEXT", "source6")
	previous := reviewedPins
	t.Cleanup(func() { reviewedPins = previous })
	reviewedPins = map[string]string{
		"derived_catalog_v38.json": "fdc94e5ded3477b44aaffe90858ca1070cd1c1d344be22724c0e02f0110bb96a",
		"quick_games_v92.json":     "0c79b9c5cb0f9602c2506ef384ac64d519731dd9add53acf602d2c4f51a3f345",
		"release_reserve_v1.json":  "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func TestHistoricalSource6ReviewedPinsRestore(t *testing.T) {
	previous := reviewedPins
	previousContext, hadContext := os.LookupEnv("CAT_CONTENTBUILD_HISTORICAL_TEST_CONTEXT")
	t.Run("historical scope", func(t *testing.T) {
		historicalSource6ReviewedPins(t)
		if len(reviewedPins) != 3 || reviewedPins["derived_catalog_v38.json"] != "fdc94e5ded3477b44aaffe90858ca1070cd1c1d344be22724c0e02f0110bb96a" || reviewedPins["quick_games_v92.json"] != "0c79b9c5cb0f9602c2506ef384ac64d519731dd9add53acf602d2c4f51a3f345" || reviewedPins["release_reserve_v1.json"] != "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7" {
			t.Fatal("historical Source6 reviewed pin scope differs")
		}
	})
	if len(reviewedPins) != len(previous) {
		t.Fatal("reviewed pins were not restored after Source6 scope")
	}
	for name, digest := range previous {
		if reviewedPins[name] != digest {
			t.Fatalf("reviewed pin was not restored after Source6 scope: %s", name)
		}
	}
	if context, present := os.LookupEnv("CAT_CONTENTBUILD_HISTORICAL_TEST_CONTEXT"); context != previousContext || present != hadContext {
		t.Fatal("historical Source6 environment scope was not restored")
	}
}
