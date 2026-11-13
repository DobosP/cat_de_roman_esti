package main

import (
	"errors"
	"reflect"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contexto"
)

func validateBundle(bundle *content.Content) error {
	// Use the native fixture and pack size ceilings before constructing services.
	if !bundle.PackRanked || len(bundle.Nodes) == 0 || len(bundle.Nodes) > 10000 ||
		len(bundle.Edges) > 50000 || len(bundle.PackItems)+len(bundle.Boards) > 20000 {
		return errors.New("expected a bounded ranked serving bundle")
	}
	nodes := make(map[string]bool, len(bundle.Nodes))
	for _, node := range bundle.Nodes {
		if node.ID == "" || nodes[node.ID] || node.LabelRO == "" || bundle.Labels[node.ID] == "" {
			return errors.New("invalid bundle node identity or label")
		}
		nodes[node.ID] = true
	}
	if len(nodes) != len(bundle.Labels) {
		return errors.New("bundle node and label inventories differ")
	}
	edges := make(map[string]bool, len(bundle.Edges))
	for _, edge := range bundle.Edges {
		if edge.ID == "" || edges[edge.ID] || !nodes[edge.Src] || !nodes[edge.Dst] {
			return errors.New("invalid bundle edge identity or endpoint")
		}
		edges[edge.ID] = true
	}
	for _, id := range bundle.NormalizedIndex {
		if !nodes[id] {
			return errors.New("normalized index references an unknown node")
		}
	}
	return contexto.ValidateBoardReviewRules(bundle)
}

// additiveWord binds dry-run accounting to exactly one word and 4–8 links.
// The importer recomputes node degree after inserting incident edges.
func additiveWord(before, after *content.Content) (string, error) {
	if len(after.Nodes) != len(before.Nodes)+1 {
		return "", errors.New("expected exactly one additional KG concept")
	}
	for i, old := range before.Nodes {
		node := after.Nodes[i]
		old.Degree, node.Degree = 0, 0
		if !reflect.DeepEqual(old, node) {
			return "", errors.New("existing KG concept changed or moved")
		}
	}
	word := after.Nodes[len(before.Nodes)]
	if word.NodeType != "concept" {
		return "", errors.New("added KG node is not a word concept")
	}
	added := len(after.Edges) - len(before.Edges)
	if added < 4 || added > 8 {
		return "", errors.New("expected 4–8 added links and no removed links")
	}
	if !reflect.DeepEqual(before.Edges, after.Edges[:len(before.Edges)]) {
		return "", errors.New("existing KG link changed or moved")
	}
	for _, edge := range after.Edges[len(before.Edges):] {
		if edge.IsDistractor || (edge.Src == word.ID) == (edge.Dst == word.ID) {
			return "", errors.New("added link must join the new word to an existing concept")
		}
	}
	return word.ID, nil
}
