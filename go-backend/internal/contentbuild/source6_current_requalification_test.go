package contentbuild

import (
	"bytes"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

// Current reviewed-source coverage is distinct from the immutable original
// Source6 test and from HTTP/image/device qualification.
// No historical pin override applies to this real current-root Build.
func TestRebuildCurrentSource6ReviewOnlyRequalification(t *testing.T) {
	root := repoRoot(t)
	wantPins := map[string]string{
		"derived_catalog_v38.json": "fdc94e5ded3477b44aaffe90858ca1070cd1c1d344be22724c0e02f0110bb96a",
		"quick_games_v92.json":     "234305a844033cff0914a5213f6c0b8dcd1b21918d57cc851780259c9e87ee59",
		"release_reserve_v1.json":  "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
	if !reflect.DeepEqual(reviewedPins, wantPins) {
		t.Fatal("current reviewed authority differs or historical pins leaked")
	}
	built, err := Build(root)
	if err != nil {
		t.Fatal(err)
	}
	installed, err := os.ReadFile(filepath.Join(root, "go-backend/internal/content/bundled.json"))
	if err != nil || !bytes.Equal(built, installed) || len(built) != 7272404 || SHA256(built) != "a220c22ec948e0738fa34d614fa033d715aee10a9ebf18369691f1dbe1166a4a" {
		t.Fatal("complete current reviewed rebuild/export identity differs", err)
	}
	pin, err := os.ReadFile(filepath.Join(root, "go-backend/internal/content/digest.go"))
	if err != nil || SHA256(pin) != "41295fbf205e586a4abb271cf77f0bb38ea35bd4109e965ffdbe8152fc602286" || !bytes.Equal(pin, PinBytes(built)) {
		t.Fatal("current reviewed digest declaration differs", err)
	}
	if !reflect.DeepEqual(reviewedPins, wantPins) {
		t.Fatal("current rebuild changed reviewed authority")
	}
	current, err := decodeObject(built)
	if err != nil {
		t.Fatal(err)
	}
	historicalRoot := source6HistoricalRoot(t)
	originalRaw, err := os.ReadFile(filepath.Join(historicalRoot, "go-backend/internal/content/bundled.json"))
	if err != nil || len(originalRaw) != 7272424 || SHA256(originalRaw) != "e0cfe93de076f14a782dc6377b2655d4ef10f86ada1560ae1202bb06dbfdf877" {
		t.Fatal("verified original Source6 comparison bytes differ", err)
	}
	original, err := decodeObject(originalRaw)
	if err != nil {
		t.Fatal(err)
	}
	wantSources := map[string]string{
		"alchimie_discovery_world_v92.json":   "572882a77dbdd8bac63ca69c64c6990a1601a49551693cf1b1b5fcb7a81861de",
		"alchimie_recipe_extensions_v92.json": "eeb7eede9009f09a7d9df012c7addb9f26b1b484040eb31c44ba2e6f7f35cee8",
		"board_rankings_v37.json":             "036c8a00de347939d132ba25512da7cba53b12e9d11a9f86cecc07cc98293c31",
		"derived_catalog_v38.json":            "fdc94e5ded3477b44aaffe90858ca1070cd1c1d344be22724c0e02f0110bb96a",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "63f0dcd7992f0d1434eab49b9c1b7e97f0db30a22cd708b7b25c0199f39031bf",
		"quick_games_v92.json":                "234305a844033cff0914a5213f6c0b8dcd1b21918d57cc851780259c9e87ee59",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
	// Input changes are review records only. Five other source files remain
	// byte-identical; the three changed files retain every other decoded value.
	reviewFields := map[string]string{
		"alchimie_discovery_world_v92.json":   "reviews",
		"alchimie_recipe_extensions_v92.json": "semantic_reviews",
		"quick_games_v92.json":                "reviews",
	}
	currentSources, currentOK := current["sources"].(map[string]any)
	originalSources, originalOK := original["sources"].(map[string]any)
	if !currentOK || !originalOK || len(currentSources) != 8 || len(originalSources) != 8 || len(SourceNames) != 8 {
		t.Fatal("complete eight-source inventories differ")
	}
	seen, changed := map[string]bool{}, 0
	for _, name := range SourceNames {
		want, known := wantSources[name]
		if !known || seen[name] {
			t.Fatalf("current source inventory has an unknown or repeated name: %s", name)
		}
		seen[name] = true
		raw, err := os.ReadFile(sourcePath(root, name))
		if err != nil || SHA256(raw) != want || currentSources[name] != want {
			t.Fatalf("current complete source/export binding differs: %s (%v)", name, err)
		}
		oldRaw, err := os.ReadFile(sourcePath(historicalRoot, name))
		if err != nil {
			t.Fatal(err)
		}
		field, reviewOnly := reviewFields[name]
		if (currentSources[name] != originalSources[name]) != reviewOnly {
			t.Fatalf("source digest delta is outside the exact three reviewed catalogs: %s", name)
		}
		if !reviewOnly {
			if !bytes.Equal(raw, oldRaw) {
				t.Fatalf("unreviewed source bytes changed: %s", name)
			}
			continue
		}
		changed++
		now, err := decodeObject(raw)
		if err != nil {
			t.Fatal(err)
		}
		old, err := decodeObject(oldRaw)
		if err != nil {
			t.Fatal(err)
		}
		nowReviews, nowHasReviews := now[field].([]any)
		oldReviews, oldHasReviews := old[field].([]any)
		if !nowHasReviews || !oldHasReviews || len(nowReviews) == 0 || len(oldReviews) == 0 || reflect.DeepEqual(nowReviews, oldReviews) {
			t.Fatalf("expected actual review-only input delta is absent: %s", name)
		}
		comparison := copyObject(now)
		comparison[field] = old[field]
		if !reflect.DeepEqual(comparison, old) {
			t.Fatalf("non-review source content/gameplay/provenance/history changed: %s", name)
		}
	}
	if len(seen) != 8 || changed != 3 {
		t.Fatal("exact current eight-source tuple or three review-only deltas differ")
	}

	// Restore precisely five leaves on copied ancestor maps, then compare the
	// ENTIRE decoded bundle. Both original decoded inputs remain untouched.
	// No manifest/content hash/metadata/root object exception is permitted.
	comparison := copyObject(current)
	for section, field := range map[string]string{"discovery_world": "reviews", "recipe_extensions": "semantic_reviews"} {
		now, nowOK := current[section].(map[string]any)
		old, oldOK := original[section].(map[string]any)
		if !nowOK || !oldOK {
			t.Fatalf("required whole bundle section differs: %s", section)
		}
		nowReviews, nowHasReviews := now[field].([]any)
		oldReviews, oldHasReviews := old[field].([]any)
		if !nowHasReviews || !oldHasReviews || len(nowReviews) == 0 || len(oldReviews) == 0 || reflect.DeepEqual(nowReviews, oldReviews) {
			t.Fatalf("expected actual bundle review delta is absent: %s.%s", section, field)
		}
		copy := copyObject(now)
		copy[field] = old[field]
		comparison[section] = copy
	}
	sources := copyObject(currentSources)
	for name := range reviewFields {
		sources[name] = originalSources[name]
	}
	comparison["sources"] = sources
	if !reflect.DeepEqual(comparison, original) {
		t.Fatal("complete current export differs outside the exact five review/source-digest leaves")
	}
}
