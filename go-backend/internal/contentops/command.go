package contentops

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

func Run(args []string, out io.Writer) error {
	if len(args) == 0 {
		return errors.New("usage: cat-content-ops COMMAND [--root ROOT] [--check|--write]; commands: check, import-candidates, critique, build-review, apply-review, audit-projections, rank, derive, delta, submissions")
	}
	command := args[0]
	args = args[1:]
	submission := ""
	if command == "submissions" {
		if len(args) == 0 {
			return errors.New("submissions requires list, stage, promote or reject")
		}
		submission = args[0]
		args = args[1:]
	}
	fs := flag.NewFlagSet("cat-content-ops "+command, flag.ContinueOnError)
	fs.SetOutput(out)
	root := fs.String("root", ".", "local repository/source root")
	dir := fs.String("dir", "", "candidate/review/queue directory")
	idsArg := fs.String("ids", "", "comma-separated exact IDs")
	status := fs.String("status", "pending", "critique status filter")
	game := fs.String("game", "", "critique game filter")
	dossier := fs.String("dossier", "", "dossier directory")
	dossiers := fs.String("dossiers", "", "review dossier directory")
	analyst := fs.String("analyst", "", "authored analyst JSON")
	verifier := fs.String("verifier", "", "authored verifier JSON")
	projection := fs.String("projection-audit", "", "exact live projection audit")
	output := fs.String("out", "", "output directory or JSON file")
	reviews := fs.String("reviews", "", "submission review artifact directory")
	textOutput := fs.Bool("text", false, "concise content inventory delta totals")
	jsonOutput := fs.Bool("json", false, "JSON output (default)")
	baseline := fs.String("baseline", "HEAD", "Git baseline commit/ref")
	strict := fs.Bool("strict", false, "fail on deterministic critique FAIL")
	packOnly := fs.Bool("pack-only", false, "refuse graph mutation")
	write := fs.Bool("write", false, "explicitly write reviewed local files")
	check := fs.Bool("check", false, "read-only check (default)")
	if e := fs.Parse(args); e != nil {
		return e
	}
	if fs.NArg() != 0 {
		return errors.New("unexpected positional argument; use --ids")
	}
	if command == "check" && *write {
		return errors.New("check is read only; --write is refused")
	}
	if *write && *check {
		return errors.New("--write and --check are mutually exclusive")
	}
	resolved, e := filepath.Abs(*root)
	if e != nil {
		return e
	}
	*root = resolved
	ids := []string{}
	if *idsArg != "" {
		ids = strings.Split(*idsArg, ",")
	}
	if *textOutput && *jsonOutput {
		return errors.New("--text and --json are mutually exclusive")
	}
	if command == "delta" {
		report, e := Delta(*root, *baseline)
		if e != nil {
			return e
		}
		if *textOutput {
			_, e = fmt.Fprintln(out, DeltaText(report))
			return e
		}
		return json.NewEncoder(out).Encode(report)
	}
	s, e := LoadSources(*root)
	if e != nil {
		return e
	}
	var result Object
	switch command {
	case "check":
		result, e = s.Check()
	case "import-candidates":
		if !*packOnly || *dir == "" {
			return errors.New("import-candidates requires --dir and --pack-only")
		}
		result, e = s.Import(*dir, *write)
	case "critique":
		if len(ids) == 0 {
			rows, games, err := indexPack(s.Pack)
			if err != nil {
				return err
			}
			for id, r := range rows {
				if (*status == "" || str(r["status"]) == *status) && (*game == "" || games[id] == *game) {
					ids = append(ids, id)
				}
			}
			sort.Strings(ids)
		}
		if *write && *dossier == "" {
			return errors.New("critique --write requires --dossier")
		}
		result, e = s.WriteDossiers(ids, *status, *game, *dossier, *strict, *write)
	case "build-review":
		if *analyst == "" || *verifier == "" || *dossiers == "" || (*write && *output == "") {
			return errors.New("build-review requires --analyst --verifier --dossiers and --out for writes")
		}
		result, e = s.BuildReview(*analyst, *verifier, *dossiers, *projection, *output, *write)
	case "apply-review":
		if *dir == "" {
			return errors.New("apply-review requires --dir")
		}
		result, e = s.ApplyReview(*dir, *write)
	case "audit-projections":
		if len(ids) == 0 || *dossier == "" || (*write && *output == "") {
			return errors.New("audit-projections requires --ids --dossier and --out for writes")
		}
		result, e = s.AuditProjections(ids, *dossier, *output, *write)
	case "submissions":
		if *dir == "" {
			return errors.New("submissions requires --dir")
		}
		result, e = s.Submissions(submission, *dir, ids, *reviews, *write)
	case "rank":
		result, e = s.Rank(*write)
	case "derive":
		result, e = s.Derive(*write)
	default:
		return fmt.Errorf("unknown content operator %s", command)
	}
	if e == nil && !*write {
		e = checkSnapshots(s.Inputs)
	}
	if result != nil {
		encoder := json.NewEncoder(out)
		encoder.SetEscapeHTML(false)
		encoder.SetIndent("", " ")
		if re := encoder.Encode(result); re != nil {
			return re
		}
	}
	return e
}
func Main() {
	if e := Run(os.Args[1:], os.Stdout); e != nil {
		fmt.Fprintln(os.Stderr, "cat-content-ops:", e)
		os.Exit(1)
	}
}
