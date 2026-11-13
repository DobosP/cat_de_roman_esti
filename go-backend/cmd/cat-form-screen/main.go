// cat-form-screen is the read-only S1 candidate screen for V5 forms and synonyms.
//
// Run from go-backend:
//
//	go run ./cmd/cat-form-screen --root .. --input /absolute/path/to/batch.json
//
// The input object is {"schema":"cat-form-screen-input-1","items":[...]}. Each
// item has id, kind (form, synonym or diminutive), owner_id and forms (literal
// surface strings). Optional requires and co_landing arrays contain item IDs.
// A co_landing group lists every other member in each item. The current
// registry's dependencies and co_landing_group are enforced even when omitted
// by the proposal. A dependency must already be landed or screen in this
// packet. All members of a co-landing group must screen together.
// This command consumes proposed spellings and writes one result JSON to stdout.
// Exit zero means screening completed. Inspect each item's state and reason_code;
// only screened items have accepted_forms. Exit nonzero means no usable receipt.
//
// Threat model. The orchestrator controls the executable, Cat worktree, paths
// and registry/evidence writes. Proposal bytes are untrusted. Strict, bounded
// UTF-8 JSON rejects duplicate, mis-cased and unknown fields, null forms and
// invalid IDs. Candidate values cannot select filesystem paths, authorize a
// hold release or write any file. Root-scoped reads check file type and identity;
// input symlinks and special files are refused. A same-user process replacing
// the trusted executable or authority tree concurrently is outside this model.
// Receipts hash the exact input, executable, registry, bundle and other authority
// bytes. They are private screen records. The orchestrator re-runs the screen
// from trusted inputs at assembly; review, sources and installation have their
// own proof requirements.
//
// The structured exclusions, historical graph-candidate fields, effective
// journal and explicitly bound negative test assertions are screened here.
// Unindexed legacy assertions and prose still require independent inspection,
// and a new diminutive mislabelled as a form
// still requires source reviewers to catch the word-family error. The fuzzy
// check compares the actual native resolver before and after the whole survivor
// batch on candidate inputs, deny-listed and pinned probes, and deletions and
// adjacent transpositions at the first, middle and final character of each key.
// Existing owner changes block the item. The all-Cald-target resolver diff and
// HTTP checks still run at S7–S9. The inbound check applies to eligible Cald targets;
// a form adds no graph predecessors.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"slices"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
)

const (
	inputSchema  = "cat-form-screen-input-1"
	resultSchema = "cat-form-screen-result-1"
	maxForms     = 100
	maxInput     = 128 << 10
	maxAuthority = 32 << 20
)

var identifier = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9_.:-]{0,191}$`)

type batch struct {
	Schema string     `json:"schema"`
	Items  []proposal `json:"items"`
}

type proposal struct {
	ID        string   `json:"id"`
	Kind      string   `json:"kind"`
	OwnerID   string   `json:"owner_id"`
	Forms     []string `json:"forms"`
	Requires  []string `json:"requires"`
	CoLanding []string `json:"co_landing"`
}

type receipt struct {
	Schema       string            `json:"schema"`
	Bindings     map[string]string `json:"bindings"`
	Items        []itemResult      `json:"items"`
	FuzzyChanges []fuzzyChange     `json:"fuzzy_changes"`
}

type itemResult struct {
	ID            string       `json:"id"`
	Kind          string       `json:"kind"`
	OwnerID       string       `json:"owner_id"`
	State         string       `json:"state"`
	Reason        string       `json:"reason_code"`
	AcceptedForms []string     `json:"accepted_forms"`
	Forms         []formResult `json:"forms"`
}

type formResult struct {
	Surface          string   `json:"surface"`
	Key              string   `json:"key"`
	Reason           string   `json:"reason_code"`
	ExactOwner       string   `json:"exact_owner"`
	FuzzyOwner       string   `json:"fuzzy_owner"`
	ProspectiveOwner string   `json:"prospective_owner"`
	Refs             []string `json:"refs"`
}

type fuzzyChange struct {
	Probe       string   `json:"probe"`
	BeforeOwner string   `json:"before_owner"`
	AfterOwner  string   `json:"after_owner"`
	ItemIDs     []string `json:"item_ids"`
}

func main() {
	if err := run(os.Args[1:], os.Stdout, os.Stderr); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(args []string, out, stderr io.Writer) error {
	flags := flag.NewFlagSet("cat-form-screen", flag.ContinueOnError)
	flags.SetOutput(stderr)
	rootPath := flags.String("root", "", "trusted Cat worktree")
	inputPath := flags.String("input", "", "candidate JSON file")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 || *rootPath == "" || *inputPath == "" {
		return fmt.Errorf("usage: cat-form-screen --root WORKTREE --input CANDIDATES.json")
	}
	absoluteInput, err := filepath.Abs(*inputPath)
	if err != nil {
		return err
	}
	inputDir, err := os.OpenRoot(filepath.Dir(absoluteInput))
	if err != nil {
		return err
	}
	defer inputDir.Close()
	input, err := readRegular(inputDir, filepath.Base(absoluteInput), maxInput)
	if err != nil {
		return fmt.Errorf("input: %w", err)
	}
	items, err := decodeBatch(input)
	if err != nil {
		return fmt.Errorf("input: %w", err)
	}

	root, err := os.OpenRoot(*rootPath)
	if err != nil {
		return err
	}
	defer root.Close()
	authority, bindings, err := loadAuthority(root)
	if err != nil {
		return fmt.Errorf("authority: %w", err)
	}
	bindings["input_sha256"] = contentbuild.SHA256(input)
	if bindings["executable_sha256"], err = executableHash(); err != nil {
		return fmt.Errorf("tool provenance: %w", err)
	}

	results, changes := authority.screen(items)
	return json.NewEncoder(out).Encode(receipt{resultSchema, bindings, results, changes})
}

func exactFields(raw []byte, required, optional []string) (map[string]json.RawMessage, error) {
	var fields map[string]json.RawMessage
	if err := json.Unmarshal(raw, &fields); err != nil || fields == nil {
		return nil, fmt.Errorf("expected a JSON object")
	}
	for _, key := range required {
		if len(fields[key]) == 0 || bytes.Equal(fields[key], []byte("null")) {
			return nil, fmt.Errorf("missing or null required field %q", key)
		}
	}
	for _, key := range optional {
		if raw, exists := fields[key]; exists {
			if bytes.Equal(raw, []byte("null")) {
				return nil, fmt.Errorf("optional field %q cannot be null", key)
			}
			delete(fields, key)
		}
	}
	if len(fields) != len(required) {
		return nil, fmt.Errorf("unknown JSON field")
	}
	return fields, nil
}

func decodeBatch(raw []byte) ([]proposal, error) {
	if err := strictjson.Validate(raw); err != nil {
		return nil, err
	}
	fields, err := exactFields(raw, []string{"schema", "items"}, nil)
	if err != nil {
		return nil, err
	}
	var schema string
	var rows []json.RawMessage
	if json.Unmarshal(fields["schema"], &schema) != nil || schema != inputSchema ||
		json.Unmarshal(fields["items"], &rows) != nil || len(rows) == 0 || len(rows) > maxForms {
		return nil, fmt.Errorf("expected %s with 1–%d items", inputSchema, maxForms)
	}
	seen := map[string]bool{}
	total := 0
	items := make([]proposal, 0, len(rows))
	for index, row := range rows {
		fields, err := exactFields(row, []string{"id", "kind", "owner_id", "forms"}, []string{"requires", "co_landing"})
		if err != nil {
			return nil, fmt.Errorf("item %d: %w", index+1, err)
		}
		var surfaces []*string
		if err := json.Unmarshal(fields["forms"], &surfaces); err != nil || slices.Contains(surfaces, nil) {
			return nil, fmt.Errorf("forms must contain only strings at item %d", index+1)
		}
		var item proposal
		if json.Unmarshal(row, &item) != nil || !identifier.MatchString(item.ID) || seen[item.ID] ||
			!identifier.MatchString(item.OwnerID) || len(item.Forms) == 0 ||
			len(item.Requires) > maxForms || len(item.CoLanding) > maxForms {
			return nil, fmt.Errorf("invalid shape or duplicate identity at item %d", index+1)
		}
		if item.Kind != "form" && item.Kind != "synonym" && item.Kind != "diminutive" {
			return nil, fmt.Errorf("invalid kind at item %d", index+1)
		}
		for _, references := range [][]string{item.Requires, item.CoLanding} {
			unique := map[string]bool{item.ID: true}
			for _, ref := range references {
				if !identifier.MatchString(ref) || unique[ref] {
					return nil, fmt.Errorf("invalid, duplicate or self-referential dependency at item %d", index+1)
				}
				unique[ref] = true
			}
		}
		total += len(item.Forms)
		if total > maxForms {
			return nil, fmt.Errorf("candidate input exceeds %d forms", maxForms)
		}
		seen[item.ID] = true
		items = append(items, item)
	}
	return items, nil
}

// The orchestrator controls the paths. Root confines subordinate opens and
// Lstat refuses links and special files before opening them.
func readRegular(root *os.Root, name string, max int64) ([]byte, error) {
	if !fs.ValidPath(name) {
		return nil, fmt.Errorf("invalid local path")
	}
	rel := filepath.FromSlash(name)
	prior, err := root.Lstat(rel)
	if err != nil {
		return nil, err
	}
	if !prior.Mode().IsRegular() || prior.Size() > max {
		return nil, fmt.Errorf("%s is not a bounded regular file", name)
	}
	file, err := root.Open(rel)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	opened, err := file.Stat()
	if err != nil || !opened.Mode().IsRegular() || !os.SameFile(prior, opened) {
		return nil, fmt.Errorf("%s changed before reading", name)
	}
	raw, err := io.ReadAll(io.LimitReader(file, max+1))
	if err != nil {
		return nil, err
	}
	after, err := file.Stat()
	if err != nil || int64(len(raw)) != opened.Size() || opened.Size() != after.Size() ||
		!opened.ModTime().Equal(after.ModTime()) || int64(len(raw)) > max {
		return nil, fmt.Errorf("%s changed during reading or exceeds its bound", name)
	}
	return raw, nil
}

func executableHash() (string, error) {
	name, err := os.Executable()
	if err != nil {
		return "", err
	}
	name, err = filepath.EvalSymlinks(name)
	if err != nil {
		return "", err
	}
	dir, err := os.OpenRoot(filepath.Dir(name))
	if err != nil {
		return "", err
	}
	defer dir.Close()
	raw, err := readRegular(dir, filepath.Base(name), 64<<20)
	if err != nil {
		return "", err
	}
	return contentbuild.SHA256(raw), nil
}
