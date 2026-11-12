package contentrails

import (
	"context"
	"fmt"
)

type quickBridgeRelease struct {
	session                                 *quickBridgeSession
	path, pin                               string
	raw                                     map[string]any
	source                                  *Source
	sourcePath, candidate, factual, quality string
	confirmations                           map[string]map[string]any
}

func loadQuickBridgeRelease(ctx context.Context, root, path, pin string, cachePins ...QuickCachePin) (*quickBridgeRelease, error) {
	b, err := pendingRegular(path, MaxBytes)
	if err != nil {
		return nil, err
	}
	if !authorityDigest(pin) || digestBytes(b) != pin {
		return nil, fmt.Errorf("quick bridge independent release pin differs")
	}
	release, err := pendingDecode(b, MaxBytes)
	releaseKeys := []string{"schema", "bridge_frame", "prepare_bundle", "source", "candidate", "factual_review", "quality_review", "factual_confirmation", "quality_confirmation", "operator_checks"}
	if release["schema"] == "quick-bridge-release-v2" {
		releaseKeys = append(releaseKeys, "author_cache_context")
	}
	if err != nil || !pendingExact(release, releaseKeys...) || release["schema"] != "quick-bridge-release-v1" && release["schema"] != "quick-bridge-release-v2" || !same(release["operator_checks"], map[string]any{"fresh_whole_candidate_same_role": true, "confirmation_isolation": true, "baseline_evidence_checked": true}) {
		return nil, fmt.Errorf("quick bridge exact independently reviewed release frame required")
	}
	frameRef := object(release["bridge_frame"])
	s, err := loadQuickBridge(ctx, root, text(frameRef["path"]), text(frameRef["sha256"]), cachePins...)
	if err != nil {
		return nil, err
	}
	if object(s.pending["bindings"])["author_cache_binding_sha256"] != nil {
		context, e := bridgeCacheContext(s.pending, s.files)
		if e != nil {
			return nil, e
		}
		if release["schema"] != "quick-bridge-release-v2" || !same(release["author_cache_context"], context) {
			return nil, fmt.Errorf("quick release v2 complete exposure context required")
		}
	} else if release["schema"] != "quick-bridge-release-v1" {
		return nil, fmt.Errorf("quick release version/context mismatch")
	}
	if _, err = s.files.read(frameRef); err != nil {
		return nil, err
	}
	if _, exists := s.files.blobs[path]; exists {
		return nil, fmt.Errorf("quick bridge release/frame collision")
	}
	s.files.blobs[path] = b
	s.files.total += len(b)
	if s.files.total > 64<<20 {
		return nil, fmt.Errorf("quick bridge external evidence byte bound")
	}
	inputs := map[string]map[string]any{}
	for _, key := range []string{"prepare_bundle", "source", "candidate", "factual_review", "quality_review", "factual_confirmation", "quality_confirmation"} {
		ref := object(release[key])
		if _, exists := s.files.blobs[text(ref["path"])]; exists {
			return nil, fmt.Errorf("quick bridge release input collision")
		}
		value, err := s.files.object(ref)
		if err != nil {
			return nil, err
		}
		inputs[key] = value
	}
	expected, err := bridgeFullDraft(s)
	if err != nil {
		return nil, err
	}
	expectedBytes, err := Render(expected)
	if err != nil {
		return nil, err
	}
	if digestBytes(expectedBytes) != object(release["prepare_bundle"])["sha256"] {
		return nil, fmt.Errorf("quick bridge full draft differs from current native regeneration")
	}
	members := bundleMembers(expected)
	sourceBytes := s.files.blobs[text(object(release["source"])["path"])]
	candidateBytes := s.files.blobs[text(object(release["candidate"])["path"])]
	if digestBytes(sourceBytes) != digestBytes(members["source.json"]) || digestBytes(candidateBytes) != digestBytes(members["candidate.json"]) {
		return nil, fmt.Errorf("quick bridge full source/candidate omission/change")
	}
	source, err := LoadSource(text(object(release["source"])["path"]))
	if err != nil {
		return nil, err
	}
	if source.SHA256 != expected["source_sha256"] {
		return nil, fmt.Errorf("quick bridge loaded full source CAS")
	}
	evidence, baseline, err := bridgeBaseline(s)
	if err != nil {
		return nil, err
	}
	confirmations := map[string]map[string]any{}
	for i, role := range []string{"factual", "quality"} {
		report := inputs[role+"_review"]
		confirmation := inputs[role+"_confirmation"]
		if err = bridgeCanonical(s, role, i, report, confirmation, release, expected, evidence[role], baseline[role]); err != nil {
			return nil, err
		}
		confirmations[role] = confirmation
	}
	if err = bridgePeerBlindConfirmations(confirmations); err != nil {
		return nil, err
	}
	if err = s.verify(ctx, ""); err != nil {
		return nil, err
	}
	return &quickBridgeRelease{s, path, pin, release, source, text(object(release["source"])["path"]), text(object(release["candidate"])["path"]), text(object(release["factual_review"])["path"]), text(object(release["quality_review"])["path"]), confirmations}, nil
}
func bridgeCanonical(s *quickBridgeSession, role string, index int, report, confirmation, release, draft, baselineEvidence, baseline map[string]any) error {
	sourceSHA, candidateSHA := draft["source_sha256"], draft["candidate_sha256"]
	binding := map[string]any{"schema": "quick-bridge-canonical-binding-v1", "frame_sha256": s.frameSHA, "prepare_bundle_sha256": object(release["prepare_bundle"])["sha256"], "source_sha256": sourceSHA, "baseline": baselineEvidence}
	if object(s.pending["bindings"])["author_cache_binding_sha256"] != nil {
		context, e := bridgeCacheContext(s.pending, s.files)
		if e != nil {
			return e
		}
		binding["schema"] = "quick-bridge-canonical-binding-v2"
		binding["author_cache_context"] = context
	}
	if !pendingExact(report, "kind", "role", "reviewer", "candidate_sha256", "items", "baseline_evidence", "evidence_sha256", "inherited_review_sha256") || report["kind"] != "quick-content-review-v1" || report["role"] != role || report["reviewer"] != s.names[role] || report["candidate_sha256"] != candidateSHA || !same(report["baseline_evidence"], binding) || report["evidence_sha256"] != s.frameSHA || report["inherited_review_sha256"] != object(baselineEvidence["review"])["sha256"] {
		return fmt.Errorf("quick bridge canonical full role/identity/candidate/evidence binding")
	}
	all := append(append([]any{}, rows(object(s.snap.source.Raw["quick"])["boards"])...), rows(s.pending["boards"])...)
	if !arrayShape(report["items"], len(all), len(all)) {
		return fmt.Errorf("quick bridge canonical full exact coverage")
	}
	wanted, newRaw := map[string]map[string]any{}, map[string]map[string]any{}
	for _, v := range all {
		r := object(v)
		wanted[text(r["id"])] = r
	}
	for _, v := range rows(object(s.raw[index])["items"]) {
		r := object(v)
		newRaw[text(r["id"])] = r
	}
	rawSHA := s.material[role+"_envelope"]["review_sha256"]
	judged := map[string]bool{}
	for _, v := range rows(report["items"]) {
		r := object(v)
		id := text(r["id"])
		authored := wanted[id]
		if authored == nil || judged[id] || r["verdict"] != "accept" || bridgeNorm(text(r["rationale"])) == "" || !sourcesValue(r["sources"]) {
			return fmt.Errorf("quick bridge canonical missing/unknown/duplicate/hold/unsafe judgment")
		}
		judged[id] = true
		if raw := newRaw[id]; raw != nil {
			expected := map[string]any{"id": raw["id"], "verdict": raw["verdict"], "rationale": raw["rationale"], "sources": raw["sources"], "evidence_basis": map[string]any{"schema": "quick-raw-binding-v1", "review_binding": raw["review_binding"], "record_sha256": raw["record_sha256"], "raw_review_sha256": rawSHA, "child_safe": true}}
			if !same(r, expected) {
				return fmt.Errorf("quick bridge translation changed original identity/verdict/rationale/ordered URLs")
			}
		} else {
			prior := object(baseline[id])
			basis := map[string]any{"schema": "quick-baseline-binding-v1", "record_sha256": digest(authored), "baseline_item_sha256": digest(prior), "baseline_review_sha256": object(baselineEvidence["review"])["sha256"], "child_safe": true}
			if !pendingExact(r, "id", "verdict", "rationale", "sources", "inherited", "evidence_basis") || r["inherited"] != true || !same(r["sources"], prior["sources"]) || !same(r["evidence_basis"], basis) {
				return fmt.Errorf("quick bridge canonical old baseline evidence changed/omitted")
			}
		}
	}
	confirmationKeys := []string{"schema", "role", "reviewer", "signed_at", "first_peer_read_at", "frame_sha256", "prepare_bundle_sha256", "source_sha256", "candidate_sha256", "canonical_review_sha256", "baseline_evidence", "items", "verdict", "rationale"}
	confirmationSchema := "quick-full-candidate-confirmation-v1"
	if object(s.pending["bindings"])["author_cache_binding_sha256"] != nil {
		context, e := bridgeCacheContext(s.pending, s.files)
		if e != nil {
			return e
		}
		confirmationSchema = "quick-full-candidate-confirmation-v2"
		confirmationKeys = append(confirmationKeys, "author_cache_context")
		if !same(confirmation["author_cache_context"], context) {
			return fmt.Errorf("quick canonical confirmation v2 exposure context differs")
		}
	}
	if !pendingExact(confirmation, confirmationKeys...) || confirmation["schema"] != confirmationSchema || confirmation["role"] != role || confirmation["reviewer"] != s.names[role] || confirmation["frame_sha256"] != s.frameSHA || confirmation["prepare_bundle_sha256"] != object(release["prepare_bundle"])["sha256"] || confirmation["source_sha256"] != sourceSHA || confirmation["candidate_sha256"] != candidateSHA || confirmation["canonical_review_sha256"] != object(release[role+"_review"])["sha256"] || !same(confirmation["baseline_evidence"], baselineEvidence) || confirmation["verdict"] != "accept" || bridgeNorm(text(confirmation["rationale"])) == "" || !arrayShape(confirmation["items"], len(all), len(all)) {
		return fmt.Errorf("quick bridge fresh full-candidate original same-role confirmation required")
	}
	signed, err := bridgeTime(confirmation["signed_at"])
	replayed, _ := bridgeTime(s.material["operator_replay"]["created_at"])
	if err != nil || !signed.After(replayed) {
		return fmt.Errorf("quick bridge canonical confirmation is not fresh after raw replay")
	}
	seen := map[string]bool{}
	for _, v := range rows(confirmation["items"]) {
		r := object(v)
		id := text(r["id"])
		authored := wanted[id]
		basis := "baseline_unchanged"
		if newRaw[id] != nil {
			basis = "fresh_raw"
		}
		if !pendingExact(r, "id", "record_sha256", "child_safe", "evidence_checked", "evidence_basis") || authored == nil || seen[id] || r["record_sha256"] != digest(authored) || r["child_safe"] != true || r["evidence_checked"] != true || r["evidence_basis"] != basis {
			return fmt.Errorf("quick bridge full per-item evidence/safety confirmation incomplete")
		}
		seen[id] = true
	}
	return nil
}
func bridgePeerBlindConfirmations(confirmations map[string]map[string]any) error {
	f, err := bridgeTime(confirmations["factual"]["signed_at"])
	if err != nil {
		return err
	}
	q, err := bridgeTime(confirmations["quality"]["signed_at"])
	if err != nil {
		return err
	}
	for _, c := range confirmations {
		if c["first_peer_read_at"] != nil {
			t, e := bridgeTime(c["first_peer_read_at"])
			if e != nil || !t.After(f) || !t.After(q) {
				return fmt.Errorf("quick bridge whole-candidate peer read before both signed")
			}
		}
	}
	return nil
}
func ProposeQuickBridge(ctx context.Context, root, release, pin, output string, cachePins ...QuickCachePin) (map[string]any, error) {
	r, err := loadQuickBridgeRelease(ctx, root, release, pin, cachePins...)
	if err != nil {
		return nil, err
	}
	catalog, err := BuildProposal(r.session.root, r.source, "quick", r.candidate, r.factual, r.quality)
	if err != nil {
		return nil, err
	}
	if err = bridgePreservedCatalog(r.session, catalog); err != nil {
		return nil, err
	}
	return r.session.publish(ctx, output, catalog)
}
func bridgePreservedCatalog(s *quickBridgeSession, catalog map[string]any) error {
	expected := append(append([]any{}, rows(object(s.snap.source.Raw["quick"])["boards"])...), rows(s.pending["boards"])...)
	if !same(catalog["authored"], expected) || !arrayShape(catalog["excluded"], 0, 0) {
		return fmt.Errorf("quick bridge proposal silently dropped or changed authored rows")
	}
	current, err := s.snap.object("cat_de_roman_esti/fixtures/quick_games_v92.json")
	if err != nil {
		return err
	}
	byID := map[string]map[string]any{}
	for _, v := range rows(catalog["boards"]) {
		r := object(v)
		byID[text(r["id"])] = r
	}
	for _, v := range rows(current["boards"]) {
		old := object(clone(v))
		next := object(clone(byID[text(old["id"])]))
		for _, key := range []string{"standard_rank", "starter_rank"} {
			delete(old, key)
			delete(next, key)
		}
		if !same(old, next) {
			return fmt.Errorf("quick bridge old runtime payload/score changed")
		}
	}
	return nil
}
