package contentrails

import (
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/alchimie_explore"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"net/url"
	"path/filepath"
	"sort"
	"strings"
)

func worldCandidate(root string, s *Source, historical bool) (map[string]any, error) {
	return worldCandidateForPhase(root, s, historical, false)
}

// Installed reconstruction checks the completed candidate against the installed
// world. Staging instead requires its immutable predecessor to remain current.
func worldCandidateForPhase(root string, s *Source, historical, installed bool) (map[string]any, error) {
	g, err := sourceGraph(root)
	if err != nil {
		return nil, err
	}
	src := object(s.Raw["world"])
	byLabel := map[string][]string{}
	surfaces := map[string]bool{}
	for _, id := range g.AllIDs() {
		n := g.Node(id)
		byLabel[n.LabelRO] = append(byLabel[n.LabelRO], id)
		for _, label := range append([]string{n.LabelRO}, n.Aliases...) {
			surfaces[contentbuild.Normalize(label)] = true
		}
	}
	authored := map[string]any{}
	for label, v := range object(src["world_concepts"]) {
		definition := object(v)
		id := text(definition["id"])
		refs := rows(definition["sources"])
		if id == "" || len(definition) != 3 || surfaces[contentbuild.Normalize(label)] || len(refs) < 1 || len(refs) > 8 || !validSources(refs) {
			return nil, fmt.Errorf("authored world definition shadows source or lacks provenance")
		}
		snapshot := map[string]any{"id": id, "label": label, "description": definition["description"], "source": "authored:alchimie", "redistributable": false, "references": refs}
		if authored[id] != nil {
			return nil, fmt.Errorf("duplicate authored world concept")
		}
		authored[id] = map[string]any{"id": id, "label": label, "description": definition["description"], "source": "authored:alchimie", "redistributable": false, "origin": "authored", "references": refs, "snapshot": snapshot}
		byLabel[label] = []string{id}
		surfaces[contentbuild.Normalize(label)] = true
	}
	resolve := func(label string) (string, error) {
		found := byLabel[label]
		if len(found) != 1 {
			return "", fmt.Errorf("unknown or ambiguous authored label: %s", label)
		}
		return found[0], nil
	}
	used := map[string]bool{}
	convert := func(raw any) ([]string, error) {
		out := []string{}
		for _, label := range ids(raw) {
			id, err := resolve(label)
			if err != nil {
				return nil, err
			}
			out = append(out, id)
			used[id] = true
		}
		return out, nil
	}
	starters, err := convert(src["starters"])
	if err != nil {
		return nil, err
	}
	recipes := []any{}
	for _, v := range rows(src["recipes"]) {
		r := rows(v)
		if len(r) != 5 {
			return nil, fmt.Errorf("recipe authoring row requires five fields")
		}
		pair, err := convert([]any{r[1], r[2]})
		if err != nil {
			return nil, err
		}
		sort.Strings(pair)
		result, err := resolve(text(r[3]))
		if err != nil {
			return nil, err
		}
		used[result] = true
		rid := text(r[0])
		refs := object(src["recipe_sources"])[rid]
		if refs == nil {
			refs = []string{"https://dexonline.ro/definitie/" + url.PathEscape(g.Casefold(text(r[3])))}
		}
		recipes = append(recipes, map[string]any{"id": rid, "pair": pair, "result": result, "explanation": r[4], "sources": refs})
	}
	unlocks := []any{}
	for _, v := range rows(src["unlocks"]) {
		u := rows(v)
		if len(u) != 4 {
			return nil, fmt.Errorf("invalid authored unlock")
		}
		concepts, err := convert(u[3])
		if err != nil {
			return nil, err
		}
		unlocks = append(unlocks, map[string]any{"id": u[0], "after_discoveries": u[1], "title": u[2], "concept_ids": concepts})
	}
	goals := []any{}
	for _, v := range rows(src["goals"]) {
		goal := rows(v)
		if len(goal) != 3 {
			return nil, fmt.Errorf("invalid authored goal")
		}
		target, err := resolve(text(goal[1]))
		if err != nil {
			return nil, err
		}
		goals = append(goals, map[string]any{"id": goal[0], "target": target, "title": goal[2]})
	}
	for id := range authored {
		if !used[id] {
			return nil, fmt.Errorf("unused authored definition")
		}
	}
	concepts := []any{}
	keys := []string{}
	for id := range used {
		keys = append(keys, id)
	}
	sort.Strings(keys)
	for _, id := range keys {
		if a := authored[id]; a != nil {
			concepts = append(concepts, a)
			continue
		}
		n := g.Node(id)
		description := n.Description
		if d := object(src["descriptions"])[n.LabelRO]; d != nil {
			description = text(d)
		}
		concepts = append(concepts, map[string]any{"id": id, "label": n.LabelRO, "description": description, "source": n.Source, "redistributable": n.Redistributable, "snapshot": contentbuild.NodeSnapshot(n)})
	}
	bind, err := bindings(root)
	if err != nil {
		return nil, err
	}
	previousName := "world_previous"
	if !historical {
		previousName = "world_candidate"
	}
	previous, err := archive(root, s, previousName)
	if err != nil {
		return nil, err
	}
	if !historical && !installed {
		if err = previousMatchesCurrent(root, previous); err != nil {
			return nil, err
		}
	}
	world := clone(src["world"]).(map[string]any)
	world["starter_ids"] = starters
	oldBind := map[string]any{"kg_sha256": bind["kg_sample.json"], "rubric_sha256": bind["rubric"], "editorial_source_sha256": s.SHA256, "previous_world_sha256": object(object(s.Raw["archives"])[previousName])["sha256"]}
	if historical {
		old, err := archive(root, s, "world_candidate")
		if err != nil {
			return nil, err
		}
		oldBind = clone(old["bindings"]).(map[string]any)
	}
	out := map[string]any{"schema_version": 1, "kind": "alchimie-discovery-world-candidates-v1", "world": world, "bindings": oldBind, "concepts": concepts, "recipes": recipes, "unlocks": unlocks, "goals": goals}
	versions, err := compatibleVersions(previous, out, text(oldBind["previous_world_sha256"]))
	if err != nil {
		return nil, err
	}
	out["compatible_versions"] = versions
	if !historical {
		out["native_source_version"] = s.Version
	}
	if installed {
		if err = previousMatchesCurrent(root, out); err != nil {
			return nil, fmt.Errorf("installed world differs from reconstructed candidate/history: %w", err)
		}
	}
	return out, nil
}
func mechanics(raw map[string]any) map[string]any {
	starters := ids(object(raw["world"])["starter_ids"])
	sort.Strings(starters)
	recipes := []any{}
	for _, v := range rows(raw["recipes"]) {
		r := object(v)
		recipes = append(recipes, map[string]any{"pair": r["pair"], "result": r["result"]})
	}
	sort.Slice(recipes, func(i, j int) bool {
		return strings.Join(ids(object(recipes[i])["pair"]), "\x00") < strings.Join(ids(object(recipes[j])["pair"]), "\x00")
	})
	unlocks := []any{}
	for _, v := range rows(raw["unlocks"]) {
		u := object(v)
		concepts := ids(u["concept_ids"])
		sort.Strings(concepts)
		unlocks = append(unlocks, map[string]any{"after": u["after_discoveries"], "concepts": concepts})
	}
	sort.Slice(unlocks, func(i, j int) bool {
		a, b := object(unlocks[i]), object(unlocks[j])
		if integer(a["after"]) != integer(b["after"]) {
			return integer(a["after"]) < integer(b["after"])
		}
		return strings.Join(ids(a["concepts"]), "\x00") < strings.Join(ids(b["concepts"]), "\x00")
	})
	return map[string]any{"starters": starters, "recipes": recipes, "unlocks": unlocks}
}
func compatibleVersions(old, current map[string]any, sourceSHA string) ([]any, error) {
	if object(old["world"])["id"] != object(current["world"])["id"] || !same(object(old["world"])["starter_ids"], object(current["world"])["starter_ids"]) {
		return nil, fmt.Errorf("world identity/original starters changed")
	}
	for _, key := range []string{"unlocks", "goals"} {
		for _, v := range rows(old[key]) {
			found := false
			for _, now := range rows(current[key]) {
				found = found || same(v, now)
			}
			if !found {
				return nil, fmt.Errorf("original %s changed", key)
			}
		}
	}
	currentIDs := map[string]bool{}
	for _, v := range rows(current["concepts"]) {
		currentIDs[text(object(v)["id"])] = true
	}
	for _, v := range rows(old["concepts"]) {
		if !currentIDs[text(object(v)["id"])] {
			return nil, fmt.Errorf("historical concept removed")
		}
	}
	currentPairs := map[string]string{}
	for _, v := range rows(current["recipes"]) {
		r := object(v)
		currentPairs[strings.Join(ids(r["pair"]), "\x00")] = text(r["result"])
	}
	for _, v := range rows(old["recipes"]) {
		r := object(v)
		if currentPairs[strings.Join(ids(r["pair"]), "\x00")] != text(r["result"]) {
			return nil, fmt.Errorf("historical recipe result changed")
		}
	}
	versions := clone(rows(old["compatible_versions"])).([]any)
	m := mechanics(old)
	if digest(m) != digest(mechanics(current)) {
		versions = append(versions, map[string]any{"world_id": object(old["world"])["id"], "recipe_hash": digest(m), "source_sha256": sourceSHA, "mechanics": m})
	}
	if len(versions) > 16 {
		return nil, fmt.Errorf("compatible history cap")
	}
	seen := map[string]bool{}
	for _, v := range versions {
		hash := text(object(v)["recipe_hash"])
		if hash == "" || seen[hash] {
			return nil, fmt.Errorf("duplicate compatibility history")
		}
		seen[hash] = true
	}
	return versions, nil
}
func buildWorld(root string, s *Source, candidate map[string]any, candidateSHA string, reviews []Review) (map[string]any, error) {
	accepted := acceptedIDs(reviews)
	for _, v := range rows(candidate["recipes"]) {
		if !accepted[text(object(v)["id"])] {
			return nil, fmt.Errorf("every world recipe must pass both independent reviews")
		}
	}
	for _, review := range reviews {
		if review.Raw["world_verdict"] != "accept" || strings.TrimSpace(text(review.Raw["world_rationale"])) == "" {
			return nil, fmt.Errorf("world/supply/goal acceptance required")
		}
		conceptReview := map[string]any{}
		for _, v := range rows(review.Raw["concepts"]) {
			row := object(v)
			id := text(row["id"])
			if conceptReview[id] != nil {
				return nil, fmt.Errorf("duplicate concept review")
			}
			conceptReview[id] = row
		}
		if len(conceptReview) != len(rows(candidate["concepts"])) {
			return nil, fmt.Errorf("complete concept coverage required")
		}
		old, err := archive(root, s, "world_previous")
		if err != nil {
			return nil, err
		}
		previous := map[string]any{}
		for _, v := range rows(old["concepts"]) {
			previous[text(object(v)["id"])] = v
		}
		for _, v := range rows(candidate["concepts"]) {
			c := object(v)
			r := object(conceptReview[text(c["id"])])
			b, _ := Render(c)
			if !allowedKeys(r, "id", "concept_sha256", "verdict", "rationale", "sources", "inherited") || !sourcesValue(r["sources"]) || r["concept_sha256"] != contentbuild.SHA256(b) || r["verdict"] != "accept" || strings.TrimSpace(text(r["rationale"])) == "" || !validSources(rows(r["sources"])) {
				return nil, fmt.Errorf("altered/missing concept judgment")
			}
			inherited, ok := r["inherited"].(bool)
			if r["inherited"] != nil && !ok {
				return nil, fmt.Errorf("invalid inheritance declaration")
			}
			if inherited && !same(previous[text(c["id"])], c) {
				return nil, fmt.Errorf("changed inherited concept")
			}
			if !inherited && review.Role == "factual" && len(rows(r["sources"])) == 0 {
				return nil, fmt.Errorf("new factual concept needs checked sources")
			}
		}
	}
	out := clone(candidate).(map[string]any)
	delete(out, "kind")
	out["candidate_sha256"] = candidateSHA
	out["reviews"] = reviewDescriptors(reviews, true)
	factual := reviews[0]
	byID := map[string]any{}
	for _, v := range rows(factual.Raw["items"]) {
		byID[text(object(v)["id"])] = v
	}
	for _, v := range rows(out["recipes"]) {
		r := object(v)
		sources := ids(object(byID[text(r["id"])])["sources"])
		sort.Strings(sources)
		unique := []string{}
		for _, source := range sources {
			if len(unique) == 0 || unique[len(unique)-1] != source {
				unique = append(unique, source)
			}
		}
		r["sources"] = unique
	}
	g, err := sourceGraph(root)
	if err != nil {
		return nil, err
	}
	out = clone(out).(map[string]any)
	if _, err = contentbuild.ValidateDiscoveryWorld(out, g); err != nil {
		return nil, err
	}
	return out, nil
}
func auditWorld(root string, raw map[string]any) (map[string]any, error) {
	if errors := contentbuild.ValidateFixture(filepath.Join(root, "cat_de_roman_esti/fixtures/kg_sample.json")); len(errors) != 0 {
		return nil, fmt.Errorf("prospective world source fixture invalid: %s", strings.Join(errors[:min(len(errors), 8)], "; "))
	}
	g, err := sourceGraph(root)
	if err != nil {
		return nil, err
	}
	normalized, err := contentbuild.ValidateDiscoveryWorld(raw, g)
	if err != nil {
		return nil, err
	}
	// The source root can intentionally contain an old installed world while
	// its graph and a separately reviewed prospective world are being staged.
	// Use a fresh sealed serving snapshot only inside this audit, then overlay
	// the independently parsed source graph and the validated prospective world.
	// Export/startup continue to require coherent reviewed installed sources.
	data, err := content.Load()
	if err != nil {
		return nil, err
	}
	data.Nodes = g.Content.Nodes
	data.Edges = g.Content.Edges
	data.Labels = g.Content.Labels
	data.CategoryLabels = g.Content.CategoryLabels
	data.NormalizedIndex = g.Content.NormalizedIndex
	data.DiscoveryWorld = normalized
	recipes := rows(raw["recipes"])
	goalIDs := []*string{nil}
	for _, v := range rows(raw["goals"]) {
		id := text(object(v)["id"])
		goalIDs = append(goalIDs, &id)
	}
	goalResults := []any{}
	var reference any
	for _, goal := range goalIDs {
		svc := alchimie_explore.New(data)
		state, e := svc.Create(nil, goal)
		if e != nil {
			return nil, e
		}
		sid := text(state["game_id"])
		for _, v := range state["goals"].([]any) {
			if object(v)["target_id"] != nil {
				return nil, fmt.Errorf("undiscovered target leaked")
			}
		}
		for action := 0; action < 256; action++ {
			owned := ownedIDs(state)
			var chosen map[string]any
			for _, v := range recipes {
				r := object(v)
				pair := ids(r["pair"])
				if owned[pair[0]] && owned[pair[1]] && !owned[text(r["result"])] {
					chosen = r
					break
				}
			}
			if chosen == nil {
				break
			}
			pair := ids(chosen["pair"])
			state, e = svc.Combine(sid, pair[0], pair[1])
			if e != nil {
				return nil, e
			}
			if len(state["discovered"].([]any)) != 1 {
				return nil, fmt.Errorf("world productive recipe failed")
			}
		}
		if state["complete"] != true || len(ownedIDs(state)) != len(rows(raw["concepts"])) {
			return nil, fmt.Errorf("world full closure replay failed")
		}
		checkpoint := clone(state["progress"])
		if reference != nil && !same(reference, checkpoint) {
			return nil, fmt.Errorf("goal-dependent recipe mechanics")
		}
		reference = checkpoint
		for _, v := range recipes {
			r := object(v)
			pair := ids(r["pair"])
			repeated, e := svc.Combine(sid, pair[0], pair[1])
			if e != nil || len(repeated["discovered"].([]any)) != 0 {
				return nil, fmt.Errorf("repeated recipe discovery drift")
			}
		}
		restored, e := svc.Create(object(checkpoint), nil)
		if e != nil || !same(restored["progress"], checkpoint) || !same(ownedIDs(restored), ownedIDs(state)) {
			return nil, fmt.Errorf("complete restore drift")
		}
		goalResults = append(goalResults, map[string]any{"goal_id": goal, "complete": true, "all_recipes_consistent": true, "replayed_discoveries": integer(state["discovered_count"])})
	}
	histories := []any{}
	prefixes := 0
	for _, v := range rows(raw["compatible_versions"]) {
		version := object(v)
		m := object(version["mechanics"])
		owned := map[string]bool{}
		for _, id := range ids(m["starters"]) {
			owned[id] = true
		}
		pairs := []any{}
		svc := alchimie_explore.New(data)
		for action := 0; action < 256; action++ {
			var next map[string]any
			for _, v := range rows(m["recipes"]) {
				r := object(v)
				p := ids(r["pair"])
				if owned[p[0]] && owned[p[1]] && !owned[text(r["result"])] {
					next = r
					break
				}
			}
			if next == nil {
				break
			}
			pairs = append(pairs, clone(next["pair"]))
			owned[text(next["result"])] = true
			for _, u := range rows(m["unlocks"]) {
				unlock := object(u)
				if len(pairs) >= integer(unlock["after"]) {
					for _, id := range ids(unlock["concepts"]) {
						owned[id] = true
					}
				}
			}
			checkpoint := map[string]any{"world_id": version["world_id"], "recipe_hash": version["recipe_hash"], "discoveries": clone(pairs)}
			state, e := svc.Create(checkpoint, nil)
			if e != nil {
				return nil, e
			}
			newOwned := ownedIDs(state)
			for id := range owned {
				if !newOwned[id] {
					return nil, fmt.Errorf("historical prefix lost earned concept")
				}
			}
			if !same(object(state["progress"])["discoveries"], pairs) {
				return nil, fmt.Errorf("historical discoveries changed")
			}
			prefixes++
		}
		histories = append(histories, map[string]any{"recipe_hash": version["recipe_hash"], "prefixes_preserved": len(pairs), "previous_owned": len(owned), "all_earned_concepts_preserved": true})
	}
	return map[string]any{"kind": "alchimie-discovery-world-audit-v1", "verdict": "accept", "candidate_sha256": raw["candidate_sha256"], "world_id": object(raw["world"])["id"], "goal_replays": goalResults, "compatible_save_replays": histories, "historical_prefixes": prefixes, "metrics": map[string]any{"concepts": len(rows(raw["concepts"])), "recipes": len(recipes), "optional_goals": len(rows(raw["goals"])), "historical_books": len(histories)}, "checks": map[string]any{"all_concepts_reachable": true, "all_goals_reachable": true, "goal_independent_recipes": true, "complete_replay_restoration": true, "undiscovered_target_ids_hidden": true, "recipes_private": true}}, nil
}
func ownedIDs(state map[string]any) map[string]bool {
	out := map[string]bool{}
	if state == nil {
		return out
	}
	for _, v := range state["inventory"].([]any) {
		out[text(object(v)["id"])] = true
	}
	return out
}

func previousMatchesCurrent(root string, previous map[string]any) error {
	current, err := fixture(root, "alchimie_discovery_world_v92.json")
	if err != nil {
		return err
	}
	if object(previous["world"])["id"] != object(current["world"])["id"] || !same(mechanics(previous), mechanics(current)) || !same(previous["compatible_versions"], current["compatible_versions"]) {
		return fmt.Errorf("previous immutable archive is stale for currently installed world/history")
	}
	return nil
}
