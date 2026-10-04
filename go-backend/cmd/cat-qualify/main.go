// cat-qualify captures/replays bounded HTTP contracts and runs anonymous release
// smoke and fixed-workload benchmarks without Python or Rust tooling.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpgolden"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"
)

func writeJSON(path string, v any) error {
	raw, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if path == "" {
		_, err = os.Stdout.Write(raw)
		return err
	}
	if err = os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0600)
}
func run() error {
	if len(os.Args) < 2 {
		return fmt.Errorf("usage: cat-qualify parity|capture|replay|smoke|benchmark [flags]")
	}
	mode := os.Args[1]
	flags := flag.NewFlagSet(mode, flag.ContinueOnError)
	origin := flags.String("url", "", "explicit anonymous HTTP(S) origin")
	binary := flags.String("binary", "", "native server replay executable (parity/replay only)")
	input := flags.String("input", "", "source-bound JSON or .gz corpus for replay")
	output := flags.String("output", "", "capture corpus output file")
	report := flags.String("report", "", "aggregate qualification receipt file")
	reference := flags.String("reference", "", "explicit captured reference description")
	staticRoot := flags.String("static-root", "cat_de_roman_esti/web/static", "release static tree for smoke byte verification")
	timeout := flags.Duration("timeout", 2*time.Minute, "whole qualification timeout, at most 10m")
	flows := flags.Int("flows", 200, "benchmark measured flows, 1..900")
	warmup := flags.Int("warmup-flows", 24, "benchmark warmup flows, 0..100")
	concurrency := flags.Int("concurrency", 1, "benchmark concurrency, 1..64")
	workload := flags.String("workload", "journeys", "benchmark creates or journeys")
	if err := flags.Parse(os.Args[2:]); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return fmt.Errorf("unexpected positional arguments")
	}
	if *timeout <= 0 || *timeout > 10*time.Minute {
		return fmt.Errorf("timeout must be positive and at most 10m")
	}
	if *origin != "" && *binary != "" {
		return fmt.Errorf("choose one explicit origin or replay binary")
	}
	switch mode {
	case "parity", "capture", "replay", "smoke", "benchmark":
	default:
		return fmt.Errorf("unknown qualification mode %s", mode)
	}
	if (mode == "capture" || mode == "smoke" || mode == "benchmark") && *origin == "" {
		return fmt.Errorf("%s requires an explicit --url", mode)
	}
	if mode == "capture" && (*output == "" || *reference == "") {
		return fmt.Errorf("capture requires --output and --reference")
	}
	if mode == "replay" && *input == "" {
		return fmt.Errorf("replay requires --input")
	}
	data, err := content.Load()
	if err != nil {
		return err
	}
	var transport httpgolden.Transport
	if *origin != "" {
		transport, err = httpgolden.HTTP(*origin)
	} else if *binary != "" {
		transport, err = httpgolden.Binary(*binary)
	} else {
		handler := httpapi.New(data)
		handler.StaticRoot = *staticRoot
		transport = httpgolden.Local(handler)
	}
	if err != nil {
		return err
	}
	limit := 600
	if mode == "parity" || mode == "replay" {
		limit = httpgolden.MaxCases
	}
	if mode == "benchmark" {
		limit = httpgolden.MaxCalls
	}
	client, err := httpgolden.NewClient(transport, limit)
	if err != nil {
		return err
	}
	defer client.Close()
	ctx, cancel := context.WithTimeout(context.Background(), *timeout)
	defer cancel()
	var value any
	switch mode {
	case "parity", "replay":
		var corpus *httpgolden.Corpus
		if mode == "parity" {
			corpus, err = httpgolden.Frozen()
		} else {
			var file *os.File
			file, err = os.Open(*input)
			if err == nil {
				corpus, err = httpgolden.ReadCorpus(file, strings.HasSuffix(*input, ".gz"))
				file.Close()
			}
		}
		if err == nil {
			var result httpgolden.Report
			result, err = httpgolden.Replay(ctx, client, corpus, data)
			if mode == "parity" {
				result.Mode = "independent_parity"
			}
			value = result
		}
	case "capture":
		var corpus *httpgolden.Corpus
		corpus, err = httpgolden.Capture(ctx, client, data, *reference)
		if err == nil {
			err = writeJSON(*output, corpus)
			value = map[string]any{"ok": true, "mode": "capture", "requests": len(corpus.Cases), "reference": corpus.Reference, "independent_reference_verified": false}
		}
	case "smoke":
		value, err = httpgolden.Smoke(ctx, client, data, *staticRoot)
	case "benchmark":
		value, err = httpgolden.Benchmark(ctx, client, data, httpgolden.BenchmarkConfig{Flows: *flows, Warmup: *warmup, Concurrency: *concurrency, Workload: *workload})
	}
	if err != nil {
		return err
	}
	if err = writeJSON(*report, value); err != nil {
		return err
	}
	if *report != "" {
		return writeJSON("", value)
	}
	return nil
}
func main() {
	if err := run(); err != nil {
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"ok": false, "error": err.Error()})
		if err != io.EOF {
			os.Exit(1)
		}
	}
}
