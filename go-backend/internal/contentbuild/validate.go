package contentbuild

import (
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

var Games = []string{"conexiuni", "contexto", "lant", "alchimie"}
var payloadKeys = map[string][]string{"conexiuni": {"groups", "group_labels", "order"}, "contexto": {"target"}, "lant": {"start", "target", "optimal"}, "alchimie": {"seeds", "target", "target_depth"}}

// ValidateFixture checks the source graph contract, directed puzzle paths,
// category scope, shortest paths, distractor shortcuts, aliases and counts.
func ValidateFixture(path string) []string {
	raw, e := ReadObject(path, 16<<20)
	if e != nil {
		return []string{"structure: " + e.Error()}
	}
	return validateFixture(raw)
}
func validateFixture(raw map[string]any) []string {
	errors := []string{}
	fail := func(class, msg string) { errors = append(errors, class+": "+msg) }
	r, e := frozenRules()
	if e != nil {
		return []string{e.Error()}
	}
	cats := object(r["category_labels"])
	for _, k := range []string{"meta", "kg_nodes", "kg_edges", "kg_puzzles"} {
		if _, ok := raw[k]; !ok {
			fail("structure", "missing "+k)
		}
	}
	for _, k := range []string{"kg_nodes", "kg_edges", "kg_puzzles"} {
		if _, ok := raw[k].([]any); !ok {
			fail("structure", k+" must be an array")
		}
	}
	if len(errors) > 0 {
		return errors
	}
	if len(array(raw["kg_nodes"])) > 10000 || len(array(raw["kg_edges"])) > 50000 || len(array(raw["kg_puzzles"])) > 5000 {
		fail("structure", "record cap exceeded")
		return errors
	}
	kinds := []struct {
		key    string
		fields []string
	}{{"kg_nodes", []string{"id", "node_type", "label_ro", "category", "description", "salience", "difficulty_tier", "degree"}}, {"kg_edges", []string{"id", "src_id", "dst_id", "relation", "label_ro", "strength", "is_distractor", "bidirectional"}}, {"kg_puzzles", []string{"id", "start_id", "target_id", "category", "difficulty", "optimal_hops", "par", "solution_path", "hint_neighbors", "start_salience", "target_salience"}}}
	for _, kind := range kinds {
		ids := map[string]bool{}
		for i, v := range array(raw[kind.key]) {
			m := object(v)
			if m == nil {
				fail("field_shapes", fmt.Sprintf("%s[%d] must be object", kind.key, i))
				continue
			}
			fields := kind.fields
			if kind.key == "kg_nodes" {
				if _, ok := m["aliases"]; ok {
					fields = append(append([]string{}, fields...), "aliases")
				}
			}
			if !exact(m, fields...) {
				fail("field_shapes", kind.key+" "+str(m["id"])+" unexpected fields")
			}
			id := str(m["id"])
			if id == "" {
				fail("field_shapes", "empty/non-string id")
			}
			if ids[id] {
				fail("unique_ids", "duplicate "+id)
			}
			ids[id] = true
			if kind.key == "kg_nodes" {
				if _, ok := cats[str(m["category"])]; !ok {
					fail("field_shapes", "unknown category")
				}
				sal := number(m["salience"])
				tier := "hard"
				if sal >= .66 {
					tier = "easy"
				} else if sal >= .33 {
					tier = "medium"
				}
				if str(m["difficulty_tier"]) != tier {
					fail("node_tier_bands", id+" salience tier mismatch")
				}
				if _, ok := integer(m["degree"]); !ok {
					fail("field_shapes", id+" degree must be integer")
				}
				if str(m["node_type"]) == "concept" && len(strings.FieldsFunc(str(m["label_ro"]), pySpace)) > 5 {
					fail("label_style", id+" concept exceeds five words")
				}
				if a, ok := m["aliases"]; ok {
					if _, ok := a.([]any); !ok {
						fail("field_shapes", id+" aliases must be array")
					}
					for _, x := range array(a) {
						if str(x) == "" || Normalize(str(x)) == "" {
							fail("alias_unique", id+" empty alias")
						}
						if len(strings.FieldsFunc(str(x), pySpace)) > 5 {
							fail("label_style", id+" alias exceeds five words")
						}
					}
				}
			} else if kind.key == "kg_edges" {
				for _, k := range []string{"src_id", "dst_id"} {
					if str(m[k]) == "" {
						fail("field_shapes", id+" missing "+k)
					}
				}
				for _, k := range []string{"is_distractor", "bidirectional"} {
					if _, ok := m[k].(bool); !ok {
						n, numeric := integer(m[k])
						if !numeric || (n != 0 && n != 1) {
							fail("field_shapes", id+" "+k+" must be boolean or 0/1")
						}
					}
				}
			} else {
				for _, k := range []string{"par", "optimal_hops"} {
					if _, ok := integer(m[k]); !ok {
						fail("field_shapes", id+" "+k+" must be integer")
					}
				}
				for _, k := range []string{"solution_path", "hint_neighbors"} {
					if _, ok := m[k].([]any); !ok {
						fail("field_shapes", id+" "+k+" must be array")
					}
					for _, x := range array(m[k]) {
						if str(x) == "" {
							fail("field_shapes", id+" invalid path id")
						}
					}
				}
				if !contains([]string{"easy", "hard"}, str(m["difficulty"])) {
					fail("field_shapes", id+" unknown difficulty")
				}
			}
		}
	}
	for _, v := range errors {
		if strings.HasPrefix(v, "field_shapes:") {
			return errors
		}
	}
	c, e := parsedGraph(raw)
	if e != nil {
		return append(errors, e.Error())
	}
	g := graph.New(c)
	owners := map[string]string{}
	for _, n := range c.Nodes {
		for _, s := range []string{n.ID, n.LabelRO} {
			k := Normalize(s)
			if owners[k] == "" {
				owners[k] = n.ID
			}
		}
	}
	aliases := map[string]string{}
	for _, n := range c.Nodes {
		for _, a := range n.Aliases {
			k := Normalize(a)
			if owner := owners[k]; owner != "" {
				fail("alias_unique", n.ID+" alias collides with label/id "+owner)
			}
			if owner := aliases[k]; owner != "" && owner != n.ID {
				fail("alias_unique", n.ID+" alias collides with "+owner)
			}
			if aliases[k] == "" {
				aliases[k] = n.ID
			}
		}
	}
	meta := object(raw["meta"])
	counts := object(meta["counts"])
	catCounts := map[string]any{}
	for _, n := range c.Nodes {
		catCounts[n.Category] = int(number(catCounts[n.Category])) + 1
	}
	pcd := map[string]any{}
	for _, v := range array(raw["kg_puzzles"]) {
		m := object(v)
		k := str(m["category"]) + "/" + str(m["difficulty"])
		pcd[k] = int(number(pcd[k])) + 1
	}
	for k, n := range map[string]int{"nodes": len(c.Nodes), "edges": len(c.Edges), "puzzles": len(array(raw["kg_puzzles"]))} {
		if number(counts[k]) != float64(n) {
			fail("meta_counts", k+" count differs")
		}
	}
	for k, v := range map[string]any{"by_category": catCounts, "puzzles_by_cat_diff": pcd} {
		if m := object(counts[k]); len(m) > 0 && !equal(m, v) {
			fail("meta_counts", k+" differs")
		}
	}
	for _, e := range c.Edges {
		if !g.Exists(e.Src) || !g.Exists(e.Dst) {
			fail("puzzle_ids_resolve", e.ID+" unknown endpoint")
		}
	}
	for _, v := range array(raw["kg_puzzles"]) {
		p := object(v)
		id := str(p["id"])
		path := stringsOf(p["solution_path"])
		h, _ := integer(p["optimal_hops"])
		par, _ := integer(p["par"])
		cat := str(p["category"])
		start, target := str(p["start_id"]), str(p["target_id"])
		if len(path) == 0 {
			fail("puzzle_shortest_path", id+" empty path")
			continue
		}
		if path[0] != start || path[len(path)-1] != target {
			fail("puzzle_shortest_path", id+" endpoints differ")
		}
		if h != par || h != len(path)-1 {
			fail("puzzle_par", id+" par differs")
		}
		lo, hi := 2, 3
		if str(p["difficulty"]) == "hard" {
			lo, hi = 4, 7
		}
		if h < lo || h > hi {
			fail("puzzle_hop_band", id+" outside band")
		}
		if !equal(p["hint_neighbors"], path[1:]) {
			fail("puzzle_hints", id+" hint path differs")
		}
		pc := map[string]bool{}
		valid := true
		for _, n := range path {
			if !g.Exists(n) {
				fail("puzzle_ids_resolve", id+" unknown path node")
				valid = false
				continue
			}
			pc[g.Node(n).Category] = true
			if cat != "mixed" && g.Node(n).Category != cat {
				fail("puzzle_category_scope", id+" leaves category")
			}
		}
		if cat == "mixed" && len(pc) < 2 {
			fail("puzzle_category_scope", id+" mixed stays in one category")
		}
		if cat != "mixed" && cats[cat] == nil {
			fail("puzzle_category_scope", id+" unknown category")
		}
		if !valid {
			continue
		}
		adj := func(n string, all bool) []string {
			out := []string{}
			for _, nb := range g.Neighbors(n, all) {
				if cat == "mixed" || g.Node(n).Category == cat && g.Node(nb.ID).Category == cat {
					out = append(out, nb.ID)
				}
			}
			return out
		}
		d, ok := distanceWith(start, target, func(n string) []string { return adj(n, false) })
		if !ok || d != h {
			fail("puzzle_shortest_path", id+" actual distance differs")
		}
		for i := 0; i+1 < len(path); i++ {
			if !contains(adj(path[i], false), path[i+1]) {
				fail("puzzle_shortest_path", id+" invalid hop")
			}
		}
		if d, ok := distanceWith(start, target, func(n string) []string { return adj(n, true) }); ok && d < par {
			fail("puzzle_distractor_shortcut", id+" distractor shortcut")
		}
	}
	return errors
}
func distanceWith(start, target string, adj func(string) []string) (int, bool) {
	seen := map[string]int{start: 0}
	q := []string{start}
	for len(q) > 0 {
		n := q[0]
		q = q[1:]
		if n == target {
			return seen[n], true
		}
		for _, x := range adj(n) {
			if _, ok := seen[x]; !ok {
				seen[x] = seen[n] + 1
				q = append(q, x)
			}
		}
	}
	return 0, false
}

// ValidateEnvelope checks all fields, enum values and scalar types, including
// pending/rejected inventory that is never served.
func ValidateEnvelope(game string, rec map[string]any) []string {
	keys, ok := payloadKeys[game]
	if !ok {
		return []string{"unknown game"}
	}
	e := []string{}
	fields := append([]string{"id", "category", "difficulty", "source", "status"}, keys...)
	if !exact(rec, fields...) {
		e = append(e, "record field shape differs")
	}
	if str(rec["id"]) == "" {
		e = append(e, "id must be non-empty string")
	}
	r, err := frozenRules()
	if err != nil {
		return append(e, err.Error())
	}
	if rec["category"] != nil && object(r["category_labels"])[str(rec["category"])] == nil {
		e = append(e, "unknown category")
	}
	if !contains([]string{"usor", "normal", "greu"}, str(rec["difficulty"])) {
		e = append(e, "unknown difficulty")
	}
	if !contains([]string{"user", "ai", "ai_corpus"}, str(rec["source"])) {
		e = append(e, "unknown source")
	}
	if !contains([]string{"approved", "pending", "rejected"}, str(rec["status"])) {
		e = append(e, "unknown status")
	}
	return e
}

// ValidatePayload uses the exact source graph, not the bundled serving export.
func ValidatePayload(g *graph.Service, game string, rec map[string]any) []string {
	e := []string{}
	add := func(s string) { e = append(e, s) }
	switch game {
	case "conexiuni":
		groups, labels := object(rec["groups"]), object(rec["group_labels"])
		if len(groups) != 4 {
			return []string{"groups must contain four groups"}
		}
		tiles := []string{}
		for k, v := range groups {
			if len(array(v)) != 4 {
				add("group requires four tiles")
			}
			tiles = append(tiles, stringsOf(v)...)
			if strings.TrimSpace(str(labels[k])) == "" {
				add("group label required")
			}
		}
		if len(labels) != len(groups) {
			add("group labels keys differ")
		}
		seen := map[string]bool{}
		for _, n := range tiles {
			if seen[n] || !g.Exists(n) {
				add("duplicate or unknown tile")
			}
			seen[n] = true
		}
		order := stringsOf(rec["order"])
		sort.Strings(order)
		sort.Strings(tiles)
		if !equal(order, tiles) {
			add("order is not tile permutation")
		}
	case "contexto":
		target := str(rec["target"])
		if !g.Exists(target) {
			return []string{"unknown target"}
		}
		d := g.DistancesTo(target)
		responsive := 0
		for _, n := range d {
			if n >= 1 && n <= 5 {
				responsive++
			}
		}
		if len(d) < 120 {
			add("target reachable zone below 120")
		}
		if responsive < 40 {
			add("target responsive zone below 40")
		}
	case "lant":
		a, b := str(rec["start"]), str(rec["target"])
		if !g.Exists(a) || !g.Exists(b) || a == b {
			return []string{"distinct known endpoints required"}
		}
		d, ok := g.Distance(a, b)
		if !ok {
			return []string{"target unreachable"}
		}
		par, valid := integer(rec["optimal"])
		if !valid || par != d {
			add("optimal must equal directed BFS distance")
		}
		bands := map[string][2]int{"usor": {2, 3}, "normal": {3, 4}, "greu": {4, 6}}
		band, ok := bands[str(rec["difficulty"])]
		if !ok || d < band[0] || d > band[1] {
			add("distance outside difficulty band")
		}
		from, to := g.DistancesFrom(a), g.DistancesTo(b)
		layers := map[int]int{}
		for n, dist := range from {
			if t, ok := to[n]; ok && dist+t == d {
				layers[dist]++
			}
		}
		first := 0
		for _, n := range g.NeighborIDs(a) {
			if t, ok := to[n]; ok && t == d-1 {
				first++
			}
		}
		if first < 2 {
			add("fewer than two valid first-hop choices")
		}
		for layer := 1; layer < d; layer++ {
			if layers[layer] < 2 {
				add("shortest-path layer width below two")
				break
			}
		}
	case "alchimie":
		seeds := stringsOf(rec["seeds"])
		target, cat := str(rec["target"]), str(rec["category"])
		seen := map[string]bool{}
		if len(seeds) < 5 || len(seeds) > 7 {
			add("five to seven seeds required")
		}
		for _, n := range append(append([]string{}, seeds...), target) {
			if !g.Exists(n) {
				add("unknown node")
			}
		}
		for _, n := range seeds {
			if seen[n] {
				add("duplicate seed")
			}
			seen[n] = true
		}
		if seen[target] {
			add("target is a seed")
		}
		if len(e) > 0 {
			return e
		}
		actual, ok := MinimumAlchimieActions(g, seeds, target, cat)
		depth, valid := integer(rec["target_depth"])
		if !ok {
			add("target not certified within six actions and 50000 states")
		} else if !valid || depth != actual {
			add("target_depth differs from exact action par")
		}
		openings := 0
		for i, a := range seeds {
			for _, b := range seeds[i+1:] {
				for _, n := range g.CommonNeighbors(a, b, cat) {
					if !seen[n] {
						openings++
						break
					}
				}
			}
		}
		if openings < 2 {
			add("fewer than two opening pairs")
		}
	default:
		add("unknown game")
	}
	return e
}

// ValidatePack validates prospective packs independently of reviewed-source pins.
func ValidatePack(kgPath, packPath string) []string {
	raw, err := ReadObject(packPath, 8<<20)
	if err != nil {
		return []string{"structure: " + err.Error()}
	}
	g, err := SourceGraph(kgPath)
	if err != nil {
		return []string{"structure: " + err.Error()}
	}
	return validatePack(raw, g)
}
func validatePack(raw map[string]any, g *graph.Service) []string {
	e := []string{}
	fields := append([]string{"meta"}, Games...)
	if !exact(raw, fields...) {
		return []string{"structure: pack top-level keys differ"}
	}
	ids := map[string]bool{}
	meta := object(raw["meta"])
	counts, water := object(meta["counts"]), object(meta["id_high_water"])
	for _, game := range Games {
		rows, ok := raw[game].([]any)
		if !ok {
			e = append(e, "structure: game must be array")
			continue
		}
		maxID := 0
		for _, v := range rows {
			rec := object(v)
			if rec == nil {
				e = append(e, "item_shape: non-object item")
				continue
			}
			id := str(rec["id"])
			if ids[id] {
				e = append(e, "unique_ids: "+id)
			}
			ids[id] = true
			for _, msg := range ValidateEnvelope(game, rec) {
				e = append(e, "item_shape: "+game+" "+id+": "+msg)
			}
			if rec["status"] == "approved" {
				for _, msg := range ValidatePayload(g, game, rec) {
					e = append(e, "playability: "+game+" "+id+": "+msg)
				}
			}
			parts := strings.Split(id, "_")
			prefix := map[string]string{"conexiuni": "cx", "contexto": "ct", "lant": "lt", "alchimie": "al"}[game]
			if len(parts) >= 3 && parts[0] == prefix {
				n, err := strconv.Atoi(parts[len(parts)-1])
				if err == nil && n > maxID {
					maxID = n
				}
			}
		}
		if n, ok := integer(counts[game]); !ok || n != len(rows) {
			e = append(e, "meta_counts: "+game+" differs")
		}
		if n, ok := integer(water[game]); !ok || n < maxID {
			e = append(e, "id_high_water: "+game+" invalid mark")
		}
	}
	return e
}

// ValidateSources checks each source, the mirrored fixture copies and all bound
// selector/world/review identities before an export is allowed.
func ValidateSources(root string) error { _, err := build(root, true); return err }
func sourcePath(root, name string) string {
	return filepath.Join(root, "cat_de_roman_esti", "fixtures", name)
}

// ValidatePackObjects performs the prospective pack gate without writing files.
func ValidatePackObjects(kg, pack map[string]any) []string {
	c, err := parsedGraph(kg)
	if err != nil {
		return []string{"structure: " + err.Error()}
	}
	return validatePack(pack, graph.New(c))
}
