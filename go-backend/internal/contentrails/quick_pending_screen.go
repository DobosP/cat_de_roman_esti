package contentrails

import (
	"bufio"
	"bytes"
	"fmt"
	"sort"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
)

func pendingVisible(r map[string]any) []string {
	p := object(r["payload"])
	if r["game"] == "intrusul" {
		return append(ids(p["members"]), text(p["intruder"]))
	}
	out := []string{}
	for _, v := range rows(p["pairs"]) {
		out = append(out, ids(object(v)["members"])...)
	}
	return out
}

func pendingScreen(s *quickPendingSnapshot, boards, ratings []any) (map[string]any, error) {
	registry := s.files["docs/content-registry/registry.jsonl"]
	current, historical := map[string]map[string]any{}, []any{}
	unknown := map[string]bool{}
	scan := bufio.NewScanner(bytes.NewReader(registry))
	scan.Buffer(make([]byte, 4096), 1<<20)
	for scan.Scan() {
		if len(current) > 20000 {
			return nil, fmt.Errorf("quick registry record bound")
		}
		r, err := pendingDecode(scan.Bytes(), 1<<20)
		if err != nil || r["schema"] != "cat-content-candidate-1" || text(r["id"]) == "" || text(r["type"]) == "" || text(r["state"]) == "" {
			return nil, fmt.Errorf("quick pending registry schema")
		}
		current[text(r["id"])] = r
		game := strings.TrimPrefix(text(r["type"]), "board.")
		if game != "intrusul" && game != "perechi" {
			continue
		}
		p := object(r["payload"])
		if game == "intrusul" && len(rows(p["members"])) == 3 && text(p["intruder"]) != "" || game == "perechi" && len(rows(p["pairs"])) == 4 {
			historical = append(historical, map[string]any{"id": r["id"], "game": game, "payload": p})
		} else if text(p["board_id"]) == "" {
			// Empty research payloads are explicit unresolved debt, never proof
			// that the original source contained no playable board.
			unknown[text(r["id"])] = true
		}
	}
	if err := scan.Err(); err != nil {
		return nil, err
	}
	ex, err := s.object("docs/content-registry/exclusions.json")
	if err != nil || ex["schema"] != "cat-content-exclusions-1" || object(ex["owner_rules"]) == nil {
		return nil, fmt.Errorf("quick pending exclusion schema")
	}
	kg, err := s.object("cat_de_roman_esti/fixtures/kg_sample.json")
	if err != nil {
		return nil, err
	}
	g, err := contentbuild.QuickGraphSnapshot(kg)
	if err != nil {
		return nil, err
	}
	blockedIDs, heldNodes := map[string]bool{}, map[string]bool{}
	ownerRows := 0
	for _, r := range current {
		blockedIDs[text(r["id"])], blockedIDs[text(object(r["origin"])["id"])] = true, true
		p := object(r["payload"])
		if id := text(p["board_id"]); id != "" {
			blockedIDs[id] = true
		}
		if r["state"] == "held_owner" {
			ownerRows++
			// A held form/synonym is not a blanket ban on an already installed
			// owner. Class P does not acquire permission to alter that form.
			if r["type"] == "concept" || r["type"] == "name" {
				for _, id := range []string{text(p["node_id"]), text(object(r["identity"])["owner_id"])} {
					if id != "" {
						heldNodes[id] = true
					}
				}
			}
		}
	}
	for _, v := range rows(ex["board_controls"]) {
		blockedIDs[text(object(v)["id"])] = true
	}
	for _, id := range ids(ex["owner_held_conexiuni"]) {
		blockedIDs[id] = true
	}
	labels := ids(object(object(ex["owner_rules"])["held_families"])["labels_ro"])
	for _, n := range g.Content.Nodes {
		for _, label := range labels {
			if contentbuild.Normalize(n.LabelRO) == contentbuild.Normalize(label) {
				heldNodes[n.ID] = true
			}
		}
	}
	for i, v := range boards {
		r, rating := object(v), object(ratings[i])
		if blockedIDs[text(r["id"])] || blockedIDs[text(r["source_id"])] || blockedIDs[text(rating["id"])] {
			return nil, fmt.Errorf("quick pending held/stock/registry identity collision")
		}
		for _, id := range pendingVisible(r) {
			if heldNodes[id] {
				return nil, fmt.Errorf("quick pending requires owner ruling for held node identity")
			}
		}
	}
	core, err := s.object("cat_de_roman_esti/fixtures/derived_catalog_v38.json")
	if err != nil {
		return nil, err
	}
	quick, err := s.object("cat_de_roman_esti/fixtures/quick_games_v92.json")
	if err != nil {
		return nil, err
	}
	stock := append(append(append([]any{}, rows(core["boards"])...), rows(quick["boards"])...), historical...)
	if _, _, err = contentbuild.ValidateQuickRows(boards, stock, g); err != nil {
		return nil, err
	}
	unresolved := []string{}
	for id := range unknown {
		unresolved = append(unresolved, id)
	}
	sort.Strings(unresolved)
	pack, err := s.object("cat_de_roman_esti/fixtures/games_pack.json")
	if err != nil {
		return nil, err
	}
	quads := []any{}
	for _, v := range rows(pack["conexiuni"]) {
		quads = append(quads, object(v)["groups"])
	}
	debt, err := s.object("cat_de_roman_esti/fixtures/conexiuni_rejection_tombstones.json")
	if err != nil {
		return nil, err
	}
	quads = append(quads, debt["items"])
	return map[string]any{
		"schema": "quick-pending-stock-screen-v1", "mechanical_pass": true, "complete": len(unresolved) == 0,
		"unresolved_quick_history": unresolved, "unresolved_history_requires_independent_relevance_closure": true,
		"registry_sha256": digestBytes(registry), "exclusions_sha256": digestBytes(s.files["docs/content-registry/exclusions.json"]),
		"stock_sha256": digest(stock), "quad_inventory_sha256": digest(quads), "historical_quick_payloads": len(historical),
		"registry_current_rows": len(current), "owner_held_rows_preserved": ownerRows, "conexiuni_locks_preserved": len(ids(ex["owner_held_conexiuni"])),
		"approval": nil,
	}, nil
}
