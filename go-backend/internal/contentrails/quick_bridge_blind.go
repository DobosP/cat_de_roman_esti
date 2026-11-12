package contentrails

import (
	"fmt"
	"sort"
	"strings"
)

func bridgeCritic(root string, frame, pending map[string]any, dossiers, public, private map[string]map[string]any, material map[string]map[string]any, consumer []any, identities map[string]string, files *quickBridgeFiles) error {
	closure, receipt := material["critic_closure"], material["operator_replay"]
	pendingSHA := object(pending["_bridge"])["pending_sha256"]
	if !pendingExact(closure, "schema", "role", "reviewer", "signed_at", "pending_sha256", "items") || closure["schema"] != "quick-critic-semantic-closure-v1" || closure["role"] != "critic" || closure["reviewer"] != identities["critic"] || closure["pending_sha256"] != pendingSHA || !arrayShape(closure["items"], len(dossiers), len(dossiers)) {
		return fmt.Errorf("quick bridge independent critic semantic closure exact coverage required")
	}
	if !pendingExact(receipt, "schema", "root", "created_at", "bundle_sha256", "native_build_proof_sha256", "consumer_tools", "checks", "replays") || receipt["schema"] != "quick-bridge-operator-replay-v1" || receipt["root"] != root || receipt["bundle_sha256"] != object(frame["bundle"])["sha256"] || receipt["native_build_proof_sha256"] != object(frame["native_build_proof"])["sha256"] || !same(receipt["consumer_tools"], consumer) || !same(receipt["checks"], map[string]any{"fresh_compare_quick": true, "review_isolation": true, "source_first_fetch_provenance": true}) || !arrayShape(receipt["replays"], len(dossiers), len(dossiers)) {
		return fmt.Errorf("quick bridge Root-pinned replay/isolation/source-provenance receipt required")
	}
	created, err := bridgeTime(receipt["created_at"])
	if err != nil {
		return err
	}
	latest, err := bridgeTime(closure["signed_at"])
	if err != nil {
		return err
	}
	for _, role := range []string{"critic", "factual", "quality"} {
		r := material[role+"_envelope"]
		if role == "critic" {
			r = closure
		}
		signed, err := bridgeTime(r["signed_at"])
		if err != nil || created.Before(signed) {
			return fmt.Errorf("quick bridge Root receipt predates signed evidence")
		}
		if signed.After(latest) {
			latest = signed
		}
	}
	replays := map[string]map[string]any{}
	for _, v := range rows(receipt["replays"]) {
		r := object(v)
		id := text(r["id"])
		when, err := bridgeTime(r["replayed_at"])
		if !pendingExact(r, "id", "comparison_sha256", "executed_source_sha256", "exit_code", "replayed_at") || dossiers[id] == nil || replays[id] != nil || integer(r["exit_code"]) != 0 || r["executed_source_sha256"] != object(consumer[1])["sha256"] || !authorityDigest(r["comparison_sha256"]) || err != nil || when.After(created) || !when.After(latest) {
			return fmt.Errorf("quick bridge compare-quick replay identity/current consumer/result")
		}
		replays[id] = r
	}
	seen := map[string]bool{}
	for _, v := range rows(closure["items"]) {
		r := object(v)
		id := text(r["id"])
		dossier := dossiers[id]
		if !pendingExact(r, "id", "review_binding", "record_sha256", "comparison_path", "comparison_sha256", "verdict", "rationale", "truthful_predicates", "no_equally_valid_alternative", "child_safe") || dossier == nil || seen[id] || r["review_binding"] != dossier["review_binding"] || r["record_sha256"] != dossier["record_sha256"] || r["verdict"] != "accept" || bridgeNorm(text(r["rationale"])) == "" || r["truthful_predicates"] != true || r["no_equally_valid_alternative"] != true || r["child_safe"] != true || replays[id]["comparison_sha256"] != r["comparison_sha256"] {
			return fmt.Errorf("quick bridge critic hold/reject/unsafe/unclosed/duplicate/stale item")
		}
		b, err := files.two(map[string]any{"path": r["comparison_path"], "sha256": r["comparison_sha256"]})
		if err != nil {
			return err
		}
		comp, err := pendingDecode(b, quickPendingMaxBytes)
		if err != nil {
			return err
		}
		if err = bridgeComparison(root, frame, pending, dossier, public[id], private[id], comp, consumer, files); err != nil {
			return err
		}
		seen[id] = true
	}
	return nil
}

func bridgeComparison(root string, frame, pending, dossier, public, private, comp map[string]any, consumer []any, files *quickBridgeFiles) error {
	if !pendingExact(comp, "schema", "challenge_id", "game", "mode", "public_binding", "native_binding", "key_binding", "response_binding", "mechanical_match", "details", "issues", "status", "approval", "human_checks_required", "limitation") || comp["schema"] != "cat-quick-blind-comparison-1" || comp["challenge_id"] != public["challenge_id"] || comp["game"] != public["game"] || comp["mode"] != "regular_category" || comp["mode"] != public["mode"] || comp["mechanical_match"] != true || !arrayShape(comp["issues"], 0, 0) || comp["status"] != "needs_human_semantic_checks" || comp["approval"] != nil || !same(comp["human_checks_required"], []string{"Truthful natural exact-sense predicates", "No equally valid semantic alternate", "Recognition and source-backed A/I/J review", "Independent critic and factual/quality roles", "Unresolved history relevance closure remains mandatory"}) || comp["limitation"] != "Operator-pinned tool/build receipt plus fresh native replay bind bytes only; no semantic, source-policy, independence, installation or serving approval." {
		return fmt.Errorf("quick bridge exact Stage3 comparison/mechanical-only schema required")
	}
	binding := map[string]any{"stock_screen": pending["screen"], "consumer_tools": consumer, "root": root, "baseline_source_sha256": pending["baseline_source_sha256"], "baseline_source_version": pending["baseline_source_version"], "bundle": map[string]any{"path": object(frame["bundle"])["path"], "sha256": object(frame["bundle"])["sha256"]}, "native_tool": pending["tool"], "native_build_proof": map[string]any{"path": object(frame["native_build_proof"])["path"], "sha256": object(frame["native_build_proof"])["sha256"]}, "pending_sha256": object(pending["_bridge"])["pending_sha256"], "record_sha256": dossier["record_sha256"], "review_binding": dossier["review_binding"], "bindings": pending["bindings"], "inventory_sha256": object(pending["bindings"])["inventory_sha256"], "game": public["game"], "mode": public["mode"]}
	if !same(binding, comp["native_binding"]) {
		return fmt.Errorf("quick bridge comparison current native/proof/inventory/consumer/dossier binding differs")
	}
	pub, err := files.two(object(comp["public_binding"]))
	if err != nil {
		return err
	}
	if digestBytes(pub) != dossier["public_projection_sha256"] {
		return fmt.Errorf("quick bridge blind public bytes changed")
	}
	pubObject, err := pendingDecode(pub, quickPendingMaxBytes)
	if err != nil || !same(public, pubObject) {
		return fmt.Errorf("quick bridge blind public context changed")
	}
	keyBytes, err := files.two(object(comp["key_binding"]))
	if err != nil {
		return err
	}
	key, err := pendingDecode(keyBytes, quickPendingMaxBytes)
	if err != nil || !pendingExact(key, "schema", "challenge_id", "game", "mode", "item_id", "native_binding", "public_binding", "private_projection", "approval") || key["schema"] != "cat-quick-blind-key-1" || key["challenge_id"] != comp["challenge_id"] || key["game"] != comp["game"] || key["mode"] != comp["mode"] || key["item_id"] != dossier["id"] || !same(key["native_binding"], binding) || !same(key["public_binding"], comp["public_binding"]) || !same(key["private_projection"], private) || key["approval"] != nil {
		return fmt.Errorf("quick bridge private key/native task binding differs")
	}
	responseBytes, err := files.two(object(comp["response_binding"]))
	if err != nil {
		return err
	}
	response, err := pendingDecode(responseBytes, quickPendingMaxBytes)
	if err != nil {
		return err
	}
	if response["challenge_id"] != public["challenge_id"] || response["public_sha256"] != dossier["public_projection_sha256"] || response["game"] != public["game"] || response["mode"] != public["mode"] || response["ambiguous"] != false {
		return fmt.Errorf("quick bridge critic response challenge/public/mode/ambiguity")
	}
	tokens := map[string]bool{}
	for _, v := range rows(public["tiles"]) {
		token := text(object(v)["tile"])
		if token == "" || tokens[token] {
			return fmt.Errorf("quick bridge public token coverage")
		}
		tokens[token] = true
	}
	expected := object(private["expected_answer"])
	if public["game"] == "intrusul" {
		if !pendingExact(response, "challenge_id", "public_sha256", "game", "mode", "ambiguous", "odd", "predicate", "tile_explanations", "alternate_predicates") || len(tokens) != 4 || !tokens[text(response["odd"])] || response["odd"] != expected["odd"] || strings.TrimSpace(text(response["predicate"])) == "" || !arrayShape(response["alternate_predicates"], 0, 0) || !same(comp["details"], map[string]any{"odd_exact_match": true, "semantic_predicate_truth_verified": false}) {
			return fmt.Errorf("quick bridge malformed/wrong/alternate Intrusul response")
		}
		explanations := object(response["tile_explanations"])
		if len(explanations) != len(tokens) {
			return fmt.Errorf("quick bridge per-tile reasoning missing")
		}
		for token := range tokens {
			if strings.TrimSpace(text(explanations[token])) == "" {
				return fmt.Errorf("quick bridge blank per-tile reasoning")
			}
		}
	} else if public["game"] == "perechi" {
		if !pendingExact(response, "challenge_id", "public_sha256", "game", "mode", "ambiguous", "pairs", "explanations", "alternate_matching") || len(tokens) != 8 || !arrayShape(response["pairs"], 4, 4) || !arrayShape(response["explanations"], 4, 4) || response["alternate_matching"] != nil || !same(comp["details"], map[string]any{"matching_exact_match": true, "semantic_pair_truth_verified": false}) {
			return fmt.Errorf("quick bridge malformed/alternate Perechi response")
		}
		seen, actual, want := map[string]bool{}, []string{}, []string{}
		for _, v := range rows(response["pairs"]) {
			if !stringArray(v, 2, 2) {
				return fmt.Errorf("quick bridge malformed pair tokens")
			}
			pair := ids(v)
			for _, token := range pair {
				if !tokens[token] || seen[token] {
					return fmt.Errorf("quick bridge unknown/duplicated pair token")
				}
				seen[token] = true
			}
			sort.Strings(pair)
			actual = append(actual, strings.Join(pair, "|"))
		}
		for _, v := range rows(expected["pairs"]) {
			pair := ids(object(v)["members"])
			sort.Strings(pair)
			want = append(want, strings.Join(pair, "|"))
		}
		sort.Strings(actual)
		sort.Strings(want)
		if !same(actual, want) {
			return fmt.Errorf("quick bridge wrong matching")
		}
		for _, v := range rows(response["explanations"]) {
			if strings.TrimSpace(text(v)) == "" {
				return fmt.Errorf("quick bridge blank pair reasoning")
			}
		}
	} else {
		return fmt.Errorf("quick bridge unsupported blind game")
	}
	return nil
}
