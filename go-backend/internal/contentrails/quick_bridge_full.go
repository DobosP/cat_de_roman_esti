package contentrails

import (
	"context"
	"fmt"
)

func bridgeNextSource(s *quickBridgeSession) (*Source, []byte, error) {
	a, sources, err := pendingAuthoritySources(s.root)
	if err != nil {
		return nil, nil, err
	}
	base := s.snap.source
	chain := rows(a.raw["source_chain"])
	if len(chain) > 0 {
		base = sources[text(object(chain[len(chain)-1])["sha256"])]
	}
	if base == nil || !same(object(base.Raw["quick"])["boards"], object(s.snap.source.Raw["quick"])["boards"]) {
		return nil, nil, fmt.Errorf("quick bridge latest full source/quick authority disagreement; rebase first")
	}
	next := object(clone(base.Raw))
	next["version"], next["parent_source_sha256"] = base.Version+1, base.SHA256
	next["quick"] = map[string]any{"boards": append(append([]any{}, rows(object(base.Raw["quick"])["boards"])...), rows(s.pending["boards"])...)}
	b, err := Render(next)
	if err != nil {
		return nil, nil, err
	}
	source, err := decodeSource(b, base.SHA256, base.Version+1)
	return source, b, err
}
func bridgeBaseline(s *quickBridgeSession) (map[string]map[string]any, map[string]map[string]any, error) {
	a, err := parseInstalledAuthorities(installedAuthorityBytes, InstalledAuthoritiesSHA256)
	if err != nil {
		return nil, nil, err
	}
	entry := object(object(a.raw["rails"])["quick"])
	if entry == nil {
		return nil, nil, fmt.Errorf("quick bridge baseline authority missing")
	}
	evidence, reports := map[string]map[string]any{}, map[string]map[string]any{}
	old := rows(object(s.snap.source.Raw["quick"])["boards"])
	for _, role := range []string{"factual", "quality"} {
		ref := object(entry[role+"_review"])
		b := s.snap.files[text(ref["path"])]
		raw, err := pendingDecode(b, MaxBytes)
		if err != nil || digestBytes(b) != ref["sha256"] || raw["kind"] != "quick-content-review-v1" || raw["role"] != role || !arrayShape(raw["items"], len(old), len(old)) {
			return nil, nil, fmt.Errorf("quick bridge original baseline semantic evidence differs")
		}
		byID := map[string]any{}
		for _, v := range rows(raw["items"]) {
			r := object(v)
			id := text(r["id"])
			if id == "" || byID[id] != nil || r["verdict"] != "accept" {
				return nil, nil, fmt.Errorf("quick bridge baseline full accepted coverage")
			}
			byID[id] = r
		}
		for _, v := range old {
			if byID[text(object(v)["id"])] == nil {
				return nil, nil, fmt.Errorf("quick bridge baseline old row omitted")
			}
		}
		evidence[role] = map[string]any{"schema": "quick-baseline-evidence-v1", "source_sha256": s.snap.source.SHA256, "artifact_sha256": entry["artifact_sha256"], "review": ref, "item_sha256": map[string]any{}}
		for id, r := range byID {
			object(evidence[role]["item_sha256"])[id] = digest(r)
		}
		reports[role] = byID
	}
	return evidence, reports, nil
}
func bridgeFullDraft(s *quickBridgeSession) (map[string]any, error) {
	source, sourceBytes, err := bridgeNextSource(s)
	if err != nil {
		return nil, err
	}
	candidate, err := Candidate(s.root, source, "quick", false)
	if err != nil {
		return nil, err
	}
	candidateBytes, err := Render(candidate)
	if err != nil || len(candidateBytes) > MaxBytes {
		return nil, fmt.Errorf("quick full candidate byte bound")
	}
	evidence, baseline, err := bridgeBaseline(s)
	if err != nil {
		return nil, err
	}
	members := []any{}
	add := func(path string, b []byte) {
		members = append(members, map[string]any{"path": path, "bytes": len(b), "sha256": digestBytes(b), "data": string(b)})
	}
	add("source.json", sourceBytes)
	add("candidate.json", candidateBytes)
	for i, role := range []string{"factual", "quality"} {
		items := []any{}
		for _, v := range rows(object(s.snap.source.Raw["quick"])["boards"]) {
			r := object(v)
			id := text(r["id"])
			items = append(items, map[string]any{"id": id, "record_sha256": digest(r), "judgment": nil, "baseline_item": baseline[role][id], "baseline_evidence": evidence[role]})
		}
		for _, v := range rows(object(s.raw[i])["items"]) {
			r := object(v)
			items = append(items, map[string]any{"id": r["id"], "record_sha256": r["record_sha256"], "judgment": r, "baseline_item": nil, "baseline_evidence": nil})
		}
		draft := map[string]any{"kind": "quick-canonical-review-draft-v1", "role": role, "reviewer": s.names[role], "frame_sha256": s.frameSHA, "source_sha256": source.SHA256, "candidate_sha256": digestBytes(candidateBytes), "baseline_evidence": evidence[role], "items": items, "approval": nil, "requires_fresh_whole_candidate_confirmation": true}
		b, err := Render(draft)
		if err != nil {
			return nil, err
		}
		add(role+"-draft.json", b)
	}
	core, err := s.snap.object("cat_de_roman_esti/fixtures/derived_catalog_v38.json")
	if err != nil {
		return nil, err
	}
	// Canonical digest binds the complete frozen core payload without changing it.
	return map[string]any{"schema": "quick-full-draft-bundle-v1", "frame_sha256": s.frameSHA, "pending_sha256": object(s.pending["_bridge"])["pending_sha256"], "baseline_source_sha256": s.snap.source.SHA256, "preserved_old_rows": s.pending["preserved_old_rows"], "core_payload_sha256": digest(core["boards"]), "source_sha256": source.SHA256, "candidate_sha256": digestBytes(candidateBytes), "members": members, "qualified": false, "approval": nil}, nil
}
func PrepareQuickBridge(ctx context.Context, root, frame, pin, output string) (map[string]any, error) {
	s, err := loadQuickBridge(ctx, root, frame, pin)
	if err != nil {
		return nil, err
	}
	draft, err := bridgeFullDraft(s)
	if err != nil {
		return nil, err
	}
	return s.publish(ctx, output, draft)
}

// QuickFullDraftView is byte extraction only. Release/install always regenerate
// and compare this entire native bundle under current complete raw bindings.
func QuickFullDraftView(path, member string) ([]byte, error) {
	allowed := map[string]bool{"source.json": true, "candidate.json": true, "factual-draft.json": true, "quality-draft.json": true}
	if !allowed[member] {
		return nil, fmt.Errorf("quick full draft role member")
	}
	b, err := pendingRegular(path, quickPendingMaxBytes)
	if err != nil {
		return nil, err
	}
	bundle, err := pendingDecode(b, quickPendingMaxBytes)
	if err != nil || !pendingExact(bundle, "schema", "frame_sha256", "pending_sha256", "baseline_source_sha256", "preserved_old_rows", "core_payload_sha256", "source_sha256", "candidate_sha256", "members", "qualified", "approval") || bundle["schema"] != "quick-full-draft-bundle-v1" || bundle["qualified"] != false || bundle["approval"] != nil || !arrayShape(bundle["members"], 4, 4) {
		return nil, fmt.Errorf("quick full draft bundle schema")
	}
	seen := map[string]bool{}
	var out []byte
	for _, v := range rows(bundle["members"]) {
		r := object(v)
		name := text(r["path"])
		data := []byte(text(r["data"]))
		if !pendingExact(r, "path", "bytes", "sha256", "data") || !allowed[name] || seen[name] || integer(r["bytes"]) != len(data) || digestBytes(data) != r["sha256"] {
			return nil, fmt.Errorf("quick full draft member binding")
		}
		seen[name] = true
		if name == member {
			out = data
		}
	}
	return out, nil
}
