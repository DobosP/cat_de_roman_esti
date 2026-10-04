package contentrails

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"sort"
)

func buildReserve(root string, s *Source) (map[string]any, error) {
	proposal, err := archive(root, s, "reserve_proposal")
	if err != nil {
		return nil, err
	}
	alchimie, err := archive(root, s, "reserve_alchimie")
	if err != nil {
		return nil, err
	}
	quality, err := archive(root, s, "reserve_quality")
	if err != nil {
		return nil, err
	}
	author, reviewer := text(proposal["author"]), text(quality["reviewer"])
	g, err := sourceGraph(root)
	if err != nil {
		return nil, err
	}
	a := object(s.Raw["archives"])
	pSHA := object(a["reserve_proposal"])["sha256"]
	alSHA := object(a["reserve_alchimie"])["sha256"]
	qSHA := object(a["reserve_quality"])["sha256"]
	if proposal["baseline"] != "cc0a6a4" || alchimie["baseline"] != "cc0a6a4" || author == "" || alchimie["author"] != author || quality["author_of_proposals"] != author || reviewer == "" || g.Casefold(author) == g.Casefold(reviewer) || quality["role"] != "quality" || quality["candidate_sha256"] != pSHA || quality["alchimie_candidate_sha256"] != alSHA {
		return nil, fmt.Errorf("reserve baseline/independence/review binding")
	}
	proposed := append(append([]any{}, rows(proposal["items"])...), rows(alchimie["items"])...)
	if len(proposed) != 23 || len(rows(quality["items"])) != 23 {
		return nil, fmt.Errorf("finite reserve requires exact 23 judgments")
	}
	judged := map[string]any{}
	for _, v := range rows(quality["items"]) {
		r := object(v)
		id := text(r["id"])
		if id == "" || judged[id] != nil {
			return nil, fmt.Errorf("duplicate reserve judgment")
		}
		judged[id] = r
	}
	pack, err := fixture(root, "games_pack.json")
	if err != nil {
		return nil, err
	}
	derived, err := fixture(root, "derived_catalog_v38.json")
	if err != nil {
		return nil, err
	}
	quick, err := fixture(root, "quick_games_v92.json")
	if err != nil {
		return nil, err
	}
	quickRows := append(append([]any{}, rows(derived["boards"])...), rows(quick["boards"])...)
	sort.Slice(proposed, func(i, j int) bool { return text(object(proposed[i])["id"]) < text(object(proposed[j])["id"]) })
	seen := map[string]bool{}
	reserved, quickReserved := []any{}, []any{}
	reservedIDs := []string{}
	for _, v := range proposed {
		r := object(v)
		id, game := text(r["id"]), text(r["game"])
		review := object(judged[id])
		hash := digest(r["record"])
		if id == "" || seen[id] || r["record_sha256"] != hash || review["record_sha256"] != hash || review["game"] != game || review["verdict"] != "accept" || review["action"] != "reserve_from_new_selection" {
			return nil, fmt.Errorf("unresolved/stale reserve judgment")
		}
		seen[id] = true
		available := rows(pack[game])
		isQuick := game == "intrusul" || game == "perechi"
		if isQuick {
			available = quickRows
		}
		matches := []map[string]any{}
		for _, v := range available {
			record := object(v)
			if record["id"] == id {
				matches = append(matches, record)
			}
		}
		if len(matches) != 1 || digest(matches[0]) != hash {
			return nil, fmt.Errorf("current archived reserve record drift")
		}
		record := matches[0]
		row := map[string]any{"id": id, "game": game, "record_sha256": hash}
		if isQuick {
			row["source_id"] = record["source_id"]
			row["definition_sha256"] = digest(map[string]any{"id": record["id"], "game": record["game"], "source_id": record["source_id"], "category": record["category"], "difficulty": record["difficulty"], "payload": record["payload"]})
			quickReserved = append(quickReserved, row)
		} else {
			if record["status"] != "approved" {
				return nil, fmt.Errorf("nonapproved reserve stock")
			}
			reserved = append(reserved, row)
			reservedIDs = append(reservedIDs, id)
		}
	}
	if len(reserved) != 20 || len(quickReserved) != 3 {
		return nil, fmt.Errorf("finite reserve game counts changed")
	}
	return map[string]any{"meta": map[string]any{"kind": "v1-release-reserve-v1", "baseline": "cc0a6a4", "count": len(reserved), "quick_count": len(quickReserved), "author": author, "reviewer": reviewer, "proposal_sha256": pSHA, "alchimie_proposal_sha256": alSHA, "quality_review_sha256": qSHA}, "ids": reservedIDs, "pack": reserved, "quick": quickReserved}, nil
}

// Reserve rendering retains the historical insertion order as well as values;
// its independently reviewed digest remains exact without changing either copy.
func renderReserve(raw map[string]any) ([]byte, error) {
	var compact bytes.Buffer
	var write func(any) error
	write = func(v any) error {
		switch m := v.(type) {
		case map[string]any:
			keys := sortedKeys(m)
			if m["meta"] != nil {
				keys = []string{"meta", "ids", "pack", "quick"}
			} else if m["kind"] == "v1-release-reserve-v1" {
				keys = []string{"kind", "baseline", "count", "quick_count", "author", "reviewer", "proposal_sha256", "alchimie_proposal_sha256", "quality_review_sha256"}
			} else if m["record_sha256"] != nil {
				keys = []string{"id", "game", "record_sha256"}
				if m["source_id"] != nil {
					keys = append(keys, "source_id", "definition_sha256")
				}
			}
			compact.WriteByte('{')
			for i, key := range keys {
				if i > 0 {
					compact.WriteByte(',')
				}
				b, _ := contentbuild.Canonical(key)
				compact.Write(b)
				compact.WriteByte(':')
				if err := write(m[key]); err != nil {
					return err
				}
			}
			compact.WriteByte('}')
		case []any:
			compact.WriteByte('[')
			for i, value := range m {
				if i > 0 {
					compact.WriteByte(',')
				}
				if err := write(value); err != nil {
					return err
				}
			}
			compact.WriteByte(']')
		default:
			b, err := contentbuild.Canonical(v)
			if err != nil {
				return err
			}
			compact.Write(b)
		}
		return nil
	}
	if err := write(raw); err != nil {
		return nil, err
	}
	var indented bytes.Buffer
	if err := json.Indent(&indented, compact.Bytes(), "", "  "); err != nil {
		return nil, err
	}
	return append(indented.Bytes(), '\n'), nil
}
