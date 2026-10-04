// Package mobilepack builds the intentionally narrow public mobile KG projection.
package mobilepack

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/roeduclient"
	"sort"
	"strings"
)

func val(v any) string {
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}
func canonical(v any) ([]byte, error) {
	var b bytes.Buffer
	e := json.NewEncoder(&b)
	e.SetEscapeHTML(false)
	if err := e.Encode(v); err != nil {
		return nil, err
	}
	return bytes.TrimSuffix(b.Bytes(), []byte{'\n'}), nil
}
func Build(raw roeduclient.Bundle) (map[string]any, error) {
	nodes, edges, puzzles := []map[string]string{}, []map[string]string{}, []map[string]string{}
	mn, me, mp := []map[string]string{}, [][]string{}, []map[string]string{}
	for _, r := range raw.Nodes {
		id := val(r["id"])
		if id == "" {
			continue
		}
		label := val(r["label_ro"])
		if label == "" {
			label = val(r["title"])
		}
		if label == "" {
			label = id
		}
		nodes = append(nodes, map[string]string{"id": id, "label_ro": label})
		mn = append(mn, map[string]string{"id": id, "label": label})
	}
	for _, r := range raw.Edges {
		a, b := val(r["src_id"]), val(r["dst_id"])
		if a == "" || b == "" {
			continue
		}
		edges = append(edges, map[string]string{"id": val(r["id"]), "src_id": a, "dst_id": b})
		pair := []string{a, b}
		sort.Strings(pair)
		me = append(me, pair)
	}
	for _, r := range raw.Puzzles {
		id, a, b := val(r["id"]), val(r["start_id"]), val(r["target_id"])
		if id == "" || a == "" || b == "" {
			continue
		}
		d := val(r["difficulty"])
		puzzles = append(puzzles, map[string]string{"id": id, "start_id": a, "target_id": b, "difficulty": d})
		mp = append(mp, map[string]string{"id": id, "start": a, "target": b, "difficulty": d})
	}
	for _, records := range [][]map[string]string{nodes, edges, puzzles, mn, mp} {
		sort.SliceStable(records, func(i, j int) bool { return records[i]["id"] < records[j]["id"] })
	}
	sort.SliceStable(me, func(i, j int) bool { return strings.Join(me[i], "|") < strings.Join(me[j], "|") })
	data, err := canonical(map[string]any{"kg_nodes": mn, "kg_edges": me, "kg_puzzles": mp})
	if err != nil {
		return nil, err
	}
	build := val(raw.Meta["build_version"])
	if build == "" {
		build = "unknown"
	}
	manifest := map[string]any{"app": "cat_de_roman_esti", "schema_version": 1, "manifest_version": 1, "build_version": build, "generated_at": val(raw.Meta["generated_at"]), "content_hash": fmt.Sprintf("sha256:%x", sha256.Sum256(data)), "counts": map[string]int{"nodes": len(nodes), "edges": len(edges), "puzzles": len(puzzles)}}
	return map[string]any{"contract": "cat_de_roman_esti.mobile_app_pack.v1", "manifest": manifest, "kg_nodes": nodes, "kg_edges": edges, "kg_puzzles": puzzles}, nil
}
func Bytes(raw roeduclient.Bundle) ([]byte, error) {
	out, err := Build(raw)
	if err != nil {
		return nil, err
	}
	var b bytes.Buffer
	e := json.NewEncoder(&b)
	e.SetEscapeHTML(false)
	e.SetIndent("", "  ")
	if err = e.Encode(out); err != nil {
		return nil, err
	}
	return b.Bytes(), nil
}
