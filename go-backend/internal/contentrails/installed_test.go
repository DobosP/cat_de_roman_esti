package contentrails

import (
	"bytes"
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

type installedFixture struct {
	root     string
	selected *Source
	source   *Source
	manifest map[string]any
	entry    map[string]any
}

func installedFixtureForTest(t *testing.T) installedFixture {
	t.Helper()
	root, selected := cloneRoot(t)
	dir := filepath.Join(root, "docs/reviews/synthetic-installed-v2")
	s := sourceV2(t, dir)
	candidate, err := Candidate(root, s, "quick", false)
	if err != nil {
		t.Fatal(err)
	}
	candidatePath := filepath.Join(dir, "candidate.json")
	writeJSONTest(t, candidatePath, candidate)
	blob, _ := Render(candidate)
	reviews := syntheticReviews(t, dir, "quick", candidate, digestBytes(blob))
	proposal, err := BuildProposal(root, s, "quick", candidatePath, reviews[0], reviews[1])
	if err != nil {
		t.Fatal(err)
	}
	proposalPath := filepath.Join(dir, "proposal.json")
	writeJSONTest(t, proposalPath, proposal)
	// The separate installation tests exercise the guarded writer. This fixture
	// represents its installed result before publication authority is checked.
	artifactPath, _ := ArtifactPath(root, "quick")
	writeJSONTest(t, artifactPath, proposal)
	audit, err := Audit(context.Background(), root, "quick", proposal)
	if err != nil {
		t.Fatal(err)
	}
	auditPath := filepath.Join(dir, "published-audit.json")
	writeJSONTest(t, auditPath, audit)
	proposalBytes, _ := Render(proposal)
	auditBytes, _ := Render(audit)
	artifactSHA := digestBytes(proposalBytes)
	finals := []string{}
	for _, role := range []string{"factual", "quality"} {
		path := filepath.Join(dir, "published-final-"+role+".json")
		writeJSONTest(t, path, map[string]any{"kind": FinalKind("quick"), "role": role, "reviewer": "synthetic-" + role, "catalog_sha256": artifactSHA, "audit_sha256": digestBytes(auditBytes), "verdict": "accept", "rationale": "Synthetic fixture-only final published-authority judgment."})
		finals = append(finals, path)
	}
	entry, err := BuildInstalledAuthorityEntry(root, s, "quick", candidatePath, reviews[0], reviews[1], proposalPath, auditPath, finals[0], finals[1], artifactSHA)
	if err != nil {
		t.Fatal(err)
	}
	manifest := map[string]any{"schema": "native-content-installed-authorities-v1", "version": 1, "source_chain": []any{map[string]any{"path": "docs/reviews/synthetic-installed-v2/source-v2.json", "sha256": s.SHA256, "version": 2, "parent_source_sha256": AuthoredSHA256}}, "rails": map[string]any{"quick": entry}}
	return installedFixture{root, selected, s, manifest, entry}
}

func authorityForTest(t *testing.T, raw map[string]any) *installedAuthorities {
	t.Helper()
	blob, err := Render(raw)
	if err != nil {
		t.Fatal(err)
	}
	a, err := parseInstalledAuthorities(blob, digestBytes(blob))
	if err != nil {
		t.Fatal(err)
	}
	return a
}

func TestInstalledAuthorityEmptyKeepsHistoricalBaselineAndPinIsSeparate(t *testing.T) {
	a, err := loadInstalledAuthorities(rootPath(t))
	if err != nil {
		t.Fatal(err)
	}
	empty, _ := Render(map[string]any{"schema": "native-content-installed-authorities-v1", "version": 1, "source_chain": []any{}, "rails": map[string]any{}})
	a, err = parseInstalledAuthorities(empty, digestBytes(empty))
	if err != nil {
		t.Fatal(err)
	}
	if _, adopted, err := a.rebuild(rootPath(t), sourceForTest(t), "quick"); adopted || err != nil {
		t.Fatal("empty authority changed the historical baseline")
	}
	paths, err := runtimePaths(rootPath(t))
	if err != nil {
		t.Fatal(err)
	}
	seen := map[string]bool{}
	for _, path := range paths {
		relative, _ := filepath.Rel(rootPath(t), path)
		seen[filepath.ToSlash(relative)] = true
	}
	if seen[installedManifestPath] || seen[installedPinPath] {
		t.Fatal("authority metadata circularly entered its own runtime audit")
	}
	for _, required := range []string{"go-backend/internal/contentrails/sources/authored-v1.json", "go-backend/internal/contentrails/installed.go", "go-backend/internal/contentbuild/rules_unicode15.json", "go-backend/internal/content/bundled.json", "go-backend/internal/content/digest.go"} {
		if !seen[required] {
			t.Fatal("previously audited runtime or new authority validation escaped inventory", required)
		}
	}
	readset, err := inputReadPaths(rootPath(t), sourceForTest(t))
	if err != nil {
		t.Fatal(err)
	}
	for _, relative := range []string{installedManifestPath, installedPinPath} {
		found := false
		for _, path := range readset {
			if path == filepath.Join(rootPath(t), relative) {
				found = true
			}
		}
		if !found {
			t.Fatal("separately pinned metadata escaped transaction readset", relative)
		}
	}
}

func TestInstalledAuthorityPinExclusionPermitsOnlyDigestMetadata(t *testing.T) {
	expected, err := PinBytesForInstalledAuthorities(InstalledAuthoritiesSHA256)
	if err != nil || validateInstalledPinBytes(expected, expected, InstalledAuthoritiesSHA256) != nil {
		t.Fatal("metadata-only pin template refused", err)
	}
	for _, injected := range [][]byte{
		append(append([]byte{}, expected...), []byte("func init() {}\n")...),
		append(append([]byte{}, expected...), []byte("var extraAuthority = true\n")...),
		bytes.Replace(expected, []byte("package contentrails\n"), []byte("package contentrails\n\nimport \"os\"\n"), 1),
		append(append([]byte{}, expected...), []byte("// drift\n")...),
	} {
		// Equal source and conceptual newly compiled bytes with an unchanged pin
		// must still fail: this file may never hide new code from RuntimeHashes.
		if err := validateInstalledPinBytes(injected, injected, InstalledAuthoritiesSHA256); err == nil {
			t.Fatal("excluded metadata pin source admitted code or template drift")
		}
	}
}

func TestInstalledAuthorityProtectedDocumentReaderRefusals(t *testing.T) {
	root := t.TempDir()
	dir := filepath.Join(root, "docs/reviews/reader")
	if err := os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, "document.json")
	if err := os.WriteFile(path, []byte("{}\n"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := regularAuthorityBytes(root, "docs/reviews/reader/document.json"); err != nil {
		t.Fatal("regular protected document refused", err)
	}
	link := filepath.Join(root, "docs/reviews/linked-parent")
	if err := os.Symlink(dir, link); err != nil {
		t.Fatal(err)
	}
	large := filepath.Join(dir, "large.json")
	f, err := os.Create(large)
	if err != nil {
		t.Fatal(err)
	}
	if err = f.Truncate(MaxBytes + 1); err != nil {
		t.Fatal(err)
	}
	if err = f.Close(); err != nil {
		t.Fatal(err)
	}
	for _, relative := range []string{"docs/reviews/linked-parent/document.json", "docs/reviews/reader", "docs/reviews/reader/large.json", "docs/reviews/../reader/document.json", `docs\reviews\reader\document.json`, "/tmp/document.json"} {
		if _, err := regularAuthorityBytes(root, relative); err == nil {
			t.Fatal("unsafe/nonregular/oversized protected document accepted", relative)
		}
	}
}

func TestInstalledAuthorityDraftOutputCannotOverwriteAuthorityOrRuntime(t *testing.T) {
	root := rootPath(t)
	for _, relative := range []string{installedPinPath, installedManifestPath, "go-backend/internal/contentrails/installed.go", "go-backend/internal/content/digest.go", "go-backend/go.mod"} {
		if err := ProtectedOutput(root, filepath.Join(root, relative)); err == nil {
			t.Fatal("draft output could overwrite protected authority or runtime input", relative)
		}
	}
	if err := ProtectedOutput(root, filepath.Join(root, "docs/reviews/synthetic-new-authority-entry.json")); err != nil {
		t.Fatal("fresh draft metadata output refused", err)
	}
}

func TestReviewedInstalledVersionTwoReconstructsWithoutRelabelingV1(t *testing.T) {
	f := installedFixtureForTest(t)
	a := authorityForTest(t, f.manifest)
	rebuilt, adopted, err := a.rebuild(f.root, f.selected, "quick")
	if err != nil || !adopted {
		t.Fatal("complete independently reviewed installed authority refused", err)
	}
	blob, _ := Render(rebuilt)
	target, _ := ArtifactPath(f.root, "quick")
	actual, _ := os.ReadFile(target)
	if !bytes.Equal(blob, actual) {
		t.Fatal("installed authority did not reconstruct exact current bytes")
	}
	if _, err = baseline(f.root, f.source, "quick"); err == nil {
		t.Fatal("new authority silently weakened immutable V1 archive checks")
	}
	if _, adopted, err = a.rebuild(f.root, f.selected, "reserve"); err != nil || adopted {
		t.Fatal("quick adoption widened another rail")
	}
}

func TestInstalledAuthoritySchemaPinAndSequentialChainRefusals(t *testing.T) {
	f := installedFixtureForTest(t)
	mutations := []func(map[string]any){
		func(m map[string]any) { m["extra"] = true },
		func(m map[string]any) { m["rails"] = map[string]any{} },
		func(m map[string]any) { object(m["rails"])["reserve"] = f.entry },
		func(m map[string]any) { object(rows(m["source_chain"])[0])["version"] = 3 },
		func(m map[string]any) {
			object(rows(m["source_chain"])[0])["parent_source_sha256"] = strings.Repeat("0", 64)
		},
		func(m map[string]any) { object(rows(m["source_chain"])[0])["path"] = "docs/reviews/../source.json" },
		func(m map[string]any) {
			object(rows(m["source_chain"])[0])["sha256"] = strings.ToUpper(f.source.SHA256)
		},
		func(m map[string]any) { delete(object(object(m["rails"])["quick"]), "factual_review") },
		func(m map[string]any) {
			object(object(object(m["rails"])["quick"])["candidate"])["path"] = "/tmp/candidate.json"
		},
		func(m map[string]any) { object(object(object(m["rails"])["quick"])["audit"])["sha256"] = "not-a-sha" },
	}
	for i, mutate := range mutations {
		bad := clone(f.manifest).(map[string]any)
		mutate(bad)
		blob, _ := Render(bad)
		if _, err := parseInstalledAuthorities(blob, digestBytes(blob)); err == nil {
			t.Fatal("invalid current-authority manifest accepted", i)
		}
	}
	blob, _ := Render(f.manifest)
	if _, err := parseInstalledAuthorities(append(blob, ' '), digestBytes(blob)); err == nil {
		t.Fatal("manifest tampering accepted against old pin")
	}
	for _, relative := range []string{installedManifestPath, installedPinPath} {
		path := filepath.Join(f.root, relative)
		old, _ := os.ReadFile(path)
		if err := os.WriteFile(path, append(old, ' '), 0600); err != nil {
			t.Fatal(err)
		}
		if _, err := loadInstalledAuthorities(f.root); err == nil {
			t.Fatal("root authority metadata diverged from compiled authority", relative)
		}
		if err := os.WriteFile(path, old, 0600); err != nil {
			t.Fatal(err)
		}
	}
}

func TestInstalledAuthorityCannotBeGrantedByPinsWithoutCurrentReviews(t *testing.T) {
	f := installedFixtureForTest(t)
	for _, key := range installedDocumentKeys {
		t.Run("missing-"+key, func(t *testing.T) {
			m := clone(f.manifest).(map[string]any)
			d := object(object(object(m["rails"])["quick"])[key])
			d["path"] = "docs/reviews/synthetic-installed-v2/missing-" + key + ".json"
			a := authorityForTest(t, m)
			if _, _, err := a.rebuild(f.root, f.selected, "quick"); err == nil {
				t.Fatal("new artifact/source pins granted authority without exact review evidence")
			}
		})
	}
	for _, key := range []string{"factual_review", "quality_review", "audit", "final_factual_review", "final_quality_review"} {
		t.Run("rehash-tampered-"+key, func(t *testing.T) {
			m := clone(f.manifest).(map[string]any)
			d := object(object(object(m["rails"])["quick"])[key])
			path := filepath.Join(f.root, text(d["path"]))
			old, _ := os.ReadFile(path)
			defer os.WriteFile(path, old, 0600)
			raw, err := Read(path)
			if err != nil {
				t.Fatal(err)
			}
			switch key {
			case "quality_review":
				raw["reviewer"] = "synthetic-factual"
			case "factual_review":
				object(rows(raw["items"])[0])["verdict"] = "reject"
			case "audit":
				raw["source_bindings"] = map[string]any{}
			default:
				raw["verdict"] = "hold"
			}
			writeJSONTest(t, path, raw)
			blob, _ := os.ReadFile(path)
			d["sha256"] = digestBytes(blob)
			a := authorityForTest(t, m)
			if _, _, err = a.rebuild(f.root, f.selected, "quick"); err == nil {
				t.Fatal("rehashed authority metadata bypassed independent approval/current-audit checks")
			}
		})
	}
}

func TestInstalledAuthorityStaleSourcesRuntimeAndSymlinksRefuse(t *testing.T) {
	f := installedFixtureForTest(t)
	a := authorityForTest(t, f.manifest)
	for _, relative := range []string{"docs/reviews/synthetic-installed-v2/source-v2.json", "go-backend/internal/graph/service.go", "cat_de_roman_esti/fixtures/kg_sample.json"} {
		t.Run(relative, func(t *testing.T) {
			path := filepath.Join(f.root, relative)
			old, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			defer os.WriteFile(path, old, 0600)
			if err = os.WriteFile(path, append(old, '\n'), 0600); err != nil {
				t.Fatal(err)
			}
			if _, _, err = a.rebuild(f.root, f.selected, "quick"); err == nil {
				t.Fatal("stale source/runtime/audit accepted")
			}
		})
	}
	for _, key := range []string{"candidate", "factual_review", "audit"} {
		t.Run("symlink-"+key, func(t *testing.T) {
			m := clone(f.manifest).(map[string]any)
			d := object(object(object(m["rails"])["quick"])[key])
			target := filepath.Join(f.root, text(d["path"]))
			relative := "docs/reviews/synthetic-installed-v2/symlink-" + key + ".json"
			path := filepath.Join(f.root, relative)
			if err := os.Symlink(target, path); err != nil {
				t.Fatal(err)
			}
			d["path"] = relative
			a := authorityForTest(t, m)
			if _, _, err := a.rebuild(f.root, f.selected, "quick"); err == nil {
				t.Fatal("symlinked registered authority document accepted")
			}
		})
	}
}

func TestFutureInstalledParentChainRequiresExactSequentialReviewedPredecessor(t *testing.T) {
	f := installedFixtureForTest(t)
	v3 := clone(f.source.Raw).(map[string]any)
	v3["version"], v3["parent_source_sha256"] = 3, f.source.SHA256
	path := filepath.Join(f.root, "docs/reviews/synthetic-installed-v2/source-v3.json")
	writeJSONTest(t, path, v3)
	if _, err := LoadSource(path); err == nil {
		t.Fatal("unadopted version two became a reviewed parent through source pin alone")
	}
	blob, _ := os.ReadFile(path)
	m := clone(f.manifest).(map[string]any)
	m["source_chain"] = append(rows(m["source_chain"]), map[string]any{"path": "docs/reviews/synthetic-installed-v2/source-v3.json", "sha256": digestBytes(blob), "version": 3, "parent_source_sha256": f.source.SHA256})
	object(object(m["rails"])["quick"])["source_sha256"] = digestBytes(blob)
	a := authorityForTest(t, m)
	sources, err := a.sources(f.root)
	if err != nil || sources[digestBytes(blob)] == nil || !a.registeredParent(3, f.source.SHA256) || a.registeredParent(3, AuthoredSHA256) || a.registeredParent(4, f.source.SHA256) {
		t.Fatal("sequential exact parent chain not enforced", err)
	}
	if _, _, err = a.rebuild(f.root, f.selected, "quick"); err == nil {
		t.Fatal("valid parent metadata falsely approved unreviewed version-three candidate")
	}
}
