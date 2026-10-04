package contentbuild

import (
	"bytes"
	"encoding/json"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"math"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
)

func repoRoot(t *testing.T) string {
	t.Helper()
	p, e := filepath.Abs("../../..")
	if e != nil {
		t.Fatal(e)
	}
	return p
}
func source(t *testing.T, name string) map[string]any {
	t.Helper()
	m, e := ReadObject(sourcePath(repoRoot(t), name), 16<<20)
	if e != nil {
		t.Fatal(e)
	}
	return m
}
func clone(t *testing.T, m map[string]any) map[string]any {
	t.Helper()
	b, e := Canonical(m)
	if e != nil {
		t.Fatal(e)
	}
	r, e := decodeObject(b)
	if e != nil {
		t.Fatal(e)
	}
	return r
}
func TestRebuildFrozenBundleAndPin(t *testing.T) {
	root := repoRoot(t)
	b, e := Build(root)
	if e != nil {
		t.Fatal(e)
	}
	old, e := os.ReadFile(filepath.Join(root, "go-backend/internal/content/bundled.json"))
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(b, old) {
		t.Fatalf("native source rebuild differs: %s vs %s", SHA256(b), SHA256(old))
	}
	if SHA256(b) != "f2f8a629f3366a8da6984f608d01dd2ef2354f6de857f0db8b1268047fb6de88" {
		t.Fatal("independently frozen release digest drift")
	}
	pin, e := os.ReadFile(filepath.Join(root, "go-backend/internal/content/digest.go"))
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(pin, PinBytes(b)) {
		t.Fatal("digest pin differs")
	}
	m, e := decodeObject(b)
	if e != nil {
		t.Fatal(e)
	}
	if len(array(m["nodes"])) != 2416 || len(array(m["edges"])) != 9458 || len(array(m["pack_items"])) != 709 || len(array(m["boards"])) != 418 {
		t.Fatal("frozen source inventories differ")
	}
	world := object(m["discovery_world"])
	if len(array(world["concepts"])) != 251 || len(array(world["recipes"])) != 351 || len(array(world["compatible_versions"])) != 9 {
		t.Fatal("world inventory/history differs")
	}
	if len(object(m["sources"])) != 8 {
		t.Fatal("missing source authority")
	}
	for _, name := range SourceNames {
		raw, e := os.ReadFile(sourcePath(root, name))
		if e != nil {
			t.Fatal(e)
		}
		if object(m["sources"])[name] != TextSHA256(raw) {
			t.Fatalf("source digest differs: %s", name)
		}
	}
}
func TestPinnedUnicodeAndCanonicalEncoding(t *testing.T) {
	tests := map[string]string{"ȘTEFAN\u00a0ﬃ ß İ\u0301": "stefan ffi ss i", "  Ţară\t\n": "tara", "\U00001c89\U00001c8a": "\U00001c89\U00001c8a", "A\u034f": "a\u034f"}
	for input, want := range tests {
		if got := Normalize(input); got != want {
			t.Fatalf("%q => %q want %q", input, got, want)
		}
	}
	r, e := frozenRules()
	if e != nil {
		t.Fatal(e)
	}
	if letter('\U00001c89', r) {
		t.Fatal("Unicode16 letter leaked into pinned Unicode15 tables")
	}
	if upper("ß", r) != "SS" || labelPattern("șase-sate noi", r) != "Ș___-____ N__" {
		t.Fatal("pinned uppercase/letter pattern drift")
	}
	values := []struct {
		v any
		s string
	}{{float64(1e6), "1000000.0"}, {float64(1e-5), "1e-05"}, {float64(1e16), "1e+16"}, {json.Number("0.800"), "0.8"}, {map[string]any{"ț": "<Ș>&\u2028", "a": "\x00"}, "{\"a\":\"\\u0000\",\"ț\":\"<Ș>&\u2028\"}"}}
	for _, v := range values {
		b, e := Canonical(v.v)
		if e != nil || string(b) != v.s {
			t.Fatalf("canonical %v => %s (%v), want %s", v.v, b, e, v.s)
		}
	}
	if _, e := Canonical(math.Inf(1)); e == nil {
		t.Fatal("non-finite number accepted")
	}
}
func TestFixtureMutationsRejected(t *testing.T) {
	raw := source(t, "kg_sample.json")
	cases := []struct {
		name, class string
		mutate      func(map[string]any)
	}{
		{"shape", "field_shapes", func(m map[string]any) { object(array(m["kg_nodes"])[0])["unexpected"] = true }},
		{"duplicate", "unique_ids", func(m map[string]any) { object(array(m["kg_nodes"])[1])["id"] = object(array(m["kg_nodes"])[0])["id"] }},
		{"tier", "node_tier_bands", func(m map[string]any) { object(array(m["kg_nodes"])[0])["difficulty_tier"] = "hard" }},
		{"own alias", "alias_unique", func(m map[string]any) { n := object(array(m["kg_nodes"])[0]); n["aliases"] = []any{n["label_ro"]} }},
		{"long alias", "label_style", func(m map[string]any) {
			object(array(m["kg_nodes"])[0])["aliases"] = []any{"unu doi trei patru cinci șase"}
		}},
		{"counts", "meta_counts", func(m map[string]any) { object(object(m["meta"])["counts"])["nodes"] = 0 }},
		{"endpoint", "puzzle_ids_resolve", func(m map[string]any) { object(array(m["kg_edges"])[0])["dst_id"] = "missing" }},
		{"par", "puzzle_par", func(m map[string]any) { object(array(m["kg_puzzles"])[0])["par"] = 99 }},
		{"hints", "puzzle_hints", func(m map[string]any) { object(array(m["kg_puzzles"])[0])["hint_neighbors"] = []any{} }},
		{"scope", "puzzle_category_scope", func(m map[string]any) { object(array(m["kg_puzzles"])[0])["category"] = "unknown" }},
		{"distractor", "puzzle_distractor_shortcut", func(m map[string]any) {
			p := object(array(m["kg_puzzles"])[0])
			e := copyObject(object(array(m["kg_edges"])[0]))
			e["id"] = "synthetic_shortcut"
			e["src_id"] = p["start_id"]
			e["dst_id"] = p["target_id"]
			e["bidirectional"] = false
			e["is_distractor"] = true
			m["kg_edges"] = append(array(m["kg_edges"]), e)
		}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			m := clone(t, raw)
			tc.mutate(m)
			errors := validateFixture(m)
			found := false
			for _, e := range errors {
				found = found || strings.HasPrefix(e, tc.class+":")
			}
			if !found {
				t.Fatalf("mutation not rejected by %s: %v", tc.class, errors)
			}
		})
	}
}
func TestPackEnvelopeAndGameplayMutations(t *testing.T) {
	kg := source(t, "kg_sample.json")
	c, e := parsedGraph(kg)
	if e != nil {
		t.Fatal(e)
	}
	g := graph.New(c)
	pack := source(t, "games_pack.json")
	for _, game := range Games {
		t.Run(game, func(t *testing.T) {
			var rec map[string]any
			for _, v := range array(pack[game]) {
				if object(v)["status"] == "approved" {
					rec = clone(t, object(v))
					break
				}
			}
			if errors := ValidateEnvelope(game, rec); len(errors) != 0 {
				t.Fatal(errors)
			}
			if errors := ValidatePayload(g, game, rec); len(errors) != 0 {
				t.Fatal(errors)
			}
			switch game {
			case "conexiuni":
				groups := object(rec["groups"])
				for k := range groups {
					array(groups[k])[0] = "missing"
					break
				}
			case "contexto":
				rec["target"] = "missing"
			case "lant":
				rec["optimal"] = 99
			case "alchimie":
				rec["target_depth"] = 99
			}
			if errors := ValidatePayload(g, game, rec); len(errors) == 0 {
				t.Fatal("mutated gameplay accepted")
			}
			rec["status"] = "unknown"
			if errors := ValidateEnvelope(game, rec); len(errors) == 0 {
				t.Fatal("invalid envelope accepted")
			}
		})
	}
	bad := clone(t, pack)
	object(object(bad["meta"])["id_high_water"])["lant"] = 0
	if errors := validatePack(bad, g); len(errors) == 0 {
		t.Fatal("high-water regression accepted")
	}
}
func syntheticGraph(t *testing.T, ids []string, pairs [][2]string) *graph.Service {
	t.Helper()
	nodes, edges := []any{}, []any{}
	for _, id := range ids {
		nodes = append(nodes, map[string]any{"id": id, "label_ro": id, "category": "societate", "node_type": "concept", "salience": json.Number("0.8")})
	}
	for i, p := range pairs {
		edges = append(edges, map[string]any{"id": "e" + strconv.Itoa(i), "src_id": p[0], "dst_id": p[1], "strength": json.Number("0.8"), "bidirectional": false, "is_distractor": false})
	}
	c, e := parsedGraph(map[string]any{"kg_nodes": nodes, "kg_edges": edges})
	if e != nil {
		t.Fatal(e)
	}
	return graph.New(c)
}
func TestDirectedContextoAndSequentialAlchimie(t *testing.T) {
	ids := []string{"target"}
	pairs := [][2]string{}
	for i := 0; i < 120; i++ {
		id := "n" + strconv.Itoa(i)
		ids = append(ids, id)
		pairs = append(pairs, [2]string{id, "target"})
	}
	g := syntheticGraph(t, ids, pairs)
	if errors := ValidatePayload(g, "contexto", map[string]any{"target": "target"}); len(errors) != 0 {
		t.Fatal(errors)
	}
	for i, p := range pairs {
		pairs[i] = [2]string{p[1], p[0]}
	}
	g = syntheticGraph(t, ids, pairs)
	if errors := ValidatePayload(g, "contexto", map[string]any{"target": "target"}); len(errors) == 0 {
		t.Fatal("outbound distance substituted for guess-to-target distance")
	}
	ids = []string{"a", "b", "c", "d", "e", "x", "y", "target"}
	pairs = [][2]string{{"a", "x"}, {"b", "x"}, {"c", "y"}, {"d", "y"}, {"x", "target"}, {"y", "target"}}
	g = syntheticGraph(t, ids, pairs)
	seeds := []string{"a", "b", "c", "d", "e"}
	if depth, ok := MinimumAlchimieActions(g, seeds, "target", "societate"); !ok || depth != 3 {
		t.Fatalf("sequential action par = %d %v", depth, ok)
	}
	rec := map[string]any{"seeds": []any{"a", "b", "c", "d", "e"}, "target": "target", "category": "societate", "target_depth": json.Number("2")}
	if errors := ValidatePayload(g, "alchimie", rec); len(errors) == 0 {
		t.Fatal("parallel closure depth accepted as action par")
	}
	rec["target_depth"] = json.Number("3")
	if errors := ValidatePayload(g, "alchimie", rec); len(errors) != 0 {
		t.Fatal(errors)
	}
}
func TestEverySourceAuthorityRejectsMutations(t *testing.T) {
	root := repoRoot(t)
	src := map[string]map[string]any{}
	ds := map[string]any{}
	for _, name := range SourceNames {
		src[name] = source(t, name)
		b, e := os.ReadFile(sourcePath(root, name))
		if e != nil {
			t.Fatal(e)
		}
		ds[name] = TextSHA256(b)
	}
	c, e := parsedGraph(src["kg_sample.json"])
	if e != nil {
		t.Fatal(e)
	}
	g := graph.New(c)
	r, e := frozenRules()
	if e != nil {
		t.Fatal(e)
	}
	t.Run("ranking source binding", func(t *testing.T) {
		m := clone(t, src["board_rankings_v37.json"])
		object(m["meta"])["pack_sha256"] = strings.Repeat("0", 64)
		if _, e := validateRankings(m, src["games_pack.json"], ds); e == nil {
			t.Fatal("stale ranking source accepted")
		}
	})
	t.Run("ranking formula", func(t *testing.T) {
		m := clone(t, src["board_rankings_v37.json"])
		object(array(m["boards"])[0])["pilot_score"] = 0
		if _, e := validateRankings(m, src["games_pack.json"], ds); e == nil {
			t.Fatal("tampered ranking accepted")
		}
	})
	t.Run("derived identity", func(t *testing.T) {
		m := clone(t, src["derived_catalog_v38.json"])
		object(array(m["boards"])[0])["id"] = "vi_wrong"
		if e := validateDerived(m, src["games_pack.json"], ds, r); e == nil {
			t.Fatal("tampered derived identity accepted")
		}
	})
	t.Run("quick reviews", func(t *testing.T) {
		m := clone(t, src["quick_games_v92.json"])
		object(array(m["reviews"])[1])["reviewer"] = object(array(m["reviews"])[0])["reviewer"]
		if e := validateQuick(m, src["derived_catalog_v38.json"], g, ds); e == nil {
			t.Fatal("same reviewer accepted")
		}
	})
	t.Run("quick formula", func(t *testing.T) {
		m := clone(t, src["quick_games_v92.json"])
		object(array(m["boards"])[0])["standard_score"] = 0
		if e := validateQuick(m, src["derived_catalog_v38.json"], g, ds); e == nil {
			t.Fatal("authored score override accepted")
		}
	})
	t.Run("reserve record", func(t *testing.T) {
		m := clone(t, src["release_reserve_v1.json"])
		object(array(m["pack"])[0])["record_sha256"] = strings.Repeat("0", 64)
		if _, e := validateReserve(m, src["games_pack.json"]); e == nil {
			t.Fatal("reserved archived record edit accepted")
		}
	})
	t.Run("world provenance", func(t *testing.T) {
		m := clone(t, src["alchimie_discovery_world_v92.json"])
		object(array(m["concepts"])[0])["source"] = "foreign"
		if _, e := validateWorld(m, g); e == nil {
			t.Fatal("world source provenance drift accepted")
		}
	})
	t.Run("world archived fingerprint", func(t *testing.T) {
		m := clone(t, src["alchimie_discovery_world_v92.json"])
		object(array(m["compatible_versions"])[0])["recipe_hash"] = strings.Repeat("0", 64)
		if _, e := validateWorld(m, g); e == nil {
			t.Fatal("changed saved-progress archive accepted")
		}
	})
	t.Run("world historical recipe", func(t *testing.T) {
		m := clone(t, src["alchimie_discovery_world_v92.json"])
		old := object(array(m["compatible_versions"])[0])
		mech := object(old["mechanics"])
		object(array(mech["recipes"])[0])["result"] = "missing"
		old["recipe_hash"] = asciiDigest(mech)
		if _, e := validateWorld(m, g); e == nil {
			t.Fatal("rehash of changed historical recipe accepted")
		}
	})
	t.Run("extensions entry", func(t *testing.T) {
		m := clone(t, src["alchimie_recipe_extensions_v92.json"])
		board := object(array(m["boards"])[0])
		object(array(board["additions"])[0])["result"] = "missing"
		if e := ValidateRecipeExtensions(m); e == nil {
			t.Fatal("changed addition accepted")
		}
	})
	t.Run("extensions pair overwrite after rehash", func(t *testing.T) {
		m := clone(t, src["alchimie_recipe_extensions_v92.json"])
		board := object(array(m["boards"])[0])
		object(array(board["additions"])[0])["pair"] = object(array(object(board["core"])["recipes"])[0])["pair"]
		entry := copyObject(board)
		delete(entry, "entry_sha256")
		board["entry_sha256"] = valueDigest(entry)
		if e := ValidateRecipeExtensions(m); e == nil {
			t.Fatal("self-consistent overwrite of protected core recipe accepted")
		}
	})
}

func TestMissingRequiredRubricFailsClosed(t *testing.T) {
	if err := verifyRubric(filepath.Join(repoRoot(t), "missing-native-source-root")); err == nil || !strings.Contains(err.Error(), "required reviewed rubric") {
		t.Fatalf("missing required rubric accepted: %v", err)
	}
}
func TestMalformedSourceEncodingAndNumbers(t *testing.T) {
	if _, err := decodeObject([]byte("{\"bad\":\"\xff\"}")); err == nil {
		t.Fatal("invalid UTF-8 silently replaced")
	}
	if _, err := Canonical(json.Number("01")); err == nil {
		t.Fatal("invalid numeric lexeme accepted")
	}
	m := source(t, "alchimie_discovery_world_v92.json")
	m["schema_version"] = json.Number("1.0")
	if err := strictWorldRecords(m); err == nil {
		t.Fatal("floating schema version accepted")
	}
	m = source(t, "alchimie_discovery_world_v92.json")
	m["compatible_versions"] = nil
	if err := strictWorldRecords(m); err == nil {
		t.Fatal("null archive list accepted")
	}
}

func TestProvenanceURLPortContract(t *testing.T) {
	for _, tc := range []struct {
		url   string
		valid bool
	}{{"https://example.test/reference", true}, {"http://example.test:1/path", true}, {"http://example.test:0001/path", true}, {"http://example.test:65535/path", true}, {"http://[::1]:65535/path", true}, {"http://example.test:/path", true}, {"http://example.test:0/path", false}, {"http://example.test:0000/path", false}, {"http://example.test:65536/path", false}, {"http://[::1]:65536/path", false}, {"http://example.test:99999999999999999999999999999/path", false}, {"http://example.test:wrong/path", false}, {"http://example.test/reference\u202f", false}, {"https://user:password@example.test/path", false}, {"file:///reference", false}} {
		if got := ValidReference(tc.url); got != tc.valid {
			t.Fatalf("provenance URL %q = %v want %v", tc.url, got, tc.valid)
		}
	}
}

func TestPrivateSourceUnicodeScalarAndDuplicateRefusal(t *testing.T) {
	for _, raw := range []string{`{"x":"\ud800"}`, `{"x":"\udc00"}`, `{"x":"\ud800\u0041"}`, `{"x":1,"\u0078":2}`} {
		if _, err := DecodeObject([]byte(raw)); err == nil {
			t.Fatalf("private source silently repaired or shadowed %s", raw)
		}
	}
	for raw, want := range map[string]string{`{"x":"\ud83d\ude00"}`: "😀", `{"x":"\\ud800"}`: `\ud800`} {
		got, err := DecodeObject([]byte(raw))
		if err != nil || got["x"] != want {
			t.Fatalf("valid source %s fails: %v", raw, err)
		}
	}
}
func TestFixtureNonnumericSalienceRefusal(t *testing.T) {
	base := source(t, "kg_sample.json")
	for _, value := range []any{"0.8", true, []any{json.Number("0.8")}, json.Number("1e999")} {
		raw := clone(t, base)
		node := object(array(raw["kg_nodes"])[0])
		node["salience"] = value
		node["difficulty_tier"] = "hard"
		errors := validateFixture(raw)
		found := false
		for _, err := range errors {
			found = found || strings.HasPrefix(err, "field_shapes:") && strings.Contains(err, "salience")
		}
		if !found {
			t.Fatalf("invalid salience %v accepted: %v", value, errors)
		}
	}
}
