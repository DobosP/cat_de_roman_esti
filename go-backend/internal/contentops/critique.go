package contentops

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/alchimie"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

type Sources struct {
	Root                       string
	Pack                       Object
	Graph                      *graph.Service
	KG                         Object
	PackBytes                  []byte
	KGHash, RubricHash         string
	Rejections, LantRejections []Object
	Inputs                     map[string]snapshot
	BaseInventory              []string
}

func LoadSources(root string) (*Sources, error) {
	root, e := filepath.Abs(root)
	if e != nil {
		return nil, e
	}
	inventory, e := runtimeInventory(root)
	if e != nil {
		return nil, e
	}
	inputs, e := snapshotSources(root)
	if e != nil {
		return nil, e
	}
	pack, blob, e := mirrors(root)
	if e != nil {
		return nil, e
	}
	if e = validateSourcePackEnvelope(pack); e != nil {
		return nil, e
	}
	kg, kgb, e := read(filepath.Join(root, fixtures+"kg_sample.json"))
	if e != nil {
		return nil, e
	}
	mirror, e := os.ReadFile(filepath.Join(root, "tests/fixtures/kg_sample.json"))
	if e != nil {
		return nil, e
	}
	if !bytes.Equal(kgb, mirror) {
		return nil, errors.New("KG mirror drift")
	}
	rubric, e := os.ReadFile(filepath.Join(root, "docs/CRITIQUE_RUBRIC.md"))
	if e != nil {
		return nil, e
	}
	nativeGraph, e := contentbuild.SourceGraph(filepath.Join(root, fixtures+"kg_sample.json"))
	if e != nil {
		return nil, e
	}
	s := &Sources{Root: root, Pack: pack, Graph: nativeGraph, KG: kg, PackBytes: blob, KGHash: textDigest(kgb), RubricHash: textDigest(rubric), Inputs: inputs, BaseInventory: inventory}
	s.Rejections, e = loadLedger(root, "conexiuni")
	if e != nil {
		return nil, e
	}
	s.LantRejections, e = loadLedger(root, "lant")
	if e != nil {
		return nil, e
	}
	if e = checkSnapshots(inputs); e != nil {
		return nil, e
	}
	if e = s.checkInventory(); e != nil {
		return nil, e
	}
	s.reconcileHighWater()
	return s, nil
}
func ledgerPath(root, game string) string {
	return filepath.Join(root, fixtures+game+"_rejection_tombstones.json")
}
func loadLedger(root, game string) ([]Object, error) {
	m, _, e := read(ledgerPath(root, game))
	if e != nil {
		return nil, e
	}
	if integer(m["schema_version"]) != 1 || obj(m["items"]) == nil || obj(m["meta"]) == nil {
		return nil, errors.New("invalid rejection ledger schema")
	}
	items, meta := obj(m["items"]), obj(m["meta"])
	if !validHex(str(meta["initial_seed_gate_sha256"])) || integer(meta["count"]) != len(items) {
		return nil, errors.New("invalid rejection ledger metadata")
	}
	out := []Object{}
	seedIDs := []string{}
	for _, id := range keys(items) {
		row := obj(items[id])
		if row == nil || !validHex(str(row["record_sha256"])) || !validHex(str(row["source_gate_sha256"])) || !validBinding(str(row["review_binding"])) {
			return nil, fmt.Errorf("invalid rejection binding %s", id)
		}
		r := Object{"id": id}
		if game == "conexiuni" {
			groups := obj(row["groups"])
			if len(groups) != 4 || !validHex(str(row["groups_sha256"])) || digest(canonical(groups)) != str(row["groups_sha256"]) {
				return nil, fmt.Errorf("rejection groups digest drift %s", id)
			}
			seen := map[string]bool{}
			for _, g := range []string{"g1", "g2", "g3", "g4"} {
				ids, e := uniqueStrings(groups[g])
				if e != nil || len(ids) != 4 {
					return nil, errors.New("invalid rejection group")
				}
				for _, x := range ids {
					if seen[x] {
						return nil, errors.New("repeated rejection tile")
					}
					seen[x] = true
				}
			}
			r["groups"] = groups
		} else {
			start, target := str(row["start"]), str(row["target"])
			pair := Object{"start": start, "target": target}
			if (!strings.HasPrefix(id, "lt_") && !regexp.MustCompile("^sub_[0-9a-f]{32}$").MatchString(id)) || start == "" || target == "" || start == target || digest(canonical(pair)) != str(row["pair_sha256"]) {
				return nil, errors.New("invalid rejection pair digest")
			}
			r["start"] = start
			r["target"] = target
			if str(row["source_gate_sha256"]) == str(meta["initial_seed_gate_sha256"]) {
				seedIDs = append(seedIDs, id)
			}
		}
		out = append(out, r)
	}
	if game == "conexiuni" && integer(meta["group_count"]) != 4*len(items) {
		return nil, errors.New("stale rejection group count")
	}
	if game == "lant" {
		seed := strings.Join(seedIDs, "\n")
		if len(seedIDs) > 0 {
			seed += "\n"
		}
		if !validHex(str(meta["initial_seed_pack_sha256"])) || !validGitSHA(str(meta["initial_seed_pack_commit"])) || digest([]byte(seed)) != str(meta["initial_seed_id_set_sha256"]) {
			return nil, errors.New("Lanț rejection initial seed drift")
		}
	}
	return out, nil
}
func (s *Sources) brief(id string) Object {
	g := s.Graph
	n := g.Node(id)
	if n == nil {
		return Object{"id": id, "label": "<missing>", "node_type": "?", "category": "?", "salience": 0.0, "degree": 0, "incoming_degree": 0, "description": ""}
	}
	return Object{"id": id, "label": n.LabelRO, "node_type": n.NodeType, "category": n.Category, "salience": n.Salience, "degree": len(g.NeighborIDs(id)), "incoming_degree": len(g.PredecessorIDs(id)), "description": n.Description}
}
func finding(check, level, detail string) Object {
	return Object{"check": check, "level": level, "detail": detail}
}
func boardIDs(r Object) []string {
	ids := []string{}
	for _, g := range keys(obj(r["groups"])) {
		a, _ := stringsOf(obj(r["groups"])[g])
		ids = append(ids, a...)
	}
	return ids
}
func overlap(a, b []string) int {
	m := map[string]bool{}
	for _, s := range a {
		m[s] = true
	}
	n := 0
	for _, s := range b {
		if m[s] {
			n++
		}
	}
	return n
}
func members(r Object, g string) []string { ids, _ := stringsOf(obj(r["groups"])[g]); return ids }
func normalizedPhrase(s string) string    { return contentbuild.Normalize(s) }
func (s *Sources) Findings(r Object, game string, selected map[string]bool) []Object {
	out := []Object{}
	g := s.Graph
	stock := str(r["status"]) == "approved"
	level := "FAIL"
	if stock {
		level = "WARN"
	}
	id := str(r["id"])
	targets := []string{}
	switch game {
	case "contexto", "alchimie":
		targets = []string{str(r["target"])}
	case "lant":
		targets = []string{str(r["start"]), str(r["target"])}
	}
	floor := map[string]float64{"usor": .60, "normal": .35, "greu": .20}[str(r["difficulty"])]
	for _, target := range targets {
		if g.Salience(target) < floor {
			out = append(out, finding("salience_floor", "WARN", fmt.Sprintf("%s below %.2f salience floor", g.Label(target), floor)))
		}
	}
	switch game {
	case "contexto":
		target := str(r["target"])
		incoming := g.PredecessorIDs(target)
		n := 0
		for _, x := range incoming {
			if x != target {
				n++
			}
		}
		if n < 5 {
			out = append(out, finding("contexto_incoming_floor", level, fmt.Sprintf("%d unique incoming predecessors; floor 5", n)))
		}
	case "lant":
		start, target := str(r["start"]), str(r["target"])
		dist := g.DistancesFrom(start)
		optimal := integer(r["optimal"])
		first, width, total := branch(g, start, target, optimal)
		_ = total
		if dist[target] != optimal || first < 2 || width < 2 {
			out = append(out, finding("lant_playability", level, "distance or shortest-path choice floors fail"))
		}
		if !stock {
			for _, v := range array(s.Pack["lant"]) {
				other := obj(v)
				if str(other["id"]) != id && str(other["start"]) == start && str(other["target"]) == target {
					out = append(out, finding("lant_pair_reuse", "FAIL", "directed pair reused by "+str(other["id"])))
				}
			}
			for _, other := range s.LantRejections {
				if str(other["start"]) == start && str(other["target"]) == target {
					out = append(out, finding("lant_rejection_debt", "FAIL", "directed pair rejected by "+str(other["id"])))
				}
			}
		}
	case "conexiuni":
		groups := obj(r["groups"])
		labels := obj(r["group_labels"])
		unfair, contested, raw := fairness(g, r)
		_ = raw
		if len(unfair) > 0 {
			out = append(out, finding("tile_fairness", "FAIL", "foreign type-compatible pull exceeds own: "+strings.Join(unfair, ", ")))
		}
		if len(contested) >= 2 {
			l := "WARN"
			if len(contested) >= 4 {
				l = "FAIL"
			}
			out = append(out, finding("red_herring_budget", l, fmt.Sprintf("%d contested tiles; budget <4", len(contested))))
		}
		homogeneous := map[string]bool{}
		allHom := true
		for _, group := range keys(groups) {
			ids := members(r, group)
			types := map[string]int{}
			for _, x := range ids {
				n := g.Node(x)
				if n != nil {
					types[n.NodeType]++
				}
			}
			if len(types) != 1 {
				allHom = false
			} else {
				for typ := range types {
					homogeneous[typ] = true
				}
			}
			if len(types) == 2 {
				for _, count := range types {
					if count >= 2 {
						out = append(out, finding("type_coherence", "WARN", "mixed node types in "+group))
						break
					}
				}
			}
			label := normalizedPhrase(str(labels[group]))
			for _, x := range ids {
				nl := normalizedPhrase(g.Label(x))
				if len([]rune(nl)) >= 3 && strings.Contains(" "+label+" ", " "+nl+" ") {
					out = append(out, finding("label_self_leak", level, "group label repeats "+g.Label(x)))
				}
			}
			if vagueLabel(label) {
				out = append(out, finding("vague_predicate_wording", level, "catch-all group wording: "+str(labels[group])))
			}
		}
		if allHom && len(homogeneous) >= 3 {
			l := level
			if len(homogeneous) == 3 {
				l = "WARN"
			}
			out = append(out, finding("board_type_shortcut", l, fmt.Sprintf("%d homogeneous group types", len(homogeneous))))
		}
		out = append(out, s.surfaceFindings(r, level)...)
		gks := keys(groups)
		for i, a := range gks {
			for _, b := range gks[i+1:] {
				links := map[string][]string{}
				for _, x := range members(r, a) {
					for _, y := range members(r, b) {
						e := g.Link(x, y)
						rev := g.Link(y, x)
						if (e != nil && e.Strength >= .6) || (rev != nil && rev.Strength >= .6) {
							links[x] = append(links[x], y)
						}
					}
				}
				if matching(links) >= 3 {
					out = append(out, finding("mirrored_groups", level, a+" and "+b+" have >=3 strong disjoint pairs"))
				}
			}
		}
		comparisons := []Object{}
		for _, v := range array(s.Pack["conexiuni"]) {
			other := obj(v)
			if !stock || str(other["status"]) == "approved" || selected[str(other["id"])] {
				comparisons = append(comparisons, other)
			}
		}
		if !stock {
			comparisons = append(comparisons, s.Rejections...)
		}
		duplicateGroups := map[string][]string{}
		reskins := []string{}
		for _, other := range comparisons {
			if str(other["id"]) == id {
				continue
			}
			if overlap(boardIDs(r), boardIDs(other)) >= 8 {
				reskins = append(reskins, str(other["id"]))
			}
			for _, a := range gks {
				for _, b := range keys(obj(other["groups"])) {
					if overlap(members(r, a), members(other, b)) >= 3 {
						duplicateGroups[a] = append(duplicateGroups[a], str(other["id"]))
						break
					}
				}
			}
		}
		if len(reskins) > 0 {
			sort.Strings(reskins)
			out = append(out, finding("board_reskin", level, "half-board reuse: "+strings.Join(reskins, ", ")))
		}
		for _, a := range gks {
			if len(duplicateGroups[a]) > 0 {
				sort.Strings(duplicateGroups[a])
				out = append(out, finding("duplicate_groups", level, a+" exact/three-of-four quad reuse: "+strings.Join(duplicateGroups[a], ", ")))
			}
		}
		if len(selected) > 0 {
			use := map[string]int{}
			for _, v := range array(s.Pack["conexiuni"]) {
				other := obj(v)
				if str(other["status"]) == "approved" || selected[str(other["id"])] {
					for _, x := range boardIDs(other) {
						use[x]++
					}
				}
			}
			for _, x := range boardIDs(r) {
				if use[x] > 8 {
					out = append(out, finding("member_overuse", level, fmt.Sprintf("%s projected use %d >8", x, use[x])))
				}
			}
		}
	}
	if s.regionFinding(r, game) {
		out = append(out, finding("generic_region_link", "WARN", "non-distinctive region association requires independent verification"))
	}
	return out
}
func branch(g *graph.Service, start, target string, optimal int) (int, int, int) {
	from, to := g.DistancesFrom(start), g.DistancesTo(target)
	layers := map[int]int{}
	for id, d := range from {
		if t, ok := to[id]; ok && d+t == optimal {
			layers[d]++
		}
	}
	first := 0
	for _, id := range g.NeighborIDs(start) {
		if d, ok := to[id]; ok && d == optimal-1 {
			first++
		}
	}
	width, total := 1<<30, 0
	for i := 1; i < optimal; i++ {
		width = min(width, layers[i])
		total += layers[i]
	}
	if optimal <= 1 {
		width = 1
	}
	return first, width, total
}
func fairness(g *graph.Service, r Object) ([]string, []string, int) {
	unfair, contested := []string{}, []string{}
	raw := 0
	groups := obj(r["groups"])
	for _, group := range keys(groups) {
		for _, id := range members(r, group) {
			neighbors := g.NeighborIDs(id)
			own := overlap(neighbors, members(r, group))
			for _, neighbor := range neighbors {
				if neighbor == id {
					own--
					break
				}
			}
			bad, tied, rawBad := false, false, false
			for _, foreign := range keys(groups) {
				if foreign == group {
					continue
				}
				pull := overlap(neighbors, members(r, foreign))
				if pull > own {
					rawBad = true
				}
				same := 0
				for _, x := range members(r, foreign) {
					if g.Node(x) != nil && g.Node(id) != nil && g.Node(x).NodeType == g.Node(id).NodeType {
						same++
					}
				}
				if same >= 2 {
					if pull > own {
						bad = true
					}
					if pull == own && pull > 0 {
						tied = true
					}
				}
			}
			if bad {
				unfair = append(unfair, id)
			}
			if tied && !bad {
				contested = append(contested, id)
			}
			if rawBad {
				raw++
			}
		}
	}
	sort.Strings(unfair)
	sort.Strings(contested)
	return unfair, contested, raw
}
func matching(links map[string][]string) int {
	matched := map[string]string{}
	var visit func(string, map[string]bool) bool
	visit = func(x string, seen map[string]bool) bool {
		for _, y := range links[x] {
			if seen[y] {
				continue
			}
			seen[y] = true
			if matched[y] == "" || visit(matched[y], seen) {
				matched[y] = x
				return true
			}
		}
		return false
	}
	for x := range links {
		visit(x, map[string]bool{})
	}
	return len(matched)
}
func vagueLabel(label string) bool {
	for _, p := range []string{"tin de ", "repere ale ", "repere din ", "apar in ", "apar cand ", "intra in ", "fac parte din ", "se intalnesc ", "participa la ", "insotesc ", "ajuta sau ", "structuri si repere ", "simboluri sau repere ", "programe sau masuri ", "din lumea ", "in lumea ", "constelatia ", "pe scurt "} {
		if strings.HasPrefix(label, p) {
			return true
		}
	}
	return regexp.MustCompile(`\b(cu adresa|legat[ae]? (de|cu)|asociat[ae]? (de|cu)|cu impact direct|cu identitate (romaneasca|romana))\b`).MatchString(label)
}

func binding(d Object) string {
	p := copyObject(d)
	delete(p, "review_binding")
	delete(p, "rubric_sha256")
	return "sha256:" + digest(canonical(Object{"version": 1, "rubric_sha256": d["rubric_sha256"], "dossier": p}))
}
func (s *Sources) Dossiers(ids []string, status, game string) (map[string]Object, error) {
	rows, games, e := indexPack(s.Pack)
	if e != nil {
		return nil, e
	}
	selected := map[string]bool{}
	for _, id := range ids {
		if selected[id] {
			return nil, errors.New("duplicate selection ID")
		}
		selected[id] = true
		if rows[id] == nil || (status != "" && str(rows[id]["status"]) != status) || (game != "" && games[id] != game) {
			return nil, fmt.Errorf("unknown or filter-excluded ID %s", id)
		}
	}
	manifest, e := s.runtimeManifest()
	if e != nil {
		return nil, e
	}
	generator := []Object{}
	for _, name := range []string{"go-backend/internal/contentops/critique.go", "go-backend/internal/contentops/surface.go"} {
		blob, e := os.ReadFile(filepath.Join(s.Root, name))
		if e != nil {
			return nil, e
		}
		generator = append(generator, Object{"path": name, "sha256": digest(blob)})
	}
	out := map[string]Object{}
	for _, id := range ids {
		r := rows[id]
		game := games[id]
		findings := s.Findings(r, game, selected)
		d := Object{"id": id, "game": game, "category": r["category"], "difficulty": r["difficulty"], "status": r["status"], "record_sha256": digest(canonical(r)), "kg_sha256": s.KGHash, "rubric_sha256": s.RubricHash, "lint_findings": findings}
		d["review_source_version"] = "native-contentops-v1"
		d["runtime_sources"] = manifest
		d["runtime_source_manifest_sha256"] = digest(canonical(manifest))
		d["generator_sources"] = generator
		d["generator_source_manifest_sha256"] = digest(canonical(generator))
		g := s.Graph
		switch game {
		case "conexiuni":
			groups := []Object{}
			for _, group := range keys(obj(r["groups"])) {
				briefs := []Object{}
				for _, x := range members(r, group) {
					briefs = append(briefs, s.brief(x))
				}
				groups = append(groups, Object{"label": obj(r["group_labels"])[group], "members": briefs})
			}
			d["groups"] = groups
			unfair, contested, raw := fairness(g, r)
			d["fairness"] = Object{"unfair_tiles": unfair, "contested_tiles": contested, "engine_unfair_raw": raw}
		case "contexto":
			target := str(r["target"])
			d["target"] = s.brief(target)
			d["reachable"] = len(g.DistancesTo(target))
			incoming := g.PredecessorIDs(target)
			sample := []Object{}
			n := 0
			for _, x := range incoming {
				if x == target {
					continue
				}
				n++
				if len(sample) < 10 {
					sample = append(sample, Object{"id": x, "label": g.Label(x)})
				}
			}
			d["incoming_neighbor_floor"] = Object{"minimum": 5, "count": n, "sample": sample, "sample_truncated": n > 10, "recognition_assessed": false}
		case "lant":
			start, target := str(r["start"]), str(r["target"])
			d["start"] = s.brief(start)
			d["target"] = s.brief(target)
			d["optimal"] = r["optimal"]
			first, width, total := branch(g, start, target, integer(r["optimal"]))
			d["branch_profile"] = Object{"valid_first_hops": first, "narrowest_shortest_path_layer": width, "total_intermediate_shortest_path_nodes": total}
			d["representative_shortest_paths"] = s.paths(start, target, integer(r["optimal"]))
			caption, e := os.ReadFile(filepath.Join(s.Root, "go-backend/internal/lant/service.go"))
			if e != nil {
				return nil, e
			}
			d["display_rules_sha256"] = textDigest(caption)
		case "alchimie":
			seeds, e := uniqueStrings(r["seeds"])
			if e != nil {
				return nil, e
			}
			target, category := str(r["target"]), str(r["category"])
			d["target"] = s.brief(target)
			briefs := []Object{}
			for _, x := range seeds {
				briefs = append(briefs, s.brief(x))
			}
			d["seeds"] = briefs
			d["target_depth"] = r["target_depth"]
			profile, e := s.RawCraft(seeds, target, category)
			if e != nil {
				return nil, e
			}
			d["craft_profile"] = profile["profile"]
			d["productive_openings"] = profile["openings"]
			d["minimum_action_recipe"] = s.recipeEvidence(profile, target)
		}
		s.enrichDossier(d, r, game)
		d["review_binding"] = binding(d)
		out[id] = d
	}
	return out, nil
}
func (s *Sources) paths(start, target string, optimal int) []Object {
	g := s.Graph
	to := g.DistancesTo(target)
	routes := []Object{}
	var walk func([]string)
	walk = func(path []string) {
		if len(routes) >= 4 {
			return
		}
		last := path[len(path)-1]
		if last == target {
			concepts := []Object{}
			for _, id := range path {
				concepts = append(concepts, Object{"id": id, "label": g.Label(id)})
			}
			routes = append(routes, Object{"nodes": concepts})
			return
		}
		for _, id := range g.NeighborIDs(last) {
			if distance, ok := to[id]; ok && distance == optimal-len(path) {
				walk(append(append([]string{}, path...), id))
			}
		}
	}
	walk([]string{start})
	return routes
}
func (s *Sources) RawCraft(seeds []string, target, category string) (Object, error) {
	sort.Strings(seeds)
	g := s.Graph
	owned := map[string]bool{}
	for _, id := range seeds {
		owned[id] = true
	}
	gen := 0
	generation := map[string]int{}
	for _, id := range seeds {
		generation[id] = 0
	}
	openings := []Object{}
	for i, a := range seeds {
		for _, b := range seeds[i+1:] {
			fresh := []Object{}
			for _, id := range g.CommonNeighbors(a, b, category) {
				if !owned[id] {
					fresh = append(fresh, Object{"id": id, "label": g.Label(id)})
				}
			}
			if len(fresh) > 0 {
				openings = append(openings, Object{"pair": []string{a, b}, "results": fresh})
			}
		}
	}
	for {
		gen++
		ids := []string{}
		for id := range owned {
			ids = append(ids, id)
		}
		sort.Strings(ids)
		fresh := map[string]bool{}
		for i, a := range ids {
			for _, b := range ids[i+1:] {
				for _, id := range g.CommonNeighbors(a, b, category) {
					if !owned[id] {
						fresh[id] = true
					}
				}
			}
		}
		if len(fresh) == 0 {
			break
		}
		for id := range fresh {
			owned[id] = true
			generation[id] = gen
		}
		if len(owned) > MaxRecords {
			return nil, errors.New("craft closure exceeds bound")
		}
	}
	type state struct {
		ids   []string
		route []Object
	}
	frontier := []state{{append([]string{}, seeds...), []Object{}}}
	seen := map[string]bool{strings.Join(seeds, "\x00"): true}
	var recipe []Object
	for actions := 1; actions <= 6 && recipe == nil; actions++ {
		sort.Slice(frontier, func(i, j int) bool {
			return strings.Join(frontier[i].ids, "\x00") < strings.Join(frontier[j].ids, "\x00")
		})
		next := []state{}
		for _, st := range frontier {
			for i, a := range st.ids {
				for _, b := range st.ids[i+1:] {
					fresh := []string{}
					for _, id := range g.CommonNeighbors(a, b, category) {
						if sort.SearchStrings(st.ids, id) == len(st.ids) || st.ids[sort.SearchStrings(st.ids, id)] != id {
							fresh = append(fresh, id)
						}
					}
					if len(fresh) == 0 {
						continue
					}
					ids := append(append([]string{}, st.ids...), fresh...)
					sort.Strings(ids)
					step := Object{"pair": []string{a, b}, "results": fresh}
					route := append(append([]Object{}, st.route...), step)
					if sort.SearchStrings(ids, target) < len(ids) && ids[sort.SearchStrings(ids, target)] == target {
						recipe = route
						break
					}
					key := strings.Join(ids, "\x00")
					if seen[key] {
						continue
					}
					if len(seen) >= 50000 {
						return nil, errors.New("exact craft search exceeds 50000 states")
					}
					seen[key] = true
					next = append(next, state{ids, route})
				}
				if recipe != nil {
					break
				}
			}
			if recipe != nil {
				break
			}
		}
		frontier = next
	}
	if recipe == nil {
		return nil, errors.New("craft target not certified within six actions")
	}
	return Object{"profile": Object{"opening_pairs": len(openings), "closure_size": len(generation), "target_generation": generation[target]}, "openings": openings, "recipe": Object{"exact_actions": len(recipe), "steps": recipe}}, nil
}
func (s *Sources) CoreProjection(r Object) *alchimie.Projection {
	seeds, _ := stringsOf(r["seeds"])
	return alchimie.BuildProjection(s.Graph, seeds, str(r["target"]), str(r["category"]))
}

func (s *Sources) recipeEvidence(profile Object, target string) []Object {
	steps := array(obj(profile["recipe"])["steps"])
	out := []Object{}
	for index, v := range steps {
		step := obj(v)
		ids, _ := stringsOf(step["results"])
		required := map[string]bool{}
		for _, later := range steps[index+1:] {
			pair, _ := stringsOf(obj(later)["pair"])
			for _, id := range pair {
				required[id] = true
			}
		}
		required[target] = true
		sort.Slice(ids, func(i, j int) bool {
			a, b := required[ids[i]], required[ids[j]]
			if a != b {
				return a
			}
			if a {
				return ids[i] < ids[j]
			}
			if s.Graph.Salience(ids[i]) != s.Graph.Salience(ids[j]) {
				return s.Graph.Salience(ids[i]) > s.Graph.Salience(ids[j])
			}
			return ids[i] < ids[j]
		})
		n := 0
		for _, id := range ids {
			if required[id] {
				n++
			}
		}
		limit := max(6, n)
		count := len(ids)
		if len(ids) > limit {
			ids = ids[:limit]
		}
		results := []Object{}
		for _, id := range ids {
			results = append(results, Object{"id": id, "label": s.Graph.Label(id)})
		}
		pairs := []Object{}
		pair, _ := stringsOf(step["pair"])
		for _, id := range pair {
			pairs = append(pairs, Object{"id": id, "label": s.Graph.Label(id)})
		}
		out = append(out, Object{"pair": pairs, "result_count": count, "results": results})
	}
	return out
}

func (s *Sources) enrichDossier(d, r Object, game string) {
	g := s.Graph
	flags := s.regionFlags()
	involved := []string{}
	switch game {
	case "conexiuni":
		involved = boardIDs(r)
	case "contexto":
		involved = []string{str(r["target"])}
	case "lant":
		involved = []string{str(r["start"]), str(r["target"])}
	case "alchimie":
		involved, _ = stringsOf(r["seeds"])
		involved = append(involved, str(r["target"]))
	}
	regional := Object{}
	for _, id := range involved {
		if flags[id] != "" {
			regional[g.Label(id)] = flags[id]
		}
	}
	if len(regional) > 0 {
		d["nondistinctive_region_links"] = regional
	}
	switch game {
	case "conexiuni":
		group := map[string]string{}
		for _, key := range keys(obj(r["groups"])) {
			for _, id := range members(r, key) {
				group[id] = key
			}
		}
		strength := s.undirectedStrength()
		cross := []Object{}
		for a, ga := range group {
			for b, gb := range group {
				if a < b && ga != gb && strength[a][b] >= .6 {
					cross = append(cross, Object{"a": g.Label(a), "a_group": obj(r["group_labels"])[ga], "b": g.Label(b), "b_group": obj(r["group_labels"])[gb], "strength": strength[a][b]})
				}
			}
		}
		sort.Slice(cross, func(i, j int) bool {
			if number(cross[i]["strength"]) != number(cross[j]["strength"]) {
				return number(cross[i]["strength"]) > number(cross[j]["strength"])
			}
			if str(cross[i]["a"]) != str(cross[j]["a"]) {
				return str(cross[i]["a"]) < str(cross[j]["a"])
			}
			return str(cross[i]["b"]) < str(cross[j]["b"])
		})
		d["cross_group_strong_edges"] = cross
		fair := obj(d["fairness"])
		for _, key := range []string{"unfair_tiles", "contested_tiles"} {
			ids, _ := stringsOf(fair[key])
			labels := []string{}
			for _, id := range ids {
				labels = append(labels, g.Label(id))
			}
			sort.Strings(labels)
			fair[key] = labels
		}
	case "contexto":
		target := str(r["target"])
		strong := []Object{}
		for _, id := range g.PredecessorIDs(target) {
			if edge := g.Link(id, target); edge != nil && edge.Strength >= .6 {
				brief := s.brief(id)
				brief["strength"] = edge.Strength
				strong = append(strong, brief)
			}
		}
		sort.Slice(strong, func(i, j int) bool {
			if number(strong[i]["strength"]) != number(strong[j]["strength"]) {
				return number(strong[i]["strength"]) > number(strong[j]["strength"])
			}
			return str(strong[i]["id"]) < str(strong[j]["id"])
		})
		if len(strong) > 10 {
			strong = strong[:10]
		}
		d["strong_neighbors"] = strong
	case "lant":
		paths := []Object{}
		for _, path := range s.rankPaths(str(r["start"]), str(r["target"]), integer(r["optimal"])) {
			nodes, edges := []Object{}, []Object{}
			for _, id := range path {
				nodes = append(nodes, Object{"id": id, "label": g.Label(id)})
			}
			for i, src := range path[:len(path)-1] {
				dst := path[i+1]
				edge := g.Link(src, dst)
				if edge != nil {
					edges = append(edges, Object{"from": Object{"id": src, "label": g.Label(src)}, "to": Object{"id": dst, "label": g.Label(dst)}, "relation": edge.Relation, "label": edge.LabelRO, "display_label": contentbuild.Caption(g, src, dst), "strength": edge.Strength})
				}
			}
			paths = append(paths, Object{"nodes": nodes, "edges": edges})
		}
		d["representative_shortest_paths"] = paths
	case "alchimie":
		openings := []Object{}
		for _, v := range array(d["productive_openings"]) {
			raw := obj(v)
			pair, _ := stringsOf(raw["pair"])
			if len(pair) != 2 {
				continue
			}
			results := array(raw["results"])
			sort.Slice(results, func(i, j int) bool {
				a, b := str(obj(results[i])["id"]), str(obj(results[j])["id"])
				if g.Salience(a) != g.Salience(b) {
					return g.Salience(a) > g.Salience(b)
				}
				return a < b
			})
			count := len(results)
			if len(results) > 4 {
				results = results[:4]
			}
			openings = append(openings, Object{"pair": []Object{{"id": pair[0], "label": g.Label(pair[0])}, {"id": pair[1], "label": g.Label(pair[1])}}, "result_count": count, "results": results})
		}
		sort.Slice(openings, func(i, j int) bool {
			if integer(openings[i]["result_count"]) != integer(openings[j]["result_count"]) {
				return integer(openings[i]["result_count"]) > integer(openings[j]["result_count"])
			}
			return string(canonical(openings[i]["pair"])) < string(canonical(openings[j]["pair"]))
		})
		if len(openings) > 6 {
			openings = openings[:6]
		}
		d["productive_openings"] = openings
	}
}
