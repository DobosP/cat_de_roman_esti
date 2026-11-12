//go:build linux

package contentrails

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
)

// All positive data below are deliberately synthetic, private t.TempDir
// fixtures. They are not author packets, review receipts or production accepts.
type bridgeFixture struct {
	t        *testing.T
	dir      string
	files    *quickBridgeFiles
	pending  map[string]any
	dossiers map[string]map[string]any
	material map[string]map[string]any
}

func (f *bridgeFixture) put(name string, value any) map[string]any {
	f.t.Helper()
	b, err := Render(object(value))
	if err != nil {
		f.t.Fatal(err)
	}
	return f.putBytes(name, b)
}
func (f *bridgeFixture) putBytes(name string, b []byte) map[string]any {
	f.t.Helper()
	path := filepath.Join(f.dir, name)
	if err := os.WriteFile(path, b, 0600); err != nil {
		f.t.Fatal(err)
	}
	return map[string]any{"path": path, "bytes": len(b), "sha256": digestBytes(b)}
}
func newBridgeFixture(t *testing.T) *bridgeFixture {
	t.Helper()
	f := &bridgeFixture{t: t, dir: t.TempDir(), files: &quickBridgeFiles{blobs: map[string][]byte{}}, material: map[string]map[string]any{}}
	sha := strings.Repeat("a", 64)
	id := "iq92_synthetic_only"
	f.pending = map[string]any{"boards": []any{map[string]any{"id": id}}, "bindings": map[string]any{"rubric_sha256": sha}, "_bridge": map[string]any{"pending_sha256": sha}}
	f.dossiers = map[string]map[string]any{id: {"id": id, "review_binding": "sha256:" + sha, "record_sha256": sha}}
	seal := map[string]any{"schema": "quick-author-seal-v1", "author": "Author synthetic distinct", "sealed_at": "2026-11-10T12:00:00Z", "urls": []any{"https://example.test/author"}}
	ref := f.put("seal.json", seal)
	f.files.blobs[text(ref["path"])], _ = os.ReadFile(text(ref["path"]))
	object(f.pending["bindings"])["author_seal_sha256"] = ref["sha256"]
	authorBody := f.putBytes("author.body", []byte("synthetic author body"))
	authorReceipt := map[string]any{"url": "https://example.test/author", "capture_path": authorBody["path"], "capture_sha256": authorBody["sha256"], "bytes": authorBody["bytes"], "fetched_by_role": "author", "fetched_at": "2026-11-10T11:00:00Z"}
	authorEvidence := map[string]any{"schema": "quick-author-evidence-v1", "receipts": []any{authorReceipt}}
	ref = f.put("author-evidence.json", authorEvidence)
	f.files.blobs[text(ref["path"])], _ = os.ReadFile(text(ref["path"]))
	object(f.pending["bindings"])["author_evidence_sha256"] = ref["sha256"]
	f.material["author_release"] = map[string]any{"schema": "quick-review-release-v1", "author": seal["author"], "author_seal_sha256": object(f.pending["bindings"])["author_seal_sha256"], "pending_sha256": sha, "unsealed_at": "2026-11-10T14:00:00Z"}
	f.material["critic_closure"] = map[string]any{"reviewer": "Critic synthetic distinct", "signed_at": "2026-11-10T13:00:00Z"}
	receipts := []any{authorReceipt}
	for _, role := range []string{"factual", "quality"} {
		name := role + " synthetic distinct"
		body := f.putBytes(role+".body", []byte("synthetic "+role+" source body"))
		receipt := map[string]any{"url": "https://example.test/" + role, "capture_path": body["path"], "capture_sha256": body["sha256"], "bytes": body["bytes"], "fetched_by_role": role, "fetched_at": "2026-11-10T12:30:00Z"}
		receipts = append(receipts, receipt)
		raw := map[string]any{"schema": "quick-raw-review-v1", "role": role, "reviewer": name, "pending_sha256": sha, "rubric_sha256": sha, "items": []any{map[string]any{"id": id, "review_binding": "sha256:" + sha, "record_sha256": sha, "verdict": "accept", "rationale": role + " exact original rationale Case And Spaces", "sources": []any{receipt["url"]}, "child_safe": true}}}
		rawRef := f.put(role+".json", raw)
		choice := object(clone(receipt))
		choice["chosen_by"] = name
		f.material[role+"_envelope"] = map[string]any{"schema": "quick-review-envelope-v1", "role": role, "reviewer": name, "review_path": rawRef["path"], "review_sha256": rawRef["sha256"], "signed_at": "2026-11-10T13:00:00Z", "first_peer_read_at": nil, "child_safe_by_item": map[string]any{id: true}, "reviewer_chosen_sources": map[string]any{id: []any{choice}}}
	}
	f.material["review_evidence"] = map[string]any{"schema": "quick-review-evidence-v1", "pending_sha256": sha, "items": map[string]any{id: "source_backed"}, "receipts": receipts}
	artifacts := []any{}
	for n := 1; n <= 5; n++ {
		ref := f.putBytes(fmt.Sprintf("M%d.txt", n), []byte(fmt.Sprintf("synthetic public stage %d", n)))
		ref["stage"] = fmt.Sprintf("M%d", n)
		artifacts = append(artifacts, ref)
	}
	f.material["artifacts"] = map[string]any{"schema": "quick-review-artifacts-v1", "artifacts": artifacts}
	return f
}
func (f *bridgeFixture) changeRaw(role string, change func(map[string]any)) {
	f.t.Helper()
	env := f.material[role+"_envelope"]
	b, err := os.ReadFile(text(env["review_path"]))
	if err != nil {
		f.t.Fatal(err)
	}
	r, err := pendingDecode(b, MaxBytes)
	if err != nil {
		f.t.Fatal(err)
	}
	change(r)
	ref := f.put(role+".json", r)
	env["review_sha256"] = ref["sha256"]
}
func TestQuickBridgeRawPairPreservesOriginalJudgmentsAndCannotBecomeNativeReviews(t *testing.T) {
	f := newBridgeFixture(t)
	raw, names, err := bridgeReviews(f.pending, f.dossiers, f.material, f.files)
	if err != nil {
		t.Fatal(err)
	}
	if len(raw) != 2 || names["factual"] != "factual synthetic distinct" || object(rows(object(raw[0])["items"])[0])["rationale"] != "factual exact original rationale Case And Spaces" {
		t.Fatal("raw identity or rationale was translated", raw)
	}
	paths := []string{text(f.material["factual_envelope"]["review_path"]), text(f.material["quality_envelope"]["review_path"])}
	if _, err := readReviews(t.TempDir(), "quick", strings.Repeat("a", 64), map[string]any{"boards": []any{map[string]any{"id": "iq92_synthetic_only"}}}, paths); err == nil {
		t.Fatal("raw fragments bypassed full native candidate confirmation")
	}
}
func TestQuickBridgeRawPairFailsClosed(t *testing.T) {
	id := "iq92_synthetic_only"
	cases := map[string]func(*bridgeFixture){
		"same reviewer": func(f *bridgeFixture) {
			f.material["quality_envelope"]["reviewer"] = f.material["factual_envelope"]["reviewer"]
		},
		"author reviewer": func(f *bridgeFixture) { f.material["factual_envelope"]["reviewer"] = "Author synthetic distinct" },
		"critic reviewer": func(f *bridgeFixture) {
			f.material["critic_closure"]["reviewer"] = f.material["factual_envelope"]["reviewer"]
		},
		"wrong role":            func(f *bridgeFixture) { f.material["factual_envelope"]["role"] = "quality" },
		"peer before sign":      func(f *bridgeFixture) { f.material["factual_envelope"]["first_peer_read_at"] = "2026-11-10T13:00:00Z" },
		"release early":         func(f *bridgeFixture) { f.material["author_release"]["unsealed_at"] = "2026-11-10T12:59:00Z" },
		"missing safety":        func(f *bridgeFixture) { delete(object(f.material["factual_envelope"]["child_safe_by_item"]), id) },
		"false safety":          func(f *bridgeFixture) { object(f.material["factual_envelope"]["child_safe_by_item"])[id] = false },
		"missing source choice": func(f *bridgeFixture) { delete(object(f.material["factual_envelope"]["reviewer_chosen_sources"]), id) },
		"false provenance": func(f *bridgeFixture) {
			object(rows(object(f.material["factual_envelope"]["reviewer_chosen_sources"])[id])[0])["fetched_by_role"] = "critic"
		},
		"legacy receipt": func(f *bridgeFixture) {
			object(rows(f.material["review_evidence"]["receipts"])[1])["fetched_by_role"] = "legacy"
		},
		"unfetched locator": func(f *bridgeFixture) {
			f.changeRaw("factual", func(r map[string]any) {
				object(rows(r["items"])[0])["sources"] = []any{"https://example.test/unfetched"}
			})
		},
		"stale raw": func(f *bridgeFixture) {
			_ = os.WriteFile(text(f.material["factual_envelope"]["review_path"]), []byte("changed"), 0600)
		},
		"stale capture": func(f *bridgeFixture) {
			_ = os.WriteFile(text(object(rows(f.material["review_evidence"]["receipts"])[1])["capture_path"]), []byte("changed"), 0600)
		},
		"KG exception": func(f *bridgeFixture) { object(f.material["review_evidence"]["items"])[id] = "kg_only" },
		"artifact reused": func(f *bridgeFixture) {
			rows(f.material["artifacts"]["artifacts"])[1] = rows(f.material["artifacts"]["artifacts"])[0]
		},
		"unknown item": func(f *bridgeFixture) {
			f.changeRaw("factual", func(r map[string]any) { object(rows(r["items"])[0])["id"] = "iq92_unknown" })
		},
		"duplicate item": func(f *bridgeFixture) {
			f.changeRaw("factual", func(r map[string]any) { r["items"] = append(rows(r["items"]), rows(r["items"])[0]) })
		},
		"missing item": func(f *bridgeFixture) { f.changeRaw("factual", func(r map[string]any) { r["items"] = []any{} }) },
		"hold": func(f *bridgeFixture) {
			f.changeRaw("factual", func(r map[string]any) { object(rows(r["items"])[0])["verdict"] = "hold" })
		},
		"reject": func(f *bridgeFixture) {
			f.changeRaw("quality", func(r map[string]any) { object(rows(r["items"])[0])["verdict"] = "reject" })
		},
		"false raw safety": func(f *bridgeFixture) {
			f.changeRaw("quality", func(r map[string]any) { object(rows(r["items"])[0])["child_safe"] = false })
		},
		"missing raw safety": func(f *bridgeFixture) {
			f.changeRaw("quality", func(r map[string]any) { delete(object(rows(r["items"])[0]), "child_safe") })
		},
		"stale dossier": func(f *bridgeFixture) {
			f.changeRaw("factual", func(r map[string]any) {
				object(rows(r["items"])[0])["review_binding"] = "sha256:" + strings.Repeat("b", 64)
			})
		},
		"blank rationale": func(f *bridgeFixture) {
			f.changeRaw("factual", func(r map[string]any) { object(rows(r["items"])[0])["rationale"] = "  " })
		},
		"copied peer rationale": func(f *bridgeFixture) {
			f.changeRaw("quality", func(r map[string]any) {
				object(rows(r["items"])[0])["rationale"] = "factual exact original rationale Case And Spaces"
			})
		},
		"raw extra field": func(f *bridgeFixture) { f.changeRaw("quality", func(r map[string]any) { r["approval"] = true }) },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			f := newBridgeFixture(t)
			change(f)
			if _, _, err := bridgeReviews(f.pending, f.dossiers, f.material, f.files); err == nil {
				t.Fatal("unclosed raw evidence accepted")
			}
		})
	}
}
func TestQuickBridgeUnresolvedHistoryNeverPassesAnEmptyShape(t *testing.T) {
	base := map[string]any{"schema": "quick-pending-stock-screen-v1", "mechanical_pass": true, "complete": false, "unresolved_quick_history": []any{}}
	if err := bridgeStockClosure(base); err == nil {
		t.Fatal("false complete passed through empty list")
	}
	base["complete"] = true
	base["unresolved_quick_history"] = []any{"legacy research descriptor"}
	if err := bridgeStockClosure(base); err == nil {
		t.Fatal("unresolved descriptor passed")
	}
	base["unresolved_quick_history"] = []any{}
	if err := bridgeStockClosure(base); err != nil {
		t.Fatal(err)
	}
}
func TestQuickBridgePublicationRereadsRawEvidenceAndRollsBack(t *testing.T) {
	dir := t.TempDir()
	source, out := filepath.Join(dir, "raw.json"), filepath.Join(dir, "draft.json")
	if err := os.WriteFile(source, []byte("raw original"), 0600); err != nil {
		t.Fatal(err)
	}
	readset, err := contentops.CaptureRegularReadSet([]string{source})
	if err != nil {
		t.Fatal(err)
	}
	checks := 0
	verify := func() error {
		checks++
		if checks == 2 {
			return os.WriteFile(source, []byte("raw changed"), 0600)
		}
		return nil
	}
	if err := publishQuickPending(context.Background(), out, []byte("draft bytes"), readset, verify); err == nil {
		t.Fatal("changed raw report survived guarded publication")
	}
	if _, err := os.Lstat(out); !os.IsNotExist(err) {
		t.Fatal("failed publication left output", err)
	}
}

func TestQuickBridgeRationaleDuplicationThresholdsIncludeExactlyTwentyPercent(t *testing.T) {
	for _, cross := range []bool{false, true} {
		for _, duplicated := range []int{1, 2} {
			f := newBridgeFixture(t)
			originalID := "iq92_synthetic_only"
			oldDossier := f.dossiers[originalID]
			f.dossiers = map[string]map[string]any{}
			boards := []any{}
			modes := map[string]any{}
			for n := 0; n < 5; n++ {
				id := fmt.Sprintf("iq92_synthetic_%d", n)
				d := object(clone(oldDossier))
				d["id"] = id
				f.dossiers[id] = d
				boards = append(boards, map[string]any{"id": id})
				modes[id] = "source_backed"
			}
			f.pending["boards"] = boards
			f.material["review_evidence"]["items"] = modes
			for _, role := range []string{"factual", "quality"} {
				env := f.material[role+"_envelope"]
				b, _ := os.ReadFile(text(env["review_path"]))
				raw, err := pendingDecode(b, MaxBytes)
				if err != nil {
					t.Fatal(err)
				}
				prototype := object(rows(raw["items"])[0])
				oldChoice := object(clone(object(rows(object(env["reviewer_chosen_sources"])[originalID])[0])))
				items, safety, choices := []any{}, map[string]any{}, map[string]any{}
				for n := 0; n < 5; n++ {
					id := fmt.Sprintf("iq92_synthetic_%d", n)
					r := object(clone(prototype))
					r["id"] = id
					r["rationale"] = fmt.Sprintf("%s unique rationale %d", role, n)
					if !cross && role == "factual" && n <= duplicated {
						r["rationale"] = "factual unique rationale 0"
					}
					if cross && role == "quality" && n < duplicated {
						r["rationale"] = fmt.Sprintf("factual unique rationale %d", n)
					}
					items = append(items, r)
					safety[id] = true
					choices[id] = []any{clone(oldChoice)}
				}
				raw["items"] = items
				ref := f.put(role+".json", raw)
				env["review_sha256"] = ref["sha256"]
				env["child_safe_by_item"], env["reviewer_chosen_sources"] = safety, choices
			}
			_, _, err := bridgeReviews(f.pending, f.dossiers, f.material, f.files)
			if duplicated == 1 && err != nil {
				t.Fatal("exact 20 percent should pass", cross, err)
			}
			if duplicated == 2 && err == nil {
				t.Fatal("over 20 percent should fail", cross)
			}
		}
	}
}

func TestQuickBridgeDraftRefusesUnpinnedMalformedFramesBeforeSourceOrOutput(t *testing.T) {
	root, scratch := t.TempDir(), t.TempDir()
	frame, output := filepath.Join(scratch, "frame.json"), filepath.Join(scratch, "draft.json")
	for _, body := range []string{`{"schema":"wrong"}`, `{"schema":"quick-bridge-frame-v1","schema":"quick-bridge-frame-v1"}`} {
		if err := os.WriteFile(frame, []byte(body), 0600); err != nil {
			t.Fatal(err)
		}
		for _, pin := range []string{strings.Repeat("b", 64), digestBytes([]byte(body))} {
			if _, err := DraftQuickBridge(context.Background(), root, QuickBridgeDraftOptions{Frame: frame, FrameSHA256: pin, Output: output}); err == nil {
				t.Fatal("unpinned/malformed frame accepted")
			}
			if _, err := os.Lstat(output); !os.IsNotExist(err) {
				t.Fatal("refused frame created output", err)
			}
			entries, err := os.ReadDir(root)
			if err != nil || len(entries) != 0 {
				t.Fatal("refused frame changed source root", err)
			}
		}
	}
}
