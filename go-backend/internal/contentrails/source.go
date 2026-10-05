// Package contentrails preserves source authorship and independent review gates
// for native quick/world/recipe/reserve builders. It never reads a generated
// serving catalog as authored input.
package contentrails

import (
	"bytes"
	_ "embed"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
)

//go:embed sources/authored-v1.json
var authoredSource []byte

const AuthoredSHA256 = "bbeffd444e85205a08fdfcdec43914dd69d4ee11dc24e758fdac99a0909529c6"
const MaxBytes = 4 << 20

var artifacts = map[string]string{"quick": "quick_games_v92.json", "world": "alchimie_discovery_world_v92.json", "extensions": "alchimie_recipe_extensions_v92.json", "reserve": "release_reserve_v1.json"}

type Source struct {
	Raw     map[string]any
	SHA256  string
	Version int
}

func object(v any) map[string]any { m, _ := v.(map[string]any); return m }
func rows(v any) []any {
	if v == nil {
		return nil
	}
	if x, ok := v.([]any); ok {
		return x
	}
	rv := reflect.ValueOf(v)
	if rv.Kind() != reflect.Slice && rv.Kind() != reflect.Array {
		return nil
	}
	out := make([]any, rv.Len())
	for i := range out {
		out[i] = rv.Index(i).Interface()
	}
	return out
}
func text(v any) string { s, _ := v.(string); return s }
func integer(v any) int {
	switch x := v.(type) {
	case json.Number:
		n, err := x.Int64()
		if err != nil || int64(int(n)) != n {
			return -1
		}
		return int(n)
	case int:
		return x
	}
	return -1
}
func ids(v any) []string {
	out := []string{}
	for _, x := range rows(v) {
		out = append(out, text(x))
	}
	return out
}
func required(ok bool, message string) error {
	if !ok {
		return fmt.Errorf("content rail: %s", message)
	}
	return nil
}
func digest(v any) string { b, _ := contentbuild.Canonical(v); return contentbuild.SHA256(b) }
func same(a, b any) bool  { return digest(a) == digest(b) }
func clone(v any) any {
	b, _ := contentbuild.Canonical(v)
	d := json.NewDecoder(bytes.NewReader(b))
	d.UseNumber()
	var out any
	_ = d.Decode(&out)
	return out
}
func Render(v any) ([]byte, error) {
	raw, err := contentbuild.Canonical(v)
	if err != nil {
		return nil, err
	}
	var b bytes.Buffer
	if err = json.Indent(&b, raw, "", "  "); err != nil {
		return nil, err
	}
	return append(b.Bytes(), '\n'), nil
}
func Read(path string) (map[string]any, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	b, err := io.ReadAll(io.LimitReader(f, MaxBytes+1))
	if err != nil {
		return nil, err
	}
	if len(b) > MaxBytes {
		return nil, fmt.Errorf("rail JSON byte cap")
	}
	if err = strictjson.Validate(b); err != nil {
		return nil, err
	}
	return contentops.Decode(b)
}
func LoadSource(path string) (*Source, error) {
	raw := authoredSource
	var err error
	if path != "" {
		f, e := os.Open(path)
		if e != nil {
			return nil, e
		}
		defer f.Close()
		raw, err = io.ReadAll(io.LimitReader(f, MaxBytes+1))
		if err != nil {
			return nil, err
		}
	}
	s, err := decodeSource(raw, "", -1)
	if err != nil {
		return nil, err
	}
	if path == "" && s.SHA256 != AuthoredSHA256 {
		return nil, fmt.Errorf("pinned native authoring source drift")
	}
	if s.SHA256 == AuthoredSHA256 && s.Version == 1 {
		return s, nil
	}
	parent := text(s.Raw["parent_source_sha256"])
	validParent := s.Version == 2 && parent == AuthoredSHA256
	if s.Version > 2 {
		a, err := parseInstalledAuthorities(installedAuthorityBytes, InstalledAuthoritiesSHA256)
		if err != nil {
			return nil, err
		}
		validParent = a.registeredParent(s.Version, parent)
	}
	if !validParent {
		return nil, fmt.Errorf("authored transition requires sequential version and exact reviewed parent source")
	}
	return s, nil
}

func decodeSource(raw []byte, expectedParent string, expectedVersion int) (*Source, error) {
	if len(raw) > MaxBytes {
		return nil, fmt.Errorf("authored source byte cap exceeded")
	}
	if err := strictjson.Validate(raw); err != nil {
		return nil, err
	}
	value, err := contentops.Decode(raw)
	if err != nil {
		return nil, err
	}
	if err = sourceShape(value); err != nil {
		return nil, err
	}
	version := integer(value["version"])
	if value["schema"] != "native-content-authored-v1" || version < 1 || version > 1000 || expectedVersion >= 0 && (version != expectedVersion || version > 1 && value["parent_source_sha256"] != expectedParent) {
		return nil, fmt.Errorf("authored schema/version/parent refused")
	}
	return &Source{value, contentbuild.SHA256(raw), version}, nil
}
func archive(root string, s *Source, name string) (map[string]any, error) {
	a := object(object(s.Raw["archives"])[name])
	relative := text(a["path"])
	if relative == "" || filepath.IsAbs(relative) || strings.Contains(relative, "..") || !strings.HasPrefix(relative, "docs/reviews/") {
		return nil, fmt.Errorf("protected authored archive path")
	}
	p := filepath.Join(root, relative)
	raw, err := os.ReadFile(p)
	if err != nil {
		return nil, err
	}
	if len(raw) > MaxBytes || contentbuild.SHA256(raw) != a["sha256"] {
		return nil, fmt.Errorf("immutable authored archive drift: %s", name)
	}
	return Read(p)
}
func fixture(root, name string) (map[string]any, error) {
	return Read(filepath.Join(root, "cat_de_roman_esti/fixtures", name))
}
func bindings(root string) (map[string]any, error) {
	out := map[string]any{}
	for _, name := range contentbuild.SourceNames {
		raw, err := os.ReadFile(filepath.Join(root, "cat_de_roman_esti/fixtures", name))
		if err != nil {
			return nil, err
		}
		out[name] = contentbuild.TextSHA256(raw)
	}
	raw, err := os.ReadFile(filepath.Join(root, "docs/CRITIQUE_RUBRIC.md"))
	if err != nil {
		return nil, err
	}
	if contentbuild.TextSHA256(raw) != contentbuild.RubricSHA256 {
		return nil, fmt.Errorf("review rubric drift")
	}
	out["rubric"] = contentbuild.TextSHA256(raw)
	return out, nil
}
func sourceGraph(root string) (*graph.Service, error) {
	return contentbuild.SourceGraph(filepath.Join(root, "cat_de_roman_esti/fixtures/kg_sample.json"))
}
func sortedKeys(m map[string]any) []string {
	out := []string{}
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
func ArtifactPath(root, rail string) (string, error) {
	name, ok := artifacts[rail]
	if !ok {
		return "", fmt.Errorf("unknown rail %s", rail)
	}
	return filepath.Join(root, "cat_de_roman_esti/fixtures", name), nil
}
