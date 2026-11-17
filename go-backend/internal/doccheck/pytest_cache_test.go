package doccheck

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
)

// Fixture-only proposal coverage; these are never canonical campaign receipts.
func pytestCacheFixture(t *testing.T) (string, string, []string) {
	t.Helper()
	root, inventory, paths := gitInventoryFixture(t)
	writeInventorySource(t, root, ".gitignore", ".venv/\n.pytest_cache/\n")
	writeInventorySource(t, root, ".pytest_cache/README.md", "Opus 4.1\n")
	return root, inventory, paths
}

func TestInventoryCanonicalIgnoredPytestCache(t *testing.T) {
	root, inventory, _ := pytestCacheFixture(t)
	// Both precisely admitted trees may coexist; the approved .venv rule remains intact.
	virtualenvAlias(t, root, ".venv")
	report, err := CheckInventory(root, inventory)
	if err != nil || !report.Green() || report.Files != 2 {
		t.Fatalf("canonical ignored untracked cache: %+v %v", report, err)
	}
}

func TestInventoryPytestCacheProofIsNarrow(t *testing.T) {
	for _, kind := range []string{"unignored", "tracked-markdown", "tracked-nonmarkdown", "tracked-newline", "indexed-deleted", "nested", "other-ignored", "near-prefix", "no-git", "parent-git", "global-rule", "info-exclude", "local-ignore", "broad-rule", "anchored-rule", "negated-rule", "corrupt-index", "missing-git"} {
		t.Run(kind, func(t *testing.T) {
			root, inventory, _ := pytestCacheFixture(t)
			cache := filepath.Join(root, ".pytest_cache")
			switch kind {
			case "unignored":
				writeInventorySource(t, root, ".gitignore", ".venv/\n")
			case "tracked-markdown", "tracked-nonmarkdown", "tracked-newline", "indexed-deleted":
				name := ".pytest_cache/README.md"
				if kind == "tracked-nonmarkdown" || kind == "indexed-deleted" {
					name = ".pytest_cache/private.data"
				} else if kind == "tracked-newline" {
					name = ".pytest_cache/private\nentry.data"
				}
				writeInventorySource(t, root, name, "# Indexed source\n")
				inventoryGit(t, root, "add", "-f", "--", name)
				if kind == "indexed-deleted" {
					if err := os.Remove(filepath.Join(root, name)); err != nil {
						t.Fatal(err)
					}
				}
			case "nested", "other-ignored", "near-prefix":
				name := "source/.pytest_cache"
				if kind == "other-ignored" {
					name = ".ruff_cache"
					writeInventorySource(t, root, ".gitignore", ".venv/\n.pytest_cache/\n.ruff_cache/\n")
				} else if kind == "near-prefix" {
					name = ".pytest_cache-copy"
				}
				if err := os.MkdirAll(filepath.Dir(filepath.Join(root, name)), 0700); err != nil {
					t.Fatal(err)
				}
				if err := os.Rename(cache, filepath.Join(root, name)); err != nil {
					t.Fatal(err)
				}
			case "no-git", "parent-git":
				if err := os.RemoveAll(filepath.Join(root, ".git")); err != nil {
					t.Fatal(err)
				}
				if kind == "parent-git" {
					inventoryGit(t, filepath.Dir(root), "init", "--quiet")
				}
			case "global-rule", "info-exclude", "local-ignore":
				writeInventorySource(t, root, ".gitignore", ".venv/\n")
				if kind == "global-rule" {
					writeInventorySource(t, root, "global-ignore", ".pytest_cache/\n")
					inventoryGit(t, root, "config", "core.excludesFile", filepath.Join(root, "global-ignore"))
				} else if kind == "info-exclude" {
					writeInventorySource(t, root, ".git/info/exclude", ".pytest_cache/\n")
				} else {
					writeInventorySource(t, root, ".pytest_cache/.gitignore", "*\n")
				}
			case "broad-rule":
				writeInventorySource(t, root, ".gitignore", ".venv/\n.*cache*/\n")
			case "anchored-rule":
				writeInventorySource(t, root, ".gitignore", ".venv/\n/.pytest_cache/\n")
			case "negated-rule":
				writeInventorySource(t, root, ".gitignore", ".venv/\n.pytest_cache/\n!.pytest_cache/\n")
			case "corrupt-index":
				writeInventorySource(t, root, ".git/index", "corrupt fixture index\n")
			case "missing-git":
				t.Setenv("PATH", t.TempDir())
			}
			_, err := CheckInventory(root, inventory)
			if err == nil || !strings.Contains(err.Error(), "differs from physical source set") {
				t.Fatalf("%s cache wrongly excluded, or unexpected failure: %v", kind, err)
			}
		})
	}
}

func TestInventoryPytestCacheSymlinkRootsRemainRefused(t *testing.T) {
	for _, kind := range []string{"root-alias", "nested-alias", "ordinary-source-alias"} {
		t.Run(kind, func(t *testing.T) {
			root, inventory, _ := pytestCacheFixture(t)
			name := ".pytest_cache"
			if kind == "root-alias" {
				if err := os.RemoveAll(filepath.Join(root, name)); err != nil {
					t.Fatal(err)
				}
			} else if kind == "nested-alias" {
				name = "source/.pytest_cache"
				if err := os.MkdirAll(filepath.Join(root, "source"), 0700); err != nil {
					t.Fatal(err)
				}
			} else {
				name = "ordinary-alias.md"
			}
			target := t.TempDir()
			if kind == "ordinary-source-alias" {
				target = filepath.Join(root, "README.md")
			}
			if err := os.Symlink(target, filepath.Join(root, name)); err != nil {
				t.Fatal(err)
			}
			if _, err := CheckInventory(root, inventory); err == nil || !strings.Contains(err.Error(), "alias refused") {
				t.Fatalf("%s alias admitted or wrong failure: %v", kind, err)
			}
		})
	}
}

func TestInventoryPytestCacheStrictFallbackCanRemainSource(t *testing.T) {
	for _, tracked := range []bool{false, true} {
		t.Run(map[bool]string{false: "unignored", true: "tracked"}[tracked], func(t *testing.T) {
			root, inventory, paths := pytestCacheFixture(t)
			writeInventorySource(t, root, ".pytest_cache/README.md", "# Source\n")
			if tracked {
				inventoryGit(t, root, "add", "-f", "--", ".pytest_cache/README.md")
			} else {
				writeInventorySource(t, root, ".gitignore", ".venv/\n")
			}
			paths = append(paths, ".pytest_cache/README.md")
			sort.Strings(paths)
			writeInventory(t, inventory, paths)
			report, err := CheckInventory(root, inventory)
			if err != nil || !report.Green() || report.Files != 3 {
				t.Fatalf("strict fallback no longer admits declared ordinary source: %+v %v", report, err)
			}
		})
	}
}

func TestInventoryPytestCacheInventoryCannotBypassExclusion(t *testing.T) {
	for _, kind := range []string{"entry", "location"} {
		t.Run(kind, func(t *testing.T) {
			root, inventory, paths := pytestCacheFixture(t)
			want := "differs from physical source set"
			if kind == "entry" {
				paths = append(paths, ".pytest_cache/README.md")
				sort.Strings(paths)
			} else {
				inventory = filepath.Join(root, ".pytest_cache/inventory.json")
				want = "cannot be inside excluded .pytest_cache"
			}
			writeInventory(t, inventory, paths)
			if _, err := CheckInventory(root, inventory); err == nil || !strings.Contains(err.Error(), want) {
				t.Fatalf("excluded %s admitted or wrong failure: %v", kind, err)
			}
		})
	}
}

func TestInventoryPytestCacheLinksCannotSatisfySource(t *testing.T) {
	for _, target := range []string{".pytest_cache/README.md", ".pytest_cache", "./.pytest_cache/README.md", "docs/../.pytest_cache/README.md", ".pytest_cache/alias/README.md", "private.txt"} {
		t.Run(target, func(t *testing.T) {
			root, inventory, _ := pytestCacheFixture(t)
			if err := os.Symlink(".", filepath.Join(root, ".pytest_cache/alias")); err != nil {
				t.Fatal(err)
			}
			if err := os.Symlink(".pytest_cache/README.md", filepath.Join(root, "private.txt")); err != nil {
				t.Fatal(err)
			}
			writeInventorySource(t, root, "README.md", "[Guide](docs/guide.md)\n[private]("+target+")\n")
			report, err := CheckInventory(root, inventory)
			if err != nil || report.Green() || len(report.DeadLinks) != 1 {
				t.Fatalf("excluded target satisfied source link: %+v %v", report, err)
			}
		})
	}
}

func TestInventoryPytestCacheOrdinaryLinksRemainValid(t *testing.T) {
	root, inventory, _ := pytestCacheFixture(t)
	writeInventorySource(t, root, ".pytest_cache-copy/private.txt", "ordinary resource\n")
	if err := os.Symlink("README.md", filepath.Join(root, "ordinary.txt")); err != nil {
		t.Fatal(err)
	}
	writeInventorySource(t, root, "README.md", "[Guide](docs/guide.md)\n[near-prefix](.pytest_cache-copy/private.txt)\n[ordinary](ordinary.txt)\n")
	report, err := CheckInventory(root, inventory)
	if err != nil || !report.Green() || report.Files != 2 {
		t.Fatalf("ordinary link semantics changed: %+v %v", report, err)
	}
}

func TestCheckGitRouteRemainsUnchangedWithPytestCache(t *testing.T) {
	root, inventory, _ := pytestCacheFixture(t)
	writeInventorySource(t, root, "README.md", "[Guide](docs/guide.md)\n[private](.pytest_cache/README.md)\n")
	report, err := Check(root)
	if err != nil || !report.Green() {
		t.Fatalf("developer Git route changed: %+v %v", report, err)
	}
	report, err = CheckInventory(root, inventory)
	if err != nil || len(report.DeadLinks) != 1 {
		t.Fatalf("inventory did not protect excluded link: %+v %v", report, err)
	}
}
