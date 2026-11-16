// cat-lant-overlap is the read-only S1 near-duplicate screen for Lanț prospects.
//
// Run from go-backend:
//
//	go run ./cmd/cat-lant-overlap --root .. --start n_transilvania --target n_muntii_apuseni
//	go run ./cmd/cat-lant-overlap --root .. --prospects /absolute/path/to/list.json
//	go run ./cmd/cat-lant-overlap --root .. --served-sanity
//
// See README.md for the comparison rules and the threat model.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
)

const (
	schema       = "cat-lant-overlap-1"
	bundlePath   = "go-backend/internal/content/bundled.json"
	maxBundle    = 32 << 20
	maxList      = 1 << 20
	maxProspects = 256
	maxIDBytes   = 128
	maxPar       = 1000
)

type summary struct {
	Prospects      int `json:"prospects"`
	NearDuplicates int `json:"near_duplicates"`
}

type report struct {
	Schema       string   `json:"schema"`
	BundleSHA256 string   `json:"bundle_sha256"`
	ContentHash  string   `json:"content_hash"`
	Mode         string   `json:"mode"`
	ServedBoards int      `json:"served_boards"`
	Prospects    []result `json:"prospects"`
	Summary      summary  `json:"summary"`
}

func main() {
	if err := run(os.Args[1:], os.Stdout, os.Stderr); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(args []string, output, diagnostics io.Writer) error {
	flags := flag.NewFlagSet("cat-lant-overlap", flag.ContinueOnError)
	flags.SetOutput(diagnostics)
	rootPath := flags.String("root", "", "repository root (the checkout holding go-backend/internal/content/bundled.json)")
	start := flags.String("start", "", "prospect start node id")
	target := flags.String("target", "", "prospect target node id")
	par := flags.Int("par", -1, "prospect declared par (default: the shortest distance)")
	list := flags.String("prospects", "", "JSON list of {start,target,par?} prospects")
	sanity := flags.Bool("served-sanity", false, "compare every served board with the rest of the pack")
	if err := flags.Parse(args); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return nil
		}
		return err
	}
	single := *start != "" || *target != "" || *par >= 0
	modes := 0
	for _, on := range []bool{single, *list != "", *sanity} {
		if on {
			modes++
		}
	}
	if flags.NArg() != 0 || *rootPath == "" || modes != 1 || (single && (*start == "" || *target == "")) {
		return errors.New("expected --root and exactly one of --start/--target [--par], --prospects or --served-sanity")
	}
	root, err := os.OpenRoot(*rootPath)
	if err != nil {
		return err
	}
	defer root.Close()
	data, err := readRegular(root, bundlePath, maxBundle)
	if err != nil {
		return fmt.Errorf("bundle: %w", err)
	}
	if err := strictjson.Validate(data); err != nil {
		return fmt.Errorf("bundle: %w", err)
	}
	bundle, err := content.Decode(data)
	if err != nil {
		return err
	}
	a, err := newAnalyzer(bundle)
	if err != nil {
		return err
	}
	out := report{Schema: schema, BundleSHA256: contentbuild.SHA256(data), ServedBoards: len(a.boards), Prospects: []result{}}
	out.ContentHash, _ = bundle.Manifest["content_hash"].(string)
	var work []prospect
	exclude := map[int]string{}
	switch {
	case single:
		out.Mode = "prospect"
		p := prospect{Start: *start, Target: *target}
		if *par >= 0 {
			p.Par = par
		}
		work = []prospect{p}
	case *list != "":
		out.Mode = "prospects"
		raw, err := readPath(*list, maxList)
		if err != nil {
			return fmt.Errorf("prospect list: %w", err)
		}
		if work, err = parseList(raw); err != nil {
			return fmt.Errorf("prospect list: %w", err)
		}
	default:
		out.Mode = "served-sanity"
		for i, b := range a.boards {
			p := prospect{Start: b.start, Target: b.target, Par: &a.boards[i].par}
			work = append(work, p)
			exclude[i] = b.id
		}
	}
	for i, p := range work {
		r, err := a.compare(p, exclude[i])
		if err != nil {
			return err
		}
		out.Summary.Prospects++
		if r.NearDuplicate {
			out.Summary.NearDuplicates++
		}
		out.Prospects = append(out.Prospects, r)
	}
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetIndent("", "  ")
	if err := enc.Encode(out); err != nil {
		return err
	}
	_, err = output.Write(buf.Bytes())
	return err
}

func parseList(raw []byte) ([]prospect, error) {
	if err := strictjson.Validate(raw); err != nil {
		return nil, err
	}
	var work []prospect
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(&work); err != nil {
		return nil, err
	}
	var trailing any
	if d.Decode(&trailing) != io.EOF {
		return nil, errors.New("trailing JSON")
	}
	if len(work) == 0 || len(work) > maxProspects {
		return nil, fmt.Errorf("expected 1 to %d prospects", maxProspects)
	}
	for _, p := range work {
		if p.Start == "" || p.Target == "" || len(p.Start) > maxIDBytes || len(p.Target) > maxIDBytes ||
			(p.Par != nil && (*p.Par < 0 || *p.Par > maxPar)) {
			return nil, errors.New("invalid prospect entry")
		}
	}
	return work, nil
}

// readRegular reads one regular file inside root within its size bound.
func readRegular(root *os.Root, name string, limit int64) ([]byte, error) {
	info, err := root.Lstat(name)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > limit {
		return nil, errors.New("expected a regular file within its size bound")
	}
	f, err := root.Open(name)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return readBounded(f, info, limit)
}

// readPath reads one regular, non-symlink file by path within its size bound.
func readPath(path string, limit int64) ([]byte, error) {
	info, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > limit {
		return nil, errors.New("expected a regular file within its size bound")
	}
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return readBounded(f, info, limit)
}

func readBounded(f *os.File, before os.FileInfo, limit int64) ([]byte, error) {
	actual, err := f.Stat()
	if err != nil {
		return nil, err
	}
	if !actual.Mode().IsRegular() || !os.SameFile(before, actual) {
		return nil, errors.New("file changed before opening")
	}
	data, err := io.ReadAll(io.LimitReader(f, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > limit {
		return nil, errors.New("size bound exceeded")
	}
	return data, nil
}
