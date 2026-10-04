package contentrails

import (
	"encoding/hex"
	"fmt"
	"strings"
)

func validDigest(v any) bool {
	s := text(v)
	if len(s) != 64 {
		return false
	}
	b, e := hex.DecodeString(s)
	return e == nil && len(b) == 32
}
func stringArray(v any, min, max int) bool {
	x, ok := v.([]any)
	if !ok || len(x) < min || len(x) > max {
		return false
	}
	seen := map[string]bool{}
	for _, v := range x {
		s, ok := v.(string)
		if !ok || s == "" || seen[s] {
			return false
		}
		seen[s] = true
	}
	return true
}
func arrayShape(v any, min, max int) bool {
	x, ok := v.([]any)
	return ok && len(x) >= min && len(x) <= max
}
func sourceShape(raw map[string]any) error {
	fail := func(s string) error { return fmt.Errorf("native authored source: %s", s) }
	if !allowedKeys(raw, "schema", "version", "base_commit", "legacy_sources", "archives", "quick", "world", "extensions", "parent_source_sha256") || text(raw["base_commit"]) == "" {
		return fail("outer schema/identity")
	}
	legacy := object(raw["legacy_sources"])
	if len(legacy) != 4 {
		return fail("legacy provenance source count")
	}
	for _, v := range legacy {
		if !validDigest(v) {
			return fail("legacy provenance digest")
		}
	}
	archives := object(raw["archives"])
	for _, key := range []string{"quick_candidate", "quick_factual", "quick_quality", "world_previous", "world_candidate", "world_factual", "world_quality", "extensions_candidate", "extensions_factual", "extensions_quality", "reserve_proposal", "reserve_alchimie", "reserve_quality"} {
		a := object(archives[key])
		if !allowedKeys(a, "path", "sha256") || len(a) != 2 || !strings.HasPrefix(text(a["path"]), "docs/reviews/") || strings.Contains(text(a["path"]), "..") || !validDigest(a["sha256"]) {
			return fail("immutable archive descriptor")
		}
	}
	quick := object(raw["quick"])
	if len(quick) != 1 || !arrayShape(quick["boards"], 1, 256) {
		return fail("quick authoring array")
	}
	seen := map[string]bool{}
	for _, v := range rows(quick["boards"]) {
		b := object(v)
		if !allowedKeys(b, "id", "game", "source_id", "category", "difficulty", "payload", "sources", "rationale") || len(b) != 8 || text(b["id"]) == "" || seen[text(b["id"])] || text(b["source_id"]) == "" || text(b["category"]) == "" || text(b["difficulty"]) == "" || text(b["rationale"]) == "" || !sourcesValue(b["sources"]) || len(rows(b["sources"])) < 1 || len(rows(b["sources"])) > 16 {
			return fail("quick definition")
		}
		seen[text(b["id"])] = true
		p := object(b["payload"])
		switch b["game"] {
		case "intrusul":
			if len(p) != 3 || !allowedKeys(p, "members", "intruder", "group_label") || !stringArray(p["members"], 3, 3) || text(p["intruder"]) == "" || text(p["group_label"]) == "" {
				return fail("quick intrusul payload")
			}
		case "perechi":
			if len(p) != 1 || !arrayShape(p["pairs"], 4, 4) {
				return fail("quick perechi payload")
			}
			for _, v := range rows(p["pairs"]) {
				r := object(v)
				if len(r) != 2 || !allowedKeys(r, "members", "group_label") || !stringArray(r["members"], 2, 2) || text(r["group_label"]) == "" {
					return fail("quick pair definition")
				}
			}
		default:
			return fail("quick game")
		}
	}
	world := object(raw["world"])
	if len(world) != 8 || !allowedKeys(world, "world", "descriptions", "starters", "unlocks", "recipes", "goals", "world_concepts", "recipe_sources") {
		return fail("world authoring fields")
	}
	info := object(world["world"])
	if len(info) != 3 || !allowedKeys(info, "id", "title", "description") {
		return fail("world info")
	}
	for _, v := range info {
		if text(v) == "" {
			return fail("world info text")
		}
	}
	if !stringArray(world["starters"], 2, 12) || !arrayShape(world["unlocks"], 0, 12) || !arrayShape(world["recipes"], 2, 512) || !arrayShape(world["goals"], 1, 32) {
		return fail("world authoring array/bounds")
	}
	for _, v := range rows(world["recipes"]) {
		r := rows(v)
		if len(r) != 5 {
			return fail("recipe tuple")
		}
		for _, v := range r {
			if text(v) == "" {
				return fail("recipe text")
			}
		}
	}
	for _, v := range rows(world["unlocks"]) {
		u := rows(v)
		if len(u) != 4 || text(u[0]) == "" || integer(u[1]) < 1 || integer(u[1]) > 256 || text(u[2]) == "" || !stringArray(u[3], 1, 12) {
			return fail("unlock tuple")
		}
	}
	for _, v := range rows(world["goals"]) {
		g := rows(v)
		if len(g) != 3 {
			return fail("goal tuple")
		}
		for _, v := range g {
			if text(v) == "" {
				return fail("goal text")
			}
		}
	}
	if object(world["descriptions"]) == nil || object(world["world_concepts"]) == nil || object(world["recipe_sources"]) == nil {
		return fail("world maps")
	}
	for _, v := range object(world["descriptions"]) {
		if _, ok := v.(string); !ok {
			return fail("description text")
		}
	}
	for label, v := range object(world["world_concepts"]) {
		d := object(v)
		if label == "" || len(d) != 3 || !allowedKeys(d, "id", "description", "sources") || text(d["id"]) == "" || text(d["description"]) == "" || !sourcesValue(d["sources"]) || len(rows(d["sources"])) < 1 || len(rows(d["sources"])) > 8 {
			return fail("world-local definition")
		}
	}
	for _, v := range object(world["recipe_sources"]) {
		if !sourcesValue(v) || len(rows(v)) < 1 || len(rows(v)) > 8 {
			return fail("recipe references")
		}
	}
	ext := object(raw["extensions"])
	if ext["schema"] != "alchimie-bounded-completion-candidates-v1" || object(ext["bindings"]) == nil || !arrayShape(ext["boards"], 1, 512) || !arrayShape(ext["candidates"], 0, 512) {
		return fail("extension schema/core/candidate arrays")
	}
	for _, v := range rows(ext["boards"]) {
		b := object(v)
		if text(b["id"]) == "" || object(b["source_record"]) == nil || object(b["before_core"]) == nil || !validDigest(b["source_record_sha256"]) || !validDigest(b["before_core_sha256"]) {
			return fail("extension archived core")
		}
	}
	for _, v := range rows(ext["candidates"]) {
		c := object(v)
		if text(c["id"]) == "" || text(c["board_id"]) == "" || !validDigest(c["candidate_sha256"]) || !arrayShape(c["pair"], 2, 2) || object(c["result"]) == nil || object(c["target"]) == nil || !arrayShape(c["seeds"], 2, 32) || !arrayShape(c["edges"], 2, 2) {
			return fail("extension candidate")
		}
	}
	return nil
}
