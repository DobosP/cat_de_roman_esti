package contentbuild

import (
	"bytes"
	"compress/gzip"
	"io"
	"os"
	"path/filepath"
	"testing"
)

// The live bundle test keeps only generator-backed equalities (ADR-0189): the
// real builder over the installed sources reproduces the installed bundle and
// pin, the bundle's source map equals the source files and the reviewed pins,
// and the installed authority pins equal the installed rail artifacts. No
// literal here duplicates generated state, so a reviewed content install that
// updates reviewedPins and the authorities keeps it green.
func TestRebuildInstalledBundleMatchesReviewedPins(t *testing.T) {
	root := repoRoot(t)
	built, err := Build(root)
	if err != nil {
		t.Fatal(err)
	}
	installed, err := os.ReadFile(filepath.Join(root, "go-backend/internal/content/bundled.json"))
	if err != nil || !bytes.Equal(built, installed) {
		t.Fatal("source rebuild differs from the installed bundle", err)
	}
	pin, err := os.ReadFile(filepath.Join(root, "go-backend/internal/content/digest.go"))
	if err != nil || !bytes.Equal(pin, PinBytes(built)) {
		t.Fatal("digest declaration differs from the installed bundle pin", err)
	}
	m, err := decodeObject(built)
	if err != nil {
		t.Fatal(err)
	}
	sources := object(m["sources"])
	if len(sources) != 8 || len(sources) != len(SourceNames) {
		t.Fatal("eight-source authority differs")
	}
	for _, name := range SourceNames {
		raw, err := os.ReadFile(sourcePath(root, name))
		if err != nil || TextSHA256(raw) != sources[name] {
			t.Fatalf("bundle source identity differs from the source file: %s (%v)", name, err)
		}
	}
	for name, digest := range reviewedPins {
		if sources[name] != digest {
			t.Fatalf("bundle source identity differs from the reviewed pin: %s", name)
		}
	}
	authorities, err := os.ReadFile(filepath.Join(root, "go-backend/internal/contentrails/sources/installed-authorities.json"))
	if err != nil {
		t.Fatal(err)
	}
	manifest, err := decodeObject(authorities)
	if err != nil {
		t.Fatal(err)
	}
	artifacts := map[string]string{"quick": "quick_games_v92.json", "world": "alchimie_discovery_world_v92.json", "extensions": "alchimie_recipe_extensions_v92.json"}
	rails := object(manifest["rails"])
	if len(rails) == 0 {
		t.Fatal("installed authorities register no rail")
	}
	for rail, entry := range rails {
		name := artifacts[rail]
		if name == "" {
			t.Fatalf("installed authority registers an unknown rail: %s", rail)
		}
		raw, err := os.ReadFile(sourcePath(root, name))
		if err != nil || SHA256(raw) != object(entry)["artifact_sha256"] {
			t.Fatalf("installed artifact differs from its authority pin: %s (%v)", rail, err)
		}
	}
}

// The V1.5 -> V1.6 two-alias delta is history: it is asserted over the archived
// Source6 bundle against the archived Source5 context, never over live bytes.
func TestHistoricalSource6TwoAliasDeltaOverArchivedSource5(t *testing.T) {
	compressed := readHistoricalContextFile(t, source6BundleArchive, 4<<20, source6BundleArchiveSHA256)
	z, err := gzip.NewReader(bytes.NewReader(compressed))
	if err != nil {
		t.Fatal(err)
	}
	raw, err := io.ReadAll(io.LimitReader(z, (16<<20)+1))
	closeErr := z.Close()
	if err != nil || closeErr != nil || len(raw) > 16<<20 {
		t.Fatal("historical Source6 bundle decompression or byte bound differs", err, closeErr)
	}
	if len(raw) != 7272424 || SHA256(raw) != "e0cfe93de076f14a782dc6377b2655d4ef10f86ada1560ae1202bb06dbfdf877" {
		t.Fatal("historical Source6 bundle identity differs")
	}
	m, err := decodeObject(raw)
	if err != nil {
		t.Fatal(err)
	}
	historicalRoot := source5HistoricalRoot(t)
	previousRaw, err := os.ReadFile(filepath.Join(historicalRoot, "go-backend/internal/content/bundled.json"))
	if err != nil {
		t.Fatal(err)
	}
	previous, err := decodeObject(previousRaw)
	if err != nil {
		t.Fatal(err)
	}
	if len(array(m["nodes"])) != 2419 || len(array(m["edges"])) != 9473 || len(array(m["pack_items"])) != 709 || len(array(m["boards"])) != 418 {
		t.Fatal("Source6 inventories differ")
	}
	if !equal(previous["edges"], m["edges"]) || !equal(previous["pack_items"], m["pack_items"]) || !equal(previous["boards"], m["boards"]) {
		t.Fatal("two-alias release changed shared edges or game boards")
	}
	additions := map[string]string{"n_v4ist_steag": "drapel", "n_v24_food_pantry_ulei": "untdelemn"}
	oldNodes, newNodes := array(previous["nodes"]), array(m["nodes"])
	if len(oldNodes) != len(newNodes) {
		t.Fatal("two-alias release changed node inventory")
	}
	changed := 0
	for i, value := range newNodes {
		node, old := object(value), object(oldNodes[i])
		if node["id"] != old["id"] {
			t.Fatal("two-alias release changed node order")
		}
		if added := additions[str(node["id"])]; added != "" {
			want := append(append([]any{}, array(old["aliases"])...), added)
			if !equal(node["aliases"], want) {
				t.Fatalf("exact reviewed alias append differs: %s", node["id"])
			}
			restored := clone(t, node)
			restored["aliases"] = old["aliases"]
			if !equal(restored, old) {
				t.Fatalf("other alias-owner fields changed: %s", node["id"])
			}
			changed++
		} else if !equal(node, old) {
			t.Fatalf("unrelated node changed: %s", node["id"])
		}
	}
	if changed != 2 || object(m["normalized_index"])["drapel"] != "n_v4ist_steag" || object(m["normalized_index"])["untdelemn"] != "n_v24_food_pantry_ulei" {
		t.Fatal("the exact two reviewed typed inputs are missing")
	}
	world, oldWorld := object(m["discovery_world"]), object(previous["discovery_world"])
	if len(array(world["concepts"])) != 252 || len(array(world["recipes"])) != 352 || len(array(world["compatible_versions"])) != 10 {
		t.Fatal("Source6 world inventories/history differ")
	}
	for _, field := range []string{"recipes", "compatible_versions", "world", "goals", "unlocks"} {
		if !equal(world[field], oldWorld[field]) {
			t.Fatalf("two-alias release changed world mechanics/history: %s", field)
		}
	}
}
