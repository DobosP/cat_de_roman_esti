package apppack

import (
	"encoding/json"
	"reflect"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/roeduclient"
)

func syntheticItem(kind, id string) roeduclient.Record {
	return roeduclient.Record{"id": id, "kind": kind, "label_ro": "Synthetic node", "tags": []any{"topic:synthetic", "category:istorie", "difficulty:easy", "source:synthetic"}, "facets": roeduclient.Record{"topic": "synthetic", "nested": []any{"kept"}}, "source": "synthetic-contract-fixture", "provenance": roeduclient.Record{"proc_key": "fixture"}, "license": "synthetic redistributable fixture", "access_type": "open_license", "legal_basis": "synthetic fixture; redistributable test data", "gdpr_relevant": false, "redistributable": true}
}
func pack(product string, items ...roeduclient.Record) roeduclient.Record {
	return roeduclient.Record{"pack_id": "roedu:" + App + ":" + product + ":v1", "app": App, "layer": Layer, "schema_version": 1, "items": items, "pagination": roeduclient.Record{"next_cursor": nil}, "withheld": 0, "errors": []any{}}
}
func decode(t *testing.T, v any) roeduclient.Bundle {
	t.Helper()
	raw, e := json.Marshal(v)
	if e != nil {
		t.Fatal(e)
	}
	bundle, e := DecodeBundle(raw)
	if e != nil {
		t.Fatal(e)
	}
	return bundle
}
func empty(t *testing.T, b roeduclient.Bundle) {
	t.Helper()
	if len(b.Nodes)+len(b.Edges)+len(b.Puzzles) != 0 {
		t.Fatal("unsupported/private input was admitted")
	}
	if b.Nodes == nil || b.Edges == nil || b.Puzzles == nil {
		t.Fatal("empty product arrays must be present")
	}
}

func TestTaggedSyntheticFixturePreservesSelectionMetadata(t *testing.T) {
	bundle, e := ReadFixture("../../../tests/fixtures/kg_app_pack_sample.json")
	if e != nil {
		t.Fatal(e)
	}
	if len(bundle.Nodes) != 2 || len(bundle.Edges) != 1 || len(bundle.Puzzles) != 1 {
		t.Fatal("tagged fixture product counts differ")
	}
	node := bundle.Nodes[0]
	if node["id"] != "n_dacia_pack" || node["source"] != "synthetic-contract-fixture" || node["redistributable"] != true {
		t.Fatal("node identity/provenance differs")
	}
	facets := object(node["facets"])
	if facets["topic"] != "daci" || facets["category"] != "istorie" || facets["difficulty"] != "easy" {
		t.Fatal("node selector facets lost")
	}
	tags, _ := list(node["tags"])
	if !reflect.DeepEqual(tags, []any{"topic:istorie", "category:istorie", "difficulty:easy", "source:synthetic"}) {
		t.Fatal("node tags changed")
	}
	if object(bundle.Edges[0]["facets"])["topic"] != "daci" || bundle.Edges[0]["redistributable"] != true {
		t.Fatal("edge selector metadata lost")
	}
	if object(bundle.Puzzles[0]["facets"])["topic"] != "daci" || !reflect.DeepEqual(bundle.Puzzles[0]["tags"], tags) {
		t.Fatal("puzzle selector metadata lost")
	}
	counts := object(bundle.Meta["counts"])
	if counts["nodes"] != 2 || counts["edges"] != 1 || counts["puzzles"] != 1 || bundle.Meta["source_format"] != "roedu_app_pack_v1" {
		t.Fatal("input bundle metadata missing")
	}
}
func TestExactPackIdentityAndItemKindIsolation(t *testing.T) {
	base := pack("kg_nodes", syntheticItem("kg_node", "n_1"))
	for _, name := range []string{"app", "layer", "schema_version", "pack_id"} {
		t.Run("missing-"+name, func(t *testing.T) {
			p := roeduclient.Record{}
			for k, v := range base {
				p[k] = v
			}
			delete(p, name)
			empty(t, decode(t, p))
		})
	}
	for _, change := range []struct {
		field string
		value any
	}{{"app", "social"}, {"app", "ro_teacher"}, {"app", App + " "}, {"layer", "internal"}, {"layer", "public"}, {"schema_version", 2}, {"schema_version", "1"}, {"schema_version", true}, {"pack_id", "roedu:" + App + ":other:v1"}, {"pack_id", "roedu:" + App + ":kg_nodes:internal:v1"}, {"pack_id", "roedu:" + App + ":kg_nodes:v2"}} {
		p := roeduclient.Record{}
		for k, v := range base {
			p[k] = v
		}
		p[change.field] = change.value
		empty(t, decode(t, p))
	}
	node := syntheticItem("kg_node", "n_wrong_pack")
	bundle := decode(t, roeduclient.Record{"packs": []roeduclient.Record{pack("kg_nodes", syntheticItem("kg_node", "n_valid")), pack("kg_edges", node, syntheticItem("kg_edge", "e_valid")), pack("kg_puzzles", syntheticItem("unknown", "bad"))}})
	if len(bundle.Nodes) != 1 || bundle.Nodes[0]["id"] != "n_valid" || len(bundle.Edges) != 1 || bundle.Edges[0]["id"] != "e_valid" || len(bundle.Puzzles) != 0 {
		t.Fatal("kind mismatched to pack migrated into another product")
	}
	for _, schema := range []any{json.Number("1"), json.Number("1.0"), json.Number("1e0")} {
		base["schema_version"] = schema
		if len(decode(t, base).Nodes) != 1 {
			t.Fatal("numeric schema one rejected")
		}
	}
}
func TestLegalPublicFilterFailsClosed(t *testing.T) {
	for _, access := range []string{"public_document", "open_license", "public_domain"} {
		item := syntheticItem("kg_node", "n_public")
		item["access_type"] = access
		if len(decode(t, pack("kg_nodes", item)).Nodes) != 1 {
			t.Fatal("public access type withheld")
		}
	}
	cases := []struct {
		field   string
		value   any
		missing bool
	}{{"redistributable", nil, true}, {"redistributable", false, false}, {"redistributable", 1, false}, {"redistributable", "true", false}, {"gdpr_relevant", nil, true}, {"gdpr_relevant", nil, false}, {"gdpr_relevant", true, false}, {"gdpr_relevant", 0, false}, {"gdpr_relevant", "false", false}, {"access_type", nil, true}, {"access_type", "tdm_exception", false}, {"access_type", "unknown", false}, {"access_type", "", false}, {"legal_basis", nil, true}, {"legal_basis", nil, false}, {"legal_basis", "", false}, {"legal_basis", "\t \u001c\u001f\u3000", false}, {"legal_basis", 17, false}}
	for _, test := range cases {
		item := syntheticItem("kg_node", "n_withheld")
		if test.missing {
			delete(item, test.field)
		} else {
			item[test.field] = test.value
		}
		empty(t, decode(t, pack("kg_nodes", item)))
	}
}
func TestUnsafeProvenanceStrippedWithoutCallerMutation(t *testing.T) {
	item := syntheticItem("kg_node", "n_safe")
	provenance := object(item["provenance"])
	for _, key := range []string{"source_url", "sha256", "internal_path", "llms_txt"} {
		provenance[key] = "synthetic-private-value"
	}
	input := pack("kg_nodes", item)
	before, e := json.Marshal(input)
	if e != nil {
		t.Fatal(e)
	}
	records, e := RecordsFromAppPacks(input)
	if e != nil {
		t.Fatal(e)
	}
	after, e := json.Marshal(input)
	if e != nil {
		t.Fatal(e)
	}
	if string(before) != string(after) {
		t.Fatal("public filtering mutated caller")
	}
	kept := records["kg_nodes"][0]
	safe := object(kept["provenance"])
	if len(safe) != 1 || safe["proc_key"] != "fixture" {
		t.Fatal("unsafe provenance keys retained or safe source metadata lost")
	}
	object(kept["facets"])["topic"] = "modified-output"
	object(kept["facets"])["nested"].([]any)[0] = "modified-output"
	kept["tags"].([]any)[0] = "modified-output"
	if object(item["facets"])["topic"] != "synthetic" || object(item["facets"])["nested"].([]any)[0] != "kept" || item["tags"].([]any)[0] != "topic:synthetic" {
		t.Fatal("returned public records retain mutable caller aliases")
	}
}
func TestMissingEmptyAndMixedUnsupportedPacks(t *testing.T) {
	for _, input := range []any{roeduclient.Record{}, roeduclient.Record{"packs": nil}, roeduclient.Record{"packs": []any{}}, roeduclient.Record{"packs": []any{nil, "unsupported", 17, []any{}}}, pack("kg_nodes"), roeduclient.Record{"packs": pack("kg_nodes")}} {
		empty(t, decode(t, input))
	}
	p := pack("kg_nodes", syntheticItem("kg_node", "n_nested_single"))
	if len(decode(t, roeduclient.Record{"packs": p}).Nodes) != 1 {
		t.Fatal("single nested pack envelope lost")
	}
}
func TestPrivateJSONUnicodeDuplicateAndRootRefusal(t *testing.T) {
	for _, raw := range []string{`{"app":"cat_de_roman_esti","app":"other"}`, `{"s":"\ud800"}`, `{"s":"\udfff"}`, `{"s":"\ud800\u0041"}`, `{} {}`, `[]`, strings.Repeat("[", 66) + "0" + strings.Repeat("]", 66), "{\"s\":\"\xff\"}"} {
		if _, e := DecodeBundle([]byte(raw)); e == nil {
			t.Fatal("ambiguous/malformed/non-object private input accepted")
		}
	}
	p := pack("kg_nodes", syntheticItem("kg_node", "n_unicode"))
	raw, e := json.Marshal(p)
	if e != nil {
		t.Fatal(e)
	}
	raw = []byte(strings.Replace(string(raw), "Synthetic node", `Șară \ud83d\ude00`, 1))
	bundle, e := DecodeBundle(raw)
	if e != nil || bundle.Nodes[0]["label_ro"] != "Șară 😀" {
		t.Fatal("valid paired Unicode rejected or changed")
	}
	raw = []byte(strings.Replace(string(raw), `Șară \ud83d\ude00`, `literal \\ud800`, 1))
	bundle, e = DecodeBundle(raw)
	if e != nil || bundle.Nodes[0]["label_ro"] != `literal \ud800` {
		t.Fatal("literal backslash-surrogate text changed")
	}
}
func TestBytePackAndRecordCapsRefuseWholeDecode(t *testing.T) {
	input := pack("kg_nodes", syntheticItem("kg_node", "n_1"), syntheticItem("kg_node", "n_2"))
	raw, e := json.Marshal(input)
	if e != nil {
		t.Fatal(e)
	}
	limits := DefaultLimits()
	limits.Bytes = int64(len(raw) - 1)
	if _, e = DecodeBundleWithLimits(raw, limits); e == nil {
		t.Fatal("byte cap bypassed")
	}
	limits = DefaultLimits()
	limits.Nodes = 1
	if _, e = DecodeBundleWithLimits(raw, limits); e == nil {
		t.Fatal("node cap silently truncated")
	}
	limits = DefaultLimits()
	limits.Packs = 1
	multi, _ := json.Marshal(roeduclient.Record{"packs": []roeduclient.Record{pack("kg_nodes"), pack("kg_edges")}})
	if _, e = DecodeBundleWithLimits(multi, limits); e == nil {
		t.Fatal("pack cap silently truncated")
	}
	limits = Limits{Bytes: MaxFileBytes, Packs: 1, Nodes: 1, Edges: 1, Puzzles: 1}
	withheld := syntheticItem("kg_node", "n_withheld")
	withheld["gdpr_relevant"] = true
	many, _ := json.Marshal(pack("kg_nodes", withheld, withheld, withheld, withheld))
	if _, e = DecodeBundleWithLimits(many, limits); e == nil {
		t.Fatal("withheld rows bypassed scanned cap")
	}
	if _, e = DecodeBundleWithLimits(raw, Limits{}); e == nil {
		t.Fatal("missing bounds accepted")
	}
	limits = DefaultLimits()
	limits.Bytes = 10
	if _, e = ReadFixtureWithLimits("../../../tests/fixtures/kg_app_pack_sample.json", limits); e == nil {
		t.Fatal("file stat byte cap ignored")
	}
}
