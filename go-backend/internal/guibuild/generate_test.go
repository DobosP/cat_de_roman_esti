package guibuild

import (
	"bytes"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func fixtureSourceTree(t *testing.T) string {
	t.Helper()
	root := t.TempDir()
	manifest := filepath.Join(root, "go-backend", "embedfs", filepath.FromSlash(ManifestPath))
	if err := os.MkdirAll(filepath.Dir(manifest), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(manifest, fixtureManifest, 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, "versions.lock.json"), fixtureLock, 0644); err != nil {
		t.Fatal(err)
	}
	return root
}

func generatedMetadataPath(root, path string) string {
	return filepath.Join(root, "go-backend", "embedfs", filepath.FromSlash(path))
}

func requireNoDescriptor(t *testing.T, root string) {
	t.Helper()
	_, err := os.Lstat(generatedMetadataPath(root, DescriptorPath))
	if !os.IsNotExist(err) {
		t.Fatalf("descriptor still present or inaccessible: %v", err)
	}
}

func loadGenerated(t *testing.T, root string) {
	t.Helper()
	embedded := os.DirFS(filepath.Join(root, "go-backend", "embedfs"))
	identity, err := Load(embedded, embedded)
	expected := fixtureIdentity(fixtureManifest, fixtureLock)
	if err != nil || identity == nil || *identity != expected {
		t.Fatalf("generated identity=%#v, error=%v, want=%#v", identity, err, expected)
	}
}

func TestGenerateCopiesExactLockBytesAndExplicitSourceBinding(t *testing.T) {
	root := fixtureSourceTree(t)
	// The source values are explicit build arguments, not environment fallbacks.
	t.Setenv("GATE_SHA", strings.Repeat("a", 40))
	t.Setenv("GATE_TREE_SHA256", strings.Repeat("b", 64))
	t.Setenv("GATE_APP_IMAGE_ID", "sha256:"+strings.Repeat("c", 64))
	if err := Generate(root, fixtureSHA, fixtureTree); err != nil {
		t.Fatal(err)
	}
	copied, err := os.ReadFile(generatedMetadataPath(root, VersionsLockPath))
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(copied, fixtureLock) {
		t.Fatalf("lock bytes changed: got %q, want %q", copied, fixtureLock)
	}
	for _, path := range []string{DescriptorPath, VersionsLockPath} {
		info, err := os.Lstat(generatedMetadataPath(root, path))
		if err != nil || !info.Mode().IsRegular() {
			t.Fatalf("generated %s is not regular: info=%v, error=%v", path, info, err)
		}
	}
	loadGenerated(t, root)
}

func TestGenerateFailureRemovesEarlierDescriptor(t *testing.T) {
	cases := []struct {
		name   string
		sha    string
		tree   string
		change func(*testing.T, string)
	}{
		{"empty SHA", "", fixtureTree, nil},
		{"zero SHA", strings.Repeat("0", 40), fixtureTree, nil},
		{"uppercase SHA", strings.Repeat("A", 40), fixtureTree, nil},
		{"empty tree", fixtureSHA, "", nil},
		{"zero tree", fixtureSHA, strings.Repeat("0", 64), nil},
		{"uppercase tree", fixtureSHA, strings.Repeat("A", 64), nil},
		{"missing manifest", fixtureSHA, fixtureTree, func(t *testing.T, root string) {
			if err := os.Remove(generatedMetadataPath(root, ManifestPath)); err != nil {
				t.Fatal(err)
			}
		}},
		{"missing lock", fixtureSHA, fixtureTree, func(t *testing.T, root string) {
			if err := os.Remove(filepath.Join(root, "versions.lock.json")); err != nil {
				t.Fatal(err)
			}
		}},
		{"non-object manifest", fixtureSHA, fixtureTree, func(t *testing.T, root string) {
			if err := os.WriteFile(generatedMetadataPath(root, ManifestPath), []byte(`[]`), 0644); err != nil {
				t.Fatal(err)
			}
		}},
		{"non-object lock", fixtureSHA, fixtureTree, func(t *testing.T, root string) {
			if err := os.WriteFile(filepath.Join(root, "versions.lock.json"), []byte(`null`), 0644); err != nil {
				t.Fatal(err)
			}
		}},
		{"oversized manifest", fixtureSHA, fixtureTree, func(t *testing.T, root string) {
			data := []byte(`{"pad":"` + strings.Repeat("x", 4*1024*1024) + `"}`)
			if err := os.WriteFile(generatedMetadataPath(root, ManifestPath), data, 0644); err != nil {
				t.Fatal(err)
			}
		}},
		{"oversized lock", fixtureSHA, fixtureTree, func(t *testing.T, root string) {
			data := []byte(`{"pad":"` + strings.Repeat("x", 2*1024*1024) + `"}`)
			if err := os.WriteFile(filepath.Join(root, "versions.lock.json"), data, 0644); err != nil {
				t.Fatal(err)
			}
		}},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			root := fixtureSourceTree(t)
			if err := Generate(root, fixtureSHA, fixtureTree); err != nil {
				t.Fatal(err)
			}
			if test.change != nil {
				test.change(t, root)
			}
			// Even plausible ambient claims must not repair invalid explicit input.
			t.Setenv("GATE_SHA", fixtureSHA)
			t.Setenv("GATE_TREE_SHA256", fixtureTree)
			if err := Generate(root, test.sha, test.tree); err == nil {
				t.Fatal("Generate accepted invalid input")
			}
			requireNoDescriptor(t, root)
			embedded := os.DirFS(filepath.Join(root, "go-backend", "embedfs"))
			requireLoadFailure(t, embedded, embedded)
		})
	}
}

func fixtureSymlink(t *testing.T, target, link string) {
	t.Helper()
	if err := os.Symlink(target, link); err != nil {
		if runtime.GOOS == "windows" {
			t.Fatalf("Windows symlink creation is unavailable without the required local privilege: %v", err)
		}
		t.Fatalf("create symlink: %v", err)
	}
}

func TestGenerateRejectsSymlinkedInputsAndClearsEarlierDescriptor(t *testing.T) {
	for _, input := range []string{"manifest", "lock"} {
		t.Run(input, func(t *testing.T) {
			root := fixtureSourceTree(t)
			if err := Generate(root, fixtureSHA, fixtureTree); err != nil {
				t.Fatal(err)
			}
			path := filepath.Join(root, "versions.lock.json")
			data := fixtureLock
			if input == "manifest" {
				path = generatedMetadataPath(root, ManifestPath)
				data = fixtureManifest
			}
			outside := filepath.Join(t.TempDir(), "outside.json")
			if err := os.WriteFile(outside, data, 0644); err != nil {
				t.Fatal(err)
			}
			if err := os.Remove(path); err != nil {
				t.Fatal(err)
			}
			fixtureSymlink(t, outside, path)
			if err := Generate(root, fixtureSHA, fixtureTree); err == nil {
				t.Fatal("Generate accepted a symlinked input")
			}
			requireNoDescriptor(t, root)
			actual, err := os.ReadFile(outside)
			if err != nil || !bytes.Equal(actual, data) {
				t.Fatalf("outside input changed: error=%v", err)
			}
		})
	}
}

func TestGenerateRejectsSymlinkedOutputAncestorWithoutOutsideWrites(t *testing.T) {
	root := fixtureSourceTree(t)
	outside := t.TempDir()
	outsideDist := filepath.Join(outside, "dist")
	if err := os.MkdirAll(outsideDist, 0755); err != nil {
		t.Fatal(err)
	}
	outsideDescriptor := filepath.Join(outsideDist, ".gui-build.json")
	marker := []byte("outside file must remain intact\n")
	if err := os.WriteFile(outsideDescriptor, marker, 0644); err != nil {
		t.Fatal(err)
	}
	fixtureSymlink(t, outside, filepath.Join(root, "go-backend", "embedfs", "build"))
	if err := Generate(root, fixtureSHA, fixtureTree); err == nil {
		t.Fatal("Generate accepted a symlinked output ancestor")
	}
	actual, err := os.ReadFile(outsideDescriptor)
	if err != nil || !bytes.Equal(actual, marker) {
		t.Fatalf("outside descriptor was changed: data=%q, error=%v", actual, err)
	}
	if _, err := os.Lstat(filepath.Join(outsideDist, "versions.lock.json")); !os.IsNotExist(err) {
		t.Fatalf("generator wrote outside versions lock or inspection failed: %v", err)
	}
}

func TestGenerateRejectsNonRegularInputAndClearsEarlierDescriptor(t *testing.T) {
	root := fixtureSourceTree(t)
	if err := Generate(root, fixtureSHA, fixtureTree); err != nil {
		t.Fatal(err)
	}
	lock := filepath.Join(root, "versions.lock.json")
	if err := os.Remove(lock); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(lock, 0755); err != nil {
		t.Fatal(err)
	}
	if err := Generate(root, fixtureSHA, fixtureTree); err == nil {
		t.Fatal("Generate accepted a directory as the versions lock")
	}
	requireNoDescriptor(t, root)
}

func TestGenerateRejectsSymlinkedDescriptorWithoutRemovingOutsideFile(t *testing.T) {
	root := fixtureSourceTree(t)
	if err := Generate(root, fixtureSHA, fixtureTree); err != nil {
		t.Fatal(err)
	}
	descriptor := generatedMetadataPath(root, DescriptorPath)
	outside := filepath.Join(t.TempDir(), "outside.json")
	marker := []byte("outside descriptor must remain intact\n")
	if err := os.WriteFile(outside, marker, 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.Remove(descriptor); err != nil {
		t.Fatal(err)
	}
	fixtureSymlink(t, outside, descriptor)
	if err := Generate(root, fixtureSHA, fixtureTree); err == nil {
		t.Fatal("Generate accepted a symlinked descriptor output")
	}
	actual, err := os.ReadFile(outside)
	if err != nil || !bytes.Equal(actual, marker) {
		t.Fatalf("outside descriptor changed: data=%q, error=%v", actual, err)
	}
	embedded := os.DirFS(filepath.Join(root, "go-backend", "embedfs"))
	requireLoadFailure(t, embedded, embedded)
}

func TestGenerateRejectsRootAliasWithoutOutsideWrites(t *testing.T) {
	root := fixtureSourceTree(t)
	alias := filepath.Join(t.TempDir(), "source-alias")
	fixtureSymlink(t, root, alias)
	if err := Generate(alias, fixtureSHA, fixtureTree); err == nil {
		t.Fatal("Generate accepted a root alias")
	}
	requireNoDescriptor(t, root)
	actual, err := os.ReadFile(filepath.Join(root, "versions.lock.json"))
	if err != nil || !bytes.Equal(actual, fixtureLock) {
		t.Fatalf("aliased source changed: error=%v", err)
	}
}
