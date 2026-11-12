package contentrails

import (
	"context"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
	"path/filepath"
)

type quickBridgeSession struct {
	root, framePath, frameSHA string
	frame, pending            map[string]any
	dossiers                  map[string]map[string]any
	material                  map[string]map[string]any
	files                     *quickBridgeFiles
	snap                      *quickPendingSnapshot
	raw                       []any
	names                     map[string]string
}

func loadQuickBridge(ctx context.Context, root, framePath, pin string, cachePins ...QuickCachePin) (*quickBridgeSession, error) {
	root, err := pendingRoot(root)
	if err != nil {
		return nil, err
	}
	b, err := pendingRegular(framePath, MaxBytes)
	if err != nil {
		return nil, err
	}
	if !authorityDigest(pin) || digestBytes(b) != pin {
		return nil, fmt.Errorf("quick bridge independently pinned full frame differs")
	}
	frame, err := pendingDecode(b, MaxBytes)
	frameKeys := []string{"schema", "bundle", "native_build_proof", "operator_replay", "author_release", "review_evidence", "artifacts", "factual_envelope", "quality_envelope", "critic_closure", "history_closure"}
	if frame["schema"] == "quick-bridge-frame-v3" {
		frameKeys = append(frameKeys, "author_cache_binding")
	}
	if err != nil || !pendingExact(frame, frameKeys...) || frame["schema"] != "quick-bridge-frame-v2" && frame["schema"] != "quick-bridge-frame-v3" {
		return nil, fmt.Errorf("quick full bridge requires frame-v2 or cache-bound frame-v3 with explicit history closure")
	}
	cacheContext, err := cachePin(cachePins)
	if err != nil {
		return nil, err
	}
	files := &quickBridgeFiles{blobs: map[string][]byte{framePath: b}, total: len(b), cachePin: cacheContext}
	if frame["schema"] == "quick-bridge-frame-v3" {
		ref, e := cacheRef(frame["author_cache_binding"])
		if e != nil || cacheContext.Path == "" || ref["path"] != cacheContext.Path || ref["sha256"] != cacheContext.SHA256 {
			return nil, fmt.Errorf("quick frame-v3 independent cache pin differs")
		}
	} else if cacheContext.Path != "" {
		return nil, fmt.Errorf("known v2 exposure context requires frame-v3")
	}
	material := map[string]map[string]any{}
	for _, key := range []string{"bundle", "native_build_proof", "operator_replay", "author_release", "review_evidence", "artifacts", "factual_envelope", "quality_envelope", "critic_closure", "history_closure"} {
		ref := object(frame[key])
		if _, exists := files.blobs[text(ref["path"])]; exists {
			return nil, fmt.Errorf("quick bridge frame path alias")
		}
		value, err := files.object(ref)
		if err != nil {
			return nil, err
		}
		material[key] = value
	}
	snap, err := captureQuickPending(root, nil)
	if err != nil {
		return nil, err
	}
	pending, dossiers, public, private, err := bridgePendingWithHistory(root, frame, material["bundle"], snap, files, true)
	if err != nil {
		return nil, err
	}
	if frame["schema"] == "quick-bridge-frame-v3" {
		context, e := bridgeCacheContext(pending, files)
		if e != nil {
			return nil, e
		}
		if !same(context["binding"], map[string]any{"path": object(frame["author_cache_binding"])["path"], "sha256": object(frame["author_cache_binding"])["sha256"]}) || integer(object(frame["author_cache_binding"])["bytes"]) != len(files.blobs[cacheContext.Path]) {
			return nil, fmt.Errorf("quick frame-v3 cache descriptor differs")
		}
	} else if object(pending["bindings"])["author_cache_binding_sha256"] != nil {
		return nil, fmt.Errorf("v2 pending requires full frame-v3")
	}
	consumer, err := bridgeProof(root, material["native_build_proof"], pending, snap, files)
	if err != nil {
		return nil, err
	}
	pending["_bridge"] = map[string]any{"pending_sha256": object(material["bundle"]["index"])["pending_sha256"]}
	raw, names, err := bridgeReviews(pending, dossiers, material, files)
	if err != nil {
		return nil, err
	}
	if err = bridgeCritic(root, frame, pending, dossiers, public, private, material, consumer, names, files); err != nil {
		return nil, err
	}
	if err = bridgeHistoryWithCache(snap, pending, material["history_closure"], names, material, files); err != nil {
		return nil, err
	}
	s := &quickBridgeSession{root, framePath, pin, frame, pending, dossiers, material, files, snap, raw, names}
	if err = s.verify(ctx, ""); err != nil {
		return nil, err
	}
	return s, nil
}
func (s *quickBridgeSession) paths(except string) []string {
	out, seen := []string{}, map[string]bool{}
	for _, p := range s.snap.paths {
		if p != except && !seen[p] {
			out = append(out, p)
			seen[p] = true
		}
	}
	for p := range s.files.blobs {
		if p != except && !seen[p] {
			out = append(out, p)
			seen[p] = true
		}
	}
	return out
}
func (s *quickBridgeSession) verify(ctx context.Context, except string) error {
	if len(s.files.blobs) > 4100 || s.files.total > 64<<20 {
		return fmt.Errorf("quick bridge complete external readset cap")
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	if except == "" {
		if err := s.snap.unchanged(); err != nil {
			return err
		}
	} else {
		paths, err := pendingPaths(s.root, s.snap.source)
		if err != nil || !same(paths, s.snap.paths) {
			return fmt.Errorf("quick bridge source membership changed")
		}
		for relative, want := range s.snap.files {
			path := filepath.Join(s.root, filepath.FromSlash(relative))
			if path == except {
				continue
			}
			got, err := pendingRegular(path, quickPendingMaxBytes)
			if err != nil || digestBytes(got) != digestBytes(want) {
				return fmt.Errorf("quick bridge immutable inventory changed")
			}
		}
	}
	if except == "" {
		return s.files.unchanged()
	}
	for path, want := range s.files.blobs {
		if path == except {
			continue
		}
		got, e := pendingRegular(path, quickPendingMaxBytes)
		if e != nil || digestBytes(got) != digestBytes(want) {
			return fmt.Errorf("quick bridge bound raw/proof input changed")
		}
	}
	return nil
}
func (s *quickBridgeSession) readset(except string) (contentops.ReadSet, error) {
	tool := object(s.pending["tool"])
	return contentops.CaptureRegularReadSetWithProducer(s.paths(except), text(tool["path"]), text(tool["sha256"]), int64(integer(tool["bytes"])))
}
func (s *quickBridgeSession) publish(ctx context.Context, path string, value map[string]any) (map[string]any, error) {
	if err := pendingScratch(s.root, path); err != nil {
		return nil, err
	}
	for _, p := range s.paths("") {
		if path == p {
			return nil, fmt.Errorf("quick bridge output/input alias")
		}
	}
	b, err := Render(value)
	if err != nil || len(b) > quickPendingMaxBytes {
		return nil, fmt.Errorf("quick bridge output byte bound")
	}
	set, err := s.readset("")
	if err != nil {
		return nil, err
	}
	if err = publishQuickPending(ctx, path, b, set, func() error { return s.verify(ctx, "") }); err != nil {
		return nil, err
	}
	return map[string]any{"ok": true, "qualified": false, "approval": nil, "sha256": digestBytes(b)}, nil
}
