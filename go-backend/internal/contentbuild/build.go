package contentbuild

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

var SourceNames = []string{"kg_sample.json", "derived_catalog_v38.json", "quick_games_v92.json", "board_rankings_v37.json", "release_reserve_v1.json", "games_pack.json", "alchimie_discovery_world_v92.json", "alchimie_recipe_extensions_v92.json"}

// These are the three review-authority pins retained from the former native
// exporter. New catalog/reserve versions require an explicitly reviewed pin update.
var reviewedPins = map[string]string{"derived_catalog_v38.json": "b4ae19266627b738ebe29928acc5952da9be98415fb8632870243e8634a32ad9", "quick_games_v92.json": "99db98d64b5b7c103ee70eab2b2b79b04d4ff62072942a159caa65518375ed9f", "release_reserve_v1.json": "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7"}

const RubricSHA256 = "3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101"

// Build independently reconstructs every source-derived serving field. Its output
// has the exact historical deterministic byte encoding, including a final newline.
func Build(root string) ([]byte, error) {
	m, err := build(root, true)
	if err != nil {
		return nil, err
	}
	b, err := Canonical(m)
	return append(b, '\n'), err
}

// Load returns freshly built private content suitable for native offline tools.
func Load(root string) (*content.Content, error) {
	b, err := Build(root)
	if err != nil {
		return nil, err
	}
	return content.Decode(b)
}
func build(root string, validate bool) (map[string]any, error) {
	r, err := frozenRules()
	if err != nil {
		return nil, err
	}
	for _, name := range []string{"CAT_KG_FIXTURE", "CAT_GAMES_PACK", "CAT_BOARD_RANKINGS"} {
		if os.Getenv(name) != "" {
			return nil, fmt.Errorf("native export requires reviewed sources without %s override", name)
		}
	}
	src := map[string]map[string]any{}
	digests := map[string]any{}
	for _, name := range SourceNames {
		max := int64(8 << 20)
		if name == "kg_sample.json" {
			max = 16 << 20
		}
		if name == "release_reserve_v1.json" {
			max = 64 << 10
		}
		if name == "alchimie_recipe_extensions_v92.json" {
			max = 4 << 20
		}
		if name == "quick_games_v92.json" || name == "alchimie_discovery_world_v92.json" {
			max = 2 << 20
		}
		raw, e := ReadObject(sourcePath(root, name), max)
		if e != nil {
			return nil, fmt.Errorf("%s: %w", name, e)
		}
		b, e := os.ReadFile(sourcePath(root, name))
		if e != nil {
			return nil, e
		}
		src[name] = raw
		digests[name] = TextSHA256(b)
		if p := reviewedPins[name]; p != "" && p != digests[name] {
			return nil, fmt.Errorf("%s: reviewed artifact digest drift", name)
		}
	}
	kg, pack := src["kg_sample.json"], src["games_pack.json"]
	for _, name := range []string{"kg_sample.json", "games_pack.json"} {
		a, e := os.ReadFile(sourcePath(root, name))
		if e != nil {
			return nil, e
		}
		b, e := os.ReadFile(filepath.Join(root, "tests", "fixtures", name))
		if e != nil {
			return nil, e
		}
		if !bytes.Equal(a, b) {
			return nil, fmt.Errorf("copies_identical: %s package/test copies differ", name)
		}
	}
	if err := verifyRubric(root); err != nil {
		return nil, err
	}
	c, err := parsedGraph(kg)
	if err != nil {
		return nil, err
	}
	g := graph.New(c)
	if validate {
		if errors := validateFixture(kg); len(errors) > 0 {
			return nil, fmt.Errorf("fixture invalid: %s", errorSummary(errors))
		}
		if errors := validatePack(pack, g); len(errors) > 0 {
			return nil, fmt.Errorf("pack invalid: %s", errorSummary(errors))
		}
	}
	rank, err := validateRankings(src["board_rankings_v37.json"], pack, digests)
	if err != nil {
		return nil, err
	}
	reserve, err := validateReserve(src["release_reserve_v1.json"], pack)
	if err != nil {
		return nil, err
	}
	derived := src["derived_catalog_v38.json"]
	if err := validateDerived(derived, pack, digests, r); err != nil {
		return nil, err
	}
	quick := src["quick_games_v92.json"]
	if err := validateQuick(quick, derived, g, digests); err != nil {
		return nil, err
	}
	world, err := validateWorld(src["alchimie_discovery_world_v92.json"], g)
	if err != nil {
		return nil, err
	}
	extensions := src["alchimie_recipe_extensions_v92.json"]
	if err := validateExtensions(extensions, g); err != nil {
		return nil, err
	}
	items := []any{}
	for _, game := range Games {
		rows := append([]any{}, array(pack[game])...)
		sort.Slice(rows, func(i, j int) bool { return str(object(rows[i])["id"]) < str(object(rows[j])["id"]) })
		for _, v := range rows {
			m := object(v)
			if m["status"] != "approved" {
				continue
			}
			rating := rank[str(m["id"])]
			p := map[string]any{}
			for _, key := range payloadKeys[game] {
				p[key] = m[key]
			}
			category := str(m["category"])
			if m["category"] == nil {
				category = "None"
			}
			items = append(items, map[string]any{"game": game, "id": m["id"], "category": category, "difficulty": m["difficulty"], "source": m["source"], "status": m["status"], "payload": p, "pilot_score": rating["pilot_score"], "pilot_eligible": rating["pilot_eligible"], "selection_weight": rating["selection_weight"]})
		}
	}
	rawBoards := append(append([]any{}, array(derived["boards"])...), array(quick["boards"])...)
	sort.Slice(rawBoards, func(i, j int) bool { return str(object(rawBoards[i])["id"]) < str(object(rawBoards[j])["id"]) })
	boards := []any{}
	for _, game := range []string{"intrusul", "perechi"} {
		for _, v := range rawBoards {
			m := object(v)
			if m["game"] != game {
				continue
			}
			if sha := reserve[str(m["id"])]; sha != "" {
				def := map[string]any{}
				for _, key := range []string{"id", "game", "source_id", "category", "difficulty", "payload"} {
					def[key] = m[key]
				}
				if valueDigest(def) != sha {
					return nil, fmt.Errorf("release reserve quick record drift")
				}
				continue
			}
			boards = append(boards, map[string]any{"game": game, "catalog_id": m["id"], "source_id": m["source_id"], "category": m["category"], "difficulty": m["difficulty"], "overall_score": m["standard_score"], "starter_score": m["starter_score"], "overall_rank": m["standard_rank"], "starter_rank": m["starter_rank"], "starter_safe": m["starter_eligible"], "payload": m["payload"]})
		}
	}
	if len(boards) != len(rawBoards)-len(reserve) {
		return nil, fmt.Errorf("release reserve missing quick identity")
	}
	nodes, edges := []any{}, []any{}
	for _, n := range c.Nodes {
		nodes = append(nodes, nodeMap(n))
	}
	for _, e := range c.Edges {
		edges = append(edges, edgeMap(e))
	}
	captions := map[string]any{}
	reviewed, fallbacks := object(r["reviewed_captions"]), object(r["caption_fallbacks"])
	for _, a := range g.AllIDs() {
		for _, b := range g.NeighborIDs(a) {
			e := g.Link(a, b)
			if e == nil {
				continue
			}
			caption := str(fallbacks[e.Relation])
			if caption == "" {
				caption = "legătură directă"
			}
			pair := []string{a, b}
			sort.Strings(pair)
			rv := array(reviewed[strings.Join(pair, "\x00")])
			if len(rv) == 2 && valueDigest(edgeMap(*e)) == str(rv[0]) {
				caption = str(rv[1])
			}
			captions[a+"\x00"+b] = caption
		}
	}
	patterns := map[string]any{}
	for _, v := range object(r["category_labels"]) {
		patterns[str(v)] = labelPattern(str(v), r)
	}
	for _, v := range items {
		m := object(v)
		if m["game"] == "conexiuni" {
			for _, label := range object(object(m["payload"])["group_labels"]) {
				patterns[str(label)] = labelPattern(str(label), r)
			}
		}
	}
	manifest := fixtureManifest(kg)
	metadata := copyObject(object(r["metadata"]))
	health := copyObject(object(metadata["/api/health"]))
	health["concepts"] = len(nodes)
	health["version"] = r["app_version"]
	metadata["/api/health"] = health
	metadata["/api/manifest"] = manifest
	metadata["/api/categories"] = categoriesMetadata(c, items, r)
	return map[string]any{"schema_version": 2, "app_version": r["app_version"], "sources": digests, "labels": c.Labels, "category_labels": r["category_labels"], "category_order": r["category_order"], "letter_ranges": r["letter_ranges"], "label_patterns": patterns, "nodes": nodes, "edges": edges, "normalization_map": r["normalization_map"], "accent_normalization_map": r["accent_normalization_map"], "casefold_map": r["casefold_map"], "normalized_index": c.NormalizedIndex, "pack_ranked": true, "pack_items": items, "contexto_data": r["contexto_data"], "lant_captions": captions, "discovery_world": world, "recipe_extensions": extensions, "alchimie_projections": map[string]any{}, "metadata": metadata, "manifest": manifest, "boards": boards}, nil
}
func fixtureManifest(kg map[string]any) map[string]any {
	meta := object(kg["meta"])
	data := map[string]any{}
	for _, key := range []string{"kg_nodes", "kg_edges", "kg_puzzles"} {
		rows := append([]any{}, array(kg[key])...)
		sort.Slice(rows, func(i, j int) bool { return str(object(rows[i])["id"]) < str(object(rows[j])["id"]) })
		data[key] = rows
	}
	build := str(meta["build_version"])
	if build == "" {
		build = "unknown"
	}
	return map[string]any{"app": "cat_de_roman_esti", "schema_version": 1, "manifest_version": 1, "build_version": build, "generated_at": str(meta["generated_at"]), "content_hash": "sha256:" + valueDigest(data), "counts": map[string]any{"nodes": len(array(kg["kg_nodes"])), "edges": len(array(kg["kg_edges"])), "puzzles": len(array(kg["kg_puzzles"]))}}
}
func categoriesMetadata(c *content.Content, items []any, r map[string]any) map[string]any {
	out := []any{}
	for i, key := range stringsOf(r["category_order"]) {
		base := object(array(object(object(r["metadata"])["/api/categories"])["categories"])[i])
		m := copyObject(base)
		nodes := 0
		for _, n := range c.Nodes {
			if n.Category == key {
				nodes++
			}
		}
		curated, available, byDiff := map[string]any{}, map[string]any{}, map[string]any{}
		for _, game := range Games {
			count := 0
			diff := map[string]any{}
			anyAvailable := false
			floor := map[string]int{"contexto": 10, "lant": 10, "alchimie": 8}[game]
			for _, d := range []string{"usor", "normal", "greu"} {
				yes := floor > 0 && nodes >= floor
				for _, v := range items {
					it := object(v)
					if it["game"] == game && it["category"] == key && it["difficulty"] == d && it["pilot_eligible"] == true {
						yes = true
					}
				}
				diff[d] = yes
				anyAvailable = anyAvailable || yes
			}
			for _, v := range items {
				it := object(v)
				if it["game"] == game && it["category"] == key {
					count++
				}
			}
			curated[game] = count
			available[game] = anyAvailable
			byDiff[game] = diff
		}
		m["node_count"] = nodes
		m["curated"] = curated
		m["available"] = available
		m["available_by_difficulty"] = byDiff
		out = append(out, m)
	}
	return map[string]any{"categories": out}
}

// PinBytes emits the Go digest authority without changing the historical pin
// header; canonical bundle bytes remain independently frozen by native tests.
func PinBytes(b []byte) []byte {
	return []byte("// Code generated by scripts/export_go_content.py; DO NOT EDIT.\npackage content\n\nconst bundledSHA256 = \"" + SHA256(b) + "\"\n")
}
func Export(root string, check bool) error {
	if !check {
		return exportTransaction(root, func() ([]byte, []byte, error) {
			b, e := Build(root)
			if e != nil {
				return nil, nil, e
			}
			return b, PinBytes(b), nil
		}, func() error { return Export(root, true) }, nil)
	}
	b, err := Build(root)
	if err != nil {
		return err
	}
	out := filepath.Join(root, "go-backend", "internal", "content", "bundled.json")
	pin := filepath.Join(filepath.Dir(out), "digest.go")
	expectedPin := PinBytes(b)
	old, e := os.ReadFile(out)
	p, f := os.ReadFile(pin)
	if e != nil || f != nil || !bytes.Equal(old, b) || !bytes.Equal(p, expectedPin) {
		return fmt.Errorf("native private content is stale; run cat-content export")
	}
	return nil
}

func asContent(v any) (*content.Content, error) {
	b, e := Canonical(v)
	if e != nil {
		return nil, e
	}
	var c content.Content
	e = json.Unmarshal(b, &c)
	return &c, e
}

func verifyRubric(root string) error {
	b, err := os.ReadFile(filepath.Join(root, "docs", "CRITIQUE_RUBRIC.md"))
	if err != nil {
		return fmt.Errorf("required reviewed rubric: %w", err)
	}
	if TextSHA256(b) != RubricSHA256 {
		return fmt.Errorf("reviewed rubric digest drift")
	}
	return nil
}
