//go:build linux

package contentrails

import (
	"fmt"
	"os"
	"strings"
	"testing"
)

type bridgeBlindFixture struct {
	*bridgeFixture
	root            string
	frame           map[string]any
	public, private map[string]map[string]any
	consumer        []any
	comparison      map[string]any
}

func newBridgeBlindFixture(t *testing.T) *bridgeBlindFixture {
	t.Helper()
	f := newBridgeFixture(t)
	sha := strings.Repeat("a", 64)
	id := "iq92_synthetic_only"
	f.pending["baseline_source_sha256"], f.pending["baseline_source_version"] = sha, 25
	f.pending["screen"] = map[string]any{"schema": "synthetic-test-screen"}
	f.pending["tool"] = map[string]any{"path": "/synthetic-test-tool", "sha256": sha, "bytes": 1, "go_version": "go1.27.3"}
	object(f.pending["bindings"])["inventory_sha256"] = sha
	frame := map[string]any{"bundle": map[string]any{"path": "/synthetic-test-bundle", "sha256": sha}, "native_build_proof": map[string]any{"path": "/synthetic-test-proof", "sha256": sha}}
	consumer := []any{map[string]any{"path": "scripts/miner/common.py", "sha256": sha, "bytes": 1}, map[string]any{"path": "scripts/miner/critic_blind.py", "sha256": sha, "bytes": 1}}
	public := map[string]any{"schema": "quick-pending-public-v1", "challenge_id": "synthetic-only", "game": "intrusul", "mode": "regular_category", "context": map[string]any{}, "tiles": []any{map[string]any{"tile": "t0001", "text": "A"}, map[string]any{"tile": "t0002", "text": "B"}, map[string]any{"tile": "t0003", "text": "C"}, map[string]any{"tile": "t0004", "text": "D"}}, "task": "Synthetic public prompt", "response_schema": map[string]any{}}
	pubRef := f.put("public.json", public)
	pubBinding := map[string]any{"path": pubRef["path"], "sha256": pubRef["sha256"]}
	f.dossiers[id]["public_projection_sha256"] = pubRef["sha256"]
	private := map[string]any{"expected_answer": map[string]any{"odd": "t0004", "predicate": "synthetic hidden predicate"}}
	binding := map[string]any{"stock_screen": f.pending["screen"], "consumer_tools": consumer, "root": f.dir, "baseline_source_sha256": sha, "baseline_source_version": 25, "bundle": frame["bundle"], "native_tool": f.pending["tool"], "native_build_proof": frame["native_build_proof"], "pending_sha256": sha, "record_sha256": sha, "review_binding": "sha256:" + sha, "bindings": f.pending["bindings"], "inventory_sha256": sha, "game": "intrusul", "mode": "regular_category"}
	key := map[string]any{"schema": "cat-quick-blind-key-1", "challenge_id": "synthetic-only", "game": "intrusul", "mode": "regular_category", "item_id": id, "native_binding": binding, "public_binding": pubBinding, "private_projection": private, "approval": nil}
	keyRef := f.put("key.json", key)
	response := map[string]any{"challenge_id": "synthetic-only", "public_sha256": pubRef["sha256"], "game": "intrusul", "mode": "regular_category", "ambiguous": false, "odd": "t0004", "predicate": "synthetic nonblank explanation", "tile_explanations": map[string]any{"t0001": "a reason", "t0002": "b reason", "t0003": "c reason", "t0004": "d reason"}, "alternate_predicates": []any{}}
	responseRef := f.put("response.json", response)
	comparison := map[string]any{"schema": "cat-quick-blind-comparison-1", "challenge_id": "synthetic-only", "game": "intrusul", "mode": "regular_category", "public_binding": pubBinding, "native_binding": binding, "key_binding": map[string]any{"path": keyRef["path"], "sha256": keyRef["sha256"]}, "response_binding": map[string]any{"path": responseRef["path"], "sha256": responseRef["sha256"]}, "mechanical_match": true, "details": map[string]any{"odd_exact_match": true, "semantic_predicate_truth_verified": false}, "issues": []any{}, "status": "needs_human_semantic_checks", "approval": nil, "human_checks_required": []any{"Truthful natural exact-sense predicates", "No equally valid semantic alternate", "Recognition and source-backed A/I/J review", "Independent critic and factual/quality roles", "Unresolved history relevance closure remains mandatory"}, "limitation": "Operator-pinned tool/build receipt plus fresh native replay bind bytes only; no semantic, source-policy, independence, installation or serving approval."}
	compRef := f.put("comparison.json", comparison)
	f.material["critic_closure"] = map[string]any{"schema": "quick-critic-semantic-closure-v1", "role": "critic", "reviewer": "Critic synthetic distinct", "signed_at": "2026-11-10T13:00:00Z", "pending_sha256": sha, "items": []any{map[string]any{"id": id, "review_binding": "sha256:" + sha, "record_sha256": sha, "comparison_path": compRef["path"], "comparison_sha256": compRef["sha256"], "verdict": "accept", "rationale": "Synthetic critic semantic judgment", "truthful_predicates": true, "no_equally_valid_alternative": true, "child_safe": true}}}
	f.material["operator_replay"] = map[string]any{"schema": "quick-bridge-operator-replay-v1", "root": f.dir, "created_at": "2026-11-10T15:00:00Z", "bundle_sha256": sha, "native_build_proof_sha256": sha, "consumer_tools": consumer, "checks": map[string]any{"fresh_compare_quick": true, "review_isolation": true, "source_first_fetch_provenance": true}, "replays": []any{map[string]any{"id": id, "comparison_sha256": compRef["sha256"], "executed_source_sha256": sha, "exit_code": 0, "replayed_at": "2026-11-10T14:30:00Z"}}}
	return &bridgeBlindFixture{f, f.dir, frame, map[string]map[string]any{id: public}, map[string]map[string]any{id: private}, consumer, comparison}
}
func TestQuickBridgeRequiresSeparateSemanticClosureAndPinnedReplayClaims(t *testing.T) {
	f := newBridgeBlindFixture(t)
	_, identities, err := bridgeReviews(f.pending, f.dossiers, f.material, f.files)
	if err != nil {
		t.Fatal(err)
	}
	if err = bridgeCritic(f.root, f.frame, f.pending, f.dossiers, f.public, f.private, f.material, f.consumer, identities, f.files); err != nil {
		t.Fatal(err)
	}
	for _, change := range []func(){
		func() { f.material["critic_closure"]["items"] = []any{} },
		func() { f.material["operator_replay"]["checks"] = map[string]any{} },
	} {
		beforeClosure, beforeReceipt := object(clone(f.material["critic_closure"])), object(clone(f.material["operator_replay"]))
		change()
		if err = bridgeCritic(f.root, f.frame, f.pending, f.dossiers, f.public, f.private, f.material, f.consumer, identities, f.files); err == nil {
			t.Fatal("mechanical comparison replaced critic/provenance closure")
		}
		f.material["critic_closure"], f.material["operator_replay"] = beforeClosure, beforeReceipt
	}
}
func TestQuickBridgeComparisonRejectsLegacyStaleAndMechanicalOnlyMutations(t *testing.T) {
	id := "iq92_synthetic_only"
	for name, change := range map[string]func(map[string]any){
		"legacy schema":  func(c map[string]any) { c["schema"] = "cat-v2-blind-comparison-1" },
		"approval":       func(c map[string]any) { c["approval"] = true },
		"semantic claim": func(c map[string]any) { object(c["details"])["semantic_predicate_truth_verified"] = true },
		"fail":           func(c map[string]any) { c["mechanical_match"] = false },
		"issue":          func(c map[string]any) { c["issues"] = []any{"alternate"} },
		"mode":           func(c map[string]any) { c["mode"] = "daily" },
		"consumer": func(c map[string]any) {
			object(rows(object(c["native_binding"])["consumer_tools"])[1])["sha256"] = strings.Repeat("b", 64)
		},
		"proof": func(c map[string]any) {
			object(object(c["native_binding"])["native_build_proof"])["sha256"] = strings.Repeat("b", 64)
		},
		"record": func(c map[string]any) { object(c["native_binding"])["record_sha256"] = strings.Repeat("b", 64) },
		"root":   func(c map[string]any) { object(c["native_binding"])["root"] = "/other" },
		"review": func(c map[string]any) {
			object(c["native_binding"])["review_binding"] = "sha256:" + strings.Repeat("b", 64)
		},
	} {
		t.Run(name, func(t *testing.T) {
			f := newBridgeBlindFixture(t)
			c := object(clone(f.comparison))
			change(c)
			if err := bridgeComparison(f.root, f.frame, f.pending, f.dossiers[id], f.public[id], f.private[id], c, f.consumer, f.files); err == nil {
				t.Fatal("stale/misleading comparison accepted")
			}
		})
	}
}
func TestQuickBridgeResponseAndKeyBytesMustStayExact(t *testing.T) {
	id := "iq92_synthetic_only"
	for _, key := range []string{"public_binding", "key_binding", "response_binding"} {
		t.Run(key, func(t *testing.T) {
			f := newBridgeBlindFixture(t)
			path := text(object(f.comparison[key])["path"])
			if err := os.WriteFile(path, []byte("changed bytes"), 0600); err != nil {
				t.Fatal(err)
			}
			if err := bridgeComparison(f.root, f.frame, f.pending, f.dossiers[id], f.public[id], f.private[id], f.comparison, f.consumer, f.files); err == nil {
				t.Fatal("changed blind input accepted")
			}
		})
	}
	for name, change := range map[string]func(map[string]any){
		"blank reasoning": func(r map[string]any) { object(r["tile_explanations"])["t0001"] = " " },
		"missing token":   func(r map[string]any) { delete(object(r["tile_explanations"]), "t0001") },
		"alternate":       func(r map[string]any) { r["alternate_predicates"] = []any{"plausible other predicate"} },
		"wrong token":     func(r map[string]any) { r["odd"] = "t0001" },
		"unknown token":   func(r map[string]any) { r["odd"] = "t9999" },
		"ambiguous":       func(r map[string]any) { r["ambiguous"] = true },
	} {
		t.Run(name, func(t *testing.T) {
			f := newBridgeBlindFixture(t)
			ref := object(f.comparison["response_binding"])
			b, _ := os.ReadFile(text(ref["path"]))
			r, err := pendingDecode(b, MaxBytes)
			if err != nil {
				t.Fatal(err)
			}
			change(r)
			newRef := f.put("response.json", r)
			ref["sha256"] = newRef["sha256"]
			if err := bridgeComparison(f.root, f.frame, f.pending, f.dossiers[id], f.public[id], f.private[id], f.comparison, f.consumer, f.files); err == nil {
				t.Fatal("rebound malformed response accepted")
			}
		})
	}
}

func TestQuickBridgePerechiRequiresFourExactPairsAndNonblankAlignedReasoning(t *testing.T) {
	id := "iq92_synthetic_only" // pure response validator fixture, not a pending author ID
	for _, mutation := range []string{"none", "duplicate token", "wrong matching", "blank reason", "alternate"} {
		t.Run(mutation, func(t *testing.T) {
			f := newBridgeBlindFixture(t)
			public := f.public[id]
			public["game"] = "perechi"
			tiles, pairs, expected := []any{}, []any{}, []any{}
			for n := 1; n <= 8; n++ {
				tiles = append(tiles, map[string]any{"tile": fmt.Sprintf("t%04d", n), "text": fmt.Sprintf("Tile %d", n)})
			}
			for n := 1; n <= 8; n += 2 {
				pair := []any{fmt.Sprintf("t%04d", n), fmt.Sprintf("t%04d", n+1)}
				pairs = append(pairs, pair)
				expected = append(expected, map[string]any{"members": pair, "predicate": fmt.Sprintf("Pair %d", n)})
			}
			public["tiles"] = tiles
			pubRef := f.put("public.json", public)
			pb := map[string]any{"path": pubRef["path"], "sha256": pubRef["sha256"]}
			f.dossiers[id]["public_projection_sha256"] = pubRef["sha256"]
			f.private[id]["expected_answer"] = map[string]any{"pairs": expected}
			f.comparison["game"], f.comparison["public_binding"] = "perechi", pb
			object(f.comparison["native_binding"])["game"] = "perechi"
			f.comparison["details"] = map[string]any{"matching_exact_match": true, "semantic_pair_truth_verified": false}
			keyRef := object(f.comparison["key_binding"])
			keyBytes, _ := os.ReadFile(text(keyRef["path"]))
			key, err := pendingDecode(keyBytes, MaxBytes)
			if err != nil {
				t.Fatal(err)
			}
			key["game"], key["native_binding"], key["public_binding"], key["private_projection"] = "perechi", f.comparison["native_binding"], pb, f.private[id]
			ref := f.put("key.json", key)
			keyRef["sha256"] = ref["sha256"]
			response := map[string]any{"challenge_id": public["challenge_id"], "public_sha256": pubRef["sha256"], "game": "perechi", "mode": "regular_category", "ambiguous": false, "pairs": clone(pairs), "explanations": []any{"pair one", "pair two", "pair three", "pair four"}, "alternate_matching": nil}
			switch mutation {
			case "duplicate token":
				rows(rows(response["pairs"])[0])[0] = "t0002"
			case "wrong matching":
				rows(rows(response["pairs"])[0])[1], rows(rows(response["pairs"])[1])[0] = "t0003", "t0002"
			case "blank reason":
				rows(response["explanations"])[2] = " "
			case "alternate":
				response["alternate_matching"] = []any{}
			}
			ref = f.put("response.json", response)
			f.comparison["response_binding"] = map[string]any{"path": ref["path"], "sha256": ref["sha256"]}
			err = bridgeComparison(f.root, f.frame, f.pending, f.dossiers[id], f.public[id], f.private[id], f.comparison, f.consumer, f.files)
			if mutation == "none" && err != nil {
				t.Fatal(err)
			}
			if mutation != "none" && err == nil {
				t.Fatal("malformed pair response accepted", mutation)
			}
		})
	}
}
