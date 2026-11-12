//go:build linux

package contentrails

import (
	"bytes"
	"fmt"
	"os"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
)

// All bodies/role statements are synthetic t.TempDir fixtures. A successful
// helper exercise is not a genuine review, Root receipt or content approval.
type bridgeRecoveryFixture struct {
	f                *bridgeFixture
	snap             *quickPendingSnapshot
	pending, closure map[string]any
	names            map[string]string
}

func bridgeRecoveryRow(game string) (map[string]any, map[string]any) {
	row := pendingTestRow()
	kg := pendingTestKG()
	if game == "intrusul" {
		return row, kg
	}
	row = map[string]any{"id": "pq92_history_binding", "game": "perechi", "source_id": "aq92_history_binding", "category": "viata_de_roman", "difficulty": "normal", "sources": []any{"https://example.test/history-author"}, "rationale": "Synthetic new board only"}
	pairs, nodes, edges := []any{}, []any{}, []any{}
	for n := 0; n < 8; n++ {
		nodes = append(nodes, map[string]any{"id": fmt.Sprintf("recovery_p%d", n), "node_type": "concept", "label_ro": fmt.Sprintf("Cuvânt P%d", n), "category": "viata_de_roman", "salience": .9})
	}
	for n := 0; n < 8; n += 2 {
		pairs = append(pairs, map[string]any{"members": []any{fmt.Sprintf("recovery_p%d", n), fmt.Sprintf("recovery_p%d", n+1)}, "group_label": fmt.Sprintf("Pereche istorică %d", n)})
		edges = append(edges, map[string]any{"id": fmt.Sprintf("recovery_e%d", n), "src_id": fmt.Sprintf("recovery_p%d", n), "dst_id": fmt.Sprintf("recovery_p%d", n+1), "strength": .8})
	}
	row["payload"] = map[string]any{"pairs": pairs}
	kg = map[string]any{"kg_nodes": nodes, "kg_edges": edges}
	return row, kg
}
func bridgeRecoveryOldPayload(game string) map[string]any {
	if game == "intrusul" {
		return map[string]any{"members": []any{"old_legacy_a", "old_legacy_b", "old_legacy_c"}, "intruder": "old_legacy_d", "group_label": "Predicat original istoric"}
	}
	pairs := []any{}
	for n := 0; n < 8; n += 2 {
		pairs = append(pairs, map[string]any{"members": []any{fmt.Sprintf("old_legacy_%d", n), fmt.Sprintf("old_legacy_%d", n+1)}, "group_label": fmt.Sprintf("Relație originală %d", n)})
	}
	return map[string]any{"pairs": pairs}
}
func newBridgeRecoveryFixture(t *testing.T, game, mode string) *bridgeRecoveryFixture {
	t.Helper()
	f := newBridgeFixture(t)
	row, kg := bridgeRecoveryRow(game)
	payload := bridgeRecoveryOldPayload(game)
	if mode == "collision" {
		payload = object(clone(row["payload"]))
	}
	if mode == "recovered" {
		// Canonical current owners exist, but no old intended graph edges do.
		// The historical rejected board therefore fails current rating floors.
		oldBoard := map[string]any{"game": game, "payload": payload}
		nodes := rows(kg["kg_nodes"])
		for _, id := range pendingVisible(oldBoard) {
			nodes = append(nodes, map[string]any{"id": id, "node_type": "concept", "label_ro": "Concept vechi " + id, "category": "viata_de_roman", "salience": .1})
		}
		kg["kg_nodes"] = nodes
	}
	source := map[string]any{"records": []any{map[string]any{"id": "original-recovery-id", "game": game, "payload": payload, "status": "historical rejected synthetic fixture"}}}
	ref := f.put("recovery-source.json", source)
	origin := map[string]any{"path": "recovery-source.json", "scope": "synthetic-test-only", "line": 1, "pointer": "/records/0", "sha256": ref["sha256"]}
	record := pendingTestRegistry("board."+game, "held_recorded", map[string]any{})
	record["origin"] = map[string]any{"id": "original-recovery-id", "source": origin}
	snap := pendingTestSnapshot(t, []any{record})
	kgBytes, err := Render(kg)
	if err != nil {
		t.Fatal(err)
	}
	snap.files["cat_de_roman_esti/fixtures/kg_sample.json"] = kgBytes
	g, err := contentbuild.QuickGraphSnapshot(kg)
	if err != nil {
		t.Fatal(err)
	}
	rating, err := contentbuild.RateQuick(row, g)
	if err != nil {
		t.Fatal(err)
	}
	screen, err := pendingScreen(snap, []any{row}, []any{rating})
	if err != nil {
		t.Fatal(err)
	}
	pending := map[string]any{"boards": []any{row}, "screen": screen, "_bridge": map[string]any{"pending_sha256": strings.Repeat("a", 64)}}
	selected, err := contentbuild.Canonical(rows(source["records"])[0])
	if err != nil {
		t.Fatal(err)
	}
	line := bytes.TrimSuffix(snap.files["docs/content-registry/registry.jsonl"], []byte("\n"))
	occurrences := []any{map[string]any{"line": 1, "line_sha256": digestBytes(line), "record_sha256": digest(record)}}
	names := map[string]string{"factual": "factual synthetic distinct", "quality": "quality synthetic distinct"}
	var recovered any
	var recoveredSHA any
	relevance := "unrelated"
	if mode != "unrelated" {
		recovered = map[string]any{"id": "history_row", "game": game, "payload": payload}
		recoveredSHA = digest(recovered)
		relevance = "compare_payload"
	}
	judgments := []any{}
	for _, role := range []string{"factual", "quality"} {
		judgments = append(judgments, map[string]any{
			"role": role, "reviewer": names[role], "signed_at": "2026-11-10T13:10:00Z", "history_id": "history_row",
			"pending_sha256": strings.Repeat("a", 64), "registry_sha256": screen["registry_sha256"], "registry_occurrences_sha256": digest(occurrences),
			"origin": clone(origin), "selected_entry_sha256": digestBytes(selected), "recovered_board_sha256": recoveredSHA, "recovery_correspondence_checked": true,
			"items": []any{map[string]any{"id": row["id"], "record_sha256": digest(row), "relevance": relevance, "rationale": role + " independently checked the exact retained entry and recovered mapping against this new item", "original_entry_checked": true}},
		})
	}
	entry := map[string]any{"id": "history_row", "registry_occurrences": occurrences, "origin": origin, "retained_source": ref, "selected_entry_sha256": digestBytes(selected), "selected_entry": string(selected), "recovered_board": recovered, "judgments": judgments}
	closure := map[string]any{"schema": "quick-history-closure-v1", "pending_sha256": strings.Repeat("a", 64), "registry_sha256": screen["registry_sha256"], "items": []any{entry}}
	// Exercise actual serialized bytes and strict decoding, including explicit
	// JSON null recovery bindings and native screen []string -> wire []any.
	wireRef := f.put("history-wire.json", map[string]any{"pending": pending, "closure": closure})
	wireBytes, err := os.ReadFile(text(wireRef["path"]))
	if err != nil {
		t.Fatal(err)
	}
	wire, err := pendingDecode(wireBytes, MaxBytes)
	if err != nil {
		t.Fatal(err)
	}
	f.material["operator_replay"] = map[string]any{"created_at": "2026-11-10T15:00:00Z"}
	return &bridgeRecoveryFixture{f, snap, object(wire["pending"]), object(wire["closure"]), names}
}
func (f *bridgeRecoveryFixture) check(closure map[string]any) error {
	return bridgeHistory(f.snap, f.pending, closure, f.names, f.f.material, f.f.files)
}
func bridgeRecoveryEntry(closure map[string]any) map[string]any {
	return object(rows(closure["items"])[0])
}
func bridgeRecoveryRole(closure map[string]any, role string) map[string]any {
	for _, value := range rows(bridgeRecoveryEntry(closure)["judgments"]) {
		r := object(value)
		if r["role"] == role {
			return r
		}
	}
	return nil
}
func TestQuickBridgeRecoveryWireFixturesKeepHistoricalFingerprintsWithoutRatingThem(t *testing.T) {
	for _, game := range []string{"intrusul", "perechi"} {
		for _, mode := range []string{"unrelated", "recovered"} {
			t.Run(game+"/"+mode, func(t *testing.T) {
				f := newBridgeRecoveryFixture(t, game, mode)
				if _, ok := object(f.pending["screen"])["unresolved_quick_history"].([]any); !ok {
					t.Fatal("fixture did not cross native JSON wire boundary")
				}
				if err := f.check(f.closure); err != nil {
					t.Fatal(err)
				}
				if mode == "recovered" {
					// Existing canonical owners, deliberately weak historical graph:
					// re-rating the old rejection would lose negative fingerprints.
					// Only the NEW row is rated by ValidateQuickRows.
					newRow := object(rows(f.pending["boards"])[0])
					old := object(clone(newRow))
					old["payload"] = object(bridgeRecoveryEntry(f.closure)["recovered_board"])["payload"]
					kg, err := f.snap.object("cat_de_roman_esti/fixtures/kg_sample.json")
					if err != nil {
						t.Fatal(err)
					}
					g, err := contentbuild.QuickGraphSnapshot(kg)
					if err != nil {
						t.Fatal(err)
					}
					if _, err = contentbuild.RateQuick(old, g); err == nil {
						t.Fatal("old negative-control payload unexpectedly meets current rating floors")
					}
				}
			})
		}
	}
}
func TestQuickBridgeRecoveryPayloadCannotChangeAfterOriginalRoleJudgments(t *testing.T) {
	for _, game := range []string{"intrusul", "perechi"} {
		t.Run(game, func(t *testing.T) {
			f := newBridgeRecoveryFixture(t, game, "collision")
			if err := f.check(f.closure); err == nil || !strings.Contains(err.Error(), "recovered-stock collision") {
				t.Fatal("exact original historical collision was not retained", err)
			}
			originalRoles, err := contentbuild.Canonical(bridgeRecoveryEntry(f.closure)["judgments"])
			if err != nil {
				t.Fatal(err)
			}
			for _, payload := range []map[string]any{map[string]any{}, bridgeRecoveryOldPayload(game)} {
				bad := object(clone(f.closure))
				object(bridgeRecoveryEntry(bad)["recovered_board"])["payload"] = payload
				roles, err := contentbuild.Canonical(bridgeRecoveryEntry(bad)["judgments"])
				if err != nil {
					t.Fatal(err)
				}
				if !bytes.Equal(originalRoles, roles) {
					t.Fatal("test changed the original role statements")
				}
				if err = f.check(bad); err == nil {
					t.Fatal("author changed only recovered payload while old role statements remained signed")
				}
			}
		})
	}
}
func TestQuickBridgeRecoveryRequiresBothExactOriginalRoleBindings(t *testing.T) {
	for _, game := range []string{"intrusul", "perechi"} {
		for _, role := range []string{"factual", "quality"} {
			for name, change := range map[string]func(map[string]any){
				"digest mismatch":              func(r map[string]any) { r["recovered_board_sha256"] = strings.Repeat("b", 64) },
				"null mismatch":                func(r map[string]any) { r["recovered_board_sha256"] = nil },
				"missing digest":               func(r map[string]any) { delete(r, "recovered_board_sha256") },
				"origin mismatch":              func(r map[string]any) { object(r["origin"])["scope"] = "substituted" },
				"selected entry mismatch":      func(r map[string]any) { r["selected_entry_sha256"] = strings.Repeat("b", 64) },
				"history id mismatch":          func(r map[string]any) { r["history_id"] = "another original" },
				"registry occurrence mismatch": func(r map[string]any) { r["registry_occurrences_sha256"] = strings.Repeat("b", 64) },
				"pending mismatch":             func(r map[string]any) { r["pending_sha256"] = strings.Repeat("b", 64) },
				"registry mismatch":            func(r map[string]any) { r["registry_sha256"] = strings.Repeat("b", 64) },
				"false correspondence":         func(r map[string]any) { r["recovery_correspondence_checked"] = false },
				"missing correspondence":       func(r map[string]any) { delete(r, "recovery_correspondence_checked") },
				"new item mismatch":            func(r map[string]any) { object(rows(r["items"])[0])["record_sha256"] = strings.Repeat("b", 64) },
				"unknown item":                 func(r map[string]any) { object(rows(r["items"])[0])["id"] = "unknown" },
				"missing item":                 func(r map[string]any) { r["items"] = []any{} },
				"unknown field":                func(r map[string]any) { r["Root_already_confirmed"] = true },
			} {
				t.Run(game+"/"+role+"/"+name, func(t *testing.T) {
					f := newBridgeRecoveryFixture(t, game, "recovered")
					bad := object(clone(f.closure))
					change(bridgeRecoveryRole(bad, role))
					if err := f.check(bad); err == nil {
						t.Fatal("one original role recovery binding was not required")
					}
				})
			}
		}
	}
}
func TestQuickBridgeRecoveryExplicitNullAndBothRolesAreMandatory(t *testing.T) {
	for _, game := range []string{"intrusul", "perechi"} {
		for _, role := range []string{"factual", "quality"} {
			t.Run(game+"/"+role, func(t *testing.T) {
				f := newBridgeRecoveryFixture(t, game, "unrelated")
				for _, mutate := range []func(map[string]any){func(r map[string]any) { delete(r, "recovered_board_sha256") }, func(r map[string]any) { r["recovered_board_sha256"] = digest(nil) }, func(r map[string]any) { r["recovery_correspondence_checked"] = false }} {
					bad := object(clone(f.closure))
					mutate(bridgeRecoveryRole(bad, role))
					if err := f.check(bad); err == nil {
						t.Fatal("missing/null-string/false correspondence recovery binding accepted")
					}
				}
			})
		}
		t.Run(game+"/missing-role", func(t *testing.T) {
			f := newBridgeRecoveryFixture(t, game, "recovered")
			bad := object(clone(f.closure))
			entry := bridgeRecoveryEntry(bad)
			entry["judgments"] = rows(entry["judgments"])[:1]
			if err := f.check(bad); err == nil {
				t.Fatal("missing original reviewer accepted")
			}
		})
	}
}
func TestQuickBridgeRecoveredHistoricalPayloadShapesFailClosedBeforeStock(t *testing.T) {
	for _, game := range []string{"intrusul", "perechi"} {
		changes := map[string]func(map[string]any){
			"empty":                 func(b map[string]any) { b["payload"] = map[string]any{} },
			"unknown game":          func(b map[string]any) { b["game"] = "conexiuni" },
			"unknown board field":   func(b map[string]any) { b["approved"] = true },
			"unknown payload field": func(b map[string]any) { object(b["payload"])["approved"] = true },
		}
		if game == "intrusul" {
			changes["missing member"] = func(b map[string]any) { object(b["payload"])["members"] = []any{"old_a", "old_b"} }
			changes["duplicate member"] = func(b map[string]any) { object(b["payload"])["members"] = []any{"old_a", "old_a", "old_c"} }
			changes["blank identity"] = func(b map[string]any) { rows(object(b["payload"])["members"])[0] = " " }
			changes["outsider in trio"] = func(b map[string]any) { p := object(b["payload"]); p["intruder"] = rows(p["members"])[0] }
			changes["blank label"] = func(b map[string]any) { object(b["payload"])["group_label"] = " " }
			changes["punctuation label"] = func(b map[string]any) { object(b["payload"])["group_label"] = "...?!" }
		} else {
			changes["missing pair"] = func(b map[string]any) { p := object(b["payload"]); p["pairs"] = rows(p["pairs"])[:3] }
			changes["duplicate identity across pairs"] = func(b map[string]any) {
				pairs := rows(object(b["payload"])["pairs"])
				rows(object(pairs[1])["members"])[0] = rows(object(pairs[0])["members"])[0]
			}
			changes["empty pair"] = func(b map[string]any) { rows(object(b["payload"])["pairs"])[0] = map[string]any{} }
			changes["one member"] = func(b map[string]any) { object(rows(object(b["payload"])["pairs"])[0])["members"] = []any{"old_a"} }
			changes["blank label"] = func(b map[string]any) { object(rows(object(b["payload"])["pairs"])[0])["group_label"] = " " }
			changes["punctuation label"] = func(b map[string]any) { object(rows(object(b["payload"])["pairs"])[0])["group_label"] = "...?!" }
			changes["blank identity"] = func(b map[string]any) { rows(object(rows(object(b["payload"])["pairs"])[0])["members"])[0] = " " }
			changes["unknown pair field"] = func(b map[string]any) { object(rows(object(b["payload"])["pairs"])[0])["approved"] = true }
		}
		for name, change := range changes {
			t.Run(game+"/"+name, func(t *testing.T) {
				f := newBridgeRecoveryFixture(t, game, "recovered")
				bad := object(clone(f.closure))
				entry := bridgeRecoveryEntry(bad)
				board := object(entry["recovered_board"])
				change(board)
				// Even two newly matching digest strings are insufficient for a
				// malformed fingerprint. Shape validation precedes all stock use.
				for _, value := range rows(entry["judgments"]) {
					object(value)["recovered_board_sha256"] = digest(board)
				}
				if err := f.check(bad); err == nil || !strings.Contains(err.Error(), "recovered") {
					t.Fatal("malformed recovered payload reached stock", err)
				}
			})
		}
	}
}

func TestQuickBridgeRelevantUnresolvedHistoricalOwnersStayParked(t *testing.T) {
	for _, game := range []string{"intrusul", "perechi"} {
		t.Run(game, func(t *testing.T) {
			f := newBridgeRecoveryFixture(t, game, "unresolved")
			// Both exact role digests/correspondence attestations are present, but
			// unresolved legacy IDs do not become disjoint current-ID fingerprints.
			if err := f.check(f.closure); err == nil || !strings.Contains(err.Error(), "owner identity unresolved") {
				t.Fatal("unresolvable relevant owners silently passed novelty", err)
			}
		})
	}
}

func TestQuickBridgeEveryRelevantRecoveredOwnerMustResolve(t *testing.T) {
	for _, game := range []string{"intrusul", "perechi"} {
		t.Run(game, func(t *testing.T) {
			f := newBridgeRecoveryFixture(t, game, "recovered")
			bad := object(clone(f.closure))
			entry := bridgeRecoveryEntry(bad)
			board := object(entry["recovered_board"])
			payload := object(board["payload"])
			if game == "intrusul" {
				payload["intruder"] = "legacy_alias_not_a_current_owner"
			} else {
				pairs := rows(payload["pairs"])
				rows(object(pairs[len(pairs)-1])["members"])[1] = "legacy_alias_not_a_current_owner"
			}
			for _, value := range rows(entry["judgments"]) {
				object(value)["recovered_board_sha256"] = digest(board)
			}
			if err := f.check(bad); err == nil || !strings.Contains(err.Error(), "owner identity unresolved") {
				t.Fatal("one unresolved owner/alias silently passed the recovered fingerprint", err)
			}
		})
	}
}

func TestQuickBridgeRelevantButUnrecoverableHistoryCannotUseNull(t *testing.T) {
	for _, game := range []string{"intrusul", "perechi"} {
		t.Run(game, func(t *testing.T) {
			f := newBridgeRecoveryFixture(t, game, "recovered")
			bad := object(clone(f.closure))
			entry := bridgeRecoveryEntry(bad)
			entry["recovered_board"] = nil
			for _, value := range rows(entry["judgments"]) {
				object(value)["recovered_board_sha256"] = nil
			}
			if err := f.check(bad); err == nil || !strings.Contains(err.Error(), "must be recovered") {
				t.Fatal("relevant but unrecoverable original was silently closed", err)
			}
		})
	}
}
