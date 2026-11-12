package contentbuild

import (
	"fmt"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

func quickSyntheticGraph(edges []content.Edge) *graph.Service {
	c := &content.Content{}
	for i := 0; i < 32; i++ {
		c.Nodes = append(c.Nodes, content.Node{ID: fmt.Sprintf("n%d", i), NodeType: "concept", LabelRO: fmt.Sprintf("Cuvânt%d", i), Salience: .9})
	}
	c.Edges = edges
	return graph.New(c)
}
func quickSyntheticRow(game, id, family string, start int) map[string]any {
	p := map[string]any{}
	if game == "intrusul" {
		p = map[string]any{"members": []any{fmt.Sprintf("n%d", start), fmt.Sprintf("n%d", start+1), fmt.Sprintf("n%d", start+2)}, "intruder": fmt.Sprintf("n%d", start+3), "group_label": "Predicat privat"}
	} else {
		pairs := []any{}
		for i := 0; i < 8; i += 2 {
			pairs = append(pairs, map[string]any{"members": []any{fmt.Sprintf("n%d", start+i), fmt.Sprintf("n%d", start+i+1)}, "group_label": fmt.Sprintf("Pereche privată %d", i)})
		}
		p["pairs"] = pairs
	}
	return map[string]any{"id": id, "game": game, "source_id": family, "category": "viata_de_roman", "difficulty": "normal", "payload": p, "sources": []any{"https://example.test/author"}, "rationale": "Synthetic API test only"}
}
func quickSyntheticTrio(start int) []content.Edge {
	e := []content.Edge{}
	for i := start; i < start+3; i++ {
		for j := i + 1; j < start+3; j++ {
			e = append(e, content.Edge{Src: fmt.Sprintf("n%d", i), Dst: fmt.Sprintf("n%d", j), Strength: .8})
		}
	}
	return e
}
func TestQuickNativeZeroStrengthEdgePresenceParity(t *testing.T) {
	r := quickSyntheticRow("intrusul", "iq92_test", "aq92_test", 0)
	for _, strength := range []float64{0, -.2, .1} {
		for _, reversed := range []bool{false, true} {
			t.Run(fmt.Sprintf("strength=%g/reverse=%t", strength, reversed), func(t *testing.T) {
				a, b := "n0", "n3"
				if reversed {
					a, b = b, a
				}
				edges := append(quickSyntheticTrio(0), content.Edge{Src: a, Dst: b, Strength: strength})
				if _, err := RateQuick(r, quickSyntheticGraph(edges)); err == nil || !strings.Contains(err.Error(), "intruder has inlier link") {
					t.Fatalf("real edge presence disappeared: %v", err)
				}
			})
		}
	}
	for _, e := range []content.Edge{{Src: "n0", Dst: "n3", Strength: 0, IsDistractor: true}, {Src: "n0", Dst: "n3", Strength: .9, IsDistractor: true}} {
		if _, err := RateQuick(r, quickSyntheticGraph(append(quickSyntheticTrio(0), e))); err != nil {
			t.Fatalf("distractor changed admission: %v", err)
		}
	}
	if _, err := RateQuick(r, quickSyntheticGraph(quickSyntheticTrio(0))); err != nil {
		t.Fatal(err)
	}
}
func TestQuickPendingNativeStockRuntimeTrioAndFamilyRefusals(t *testing.T) {
	r := quickSyntheticRow("intrusul", "iq92_test", "aq92_test", 0)
	g := quickSyntheticGraph(quickSyntheticTrio(0))
	rating, err := RateQuick(r, g)
	if err != nil {
		t.Fatal(err)
	}
	copyID := map[string]any{}
	for k, v := range r {
		copyID[k] = v
	}
	copyID["id"] = "iq92_another"
	if _, _, err = ValidateQuickRows([]any{r, copyID}, nil, g); err == nil || !strings.Contains(err.Error(), "runtime identity") {
		t.Fatalf("duplicate materialized ID passed: %v", err)
	}
	stock := map[string]any{}
	for k, v := range rating {
		stock[k] = v
	}
	stock["id"] = "vi_dead"
	if _, _, err = ValidateQuickRows([]any{r}, []any{stock}, g); err == nil || !strings.Contains(err.Error(), "visible board") {
		t.Fatalf("dead visible board passed: %v", err)
	}
	stock["payload"] = map[string]any{"members": []any{"n2", "n0", "n1"}, "intruder": "n9", "group_label": "Alt titlu"}
	if _, _, err = ValidateQuickRows([]any{r}, []any{stock}, g); err == nil || !strings.Contains(err.Error(), "trio") {
		t.Fatalf("reordered dead trio passed: %v", err)
	}
	var authored []any
	var edges []content.Edge
	for i := 0; i < 4; i++ {
		authored = append(authored, quickSyntheticRow("intrusul", fmt.Sprintf("iq92_%d", i), "aq92_family", 4*i))
		edges = append(edges, quickSyntheticTrio(4*i)...)
	}
	if _, _, err = ValidateQuickRows(authored, nil, quickSyntheticGraph(edges)); err == nil || !strings.Contains(err.Error(), "family cap") {
		t.Fatalf("family cap passed: %v", err)
	}
}
func TestQuickPendingPerechiCrossMatchingAndDeadEightTiles(t *testing.T) {
	r := quickSyntheticRow("perechi", "pq92_test", "aq92_test", 0)
	edges := []content.Edge{}
	for i := 0; i < 8; i += 2 {
		edges = append(edges, content.Edge{Src: fmt.Sprintf("n%d", i), Dst: fmt.Sprintf("n%d", i+1), Strength: .8})
	}
	g := quickSyntheticGraph(edges)
	if _, _, err := ValidateQuickRows([]any{r}, nil, g); err != nil {
		t.Fatal(err)
	}
	stock := map[string]any{"id": "vp_dead", "game": "perechi", "payload": map[string]any{"pairs": []any{
		map[string]any{"members": []any{"n0", "n2"}}, map[string]any{"members": []any{"n1", "n3"}}, map[string]any{"members": []any{"n4", "n6"}}, map[string]any{"members": []any{"n5", "n7"}},
	}}}
	if _, _, err := ValidateQuickRows([]any{r}, []any{stock}, g); err == nil || !strings.Contains(err.Error(), "visible board") {
		t.Fatalf("alternate historical matching evaded eight-tile debt: %v", err)
	}
	for _, s := range []float64{.60, .9} {
		if _, err := RateQuick(r, quickSyntheticGraph(append(append([]content.Edge{}, edges...), content.Edge{Src: "n0", Dst: "n2", Strength: s}))); err == nil {
			t.Fatal("strong cross-pair admitted")
		}
	}
}
func TestQuickPendingRowsKeepCurrent85And336Exact(t *testing.T) {
	quick, core := source(t, "quick_games_v92.json"), source(t, "derived_catalog_v38.json")
	if len(array(quick["authored"])) != 85 || len(array(core["boards"])) != 336 {
		t.Fatal("stock count changed without a separate content decision")
	}
	b, _ := Canonical(quick["authored"])
	if SHA256(b) != "f012308507213348b0d933815c57f7ffd06ea0100a8ee5548d02ee55a3e16b25" {
		t.Fatal("current authored payload/provenance changed")
	}
	b, _ = Canonical(core["boards"])
	if SHA256(b) != "065960184d8cedca74946357fc2ea912e75af46ae191b0b32b7c5105b714764b" {
		t.Fatal("frozen core payload/scores/ranks changed")
	}
	g, err := SourceGraph(sourcePath(repoRoot(t), "kg_sample.json"))
	if err != nil {
		t.Fatal(err)
	}
	rated, nodes, err := ValidateQuickRows(array(quick["authored"]), array(core["boards"]), g)
	if err != nil || !equal(rated, quick["boards"]) || !equal(nodes, quick["nodes"]) {
		t.Fatalf("native pending extraction changed baseline: %v", err)
	}
}
