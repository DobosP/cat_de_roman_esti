package contentrails

// Stage 4A deliberately stops before native semantic confirmation. A draft is
// not quick-content-review-v1 and is never an input to BuildProposal or install.
import (
	"context"
	"fmt"
	"net/url"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode"
	"unicode/utf8"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
)

const quickBridgeQualification = "Validated raw review fragments only; full-candidate same-role confirmation and guarded install binding are not implemented. No approval or installation authority."

type QuickBridgeDraftOptions struct{ Frame, FrameSHA256, Output string }

type quickBridgeFiles struct {
	blobs map[string][]byte
	total int
}

func (f *quickBridgeFiles) read(ref map[string]any) ([]byte, error) {
	if !pendingExact(ref, "path", "bytes", "sha256") || !authorityDigest(ref["sha256"]) || integer(ref["bytes"]) < 0 || integer(ref["bytes"]) > quickPendingMaxBytes {
		return nil, fmt.Errorf("quick bridge file descriptor shape/size")
	}
	path := text(ref["path"])
	b, err := pendingRegular(path, quickPendingMaxBytes)
	if err != nil {
		return nil, err
	}
	if integer(ref["bytes"]) != len(b) || digestBytes(b) != ref["sha256"] {
		return nil, fmt.Errorf("quick bridge bound bytes differ: %s", path)
	}
	if old, exists := f.blobs[path]; exists {
		if digestBytes(old) != digestBytes(b) {
			return nil, fmt.Errorf("quick bridge file changed during read")
		}
	} else {
		f.total += len(b)
		if f.total > 64<<20 {
			return nil, fmt.Errorf("quick bridge external evidence exceeds 64 MiB")
		}
		f.blobs[path] = b
	}
	return b, nil
}
func (f *quickBridgeFiles) two(ref map[string]any) ([]byte, error) {
	if !pendingExact(ref, "path", "sha256") || !authorityDigest(ref["sha256"]) {
		return nil, fmt.Errorf("quick bridge Stage3 file binding shape")
	}
	b, err := pendingRegular(text(ref["path"]), quickPendingMaxBytes)
	if err != nil {
		return nil, err
	}
	return f.read(map[string]any{"path": ref["path"], "sha256": ref["sha256"], "bytes": len(b)})
}
func (f *quickBridgeFiles) object(ref map[string]any) (map[string]any, error) {
	b, err := f.read(ref)
	if err != nil {
		return nil, err
	}
	return pendingDecode(b, quickPendingMaxBytes)
}
func (f *quickBridgeFiles) unchanged() error {
	for path, expected := range f.blobs {
		actual, err := pendingRegular(path, quickPendingMaxBytes)
		if err != nil || digestBytes(actual) != digestBytes(expected) {
			return fmt.Errorf("quick bridge input changed: %s", path)
		}
	}
	return nil
}

var bridgeFoldOnce sync.Once
var bridgeFold map[string]string
var bridgeFoldError error

func bridgeNorm(s string) string {
	bridgeFoldOnce.Do(func() {
		data, err := content.Load()
		if err != nil {
			bridgeFoldError = err
			return
		}
		bridgeFold = data.CasefoldMap
	})
	if bridgeFoldError != nil {
		return ""
	}
	var folded strings.Builder
	for _, c := range s {
		if value, ok := bridgeFold[string(c)]; ok {
			folded.WriteString(value)
		} else {
			folded.WriteRune(c)
		}
	}
	return strings.Join(strings.FieldsFunc(folded.String(), func(c rune) bool { return unicode.IsSpace(c) || c >= '\u001c' && c <= '\u001f' }), " ")
}
func bridgeTime(v any) (time.Time, error) { return time.Parse(time.RFC3339Nano, text(v)) }
func bridgeURL(value string) (string, error) {
	u, err := url.Parse(value)
	if err != nil || u == nil || u.User != nil || u.Opaque != "" || u.Hostname() == "" || u.Scheme != "http" && u.Scheme != "https" {
		return "", fmt.Errorf("quick bridge requires credential-free HTTP(S) source")
	}
	// Standing source hostnames are ASCII. Refuse unsupported Unicode host
	// spelling instead of claiming cross-runtime Unicode lowercase identity.
	for _, character := range u.Hostname() {
		if character > 127 {
			return "", fmt.Errorf("quick bridge source hostname requires ASCII spelling")
		}
	}
	u.Scheme, u.Host, u.Fragment = strings.ToLower(u.Scheme), strings.ToLower(u.Host), ""
	// Match the independence sidecar's integer port identity before removing
	// defaults: :0443 and :443 must never count as distinct research sources.
	if port := u.Port(); port != "" {
		number, err := strconv.Atoi(port)
		if err != nil || number < 0 || number > 65535 {
			return "", fmt.Errorf("quick bridge source port outside valid range")
		}
		u.Host = strings.TrimSuffix(u.Host, ":"+port) + ":" + strconv.Itoa(number)
	} else if strings.HasSuffix(u.Host, ":") {
		u.Host = strings.TrimSuffix(u.Host, ":")
	}
	if u.Scheme == "https" && strings.HasSuffix(u.Host, ":443") {
		u.Host = strings.TrimSuffix(u.Host, ":443")
	}
	if u.Scheme == "http" && strings.HasSuffix(u.Host, ":80") {
		u.Host = strings.TrimSuffix(u.Host, ":80")
	}
	if u.Path == "" {
		u.Path = "/"
	}
	query, err := url.ParseQuery(u.RawQuery)
	if err != nil {
		return "", err
	}
	// Python sorts decoded (key, value) pairs, including repeated-key values.
	for key := range query {
		// Python replaces invalid UTF-8 during query parsing. Conservatively
		// refuse such bytes so replacement aliases cannot appear independent.
		if !utf8.ValidString(key) {
			return "", fmt.Errorf("quick bridge source query requires valid UTF-8")
		}
		for _, value := range query[key] {
			if !utf8.ValidString(value) {
				return "", fmt.Errorf("quick bridge source query requires valid UTF-8")
			}
		}
		sort.Strings(query[key])
	}
	u.RawQuery = query.Encode()
	u.ForceQuery = false
	return u.String(), nil
}
func bridgeSources(value any) (map[string]bool, error) {
	if !sourcesValue(value) || !arrayShape(value, 1, 32) {
		return nil, fmt.Errorf("quick bridge requires 1..32 fetched HTTP(S) review sources")
	}
	out := map[string]bool{}
	for _, source := range ids(value) {
		u, err := bridgeURL(source)
		if err != nil || out[u] {
			return nil, fmt.Errorf("quick bridge duplicate/invalid normalized source")
		}
		out[u] = true
	}
	return out, nil
}

// DraftQuickBridge validates an independently pinned frame. The pin must come
// from Root's reviewed evidence, not from the author who supplied the frame.
// In particular the operator receipt attests actual compare-quick re-execution,
// dispatch isolation and first-fetch provenance; JSON parsing cannot prove them.
func DraftQuickBridge(ctx context.Context, root string, opt QuickBridgeDraftOptions) (map[string]any, error) {
	root, err := pendingRoot(root)
	if err != nil {
		return nil, err
	}
	if err = pendingScratch(root, opt.Output); err != nil {
		return nil, err
	}
	frameBytes, err := pendingRegular(opt.Frame, MaxBytes)
	if err != nil {
		return nil, err
	}
	if !authorityDigest(opt.FrameSHA256) || digestBytes(frameBytes) != opt.FrameSHA256 {
		return nil, fmt.Errorf("quick bridge independently supplied frame pin differs")
	}
	frame, err := pendingDecode(frameBytes, MaxBytes)
	if err != nil || !pendingExact(frame, "schema", "bundle", "native_build_proof", "operator_replay", "author_release", "review_evidence", "artifacts", "factual_envelope", "quality_envelope", "critic_closure") || frame["schema"] != "quick-bridge-frame-v1" {
		return nil, fmt.Errorf("quick bridge frame schema")
	}
	files := &quickBridgeFiles{blobs: map[string][]byte{opt.Frame: frameBytes}, total: len(frameBytes)}
	material := map[string]map[string]any{}
	for _, key := range []string{"bundle", "native_build_proof", "operator_replay", "author_release", "review_evidence", "artifacts", "factual_envelope", "quality_envelope", "critic_closure"} {
		ref := object(frame[key])
		path := text(ref["path"])
		if _, exists := files.blobs[path]; exists || path == opt.Output {
			return nil, fmt.Errorf("quick bridge frame input/output collision")
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
	pending, dossiers, public, private, err := bridgePending(root, frame, material["bundle"], snap, files)
	if err != nil {
		return nil, err
	}
	proof := material["native_build_proof"]
	consumer, err := bridgeProof(root, proof, pending, snap, files)
	if err != nil {
		return nil, err
	}
	// Internal context added only after strict native pending validation.
	pending["_bridge"] = map[string]any{"pending_sha256": object(material["bundle"]["index"])["pending_sha256"]}
	raw, identities, err := bridgeReviews(pending, dossiers, material, files)
	if err != nil {
		return nil, err
	}
	if err = bridgeCritic(root, frame, pending, dossiers, public, private, material, consumer, identities, files); err != nil {
		return nil, err
	}
	// This output preserves every raw field and row without producing canonical
	// accepts. The next increment must bind the FULL candidate, old stock and
	// these exact raw bytes before the original same-role reviewers confirm it.
	fragments := []any{}
	for i, role := range []string{"factual", "quality"} {
		fragments = append(fragments, map[string]any{"schema": "quick-review-fragment-draft-v1", "role": role, "reviewer": identities[role], "raw_review": raw[i], "approval": nil, "requires_full_candidate_confirmation": true})
	}
	out := map[string]any{"schema": "quick-bridge-draft-v1", "qualified": false, "approval": nil, "qualification": quickBridgeQualification, "frame_sha256": opt.FrameSHA256, "pending_sha256": digestBytes(bundleMembers(material["bundle"])["pending.json"]), "baseline_source_sha256": snap.source.SHA256, "baseline_source_version": snap.source.Version, "preserved_old_rows": pending["preserved_old_rows"], "new_rows": pending["boards"], "review_fragments": fragments, "input_bindings": pendingInputBindings(files.blobs)}
	blob, err := Render(out)
	if err != nil || len(blob) > quickPendingMaxBytes {
		return nil, fmt.Errorf("quick bridge draft byte bound")
	}
	paths := append([]string{}, snap.paths...)
	for path := range files.blobs {
		if path == opt.Output {
			return nil, fmt.Errorf("quick bridge output aliases evidence")
		}
		paths = append(paths, path)
	}
	tool := object(pending["tool"])
	readset, err := contentops.CaptureRegularReadSetWithProducer(paths, text(tool["path"]), text(tool["sha256"]), int64(integer(tool["bytes"])))
	if err != nil {
		return nil, err
	}
	verify := func() error {
		if err := ctx.Err(); err != nil {
			return err
		}
		if err := snap.unchanged(); err != nil {
			return err
		}
		return files.unchanged()
	}
	if err = verify(); err != nil {
		return nil, err
	}
	if err = publishQuickPending(ctx, opt.Output, blob, readset, verify); err != nil {
		return nil, err
	}
	return map[string]any{"ok": true, "mode": "quick-bridge-draft", "qualified": false, "approval": nil, "items": len(rows(pending["boards"])), "sha256": digestBytes(blob)}, nil
}

func bundleMembers(bundle map[string]any) map[string][]byte {
	out := map[string][]byte{}
	for _, v := range rows(bundle["members"]) {
		r := object(v)
		out[text(r["path"])] = []byte(text(r["data"]))
	}
	return out
}

func bridgePending(root string, frame, bundle map[string]any, snap *quickPendingSnapshot, files *quickBridgeFiles) (map[string]any, map[string]map[string]any, map[string]map[string]any, map[string]map[string]any, error) {
	return bridgePendingWithHistory(root, frame, bundle, snap, files, false)
}

func bridgePendingWithHistory(root string, frame, bundle map[string]any, snap *quickPendingSnapshot, files *quickBridgeFiles, hasHistory bool) (map[string]any, map[string]map[string]any, map[string]map[string]any, map[string]map[string]any, error) {
	fail := func() (map[string]any, map[string]map[string]any, map[string]map[string]any, map[string]map[string]any, error) {
		return nil, nil, nil, nil, fmt.Errorf("quick bridge current pending/dossier/stock binding differs")
	}
	index := object(bundle["index"])
	if !arrayShape(index["descriptors"], 1, 256) {
		return fail()
	}
	members := bundleMembers(bundle)
	pending, err := pendingDecode(members["pending.json"], quickPendingMaxBytes)
	if err != nil || !pendingExact(pending, "schema", "status", "provenance_mode", "qualified", "approval", "qualification", "baseline_source_sha256", "baseline_source_version", "bindings", "inventory", "tool", "input_bindings", "boards", "rated", "screen", "preserved_old_rows") || pending["schema"] != "quick-pending-v1" || pending["status"] != "pending" || pending["qualified"] != false || pending["approval"] != nil || pending["provenance_mode"] != "source_backed" || pending["qualification"] != quickPendingQualification || pending["baseline_source_sha256"] != snap.source.SHA256 || integer(pending["baseline_source_version"]) != snap.source.Version || !same(pending["inventory"], snap.manifest) {
		return fail()
	}
	tool, err := pendingTool()
	if err != nil || !same(tool, pending["tool"]) {
		return fail()
	}
	rubric := snap.files["docs/CRITIQUE_RUBRIC.md"]
	if contentbuild.TextSHA256(rubric) != contentbuild.RubricSHA256 || !strings.Contains(string(rubric), "## I.") || !strings.Contains(string(rubric), "## J.") {
		return fail()
	}
	bind := object(pending["bindings"])
	if !pendingExact(bind, "kg_sha256", "rubric_sha256", "inventory_sha256", "stock_sha256", "holds_sha256", "registry_sha256", "author_packet_sha256", "author_seal_sha256", "author_evidence_sha256", "tool_sha256") {
		return fail()
	}
	for _, value := range bind {
		if !authorityDigest(value) {
			return fail()
		}
	}
	if bind["inventory_sha256"] != digest(snap.manifest) || bind["tool_sha256"] != tool["sha256"] || bind["kg_sha256"] != contentbuild.TextSHA256(snap.files["cat_de_roman_esti/fixtures/kg_sample.json"]) || bind["rubric_sha256"] != contentbuild.TextSHA256(rubric) || bind["registry_sha256"] != digestBytes(snap.files["docs/content-registry/registry.jsonl"]) || bind["holds_sha256"] != digestBytes(snap.files["docs/content-registry/exclusions.json"]) {
		return fail()
	}
	// Deliberate Stage4A refusal. Empty unresolved lists do not override a false
	// complete flag. A relevance-closure schema needs independent review first.
	screen := object(pending["screen"])
	if bridgeStockClosure(screen) != nil && !hasHistory {
		return nil, nil, nil, nil, fmt.Errorf("quick bridge unresolved stock history; independent relevance closure is not implemented")
	}
	if !arrayShape(pending["input_bindings"], 4, 4100) {
		return fail()
	}
	selected, external, selectedPaths := map[string]map[string]any{}, map[string][]byte{}, map[string]bool{}
	for _, v := range rows(pending["input_bindings"]) {
		r := object(v)
		path := text(r["path"])
		relative, relErr := filepath.Rel(root, path)
		if relErr != nil || relative == "." || relative != ".." && !strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
			return fail()
		}
		if _, exists := external[path]; exists {
			return fail()
		}
		b, err := files.read(r)
		if err != nil {
			return nil, nil, nil, nil, err
		}
		external[path] = b
		value, decodeErr := pendingDecode(b, quickPendingMaxBytes)
		if decodeErr == nil {
			for key, schema := range map[string]string{"packet": "quick-author-packet-v1", "seal": "quick-author-seal-v1", "evidence": "quick-author-evidence-v1", "inventory": "quick-pending-inventory-v1"} {
				if value["schema"] == schema {
					if selected[key] != nil {
						return fail()
					}
					selected[key] = value
					selectedPaths[path] = true
				}
			}
		}
	}
	if len(selected) != 4 || !same(selected["inventory"], snap.manifest) {
		return fail()
	}
	usedPaths := map[string]bool{}
	for path := range selectedPaths {
		usedPaths[path] = true
	}
	for _, v := range rows(selected["evidence"]["receipts"]) {
		usedPaths[text(object(v)["capture_path"])] = true
	}
	if len(usedPaths) != len(external) {
		return fail()
	}
	for path := range external {
		if !usedPaths[path] {
			return fail()
		}
	}
	boards, err := pendingPacket(selected["packet"], snap.source)
	if err != nil || !same(boards, pending["boards"]) {
		return fail()
	}
	var packetBytes []byte
	for path, blob := range external {
		if digestBytes(blob) == bind["author_packet_sha256"] {
			packetBytes = external[path]
		}
	}
	if len(packetBytes) == 0 || digestBytes(bridgeOriginal(external, "quick-author-packet-v1")) != bind["author_packet_sha256"] || digestBytes(bridgeOriginal(external, "quick-author-seal-v1")) != bind["author_seal_sha256"] || digestBytes(bridgeOriginal(external, "quick-author-evidence-v1")) != bind["author_evidence_sha256"] {
		return fail()
	}
	if err = pendingEvidence(packetBytes, boards, selected["seal"], selected["evidence"], external); err != nil {
		return nil, nil, nil, nil, err
	}
	old := []any{}
	for _, v := range rows(object(snap.source.Raw["quick"])["boards"]) {
		row := object(v)
		old = append(old, map[string]any{"id": row["id"], "record_sha256": digest(row)})
	}
	if !same(old, pending["preserved_old_rows"]) {
		return fail()
	}
	kg, err := snap.object("cat_de_roman_esti/fixtures/kg_sample.json")
	if err != nil {
		return fail()
	}
	g, err := contentbuild.QuickGraphSnapshot(kg)
	if err != nil {
		return fail()
	}
	core, err := snap.object("cat_de_roman_esti/fixtures/derived_catalog_v38.json")
	if err != nil {
		return fail()
	}
	all := append(append([]any{}, rows(object(snap.source.Raw["quick"])["boards"])...), boards...)
	rated, _, err := contentbuild.ValidateQuickRows(all, rows(core["boards"]), g)
	if err != nil || !same(rated[len(old):], pending["rated"]) {
		return fail()
	}
	freshScreen, err := pendingScreen(snap, boards, rated[len(old):])
	if err != nil || !same(freshScreen, screen) {
		return fail()
	}
	dossiers, public, private := map[string]map[string]any{}, map[string]map[string]any{}, map[string]map[string]any{}
	for _, v := range rows(index["descriptors"]) {
		d := object(v)
		id := text(d["id"])
		if dossiers[id] != nil {
			return fail()
		}
		// The existing strict extractor validates complete bundle/member schemas,
		// exact dossier review binding and public/private byte hashes.
		b, err := QuickPendingView(text(object(frame["bundle"])["path"]), id, "dossier")
		if err != nil {
			return nil, nil, nil, nil, err
		}
		dossier, err := pendingDecode(b, quickPendingMaxBytes)
		if err != nil {
			return fail()
		}
		if dossier["baseline_source_sha256"] != snap.source.SHA256 || !same(dossier["bindings"], bind) || !same(dossier["screen"], screen) {
			return fail()
		}
		var authored map[string]any
		for _, row := range boards {
			if object(row)["id"] == id {
				authored = object(row)
			}
		}
		if authored == nil || dossier["record_sha256"] != digest(authored) || !same(dossier["semantic_payload"], authored["payload"]) || dossier["game"] != authored["game"] || dossier["category"] != authored["category"] || dossier["difficulty"] != authored["difficulty"] || dossier["source_id"] != authored["source_id"] {
			return fail()
		}
		pub, e1 := pendingDecode(members[text(d["public_path"])], quickPendingMaxBytes)
		priv, e2 := pendingDecode(members[text(d["private_path"])], quickPendingMaxBytes)
		if e1 != nil || e2 != nil {
			return fail()
		}
		dossiers[id], public[id], private[id] = dossier, pub, priv
	}
	if len(dossiers) != len(boards) {
		return fail()
	}
	return pending, dossiers, public, private, nil
}
func bridgeOriginal(external map[string][]byte, schema string) []byte {
	for _, b := range external {
		value, err := pendingDecode(b, quickPendingMaxBytes)
		if err == nil && value["schema"] == schema {
			return b
		}
	}
	return nil
}

func bridgeProof(root string, proof, pending map[string]any, snap *quickPendingSnapshot, files *quickBridgeFiles) ([]any, error) {
	if !pendingExact(proof, "schema", "tool", "go_version", "compiled_rubric_sha256", "compiled_authority_sha256", "source_inputs", "sdk_image", "build_flags", "target", "inventory_sha256", "module_files", "packages", "external_modules", "external_inputs", "module_verification", "source_frame_sha256") || proof["schema"] != "cat-quick-native-build-proof-1" || proof["go_version"] != "go1.27.3" || !same(proof["tool"], pending["tool"]) || proof["inventory_sha256"] != digest(snap.manifest) || proof["compiled_rubric_sha256"] != contentbuild.RubricSHA256 || proof["compiled_authority_sha256"] != InstalledAuthoritiesSHA256 || !same(proof["build_flags"], []string{"-trimpath", "-mod=readonly", "-buildvcs=false", "-p=4"}) || !same(proof["target"], map[string]any{"goos": "linux", "goarch": "amd64", "cgo_enabled": false}) || !same(proof["module_verification"], map[string]any{"before": "all modules verified", "after": "all modules verified"}) || !authorityDigest(proof["source_frame_sha256"]) || !strings.HasPrefix(text(proof["sdk_image"]), "sha256:") || !authorityDigest(strings.TrimPrefix(text(proof["sdk_image"]), "sha256:")) || !arrayShape(proof["source_inputs"], 1, 20000) {
		return nil, fmt.Errorf("quick bridge Root-pinned native build proof/current bindings differ")
	}
	previous := ""
	for _, v := range rows(proof["source_inputs"]) {
		r := object(v)
		relative := text(r["path"])
		if relative <= previous || filepath.IsAbs(relative) || filepath.ToSlash(filepath.Clean(relative)) != relative || strings.HasPrefix(relative, "../") {
			return nil, fmt.Errorf("quick bridge build source membership/path")
		}
		previous = relative
		ref := object(clone(r))
		ref["path"] = filepath.Join(root, filepath.FromSlash(relative))
		if _, err := files.read(ref); err != nil {
			return nil, err
		}
	}
	// Completeness/external dependency bytes and command execution are Root's
	// pinned receipt evidence. This consumer does not infer them from a manifest.
	consumer := []any{}
	for _, name := range []string{"common.py", "critic_blind.py"} {
		relative := "scripts/miner/" + name
		b := snap.files[relative]
		if len(b) == 0 {
			return nil, fmt.Errorf("quick bridge current blind consumer absent")
		}
		consumer = append(consumer, map[string]any{"path": relative, "sha256": digestBytes(b), "bytes": len(b)})
	}
	return consumer, nil
}

func bridgeStockClosure(screen map[string]any) error {
	if screen["schema"] != "quick-pending-stock-screen-v1" || screen["mechanical_pass"] != true || screen["complete"] != true || !arrayShape(screen["unresolved_quick_history"], 0, 0) {
		return fmt.Errorf("quick bridge unresolved stock history; independent relevance closure is not implemented")
	}
	return nil
}
