package roeduclient

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"strings"
)

type Bundle struct {
	Meta    Record   `json:"meta"`
	Nodes   []Record `json:"kg_nodes"`
	Edges   []Record `json:"kg_edges"`
	Puzzles []Record `json:"kg_puzzles"`
}

// Load uses the legacy category/mixed union rule and refuses partial/legal-unknown
// imports. Page identities survive in meta rather than disappearing on export.
func (c *Client) Load(ctx context.Context, category, difficulty string) (Bundle, error) {
	filters := url.Values{}
	if category != "" {
		filters.Set("category", category)
	}
	if difficulty != "" {
		filters.Set("difficulty", difficulty)
	}
	puzzles, err := c.Fetch(ctx, "kg_puzzles", filters, 5000)
	if err != nil {
		return Bundle{}, err
	}
	if category != "" && category != "mixed" {
		mixed := url.Values{"category": {"mixed"}}
		if difficulty != "" {
			mixed.Set("difficulty", difficulty)
		}
		rest, err := c.Fetch(ctx, "kg_puzzles", mixed, 5000)
		if err != nil {
			return Bundle{}, err
		}
		seen := map[string]bool{}
		for _, r := range puzzles.Records {
			seen[r["id"].(string)] = true
		}
		for _, r := range rest.Records {
			if !seen[r["id"].(string)] {
				puzzles.Records = append(puzzles.Records, r)
			}
		}
		puzzles.Pages = append(puzzles.Pages, rest.Pages...)
		if len(puzzles.Records) > 5000 {
			return Bundle{}, errors.New("RO-EDU union puzzle cap exceeded")
		}
	}
	nf := url.Values{}
	if category != "" {
		nf.Set("category", category)
	}
	nodes, err := c.Fetch(ctx, "kg_nodes", nf, 10000)
	if err != nil {
		return Bundle{}, err
	}
	loaded := map[string]bool{}
	for _, r := range nodes.Records {
		loaded[r["id"].(string)] = true
	}
	missing := false
	for _, p := range puzzles.Records {
		for _, k := range []string{"start_id", "target_id"} {
			id, _ := p[k].(string)
			missing = missing || !loaded[id]
		}
		for _, k := range []string{"solution_path", "hint_neighbors"} {
			for _, v := range IDList(p[k]) {
				missing = missing || !loaded[v]
			}
		}
	}
	if category != "" && missing {
		nodes, err = c.Fetch(ctx, "kg_nodes", nil, 10000)
		if err != nil {
			return Bundle{}, err
		}
	}
	edges, err := c.Fetch(ctx, "kg_edges", nil, 50000)
	if err != nil {
		return Bundle{}, err
	}
	identities := map[string][]PageIdentity{"kg_nodes": nodes.Pages, "kg_edges": edges.Pages, "kg_puzzles": puzzles.Pages}
	var snapshot string
	haveSnapshot := false
	for _, pages := range identities {
		for _, p := range pages {
			if !haveSnapshot {
				snapshot = p.SnapshotID
				haveSnapshot = true
			} else if snapshot != p.SnapshotID {
				return Bundle{}, errors.New("RO-EDU snapshot changed across products")
			}
		}
	}
	for _, product := range [][]Record{nodes.Records, edges.Records, puzzles.Records} {
		for _, r := range product {
			if !PublicLegal(r) {
				return Bundle{}, errors.New("RO-EDU record lacks redistributable non-personal legal provenance")
			}
		}
	}
	return Bundle{Record{"build_version": "kg-build@1-real", "snapshot_id": snapshot, "product_pages": identities, "counts": Record{"nodes": len(nodes.Records), "edges": len(edges.Records), "puzzles": len(puzzles.Records)}}, nodes.Records, edges.Records, puzzles.Records}, nil
}
func IDList(v any) []string {
	if v == nil {
		return nil
	}
	if s, ok := v.(string); ok {
		s = strings.TrimSpace(s)
		if s == "" {
			return nil
		}
		var parsed any
		if json.Unmarshal([]byte(s), &parsed) != nil {
			return []string{s}
		}
		v = parsed
	}
	if values, ok := v.([]any); ok {
		out := []string{}
		for _, value := range values {
			out = append(out, fmt.Sprint(value))
		}
		return out
	}
	if values, ok := v.([]string); ok {
		return append([]string{}, values...)
	}
	return []string{fmt.Sprint(v)}
}
