// cat-board-view-diff compares private native board views without serving them.
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

const maxBundleBytes = 32 << 20

func main() {
	if err := run(os.Args[1:], os.Stdout, os.Stderr); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(args []string, output, diagnostics io.Writer) error {
	flags := flag.NewFlagSet("cat-board-view-diff", flag.ContinueOnError)
	flags.SetOutput(diagnostics)
	baseline := flags.String("baseline", "", "exact baseline private bundle path")
	baselineSHA := flags.String("baseline-sha256", "", "exact baseline bundle SHA-256")
	candidate := flags.String("candidate", "", "exact candidate private bundle path")
	candidateSHA := flags.String("candidate-sha256", "", "exact candidate bundle SHA-256")
	dryRun := flags.Bool("one-word-dry-run", false, "rebuild private prospective board views and apply the 10-board limit")
	var preview previewFiles
	flags.StringVar(&preview.root, "baseline-root", "", "baseline source checkout for one-word dry run")
	flags.StringVar(&preview.kg, "prospective-kg", "", "exact prospective KG file")
	flags.StringVar(&preview.kgSHA, "prospective-kg-sha256", "", "exact prospective KG SHA-256")
	flags.StringVar(&preview.pack, "prospective-pack", "", "exact rederived prospective pack file")
	flags.StringVar(&preview.packSHA, "prospective-pack-sha256", "", "exact prospective pack SHA-256")
	if err := flags.Parse(args); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return nil
		}
		return err
	}
	if flags.NArg() != 0 || *baseline == "" || !validSHA(*baselineSHA) {
		return errors.New("expected a baseline bundle path and lowercase SHA-256 digest")
	}
	if *dryRun && (*candidate != "" || *candidateSHA != "") {
		return errors.New("dry run takes prospective KG and pack inputs")
	}
	if !*dryRun && (*candidate == "" || !validSHA(*candidateSHA) || preview != (previewFiles{})) {
		return errors.New("S7 comparison requires candidate bundle path and lowercase SHA-256 digest")
	}
	before, err := loadBundle(*baseline, *baselineSHA)
	if err != nil {
		return fmt.Errorf("baseline bundle: %w", err)
	}
	if *dryRun {
		result, err := preview.compare(before)
		if err != nil {
			return fmt.Errorf("one-word dry run: %w", err)
		}
		result.BaselineSHA256 = *baselineSHA
		return writeReport(result, output)
	}
	after := before
	if *baseline != *candidate || *baselineSHA != *candidateSHA {
		after, err = loadBundle(*candidate, *candidateSHA)
		if err != nil {
			return fmt.Errorf("candidate bundle: %w", err)
		}
	}
	result, err := compare(before, after)
	if err != nil {
		return err
	}
	result.BaselineSHA256, result.CandidateSHA256 = *baselineSHA, *candidateSHA
	return writeReport(result, output)
}

func validSHA(value string) bool {
	if len(value) != 64 {
		return false
	}
	for _, c := range value {
		if (c < '0' || c > '9') && (c < 'a' || c > 'f') {
			return false
		}
	}
	return true
}

func readBoundFile(path, sha string, maxBytes int64) ([]byte, error) {
	info, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > maxBytes {
		return nil, errors.New("expected a regular file within its size bound")
	}
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	actual, err := f.Stat()
	if err != nil {
		return nil, err
	}
	if !actual.Mode().IsRegular() || !os.SameFile(info, actual) {
		return nil, errors.New("bundle path changed before opening")
	}
	data, err := io.ReadAll(io.LimitReader(f, maxBytes+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > maxBytes || contentbuild.SHA256(data) != sha {
		return nil, errors.New("exact file SHA-256 mismatch or size bound exceeded")
	}
	return data, nil
}

func loadBundle(path, sha string) (*content.Content, error) {
	data, err := readBoundFile(path, sha, maxBundleBytes)
	if err != nil {
		return nil, err
	}
	if err := strictjson.Validate(data); err != nil {
		return nil, err
	}
	bundle, err := content.Decode(data)
	if err != nil {
		return nil, err
	}
	var rules struct {
		RecipeExtensions map[string]any `json:"recipe_extensions"`
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.UseNumber()
	if err := decoder.Decode(&rules); err != nil {
		return nil, err
	}
	if err := contentbuild.ValidateRecipeExtensions(rules.RecipeExtensions); err != nil {
		return nil, err
	}
	if err := validateBundle(bundle); err != nil {
		return nil, err
	}
	return bundle, nil
}
