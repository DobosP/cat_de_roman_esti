package contentbuild

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

// Original Source6 coverage is separate from current-source qualification.
// This runs the real builder against immutable inputs and test-only reviewed pins.
func TestRebuildSource6TwoAliasReviewedBundleAndPin(t *testing.T) {
	root := source6HistoricalRoot(t)
	historicalSource6ReviewedPins(t)
	built, err := Build(root)
	if err != nil {
		t.Fatal(err)
	}
	installed, err := os.ReadFile(filepath.Join(root, "go-backend/internal/content/bundled.json"))
	if err != nil || !bytes.Equal(built, installed) || len(built) != 7272424 || SHA256(built) != "e0cfe93de076f14a782dc6377b2655d4ef10f86ada1560ae1202bb06dbfdf877" {
		t.Fatal("reviewed Source6 source rebuild or complete installed bundle differs", err)
	}
	pin, err := os.ReadFile(filepath.Join(root, "go-backend/internal/content/digest.go"))
	if err != nil || SHA256(pin) != "c0bededc869ef4c719d55ab22b7c3fbf6fa973eb972b912860d8dddf92c34b4d" || !bytes.Equal(pin, PinBytes(built)) {
		t.Fatal("reviewed Source6 digest declaration differs", err)
	}
	wantSources := map[string]string{
		"alchimie_discovery_world_v92.json":   "8f013a8f6b54a97a768a34c42e669addc4f5ab9823302befbe15ad811cae77ad",
		"alchimie_recipe_extensions_v92.json": "d94647e78f8c2bd375b961f0aab52f3f7207024e60bed745b78c4a3d052d0bfc",
		"board_rankings_v37.json":             "036c8a00de347939d132ba25512da7cba53b12e9d11a9f86cecc07cc98293c31",
		"derived_catalog_v38.json":            "fdc94e5ded3477b44aaffe90858ca1070cd1c1d344be22724c0e02f0110bb96a",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "63f0dcd7992f0d1434eab49b9c1b7e97f0db30a22cd708b7b25c0199f39031bf",
		"quick_games_v92.json":                "0c79b9c5cb0f9602c2506ef384ac64d519731dd9add53acf602d2c4f51a3f345",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
	m, err := decodeObject(built)
	if err != nil {
		t.Fatal(err)
	}
	if len(object(m["sources"])) != 8 || len(wantSources) != len(SourceNames) {
		t.Fatal("Source6 eight-source authority differs")
	}
	for _, name := range SourceNames {
		raw, err := os.ReadFile(sourcePath(root, name))
		if err != nil || TextSHA256(raw) != wantSources[name] || object(m["sources"])[name] != wantSources[name] {
			t.Fatalf("Source6 complete source identity differs: %s (%v)", name, err)
		}
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
