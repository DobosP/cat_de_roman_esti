package contentrails

import (
	"context"
	"fmt"
	"math/big"
	"regexp"
	"sort"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpgolden"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
)

var pendingRuntimeID = regexp.MustCompile(`^(vi_|vp_)[0-9a-f]{20}$`)

func pendingProjection(ctx context.Context, data *content.Content, row, rating map[string]any, challenge string) (map[string]any, map[string]any, error) {
	game, runtimeID, category := text(row["game"]), text(rating["id"]), text(row["category"])
	seed := -1
	for n := 0; n < 5000; n++ {
		if err := ctx.Err(); err != nil {
			return nil, nil, err
		}
		picked := catalog.New(data).PickSeeded(game, pyrandom.New(big.NewInt(int64(n))), catalog.PickOptions{Category: category})
		if picked != nil && picked.CatalogID == runtimeID {
			seed = n
			break
		}
	}
	if seed < 0 {
		return nil, nil, fmt.Errorf("pending board not selectable in isolated overlay within 5000 seeds")
	}
	client, err := httpgolden.NewClient(httpgolden.Local(httpapi.New(data)), 4)
	if err != nil {
		return nil, nil, err
	}
	defer client.Close()
	base := "/api/wordgames/" + game + "/games"
	res, err := client.Do(ctx, httpgolden.JSONRequest("POST", fmt.Sprintf("%s?seed=%d&category=%s", base, seed, category), nil))
	if err != nil || res.Status != 200 {
		return nil, nil, fmt.Errorf("pending native create failed")
	}
	state, err := res.Object()
	if err != nil {
		return nil, nil, err
	}
	if state["solution"] != nil || state["score"] != nil || containsString(state, runtimeID) || containsString(state, text(row["source_id"])) || containsString(state, text(row["id"])) {
		return nil, nil, fmt.Errorf("pending initial state leaked private answers or identity")
	}
	p := object(row["payload"])
	if game == "intrusul" {
		if containsString(state, text(p["group_label"])) {
			return nil, nil, fmt.Errorf("pending initial predicate leaked")
		}
	} else {
		for _, pair := range rows(p["pairs"]) {
			if containsString(state, text(object(pair)["group_label"])) {
				return nil, nil, fmt.Errorf("pending initial pair predicate leaked")
			}
		}
	}
	get, err := client.Do(ctx, httpgolden.JSONRequest("GET", base+"/"+text(state["game_id"]), nil))
	if err != nil || get.Status != 200 {
		return nil, nil, fmt.Errorf("pending initial GET failed")
	}
	resumed, err := get.Object()
	if err != nil || !same(state, resumed) {
		return nil, nil, fmt.Errorf("pending initial GET drift")
	}
	// Session IDs are ephemeral and not part of reproducible public context.
	delete(state, "game_id")
	tokens, tiles := map[string]string{}, []any{}
	for i, v := range rows(state["tiles"]) {
		tile := object(v)
		id, label := text(tile["id"]), text(tile["label"])
		if id == "" || label == "" || tokens[id] != "" {
			return nil, nil, fmt.Errorf("pending native tile identity")
		}
		token := fmt.Sprintf("t%04d", i+1)
		tokens[id] = token
		tiles = append(tiles, map[string]any{"tile": token, "text": label})
	}
	if len(tokens) != len(pendingVisible(row)) {
		return nil, nil, fmt.Errorf("pending native tile coverage")
	}
	for _, id := range pendingVisible(row) {
		if tokens[id] == "" {
			return nil, nil, fmt.Errorf("pending native tile mismatch")
		}
	}
	context := map[string]any{}
	for _, key := range []string{"difficulty", "board_category", "category_label"} {
		if value, ok := state[key]; ok {
			context[key] = value
		}
	}
	public := map[string]any{"schema": "quick-pending-public-v1", "challenge_id": challenge, "game": game, "mode": "regular_category", "context": context, "tiles": tiles}
	answer := map[string]any{}
	if game == "intrusul" {
		answer["odd"], answer["predicate"] = tokens[text(p["intruder"])], p["group_label"]
		public["task"] = "Pick the single odd tile and explain the natural predicate shared by the other three; report any alternate odd tile or predicate."
		public["response_schema"] = map[string]any{"odd": "tile", "predicate": "nonblank text", "tile_explanations": "one per tile", "alternate_predicates": []any{}, "ambiguous": false}
	} else {
		pairs := []any{}
		for _, v := range rows(p["pairs"]) {
			r := object(v)
			members := ids(r["members"])
			pair := []string{tokens[members[0]], tokens[members[1]]}
			sort.Strings(pair)
			pairs = append(pairs, map[string]any{"members": pair, "predicate": r["group_label"]})
		}
		answer["pairs"] = pairs
		public["task"] = "Match all eight tiles into four natural pairs; explain each pair and report any competing matching or ambiguous tile."
		public["response_schema"] = map[string]any{"pairs": "four disjoint tile pairs", "explanations": "four nonblank texts", "alternate_matching": nil, "ambiguous": false}
	}
	private := map[string]any{"schema": "quick-pending-private-v1", "challenge_id": challenge, "id": row["id"], "runtime_id": runtimeID, "game": game, "mode": "regular_category", "seed": seed, "token_map": tokens, "expected_answer": answer, "native_initial_state": state, "initial_get_equal": true, "isolated_overlay_only": true, "approval": nil}
	return public, private, nil
}

func pendingBundle(ctx context.Context, snap *quickPendingSnapshot, boards, ratings []any, nodes map[string]any, data *content.Content, inputs map[string][]byte, opt QuickPendingOptions, screen, tool map[string]any) (map[string]any, error) {
	old := []any{}
	for _, v := range rows(object(snap.source.Raw["quick"])["boards"]) {
		r := object(v)
		old = append(old, map[string]any{"id": r["id"], "record_sha256": digest(r)})
	}
	binding := map[string]any{
		"kg_sha256":        contentbuild.TextSHA256(snap.files["cat_de_roman_esti/fixtures/kg_sample.json"]),
		"rubric_sha256":    contentbuild.TextSHA256(snap.files["docs/CRITIQUE_RUBRIC.md"]),
		"inventory_sha256": digest(snap.manifest), "stock_sha256": screen["stock_sha256"], "holds_sha256": screen["exclusions_sha256"],
		"registry_sha256": screen["registry_sha256"], "author_packet_sha256": digestBytes(inputs[opt.Packet]),
		"author_seal_sha256": digestBytes(inputs[opt.AuthorSeal]), "author_evidence_sha256": digestBytes(inputs[opt.ReceiptManifest]),
		"tool_sha256": tool["sha256"],
	}
	if opt.CacheBinding != "" {
		binding["author_cache_binding_sha256"] = opt.CacheBindingSHA256
	}
	pending := map[string]any{"schema": "quick-pending-v1", "status": "pending", "provenance_mode": "source_backed", "qualified": false, "approval": nil, "qualification": quickPendingQualification, "baseline_source_sha256": snap.source.SHA256, "baseline_source_version": snap.source.Version, "bindings": binding, "inventory": snap.manifest, "tool": tool, "input_bindings": pendingInputBindings(inputs), "boards": boards, "rated": ratings, "screen": screen, "preserved_old_rows": old}
	pendingBytes, err := Render(pending)
	if err != nil {
		return nil, err
	}
	pendingSHA := digestBytes(pendingBytes)
	members, descriptors := []any{}, []any{}
	add := func(path string, b []byte) {
		members = append(members, map[string]any{"path": path, "bytes": len(b), "sha256": digestBytes(b), "data": string(b)})
	}
	add("pending.json", pendingBytes)
	for i, v := range boards {
		r, rating := object(v), object(ratings[i])
		challenge := digest([]any{pendingSHA, r["id"], "quick-pending-regular-category-v1"})[:24]
		public, private, err := pendingProjection(ctx, data, r, rating, challenge)
		if err != nil {
			return nil, err
		}
		publicBytes, err := Render(public)
		if err != nil {
			return nil, err
		}
		privateBytes, err := Render(private)
		if err != nil {
			return nil, err
		}
		publicPath, privatePath := "public/"+challenge+".json", "private/"+challenge+".json"
		add(publicPath, publicBytes)
		add(privatePath, privateBytes)
		subset := map[string]any{}
		for _, id := range pendingVisible(r) {
			subset[id] = nodes[id]
		}
		dossier := map[string]any{"schema": "quick-pending-dossier-v1", "id": r["id"], "game": r["game"], "status": "pending", "provenance_mode": "source_backed", "source_id": r["source_id"], "runtime_id": rating["id"], "record_sha256": digest(r), "kg_sha256": binding["kg_sha256"], "rubric_sha256": binding["rubric_sha256"], "pending_sha256": pendingSHA, "baseline_source_sha256": snap.source.SHA256, "bindings": binding, "semantic_payload": r["payload"], "nodes": subset, "category": r["category"], "difficulty": r["difficulty"], "public_projection_sha256": digestBytes(publicBytes), "private_projection_sha256": digestBytes(privateBytes), "screen": screen, "approval": nil, "qualified": false, "qualification": quickPendingQualification}
		bound := object(clone(dossier))
		delete(bound, "rubric_sha256")
		dossier["review_binding"] = "sha256:" + digest(map[string]any{"schema": "quick-pending-review-binding-v1", "rubric_sha256": dossier["rubric_sha256"], "dossier": bound})
		dossierBytes, err := Render(dossier)
		if err != nil {
			return nil, err
		}
		dossierPath := "dossiers/" + text(r["id"]) + ".json"
		add(dossierPath, dossierBytes)
		descriptor := map[string]any{"dossier_path": dossierPath, "dossier_sha256": digestBytes(dossierBytes), "public_path": publicPath, "private_path": privatePath}
		for _, key := range []string{"id", "game", "review_binding", "record_sha256", "kg_sha256", "rubric_sha256", "status", "provenance_mode", "source_id", "runtime_id", "pending_sha256"} {
			descriptor[key] = dossier[key]
		}
		descriptors = append(descriptors, descriptor)
	}
	index := map[string]any{"schema": "quick-pending-index-v1", "qualified": false, "approval": nil, "pending_sha256": pendingSHA, "descriptors": descriptors}
	return map[string]any{"schema": "quick-pending-bundle-v1", "qualified": false, "qualification": quickPendingQualification, "index": index, "members": members}, nil
}

// QuickPendingView extracts an exact member for a specific role. This is byte
// extraction only, never semantic or freshness approval. Consumers must pin the
// whole bundle and revalidate its native inventory/tool/row bindings (Stage 3/4).
func QuickPendingView(path, item, view string) ([]byte, error) {
	if view != "public" && view != "dossier" {
		return nil, fmt.Errorf("pending view must be public or dossier")
	}
	b, err := pendingRegular(path, quickPendingMaxBytes)
	if err != nil {
		return nil, err
	}
	bundle, err := pendingDecode(b, quickPendingMaxBytes)
	if err != nil || !pendingExact(bundle, "schema", "qualified", "qualification", "index", "members") || bundle["schema"] != "quick-pending-bundle-v1" || bundle["qualified"] != false || bundle["qualification"] != quickPendingQualification {
		return nil, fmt.Errorf("quick pending bundle shape")
	}
	index := object(bundle["index"])
	if !pendingExact(index, "schema", "qualified", "approval", "pending_sha256", "descriptors") || index["schema"] != "quick-pending-index-v1" || index["qualified"] != false || index["approval"] != nil || !authorityDigest(index["pending_sha256"]) || !arrayShape(index["descriptors"], 1, 256) {
		return nil, fmt.Errorf("quick pending index shape")
	}
	members := map[string][]byte{}
	for _, v := range rows(bundle["members"]) {
		r := object(v)
		path := text(r["path"])
		data := []byte(text(r["data"]))
		if !pendingExact(r, "path", "bytes", "sha256", "data") || members[path] != nil || integer(r["bytes"]) != len(data) || digestBytes(data) != r["sha256"] {
			return nil, fmt.Errorf("quick pending member hash/duplicate")
		}
		members[path] = data
	}
	if digestBytes(members["pending.json"]) != index["pending_sha256"] || len(members) != 1+3*len(rows(index["descriptors"])) {
		return nil, fmt.Errorf("quick pending member coverage")
	}
	seen := map[string]bool{}
	var out []byte
	for _, v := range rows(index["descriptors"]) {
		r := object(v)
		id := text(r["id"])
		if !pendingExact(r, "dossier_path", "dossier_sha256", "public_path", "private_path", "id", "game", "review_binding", "record_sha256", "kg_sha256", "rubric_sha256", "status", "provenance_mode", "source_id", "runtime_id", "pending_sha256") || r["pending_sha256"] != index["pending_sha256"] || r["status"] != "pending" || r["provenance_mode"] != "source_backed" {
			return nil, fmt.Errorf("quick pending descriptor schema/status")
		}
		game := text(r["game"])
		if game != "intrusul" && game != "perechi" || game == "intrusul" && (!strings.HasPrefix(id, "iq92_") || !strings.HasPrefix(text(r["runtime_id"]), "vi_")) || game == "perechi" && (!strings.HasPrefix(id, "pq92_") || !strings.HasPrefix(text(r["runtime_id"]), "vp_")) || !pendingRuntimeID.MatchString(text(r["runtime_id"])) || !strings.HasPrefix(text(r["source_id"]), "aq92_") {
			return nil, fmt.Errorf("quick pending descriptor game/namespace")
		}
		for _, key := range []string{"dossier_sha256", "record_sha256", "kg_sha256", "rubric_sha256", "pending_sha256"} {
			if !authorityDigest(r[key]) {
				return nil, fmt.Errorf("quick pending descriptor digest")
			}
		}
		challenge := digest([]any{index["pending_sha256"], id, "quick-pending-regular-category-v1"})[:24]
		if r["dossier_path"] != "dossiers/"+id+".json" || r["public_path"] != "public/"+challenge+".json" || r["private_path"] != "private/"+challenge+".json" {
			return nil, fmt.Errorf("quick pending member role/path mismatch")
		}
		if seen[id] || !quickPendingID.MatchString(id) {
			return nil, fmt.Errorf("quick pending descriptor identity")
		}
		seen[id] = true
		dossierBytes := members[text(r["dossier_path"])]
		if digestBytes(dossierBytes) != r["dossier_sha256"] {
			return nil, fmt.Errorf("quick pending dossier hash")
		}
		dossier, err := pendingDecode(dossierBytes, quickPendingMaxBytes)
		if err != nil {
			return nil, err
		}
		if dossier["schema"] != "quick-pending-dossier-v1" || dossier["qualified"] != false || dossier["approval"] != nil {
			return nil, fmt.Errorf("quick pending dossier is not pending")
		}
		for _, key := range []string{"id", "game", "review_binding", "record_sha256", "kg_sha256", "rubric_sha256", "status", "provenance_mode", "source_id", "runtime_id", "pending_sha256"} {
			if !same(r[key], dossier[key]) {
				return nil, fmt.Errorf("quick pending descriptor/dossier mismatch")
			}
		}
		bound := object(clone(dossier))
		delete(bound, "review_binding")
		delete(bound, "rubric_sha256")
		if dossier["review_binding"] != "sha256:"+digest(map[string]any{"schema": "quick-pending-review-binding-v1", "rubric_sha256": dossier["rubric_sha256"], "dossier": bound}) || digestBytes(members[text(r["public_path"])]) != dossier["public_projection_sha256"] || digestBytes(members[text(r["private_path"])]) != dossier["private_projection_sha256"] {
			return nil, fmt.Errorf("quick pending review/projection binding")
		}
		public, err := pendingDecode(members[text(r["public_path"])], quickPendingMaxBytes)
		if err != nil || !pendingExact(public, "schema", "challenge_id", "game", "mode", "context", "tiles", "task", "response_schema") || public["schema"] != "quick-pending-public-v1" || public["challenge_id"] != challenge || public["game"] != r["game"] || public["mode"] != "regular_category" {
			return nil, fmt.Errorf("quick pending public role/schema mismatch")
		}
		if id == item {
			if view == "public" {
				out = members[text(r["public_path"])]
			} else {
				out = dossierBytes
			}
		}
	}
	if out == nil {
		return nil, fmt.Errorf("pending view must select one exact authored item")
	}
	return out, nil
}
