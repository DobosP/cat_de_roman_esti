package contentrails

import (
	"context"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpgolden"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
	"math/big"
	"sort"
)

func quickBindings(root string, live bool) (map[string]any, error) {
	bind, err := bindings(root)
	if err != nil {
		return nil, err
	}
	core, err := fixture(root, "derived_catalog_v38.json")
	if err != nil {
		return nil, err
	}
	b, _ := Render(core["boards"])
	out := map[string]any{"kg_sha256": bind["kg_sample.json"], "rubric_sha256": bind["rubric"], "core_payload_sha256": contentbuild.SHA256(b)}
	if live {
		out["pack_sha256"] = bind["games_pack.json"]
		out["core_catalog_sha256"] = bind["derived_catalog_v38.json"]
	}
	return out, nil
}
func quickCandidate(root string, s *Source, historical bool) (map[string]any, error) {
	bind, err := quickBindings(root, false)
	if err != nil {
		return nil, err
	}
	editorial := s.SHA256
	if historical {
		editorial = text(object(s.Raw["legacy_sources"])["scripts/quick_game_content_source_v92.py"])
	}
	bind["editorial_source_sha256"] = editorial
	candidate := map[string]any{"kind": "quick-content-candidates-v1", "boards": clone(object(s.Raw["quick"])["boards"]), "bindings": bind}
	if !historical {
		candidate["native_source_version"] = s.Version
	}
	if len(rows(candidate["boards"])) == 0 || len(rows(candidate["boards"])) > 256 {
		return nil, fmt.Errorf("quick authored board bound")
	}
	return candidate, nil
}
func buildQuick(root string, s *Source, candidate map[string]any, candidateSHA string, reviews []Review) (map[string]any, error) {
	g, err := sourceGraph(root)
	if err != nil {
		return nil, err
	}
	base, err := fixture(root, "derived_catalog_v38.json")
	if err != nil {
		return nil, err
	}
	accepted := acceptedIDs(reviews)
	chosen, rated := []any{}, []any{}
	visible := map[string]bool{}
	for _, raw := range rows(candidate["boards"]) {
		m := object(raw)
		if !accepted[text(m["id"])] {
			continue
		}
		rating, err := contentbuild.RateQuick(m, g)
		if err != nil {
			return nil, err
		}
		chosen = append(chosen, m)
		rated = append(rated, rating)
		payload := object(m["payload"])
		if m["game"] == "intrusul" {
			for _, id := range append(ids(payload["members"]), text(payload["intruder"])) {
				visible[id] = true
			}
		} else {
			for _, pair := range rows(payload["pairs"]) {
				for _, id := range ids(object(pair)["members"]) {
					visible[id] = true
				}
			}
		}
	}
	if len(chosen) == 0 {
		return nil, fmt.Errorf("no independently accepted quick boards")
	}
	contentbuild.AssignQuickRanks(rated)
	nodes := map[string]any{}
	for id := range visible {
		nodes[id] = contentbuild.NodeSnapshot(g.Node(id))
	}
	bind, err := quickBindings(root, true)
	if err != nil {
		return nil, err
	}
	excluded := []string{}
	for _, raw := range rows(candidate["boards"]) {
		id := text(object(raw)["id"])
		if !accepted[id] {
			excluded = append(excluded, id)
		}
	}
	sort.Strings(excluded)
	out := map[string]any{"kind": "quick-content-catalog-v1", "candidate_sha256": candidateSHA, "bindings": bind, "reviews": reviewDescriptors(reviews, false), "authored": chosen, "boards": rated, "nodes": nodes, "excluded": excluded}
	digests, err := bindings(root)
	if err != nil {
		return nil, err
	}
	if err = contentbuild.ValidateQuickCatalog(out, base, g, digests); err != nil {
		return nil, err
	}
	return out, nil
}
func auditQuick(ctx context.Context, root string, raw map[string]any) (map[string]any, error) {
	data, err := content.Load()
	if err != nil {
		return nil, err
	}
	g, err := sourceGraph(root)
	if err != nil {
		return nil, err
	}
	base, err := fixture(root, "derived_catalog_v38.json")
	if err != nil {
		return nil, err
	}
	bind, err := bindings(root)
	if err != nil {
		return nil, err
	}
	if err = contentbuild.ValidateQuickCatalog(raw, base, g, bind); err != nil {
		return nil, err
	}
	data.Nodes = g.Content.Nodes
	data.Edges = g.Content.Edges
	data.Labels = g.Content.Labels
	data.CategoryLabels = g.Content.CategoryLabels
	data.NormalizedIndex = g.Content.NormalizedIndex
	// Preserve the independently frozen derived payload; replace only supplements
	// inside this offline process, then prove ordinary seeded HTTP selection.
	combined := []content.Board{}
	for _, board := range data.Boards {
		if len(board.SourceID) < 5 || board.SourceID[:5] != "aq92_" {
			combined = append(combined, board)
		}
	}
	for _, v := range rows(raw["boards"]) {
		m := object(v)
		var rank *int
		if m["starter_rank"] != nil {
			r := integer(m["starter_rank"])
			rank = &r
		}
		combined = append(combined, content.Board{Game: text(m["game"]), CatalogID: text(m["id"]), SourceID: text(m["source_id"]), Category: text(m["category"]), Difficulty: text(m["difficulty"]), OverallScore: integer(m["standard_score"]), StarterScore: integer(m["starter_score"]), OverallRank: integer(m["standard_rank"]), StarterRank: rank, StarterSafe: m["starter_eligible"] == true, Payload: object(m["payload"])})
	}
	data.Boards = combined
	client, _ := httpgolden.NewClient(httpgolden.Local(httpapi.New(data)), 2000)
	defer client.Close()
	replays := []any{}
	for _, v := range rows(raw["boards"]) {
		m := object(v)
		game, id, category := text(m["game"]), text(m["id"]), text(m["category"])
		seed := -1
		for n := 0; n < 5000; n++ {
			picked := catalog.New(data).PickSeeded(game, pyrandom.New(big.NewInt(int64(n))), catalog.PickOptions{Category: category})
			if picked != nil && picked.CatalogID == id {
				seed = n
				break
			}
		}
		if seed < 0 {
			return nil, fmt.Errorf("quick board not naturally selectable within 5000 seeds: %s", id)
		}
		basePath := fmt.Sprintf("/api/wordgames/%s/games", game)
		res, err := client.Do(ctx, httpgolden.JSONRequest("POST", fmt.Sprintf("%s?seed=%d&category=%s", basePath, seed, category), nil))
		if err != nil || res.Status != 200 {
			return nil, fmt.Errorf("quick natural create failed: %s", id)
		}
		state, err := res.Object()
		if err != nil {
			return nil, err
		}
		if state["score"] != nil || state["solution"] != nil || containsString(state, text(m["source_id"])) || containsString(state, id) {
			return nil, fmt.Errorf("quick private identity leaked")
		}
		sid := text(state["game_id"])
		path := basePath + "/" + sid
		resume, err := client.Do(ctx, httpgolden.JSONRequest("GET", path, nil))
		if err != nil || resume.Status != 200 {
			return nil, fmt.Errorf("initial quick resume failed")
		}
		resumed, err := resume.Object()
		if err != nil || !same(resumed, state) {
			return nil, fmt.Errorf("initial quick state changed")
		}
		payload := object(m["payload"])
		actions := []map[string]any{}
		hidden := map[string]bool{}
		action := "guess"
		if game == "intrusul" {
			if containsString(state, text(payload["group_label"])) {
				return nil, fmt.Errorf("hidden outsider predicate leaked")
			}
			actions = append(actions, map[string]any{"id": payload["intruder"]})
		} else {
			action = "match"
			for _, pair := range rows(payload["pairs"]) {
				p := object(pair)
				hidden[text(p["group_label"])] = true
				if containsString(state, text(p["group_label"])) {
					return nil, fmt.Errorf("hidden pair predicate leaked")
				}
				actions = append(actions, map[string]any{"ids": p["members"]})
			}
		}
		for actionIndex, body := range actions {
			res, err = client.Do(ctx, httpgolden.JSONRequest("POST", path+"/"+action, body))
			if err != nil || res.Status != 200 {
				return nil, fmt.Errorf("quick winning action failed")
			}
			state, err = res.Object()
			if err != nil {
				return nil, err
			}
			if game == "perechi" {
				delete(hidden, text(object(rows(payload["pairs"])[actionIndex])["group_label"]))
				for label := range hidden {
					if containsString(state, label) {
						return nil, fmt.Errorf("unsolved pair predicate leaked")
					}
				}
			}
		}
		if state["won"] != true || integer(state["score"]) != 1000 {
			return nil, fmt.Errorf("quick scored win failed")
		}
		res, err = client.Do(ctx, httpgolden.JSONRequest("GET", path, nil))
		if err != nil || res.Status != 200 {
			return nil, fmt.Errorf("terminal resume failed")
		}
		terminal, _ := res.Object()
		if terminal["won"] != true || integer(terminal["score"]) != 1000 || containsString(terminal, text(m["source_id"])) || containsString(terminal, id) {
			return nil, fmt.Errorf("terminal score changed")
		}
		replays = append(replays, map[string]any{"id": id, "game": game, "source_id": m["source_id"], "category": category, "public_seed": seed, "score": 1000, "hidden_answers_preserved": true, "terminal_get_preserved": true})
	}
	return map[string]any{"kind": "quick-content-live-audit-v1", "passed": true, "candidate_sha256": raw["candidate_sha256"], "replays": replays, "core_boards_preserved": true, "requests": client.Count()}, nil
}
func containsString(v any, want string) bool {
	if want == "" {
		return false
	}
	switch x := v.(type) {
	case string:
		return x == want
	case map[string]any:
		for _, v := range x {
			if containsString(v, want) {
				return true
			}
		}
	case []any:
		for _, v := range x {
			if containsString(v, want) {
				return true
			}
		}
	}
	return false
}
