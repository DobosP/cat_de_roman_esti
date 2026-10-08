package doccheck

import (
	"encoding/json"
	"fmt"
	"os"
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
		Schema int `json:"schema"`
		Paths []string `json:"paths"`
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
		Schema int `json:"schema"`
		Paths []string `json:"paths"`
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
