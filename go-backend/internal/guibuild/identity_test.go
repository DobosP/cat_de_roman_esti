package guibuild

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io/fs"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/DobosP/roedu-ui/web-kit/health"
)

// These explicit synthetic values are test fixtures, never production defaults.
const fixtureSHA = "1111111111111111111111111111111111111111"
const fixtureTree = "2222222222222222222222222222222222222222222222222222222222222222"

var fixtureManifest = []byte("{\n  \"index.html\": {\"file\": \"assets/app.js\", \"isEntry\": true}\n}\n")
var fixtureLock = []byte(" {\n  \"schema\": 1, \"fixture\": \"synthetic\"\n}\n")

func fixtureDigest(data []byte) string {
	digest := sha256.Sum256(data)
	return hex.EncodeToString(digest[:])
}

func fixtureIdentity(manifest, lock []byte) health.Identity {
	return health.Identity{
		SHA:                fixtureSHA,
		TreeSHA256:         fixtureTree,
		ManifestSHA256:     fixtureDigest(manifest),
		VersionsLockSHA256: fixtureDigest(lock),
	}
}

func fixtureDescriptor(t *testing.T, identity health.Identity) []byte {
	t.Helper()
	data, err := json.Marshal(identity)
	if err != nil {
		t.Fatal(err)
	}
	return append(data, '\n')
}

func fixtureFiles(t *testing.T) (fstest.MapFS, fstest.MapFS, health.Identity) {
	t.Helper()
	identity := fixtureIdentity(fixtureManifest, fixtureLock)
	assets := fstest.MapFS{
		ManifestPath: &fstest.MapFile{Data: bytes.Clone(fixtureManifest), Mode: 0644},
	}
	metadata := fstest.MapFS{
		DescriptorPath:   &fstest.MapFile{Data: fixtureDescriptor(t, identity), Mode: 0644},
		VersionsLockPath: &fstest.MapFile{Data: bytes.Clone(fixtureLock), Mode: 0644},
	}
	return assets, metadata, identity
}

func requireLoadFailure(t *testing.T, assets, metadata fs.FS) {
	t.Helper()
	identity, err := Load(assets, metadata)
	if err == nil || identity != nil {
		t.Fatalf("Load returned identity=%#v, error=%v; wanted no identity and an error", identity, err)
	}
}

func TestLoadBindsExactEmbeddedBytes(t *testing.T) {
	assets, metadata, expected := fixtureFiles(t)
	identity, err := Load(assets, metadata)
	if err != nil {
		t.Fatal(err)
	}
	if *identity != expected {
		t.Fatalf("identity = %#v, want %#v", *identity, expected)
	}

	// Equivalent JSON with different bytes cannot reuse the earlier descriptor.
	assets[ManifestPath].Data = []byte(`{"index.html":{"file":"assets/app.js","isEntry":true}}`)
	requireLoadFailure(t, assets, metadata)
	expected = fixtureIdentity(assets[ManifestPath].Data, metadata[VersionsLockPath].Data)
	metadata[DescriptorPath].Data = fixtureDescriptor(t, expected)
	identity, err = Load(assets, metadata)
	if err != nil || identity == nil || *identity != expected {
		t.Fatalf("rebound exact bytes: identity=%#v, error=%v", identity, err)
	}

	metadata[VersionsLockPath].Data = bytes.TrimSpace(fixtureLock)
	requireLoadFailure(t, assets, metadata)
}

func TestLoadRejectsMissingInputs(t *testing.T) {
	for _, path := range []string{ManifestPath, DescriptorPath, VersionsLockPath} {
		t.Run(path, func(t *testing.T) {
			assets, metadata, _ := fixtureFiles(t)
			delete(assets, path)
			delete(metadata, path)
			requireLoadFailure(t, assets, metadata)
		})
	}
}

func TestLoadRejectsMalformedDescriptor(t *testing.T) {
	cases := []struct {
		name   string
		change func([]byte) []byte
	}{
		{"empty", func([]byte) []byte { return nil }},
		{"malformed", func([]byte) []byte { return []byte(`{"sha":`) }},
		{"array", func([]byte) []byte { return []byte(`[]`) }},
		{"null", func([]byte) []byte { return []byte(`null`) }},
		{"extra", func(data []byte) []byte { return append([]byte(`{"unexpected":"value",`), data[1:]...) }},
		{"duplicate", func(data []byte) []byte { return append([]byte(`{"sha":"`+fixtureSHA+`",`), data[1:]...) }},
		{"wrong case", func(data []byte) []byte { return bytes.Replace(data, []byte(`"sha"`), []byte(`"SHA"`), 1) }},
		{"non-string", func(data []byte) []byte {
			return bytes.Replace(data, []byte(`"sha":"`+fixtureSHA+`"`), []byte(`"sha":42`), 1)
		}},
		{"missing field", func(data []byte) []byte { return bytes.Replace(data, []byte(`"sha":"`+fixtureSHA+`",`), nil, 1) }},
		{"trailing object", func(data []byte) []byte { return append(data, []byte(`{}`)...) }},
		{"trailing scalar", func(data []byte) []byte { return append(data, []byte(`true`)...) }},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			assets, metadata, _ := fixtureFiles(t)
			metadata[DescriptorPath].Data = test.change(metadata[DescriptorPath].Data)
			requireLoadFailure(t, assets, metadata)
		})
	}
}

func TestLoadRejectsInvalidOrMismatchedBindings(t *testing.T) {
	cases := []struct {
		name   string
		change func(*health.Identity)
	}{
		{"short SHA", func(i *health.Identity) { i.SHA = "1" }},
		{"uppercase SHA", func(i *health.Identity) { i.SHA = strings.Repeat("A", 40) }},
		{"zero SHA", func(i *health.Identity) { i.SHA = strings.Repeat("0", 40) }},
		{"short tree", func(i *health.Identity) { i.TreeSHA256 = "2" }},
		{"uppercase tree", func(i *health.Identity) { i.TreeSHA256 = strings.Repeat("A", 64) }},
		{"zero tree", func(i *health.Identity) { i.TreeSHA256 = strings.Repeat("0", 64) }},
		{"invalid manifest hash", func(i *health.Identity) { i.ManifestSHA256 = "not-a-hash" }},
		{"zero manifest hash", func(i *health.Identity) { i.ManifestSHA256 = strings.Repeat("0", 64) }},
		{"manifest mismatch", func(i *health.Identity) { i.ManifestSHA256 = strings.Repeat("3", 64) }},
		{"zero lock hash", func(i *health.Identity) { i.VersionsLockSHA256 = strings.Repeat("0", 64) }},
		{"lock mismatch", func(i *health.Identity) { i.VersionsLockSHA256 = strings.Repeat("4", 64) }},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			assets, metadata, identity := fixtureFiles(t)
			test.change(&identity)
			metadata[DescriptorPath].Data = fixtureDescriptor(t, identity)
			requireLoadFailure(t, assets, metadata)
		})
	}
}

func TestLoadRejectsNonObjectJSONInputs(t *testing.T) {
	for _, path := range []string{ManifestPath, VersionsLockPath} {
		for _, value := range []string{"", "[]", "null", "42", "{", "{} {}"} {
			t.Run(path+"/"+value, func(t *testing.T) {
				assets, metadata, _ := fixtureFiles(t)
				if path == ManifestPath {
					assets[path].Data = []byte(value)
				} else {
					metadata[path].Data = []byte(value)
				}
				identity := fixtureIdentity(assets[ManifestPath].Data, metadata[VersionsLockPath].Data)
				metadata[DescriptorPath].Data = fixtureDescriptor(t, identity)
				requireLoadFailure(t, assets, metadata)
			})
		}
	}
}

func TestLoadRejectsOversizedAndNonRegularInputs(t *testing.T) {
	for _, path := range []string{ManifestPath, DescriptorPath, VersionsLockPath} {
		t.Run(path+"/oversized", func(t *testing.T) {
			assets, metadata, _ := fixtureFiles(t)
			file := metadata[path]
			if path == ManifestPath {
				file = assets[path]
			}
			// Exceeds all three documented input bounds without executing a build.
			file.Data = []byte(`{"pad":"` + strings.Repeat("x", 8*1024*1024) + `"}`)
			requireLoadFailure(t, assets, metadata)
		})
		for _, mode := range []fs.FileMode{fs.ModeDir, fs.ModeSymlink} {
			t.Run(path+"/"+mode.String(), func(t *testing.T) {
				assets, metadata, _ := fixtureFiles(t)
				file := metadata[path]
				if path == ManifestPath {
					file = assets[path]
				}
				file.Mode = mode | 0644
				requireLoadFailure(t, assets, metadata)
			})
		}
	}
}

func TestLoadIgnoresRuntimeEnvironmentClaims(t *testing.T) {
	assets, metadata, expected := fixtureFiles(t)
	for name, value := range map[string]string{
		"GATE_SHA":                  strings.Repeat("a", 40),
		"GATE_TREE_SHA256":          strings.Repeat("b", 64),
		"GATE_APP_IMAGE_ID":         "sha256:" + strings.Repeat("c", 64),
		"GATE_MANIFEST_SHA256":      strings.Repeat("d", 64),
		"GATE_VERSIONS_LOCK_SHA256": strings.Repeat("e", 64),
	} {
		t.Setenv(name, value)
	}
	identity, err := Load(assets, metadata)
	if err != nil || identity == nil || *identity != expected {
		t.Fatalf("environment changed baked identity: identity=%#v, error=%v", identity, err)
	}
	delete(metadata, DescriptorPath)
	requireLoadFailure(t, assets, metadata)
}
