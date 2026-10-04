package contentrails

import (
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/alchimie"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"sort"
	"strings"
)

func concept(g *graph.Service, id string) map[string]any {
	n := g.Node(id)
	if n == nil {
		return nil
	}
	return map[string]any{"id": id, "label": n.LabelRO, "category": n.Category}
}
func projectionCore(p *alchimie.Projection, seeds []string, target, category string) map[string]any {
	pairs := []alchimie.Pair{}
	for pair := range p.Recipes {
		pairs = append(pairs, pair)
	}
	sort.Slice(pairs, func(i, j int) bool {
		if pairs[i][0] != pairs[j][0] {
			return pairs[i][0] < pairs[j][0]
		}
		return pairs[i][1] < pairs[j][1]
	})
	recipes := []any{}
	for _, pair := range pairs {
		recipes = append(recipes, map[string]any{"pair": pair, "results": p.Recipes[pair]})
	}
	return map[string]any{"seeds": seeds, "target": target, "category": category, "par": p.Par, "recipes": recipes, "routes": p.Routes}
}
func buildExtensions(root string, s *Source, candidate map[string]any, candidateSHA string, reviews []Review) (map[string]any, error) {
	if candidate["schema"] != "alchimie-bounded-completion-candidates-v1" {
		return nil, fmt.Errorf("extension candidate schema")
	}
	bind, err := bindings(root)
	if err != nil {
		return nil, err
	}
	wanted := map[string]string{"pack": "games_pack.json", "kg": "kg_sample.json", "rubric": "rubric"}
	for name, file := range wanted {
		b := object(object(candidate["bindings"])[name])
		path := "cat_de_roman_esti/fixtures/" + file
		if name == "rubric" {
			path = "docs/CRITIQUE_RUBRIC.md"
		}
		if b["path"] != path || b["sha256"] != bind[file] {
			return nil, fmt.Errorf("extension source binding drift")
		}
	}
	data, err := contentbuild.Load(root)
	if err != nil {
		return nil, err
	}
	g, err := sourceGraph(root)
	if err != nil {
		return nil, err
	}
	packRaw, err := fixture(root, "games_pack.json")
	if err != nil {
		return nil, err
	}
	sourceRecords := map[string]any{}
	for _, v := range rows(packRaw["alchimie"]) {
		sourceRecords[text(object(v)["id"])] = v
	}
	eligible := map[string]any{}
	for _, item := range data.PackItems {
		if item.Game == "alchimie" && item.PilotEligible {
			eligible[item.ID] = &item
		}
	}
	type coreEntry struct {
		raw        map[string]any
		core       map[string]any
		projection *alchimie.Projection
		concepts   map[string]bool
	}
	cores := map[string]coreEntry{}
	for _, v := range rows(candidate["boards"]) {
		board := object(v)
		id := text(board["id"])
		if _, ok := eligible[id]; !ok || cores[id].core != nil {
			return nil, fmt.Errorf("unknown/duplicate archived extension board")
		}
		source := object(sourceRecords[id])
		payload := source
		seeds := ids(payload["seeds"])
		target, category := text(payload["target"]), text(source["category"])
		if !same(board["source_record"], source) || board["source_record_sha256"] != digest(source) {
			return nil, fmt.Errorf("archived source record changed")
		}
		p := alchimie.BuildProjection(g, seeds, target, category)
		if p == nil {
			return nil, fmt.Errorf("current projection unavailable")
		}
		before := object(board["before_core"])
		if board["before_core_sha256"] != digest(before) || integer(before["par"]) != p.Par {
			return nil, fmt.Errorf("archived projection fingerprint/par changed")
		}
		labelledPair := func(v any) (alchimie.Pair, []string, bool) {
			r := object(v)
			pair := rows(r["pair"])
			if len(pair) != 2 {
				return alchimie.Pair{}, nil, false
			}
			idsPair := alchimie.Pair{text(object(pair[0])["id"]), text(object(pair[1])["id"])}
			outputs := []string{}
			for _, v := range rows(r["results"]) {
				outputs = append(outputs, text(object(v)["id"]))
			}
			return idsPair, outputs, true
		}
		recipes := rows(before["recipes"])
		if len(recipes) != len(p.Recipes) {
			return nil, fmt.Errorf("archived core recipe count changed")
		}
		for _, v := range recipes {
			pair, outputs, ok := labelledPair(v)
			if !ok || !same(outputs, p.Recipes[pair]) {
				return nil, fmt.Errorf("archived core recipes differ")
			}
		}
		nativeRoutes := []any{}
		for _, v := range rows(before["routes"]) {
			route := []any{}
			for _, v := range rows(v) {
				pair, outputs, ok := labelledPair(v)
				if !ok {
					return nil, fmt.Errorf("archived route shape")
				}
				route = append(route, map[string]any{"pair": pair, "results": outputs})
			}
			nativeRoutes = append(nativeRoutes, route)
		}
		if !same(nativeRoutes, p.Routes) {
			return nil, fmt.Errorf("archived core routes differ")
		}
		concepts := map[string]bool{}
		for _, v := range rows(before["concepts"]) {
			n := object(v)
			nid := text(n["id"])
			if !same(n, concept(g, nid)) || concepts[nid] {
				return nil, fmt.Errorf("archived labels or concepts differ")
			}
			concepts[nid] = true
		}
		for _, seed := range seeds {
			if !concepts[seed] {
				return nil, fmt.Errorf("seed missing from core concept scope")
			}
		}
		for pair, results := range p.Recipes {
			for _, id := range append(pair[:], results...) {
				if !concepts[id] {
					return nil, fmt.Errorf("recipe concept missing from scope")
				}
			}
		}
		cores[id] = coreEntry{board, projectionCore(p, seeds, target, category), p, concepts}
	}
	if len(cores) != len(eligible) {
		return nil, fmt.Errorf("complete selectable board/core coverage required")
	}
	accepted := acceptedIDs(reviews)
	options := map[string][]map[string]any{}
	for _, v := range rows(candidate["candidates"]) {
		row := object(v)
		id, bid := text(row["id"]), text(row["board_id"])
		copy := clone(row).(map[string]any)
		delete(copy, "candidate_sha256")
		if row["candidate_sha256"] != digest(copy) {
			return nil, fmt.Errorf("extension candidate changed")
		}
		entry, ok := cores[bid]
		if !ok || row["before_core_sha256"] != entry.raw["before_core_sha256"] {
			return nil, fmt.Errorf("extension core binding changed")
		}
		pairRows := rows(row["pair"])
		if len(pairRows) != 2 {
			return nil, fmt.Errorf("extension pair cardinality")
		}
		pair := []string{text(object(pairRows[0])["id"]), text(object(pairRows[1])["id"])}
		result := text(object(row["result"])["id"])
		identity := map[string]any{"board_id": bid, "pair": pair, "result": result}
		if id != "alrecipe-"+bid+"-"+digest(identity)[:16] || pair[0] >= pair[1] || entry.projection.Recipes[alchimie.Pair{pair[0], pair[1]}] != nil || !entry.concepts[pair[0]] || !entry.concepts[pair[1]] || !entry.concepts[result] || result == pair[0] || result == pair[1] {
			return nil, fmt.Errorf("extension identity/absent-pair scope")
		}
		seeds := ids(entry.core["seeds"])
		contains := func(xs []string, s string) bool {
			for _, x := range xs {
				if x == s {
					return true
				}
			}
			return false
		}
		target := text(entry.core["target"])
		if contains(seeds, result) || contains(pair, target) {
			return nil, fmt.Errorf("extension result/target cohort scope")
		}
		cohorts := []string{}
		if contains(seeds, pair[0]) && contains(seeds, pair[1]) {
			cohorts = append(cohorts, "missing_seed_pair")
		}
		if result == target {
			cohorts = append(cohorts, "missing_target_pair")
		}
		if len(cohorts) == 0 || !same(cohorts, row["cohorts"]) || row["category"] != entry.core["category"] || !same(row["par"], entry.core["par"]) {
			return nil, fmt.Errorf("extension cohort/category/par changed")
		}
		candidateSeeds := []string{}
		for _, v := range rows(row["seeds"]) {
			candidateSeeds = append(candidateSeeds, text(object(v)["id"]))
		}
		if !same(candidateSeeds, seeds) || object(row["target"])["id"] != target {
			return nil, fmt.Errorf("extension seed/target binding changed")
		}
		for _, v := range append(append(append([]any{}, pairRows...), row["result"], row["target"]), rows(row["seeds"])...) {
			n := object(v)
			if !same(n, concept(g, text(n["id"]))) {
				return nil, fmt.Errorf("extension label/context differs")
			}
		}
		if !contains(g.CommonNeighbors(pair[0], pair[1], text(entry.core["category"])), result) {
			return nil, fmt.Errorf("extension result not in scoped graph")
		}
		edges := rows(row["edges"])
		if len(edges) != 2 {
			return nil, fmt.Errorf("two archived edges required")
		}
		kg, err := fixture(root, "kg_sample.json")
		if err != nil {
			return nil, err
		}
		fixtureEdges := map[string]any{}
		for _, v := range rows(kg["kg_edges"]) {
			fixtureEdges[text(object(v)["id"])] = v
		}
		for i, parent := range pair {
			edge := g.Link(parent, result)
			archived := object(edges[i])
			if edge == nil || edge.IsDistractor || edge.Strength < .7 || !same(archived["runtime_edge"], contentbuild.EdgeSnapshot(edge)) || !same(archived["fixture_edge"], fixtureEdges[edge.ID]) || archived["fixture_edge_sha256"] != digest(fixtureEdges[edge.ID]) {
				return nil, fmt.Errorf("extension edge metadata/provenance differs")
			}
		}
		if accepted[id] {
			key := bid + "\x00" + strings.Join(pair, "\x00")
			options[key] = append(options[key], row)
		}
	}
	diagnostics := []any{}
	added := map[string][]any{}
	for _, key := range sortedKeysAny(options) {
		choices := options[key]
		row := choices[0]
		bid := text(row["board_id"])
		pair := []string{text(object(rows(row["pair"])[0])["id"]), text(object(rows(row["pair"])[1])["id"])}
		if len(choices) != 1 {
			ids := []string{}
			for _, row := range choices {
				ids = append(ids, text(row["id"]))
			}
			sort.Strings(ids)
			diagnostics = append(diagnostics, map[string]any{"board_id": bid, "pair": pair, "reason": "competing accepted outputs; all dropped", "candidate_ids": ids})
			continue
		}
		eids := []string{}
		for _, v := range rows(row["edges"]) {
			eids = append(eids, text(object(object(v)["runtime_edge"])["id"]))
		}
		added[bid] = append(added[bid], map[string]any{"candidate_id": row["id"], "candidate_sha256": row["candidate_sha256"], "pair": pair, "result": object(row["result"])["id"], "edge_ids": eids})
	}
	boards := []any{}
	keys := []string{}
	for key := range added {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, bid := range keys {
		entry := cores[bid]
		nodes, edges := map[string]any{}, map[string]any{}
		for nid := range entry.concepts {
			nodes[nid] = contentbuild.NodeSnapshot(g.Node(nid))
		}
		for pair, results := range entry.projection.Recipes {
			for _, result := range results {
				for _, parent := range pair {
					edge := g.Link(parent, result)
					if edge == nil {
						return nil, fmt.Errorf("core edge missing")
					}
					edges[edge.ID] = contentbuild.EdgeSnapshot(edge)
				}
			}
		}
		for _, v := range added[bid] {
			a := object(v)
			for _, parent := range ids(a["pair"]) {
				e := g.Link(parent, text(a["result"]))
				edges[e.ID] = contentbuild.EdgeSnapshot(e)
			}
		}
		board := map[string]any{"id": bid, "core": entry.core, "core_sha256": digest(entry.core), "nodes": nodes, "edges": edges, "additions": added[bid]}
		board["entry_sha256"] = digest(board)
		boards = append(boards, board)
	}
	out := map[string]any{"schema": "alchimie-recipe-extensions-v1", "candidate_sha256": candidateSHA, "bindings": map[string]any{"kg": object(candidate["bindings"])["kg"], "pack": object(candidate["bindings"])["pack"], "rubric": object(candidate["bindings"])["rubric"]}, "semantic_reviews": reviewDescriptors(reviews, false), "boards": boards, "diagnostics": diagnostics}
	out = clone(out).(map[string]any)
	if err = contentbuild.ValidateRecipeExtensions(out); err != nil {
		return nil, err
	}
	return out, nil
}
func sortedKeysAny(m map[string][]map[string]any) []string {
	out := []string{}
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
func auditExtensions(root string, raw map[string]any) (map[string]any, error) {
	if err := contentbuild.ValidateRecipeExtensions(raw); err != nil {
		return nil, err
	}
	g, err := sourceGraph(root)
	if err != nil {
		return nil, err
	}
	replayed, additions := 0, 0
	for _, v := range rows(raw["boards"]) {
		board := object(v)
		core := object(board["core"])
		seeds := ids(core["seeds"])
		target, category := text(core["target"]), text(core["category"])
		p := alchimie.BuildProjection(g, seeds, target, category)
		if p == nil || !same(projectionCore(p, seeds, target, category), core) {
			return nil, fmt.Errorf("native core/route audit differs")
		}
		merged := map[alchimie.Pair][]string{}
		for pair, out := range p.Recipes {
			merged[pair] = out
		}
		for _, v := range rows(board["additions"]) {
			a := object(v)
			pair := ids(a["pair"])
			merged[alchimie.Pair{pair[0], pair[1]}] = []string{text(a["result"])}
			additions++
		}
		plan := alchimie.MinimumPlan(seeds, target, merged, 6)
		if plan == nil || len(plan) != integer(core["par"]) {
			return nil, fmt.Errorf("extension changes optimal par")
		}
		for nid, snapshot := range object(board["nodes"]) {
			if !same(snapshot, contentbuild.NodeSnapshot(g.Node(nid))) {
				return nil, fmt.Errorf("extension node provenance drift")
			}
		}
		for _, snapshot := range object(board["edges"]) {
			e := object(snapshot)
			edge := g.Link(text(e["src_id"]), text(e["dst_id"]))
			if !same(snapshot, contentbuild.EdgeSnapshot(edge)) {
				return nil, fmt.Errorf("extension edge provenance drift")
			}
		}
		replayed++
	}
	return map[string]any{"kind": "alchimie-recipe-extension-native-audit-v1", "verdict": "accept", "candidate_sha256": raw["candidate_sha256"], "boards_replayed": replayed, "additions_replayed": additions, "unchanged_cores_routes_par": true, "graph_provenance_preserved": true}, nil
}
