package contentbuild

import (
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
)

const prospectiveLantCaptionSchema = "cat-prospective-lant-captions-1"

func readDirect(path string, max int64) ([]byte, error) {
	lstat, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if !lstat.Mode().IsRegular() {
		return nil, fmt.Errorf("source is not a direct regular file")
	}
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > max {
		return nil, fmt.Errorf("source exceeds %d byte bound or is not a regular file", max)
	}
	b, err := io.ReadAll(io.LimitReader(f, max+1))
	if err != nil {
		return nil, err
	}
	if int64(len(b)) > max {
		return nil, fmt.Errorf("source exceeds byte bound")
	}
	return b, nil
}

func boundObject(path string, max int64) (map[string]any, []byte, error) {
	b, err := readDirect(path, max)
	if err != nil {
		return nil, nil, err
	}
	m, err := decodeObject(b)
	return m, b, err
}

func binding(display string, data []byte) map[string]any {
	return map[string]any{"path": display, "sha256": SHA256(data), "bytes": len(data)}
}

func nativeSourceBindings(root string) ([]any, error) {
	pattern := filepath.Join(root, "go-backend", "internal", "contentbuild", "*.go")
	paths, err := filepath.Glob(pattern)
	if err != nil {
		return nil, err
	}
	paths = append(paths, filepath.Join(root, "go-backend", "cmd", "cat-content", "main.go"))
	sort.Strings(paths)
	out := make([]any, 0, len(paths))
	for _, path := range paths {
		rel, err := filepath.Rel(root, path)
		if err != nil {
			return nil, err
		}
		info, err := os.Lstat(path)
		if err != nil || !info.Mode().IsRegular() {
			return nil, fmt.Errorf("native source must be a regular file: %s", filepath.ToSlash(rel))
		}
		b, err := os.ReadFile(path)
		if err != nil {
			return nil, err
		}
		out = append(out, binding(filepath.ToSlash(rel), b))
	}
	return out, nil
}

// BuildProspectiveLantCaptions validates an explicit KG/pack pair and emits an
// unapproved preview artifact. It deliberately does not build serving content
// or consult/rewrite installed catalog, ranking, source or rail pins.
func BuildProspectiveLantCaptions(root, kgPath, packPath string) ([]byte, error) {
	if runtime.Version() != "go1.27.3" {
		return nil, fmt.Errorf("prospective preview requires go1.27.3, got %s", runtime.Version())
	}
	root, err := filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	kgPath, err = filepath.Abs(kgPath)
	if err != nil {
		return nil, err
	}
	packPath, err = filepath.Abs(packPath)
	if err != nil {
		return nil, err
	}
	kg, kgBytes, err := boundObject(kgPath, 16<<20)
	if err != nil {
		return nil, fmt.Errorf("kg: %w", err)
	}
	if errors := validateFixture(kg); len(errors) > 0 {
		return nil, fmt.Errorf("fixture invalid: %s", errorSummary(errors))
	}
	pack, packBytes, err := boundObject(packPath, 8<<20)
	if err != nil {
		return nil, fmt.Errorf("pack: %w", err)
	}
	c, err := parsedGraph(kg)
	if err != nil {
		return nil, err
	}
	g := graph.New(c)
	if errors := validatePack(pack, g); len(errors) > 0 {
		return nil, fmt.Errorf("pack invalid: %s", errorSummary(errors))
	}
	rubricPath := filepath.Join(root, "docs", "CRITIQUE_RUBRIC.md")
	rubricBytes, err := readDirect(rubricPath, 1<<20)
	if err != nil {
		return nil, fmt.Errorf("required reviewed rubric: %w", err)
	}
	if TextSHA256(rubricBytes) != RubricSHA256 {
		return nil, fmt.Errorf("reviewed rubric digest drift")
	}
	rules, err := frozenRules()
	if err != nil {
		return nil, err
	}
	rulesPath := filepath.Join(root, "go-backend", "internal", "contentbuild", "rules_unicode15.json")
	rootRules, err := readDirect(rulesPath, 8<<20)
	if err != nil || SHA256(rootRules) != rulesSHA256 || SHA256(rootRules) != SHA256(rulesBytes) {
		return nil, fmt.Errorf("root frozen rules differ from native rules")
	}
	provenancePath := filepath.Join(root, "go-backend", "internal", "contentbuild", "rules_provenance.json")
	rootProvenance, err := readDirect(provenancePath, 1<<20)
	if err != nil || SHA256(rootProvenance) != SHA256(provenanceBytes) {
		return nil, fmt.Errorf("root frozen rules provenance differs from native provenance")
	}
	native, err := nativeSourceBindings(root)
	if err != nil {
		return nil, err
	}
	captions := lantCaptions(g, rules)
	artifact := map[string]any{
		"schema":        prospectiveLantCaptionSchema,
		"purpose":       "unapproved_native_preview_only",
		"game":          "lant",
		"qualification": "Native derivation and validation only; no content, source, ranking, rail, installation or serving approval.",
		"inputs": map[string]any{
			"kg":               binding(kgPath, kgBytes),
			"pack":             binding(packPath, packBytes),
			"rubric":           binding("docs/CRITIQUE_RUBRIC.md", rubricBytes),
			"rules_unicode15":  binding("go-backend/internal/contentbuild/rules_unicode15.json", rootRules),
			"rules_provenance": binding("go-backend/internal/contentbuild/rules_provenance.json", rootProvenance),
			"native_sources":   native,
			"go_version":       runtime.Version(),
		},
		"counts":   map[string]any{"directed_edges": len(captions)},
		"captions": captions,
	}
	b, err := Canonical(artifact)
	return append(b, '\n'), err
}

// WriteProspectiveLantCaptions writes a new private evidence artifact outside
// the source tree. Existing files and repository/serving paths are never used.
func WriteProspectiveLantCaptions(root, kgPath, packPath, out string) error {
	root, err := filepath.Abs(root)
	if err != nil {
		return err
	}
	out, err = filepath.Abs(out)
	if err != nil {
		return err
	}
	rel, err := filepath.Rel(root, out)
	if err != nil {
		return err
	}
	if rel == "." || rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		return fmt.Errorf("prospective preview output must be outside repository root")
	}
	parent := filepath.Dir(out)
	resolvedParent, err := filepath.EvalSymlinks(parent)
	if err != nil {
		return err
	}
	if resolvedParent != filepath.Clean(parent) {
		return fmt.Errorf("prospective preview output parent must not traverse symlinks")
	}
	b, err := BuildProspectiveLantCaptions(root, kgPath, packPath)
	if err != nil {
		return err
	}
	f, err := os.OpenFile(out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
	if err != nil {
		return err
	}
	if _, err = f.Write(b); err == nil {
		err = f.Sync()
	}
	if closeErr := f.Close(); err == nil {
		err = closeErr
	}
	return err
}
