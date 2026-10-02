package graph

import (
	"encoding/json"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"os"
	"reflect"
	"testing"
)

func TestCanonicalPythonGraph(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	g := New(c)
	if g != New(c) {
		t.Fatal("graph not shared")
	}
	var v struct {
		Texts []struct {
			Text, Normalized, Resolved, Fuzzy string
			Unresolved                        bool
			Suggestions                       []string
		}
		Ratios  [][]any
		Targets []struct {
			ID                      string
			Neighbors, Predecessors []string
			FromOrder               []string `json:"from_order"`
			ToOrder                 []string `json:"to_order"`
			From, To                map[string]int
			Weighted                map[string]float64
		}
		Salience, SalienceAscending []string
	}
	data, err := os.ReadFile("testdata/python_graph.json")
	if err != nil {
		t.Fatal(err)
	}
	var raw map[string]json.RawMessage
	json.Unmarshal(data, &raw)
	json.Unmarshal(data, &v)
	json.Unmarshal(raw["salience_ascending"], &v.SalienceAscending)
	for _, row := range v.Texts {
		if got := g.Normalize(row.Text); got != row.Normalized {
			t.Fatalf("normalize %q got %q want %q", row.Text, got, row.Normalized)
		}
		if g.ReviewedUnresolved(row.Text) != row.Unresolved || g.Resolve(row.Text) != row.Resolved || g.ResolveFuzzy(row.Text) != row.Fuzzy || !reflect.DeepEqual(g.Suggest(row.Text, 3), row.Suggestions) {
			t.Fatalf("resolver %q differs: resolve %q fuzzy %q suggestions %v", row.Text, g.Resolve(row.Text), g.ResolveFuzzy(row.Text), g.Suggest(row.Text, 3))
		}
	}
	for _, row := range v.Ratios {
		if got := SequenceRatio(row[0].(string), row[1].(string)); got != row[2].(float64) {
			t.Fatalf("SequenceMatcher %q/%q: %.17g != %.17g", row[0], row[1], got, row[2])
		}
	}
	for _, row := range v.Targets {
		from, fromOrder := g.DistancesFromOrdered(row.ID)
		to, toOrder := g.DistancesToOrdered(row.ID)
		if !reflect.DeepEqual(from, row.From) || !reflect.DeepEqual(to, row.To) || !reflect.DeepEqual(g.WeightedDistancesTo(row.ID), row.Weighted) || !reflect.DeepEqual(g.NeighborIDs(row.ID), row.Neighbors) || !reflect.DeepEqual(g.PredecessorIDs(row.ID), row.Predecessors) {
			t.Fatalf("graph distances/neighbors differ for %s", row.ID)
		}
		if !reflect.DeepEqual(fromOrder, row.FromOrder) || !reflect.DeepEqual(toOrder, row.ToOrder) {
			t.Fatalf("BFS insertion order differs for %s", row.ID)
		}
	}
	if !reflect.DeepEqual(g.BySalience(.6, true), v.Salience) || !reflect.DeepEqual(g.BySalience(0, false), v.SalienceAscending) {
		t.Fatal("salience ordering differs")
	}
}
