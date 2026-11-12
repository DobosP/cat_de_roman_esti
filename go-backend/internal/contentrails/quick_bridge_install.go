package contentrails

import (
	"context"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
	"path/filepath"
)

type quickInstallGuard struct {
	release *quickBridgeRelease
	target  string
	strict  contentops.ReadSet
	ctx     context.Context
}

func quickNeedsBridge(root string, source *Source) (bool, error) {
	if source == nil {
		return false, fmt.Errorf("quick bridge missing source")
	}
	baseline, err := pendingCurrentSource(root)
	if err != nil {
		return false, err
	}
	return !same(quickSemanticView(rows(object(source.Raw["quick"])["boards"])), quickSemanticView(rows(object(baseline.Raw["quick"])["boards"]))), nil
}
func (g *quickInstallGuard) verify(ctx context.Context, after bool) error {
	if g.ctx != nil {
		if err := g.ctx.Err(); err != nil {
			return err
		}
	}
	except := ""
	if after {
		except = g.target
	}
	if object(g.release.session.pending["bindings"])["author_cache_binding_sha256"] != nil {
		if _, e := bridgeCacheContext(g.release.session.pending, g.release.session.files); e != nil {
			return e
		}
	}
	if err := g.release.session.verify(ctx, except); err != nil {
		return err
	}
	return g.strict.Verify()
}
func InstallQuickBridge(ctx context.Context, root, path, pin string, cachePins ...QuickCachePin) error {
	b, err := pendingRegular(path, MaxBytes)
	if err != nil {
		return err
	}
	if !authorityDigest(pin) || digestBytes(b) != pin {
		return fmt.Errorf("quick bridge independent install frame pin differs")
	}
	frame, err := pendingDecode(b, MaxBytes)
	installKeys := []string{"schema", "release", "proposal", "audit", "final_factual_review", "final_quality_review", "factual_binding", "quality_binding", "expected_sha256", "operator_checks"}
	if frame["schema"] == "quick-bridge-install-v2" {
		installKeys = append(installKeys, "author_cache_context")
	}
	if err != nil || !pendingExact(frame, installKeys...) || frame["schema"] != "quick-bridge-install-v1" && frame["schema"] != "quick-bridge-install-v2" || !authorityDigest(frame["expected_sha256"]) || !same(frame["operator_checks"], map[string]any{"fresh_same_role_finals": true, "final_isolation": true}) {
		return fmt.Errorf("quick bridge exact final install frame required")
	}
	releaseRef := object(frame["release"])
	release, err := loadQuickBridgeRelease(ctx, root, text(releaseRef["path"]), text(releaseRef["sha256"]), cachePins...)
	if err != nil {
		return err
	}
	s := release.session
	if object(s.pending["bindings"])["author_cache_binding_sha256"] != nil {
		context, e := bridgeCacheContext(s.pending, s.files)
		if e != nil {
			return e
		}
		if frame["schema"] != "quick-bridge-install-v2" || !same(frame["author_cache_context"], context) {
			return fmt.Errorf("quick install v2 complete exposure context required")
		}
	} else if frame["schema"] != "quick-bridge-install-v1" {
		return fmt.Errorf("quick install version/context mismatch")
	}
	if _, err = s.files.read(releaseRef); err != nil {
		return err
	}
	if _, exists := s.files.blobs[path]; exists {
		return fmt.Errorf("quick bridge install frame alias")
	}
	s.files.blobs[path] = b
	s.files.total += len(b)
	if s.files.total > 64<<20 {
		return fmt.Errorf("quick bridge external evidence byte bound")
	}
	material := map[string]map[string]any{}
	for _, key := range []string{"proposal", "audit", "final_factual_review", "final_quality_review", "factual_binding", "quality_binding"} {
		ref := object(frame[key])
		if _, exists := s.files.blobs[text(ref["path"])]; exists {
			return fmt.Errorf("quick bridge final input alias")
		}
		value, err := s.files.object(ref)
		if err != nil {
			return err
		}
		material[key] = value
	}
	catalog, err := BuildProposal(s.root, release.source, "quick", release.candidate, release.factual, release.quality)
	if err != nil {
		return err
	}
	if err = bridgePreservedCatalog(s, catalog); err != nil {
		return err
	}
	catalogBytes, err := Render(catalog)
	if err != nil || digestBytes(catalogBytes) != frame["expected_sha256"] || object(frame["proposal"])["sha256"] != frame["expected_sha256"] {
		return fmt.Errorf("quick bridge reviewed proposal/pin differs")
	}
	latestConfirmed, e := bridgeTime(release.confirmations["factual"]["signed_at"])
	if e != nil {
		return e
	}
	qualityConfirmed, e := bridgeTime(release.confirmations["quality"]["signed_at"])
	if e != nil {
		return e
	}
	if qualityConfirmed.After(latestConfirmed) {
		latestConfirmed = qualityConfirmed
	}
	finals := map[string]map[string]any{}
	for _, role := range []string{"factual", "quality"} {
		final := material["final_"+role+"_review"]
		binding := material[role+"_binding"]
		expected := map[string]any{"schema": "quick-bridge-final-binding-v1", "role": role, "reviewer": s.names[role], "release_sha256": release.pin, "frame_sha256": s.frameSHA, "canonical_review_sha256": object(release.raw[role+"_review"])["sha256"], "confirmation_sha256": object(release.raw[role+"_confirmation"])["sha256"], "raw_review_sha256": s.material[role+"_envelope"]["review_sha256"], "critic_closure_sha256": object(s.frame["critic_closure"])["sha256"], "history_closure_sha256": object(s.frame["history_closure"])["sha256"], "catalog_sha256": frame["expected_sha256"], "audit_sha256": object(frame["audit"])["sha256"], "final_review_sha256": object(frame["final_"+role+"_review"])["sha256"]}
		if object(s.pending["bindings"])["author_cache_binding_sha256"] != nil {
			context, e := bridgeCacheContext(s.pending, s.files)
			if e != nil {
				return e
			}
			expected["schema"] = "quick-bridge-final-binding-v2"
			expected["author_cache_context"] = context
		}
		comparable := object(clone(binding))
		delete(comparable, "signed_at")
		delete(comparable, "first_peer_read_at")
		if !same(comparable, expected) || len(binding) != len(expected)+2 || final["role"] != role || final["reviewer"] != s.names[role] || final["verdict"] != "accept" {
			return fmt.Errorf("quick bridge final original same-role/raw binding differs")
		}
		signed, e := bridgeTime(binding["signed_at"])
		if e != nil || !signed.After(latestConfirmed) {
			return fmt.Errorf("quick bridge final is not fresh after canonical confirmation")
		}
		finals[role] = binding
	}
	if err = bridgePeerBlindConfirmations(finals); err != nil {
		return err
	}
	target, err := ArtifactPath(s.root, "quick")
	if err != nil {
		return err
	}
	// Strict immutable evidence set excludes only the declared old->new mutable
	// artifact. The existing native installer validates the target and owns all
	// writes/rollback under its single normal mutable-target transaction.
	strict, err := s.readset(target)
	if err != nil {
		return err
	}
	guard := &quickInstallGuard{release, target, strict, ctx}
	if err = guard.verify(ctx, false); err != nil {
		return err
	}
	return installProposal(s.root, release.source, "quick", release.candidate, release.factual, release.quality, text(object(frame["proposal"])["path"]), text(object(frame["audit"])["path"]), text(object(frame["final_factual_review"])["path"]), text(object(frame["final_quality_review"])["path"]), text(frame["expected_sha256"]), release.sourcePath, guard)
}
func (g *quickInstallGuard) validateSource(root string, source *Source, candidate, factual, quality string) error {
	r := g.release
	absolute, err := filepath.Abs(root)
	if err != nil {
		return err
	}
	if absolute != r.session.root || source.SHA256 != r.source.SHA256 || !same(source.Raw, r.source.Raw) || candidate != r.candidate || factual != r.factual || quality != r.quality {
		return fmt.Errorf("quick bridge install inputs differ from confirmed full release")
	}
	return nil
}

func quickSemanticView(boards []any) []any {
	out := []any{}
	for _, v := range boards {
		r := object(v)
		m := map[string]any{}
		for _, key := range []string{"id", "game", "source_id", "category", "difficulty", "payload"} {
			m[key] = r[key]
		}
		out = append(out, m)
	}
	return out
}
