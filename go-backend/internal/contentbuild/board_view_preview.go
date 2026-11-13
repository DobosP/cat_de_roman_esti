package contentbuild

import (
	"encoding/json"
	"fmt"
	"sort"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

// BoardViewGraph validates exact fixture bytes and constructs the native graph.
// Its caller owns the unapproved operator snapshot.
func BoardViewGraph(raw map[string]any) (*graph.Service, error) {
	if failures := validateFixture(raw); len(failures) > 0 {
		return nil, fmt.Errorf("fixture invalid: %s", errorSummary(failures))
	}
	c, err := parsedGraph(raw)
	if err != nil {
		return nil, err
	}
	return graph.New(c), nil
}

// BoardViewCatalogs fills a private graph snapshot with the serving-shaped
// projections of already validated pack and Quick operator data. It does not
// produce a bundle, touch source pins, or update the server.
func BoardViewCatalogs(g *graph.Service, pack, rankings, derived, quick, reserve, extensions map[string]any) error {
	r, err := frozenRules()
	if err != nil {
		return err
	}
	reserved, err := validateReserve(reserve, pack)
	if err != nil {
		return err
	}
	approved := []map[string]any{}
	ranks := map[string]map[string]any{}
	for _, row := range array(rankings["boards"]) {
		m := object(row)
		ranks[str(m["id"])] = m
	}
	patterns := map[string]string{}
	for _, label := range g.Content.CategoryLabels {
		patterns[label] = labelPattern(label, r)
	}
	for _, game := range Games {
		rows := append([]any{}, array(pack[game])...)
		sort.Slice(rows, func(i, j int) bool {
			return str(object(rows[i])["id"]) < str(object(rows[j])["id"])
		})
		for _, row := range rows {
			m := object(row)
			if m["status"] != "approved" {
				continue
			}
			id := str(m["id"])
			rank := ranks[id]
			payload := map[string]any{}
			for _, key := range payloadKeys[game] {
				payload[key] = m[key]
			}
			if game == "conexiuni" {
				for _, label := range object(payload["group_labels"]) {
					patterns[str(label)] = labelPattern(str(label), r)
				}
			}
			category := str(m["category"])
			if m["category"] == nil {
				category = "None"
			}
			approved = append(approved, map[string]any{
				"game": game, "id": id, "category": category, "difficulty": m["difficulty"],
				"source": m["source"], "status": m["status"], "payload": payload,
				"pilot_score": rank["pilot_score"], "pilot_eligible": rank["pilot_eligible"],
				"selection_weight": rank["selection_weight"],
			})
		}
	}
	stock := array(derived["boards"])
	rated, _, err := validateQuickRows(array(quick["authored"]), stock, g)
	if err != nil {
		return err
	}
	boards := []map[string]any{}
	for _, row := range append(append([]any{}, stock...), rated...) {
		m := object(row)
		id := str(m["id"])
		if sha := reserved[id]; sha != "" {
			definition := map[string]any{}
			for _, key := range []string{"id", "game", "source_id", "category", "difficulty", "payload"} {
				definition[key] = m[key]
			}
			if valueDigest(definition) != sha {
				return fmt.Errorf("release reserve quick definition drift for %s", id)
			}
			delete(reserved, id)
			continue
		}
		boards = append(boards, map[string]any{
			"game": m["game"], "catalog_id": id, "source_id": m["source_id"],
			"category": m["category"], "difficulty": m["difficulty"], "payload": m["payload"],
			"overall_score": m["standard_score"], "overall_rank": m["standard_rank"],
			"starter_score": m["starter_score"], "starter_rank": m["starter_rank"], "starter_safe": m["starter_eligible"],
		})
	}
	if len(reserved) != 0 {
		return fmt.Errorf("release reserve missing quick identities")
	}
	c := g.Content
	if err := decodeBoardViewJSON(approved, &c.PackItems); err != nil {
		return err
	}
	if err := decodeBoardViewJSON(boards, &c.Boards); err != nil {
		return err
	}

	sort.Slice(c.Boards, func(i, j int) bool {
		a, b := c.Boards[i], c.Boards[j]
		return a.Game < b.Game || a.Game == b.Game && a.CatalogID < b.CatalogID
	})
	c.LabelPatterns = patterns
	c.LantCaptions = map[string]string{}
	for edge, caption := range lantCaptions(g, r) {
		c.LantCaptions[edge] = str(caption)
	}
	c.PackRanked = true
	if err := decodeBoardViewJSON(r["contexto_data"], &c.ContextoData); err != nil {
		return err
	}
	return decodeBoardViewJSON(extensions, &c.RecipeExtensions)
}

func decodeBoardViewJSON(rows any, into any) error {
	data, err := json.Marshal(rows)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, into)
}

// ValidatePackObjectsFromGraph validates the exact pack against an already
// constructed prospective graph.
func ValidatePackObjectsFromGraph(g *graph.Service, pack map[string]any) []string {
	return validatePack(pack, g)
}
