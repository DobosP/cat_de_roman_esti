// cat-content-rail is the source-bound native quick/world/recipe/reserve operator.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentrails"
	"os"
	"time"
)

func run() error {
	if len(os.Args) < 2 {
		return fmt.Errorf("usage: cat-content-rail all|quick|world|extensions|reserve --check | --candidate-out PATH | --candidate PATH --factual-review PATH --quality-review PATH --proposal PATH | --audit-catalog PATH --audit-out PATH")
	}
	rail := os.Args[1]
	f := flag.NewFlagSet(rail, flag.ContinueOnError)
	root := f.String("root", "..", "repository root")
	check := f.Bool("check", false, "rebuild unchanged baseline and check exact approved bytes")
	source := f.String("source", "", "native authored JSON; changed source needs version>1 and exact parent_source_sha256")
	candidateOut := f.String("candidate-out", "", "generate source-bound candidate without approvals")
	candidate := f.String("candidate", "", "exact native candidate input")
	factual := f.String("factual-review", "", "complete factual review")
	quality := f.String("quality-review", "", "complete independent quality review")
	proposal := f.String("proposal", "", "explicit saved proposal output")
	auditCatalog := f.String("audit-catalog", "", "exact catalog to audit privately")
	auditOut := f.String("audit-out", "", "explicit native audit output")
	write := f.Bool("write", false, "install only after bound native audit and final independent judgments")
	finalAudit := f.String("live-audit", "", "bound saved native audit")
	finalFactual := f.String("final-factual-review", "", "final factual acceptance")
	finalQuality := f.String("final-quality-review", "", "final quality acceptance")
	pin := f.String("expected-sha256", "", "explicit reviewed output artifact pin for installation")
	if err := f.Parse(os.Args[2:]); err != nil {
		return err
	}
	if f.NArg() != 0 {
		return fmt.Errorf("unexpected positional argument")
	}
	s, err := contentrails.LoadSource(*source)
	if err != nil {
		return err
	}
	if rail == "all" {
		if !*check || *write || *candidateOut != "" || *candidate != "" || *auditCatalog != "" {
			return fmt.Errorf("all requires separate --check only")
		}
		results, err := contentrails.CheckAll(*root, s)
		if err != nil {
			return err
		}
		return json.NewEncoder(os.Stdout).Encode(map[string]any{"ok": true, "rails": results})
	}
	if *check {
		if *write || *candidateOut != "" || *candidate != "" || *auditCatalog != "" {
			return fmt.Errorf("check must be a separate action")
		}
		result, err := contentrails.Check(*root, s, rail)
		if err != nil {
			return err
		}
		return json.NewEncoder(os.Stdout).Encode(result)
	}
	if *candidateOut != "" {
		if *write || *candidate != "" || *auditCatalog != "" {
			return fmt.Errorf("candidate generation must be separate")
		}
		if err = contentrails.ProtectedOutput(*root, *candidateOut, *source); err != nil {
			return err
		}
		value, err := contentrails.Candidate(*root, s, rail, false)
		if err != nil {
			return err
		}
		b, err := contentrails.Render(value)
		if err != nil {
			return err
		}
		if err = contentrails.WriteOutputs([]string{*candidateOut}, b); err != nil {
			return err
		}
		return json.NewEncoder(os.Stdout).Encode(map[string]any{"ok": true, "mode": "candidate", "source_sha256": s.SHA256, "source_version": s.Version})
	}
	if *auditCatalog != "" {
		if *write || *candidate != "" || *auditOut == "" {
			return fmt.Errorf("audit must be separate and requires --audit-out")
		}
		if err = contentrails.ProtectedOutput(*root, *auditOut, *auditCatalog, *source); err != nil {
			return err
		}
		value, err := contentrails.Read(*auditCatalog)
		if err != nil {
			return err
		}
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
		defer cancel()
		audit, err := contentrails.Audit(ctx, *root, rail, value)
		if err != nil {
			return err
		}
		b, err := contentrails.Render(audit)
		if err != nil {
			return err
		}
		if err = contentrails.WriteOutputs([]string{*auditOut}, b); err != nil {
			return err
		}
		return json.NewEncoder(os.Stdout).Encode(map[string]any{"ok": true, "mode": "audit", "rail": rail})
	}
	if rail == "reserve" && *write && *candidate == "" {
		if err = contentrails.InstallReserve(*root, s, *pin); err != nil {
			return err
		}
		return json.NewEncoder(os.Stdout).Encode(map[string]any{"ok": true, "mode": "write", "rail": rail})
	}
	if *write {
		if err = contentrails.InstallProposal(*root, s, rail, *candidate, *factual, *quality, *proposal, *finalAudit, *finalFactual, *finalQuality, *pin, *source); err != nil {
			return err
		}
		return json.NewEncoder(os.Stdout).Encode(map[string]any{"ok": true, "mode": "write", "rail": rail})
	}
	if *candidate == "" || *factual == "" || *quality == "" || *proposal == "" {
		return fmt.Errorf("proposal requires exact candidate, both independent reviews and explicit output")
	}
	if err = contentrails.ProtectedOutput(*root, *proposal, *candidate, *factual, *quality, *finalAudit, *finalFactual, *finalQuality, *source); err != nil {
		return err
	}
	value, err := contentrails.BuildProposal(*root, s, rail, *candidate, *factual, *quality)
	if err != nil {
		return err
	}
	b, err := contentrails.OutputBytes(rail, value)
	if err != nil {
		return err
	}
	if err = contentrails.WriteOutputs([]string{*proposal}, b); err != nil {
		return err
	}
	return json.NewEncoder(os.Stdout).Encode(map[string]any{"ok": true, "mode": map[bool]string{false: "proposal", true: "write"}[*write], "rail": rail})
}
func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "cat-content-rail:", err)
		os.Exit(1)
	}
}
