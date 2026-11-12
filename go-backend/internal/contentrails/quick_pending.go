package contentrails

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
)

// QuickPendingOptions are scratch inputs only. Registry/exclusions and current
// authority are resolved at fixed paths under Root; no source override exists.
type QuickPendingOptions struct {
	Packet, InventoryManifest, AuthorSeal, ReceiptManifest, Output string
}

var quickPendingID = regexp.MustCompile(`^(iq92_|pq92_|aq92_)[A-Za-z0-9_-]{1,180}$`)

func pendingExact(m map[string]any, keys ...string) bool {
	return m != nil && len(m) == len(keys) && allowedKeys(m, keys...)
}

func pendingDecode(b []byte, max int) (map[string]any, error) {
	if len(b) > max {
		return nil, fmt.Errorf("pending JSON byte bound")
	}
	return contentops.Decode(b)
}

func pendingScratch(root, path string) error {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path {
		return fmt.Errorf("pending output requires an absolute canonical scratch path")
	}
	if err := contentbuild.ValidatePrivatePendingParent(path); err != nil {
		return err
	}
	physical, err := filepath.EvalSymlinks(filepath.Dir(path))
	if err != nil || physical != filepath.Dir(path) {
		return fmt.Errorf("pending output parent must exist without symlinks")
	}
	rel, err := filepath.Rel(root, path)
	if err != nil || rel == "." || rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		return fmt.Errorf("pending output must be outside repository")
	}
	// A different checkout is not scratch either.
	for dir := filepath.Dir(path); ; dir = filepath.Dir(dir) {
		if _, err := os.Lstat(filepath.Join(dir, ".git")); err == nil || !os.IsNotExist(err) {
			return fmt.Errorf("pending output must be outside all Git checkouts")
		}
		if dir == filepath.Dir(dir) {
			break
		}
	}
	if _, err := os.Lstat(path); !os.IsNotExist(err) {
		return fmt.Errorf("pending output already exists or is not a new regular destination")
	}
	return nil
}

func pendingPacket(raw map[string]any, source *Source) ([]any, error) {
	if !pendingExact(raw, "schema", "baseline_source_sha256", "boards") || raw["schema"] != "quick-author-packet-v1" || raw["baseline_source_sha256"] != source.SHA256 || !arrayShape(raw["boards"], 1, 256) {
		return nil, fmt.Errorf("quick author packet shape/current source/bound")
	}
	old := rows(object(source.Raw["quick"])["boards"])
	if len(old)+len(rows(raw["boards"])) > 256 {
		return nil, fmt.Errorf("full quick authored board cap")
	}
	seen := map[string]bool{}
	for _, v := range old {
		seen[text(object(v)["id"])] = true
	}
	for _, v := range rows(raw["boards"]) {
		r := object(v)
		id, family := text(r["id"]), text(r["source_id"])
		if !pendingExact(r, "id", "game", "source_id", "category", "difficulty", "payload", "sources", "rationale") || !quickPendingID.MatchString(id) || !quickPendingID.MatchString(family) || !strings.HasPrefix(family, "aq92_") || strings.TrimSpace(text(r["rationale"])) == "" || seen[id] || !sourcesValue(r["sources"]) || !arrayShape(r["sources"], 1, 16) {
			return nil, fmt.Errorf("quick pending authored row/reference/identity shape")
		}
		if r["game"] == "intrusul" && !strings.HasPrefix(id, "iq92_") || r["game"] == "perechi" && !strings.HasPrefix(id, "pq92_") || r["game"] != "intrusul" && r["game"] != "perechi" {
			return nil, fmt.Errorf("quick authored/game namespace mismatch")
		}
		seen[id] = true
	}
	return rows(raw["boards"]), nil
}

// pendingEvidence binds existing capture bytes, chronology and the complete
// author URL set. It does not authenticate a fetcher or waive source policy;
// admissibility and independent reviewer sources remain mandatory Stage 4 gates.
func pendingEvidence(packet []byte, boards []any, seal, evidence map[string]any, captures map[string][]byte) error {
	packetSHA := digestBytes(packet)
	if !pendingExact(seal, "schema", "author", "packet_sha256", "sealed_at", "urls") || seal["schema"] != "quick-author-seal-v1" || seal["packet_sha256"] != packetSHA || strings.TrimSpace(text(seal["author"])) == "" || !stringArray(seal["urls"], 1, 4096) {
		return fmt.Errorf("quick author seal shape/identity/packet")
	}
	sealed, err := time.Parse(time.RFC3339Nano, text(seal["sealed_at"]))
	if err != nil {
		return fmt.Errorf("quick author seal requires zoned time")
	}
	if !pendingExact(evidence, "schema", "packet_sha256", "items", "receipts") || evidence["schema"] != "quick-author-evidence-v1" || evidence["packet_sha256"] != packetSHA || !arrayShape(evidence["receipts"], 1, 4096) {
		return fmt.Errorf("quick author evidence shape/packet")
	}
	want, items := map[string]bool{}, map[string]any{}
	for _, v := range boards {
		r := object(v)
		items[text(r["id"])] = "source_backed"
		for _, u := range ids(r["sources"]) {
			want[u] = true
		}
	}
	if !same(items, evidence["items"]) || len(ids(seal["urls"])) != len(want) {
		return fmt.Errorf("quick author evidence item or whole-author URL coverage")
	}
	for _, u := range ids(seal["urls"]) {
		if !want[u] {
			return fmt.Errorf("quick author seal URL coverage")
		}
	}
	seen := map[string]bool{}
	for _, v := range rows(evidence["receipts"]) {
		r := object(v)
		u, path := text(r["url"]), text(r["capture_path"])
		if !pendingExact(r, "url", "capture_path", "capture_sha256", "bytes", "fetched_by_role", "fetched_at") || !want[u] || seen[u] || r["fetched_by_role"] != "author" || !authorityDigest(r["capture_sha256"]) || digestBytes(captures[path]) != r["capture_sha256"] || len(captures[path]) == 0 || integer(r["bytes"]) != len(captures[path]) {
			return fmt.Errorf("quick author receipt identity/capture/coverage")
		}
		fetched, err := time.Parse(time.RFC3339Nano, text(r["fetched_at"]))
		if err != nil || fetched.After(sealed) {
			return fmt.Errorf("quick author receipt must precede seal")
		}
		seen[u] = true
	}
	if len(seen) != len(want) {
		return fmt.Errorf("quick author receipt complete URL coverage")
	}
	return nil
}

// PrepareQuickPending builds an unapproved byte-bound private bundle. Every
// material input comes from a frozen readset; only the new scratch output may
// be created. This action cannot produce a native semantic review or authority.
func PrepareQuickPending(ctx context.Context, root string, opt QuickPendingOptions) (map[string]any, error) {
	root, err := pendingRoot(root)
	if err != nil {
		return nil, err
	}
	if err = pendingScratch(root, opt.Output); err != nil {
		return nil, err
	}
	inputPaths := []string{opt.Packet, opt.InventoryManifest, opt.AuthorSeal, opt.ReceiptManifest}
	totalInputBytes := 0
	inputs, distinct := map[string][]byte{}, map[string]bool{}
	for _, path := range inputPaths {
		if distinct[path] || path == opt.Output {
			return nil, fmt.Errorf("pending input/output path collision")
		}
		distinct[path] = true
		b, err := pendingRegular(path, quickPendingMaxBytes)
		if err != nil {
			return nil, err
		}
		totalInputBytes += len(b)
		if totalInputBytes > 64<<20 {
			return nil, fmt.Errorf("pending external evidence aggregate exceeds 64 MiB")
		}
		inputs[path] = b
	}
	packet, err := pendingDecode(inputs[opt.Packet], MaxBytes)
	if err != nil {
		return nil, err
	}
	inventory, err := pendingDecode(inputs[opt.InventoryManifest], quickPendingMaxBytes)
	if err != nil {
		return nil, err
	}
	seal, err := pendingDecode(inputs[opt.AuthorSeal], MaxBytes)
	if err != nil {
		return nil, err
	}
	evidence, err := pendingDecode(inputs[opt.ReceiptManifest], MaxBytes)
	if err != nil {
		return nil, err
	}
	for _, v := range rows(evidence["receipts"]) {
		path := text(object(v)["capture_path"])
		if !distinct[path] {
			if path == opt.Output {
				return nil, fmt.Errorf("pending capture/output path collision")
			}
			b, err := pendingRegular(path, MaxBytes)
			if err != nil {
				return nil, err
			}
			totalInputBytes += len(b)
			if totalInputBytes > 64<<20 {
				return nil, fmt.Errorf("pending external evidence aggregate exceeds 64 MiB")
			}
			inputs[path], distinct[path] = b, true
			inputPaths = append(inputPaths, path)
		}
	}
	snap, err := captureQuickPending(root, inputPaths)
	if err != nil {
		return nil, err
	}
	if !same(inventory, snap.manifest) {
		return nil, fmt.Errorf("stale or incomplete quick pending inventory")
	}
	if err = snap.unchanged(); err != nil {
		return nil, err
	}
	// Stage 1 and the subsequent exact-rubric rebuild remain prerequisites.
	rubric := string(snap.files["docs/CRITIQUE_RUBRIC.md"])
	if !strings.Contains(rubric, "## I.") || !strings.Contains(rubric, "## J.") || contentbuild.TextSHA256([]byte(rubric)) != contentbuild.RubricSHA256 {
		return nil, fmt.Errorf("quick pending requires current compiled I/J rubric binding")
	}
	boards, err := pendingPacket(packet, snap.source)
	if err != nil {
		return nil, err
	}
	if err = pendingEvidence(inputs[opt.Packet], boards, seal, evidence, inputs); err != nil {
		return nil, err
	}
	kg, err := snap.object("cat_de_roman_esti/fixtures/kg_sample.json")
	if err != nil {
		return nil, err
	}
	g, err := contentbuild.QuickGraphSnapshot(kg)
	if err != nil {
		return nil, err
	}
	core, err := snap.object("cat_de_roman_esti/fixtures/derived_catalog_v38.json")
	if err != nil {
		return nil, err
	}
	current, err := snap.object("cat_de_roman_esti/fixtures/quick_games_v92.json")
	if err != nil {
		return nil, err
	}
	if err = snap.quickArtifactBound(); err != nil {
		return nil, err
	}
	bind := map[string]any{}
	for _, name := range contentbuild.SourceNames {
		bind[name] = contentbuild.TextSHA256(snap.files["cat_de_roman_esti/fixtures/"+name])
	}
	if !same(current["authored"], object(snap.source.Raw["quick"])["boards"]) {
		return nil, fmt.Errorf("current quick source/authored stock differs")
	}
	if err = contentbuild.ValidateQuickCatalog(current, core, g, bind); err != nil {
		return nil, fmt.Errorf("current quick stock: %w", err)
	}
	all := append(append([]any{}, rows(current["authored"])...), boards...)
	rated, nodes, err := contentbuild.ValidateQuickRows(all, rows(core["boards"]), g)
	if err != nil {
		return nil, err
	}
	screen, err := pendingScreen(snap, boards, rated[len(rows(current["authored"])):])
	if err != nil {
		return nil, err
	}
	// Check the actual projected non-review catalog and full next source bytes.
	// Stage 4 must recheck the final catalog including real review descriptors.
	projected, err := Render(map[string]any{"kind": "quick-pending-catalog-projection-v1", "authored": all, "boards": rated, "nodes": nodes, "bindings": current["bindings"], "approval": nil})
	if err != nil || len(projected) > 2<<20 {
		return nil, fmt.Errorf("quick pending catalog projection exceeds 2 MiB")
	}
	nextSource := object(clone(snap.source.Raw))
	nextSource["quick"] = map[string]any{"boards": all}
	nextBytes, err := Render(nextSource)
	if err != nil || len(nextBytes) > MaxBytes {
		return nil, fmt.Errorf("full quick authored source exceeds 4 MiB")
	}
	tool, err := pendingTool()
	if err != nil {
		return nil, err
	}
	toolPath := text(tool["path"])
	if _, collides := inputs[toolPath]; collides {
		return nil, fmt.Errorf("pending producer path collides with author/evidence document")
	}
	// Documents stay capped at 32 MiB; only this explicit producer uses its
	// independently bounded 256 MiB compact identity/digest snapshot.
	readset, err := contentops.CaptureRegularReadSetWithProducer(append(append([]string{}, snap.paths...), inputPaths...), toolPath, text(tool["sha256"]), int64(integer(tool["bytes"])))
	if err != nil {
		return nil, err
	}
	data, err := content.Load()
	if err != nil {
		return nil, err
	}
	data = quickOverlay(data, g, rated)
	bundle, err := pendingBundle(ctx, snap, boards, rated[len(rows(current["authored"])):], nodes, data, inputs, opt, screen, tool)
	if err != nil {
		return nil, err
	}
	blob, err := Render(bundle)
	if err != nil || len(blob) > quickPendingMaxBytes {
		return nil, fmt.Errorf("quick pending bundle exceeds 32 MiB")
	}
	if err = ctx.Err(); err != nil {
		return nil, err
	}
	verify := func() error {
		if err := ctx.Err(); err != nil {
			return err
		}
		if err := snap.unchanged(); err != nil {
			return err
		}
		for path, expected := range inputs {
			actual, err := pendingRegular(path, quickPendingMaxBytes)
			if err != nil || digestBytes(actual) != digestBytes(expected) {
				return fmt.Errorf("quick pending external input changed")
			}
		}
		return nil
	}
	if err = pendingScratch(root, opt.Output); err != nil {
		return nil, err
	}
	if err = publishQuickPending(ctx, opt.Output, blob, readset, verify); err != nil {
		return nil, err
	}
	return map[string]any{"ok": true, "mode": "quick-pending-private", "qualified": false, "approval": nil, "items": len(boards), "sha256": digestBytes(blob)}, nil
}

func pendingInputBindings(inputs map[string][]byte) []any {
	paths := make([]string, 0, len(inputs))
	for path := range inputs {
		paths = append(paths, path)
	}
	sort.Strings(paths)
	out := []any{}
	for _, path := range paths {
		out = append(out, map[string]any{"path": path, "sha256": digestBytes(inputs[path]), "bytes": len(inputs[path])})
	}
	return out
}

// publishQuickPending checks cancellation and all frozen inputs on both sides
// of the single private publication. A cancellation after linking invokes the
// publisher's same-inode cleanup just like a stale readset.
func publishQuickPending(ctx context.Context, path string, blob []byte, readset contentops.ReadSet, verify func() error) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	check := func() error {
		if err := ctx.Err(); err != nil {
			return err
		}
		if err := verify(); err != nil {
			return err
		}
		return ctx.Err()
	}
	return contentbuild.WritePrivatePendingArtifact(path, blob, func(publish func() error) error {
		return contentops.GuardedTransaction(filepath.Dir(path), nil, readset, func() error {
			if err := check(); err != nil {
				return err
			}
			if err := publish(); err != nil {
				return err
			}
			return check()
		})
	})
}
