package content

import (
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// Port the independent legacy release coupling contract: badge/package/lock
// fields must agree with the canonical native build, not merely each other.
func TestNativeReleaseVersionCoupling(t *testing.T) {
	c, err := Load()
	if err != nil {
		t.Fatal(err)
	}
	version := c.AppVersion
	if !regexp.MustCompile(`^[0-9]+\.[0-9]+\.[0-9]+$`).MatchString(version) {
		t.Fatal("native release version is not SemVer")
	}
	root := "../../.."
	read := func(path string) []byte {
		t.Helper()
		b, err := os.ReadFile(filepath.Join(root, path))
		if err != nil {
			t.Fatal(err)
		}
		return b
	}
	var pkg struct {
		Version string `json:"version"`
	}
	if err = json.Unmarshal(read("frontend/package.json"), &pkg); err != nil {
		t.Fatal(err)
	}
	var lock struct {
		Version  string `json:"version"`
		Packages map[string]struct {
			Version string `json:"version"`
		} `json:"packages"`
	}
	if err = json.Unmarshal(read("frontend/package-lock.json"), &lock); err != nil {
		t.Fatal(err)
	}
	values := map[string]string{"frontend package": pkg.Version, "lock": lock.Version, "lock root package": lock.Packages[""].Version}
	extract := func(raw []byte, pattern, label string) string {
		t.Helper()
		matches := regexp.MustCompile(pattern).FindAllSubmatch(raw, -1)
		if len(matches) != 1 {
			t.Fatal("release declaration must be unique", label)
		}
		return string(matches[0][1])
	}
	release := read("frontend/src/release.ts")
	values["frontend RELEASE_VERSION"] = extract(release, `export const RELEASE_VERSION = "([^"]+)";`, "RELEASE_VERSION")
	label := extract(release, `export const RELEASE_LABEL = "([^"]+)";`, "RELEASE_LABEL")
	if label != "V"+version {
		t.Fatal("lobby badge does not name native release", label, version)
	}
	// Retained source declarations remain coupled without executing Python.
	values["legacy package"] = extract(read("cat_de_roman_esti/__init__.py"), `(?m)^__version__ = "([^"]+)"$`, "legacy __version__")
	project := string(read("pyproject.toml"))
	start := strings.Index(project, "[project]\n")
	if start < 0 {
		t.Fatal("project metadata missing")
	}
	section := project[start+len("[project]\n"):]
	if end := strings.Index(section, "\n["); end >= 0 {
		section = section[:end]
	}
	values["project metadata"] = extract([]byte(section), `(?m)^version = "([^"]+)"$`, "project version")
	for name, actual := range values {
		if actual != version {
			t.Errorf("%s=%s differs from native %s", name, actual, version)
		}
	}
}
