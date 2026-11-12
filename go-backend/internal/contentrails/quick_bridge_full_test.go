//go:build linux

package contentrails

import (
	"context"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// These fixtures exercise confirmation rules, not a real pending/source grant.
// They never change a fixture, installed source, pin or authority file.
func bridgeCanonicalFixture(t *testing.T) (*quickBridgeSession, map[string]any, map[string]any, map[string]any, map[string]any, map[string]any, map[string]any) {
	t.Helper()
	f := newBridgeFixture(t)
	newRow := object(rows(f.pending["boards"])[0])
	newID := text(newRow["id"])
	f.dossiers[newID]["record_sha256"] = digest(newRow)
	for _, role := range []string{"factual", "quality"} {
		f.changeRaw(role, func(r map[string]any) { object(rows(r["items"])[0])["record_sha256"] = digest(newRow) })
	}
	raw, names, err := bridgeReviews(f.pending, f.dossiers, f.material, f.files)
	if err != nil {
		t.Fatal(err)
	}
	f.material["operator_replay"] = map[string]any{"created_at": "2026-11-10T15:00:00Z"}
	old := map[string]any{"id": "iq92_old_synthetic", "game": "intrusul", "payload": map[string]any{"test": "old private payload"}}
	session := &quickBridgeSession{frameSHA: strings.Repeat("a", 64), pending: f.pending, raw: raw, names: names, material: f.material, snap: &quickPendingSnapshot{source: &Source{Raw: map[string]any{"quick": map[string]any{"boards": []any{old}}}}}}
	sha := strings.Repeat("b", 64)
	baselineItem := map[string]any{"id": old["id"], "verdict": "accept", "rationale": "original baseline fixture rationale", "sources": []any{"https://example.test/old"}}
	evidence := map[string]any{"schema": "quick-baseline-evidence-v1", "review": map[string]any{"path": "synthetic-baseline.json", "sha256": sha}}
	baseline := map[string]any{text(old["id"]): baselineItem}
	release := map[string]any{"prepare_bundle": map[string]any{"sha256": sha}, "factual_review": map[string]any{"sha256": sha}}
	draft := map[string]any{"source_sha256": strings.Repeat("c", 64), "candidate_sha256": strings.Repeat("d", 64)}
	original := object(rows(object(raw[0])["items"])[0])
	rawSHA := f.material["factual_envelope"]["review_sha256"]
	items := []any{
		map[string]any{"id": old["id"], "verdict": "accept", "rationale": "Fresh baseline evidence considered for this whole candidate", "sources": baselineItem["sources"], "inherited": true, "evidence_basis": map[string]any{"schema": "quick-baseline-binding-v1", "record_sha256": digest(old), "baseline_item_sha256": digest(baselineItem), "baseline_review_sha256": sha, "child_safe": true}},
		map[string]any{"id": original["id"], "verdict": original["verdict"], "rationale": original["rationale"], "sources": original["sources"], "evidence_basis": map[string]any{"schema": "quick-raw-binding-v1", "review_binding": original["review_binding"], "record_sha256": original["record_sha256"], "raw_review_sha256": rawSHA, "child_safe": true}},
	}
	report := map[string]any{"kind": "quick-content-review-v1", "role": "factual", "reviewer": names["factual"], "candidate_sha256": draft["candidate_sha256"], "items": items, "baseline_evidence": map[string]any{"schema": "quick-bridge-canonical-binding-v1", "frame_sha256": session.frameSHA, "prepare_bundle_sha256": sha, "source_sha256": draft["source_sha256"], "baseline": evidence}, "evidence_sha256": session.frameSHA, "inherited_review_sha256": sha}
	confirm := map[string]any{"schema": "quick-full-candidate-confirmation-v1", "role": "factual", "reviewer": names["factual"], "signed_at": "2026-11-10T16:00:00Z", "first_peer_read_at": nil, "frame_sha256": session.frameSHA, "prepare_bundle_sha256": sha, "source_sha256": draft["source_sha256"], "candidate_sha256": draft["candidate_sha256"], "canonical_review_sha256": sha, "baseline_evidence": evidence, "verdict": "accept", "rationale": "Fresh exact entire authored candidate and baseline checked", "items": []any{map[string]any{"id": old["id"], "record_sha256": digest(old), "child_safe": true, "evidence_checked": true, "evidence_basis": "baseline_unchanged"}, map[string]any{"id": newID, "record_sha256": digest(newRow), "child_safe": true, "evidence_checked": true, "evidence_basis": "fresh_raw"}}}
	return session, report, confirm, release, draft, evidence, baseline
}
func TestQuickBridgeCanonicalRequiresFreshOriginalWholeCandidateAndLosslessNewRows(t *testing.T) {
	s, r, c, release, draft, evidence, baseline := bridgeCanonicalFixture(t)
	if err := bridgeCanonical(s, "factual", 0, r, c, release, draft, evidence, baseline); err != nil {
		t.Fatal(err)
	}
	for name, change := range map[string]func(map[string]any, map[string]any){
		"wrong identity":           func(r, c map[string]any) { r["reviewer"] = "another reviewer" },
		"wrong role":               func(r, c map[string]any) { c["role"] = "quality" },
		"new rationale translated": func(r, c map[string]any) { object(rows(r["items"])[1])["rationale"] = "edited rationale" },
		"new URL translated": func(r, c map[string]any) {
			object(rows(r["items"])[1])["sources"] = []any{"https://example.test/changed"}
		},
		"hold":          func(r, c map[string]any) { object(rows(r["items"])[1])["verdict"] = "hold" },
		"quality keep":  func(r, c map[string]any) { object(rows(r["items"])[1])["verdict"] = "keep" },
		"old omitted":   func(r, c map[string]any) { r["items"] = rows(r["items"])[1:] },
		"duplicate old": func(r, c map[string]any) { rows(r["items"])[1] = rows(r["items"])[0] },
		"old record changed": func(r, c map[string]any) {
			object(object(rows(r["items"])[0])["evidence_basis"])["record_sha256"] = strings.Repeat("e", 64)
		},
		"missing old evidence": func(r, c map[string]any) { delete(object(rows(r["items"])[0]), "evidence_basis") },
		"unconfirmed old":      func(r, c map[string]any) { c["items"] = rows(c["items"])[1:] },
		"false child safety":   func(r, c map[string]any) { object(rows(c["items"])[1])["child_safe"] = false },
		"stale confirmation":   func(r, c map[string]any) { c["signed_at"] = "2026-11-10T15:00:00Z" },
		"candidate mismatch":   func(r, c map[string]any) { c["candidate_sha256"] = strings.Repeat("e", 64) },
		"draft not confirmed":  func(r, c map[string]any) { r["kind"] = "quick-canonical-review-draft-v1" },
	} {
		t.Run(name, func(t *testing.T) {
			badR, badC := object(clone(r)), object(clone(c))
			change(badR, badC)
			if err := bridgeCanonical(s, "factual", 0, badR, badC, release, draft, evidence, baseline); err == nil {
				t.Fatal("canonical confirmation bypass")
			}
		})
	}
}
func TestQuickBridgeGenericInstallerCannotOmitMandatoryGuard(t *testing.T) {
	root := rootPath(t)
	base, err := pendingCurrentSource(root)
	if err != nil {
		t.Fatal(err)
	}
	for _, change := range []func(map[string]any){
		func(raw map[string]any) {
			q := object(raw["quick"])
			q["boards"] = append(rows(q["boards"]), clone(object(rows(q["boards"])[0])))
			object(rows(q["boards"])[len(rows(q["boards"]))-1])["id"] = "iq92_synthetic_added"
		},
		func(raw map[string]any) {
			object(rows(object(raw["quick"])["boards"])[0])["payload"] = map[string]any{"synthetic": "changed"}
		},
		func(raw map[string]any) { q := object(raw["quick"]); q["boards"] = rows(q["boards"])[1:] },
	} {
		next := &Source{Raw: object(clone(base.Raw)), SHA256: base.SHA256, Version: base.Version}
		change(next.Raw)
		err = InstallProposal(root, next, "quick", "missing", "missing", "missing", "missing", "missing", "missing", "missing", "missing", "missing")
		if err == nil || !strings.Contains(err.Error(), "mandatory V4") {
			t.Fatal("generic native installer bypassed raw bridge", err)
		}
	}
	same := &Source{Raw: object(clone(base.Raw)), SHA256: base.SHA256, Version: base.Version}
	object(rows(object(same.Raw["quick"])["boards"])[0])["rationale"] = "metadata-only annotation"
	if needed, e := quickNeedsBridge(root, same); e != nil || needed {
		t.Fatal("metadata-only native rebind was mistaken for gameplay delta", e)
	}
}
func TestQuickBridgeHistoryRequiresExactOriginalEntryAndIndependentPerItemRelevance(t *testing.T) {
	f := newBridgeFixture(t)
	source := map[string]any{"records": []any{map[string]any{"id": "original-synthetic-id", "text": "original unapproved research"}}}
	ref := f.put("historical.json", source)
	origin := map[string]any{"path": "historical.json", "scope": "synthetic-test-only", "line": 1, "pointer": "/records/0", "sha256": ref["sha256"]}
	record := pendingTestRegistry("board.intrusul", "held_recorded", map[string]any{})
	record["origin"] = map[string]any{"id": "original-synthetic-id", "source": origin}
	snap := pendingTestSnapshot(t, []any{record})
	row := pendingTestRow()
	g, err := contentbuild.QuickGraphSnapshot(pendingTestKG())
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
	// bridgeHistory consumes decoded native wire JSON, not pendingScreen's
	// in-memory []string representation. Production array guards stay strict.
	screen = object(clone(screen))
	f.material["operator_replay"] = map[string]any{"created_at": "2026-11-10T15:00:00Z"}
	pending := map[string]any{"boards": []any{row}, "screen": screen, "_bridge": map[string]any{"pending_sha256": strings.Repeat("a", 64)}}
	selected, err := contentbuild.Canonical(rows(source["records"])[0])
	if err != nil {
		t.Fatal(err)
	}
	line := strings.TrimSuffix(string(snap.files["docs/content-registry/registry.jsonl"]), "\n")
	judgments := []any{}
	names := map[string]string{"factual": "factual synthetic distinct", "quality": "quality synthetic distinct"}
	for _, role := range []string{"factual", "quality"} {
		judgments = append(judgments, map[string]any{"role": role, "reviewer": names[role], "signed_at": "2026-11-10T13:10:00Z", "items": []any{map[string]any{"id": row["id"], "record_sha256": digest(row), "relevance": "unrelated", "rationale": role + " original entry compared with exact new board", "original_entry_checked": true}}})
	}
	entry := map[string]any{"id": "history_row", "registry_occurrences": []any{map[string]any{"line": 1, "line_sha256": digestBytes([]byte(line)), "record_sha256": digest(record)}}, "origin": origin, "retained_source": ref, "selected_entry_sha256": digestBytes(selected), "selected_entry": string(selected), "recovered_board": nil, "judgments": judgments}
	closure := map[string]any{"schema": "quick-history-closure-v1", "pending_sha256": strings.Repeat("a", 64), "registry_sha256": screen["registry_sha256"], "items": []any{entry}}
	for _, value := range judgments {
		judgment := object(value)
		judgment["history_id"] = entry["id"]
		judgment["pending_sha256"] = closure["pending_sha256"]
		judgment["registry_sha256"] = closure["registry_sha256"]
		judgment["registry_occurrences_sha256"] = digest(entry["registry_occurrences"])
		judgment["origin"] = clone(origin)
		judgment["selected_entry_sha256"] = entry["selected_entry_sha256"]
		judgment["recovered_board_sha256"] = nil
		judgment["recovery_correspondence_checked"] = true
	}
	if err = bridgeHistory(snap, pending, closure, names, f.material, f.files); err != nil {
		t.Fatal(err)
	}
	for name, change := range map[string]func(map[string]any){
		"empty closure": func(c map[string]any) { c["items"] = []any{} },
		"changed source": func(c map[string]any) {
			object(object(rows(c["items"])[0])["retained_source"])["sha256"] = strings.Repeat("b", 64)
		},
		"wrong historical id": func(c map[string]any) { object(rows(c["items"])[0])["id"] = "unknown" },
		"missing reviewer": func(c map[string]any) {
			object(rows(c["items"])[0])["judgments"] = rows(object(rows(c["items"])[0])["judgments"])[:1]
		},
		"empty original": func(c map[string]any) { object(rows(c["items"])[0])["selected_entry"] = "{}" },
		"unknown relevance": func(c map[string]any) {
			object(rows(object(rows(object(rows(c["items"])[0])["judgments"])[0])["items"])[0])["relevance"] = "unresolved"
		},
	} {
		t.Run(name, func(t *testing.T) {
			bad := object(clone(closure))
			change(bad)
			if err := bridgeHistory(snap, pending, bad, names, f.material, f.files); err == nil {
				t.Fatal("unresolved historical exclusion disappeared")
			}
		})
	}
}
func TestQuickBridgeFullBundleViewNeverCreatesAnApproval(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, "draft.json")
	members := []any{}
	for _, name := range []string{"source.json", "candidate.json", "factual-draft.json", "quality-draft.json"} {
		data := []byte("synthetic " + name)
		members = append(members, map[string]any{"path": name, "bytes": len(data), "sha256": digestBytes(data), "data": string(data)})
	}
	bundle := map[string]any{"schema": "quick-full-draft-bundle-v1", "frame_sha256": "x", "pending_sha256": "x", "baseline_source_sha256": "x", "preserved_old_rows": []any{}, "core_payload_sha256": "x", "source_sha256": "x", "candidate_sha256": "x", "members": members, "qualified": false, "approval": nil}
	writeJSONTest(t, p, bundle)
	b, err := QuickFullDraftView(p, "factual-draft.json")
	if err != nil || string(b) != "synthetic factual-draft.json" {
		t.Fatal(err)
	}
	if _, err = QuickFullDraftView(p, "accept"); err == nil {
		t.Fatal("unknown authority view accepted")
	}
	canceled, cancel := context.WithCancel(context.Background())
	cancel()
	if err = (&quickInstallGuard{ctx: canceled}).verify(context.Background(), false); err == nil {
		t.Fatal("cancelled install guard ignored")
	}
	if _, err = os.Stat(filepath.Join(dir, "authority.json")); !os.IsNotExist(err) {
		t.Fatal("view wrote authority")
	}
}

func TestQuickBridgeFullConfirmationPeerBlindness(t *testing.T) {
	confirmations := map[string]map[string]any{"factual": {"signed_at": "2026-11-10T16:00:00Z", "first_peer_read_at": nil}, "quality": {"signed_at": "2026-11-10T16:01:00Z", "first_peer_read_at": nil}}
	if err := bridgePeerBlindConfirmations(confirmations); err != nil {
		t.Fatal(err)
	}
	confirmations["factual"]["first_peer_read_at"] = "2026-11-10T16:01:00Z"
	if err := bridgePeerBlindConfirmations(confirmations); err == nil {
		t.Fatal("full confirmation peer exposed before both signed")
	}
	confirmations["factual"]["first_peer_read_at"] = "2026-11-10T16:01:00.000000001Z"
	if err := bridgePeerBlindConfirmations(confirmations); err != nil {
		t.Fatal(err)
	}
}

func TestQuickBridgeInstallEvidenceRaceRollsBackExistingArtifact(t *testing.T) {
	root := t.TempDir()
	target, raw := filepath.Join(root, "quick-artifact.json"), filepath.Join(t.TempDir(), "raw.json")
	if err := os.WriteFile(target, []byte("original artifact"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(raw, []byte("original raw"), 0600); err != nil {
		t.Fatal(err)
	}
	set, err := contentops.CaptureReadSet([]string{target, raw})
	if err != nil {
		t.Fatal(err)
	}
	strict, err := contentops.CaptureRegularReadSet([]string{raw})
	if err != nil {
		t.Fatal(err)
	}
	err = contentops.GuardedTransaction(root, map[string][]byte{target: []byte("reviewed next artifact")}, set, func() error {
		if e := os.WriteFile(raw, []byte("changed raw after write"), 0600); e != nil {
			return e
		}
		return strict.Verify()
	})
	if err == nil {
		t.Fatal("raw race survived final native transaction")
	}
	b, e := os.ReadFile(target)
	if e != nil || string(b) != "original artifact" {
		t.Fatal("native transaction did not restore artifact", e)
	}
	if _, e = os.Lstat(filepath.Join(root, ".cat-content-ops.lock")); !os.IsNotExist(e) {
		t.Fatal("failed transaction left lock", e)
	}
}
func TestQuickBridgeRawQualityKeepNeverPromotes(t *testing.T) {
	f := newBridgeFixture(t)
	f.changeRaw("quality", func(r map[string]any) { object(rows(r["items"])[0])["verdict"] = "keep" })
	if _, _, err := bridgeReviews(f.pending, f.dossiers, f.material, f.files); err == nil {
		t.Fatal("raw keep became canonical accept")
	}
}
func TestQuickBridgeProposalPreservesEveryOldPayloadAndScore(t *testing.T) {
	oldSource := map[string]any{"id": "iq92_old", "payload": map[string]any{"original": true}, "sources": []any{"https://example.test/original"}, "rationale": "original"}
	newSource := map[string]any{"id": "iq92_new"}
	oldRuntime := map[string]any{"id": "vi_old", "payload": oldSource["payload"], "standard_score": 80, "standard_rank": 1, "starter_rank": 1}
	currentBytes, err := Render(map[string]any{"boards": []any{oldRuntime}})
	if err != nil {
		t.Fatal(err)
	}
	s := &quickBridgeSession{snap: &quickPendingSnapshot{source: &Source{Raw: map[string]any{"quick": map[string]any{"boards": []any{oldSource}}}}, files: map[string][]byte{"cat_de_roman_esti/fixtures/quick_games_v92.json": currentBytes}}, pending: map[string]any{"boards": []any{newSource}}}
	catalog := map[string]any{"authored": []any{oldSource, newSource}, "boards": []any{clone(oldRuntime)}, "excluded": []any{}}
	object(rows(catalog["boards"])[0])["standard_rank"] = 2
	if err = bridgePreservedCatalog(s, catalog); err != nil {
		t.Fatal("rank-only recomputation refused", err)
	}
	for name, change := range map[string]func(map[string]any){
		"old row omitted": func(c map[string]any) { c["authored"] = rows(c["authored"])[1:] },
		"old provenance changed": func(c map[string]any) {
			object(rows(c["authored"])[0])["sources"] = []any{"https://example.test/replaced"}
		},
		"old payload changed": func(c map[string]any) { object(rows(c["boards"])[0])["payload"] = map[string]any{"changed": true} },
		"old score changed":   func(c map[string]any) { object(rows(c["boards"])[0])["standard_score"] = 81 },
		"silent excluded":     func(c map[string]any) { c["excluded"] = []any{"iq92_old"} },
	} {
		t.Run(name, func(t *testing.T) {
			bad := object(clone(catalog))
			change(bad)
			if err := bridgePreservedCatalog(s, bad); err == nil {
				t.Fatal("old stock drift accepted")
			}
		})
	}
}
