package contentrails

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
)

const quickPendingMaxBytes = 32 << 20
const quickPendingQualification = "Unapproved private pending projection only; no semantic, source-policy, content, installation or serving approval."

// The fixed source set includes every pack/quick reserve and historical novelty
// input, plus all miner code used to interpret the registry/compatibility index.
var quickPendingPolicyPaths = []string{
	"docs/CONTENT_LOOP.md", "docs/content-registry/registry.jsonl", "docs/content-registry/exclusions.json",
	"cat_de_roman_esti/fixtures/board_demotions_v43.json", "cat_de_roman_esti/fixtures/contexto_demotions_v44.json",
	"cat_de_roman_esti/fixtures/contexto_impact_reserve_v69.json", "cat_de_roman_esti/fixtures/conexiuni_rejection_tombstones.json",
	"cat_de_roman_esti/fixtures/lant_rejection_tombstones.json",
	"docs/adr/0052-derived-beginner-games.md", "docs/adr/0054-refine-derived-pilot-before-expansion.md",
	"docs/adr/0148-expand-all-game-content-with-independent-review.md", "docs/adr/0149-review-new-levels-and-keep-crafting-feedback-visible.md",
	"docs/adr/0189-behaviour-bound-installed-content-authorities.md", "docs/adr/0212-bounded-content-workflow-repair.md",
	"docs/adr/0226-content-loop-v4.md",
}

type quickPendingSnapshot struct {
	root     string
	source   *Source
	paths    []string
	files    map[string][]byte
	manifest map[string]any
	readset  contentops.ReadSet
}

func pendingRegular(path string, max int64) ([]byte, error) {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path {
		return nil, fmt.Errorf("pending input requires an absolute canonical path")
	}
	return contentbuild.ReadPendingInput(path, max)
}

func pendingRoot(root string) (string, error) {
	absolute, err := filepath.Abs(root)
	if err != nil {
		return "", err
	}
	physical, err := filepath.EvalSymlinks(absolute)
	if err != nil || absolute != physical {
		return "", fmt.Errorf("pending root must not traverse symlinks")
	}
	return absolute, nil
}

// pendingAuthoritySources reads the immutable compiled descriptor set through
// the strict no-symlink/nonblocking opener. Pending discovery must not call the
// legacy authority/path helpers before its own strong readset exists.
func pendingAuthoritySources(root string) (*installedAuthorities, map[string]*Source, error) {
	a, err := parseInstalledAuthorities(installedAuthorityBytes, InstalledAuthoritiesSHA256)
	if err != nil {
		return nil, nil, err
	}
	manifest, err := pendingRegular(filepath.Join(root, installedManifestPath), MaxBytes)
	if err != nil || digestBytes(manifest) != InstalledAuthoritiesSHA256 {
		return nil, nil, fmt.Errorf("pending root authority differs from compiled manifest")
	}
	pin, err := pendingRegular(filepath.Join(root, installedPinPath), MaxBytes)
	if err != nil || validateInstalledPinBytes(pin, installedPinBytes, InstalledAuthoritiesSHA256) != nil {
		return nil, nil, fmt.Errorf("pending root authority pin differs from compiled template")
	}
	sources := map[string]*Source{}
	for _, v := range rows(a.raw["source_chain"]) {
		e := object(v)
		b, err := pendingRegular(filepath.Join(root, text(e["path"])), MaxBytes)
		if err != nil {
			return nil, nil, err
		}
		if digestBytes(b) != e["sha256"] {
			return nil, nil, fmt.Errorf("pending registered source byte digest differs")
		}
		source, err := decodeSource(b, text(e["parent_source_sha256"]), integer(e["version"]))
		if err != nil {
			return nil, nil, err
		}
		for _, v := range object(source.Raw["archives"]) {
			descriptor := object(v)
			if !authorityDescriptor(descriptor) {
				return nil, nil, fmt.Errorf("pending source archive descriptor refused")
			}
			archive, err := pendingRegular(filepath.Join(root, text(descriptor["path"])), MaxBytes)
			if err != nil {
				return nil, nil, err
			}
			if digestBytes(archive) != descriptor["sha256"] {
				return nil, nil, fmt.Errorf("pending source archive byte digest differs")
			}
		}
		sources[source.SHA256] = source
	}
	return a, sources, nil
}

func pendingPaths(root string, selected *Source) ([]string, error) {
	paths, err := runtimePaths(root)
	if err != nil {
		return nil, err
	}
	a, sources, err := pendingAuthoritySources(root)
	if err != nil {
		return nil, err
	}
	if sources[selected.SHA256] == nil {
		return nil, fmt.Errorf("pending source is not in compiled registered chain")
	}
	for _, name := range contentbuild.SourceNames {
		paths = append(paths, filepath.Join(root, "cat_de_roman_esti/fixtures", name))
	}
	paths = append(paths, filepath.Join(root, "docs/CRITIQUE_RUBRIC.md"), filepath.Join(root, installedManifestPath), filepath.Join(root, installedPinPath))
	for _, v := range rows(a.raw["source_chain"]) {
		paths = append(paths, filepath.Join(root, text(object(v)["path"])))
	}
	for _, source := range sources {
		for _, v := range object(source.Raw["archives"]) {
			paths = append(paths, filepath.Join(root, text(object(v)["path"])))
		}
	}
	for _, v := range object(a.raw["rails"]) {
		for _, key := range installedDocumentKeys {
			paths = append(paths, filepath.Join(root, text(object(object(v)[key])["path"])))
		}
	}
	for _, name := range []string{"kg_sample.json", "games_pack.json", "release_reserve_v1.json"} {
		paths = append(paths, filepath.Join(root, "tests/fixtures", name))
	}
	for _, relative := range quickPendingPolicyPaths {
		paths = append(paths, filepath.Join(root, filepath.FromSlash(relative)))
	}
	entries, err := os.ReadDir(filepath.Join(root, "scripts/miner"))
	if err != nil {
		return nil, err
	}
	for _, entry := range entries {
		if strings.HasSuffix(entry.Name(), ".py") {
			paths = append(paths, filepath.Join(root, "scripts/miner", entry.Name()))
		}
	}
	seen, unique := map[string]bool{}, []string{}
	for _, path := range paths {
		if !seen[path] {
			seen[path] = true
			unique = append(unique, path)
		}
	}
	sort.Strings(unique)
	return unique, nil
}

func pendingCurrentSource(root string) (*Source, error) {
	a, sources, err := pendingAuthoritySources(root)
	if err != nil {
		return nil, err
	}
	s := sources[text(object(object(a.raw["rails"])["quick"])["source_sha256"])]
	if s == nil {
		return nil, fmt.Errorf("quick pending requires a registered current quick authority")
	}
	return s, nil
}

func captureQuickPending(root string, extra []string) (*quickPendingSnapshot, error) {
	root, err := pendingRoot(root)
	if err != nil {
		return nil, err
	}
	s, err := pendingCurrentSource(root)
	if err != nil {
		return nil, err
	}
	paths, err := pendingPaths(root, s)
	if err != nil {
		return nil, err
	}
	readset, err := contentops.CaptureRegularReadSet(append(append([]string{}, paths...), extra...))
	if err != nil {
		return nil, err
	}
	files, members := map[string][]byte{}, []any{}
	for _, path := range paths {
		b, err := pendingRegular(path, quickPendingMaxBytes)
		if err != nil {
			return nil, err
		}
		relative, err := filepath.Rel(root, path)
		if err != nil || strings.HasPrefix(relative, "..") {
			return nil, fmt.Errorf("pending inventory escaped repository")
		}
		relative = filepath.ToSlash(relative)
		files[relative] = b
		members = append(members, map[string]any{"path": relative, "sha256": digestBytes(b), "bytes": len(b)})
	}
	// Re-derive the source from the frozen bytes; an earlier pathname read is
	// never the material used for pending construction.
	a, err := parseInstalledAuthorities(files[installedManifestPath], InstalledAuthoritiesSHA256)
	if err != nil || validateInstalledPinBytes(files[installedPinPath], installedPinBytes, InstalledAuthoritiesSHA256) != nil {
		return nil, fmt.Errorf("frozen pending authority differs")
	}
	for _, v := range rows(a.raw["source_chain"]) {
		e := object(v)
		b := files[text(e["path"])]
		if digestBytes(b) != e["sha256"] {
			return nil, fmt.Errorf("frozen pending source chain differs")
		}
		decoded, e2 := decodeSource(b, text(e["parent_source_sha256"]), integer(e["version"]))
		if e2 != nil {
			return nil, e2
		}
		for _, v := range object(decoded.Raw["archives"]) {
			d := object(v)
			if !authorityDescriptor(d) || digestBytes(files[text(d["path"])]) != d["sha256"] {
				return nil, fmt.Errorf("frozen pending source archive differs")
			}
		}
		if decoded.SHA256 == s.SHA256 {
			s = decoded
		}
	}
	for _, rail := range []string{"quick", "world", "extensions"} {
		e := object(object(a.raw["rails"])[rail])
		if e == nil {
			return nil, fmt.Errorf("pending requires complete current rail declarations")
		}
		for _, key := range installedDocumentKeys {
			d := object(e[key])
			if digestBytes(files[text(d["path"])]) != d["sha256"] {
				return nil, fmt.Errorf("frozen pending reviewed document differs")
			}
		}
	}
	manifest := map[string]any{"schema": "quick-pending-inventory-v1", "baseline_source_sha256": s.SHA256, "baseline_source_version": s.Version, "members": members}
	return &quickPendingSnapshot{root, s, paths, files, manifest, readset}, nil
}

func (s *quickPendingSnapshot) unchanged() error {
	if err := s.readset.Verify(); err != nil {
		return err
	}
	paths, err := pendingPaths(s.root, s.source)
	if err != nil || !same(paths, s.paths) {
		return fmt.Errorf("pending inventory membership changed")
	}
	for relative, expected := range s.files {
		actual, err := pendingRegular(filepath.Join(s.root, filepath.FromSlash(relative)), quickPendingMaxBytes)
		if err != nil || digestBytes(actual) != digestBytes(expected) {
			return fmt.Errorf("pending inventory changed: %s", relative)
		}
	}
	return nil
}

// QuickPendingInventory emits a complete current byte/member inventory. It
// grants no approval and never accepts a caller-selected source or fixture.
func QuickPendingInventory(root string) (map[string]any, error) {
	s, err := captureQuickPending(root, nil)
	if err != nil {
		return nil, err
	}
	if err = s.unchanged(); err != nil {
		return nil, err
	}
	return s.manifest, nil
}

func (s *quickPendingSnapshot) object(relative string) (map[string]any, error) {
	b, ok := s.files[relative]
	if !ok {
		return nil, fmt.Errorf("missing frozen pending input: %s", relative)
	}
	return contentops.Decode(b)
}

func pendingTool() (map[string]any, error) {
	if runtime.Version() != "go1.27.3" {
		return nil, fmt.Errorf("pending preparation requires the owning Go 1.27.3 binary")
	}
	path, err := os.Executable()
	if err != nil {
		return nil, err
	}
	path, err = filepath.Abs(path)
	if err != nil {
		return nil, err
	}
	b, err := pendingRegular(path, 256<<20)
	if err != nil {
		return nil, err
	}
	return map[string]any{"path": path, "sha256": digestBytes(b), "bytes": len(b), "go_version": runtime.Version()}, nil
}

// quickArtifactBound authenticates the complete current fixture metadata as
// well as the authored payload/rating fields checked by ValidateQuickCatalog.
func (s *quickPendingSnapshot) quickArtifactBound() error {
	a, err := parseInstalledAuthorities(s.files[installedManifestPath], InstalledAuthoritiesSHA256)
	if err != nil {
		return err
	}
	entry := object(object(a.raw["rails"])["quick"])
	if entry == nil || contentbuild.TextSHA256(s.files["cat_de_roman_esti/fixtures/quick_games_v92.json"]) != entry["artifact_sha256"] {
		return fmt.Errorf("current quick fixture differs from installed artifact authority")
	}
	return nil
}
