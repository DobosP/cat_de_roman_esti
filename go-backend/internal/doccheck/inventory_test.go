package doccheck

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"testing"
)

func inventoryFixture(t *testing.T) (string, string, []string) {
	t.Helper()
	root := t.TempDir()
	paths := []string{"README.md", "docs/guide.md", "docs/reviews/old.md"}
	writeInventorySource(t, root, paths[0], "[Guide](docs/guide.md)\n")
	writeInventorySource(t, root, paths[1], "# Current guide\n")
	// Historical policy findings remain report-only after inventory admission.
	writeInventorySource(t, root, paths[2], "Opus 4.1\nops resume\n[old](missing.md)\n")
	inventory := filepath.Join(root, "docs/tracked-markdown.json")
	writeInventory(t, inventory, paths)
	return root, inventory, paths
}

func writeInventorySource(t *testing.T, root, name, text string) {
	t.Helper()
	file := filepath.Join(root, filepath.FromSlash(name))
	if err := os.MkdirAll(filepath.Dir(file), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(file, []byte(text), 0600); err != nil {
		t.Fatal(err)
	}
}

func writeInventory(t *testing.T, file string, paths []string) {
	t.Helper()
	raw, err := json.Marshal(struct {
		Schema int      `json:"schema"`
		Paths  []string `json:"paths"`
	}{Schema: 1, Paths: paths})
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(file, raw, 0600); err != nil {
		t.Fatal(err)
	}
}

func TestInventoryValidWithoutGitAndHistoryReportOnly(t *testing.T) {
	root, inventory, _ := inventoryFixture(t)
	for name := range generatedDirectories {
		writeInventorySource(t, root, name+"/generated.md", "Opus 4.1\n")
	}
	report, err := CheckInventory(root, inventory)
	if err != nil || !report.Green() || report.Files != 2 {
		t.Fatalf("valid physical inventory: report=%+v err=%v", report, err)
	}
}

func TestInventoryRejectsEmptyOrHistoryOnly(t *testing.T) {
	for _, kind := range []string{"empty-declaration", "zero-physical", "history-only"} {
		t.Run(kind, func(t *testing.T) {
			root := t.TempDir()
			inventory := filepath.Join(root, "tracked-markdown.json")
			paths := []string{}
			switch kind {
			case "zero-physical":
				paths = []string{"README.md"}
			case "history-only":
				paths = []string{"docs/reviews/old.md"}
				writeInventorySource(t, root, paths[0], "# Historical review\n")
			}
			writeInventory(t, inventory, paths)
			if _, err := CheckInventory(root, inventory); err == nil {
				t.Fatal("empty or history-only inventory admitted")
			}
		})
	}
}

func TestInventoryRejectsStaleSourceSet(t *testing.T) {
	for _, change := range []string{"addition", "deletion"} {
		t.Run(change, func(t *testing.T) {
			root, inventory, _ := inventoryFixture(t)
			if change == "addition" {
				writeInventorySource(t, root, "unlisted.md", "# New source\n")
			} else if err := os.Remove(filepath.Join(root, "docs/guide.md")); err != nil {
				t.Fatal(err)
			}
			if _, err := CheckInventory(root, inventory); err == nil {
				t.Fatal("stale inventory admitted")
			}
		})
	}
}

func TestInventoryRejectsMalformedAndUnsafeInput(t *testing.T) {
	inputs := []string{
		`{"schema":1,"paths":["../escape.md"]}`,
		`{"schema":1,"paths":["/absolute.md"]}`,
		`{"schema":1,"paths":["docs/../README.md"]}`,
		`{"schema":1,"paths":["C:\\escape.md"]}`,
		`{"schema":1,"paths":["README.md","README.md"]}`,
		`{"schema":1,"paths":["docs/guide.md","README.md"]}`,
		`{"schema":1,"paths":["README.txt"]}`,
		`{"schema":2,"paths":[]}`,
		`{"schema":1,"paths":null}`,
		`{"schema":1,"paths":[],"skip":["docs"]}`,
		`{"schema":1,"schema":1,"paths":[]}`,
		`{"schema":1,"paths":[]} {}`,
		`{"schema":1,"paths":[`,
		"{\"schema\":1,\"paths\":[\"\xff.md\"]}",
		strings.Repeat(" ", maxInventoryBytes+1),
	}
	for i, raw := range inputs {
		t.Run(fmt.Sprint(i), func(t *testing.T) {
			if _, err := decodeInventory([]byte(raw)); err == nil {
				t.Fatal("unsafe or malformed inventory admitted")
			}
		})
	}
	paths := make([]string, maxInventoryPaths+1)
	for i := range paths {
		paths[i] = fmt.Sprintf("%05d.md", i)
	}
	raw, err := json.Marshal(struct {
		Schema int      `json:"schema"`
		Paths  []string `json:"paths"`
	}{Schema: 1, Paths: paths})
	if err != nil {
		t.Fatal(err)
	}
	if _, err = decodeInventory(raw); err == nil {
		t.Fatal("excess path count admitted")
	}
}

func TestInventoryRejectsAliases(t *testing.T) {
	for _, kind := range []string{"Markdown", "directory", "inventory", "root"} {
		t.Run(kind, func(t *testing.T) {
			root, inventory, _ := inventoryFixture(t)
			var link, target string
			switch kind {
			case "Markdown":
				link, target = filepath.Join(root, "alias.md"), filepath.Join(root, "README.md")
			case "directory":
				link, target = filepath.Join(root, "alias"), filepath.Join(root, "docs")
			case "inventory":
				link, target = filepath.Join(root, "inventory-alias.json"), inventory
				inventory = link
			case "root":
				link, target = filepath.Join(t.TempDir(), "root-alias"), root
			}
			if err := os.Symlink(target, link); err != nil {
				t.Fatal("inventory alias contract requires symlink support:", err)
			}
			if kind == "root" {
				root, inventory = link, filepath.Join(link, "docs/tracked-markdown.json")
			}
			if _, err := CheckInventory(root, inventory); err == nil {
				t.Fatal("aliased inventory or Markdown source admitted")
			}
		})
	}
}

func TestInventoryPreservesAllCurrentPolicies(t *testing.T) {
	root, inventory, paths := inventoryFixture(t)
	writeInventorySource(t, root, "docs/guide.md", "Opus 4.1\nops resume\n[missing](missing.txt)\n")
	writeInventorySource(t, root, "README.md", "# Root\n")
	writeInventorySource(t, root, "CLAUDE.md", strings.Repeat("line\n", 13))
	paths = append(paths, "CLAUDE.md")
	sort.Strings(paths)
	writeInventory(t, inventory, paths)
	report, err := CheckInventory(root, inventory)
	if err != nil {
		t.Fatal(err)
	}
	if report.Green() || len(report.DeadLinks) != 1 || len(report.StaleTerms) != 1 ||
		len(report.RetiredVerbs) != 1 || len(report.Orphans) != 1 || len(report.Budgets) != 1 {
		t.Fatalf("inventory route lost a current policy: %+v", report)
	}
}

// These are fixture-only proposal tests, never canonical campaign evidence.
func gitInventoryFixture(t *testing.T) (string, string, []string) {
	t.Helper()
	root, inventory, paths := inventoryFixture(t)
	inventoryGit(t, root, "init", "--quiet")
	writeInventorySource(t, root, ".gitignore", ".venv/\n")
	inventoryGit(t, root, "add", "--", ".gitignore", "README.md", "docs")
	return root, inventory, paths
}

func inventoryGit(t *testing.T, root string, args ...string) {
	t.Helper()
	args = append([]string{"-C", root}, args...)
	if raw, err := exec.Command("git", args...).CombinedOutput(); err != nil {
		t.Fatalf("fixture git %v: %s: %v", args, raw, err)
	}
}

func virtualenvAlias(t *testing.T, root, name string) {
	t.Helper()
	writeInventorySource(t, root, name+"/lib/private.md", "Opus 4.1\n")
	if err := os.Symlink("lib", filepath.Join(root, filepath.FromSlash(name), "lib64")); err != nil {
		t.Fatal("fixture requires symlink support:", err)
	}
}

func TestInventoryCanonicalIgnoredVirtualenv(t *testing.T) {
	root, inventory, _ := gitInventoryFixture(t)
	virtualenvAlias(t, root, ".venv")
	report, err := CheckInventory(root, inventory)
	if err != nil || !report.Green() || report.Files != 2 {
		t.Fatalf("canonical ignored, untracked .venv: %+v %v", report, err)
	}
}

func TestInventoryVirtualenvExceptionIsNarrow(t *testing.T) {
	for _, kind := range []string{"unignored", "tracked-markdown", "tracked-nonmarkdown", "nested", "other-ignored", "no-git", "root-alias", "global-rule"} {
		t.Run(kind, func(t *testing.T) {
			root, inventory, _ := gitInventoryFixture(t)
			name := ".venv"
			switch kind {
			case "unignored":
				writeInventorySource(t, root, ".gitignore", "# no exemption\n")
			case "nested":
				name = "source/.venv"
			case "other-ignored":
				name = "venv"
				writeInventorySource(t, root, ".gitignore", "venv/\n")
			case "no-git":
				root, inventory, _ = inventoryFixture(t)
				writeInventorySource(t, root, ".gitignore", ".venv/\n")
			case "global-rule":
				writeInventorySource(t, root, ".gitignore", "# no root rule\n")
				writeInventorySource(t, root, ".git/info/exclude", ".venv/\n")
			case "root-alias":
				target := t.TempDir()
				if err := os.Symlink(target, filepath.Join(root, ".venv")); err != nil {
					t.Fatal(err)
				}
			}
			if kind != "root-alias" {
				virtualenvAlias(t, root, name)
			}
			switch kind {
			case "tracked-markdown":
				inventoryGit(t, root, "add", "-f", "--", ".venv/lib/private.md")
			case "tracked-nonmarkdown":
				writeInventorySource(t, root, ".venv/pyvenv.cfg", "fixture\n")
				inventoryGit(t, root, "add", "-f", "--", ".venv/pyvenv.cfg")
			}
			if _, err := CheckInventory(root, inventory); err == nil || !strings.Contains(err.Error(), "alias refused") {
				t.Fatalf("%s source directory alias admitted or wrong failure: %v", kind, err)
			}
		})
	}
}

func TestInventoryVirtualenvEntriesRemainExcluded(t *testing.T) {
	root, inventory, paths := gitInventoryFixture(t)
	virtualenvAlias(t, root, ".venv")
	paths = append(paths, ".venv/lib/private.md")
	sort.Strings(paths)
	writeInventory(t, inventory, paths)
	if _, err := CheckInventory(root, inventory); err == nil || !strings.Contains(err.Error(), "differs from physical source set") {
		t.Fatalf("excluded .venv source entry admitted: %v", err)
	}
}

func TestInventoryCannotResideInExcludedVirtualenv(t *testing.T) {
	root, _, paths := gitInventoryFixture(t)
	virtualenvAlias(t, root, ".venv")
	inventory := filepath.Join(root, ".venv/inventory.json")
	writeInventory(t, inventory, paths)
	if _, err := CheckInventory(root, inventory); err == nil || !strings.Contains(err.Error(), "cannot be inside excluded .venv") {
		t.Fatalf("excluded .venv inventory file admitted: %v", err)
	}
}

func TestInventoryVirtualenvLinksCannotSatisfySource(t *testing.T) {
	for _, target := range []string{".venv/lib/private.md", ".venv/lib64/private.md", ".venv", "./.venv/lib/private.md", "private.txt"} {
		t.Run(target, func(t *testing.T) {
			root, inventory, _ := gitInventoryFixture(t)
			virtualenvAlias(t, root, ".venv")
			if target == "private.txt" {
				if err := os.Symlink(".venv/lib/private.md", filepath.Join(root, target)); err != nil {
					t.Fatal(err)
				}
			}
			writeInventorySource(t, root, "README.md", "[Guide](docs/guide.md)\n[private]("+target+")\n")
			report, err := CheckInventory(root, inventory)
			if err != nil || report.Green() || len(report.DeadLinks) != 1 {
				t.Fatalf("excluded .venv target satisfied source link: %+v %v", report, err)
			}
		})
	}
}

func TestInventoryIgnoredVirtualenvDoesNotRelaxSourceAliases(t *testing.T) {
	for _, kind := range []string{"markdown", "directory", "tracked-markdown", "tracked-directory"} {
		t.Run(kind, func(t *testing.T) {
			root, inventory, _ := gitInventoryFixture(t)
			virtualenvAlias(t, root, ".venv")
			name, target := "alias.md", "README.md"
			if strings.Contains(kind, "directory") {
				name, target = "alias", "docs"
			}
			if err := os.Symlink(target, filepath.Join(root, name)); err != nil {
				t.Fatal(err)
			}
			if strings.HasPrefix(kind, "tracked-") {
				inventoryGit(t, root, "add", "--", name)
			}
			if _, err := CheckInventory(root, inventory); err == nil || !strings.Contains(err.Error(), "alias refused") {
				t.Fatalf("ordinary source alias admitted: %v", err)
			}
		})
	}
}

func TestInventoryUnexcludedVirtualenvRemainsSource(t *testing.T) {
	for _, tracked := range []bool{false, true} {
		t.Run(fmt.Sprint(tracked), func(t *testing.T) {
			root, inventory, paths := gitInventoryFixture(t)
			writeInventorySource(t, root, ".venv/source.md", "# Source\n")
			if tracked {
				inventoryGit(t, root, "add", "-f", "--", ".venv/source.md")
			} else {
				writeInventorySource(t, root, ".gitignore", "# unignored source\n")
			}
			paths = append(paths, ".venv/source.md")
			sort.Strings(paths)
			writeInventory(t, inventory, paths)
			report, err := CheckInventory(root, inventory)
			if err != nil || !report.Green() || report.Files != 3 {
				t.Fatalf("ordinary .venv source behavior changed: %+v %v", report, err)
			}
		})
	}
}

func TestInventoryOrdinaryLinkStillWorksWithExcludedVirtualenv(t *testing.T) {
	root, inventory, _ := gitInventoryFixture(t)
	virtualenvAlias(t, root, ".venv")
	writeInventorySource(t, root, ".venv-copy/private.txt", "ordinary non-source resource\n")
	if err := os.Symlink("README.md", filepath.Join(root, "ordinary.txt")); err != nil {
		t.Fatal(err)
	}
	writeInventorySource(t, root, "README.md", "[Guide](docs/guide.md)\n[near-prefix](.venv-copy/private.txt)\n[ordinary](ordinary.txt)\n")
	report, err := CheckInventory(root, inventory)
	if err != nil || !report.Green() || report.Files != 2 {
		t.Fatalf("ordinary links changed: %+v %v", report, err)
	}
}
