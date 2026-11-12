package contentrails

import (
	"bytes"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"strconv"
	"strings"
	"time"
	"unicode"
)

// History closure never changes the original screen/registry. Every unresolved
// occurrence and original retained source entry is bound, then both same-role
// reviewers judge relevance separately for every new item. Unknown stays closed.
func bridgeHistory(snap *quickPendingSnapshot, pending, closure map[string]any, names map[string]string, material map[string]map[string]any, files *quickBridgeFiles) error {
	screen := object(pending["screen"])
	unknown := ids(screen["unresolved_quick_history"])
	if screen["schema"] != "quick-pending-stock-screen-v1" || screen["mechanical_pass"] != true || !arrayShape(screen["unresolved_quick_history"], 0, 20000) || screen["complete"] != (len(unknown) == 0) {
		return fmt.Errorf("quick history contradictory stock completeness")
	}
	if !pendingExact(closure, "schema", "pending_sha256", "registry_sha256", "items") || closure["schema"] != "quick-history-closure-v1" || closure["pending_sha256"] != object(pending["_bridge"])["pending_sha256"] || closure["registry_sha256"] != screen["registry_sha256"] || !arrayShape(closure["items"], len(unknown), len(unknown)) {
		return fmt.Errorf("quick history exact closure coverage")
	}
	unresolved := map[string]bool{}
	for _, id := range unknown {
		if unresolved[id] {
			return fmt.Errorf("quick history duplicate unresolved identity")
		}
		unresolved[id] = true
	}
	occurrences := map[string][]any{}
	records := map[string]map[string]any{}
	for i, line := range bytes.Split(snap.files["docs/content-registry/registry.jsonl"], []byte("\n")) {
		if len(line) == 0 {
			continue
		}
		r, err := pendingDecode(line, 1<<20)
		if err != nil {
			return err
		}
		id := text(r["id"])
		if unresolved[id] {
			if prior := records[id]; prior != nil && !same(object(prior["origin"]), r["origin"]) {
				return fmt.Errorf("quick history multiple original sources require separate explicit closure")
			}
			occurrences[id] = append(occurrences[id], map[string]any{"line": i + 1, "line_sha256": digestBytes(line), "record_sha256": digest(r)})
			records[id] = r
		}
	}
	seen := map[string]bool{}
	recovered := []any{}
	latest := time.Time{}
	for _, v := range rows(closure["items"]) {
		row := object(v)
		id := text(row["id"])
		record := records[id]
		if !pendingExact(row, "id", "registry_occurrences", "origin", "retained_source", "selected_entry_sha256", "selected_entry", "recovered_board", "judgments") || !unresolved[id] || seen[id] || !same(row["registry_occurrences"], occurrences[id]) || !same(row["origin"], object(record["origin"])["source"]) {
			return fmt.Errorf("quick history original registry/origin identity differs")
		}
		seen[id] = true
		origin := object(row["origin"])
		ref := object(row["retained_source"])
		if ref["sha256"] != origin["sha256"] || !authorityDigest(origin["sha256"]) {
			return fmt.Errorf("quick history retained original source SHA differs")
		}
		b, err := files.read(ref)
		if err != nil {
			return err
		}
		selected, err := bridgeHistorySelect(b, origin)
		if err != nil {
			return err
		}
		if len(selected) == 0 || text(object(record["origin"])["id"]) == "" || !bytes.Contains(selected, []byte(text(object(record["origin"])["id"]))) || row["selected_entry"] != string(selected) || row["selected_entry_sha256"] != digestBytes(selected) {
			return fmt.Errorf("quick history selected original entry differs/empty")
		}
		var recoverySHA any
		if row["recovered_board"] != nil {
			board := object(row["recovered_board"])
			if err := bridgeHistoricalBoard(board, id, strings.TrimPrefix(text(record["type"]), "board.")); err != nil {
				return err
			}
			recoverySHA = digest(board)
		}
		if !arrayShape(row["judgments"], 2, 2) {
			return fmt.Errorf("quick history independent F/Q relevance judgments required")
		}
		roles := map[string]bool{}
		allUnrelated := true
		relevanceByID := map[string]string{}
		for _, j := range rows(row["judgments"]) {
			judgment := object(j)
			role := text(judgment["role"])
			if !pendingExact(judgment, "role", "reviewer", "signed_at", "history_id", "pending_sha256", "registry_sha256", "registry_occurrences_sha256", "origin", "selected_entry_sha256", "recovered_board_sha256", "recovery_correspondence_checked", "items") || role != "factual" && role != "quality" || roles[role] || judgment["reviewer"] != names[role] || !arrayShape(judgment["items"], len(rows(pending["boards"])), len(rows(pending["boards"]))) {
				return fmt.Errorf("quick history same-role exact judgment coverage")
			}
			roles[role] = true
			// These are the ORIGINAL same-role recovery judgments. Later Root
			// frame pins/canonical confirmations cannot supply omitted claims.
			if judgment["history_id"] != id || judgment["pending_sha256"] != closure["pending_sha256"] || judgment["registry_sha256"] != closure["registry_sha256"] || judgment["registry_occurrences_sha256"] != digest(row["registry_occurrences"]) || !same(judgment["origin"], origin) || judgment["selected_entry_sha256"] != row["selected_entry_sha256"] || !same(judgment["recovered_board_sha256"], recoverySHA) || judgment["recovery_correspondence_checked"] != true {
				return fmt.Errorf("quick history original same-role exact recovery/correspondence binding differs")
			}
			if recoverySHA != nil && !authorityDigest(judgment["recovered_board_sha256"]) {
				return fmt.Errorf("quick history original recovery digest shape")
			}
			signed, e := bridgeTime(judgment["signed_at"])
			rawSigned, _ := bridgeTime(material[role+"_envelope"]["signed_at"])
			released, _ := bridgeTime(material["author_release"]["unsealed_at"])
			if e != nil || signed.Before(rawSigned) || signed.After(released) {
				return fmt.Errorf("quick history judgment chronology")
			}
			if signed.After(latest) {
				latest = signed
			}
			byID := map[string]bool{}
			for _, x := range rows(judgment["items"]) {
				r := object(x)
				newID := text(r["id"])
				var authored map[string]any
				for _, board := range rows(pending["boards"]) {
					if object(board)["id"] == newID {
						authored = object(board)
					}
				}
				if !pendingExact(r, "id", "record_sha256", "relevance", "rationale", "original_entry_checked") || authored == nil || byID[newID] || r["record_sha256"] != digest(authored) || r["original_entry_checked"] != true || bridgeNorm(text(r["rationale"])) == "" || r["relevance"] != "unrelated" && r["relevance"] != "compare_payload" {
					return fmt.Errorf("quick history unknown/missing/unresolved relevance")
				}
				byID[newID] = true
				relevance := text(r["relevance"])
				if prior := relevanceByID[newID]; prior != "" && prior != relevance {
					return fmt.Errorf("quick history per-item reviewer relevance disagreement")
				}
				relevanceByID[newID] = relevance
				if relevance == "compare_payload" {
					allUnrelated = false
				}
			}
		}
		if allUnrelated {
			if row["recovered_board"] != nil {
				return fmt.Errorf("quick history unrelated closure cannot hide an unchecked payload")
			}
		} else {
			board := object(row["recovered_board"])
			if board == nil {
				return fmt.Errorf("quick history relevant original payload must be recovered")
			}
			// Both roles must explicitly concur that the recovered payload was
			// checked against this exact entry; no single-reviewer shortcut.
			recovered = append(recovered, board)
		}
	}
	if replayed, e := bridgeTime(material["operator_replay"]["created_at"]); e != nil || replayed.Before(latest) {
		return fmt.Errorf("quick history Root replay receipt predates relevance closure")
	}
	for _, role := range []string{"factual", "quality"} {
		if peer := material[role+"_envelope"]["first_peer_read_at"]; peer != nil {
			when, e := bridgeTime(peer)
			if e != nil || !when.After(latest) {
				return fmt.Errorf("quick history peer verdict exposed before relevance signatures")
			}
		}
	}
	kg, err := snap.object("cat_de_roman_esti/fixtures/kg_sample.json")
	if err != nil {
		return err
	}
	g, err := contentbuild.QuickGraphSnapshot(kg)
	if err != nil {
		return err
	}
	if len(recovered) > 0 {
		for _, value := range recovered {
			for _, id := range pendingVisible(object(value)) {
				if g.Node(id) == nil {
					return fmt.Errorf("quick history recovered owner identity unresolved; candidate remains parked")
				}
			}
		}
		if _, _, err = contentbuild.ValidateQuickRows(rows(pending["boards"]), recovered, g); err != nil {
			return fmt.Errorf("quick history recovered-stock collision: %w", err)
		}
	}
	return nil
}
func bridgeHistorySelect(b []byte, origin map[string]any) ([]byte, error) {
	if pointer, ok := origin["pointer"].(string); ok {
		value, err := pendingDecode(b, quickPendingMaxBytes)
		if err != nil {
			return nil, err
		}
		var selected any = value
		if pointer != "" && !strings.HasPrefix(pointer, "/") {
			return nil, fmt.Errorf("quick history JSON pointer")
		}
		for _, part := range strings.Split(strings.TrimPrefix(pointer, "/"), "/") {
			if pointer == "" {
				break
			}
			part = strings.ReplaceAll(strings.ReplaceAll(part, "~1", "/"), "~0", "~")
			if m := object(selected); m != nil {
				var exists bool
				selected, exists = m[part]
				if !exists {
					return nil, fmt.Errorf("quick history pointer missing")
				}
			} else {
				a := rows(selected)
				n, e := strconv.Atoi(part)
				if e != nil || n < 0 || n >= len(a) {
					return nil, fmt.Errorf("quick history pointer index")
				}
				selected = a[n]
			}
		}
		return contentbuild.Canonical(selected)
	}
	n := integer(origin["line"])
	lines := bytes.Split(b, []byte("\n"))
	if n < 1 || n > len(lines) {
		return nil, fmt.Errorf("quick history original source line missing")
	}
	return lines[n-1], nil
}

// bridgeHistoricalBoard validates the recovered fingerprint's shape, not its
// current quality/admission score. Historical rejections may fail today's graph
// or rating floors and must still retain their exact novelty fingerprints.
func bridgeHistoricalBoard(board map[string]any, id, game string) error {
	if !pendingExact(board, "id", "game", "payload") || board["id"] != id || board["game"] != game {
		return fmt.Errorf("quick history recovered original board identity/shape")
	}
	payload := object(board["payload"])
	identity := func(value any) bool {
		s, ok := value.(string)
		if !ok || s == "" || strings.TrimSpace(s) != s {
			return false
		}
		return strings.IndexFunc(s, unicode.IsControl) < 0
	}
	label := func(value any) bool {
		s, ok := value.(string)
		if !ok || strings.TrimSpace(s) == "" || strings.IndexFunc(s, unicode.IsControl) >= 0 {
			return false
		}
		return strings.IndexFunc(s, func(c rune) bool { return unicode.IsLetter(c) || unicode.IsDigit(c) }) >= 0
	}
	seen := map[string]bool{}
	members := func(value any, count int) bool {
		if !arrayShape(value, count, count) {
			return false
		}
		for _, value := range rows(value) {
			if !identity(value) || seen[text(value)] {
				return false
			}
			seen[text(value)] = true
		}
		return true
	}
	switch game {
	case "intrusul":
		if !pendingExact(payload, "members", "intruder", "group_label") || !members(payload["members"], 3) || !identity(payload["intruder"]) || seen[text(payload["intruder"])] || !label(payload["group_label"]) {
			return fmt.Errorf("quick history recovered Intrusul payload must bind three distinct members, outsider and meaningful label")
		}
	case "perechi":
		if !pendingExact(payload, "pairs") || !arrayShape(payload["pairs"], 4, 4) {
			return fmt.Errorf("quick history recovered Perechi requires four pairs")
		}
		for _, value := range rows(payload["pairs"]) {
			pair := object(value)
			if !pendingExact(pair, "members", "group_label") || !members(pair["members"], 2) || !label(pair["group_label"]) {
				return fmt.Errorf("quick history recovered Perechi payload must bind eight distinct members and meaningful labels")
			}
		}
	default:
		return fmt.Errorf("quick history recovered game is unknown")
	}
	return nil
}
