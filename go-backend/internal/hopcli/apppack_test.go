package hopcli

import (
	"slices"
	"testing"
)

func TestTaggedAppPackInputPreservesPublicSelectionMetadata(t *testing.T) {
	b, err := ReadFixture("../../../tests/fixtures/kg_app_pack_sample.json")
	if err != nil {
		t.Fatal(err)
	}
	if len(b.Raw.Nodes) != 2 || len(b.Raw.Edges) != 1 || len(b.Puzzles) != 1 {
		t.Fatal("public app-pack counts differ")
	}
	n := b.Graph.Node("n_dacia_pack")
	if n == nil || !slices.Contains(n.Tags, "topic:istorie") || n.Facets["topic"] != "daci" || n.Facets["category"] != "istorie" || n.Facets["difficulty"] != "easy" || n.Source != "synthetic-contract-fixture" || !n.Redistributable {
		t.Fatal("node selection/provenance metadata lost", n)
	}
	e := b.Graph.Link("n_dacia_pack", "n_traian_pack")
	if e == nil || !slices.Contains(e.Tags, "source:synthetic") || e.Facets["topic"] != "daci" || !e.Redistributable {
		t.Fatal("edge metadata lost", e)
	}
	p := b.Puzzles[0]
	if !slices.Equal(p.Tags, []string{"topic:istorie", "category:istorie", "difficulty:easy", "source:synthetic"}) || p.Facets["topic"] != "daci" || !p.Redistributable {
		t.Fatal("puzzle metadata lost", p)
	}
	g, err := New(b.Graph, p, "easy")
	if err != nil {
		t.Fatal(err)
	}
	if !g.Hop(p.TargetID).OK || !g.Won() || g.Score() != 1000 {
		t.Fatal("public fixture cannot play", g.Summary())
	}
}
