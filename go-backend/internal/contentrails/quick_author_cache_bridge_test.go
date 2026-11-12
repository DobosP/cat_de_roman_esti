//go:build linux

package contentrails

import (
	"fmt"
	"os"
	"testing"
)

// Existing synthetic raw-review fixtures are used only to assert refusal of
// false novelty. This cannot produce a content review, admission or real FQ GO.
func TestQuickAuthorCacheEveryExposedURLRefusesFactualNovelty(t *testing.T) {
	for chosen := 0; chosen < 13; chosen++ {
		t.Run(fmt.Sprint(chosen), func(t *testing.T) {
			f := newBridgeFixture(t)
			urls, original := []any{}, []any{}
			for i := 0; i < 13; i++ {
				u := fmt.Sprintf("https://example.test/exposure%02d", i)
				urls = append(urls, u)
				body := f.putBytes(fmt.Sprintf("exposure%02d.body", i), []byte(fmt.Sprintf("synthetic exposure %d", i)))
				original = append(original, map[string]any{"url": u, "capture_path": body["path"], "capture_sha256": body["sha256"], "bytes": body["bytes"], "fetched_by_role": "factual", "fetched_at": "2026-11-10T11:00:00Z"})
			}
			seal := map[string]any{"schema": "quick-author-seal-v2", "author": "Author synthetic distinct", "sealed_at": "2026-11-10T12:00:00Z", "urls": urls}
			ref := f.put("cache-seal.json", seal)
			f.files.blobs[text(ref["path"])], _ = os.ReadFile(text(ref["path"]))
			object(f.pending["bindings"])["author_seal_sha256"] = ref["sha256"]
			f.material["author_release"]["author_seal_sha256"] = ref["sha256"]
			evidence := map[string]any{"schema": "quick-author-evidence-v2", "receipts": original}
			ref = f.put("cache-evidence.json", evidence)
			f.files.blobs[text(ref["path"])], _ = os.ReadFile(text(ref["path"]))
			object(f.pending["bindings"])["author_evidence_sha256"] = ref["sha256"]
			f.material["review_evidence"]["receipts"] = append(rows(f.material["review_evidence"]["receipts"]), original...)
			selected := object(clone(original[chosen]))
			selected["chosen_by"] = f.material["factual_envelope"]["reviewer"]
			id := "iq92_synthetic_only"
			object(f.material["factual_envelope"]["reviewer_chosen_sources"])[id] = []any{selected}
			f.changeRaw("factual", func(r map[string]any) { object(rows(r["items"])[0])["sources"] = []any{urls[chosen]} })
			if _, _, err := bridgeReviews(f.pending, f.dossiers, f.material, f.files); err == nil {
				t.Fatal("first-factual author-exposed URL became reviewer novelty")
			}
		})
	}
}
func TestQuickAuthorCacheCanonicalConfirmationCannotLoseExposureContext(t *testing.T) {
	s, report, confirmation, release, draft, evidence, baseline := bridgeCanonicalFixture(t)
	b, _ := Render(map[string]any{"exposure_urls": []any{"https://example.test/uncited"}})
	sha := digestBytes(b)
	path := "/scratch/cache-binding"
	s.files = &quickBridgeFiles{blobs: map[string][]byte{path: b}, cachePin: QuickCachePin{path, sha}}
	object(s.pending["bindings"])["author_cache_binding_sha256"] = sha
	context, err := bridgeCacheContext(s.pending, s.files)
	if err != nil {
		t.Fatal(err)
	}
	object(report["baseline_evidence"])["schema"] = "quick-bridge-canonical-binding-v2"
	object(report["baseline_evidence"])["author_cache_context"] = context
	confirmation["schema"] = "quick-full-candidate-confirmation-v2"
	confirmation["author_cache_context"] = context
	if err = bridgeCanonical(s, "factual", 0, report, confirmation, release, draft, evidence, baseline); err != nil {
		t.Fatal(err)
	}
	delete(confirmation, "author_cache_context")
	if bridgeCanonical(s, "factual", 0, report, confirmation, release, draft, evidence, baseline) == nil {
		t.Fatal("canonical v2 confirmation erased U")
	}
}
func TestQuickAuthorCacheKnownContextCannotUseLegacyHistoryClosure(t *testing.T) {
	b, _ := Render(map[string]any{"exposure_urls": []any{"https://example.test/uncited"}})
	sha := digestBytes(b)
	path := "/scratch/cache-binding"
	pending := map[string]any{"bindings": map[string]any{"author_cache_binding_sha256": sha}}
	files := &quickBridgeFiles{blobs: map[string][]byte{path: b}, cachePin: QuickCachePin{path, sha}}
	if bridgeHistoryWithCache(nil, pending, map[string]any{"schema": "quick-history-closure-v1"}, nil, nil, files) == nil {
		t.Fatal("legacy closure erased known U")
	}
	files.cachePin = QuickCachePin{}
	if _, err := bridgeCacheContext(pending, files); err == nil {
		t.Fatal("bridge accepted missing independent Root pin")
	}
}
