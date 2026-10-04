package contentrails

import (
	"bytes"
	"context"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

var Rails = []string{"quick", "world", "extensions", "reserve"}

type CheckResult struct {
	Rail           string `json:"rail"`
	OK             bool   `json:"ok"`
	RebuiltSHA256  string `json:"rebuilt_sha256"`
	ArtifactSHA256 string `json:"artifact_sha256"`
	ExactBytes     bool   `json:"exact_bytes"`
	SemanticExact  bool   `json:"semantic_exact"`
	SourceSHA256   string `json:"native_source_sha256"`
}

func Candidate(root string, s *Source, rail string, historical bool) (map[string]any, error) {
	switch rail {
	case "quick":
		return quickCandidate(root, s, historical)
	case "world":
		return worldCandidate(root, s, historical)
	case "extensions":
		raw := object(s.Raw["extensions"])
		if raw == nil {
			return nil, fmt.Errorf("missing authored extension definitions")
		}
		out := clone(raw).(map[string]any)
		if !historical {
			out["native_source_version"] = s.Version
			out["native_source_sha256"] = s.SHA256
			bind, err := bindings(root)
			if err != nil {
				return nil, err
			}
			for name, file := range map[string]string{"kg": "kg_sample.json", "pack": "games_pack.json", "rubric": "rubric"} {
				object(object(out["bindings"])[name])["sha256"] = bind[file]
			}
		}
		return out, nil
	default:
		return nil, fmt.Errorf("candidate generation supports quick/world/extensions")
	}
}
func buildReviewed(root string, s *Source, rail string, candidate map[string]any, sha string, reviews []Review) (map[string]any, error) {
	switch rail {
	case "quick":
		return buildQuick(root, s, candidate, sha, reviews)
	case "world":
		return buildWorld(root, s, candidate, sha, reviews)
	case "extensions":
		return buildExtensions(root, s, candidate, sha, reviews)
	}
	return nil, fmt.Errorf("unknown review rail")
}
func BuildProposal(root string, s *Source, rail, candidatePath, factualPath, qualityPath string) (map[string]any, error) {
	candidate, err := Read(candidatePath)
	if err != nil {
		return nil, err
	}
	expected, err := Candidate(root, s, rail, false)
	if err != nil {
		return nil, err
	}
	raw, err := os.ReadFile(candidatePath)
	if err != nil {
		return nil, err
	}
	want, err := Render(expected)
	if err != nil {
		return nil, err
	}
	if !same(candidate, expected) || !bytes.Equal(raw, want) {
		return nil, fmt.Errorf("candidate differs from native authored source/version/current bindings")
	}
	sha := digestBytes(raw)
	reviews, err := readReviews(root, rail, sha, candidate, []string{factualPath, qualityPath})
	if err != nil {
		return nil, err
	}
	before, err := bindings(root)
	if err != nil {
		return nil, err
	}
	out, err := buildReviewed(root, s, rail, candidate, sha, reviews)
	if err != nil {
		return nil, err
	}
	after, err := bindings(root)
	if err != nil {
		return nil, err
	}
	if !same(before, after) {
		return nil, fmt.Errorf("sources changed during review construction")
	}
	for i, path := range []string{factualPath, qualityPath} {
		b, err := os.ReadFile(path)
		if err != nil || digestBytes(b) != reviews[i].SHA256 {
			return nil, fmt.Errorf("review changed during construction")
		}
	}
	return out, nil
}
func baseline(root string, s *Source, rail string) (map[string]any, error) {
	if s.SHA256 != AuthoredSHA256 || s.Version != 1 {
		return nil, fmt.Errorf("baseline check requires pinned native source v1")
	}
	if rail == "reserve" {
		return buildReserve(root, s)
	}
	candidate, err := Candidate(root, s, rail, true)
	if err != nil {
		return nil, err
	}
	expected, err := archive(root, s, rail+"_candidate")
	if err != nil {
		return nil, err
	}
	raw, err := Render(candidate)
	if err != nil {
		return nil, err
	}
	sha := text(object(object(s.Raw["archives"])[rail+"_candidate"])["sha256"])
	if !same(candidate, expected) || digestBytes(raw) != sha {
		return nil, fmt.Errorf("native %s authored reconstruction differs from independent archive", rail)
	}
	paths, err := baselineReviewPaths(root, s, rail)
	if err != nil {
		return nil, err
	}
	reviews, err := readReviews(root, rail, sha, candidate, paths)
	if err != nil {
		return nil, err
	}
	return buildReviewed(root, s, rail, candidate, sha, reviews)
}
func Check(root string, s *Source, rail string) (CheckResult, error) {
	result := CheckResult{Rail: rail, SourceSHA256: s.SHA256}
	rebuilt, err := baseline(root, s, rail)
	if err != nil {
		return result, err
	}
	path, err := ArtifactPath(root, rail)
	if err != nil {
		return result, err
	}
	artifact, err := Read(path)
	if err != nil {
		return result, err
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return result, err
	}
	var output []byte
	if rail == "reserve" {
		output, err = renderReserve(rebuilt)
	} else {
		output, err = Render(rebuilt)
	}
	if err != nil {
		return result, err
	}
	result.SemanticExact = same(rebuilt, artifact)
	result.ExactBytes = bytes.Equal(output, raw)
	result.RebuiltSHA256 = digestBytes(output)
	result.ArtifactSHA256 = digestBytes(raw)
	if !result.SemanticExact {
		return result, fmt.Errorf("native %s rebuild differs from approved fixture at %s", rail, firstDifference(clone(rebuilt), clone(artifact), "root"))
	}
	if !result.ExactBytes {
		return result, fmt.Errorf("native %s baseline byte encoding changed", rail)
	}
	if rail == "reserve" {
		copy, err := os.ReadFile(filepath.Join(root, "tests/fixtures/release_reserve_v1.json"))
		if err != nil || !bytes.Equal(copy, raw) {
			return result, fmt.Errorf("reserve mirror drift")
		}
	}
	result.OK = true
	return result, nil
}
func CheckAll(root string, s *Source) ([]CheckResult, error) {
	out := []CheckResult{}
	for _, rail := range Rails {
		result, err := Check(root, s, rail)
		out = append(out, result)
		if err != nil {
			return out, err
		}
	}
	return out, nil
}

func RuntimeHashes(root string) ([]any, error) {
	var err error
	root, err = filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	paths, err := runtimePaths(root)
	if err != nil {
		return nil, err
	}
	out := []any{}
	for _, path := range paths {
		raw, err := os.ReadFile(path)
		if err != nil {
			return nil, err
		}
		relative, err := filepath.Rel(root, path)
		if err != nil {
			return nil, err
		}
		out = append(out, map[string]any{"path": filepath.ToSlash(relative), "sha256": digestBytes(raw)})
	}
	return out, nil
}
func Audit(ctx context.Context, root, rail string, raw map[string]any) (map[string]any, error) {
	beforeRuntime, err := RuntimeHashes(root)
	if err != nil {
		return nil, err
	}
	beforeSources, err := bindings(root)
	if err != nil {
		return nil, err
	}
	var out map[string]any
	switch rail {
	case "quick":
		out, err = auditQuick(ctx, root, raw)
	case "world":
		out, err = auditWorld(root, raw)
	case "extensions":
		out, err = auditExtensions(root, raw)
	case "reserve":
		s, e := LoadSource("")
		if e != nil {
			return nil, e
		}
		expected, e := buildReserve(root, s)
		if e != nil || !same(raw, expected) {
			return nil, fmt.Errorf("finite reserve independent audit differs")
		}
		out = map[string]any{"kind": "v1-release-reserve-native-audit-v1", "verdict": "accept", "pack": 20, "quick": 3, "archived_records_preserved": true}
	default:
		return nil, fmt.Errorf("unknown audit rail")
	}
	if err != nil {
		return nil, err
	}
	b, err := Render(raw)
	if err != nil {
		return nil, err
	}
	hashes, err := RuntimeHashes(root)
	if err != nil {
		return nil, err
	}
	bind, err := bindings(root)
	if err != nil {
		return nil, err
	}
	if !same(hashes, beforeRuntime) || !same(bind, beforeSources) {
		return nil, fmt.Errorf("source/runtime changed during live audit")
	}
	out["catalog_sha256"] = digestBytes(b)
	out["runtime_sources"] = hashes
	out["source_bindings"] = bind
	out["native_audit_version"] = 1
	return out, nil
}
func FinalKind(rail string) string {
	switch rail {
	case "quick":
		return "quick-content-final-v1"
	case "world":
		return "alchimie-discovery-world-final-v1"
	case "extensions":
		return "alchimie-recipe-extension-final-review-v1"
	}
	return ""
}
func ConfirmFinal(root, rail string, catalog map[string]any, proposalPath, auditPath, factualPath, qualityPath, expectedPin string) error {
	if rail == "reserve" {
		return fmt.Errorf("finite reserve writes use reviewed archival rebuild only")
	}
	proposal, err := os.ReadFile(proposalPath)
	if err != nil {
		return err
	}
	wanted, err := Render(catalog)
	if err != nil {
		return err
	}
	sha := digestBytes(wanted)
	if !bytes.Equal(proposal, wanted) || expectedPin != sha {
		return fmt.Errorf("saved proposal or explicit reviewed artifact pin differs")
	}
	audit, err := Read(auditPath)
	if err != nil {
		return err
	}
	auditBytes, err := os.ReadFile(auditPath)
	if err != nil {
		return err
	}
	hashes, err := RuntimeHashes(root)
	if err != nil {
		return err
	}
	bindingsNow, err := bindings(root)
	if err != nil {
		return err
	}
	kind := map[string]string{"quick": "quick-content-live-audit-v1", "world": "alchimie-discovery-world-audit-v1", "extensions": "alchimie-recipe-extension-native-audit-v1"}[rail]
	accepted := audit["verdict"] == "accept"
	if rail == "quick" {
		accepted = audit["passed"] == true && (audit["verdict"] == nil || audit["verdict"] == "accept")
	}
	if audit["kind"] != kind || !accepted || audit["native_audit_version"] == nil || integer(audit["native_audit_version"]) != 1 || audit["catalog_sha256"] != sha || audit["candidate_sha256"] != catalog["candidate_sha256"] || !same(audit["runtime_sources"], hashes) || !same(audit["source_bindings"], bindingsNow) {
		return fmt.Errorf("final live audit incomplete/stale/unaccepted")
	}
	field := "reviews"
	if rail == "extensions" {
		field = "semantic_reviews"
	}
	initial := map[string]string{}
	for _, v := range rows(catalog[field]) {
		r := object(v)
		initial[text(r["role"])] = text(r["reviewer"])
	}
	roles := []string{"factual", "quality"}
	g, err := sourceGraph(root)
	if err != nil {
		return err
	}
	for i, path := range []string{factualPath, qualityPath} {
		r, err := Read(path)
		if err != nil {
			return err
		}
		role := roles[i]
		auditField := "audit_sha256"
		if rail == "extensions" {
			auditField = "live_audit_sha256"
		}
		if r["kind"] != FinalKind(rail) || r["role"] != role || r["reviewer"] != initial[role] || r["catalog_sha256"] != sha || r[auditField] != digestBytes(auditBytes) || r["verdict"] != "accept" || strings.TrimSpace(text(r["rationale"])) == "" {
			return fmt.Errorf("final reviewer/artifact/audit acceptance differs")
		}
	}
	if g.Casefold(initial["factual"]) == g.Casefold(initial["quality"]) {
		return fmt.Errorf("final reviewers not independent")
	}
	return nil
}

// WriteOutputs is a bounded two-file transaction. All snapshots are captured
// before the first write, and restored even when the second replacement fails.
func WriteOutputs(paths []string, data []byte) error {
	if len(paths) < 1 || len(paths) > 2 || len(data) > MaxBytes {
		return fmt.Errorf("output transaction bounds")
	}
	changes := map[string][]byte{}
	for _, path := range paths {
		absolute, err := filepath.Abs(path)
		if err != nil || changes[absolute] != nil {
			return fmt.Errorf("duplicate or invalid output")
		}
		changes[absolute] = data
	}
	root := filepath.Dir(paths[0])
	return contentops.Transaction(root, changes, func() error {
		for path, expected := range changes {
			actual, err := os.ReadFile(path)
			if err != nil || !bytes.Equal(actual, expected) {
				return fmt.Errorf("output byte verification failed")
			}
		}
		return nil
	})
}
func atomic(path string, data []byte) error {
	f, err := os.CreateTemp(filepath.Dir(path), ".native-content-rail-*")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	if err = f.Chmod(0644); err == nil {
		_, err = f.Write(data)
	}
	if err == nil {
		err = f.Sync()
	}
	closeErr := f.Close()
	if err != nil {
		return err
	}
	if closeErr != nil {
		return closeErr
	}
	return os.Rename(name, path)
}
func ProtectedOutput(root, target string, inputs ...string) error {
	path, err := filepath.Abs(target)
	if err != nil || target == "" {
		return fmt.Errorf("explicit output required")
	}
	for _, name := range append(append([]string{}, inputs...), filepath.Join(root, "go-backend/internal/contentrails/sources/authored-v1.json")) {
		absolute, _ := filepath.Abs(name)
		if path == absolute {
			return fmt.Errorf("output would overwrite a protected author/review input")
		}
	}
	for _, relative := range []string{"cat_de_roman_esti/fixtures", "tests/fixtures", "go-backend/internal/contentrails/sources"} {
		dir, _ := filepath.Abs(filepath.Join(root, relative))
		if path == dir || strings.HasPrefix(path, dir+string(filepath.Separator)) {
			return fmt.Errorf("proposal/audit output cannot overwrite fixture or authoring source")
		}
	}
	return nil
}
func OutputBytes(rail string, value map[string]any) ([]byte, error) {
	if rail == "reserve" {
		return renderReserve(value)
	}
	return Render(value)
}
func SortedRails() []string { out := append([]string{}, Rails...); sort.Strings(out); return out }

func firstDifference(a, b any, path string) string {
	if same(a, b) {
		return ""
	}
	if am := object(a); am != nil {
		bm := object(b)
		for _, k := range sortedKeys(am) {
			if d := firstDifference(am[k], bm[k], path+"."+k); d != "" {
				return d
			}
		}
		for _, k := range sortedKeys(bm) {
			if _, ok := am[k]; !ok {
				return path + "." + k
			}
		}
	}
	if aa, ok := a.([]any); ok {
		bb, ok := b.([]any)
		if !ok || len(aa) != len(bb) {
			return path + ".length"
		}
		for i := range aa {
			if d := firstDifference(aa[i], bb[i], fmt.Sprintf("%s[%d]", path, i)); d != "" {
				return d
			}
		}
	}
	return path
}
func Rebuild(root string, s *Source, rail string) (map[string]any, error) {
	return baseline(root, s, rail)
}

func runtimePaths(root string) ([]string, error) {
	paths := []string{}
	for _, dir := range []string{"go-backend", "shared-go/authcore"} {
		err := filepath.WalkDir(filepath.Join(root, dir), func(path string, d os.DirEntry, err error) error {
			if err != nil {
				return err
			}
			if d.IsDir() {
				if d.Name() == "testdata" || d.Name() == "node_modules" || strings.HasPrefix(d.Name(), ".") {
					return filepath.SkipDir
				}
				return nil
			}
			name := d.Name()
			if strings.HasSuffix(name, "_test.go") {
				return nil
			}
			if strings.HasSuffix(name, ".go") || name == "go.mod" || name == "go.sum" || name == "rules_unicode15.json" || name == "provenance.json" || name == "rules_provenance.json" || name == "bundled.json" || strings.Contains(filepath.ToSlash(path), "/contentrails/sources/") && strings.HasSuffix(name, ".json") {
				absolute, err := filepath.Abs(path)
				if err != nil {
					return err
				}
				paths = append(paths, absolute)
			}
			return nil
		})
		if err != nil {
			return nil, err
		}
	}
	sort.Strings(paths)
	return paths, nil
}
func inputReadPaths(root string, s *Source, inputs ...string) ([]string, error) {
	out, err := runtimePaths(root)
	if err != nil {
		return nil, err
	}
	for _, name := range contentbuild.SourceNames {
		out = append(out, filepath.Join(root, "cat_de_roman_esti/fixtures", name))
	}
	out = append(out, filepath.Join(root, "docs/CRITIQUE_RUBRIC.md"))
	for _, v := range object(s.Raw["archives"]) {
		out = append(out, filepath.Join(root, text(object(v)["path"])))
	}
	for _, name := range []string{"kg_sample.json", "games_pack.json", "release_reserve_v1.json"} {
		out = append(out, filepath.Join(root, "tests/fixtures", name))
	}
	out = append(out, inputs...)
	seen := map[string]bool{}
	unique := []string{}
	for _, path := range out {
		if path == "" {
			continue
		}
		absolute, err := filepath.Abs(path)
		if err != nil {
			return nil, err
		}
		if !seen[absolute] {
			seen[absolute] = true
			unique = append(unique, absolute)
		}
	}
	sort.Strings(unique)
	return unique, nil
}

// InstallProposal snapshots the complete input graph BEFORE building, then the
// shared operator lock checks it before writes and after the post-write gate.
func InstallProposal(root string, s *Source, rail, candidate, factual, quality, proposal, audit, finalFactual, finalQuality, expectedPin, sourcePath string) error {
	root, err := filepath.Abs(root)
	if err != nil {
		return err
	}
	if err = validateLoadedSource(root, s, sourcePath); err != nil {
		return err
	}
	target, err := ArtifactPath(root, rail)
	if err != nil {
		return err
	}
	inputs, err := inputReadPaths(root, s, candidate, factual, quality, proposal, audit, finalFactual, finalQuality, sourcePath, target)
	if err != nil {
		return err
	}
	readset, err := contentops.CaptureReadSet(inputs)
	if err != nil {
		return err
	}
	if err = validateLoadedSource(root, s, sourcePath); err != nil {
		return err
	}
	value, err := BuildProposal(root, s, rail, candidate, factual, quality)
	if err != nil {
		return err
	}
	if err = ConfirmFinal(root, rail, value, proposal, audit, finalFactual, finalQuality, expectedPin); err != nil {
		return err
	}
	blob, err := OutputBytes(rail, value)
	if err != nil {
		return err
	}
	changes := map[string][]byte{target: blob}
	return contentops.GuardedTransaction(root, changes, readset, func() error {
		if err = validateLoadedSource(root, s, sourcePath); err != nil {
			return err
		}
		signed, err := Read(audit)
		if err != nil {
			return err
		}
		manifest, err := RuntimeHashes(root)
		if err != nil {
			return err
		}
		if !same(signed["runtime_sources"], manifest) {
			return fmt.Errorf("runtime inventory changed before/during install")
		}
		if err := validateInstalled(root, rail, value, expectedPin); err != nil {
			return err
		}
		actual, err := Read(target)
		if err != nil || !same(actual, value) {
			return fmt.Errorf("installed artifact differs from reviewed proposal")
		}
		return nil
	})
}
func InstallReserve(root string, s *Source, expectedPin string) error {
	root, err := filepath.Abs(root)
	if err != nil {
		return err
	}
	target, err := ArtifactPath(root, "reserve")
	if err != nil {
		return err
	}
	mirror := filepath.Join(root, "tests/fixtures/release_reserve_v1.json")
	inputs, err := inputReadPaths(root, s, target, mirror)
	if err != nil {
		return err
	}
	readset, err := contentops.CaptureReadSet(inputs)
	if err != nil {
		return err
	}
	value, err := buildReserve(root, s)
	if err != nil {
		return err
	}
	blob, err := renderReserve(value)
	if err != nil {
		return err
	}
	if digestBytes(blob) != expectedPin || expectedPin != "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7" {
		return fmt.Errorf("finite reserve explicit reviewed pin differs")
	}
	return contentops.GuardedTransaction(root, map[string][]byte{target: blob, mirror: blob}, readset, func() error {
		if err = validateLoadedSource(root, s, ""); err != nil {
			return err
		}
		if err := contentbuild.ValidateSources(root); err != nil {
			return err
		}
		for _, path := range []string{target, mirror} {
			actual, err := os.ReadFile(path)
			if err != nil || !bytes.Equal(actual, blob) {
				return fmt.Errorf("reserve byte mirror drift")
			}
		}
		return nil
	})
}

// Staging an explicitly signed artifact does not activate it: the exporter and
// serving binary continue to enforce their reviewed source pins until the
// separate pin/code decision and rebuild. Other source files are immutable in
// the guarded readset throughout this transaction.
func validateInstalled(root, rail string, value map[string]any, expectedSHA string) error {
	path, err := ArtifactPath(root, rail)
	if err != nil {
		return err
	}
	blob, err := os.ReadFile(path)
	if err != nil || digestBytes(blob) != expectedSHA {
		return fmt.Errorf("installed signed artifact SHA differs")
	}
	g, err := sourceGraph(root)
	if err != nil {
		return err
	}
	switch rail {
	case "quick":
		base, err := fixture(root, "derived_catalog_v38.json")
		if err != nil {
			return err
		}
		bind, err := bindings(root)
		if err != nil {
			return err
		}
		return contentbuild.ValidateQuickCatalog(value, base, g, bind)
	case "world":
		_, err := contentbuild.ValidateDiscoveryWorld(value, g)
		return err
	case "extensions":
		_, err := auditExtensions(root, value)
		return err
	}
	return fmt.Errorf("unknown installed review rail")
}

func validateLoadedSource(root string, s *Source, path string) error {
	if path == "" {
		path = filepath.Join(root, "go-backend/internal/contentrails/sources/authored-v1.json")
	}
	raw, err := os.ReadFile(path)
	if err != nil || digestBytes(raw) != s.SHA256 {
		return fmt.Errorf("loaded native authoring source snapshot changed")
	}
	current, err := LoadSource(path)
	if err != nil || current.Version != s.Version || !same(current.Raw, s.Raw) {
		return fmt.Errorf("loaded source object/version changed")
	}
	return nil
}
