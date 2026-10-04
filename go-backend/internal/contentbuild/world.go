package contentbuild

import (
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"regexp"
	"sort"
	"strings"
)

func mechanics(starters any, recipes []any, unlocks []any) map[string]any {
	ss := stringsOf(starters)
	sort.Strings(ss)
	rs := []any{}
	for _, v := range recipes {
		m := object(v)
		pair := stringsOf(m["pair"])
		sort.Strings(pair)
		rs = append(rs, map[string]any{"pair": pair, "result": m["result"]})
	}
	sort.Slice(rs, func(i, j int) bool {
		a, b := stringsOf(object(rs[i])["pair"]), stringsOf(object(rs[j])["pair"])
		return strings.Join(a, "\x00") < strings.Join(b, "\x00")
	})
	us := []any{}
	for _, v := range unlocks {
		m := object(v)
		after, cs := m["after_discoveries"], m["concept_ids"]
		if after == nil {
			after = m["after"]
			cs = m["concepts"]
		}
		ids := stringsOf(cs)
		sort.Strings(ids)
		us = append(us, map[string]any{"after": after, "concepts": ids})
	}
	sort.Slice(us, func(i, j int) bool {
		a, b := object(us[i]), object(us[j])
		if number(a["after"]) != number(b["after"]) {
			return number(a["after"]) < number(b["after"])
		}
		return strings.Join(stringsOf(a["concepts"]), "\x00") < strings.Join(stringsOf(b["concepts"]), "\x00")
	})
	return map[string]any{"starters": ss, "recipes": rs, "unlocks": us}
}
func asciiDigest(v any) string {
	b, e := Canonical(v)
	if e != nil {
		return ""
	}
	var out strings.Builder
	for _, c := range string(b) {
		if c < 127 {
			out.WriteRune(c)
		} else if c <= 0xffff {
			fmt.Fprintf(&out, "\\u%04x", c)
		} else {
			n := c - 0x10000
			fmt.Fprintf(&out, "\\u%04x\\u%04x", 0xd800+(n>>10), 0xdc00+(n&0x3ff))
		}
	}
	return SHA256([]byte(out.String()))
}

func reachMechanics(m map[string]any) (map[string]bool, int) {
	owned, crafted := map[string]bool{}, map[string]bool{}
	for _, id := range stringsOf(m["starters"]) {
		owned[id] = true
	}
	for {
		before := len(owned)
		for _, v := range array(m["recipes"]) {
			r := object(v)
			pair := stringsOf(r["pair"])
			if len(pair) == 2 && owned[pair[0]] && owned[pair[1]] && !owned[str(r["result"])] {
				id := str(r["result"])
				owned[id] = true
				crafted[id] = true
			}
		}
		for _, v := range array(m["unlocks"]) {
			u := object(v)
			if len(crafted) >= int(number(u["after"])) {
				for _, id := range stringsOf(u["concepts"]) {
					owned[id] = true
				}
			}
		}
		if len(owned) == before {
			return owned, len(crafted)
		}
	}
}
func validateWorld(raw map[string]any, g *graph.Service) (map[string]any, error) {
	fail := func(s string) (map[string]any, error) { return nil, fmt.Errorf("discovery world: %s", s) }
	if err := strictWorldRecords(raw); err != nil {
		return fail(err.Error())
	}
	if number(raw["schema_version"]) != 1 || len(array(raw["concepts"])) < 3 || len(array(raw["concepts"])) > 256 || len(array(raw["recipes"])) < 2 || len(array(raw["recipes"])) > 512 || len(array(raw["goals"])) > 32 || len(array(raw["unlocks"])) > 12 || len(array(raw["compatible_versions"])) > 16 || !sha(raw["candidate_sha256"]) || !independentReviews(raw["reviews"]) {
		return fail("schema/review/bounds")
	}
	for _, v := range array(raw["reviews"]) {
		if object(v)["candidate_sha256"] != raw["candidate_sha256"] {
			return fail("review candidate mismatch")
		}
	}
	bind := object(raw["bindings"])
	if !sha(bind["kg_sha256"]) || !sha(bind["rubric_sha256"]) {
		return fail("source bindings")
	}
	world := object(raw["world"])
	if !exact(world, "id", "title", "description", "starter_ids") || str(world["id"]) == "" || len(array(world["starter_ids"])) < 2 || len(array(world["starter_ids"])) > 12 {
		return fail("world record")
	}
	concepts := map[string]map[string]any{}
	labels := map[string]bool{}
	conceptRows := []any{}
	authoredID := regexp.MustCompile(`^alw_food_[a-z0-9_]+$`)
	for _, v := range array(raw["concepts"]) {
		c := copyObject(object(v))
		if c["origin"] == nil {
			c["origin"] = "kg"
		}
		if c["references"] == nil {
			c["references"] = []any{}
		}
		id := str(c["id"])
		label := Normalize(str(c["label"]))
		if !exact(c, "id", "label", "description", "source", "redistributable", "snapshot", "origin", "references") || id == "" || concepts[id] != nil || label == "" || labels[label] || len(array(c["references"])) > 8 {
			return fail("concept schema/identity")
		}
		if _, ok := c["redistributable"].(bool); !ok {
			return fail("concept redistribution boolean")
		}
		concepts[id] = c
		labels[label] = true
		conceptRows = append(conceptRows, c)
		if c["origin"] == "authored" {
			if !authoredID.MatchString(id) || len(strings.TrimSpace(str(c["description"]))) == 0 || len(str(c["description"])) > 2000 || len(array(c["references"])) == 0 || c["source"] != "authored:alchimie" || c["redistributable"] != false {
				return fail("authored definition provenance")
			}
			for _, v := range array(c["references"]) {
				if !validReference(v) {
					return fail("authored reference")
				}
			}
			want := map[string]any{"id": id, "label": c["label"], "description": c["description"], "source": "authored:alchimie", "redistributable": false, "references": c["references"]}
			if !equal(c["snapshot"], want) || g.Exists(id) || g.Resolve(str(c["label"])) != "" {
				return fail("authored provenance or KG shadow")
			}
		} else if c["origin"] == "kg" {
			n := g.Node(id)
			if n == nil || !equal(c["snapshot"], nodeMap(*n)) || c["label"] != n.LabelRO || c["source"] != n.Source || c["redistributable"] != n.Redistributable {
				return fail("concept source/presentation drift")
			}
		} else {
			return fail("unknown concept origin")
		}
	}
	supplied := map[string]bool{}
	for _, id := range stringsOf(world["starter_ids"]) {
		if supplied[id] || concepts[id] == nil {
			return fail("invalid/duplicate starter")
		}
		supplied[id] = true
	}
	unlockIDs := map[string]bool{}
	for _, v := range array(raw["unlocks"]) {
		u := object(v)
		after, ok := integer(u["after_discoveries"])
		id := str(u["id"])
		if !exact(u, "id", "after_discoveries", "concept_ids", "title") || id == "" || unlockIDs[id] || !ok || after < 1 || after > 256 || len(array(u["concept_ids"])) < 1 || len(array(u["concept_ids"])) > 12 {
			return fail("unlock record")
		}
		unlockIDs[id] = true
		for _, n := range stringsOf(u["concept_ids"]) {
			if supplied[n] || concepts[n] == nil {
				return fail("duplicate/unknown supply")
			}
			supplied[n] = true
		}
	}
	if len(supplied)-len(array(world["starter_ids"])) > 96 {
		return fail("supply bound")
	}
	recipeIDs, pairs := map[string]bool{}, map[string]string{}
	for _, v := range array(raw["recipes"]) {
		m := object(v)
		pair := stringsOf(m["pair"])
		id := str(m["id"])
		if !exact(m, "id", "pair", "result", "explanation", "sources") || len(pair) != 2 || id == "" || recipeIDs[id] || str(m["explanation"]) == "" || len(array(m["sources"])) < 1 || len(array(m["sources"])) > 8 {
			return fail("recipe schema/id")
		}
		recipeIDs[id] = true
		sort.Strings(pair)
		key := strings.Join(pair, "\x00")
		result := str(m["result"])
		if pair[0] == pair[1] || pairs[key] != "" || concepts[pair[0]] == nil || concepts[pair[1]] == nil || concepts[result] == nil || contains(pair, result) || supplied[result] {
			return fail("recipe pair/result")
		}
		pairs[key] = result
		for _, source := range array(m["sources"]) {
			if !validReference(source) {
				return fail("recipe source URL")
			}
		}
	}
	goals, targets := map[string]bool{}, map[string]bool{}
	for _, v := range array(raw["goals"]) {
		goal := object(v)
		id, target := str(goal["id"]), str(goal["target"])
		if !exact(goal, "id", "target", "title") || id == "" || goals[id] || concepts[target] == nil || targets[target] || supplied[target] || str(goal["title"]) == "" {
			return fail("goal target/id")
		}
		goals[id] = true
		targets[target] = true
	}
	mech := mechanics(world["starter_ids"], array(raw["recipes"]), array(raw["unlocks"]))
	owned, crafted := reachMechanics(mech)
	if len(owned) != len(concepts) {
		return fail("unreachable concepts/supplies")
	}
	for _, v := range array(mech["unlocks"]) {
		if number(object(v)["after"]) > float64(crafted) {
			return fail("unreachable supply threshold")
		}
	}
	for n := range supplied {
		used := false
		for p := range pairs {
			used = used || contains(strings.Split(p, "\x00"), n)
		}
		if !used {
			return fail("unused starter or supply")
		}
	}
	hash := asciiDigest(mech)
	versions := map[string]bool{}
	for _, v := range array(raw["compatible_versions"]) {
		old := object(v)
		m := object(old["mechanics"])
		h := str(old["recipe_hash"])
		if !exact(old, "world_id", "recipe_hash", "source_sha256", "mechanics") || !sha(old["recipe_hash"]) || !sha(old["source_sha256"]) || versions[h] || old["world_id"] != world["id"] || h == hash || !equal(m, mechanics(m["starters"], array(m["recipes"]), array(m["unlocks"]))) || asciiDigest(m) != h {
			return fail("archived mechanics fingerprint/identity")
		}
		versions[h] = true
		if !equal(m["starters"], mech["starters"]) {
			return fail("historical starters changed")
		}
		oldPairs := map[string]bool{}
		expected := map[string]bool{}
		for _, id := range stringsOf(m["starters"]) {
			expected[id] = true
		}
		for _, v := range array(m["recipes"]) {
			r := object(v)
			p := stringsOf(r["pair"])
			if len(p) != 2 {
				return fail("historical pair")
			}
			key := strings.Join(p, "\x00")
			if oldPairs[key] || pairs[key] != str(r["result"]) {
				return fail("historical recipe changed")
			}
			oldPairs[key] = true
			expected[p[0]] = true
			expected[p[1]] = true
			expected[str(r["result"])] = true
		}
		oldSupplies := map[string]bool{}
		for _, v := range array(m["unlocks"]) {
			matched := false
			for _, u := range array(mech["unlocks"]) {
				matched = matched || equal(v, u)
			}
			if !matched {
				return fail("historical supplies changed")
			}
			for _, id := range stringsOf(object(v)["concepts"]) {
				if oldSupplies[id] || contains(stringsOf(m["starters"]), id) {
					return fail("historical duplicate supply")
				}
				oldSupplies[id] = true
				expected[id] = true
			}
		}
		owned, crafted := reachMechanics(m)
		if len(owned) != len(expected) {
			return fail("historical unreachable mechanics")
		}
		for _, v := range array(m["unlocks"]) {
			if number(object(v)["after"]) > float64(crafted) {
				return fail("historical unreachable supplies")
			}
		}
	}
	out := map[string]any{}
	for _, key := range []string{"schema_version", "world", "recipes", "goals", "candidate_sha256", "bindings", "reviews"} {
		out[key] = raw[key]
	}
	out["concepts"] = conceptRows
	out["unlocks"] = array(raw["unlocks"])
	out["compatible_versions"] = array(raw["compatible_versions"])
	out["mechanics"] = mech
	out["recipe_hash"] = hash
	return out, nil
}

// ValidateRecipeExtensions certifies the whole bounded historical recipe catalog.
// Source snapshots are checked at application time by the native recipe service;
// unmatched historical scopes receive no additions, preserving core mechanics.
func ValidateRecipeExtensions(raw map[string]any) error { return validateExtensions(raw, nil) }
func validateExtensions(raw map[string]any, _ *graph.Service) error {
	fail := func(s string) error { return fmt.Errorf("recipe extensions: %s", s) }
	if _, ok := raw["boards"].([]any); !ok {
		return fail("boards must be array")
	}
	if raw["schema"] != "alchimie-recipe-extensions-v1" || !sha(raw["candidate_sha256"]) || !independentReviews(raw["semantic_reviews"]) || len(array(raw["boards"])) > 512 {
		return fail("schema/reviews/bounds")
	}
	for _, name := range []string{"pack", "kg", "rubric"} {
		if !sha(object(object(raw["bindings"])[name])["sha256"]) {
			return fail("source binding")
		}
	}
	ids, cores, candidates := map[string]bool{}, map[string]bool{}, map[string]bool{}
	for _, v := range array(raw["boards"]) {
		b := object(v)
		id := str(b["id"])
		core := object(b["core"])
		fingerprint := str(b["core_sha256"])
		entry := copyObject(b)
		delete(entry, "entry_sha256")
		if id == "" || ids[id] || !sha(b["core_sha256"]) || valueDigest(core) != fingerprint || cores[fingerprint] || valueDigest(entry) != str(b["entry_sha256"]) {
			return fail("board core/entry fingerprint")
		}
		ids[id] = true
		cores[fingerprint] = true
		seeds := stringsOf(core["seeds"])
		seedSet, concepts := map[string]bool{}, map[string]bool{}
		if len(seeds) < 2 || len(seeds) > 32 {
			return fail("seed bound")
		}
		for _, n := range seeds {
			if n == "" || seedSet[n] {
				return fail("duplicate/invalid seed")
			}
			seedSet[n] = true
			concepts[n] = true
		}
		target := str(core["target"])
		par, ok := integer(core["par"])
		if target == "" || seedSet[target] || str(core["category"]) == "" || !ok || par < 1 || par > 6 {
			return fail("target/category/par")
		}
		recipes := array(core["recipes"])
		if len(recipes) < 1 || len(recipes) > 24 {
			return fail("core recipe bound")
		}
		pairs := map[string][]string{}
		for _, v := range recipes {
			r := object(v)
			p, outputs := stringsOf(r["pair"]), stringsOf(r["results"])
			if len(p) != 2 || p[0] == "" || p[0] >= p[1] || len(outputs) < 1 || len(outputs) > 2 {
				return fail("core pair/outputs")
			}
			key := strings.Join(p, "\x00")
			if pairs[key] != nil {
				return fail("duplicate core pair")
			}
			pairs[key] = outputs
			outputSet := map[string]bool{}
			for _, n := range append(append([]string{}, p...), outputs...) {
				concepts[n] = true
			}
			for _, n := range outputs {
				if n == "" || outputSet[n] {
					return fail("invalid core output")
				}
				outputSet[n] = true
			}
		}
		if !concepts[target] || len(concepts) > 32 {
			return fail("concept bound/target")
		}
		routes := array(core["routes"])
		if len(routes) < 1 || len(routes) > 4 {
			return fail("route bound")
		}
		for _, v := range routes {
			route := array(v)
			if len(route) < 1 || len(route) > 6 {
				return fail("route step bound")
			}
			owned := map[string]bool{}
			for n := range seedSet {
				owned[n] = true
			}
			for _, v := range route {
				step := object(v)
				p := stringsOf(step["pair"])
				outputs := stringsOf(step["results"])
				if len(p) != 2 || !owned[p[0]] || !owned[p[1]] || len(outputs) == 0 {
					return fail("route ownership")
				}
				available := pairs[strings.Join(p, "\x00")]
				for _, n := range outputs {
					if !contains(available, n) {
						return fail("route differs from core")
					}
					owned[n] = true
				}
			}
			if !owned[target] {
				return fail("route cannot reach target")
			}
		}
		nodes, edges := object(b["nodes"]), object(b["edges"])
		if len(nodes) != len(concepts) || len(edges) > 96 {
			return fail("snapshot scope bound")
		}
		for n := range concepts {
			m := object(nodes[n])
			if !exact(m, "id", "node_type", "label_ro", "category", "description", "salience", "difficulty_tier", "degree", "aliases", "tags", "facets", "source", "redistributable") || m["id"] != n {
				return fail("node snapshot scope")
			}
		}
		directions := map[string]bool{}
		for eid, v := range edges {
			e := object(v)
			if !exact(e, "id", "src_id", "dst_id", "relation", "label_ro", "strength", "is_distractor", "bidirectional", "tags", "facets", "source", "redistributable") || e["id"] != eid {
				return fail("edge snapshot scope")
			}
			directions[str(e["src_id"])+"\x00"+str(e["dst_id"])] = true
			if e["bidirectional"] == true {
				directions[str(e["dst_id"])+"\x00"+str(e["src_id"])] = true
			}
		}
		for p, outputs := range pairs {
			parents := strings.Split(p, "\x00")
			for _, n := range outputs {
				for _, parent := range parents {
					if !directions[parent+"\x00"+n] {
						return fail("missing core edge snapshot")
					}
				}
			}
		}
		additions := array(b["additions"])
		if len(additions) == 0 || len(pairs)+len(additions) > 24 {
			return fail("extension pair bound")
		}
		for _, v := range additions {
			a := object(v)
			p := stringsOf(a["pair"])
			result, cid := str(a["result"]), str(a["candidate_id"])
			if cid == "" || candidates[cid] || !sha(a["candidate_sha256"]) {
				return fail("candidate identity")
			}
			candidates[cid] = true
			if len(p) != 2 || p[0] == "" || p[0] >= p[1] || pairs[strings.Join(p, "\x00")] != nil {
				return fail("pair overwrite/shape")
			}
			pairs[strings.Join(p, "\x00")] = []string{result}
			if result == "" || !concepts[p[0]] || !concepts[p[1]] || !concepts[result] || contains(p, result) || seedSet[result] || contains(p, target) || (!(seedSet[p[0]] && seedSet[p[1]]) && result != target) {
				return fail("addition escapes scope/cohort")
			}
			eids := stringsOf(a["edge_ids"])
			if len(eids) != 2 {
				return fail("added edge ids")
			}
			for i, eid := range eids {
				e := object(edges[eid])
				if e == nil || !((e["src_id"] == p[i] && e["dst_id"] == result) || (e["dst_id"] == p[i] && e["src_id"] == result && e["bidirectional"] == true)) {
					return fail("addition edge endpoints/direction")
				}
				if number(e["strength"]) < .70 || number(e["strength"]) > 1 || e["is_distractor"] != false {
					return fail("weak/distractor addition edge")
				}
			}
		}
	}
	return nil
}

// Strict serving-record checks mirror the former Pydantic strict schemas; audit
// metadata on the outer catalog remains extensible.
func strictWorldRecords(raw map[string]any) error {
	errf := func(s string) error { return fmt.Errorf("strict record: %s", s) }
	text := func(v any, min, max int) bool {
		s, ok := v.(string)
		return ok && len([]rune(s)) >= min && len([]rune(s)) <= max
	}
	list := func(v any, min, max int) bool {
		a, ok := v.([]any)
		if !ok || len(a) < min || len(a) > max {
			return false
		}
		for _, x := range a {
			if !text(x, 1, 160) {
				return false
			}
		}
		return true
	}
	if n, ok := integer(raw["schema_version"]); !ok || n != 1 {
		return errf("schema version")
	}
	for _, key := range []string{"concepts", "recipes", "goals", "reviews"} {
		if _, ok := raw[key].([]any); !ok {
			return errf(key + " must be array")
		}
	}
	for _, key := range []string{"unlocks", "compatible_versions"} {
		if v, exists := raw[key]; exists {
			if _, ok := v.([]any); !ok {
				return errf(key + " must be array")
			}
		}
	}
	for _, v := range object(raw["bindings"]) {
		if !sha(v) {
			return errf("binding digest")
		}
	}
	world := object(raw["world"])
	if !text(world["id"], 1, 160) || !text(world["title"], 1, 2000) || !text(world["description"], 1, 2000) || !list(world["starter_ids"], 2, 12) {
		return errf("world fields")
	}
	for _, v := range array(raw["concepts"]) {
		m := object(v)
		if !text(m["id"], 1, 160) || !text(m["label"], 1, 2000) || !text(m["description"], 0, 1<<30) || !text(m["source"], 0, 1<<30) {
			return errf("concept fields")
		}
		if refs, exists := m["references"]; exists {
			a, ok := refs.([]any)
			if !ok || len(a) > 8 {
				return errf("concept references")
			}
			for _, v := range a {
				if !text(v, 1, 2000) {
					return errf("concept reference text")
				}
			}
		}
	}
	for _, v := range array(raw["recipes"]) {
		m := object(v)
		if !text(m["id"], 1, 160) || !list(m["pair"], 2, 2) || !text(m["result"], 1, 160) || !text(m["explanation"], 1, 2000) {
			return errf("recipe fields")
		}
		a, ok := m["sources"].([]any)
		if !ok || len(a) < 1 || len(a) > 8 {
			return errf("recipe sources")
		}
		for _, v := range a {
			if !text(v, 1, 2000) {
				return errf("recipe source text")
			}
		}
	}
	for _, v := range array(raw["goals"]) {
		m := object(v)
		if !text(m["id"], 1, 160) || !text(m["target"], 1, 160) || !text(m["title"], 1, 2000) {
			return errf("goal fields")
		}
	}
	for _, v := range array(raw["unlocks"]) {
		m := object(v)
		if !text(m["id"], 1, 160) || !text(m["title"], 1, 2000) || !list(m["concept_ids"], 1, 12) {
			return errf("unlock fields")
		}
	}
	for _, v := range array(raw["reviews"]) {
		m := object(v)
		if !exact(m, "role", "reviewer", "candidate_sha256", "sha256") || !text(m["role"], 0, 1<<30) || !text(m["reviewer"], 1, 2000) || !sha(m["candidate_sha256"]) {
			return errf("review fields")
		}
	}
	for _, v := range array(raw["compatible_versions"]) {
		m := object(v)
		mech := object(m["mechanics"])
		if !text(m["world_id"], 1, 160) || !exact(mech, "starters", "recipes", "unlocks") || !list(mech["starters"], 2, 12) {
			return errf("archived mechanics fields")
		}
		recipes, ok := mech["recipes"].([]any)
		if !ok || len(recipes) < 2 || len(recipes) > 512 {
			return errf("archived recipe bound")
		}
		unlocks, ok := mech["unlocks"].([]any)
		if !ok || len(unlocks) > 12 {
			return errf("archived unlock bound")
		}
		for _, v := range recipes {
			r := object(v)
			if !exact(r, "pair", "result") || !list(r["pair"], 2, 2) || !text(r["result"], 1, 160) {
				return errf("archived recipe fields")
			}
		}
		for _, v := range unlocks {
			u := object(v)
			n, ok := integer(u["after"])
			if !exact(u, "after", "concepts") || !ok || n < 1 || n > 256 || !list(u["concepts"], 1, 12) {
				return errf("archived unlock fields")
			}
		}
	}
	return nil
}
