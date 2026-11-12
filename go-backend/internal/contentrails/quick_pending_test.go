//go:build linux

package contentrails

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/testfixture"
)

func pendingTestRow() map[string]any {
	return map[string]any{"id": "iq92_synthetic", "game": "intrusul", "source_id": "aq92_synthetic", "category": "viata_de_roman", "difficulty": "normal", "payload": map[string]any{"members": []any{"pending_n0", "pending_n1", "pending_n2"}, "intruder": "pending_n3", "group_label": "SENTINEL_PREDICATE_PRIVATE"}, "sources": []any{"https://example.test/SENTINEL_AUTHOR_PRIVATE"}, "rationale": "SENTINEL_RATIONALE_PRIVATE"}
}
func pendingTestKG() map[string]any {
	nodes, edges := []any{}, []any{}
	for i := 0; i < 4; i++ {
		nodes = append(nodes, map[string]any{"id": fmt.Sprintf("pending_n%d", i), "node_type": "concept", "label_ro": fmt.Sprintf("Cuvânt %d", i), "category": "viata_de_roman", "salience": .9})
	}
	for i := 0; i < 3; i++ {
		for j := i + 1; j < 3; j++ {
			edges = append(edges, map[string]any{"id": fmt.Sprintf("edge_%d_%d", i, j), "src_id": fmt.Sprintf("pending_n%d", i), "dst_id": fmt.Sprintf("pending_n%d", j), "strength": .8})
		}
	}
	return map[string]any{"kg_nodes": nodes, "kg_edges": edges}
}
func pendingTestSnapshot(t *testing.T, records []any) *quickPendingSnapshot {
	t.Helper()
	s := &quickPendingSnapshot{source: &Source{Raw: map[string]any{"quick": map[string]any{"boards": []any{}}}, SHA256: strings.Repeat("a", 64), Version: 25}, files: map[string][]byte{}, manifest: map[string]any{"schema": "synthetic-inventory"}}
	for p, v := range map[string]any{
		"docs/content-registry/exclusions.json":                          map[string]any{"schema": "cat-content-exclusions-1", "owner_rules": map[string]any{"held_families": map[string]any{"labels_ro": []any{"Mănăstire", "Sucitor"}}}, "owner_held_conexiuni": []any{"cx_locked"}, "board_controls": []any{}},
		"cat_de_roman_esti/fixtures/kg_sample.json":                      pendingTestKG(),
		"cat_de_roman_esti/fixtures/quick_games_v92.json":                map[string]any{"boards": []any{}},
		"cat_de_roman_esti/fixtures/derived_catalog_v38.json":            map[string]any{"boards": []any{}},
		"cat_de_roman_esti/fixtures/games_pack.json":                     map[string]any{"conexiuni": []any{}},
		"cat_de_roman_esti/fixtures/conexiuni_rejection_tombstones.json": map[string]any{"items": map[string]any{}},
	} {
		b, err := Render(v)
		if err != nil {
			t.Fatal(err)
		}
		s.files[p] = b
	}
	for _, r := range records {
		b, err := Render(r)
		if err != nil {
			t.Fatal(err)
		}
		compact, err := contentbuild.Canonical(object(r))
		if err != nil {
			t.Fatal(err)
		}
		_ = b
		s.files["docs/content-registry/registry.jsonl"] = append(s.files["docs/content-registry/registry.jsonl"], append(compact, '\n')...)
	}
	return s
}
func pendingTestRegistry(kind, state string, payload map[string]any) map[string]any {
	return map[string]any{"schema": "cat-content-candidate-1", "id": "history_row", "type": kind, "state": state, "payload": payload}
}
func TestQuickPendingPacketStrictSchemaNamespacesCapsAndJSON(t *testing.T) {
	s := &Source{Raw: map[string]any{"quick": map[string]any{"boards": []any{}}}, SHA256: strings.Repeat("a", 64)}
	packet := map[string]any{"schema": "quick-author-packet-v1", "baseline_source_sha256": s.SHA256, "boards": []any{pendingTestRow()}}
	if _, err := pendingPacket(packet, s); err != nil {
		t.Fatal(err)
	}
	for _, mutate := range []func(map[string]any){
		func(p map[string]any) { p["nodes"] = []any{} },
		func(p map[string]any) { p["baseline_source_sha256"] = strings.Repeat("b", 64) },
		func(p map[string]any) { object(rows(p["boards"])[0])["id"] = "vi_0123456789abcdef0123" },
		func(p map[string]any) { object(rows(p["boards"])[0])["id"] = "pq92_wrong_game" },
		func(p map[string]any) { object(rows(p["boards"])[0])["id"] = "iq92_../escape" },
		func(p map[string]any) { object(rows(p["boards"])[0])["sources"] = []any{} },
		func(p map[string]any) { object(rows(p["boards"])[0])["approval"] = true },
		func(p map[string]any) { p["boards"] = []any{pendingTestRow(), pendingTestRow()} },
	} {
		p := object(clone(packet))
		mutate(p)
		if _, err := pendingPacket(p, s); err == nil {
			t.Fatal("bad packet accepted", p)
		}
	}
	for _, b := range [][]byte{[]byte(`{"x":1,"x":2}`), []byte(`{} {}`), []byte(`{"x":NaN}`)} {
		if _, err := pendingDecode(b, MaxBytes); err == nil {
			t.Fatal("non-strict pending JSON accepted")
		}
	}
	if _, err := pendingDecode(make([]byte, MaxBytes+1), MaxBytes); err == nil {
		t.Fatal("byte bound passed")
	}
}
func TestQuickPendingAuthorEvidenceExactCoverageCapturesAndChronology(t *testing.T) {
	packet := []byte("exact packet bytes")
	capture := []byte("captured source body")
	seal := map[string]any{"schema": "quick-author-seal-v1", "author": "synthetic author", "packet_sha256": digestBytes(packet), "sealed_at": "2026-11-10T12:00:00Z", "urls": []any{"https://example.test/SENTINEL_AUTHOR_PRIVATE"}}
	evidence := map[string]any{"schema": "quick-author-evidence-v1", "packet_sha256": digestBytes(packet), "items": map[string]any{"iq92_synthetic": "source_backed"}, "receipts": []any{map[string]any{"url": "https://example.test/SENTINEL_AUTHOR_PRIVATE", "capture_path": "/scratch/body", "capture_sha256": digestBytes(capture), "bytes": len(capture), "fetched_by_role": "author", "fetched_at": "2026-11-10T11:59:00Z"}}}
	caps := map[string][]byte{"/scratch/body": capture}
	if err := pendingEvidence(packet, []any{pendingTestRow()}, seal, evidence, caps); err != nil {
		t.Fatal(err)
	}
	for _, mutate := range []func(map[string]any){
		func(e map[string]any) { object(e["items"])["iq92_synthetic"] = "kg_only" },
		func(e map[string]any) { object(rows(e["receipts"])[0])["capture_sha256"] = strings.Repeat("b", 64) },
		func(e map[string]any) { object(rows(e["receipts"])[0])["fetched_at"] = "2026-11-10T12:01:00Z" },
		func(e map[string]any) { object(rows(e["receipts"])[0])["fetched_by_role"] = "legacy" },
		func(e map[string]any) { e["receipts"] = []any{} },
	} {
		e := object(clone(evidence))
		mutate(e)
		if err := pendingEvidence(packet, []any{pendingTestRow()}, seal, e, caps); err == nil {
			t.Fatal("unbound evidence accepted", e)
		}
	}
	if err := pendingEvidence([]byte("changed"), []any{pendingTestRow()}, seal, evidence, caps); err == nil {
		t.Fatal("stale packet accepted")
	}
}
func TestQuickPendingTypeSpecificHoldsAndUnresolvedDeadHistory(t *testing.T) {
	row := pendingTestRow()
	g, err := contentbuild.QuickGraphSnapshot(pendingTestKG())
	if err != nil {
		t.Fatal(err)
	}
	rating, err := contentbuild.RateQuick(row, g)
	if err != nil {
		t.Fatal(err)
	}
	for _, kind := range []string{"concept", "name", "form"} {
		record := pendingTestRegistry(kind, "held_owner", map[string]any{"node_id": "pending_n0"})
		s := pendingTestSnapshot(t, []any{record})
		_, err := pendingScreen(s, []any{row}, []any{rating})
		if kind == "form" && err != nil {
			t.Fatal("held form became a blanket board owner ban", err)
		}
		if kind != "form" && err == nil {
			t.Fatal("held owner escaped via board reference", kind)
		}
	}
	s := pendingTestSnapshot(t, []any{pendingTestRegistry("board.intrusul", "rejected", map[string]any{})})
	screen, err := pendingScreen(s, []any{row}, []any{rating})
	if err != nil || screen["complete"] != false || len(ids(screen["unresolved_quick_history"])) != 1 {
		t.Fatal("empty dead record silently passed full history screen", screen, err)
	}
	s = pendingTestSnapshot(t, []any{pendingTestRegistry("board.intrusul", "rejected", object(row["payload"]))})
	if _, err := pendingScreen(s, []any{row}, []any{rating}); err == nil {
		t.Fatal("dead payload evaded stock check")
	}
}
func TestQuickPendingNativeProjectionAndDossierKeepAnswersPrivate(t *testing.T) {
	row := pendingTestRow()
	snap := pendingTestSnapshot(t, nil)
	g, err := contentbuild.QuickGraphSnapshot(pendingTestKG())
	if err != nil {
		t.Fatal(err)
	}
	rated, nodes, err := contentbuild.ValidateQuickRows([]any{row}, nil, g)
	if err != nil {
		t.Fatal(err)
	}
	data, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	data = quickOverlay(data, g, rated)
	before, _ := Render(row)
	public, private, err := pendingProjection(context.Background(), data, row, object(rated[0]), "0123456789abcdef01234567")
	if err != nil {
		t.Fatal(err)
	}
	pb, _ := Render(public)
	for _, sentinel := range []string{"pending_n", "SENTINEL_", "iq92_", "aq92_", "vi_", "http", "intruder", "members", "group_label"} {
		if strings.Contains(string(pb), sentinel) {
			t.Fatal("public projection leaked", sentinel)
		}
	}
	if object(private["expected_answer"])["predicate"] != "SENTINEL_PREDICATE_PRIVATE" || private["initial_get_equal"] != true {
		t.Fatal("private key/native GET proof absent")
	}
	after, _ := Render(row)
	if string(before) != string(after) {
		t.Fatal("projection mutated authored input")
	}
	opt := QuickPendingOptions{Packet: "/scratch/packet", AuthorSeal: "/scratch/seal", ReceiptManifest: "/scratch/evidence"}
	inputs := map[string][]byte{opt.Packet: []byte("packet"), opt.AuthorSeal: []byte("seal"), opt.ReceiptManifest: []byte("evidence")}
	bundle, err := pendingBundle(context.Background(), snap, []any{row}, rated, nodes, data, inputs, opt, map[string]any{"complete": false}, map[string]any{"sha256": strings.Repeat("a", 64)})
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "bundle.json")
	writeJSONTest(t, path, bundle)
	for _, view := range []string{"public", "dossier"} {
		viewBytes, err := QuickPendingView(path, "iq92_synthetic", view)
		if err != nil {
			t.Fatal(err)
		}
		if view == "dossier" && (strings.Contains(string(viewBytes), "SENTINEL_AUTHOR_PRIVATE") || strings.Contains(string(viewBytes), "SENTINEL_RATIONALE_PRIVATE")) {
			t.Fatal("reviewer dossier disclosed author evidence")
		}
	}
	bad := object(clone(bundle))
	object(rows(bad["members"])[1])["data"] = "changed public bytes"
	writeJSONTest(t, path, bad)
	if _, err := QuickPendingView(path, "iq92_synthetic", "public"); err == nil {
		t.Fatal("changed member passed")
	}
	if _, err := QuickPendingView(path, "iq92_synthetic", "private"); err == nil {
		t.Fatal("private answer view exposed")
	}
}
func TestQuickPendingScratchAndGuardedReadsetRefuseMutation(t *testing.T) {
	root, scratch := t.TempDir(), testfixture.NativePendingDir(t)
	if err := os.Chmod(root, 0700); err != nil {
		t.Fatal(err)
	}
	if err := pendingScratch(root, filepath.Join(root, "bad.json")); err == nil || err.Error() != "pending output must be outside repository" {
		t.Fatal("expected repository output refusal", err)
	}
	if err := os.Mkdir(filepath.Join(scratch, ".git"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := pendingScratch(root, filepath.Join(scratch, "bad.json")); err == nil || err.Error() != "pending output must be outside all Git checkouts" {
		t.Fatal("expected other checkout output refusal", err)
	}
	if err := os.Remove(filepath.Join(scratch, ".git")); err != nil {
		t.Fatal(err)
	}
	input := filepath.Join(root, "input.json")
	if err := os.WriteFile(input, []byte("baseline"), 0600); err != nil {
		t.Fatal(err)
	}
	readset, err := contentops.CaptureRegularReadSet([]string{input})
	if err != nil {
		t.Fatal(err)
	}
	out := filepath.Join(scratch, "bundle.json")
	publishedAndMutated := false
	err = contentbuild.WritePrivatePendingArtifact(out, []byte("private"), func(publish func() error) error {
		return contentops.GuardedTransaction(scratch, nil, readset, func() error {
			if err := publish(); err != nil {
				return err
			}
			if err := os.WriteFile(input, []byte("changed"), 0600); err != nil {
				return err
			}
			publishedAndMutated = true
			return nil
		})
	})
	if !publishedAndMutated || err == nil || err.Error() != "strict pending readset changed: "+input {
		t.Fatal("expected readset refusal after publication and input mutation", publishedAndMutated, err)
	}
	if _, err := os.Lstat(out); !os.IsNotExist(err) {
		t.Fatal("failed guarded pending publication remained", err)
	}
	link := filepath.Join(scratch, "link")
	if err := os.Symlink(root, link); err != nil {
		t.Fatal(err)
	}
	if _, err := pendingRegular(filepath.Join(link, "input.json"), 1<<20); err == nil || !strings.Contains(err.Error(), "without symlinks") {
		t.Fatal("expected symlinked pending input refusal", err)
	}
}
