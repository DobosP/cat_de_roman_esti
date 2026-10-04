// cat-roedu is a bounded read-only transport smoke/fixture export operator.
package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/hopcli"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/roeduclient"
	"os"
	"path/filepath"
	"time"
)

func write(path string, data []byte) error {
	if path == "" {
		return errors.New("export requires an explicit --out")
	}
	f, err := os.CreateTemp(filepath.Dir(path), ".roedu-*")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	if err = f.Chmod(0600); err == nil {
		_, err = f.Write(data)
	}
	if err == nil {
		err = f.Sync()
	}
	closeErr := f.Close()
	if err != nil {
		return err
	}
	if closeErr != nil {
		return closeErr
	}
	return os.Rename(name, path)
}
func run() error {
	if len(os.Args) < 2 {
		return errors.New("usage: cat-roedu smoke|export --url <synthetic-or-approved-server> [--out path]")
	}
	op := os.Args[1]
	if op != "smoke" && op != "export" {
		return errors.New("unknown operation")
	}
	f := flag.NewFlagSet(op, flag.ContinueOnError)
	base := f.String("url", "http://127.0.0.1:8077", "RO-EDU base URL")
	out := f.String("out", "", "explicit output file")
	difficulty := f.String("difficulty", "easy", "smoke difficulty")
	category := f.String("category", "", "scope")
	if err := f.Parse(os.Args[2:]); err != nil {
		return err
	}
	if f.NArg() != 0 {
		return errors.New("unexpected argument")
	}
	if *difficulty != "easy" && *difficulty != "hard" {
		return errors.New("difficulty must be easy or hard")
	}
	c, err := roeduclient.New(*base, os.Getenv("ROEDU_API_KEY"), roeduclient.DefaultLimits())
	if err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	filterDifficulty := ""
	if op == "smoke" {
		filterDifficulty = *difficulty
	}
	raw, err := c.Load(ctx, *category, filterDifficulty)
	if err != nil {
		return err
	}
	b, err := hopcli.Parse(raw)
	if err != nil {
		return err
	}
	if op == "smoke" {
		result, err := hopcli.Smoke(b, *difficulty)
		if err != nil {
			return err
		}
		return json.NewEncoder(os.Stdout).Encode(result)
	}
	if len(raw.Nodes) == 0 || len(raw.Edges) == 0 || len(raw.Puzzles) == 0 {
		return errors.New("refusing empty fixture export")
	}
	data, err := json.MarshalIndent(raw, "", "  ")
	if err != nil {
		return err
	}
	if err = write(*out, append(data, '\n')); err != nil {
		return err
	}
	fmt.Printf("fixture exported: %d nodes, %d edges, %d puzzles (legal provenance and page identity retained)\n", len(raw.Nodes), len(raw.Edges), len(raw.Puzzles))
	return nil
}
func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "cat-roedu:", err)
		os.Exit(1)
	}
}
