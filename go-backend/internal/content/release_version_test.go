package content

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
)

// Neutral native metadata is mandatory. Retained Python declarations remain
// checked when present, without becoming an input to the native-only gate.
func checkReleaseVersions(root, nativeVersion string) error {
	if !regexp.MustCompile(`^[0-9]+\.[0-9]+\.[0-9]+$`).MatchString(nativeVersion) {
		return fmt.Errorf("native release version is not SemVer")
	}
	read := func(path string) ([]byte, error) {
		b, err := os.ReadFile(filepath.Join(root, path))
		if err != nil {
			return nil, err
		}
		if len(b) > 1<<20 {
			return nil, fmt.Errorf("release metadata too large: %s", path)
		}
		return b, nil
	}
	decode := func(path string, target any) error {
		b, err := read(path)
		if err != nil {
			return err
		}
		if err = strictjson.Validate(b); err != nil {
			return err
		}
		return json.Unmarshal(b, target)
	}
	extract := func(raw []byte, pattern, label string) (string, error) {
		matches := regexp.MustCompile(pattern).FindAllSubmatch(raw, -1)
		if len(matches) != 1 {
			return "", fmt.Errorf("release declaration must be unique: %s", label)
		}
		return string(matches[0][1]), nil
	}
	var release struct {
		Schema  int    `json:"schema_version"`
		Version string `json:"version"`
	}
	if err := decode("go-backend/release.json", &release); err != nil {
		return err
	}
	if release.Schema != 1 {
		return fmt.Errorf("native release metadata schema mismatch")
	}
	var pkg struct {
		Version string `json:"version"`
	}
	if err := decode("frontend/package.json", &pkg); err != nil {
		return err
	}
	var lock struct {
		Version  string `json:"version"`
		Packages map[string]struct {
			Version string `json:"version"`
		} `json:"packages"`
	}
	if err := decode("frontend/package-lock.json", &lock); err != nil {
		return err
	}
	values := map[string]string{"neutral native release": release.Version, "frontend package": pkg.Version, "lock": lock.Version, "lock root package": lock.Packages[""].Version}
	ts, err := read("frontend/src/release.ts")
	if err != nil {
		return err
	}
	values["frontend RELEASE_VERSION"], err = extract(ts, `export const RELEASE_VERSION = "([^"]+)";`, "RELEASE_VERSION")
	if err != nil {
		return err
	}
	label, err := extract(ts, `export const RELEASE_LABEL = "([^"]+)";`, "RELEASE_LABEL")
	if err != nil {
		return err
	}
	if label != "V"+nativeVersion {
		return fmt.Errorf("lobby badge does not name native release")
	}
	if legacy, err := read("cat_de_roman_esti/__init__.py"); err == nil {
		values["retained legacy package"], err = extract(legacy, `(?m)^__version__ = "([^"]+)"$`, "legacy __version__")
		if err != nil {
			return err
		}
	} else if !os.IsNotExist(err) {
		return err
	}
	if project, err := read("pyproject.toml"); err == nil {
		start := bytes.Index(project, []byte("[project]\n"))
		if start < 0 {
			return fmt.Errorf("retained project metadata missing")
		}
		section := string(project[start+len("[project]\n"):])
		if end := strings.Index(section, "\n["); end >= 0 {
			section = section[:end]
		}
		values["retained project metadata"], err = extract([]byte(section), `(?m)^version = "([^"]+)"$`, "project version")
		if err != nil {
			return err
		}
	} else if !os.IsNotExist(err) {
		return err
	}
	for name, actual := range values {
		if actual != nativeVersion {
			return fmt.Errorf("%s=%s differs from native %s", name, actual, nativeVersion)
		}
	}
	return nil
}
func TestNativeReleaseVersionCoupling(t *testing.T) {
	c, err := Load()
	if err != nil {
		t.Fatal(err)
	}
	if err = checkReleaseVersions("../../..", c.AppVersion); err != nil {
		t.Fatal(err)
	}
}
func minimalReleaseRoot(t *testing.T) string {
	t.Helper()
	root := t.TempDir()
	files := map[string]string{
		"go-backend/release.json":    `{"schema_version":1,"version":"1.0.1"}`,
		"frontend/package.json":      `{"version":"1.0.1"}`,
		"frontend/package-lock.json": `{"version":"1.0.1","packages":{"":{"version":"1.0.1"}}}`,
		"frontend/src/release.ts":    "export const RELEASE_VERSION = \"1.0.1\";\nexport const RELEASE_LABEL = \"V1.0.1\";\n",
	}
	for path, text := range files {
		putReleaseFile(t, root, path, text)
	}
	return root
}
func putReleaseFile(t *testing.T, root, path, text string) {
	t.Helper()
	full := filepath.Join(root, path)
	if err := os.MkdirAll(filepath.Dir(full), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(full, []byte(text), 0600); err != nil {
		t.Fatal(err)
	}
}
func TestMinimalNativeReleaseRootWithoutPythonReferences(t *testing.T) {
	root := minimalReleaseRoot(t)
	if err := checkReleaseVersions(root, "1.0.1"); err != nil {
		t.Fatal(err)
	}
	for _, path := range []string{"cat_de_roman_esti/__init__.py", "pyproject.toml"} {
		if _, err := os.Stat(filepath.Join(root, path)); !os.IsNotExist(err) {
			t.Fatal("minimal fixture unexpectedly contains legacy metadata")
		}
	}
}
func TestReleaseVersionMismatchAndOptionalReferenceGuards(t *testing.T) {
	cases := []struct{ name, path, text, native string }{
		{"native built version", "", "", "2.0.0"}, {"native SemVer", "", "", "V1.0.1"},
		{"neutral version", "go-backend/release.json", `{"schema_version":1,"version":"2.0.0"}`, "1.0.1"},
		{"neutral schema", "go-backend/release.json", `{"schema_version":2,"version":"1.0.1"}`, "1.0.1"},
		{"package", "frontend/package.json", `{"version":"2.0.0"}`, "1.0.1"},
		{"lock top", "frontend/package-lock.json", `{"version":"2.0.0","packages":{"":{"version":"1.0.1"}}}`, "1.0.1"},
		{"lock root", "frontend/package-lock.json", `{"version":"1.0.1","packages":{"":{"version":"2.0.0"}}}`, "1.0.1"},
		{"TS version", "frontend/src/release.ts", "export const RELEASE_VERSION = \"2.0.0\";\nexport const RELEASE_LABEL = \"V1.0.1\";", "1.0.1"},
		{"badge", "frontend/src/release.ts", "export const RELEASE_VERSION = \"1.0.1\";\nexport const RELEASE_LABEL = \"V2.0.0\";", "1.0.1"},
		{"legacy package only", "cat_de_roman_esti/__init__.py", "__version__ = \"2.0.0\"\n", "1.0.1"},
		{"legacy project only", "pyproject.toml", "[project]\nversion = \"2.0.0\"\n", "1.0.1"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			root := minimalReleaseRoot(t)
			if c.path != "" {
				putReleaseFile(t, root, c.path, c.text)
			}
			if err := checkReleaseVersions(root, c.native); err == nil {
				t.Fatal("version mismatch accepted")
			}
		})
	}
	for _, c := range []struct{ path, text string }{{"cat_de_roman_esti/__init__.py", "__version__ = \"1.0.1\"\n"}, {"pyproject.toml", "[project]\nversion = \"1.0.1\"\n"}} {
		root := minimalReleaseRoot(t)
		putReleaseFile(t, root, c.path, c.text)
		if err := checkReleaseVersions(root, "1.0.1"); err != nil {
			t.Fatal("matching optional declaration refused", err)
		}
	}
}
