package mobilepack

import (
	"bytes"
	"encoding/json"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/hopcli"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/roeduclient"
	"os"
	"reflect"
	"testing"
)

func TestFrozenPublicContractMatchesIndependentFixture(t *testing.T) {
	b, err := hopcli.ReadFixture("../../../cat_de_roman_esti/fixtures/kg_sample.json")
	if err != nil {
		t.Fatal(err)
	}
	data, err := Bytes(b.Raw)
	if err != nil {
		t.Fatal(err)
	}
	expected, err := os.ReadFile("../../../tests/fixtures/cat_mobile_app_pack_contract.json")
	if err != nil {
		t.Fatal(err)
	}
	var a, bv any
	json.Unmarshal(data, &a)
	json.Unmarshal(expected, &bv)
	if !reflect.DeepEqual(a, bv) {
		t.Fatal("native public projection differs from independent mobile contract")
	}
	if bytes.Contains(data, []byte("solution_path")) || bytes.Contains(data, []byte("hint_neighbors")) {
		t.Fatal("private helper leak")
	}
}
func TestProjectionHashStableAndPrivateHelpersExcluded(t *testing.T) {
	raw := roeduclient.Bundle{Meta: roeduclient.Record{}, Nodes: []roeduclient.Record{{"id": "z", "label_ro": "Țară"}, {"id": "a", "label_ro": "Alb"}}, Edges: []roeduclient.Record{{"id": "e", "src_id": "z", "dst_id": "a"}}, Puzzles: []roeduclient.Record{{"id": "p", "start_id": "z", "target_id": "a", "difficulty": "easy", "solution_path": []string{"z", "SECRET", "a"}, "hint_neighbors": []string{"SECRET"}}}}
	a, _ := Build(raw)
	raw.Nodes[0], raw.Nodes[1] = raw.Nodes[1], raw.Nodes[0]
	raw.Edges[0]["src_id"], raw.Edges[0]["dst_id"] = "a", "z"
	b, _ := Build(raw)
	if !reflect.DeepEqual(a["manifest"], b["manifest"]) {
		t.Fatal("hash depended on order/direction")
	}
	data, _ := Bytes(raw)
	if bytes.Contains(data, []byte("SECRET")) {
		t.Fatal("hidden route leaked")
	}
	raw.Nodes[0]["label_ro"] = "Changed"
	c, _ := Build(raw)
	if reflect.DeepEqual(b["manifest"], c["manifest"]) {
		t.Fatal("hash ignored public content")
	}
}
