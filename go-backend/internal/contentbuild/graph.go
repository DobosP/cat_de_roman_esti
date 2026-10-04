package contentbuild

import (
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"sort"
	"strings"
)

func parsedGraph(raw map[string]any) (*content.Content, error) {
	r, err := frozenRules()
	if err != nil {
		return nil, err
	}
	c := &content.Content{Labels: map[string]string{}, NormalizedIndex: map[string]string{}, NormalizationMap: map[string]string{}, AccentNormalizationMap: map[string]string{}, CasefoldMap: map[string]string{}, CategoryLabels: map[string]string{}}
	for _, name := range []string{"normalization_map", "accent_normalization_map", "casefold_map", "category_labels"} {
		b, _ := Canonical(r[name])
		switch name {
		case "normalization_map":
			err = json.Unmarshal(b, &c.NormalizationMap)
		case "accent_normalization_map":
			err = json.Unmarshal(b, &c.AccentNormalizationMap)
		case "casefold_map":
			err = json.Unmarshal(b, &c.CasefoldMap)
		case "category_labels":
			err = json.Unmarshal(b, &c.CategoryLabels)
		}
		if err != nil {
			return nil, err
		}
	}
	for _, v := range array(raw["kg_nodes"]) {
		m := object(v)
		if m == nil {
			return nil, fmt.Errorf("node must be an object")
		}
		n := content.Node{ID: str(m["id"]), NodeType: str(m["node_type"]), LabelRO: str(m["label_ro"]), Category: str(m["category"]), Description: str(m["description"]), Salience: number(m["salience"]), DifficultyTier: str(m["difficulty_tier"]), Degree: int(number(m["degree"])), Aliases: stringsOf(m["aliases"]), Tags: stringsOf(m["tags"]), Facets: object(m["facets"]), Source: str(m["source"]), Redistributable: boolValue(m["redistributable"])}
		if n.Facets == nil {
			n.Facets = map[string]any{}
		}
		c.Nodes = append(c.Nodes, n)
		label := n.LabelRO
		keep := false
		for _, x := range stringsOf(r["lowercase_display_labels"]) {
			if x == label {
				keep = true
			}
		}
		if label != "" && !keep {
			chars := []rune(label)
			label = upper(string(chars[0]), r) + string(chars[1:])
		}
		c.Labels[n.ID] = label
		c.NormalizedIndex[Normalize(n.LabelRO)] = n.ID
		c.NormalizedIndex[Normalize(n.ID)] = n.ID
	}
	ns := append([]content.Node{}, c.Nodes...)
	sort.Slice(ns, func(i, j int) bool { return ns[i].ID < ns[j].ID })
	for _, n := range ns {
		for _, a := range n.Aliases {
			k := Normalize(a)
			if _, ok := c.NormalizedIndex[k]; !ok {
				c.NormalizedIndex[k] = n.ID
			}
		}
	}
	for _, v := range array(raw["kg_edges"]) {
		m := object(v)
		if m == nil {
			return nil, fmt.Errorf("edge must be an object")
		}
		e := content.Edge{ID: str(m["id"]), Src: str(m["src_id"]), Dst: str(m["dst_id"]), Relation: str(m["relation"]), LabelRO: str(m["label_ro"]), Strength: number(m["strength"]), IsDistractor: boolValue(m["is_distractor"]), Bidirectional: boolValue(m["bidirectional"]), Tags: stringsOf(m["tags"]), Facets: object(m["facets"]), Source: str(m["source"]), Redistributable: boolValue(m["redistributable"])}
		if e.Facets == nil {
			e.Facets = map[string]any{}
		}
		c.Edges = append(c.Edges, e)
	}
	return c, nil
}

// SourceGraph builds an independent native graph from a bounded source fixture.
func SourceGraph(path string) (*graph.Service, error) {
	raw, err := ReadObject(path, 16<<20)
	if err != nil {
		return nil, err
	}
	c, err := parsedGraph(raw)
	if err != nil {
		return nil, err
	}
	return graph.New(c), nil
}
func nodeMap(n content.Node) map[string]any {
	return map[string]any{"id": n.ID, "node_type": n.NodeType, "label_ro": n.LabelRO, "category": n.Category, "description": n.Description, "salience": n.Salience, "difficulty_tier": n.DifficultyTier, "degree": n.Degree, "aliases": n.Aliases, "tags": n.Tags, "facets": n.Facets, "source": n.Source, "redistributable": n.Redistributable}
}
func edgeMap(e content.Edge) map[string]any {
	return map[string]any{"id": e.ID, "src_id": e.Src, "dst_id": e.Dst, "relation": e.Relation, "label_ro": e.LabelRO, "strength": e.Strength, "is_distractor": e.IsDistractor, "bidirectional": e.Bidirectional, "tags": e.Tags, "facets": e.Facets, "source": e.Source, "redistributable": e.Redistributable}
}

// MinimumAlchimieActions certifies exact raw graph inventory actions under the
// original six-action/50,000-state contract, independently of served projections.
func MinimumAlchimieActions(g *graph.Service, seeds []string, target, category string) (int, bool) {
	seeds = append([]string{}, seeds...)
	sort.Strings(seeds)
	key := strings.Join(seeds, "\x00")
	seen := map[string]bool{key: true}
	frontier := [][]string{seeds}
	if contains(seeds, target) {
		return 0, true
	}
	for depth := 1; depth <= 6; depth++ {
		next := [][]string{}
		for _, owned := range frontier {
			for i, a := range owned {
				for _, b := range owned[i+1:] {
					fresh := []string{}
					for _, n := range g.CommonNeighbors(a, b, category) {
						if !contains(owned, n) {
							fresh = append(fresh, n)
						}
					}
					if len(fresh) == 0 {
						continue
					}
					if contains(fresh, target) {
						return depth, true
					}
					state := append(append([]string{}, owned...), fresh...)
					sort.Strings(state)
					k := strings.Join(state, "\x00")
					if !seen[k] {
						seen[k] = true
						if len(seen) > 50000 {
							return 0, false
						}
						next = append(next, state)
					}
				}
			}
		}
		if len(next) == 0 {
			return 0, false
		}
		sort.Slice(next, func(i, j int) bool { return strings.Join(next[i], "\x00") < strings.Join(next[j], "\x00") })
		frontier = next
	}
	return 0, false
}
func contains(ss []string, s string) bool {
	for _, v := range ss {
		if v == s {
			return true
		}
	}
	return false
}
