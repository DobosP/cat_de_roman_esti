// cat-content is the private native content operator. It never starts a server.
package main

import (
	"flag"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"os"
	"path/filepath"
)

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

var exportContent = contentbuild.Export

func run(args []string) error {
	command := "export"
	if len(args) > 0 && args[0] != "" && args[0][0] != '-' {
		command = args[0]
		args = args[1:]
	}
	if command != "export" && command != "validate" && command != "validate-fixture" && command != "validate-pack" && command != "prospective-lant-captions" {
		return fmt.Errorf("unknown command %s", command)
	}
	f := flag.NewFlagSet("cat-content "+command, flag.ContinueOnError)
	root := f.String("root", "..", "repository source root")
	var check *bool
	var kg, pack, out *string
	switch command {
	case "export":
		check = f.Bool("check", false, "check deterministic export freshness without writing")
	case "validate-fixture":
		kg = f.String("kg", "", "fixture path for a standalone validator")
	case "validate-pack":
		kg = f.String("kg", "", "fixture path for a standalone validator")
		pack = f.String("pack", "", "pack path for a standalone validator")
	case "prospective-lant-captions":
		kg = f.String("kg", "", "explicit prospective fixture path")
		pack = f.String("pack", "", "explicit prospective pack path")
		out = f.String("out", "", "new output path for a private prospective artifact")
	}
	if err := f.Parse(args); err != nil {
		return err
	}
	if f.NArg() != 0 {
		return fmt.Errorf("unexpected positional arguments")
	}
	abs, err := filepath.Abs(*root)
	if err != nil {
		return err
	}
	switch command {
	case "export":
		if err := exportContent(abs, *check); err != nil {
			return err
		}
		fmt.Printf("Native private content %s\n", map[bool]string{true: "current", false: "exported"}[*check])
	case "validate":
		if err := contentbuild.ValidateSources(abs); err != nil {
			return err
		}
		fmt.Println("Native sources GREEN")
	case "validate-fixture":
		path := *kg
		if path == "" {
			path = filepath.Join(abs, "cat_de_roman_esti", "fixtures", "kg_sample.json")
		}
		errors := contentbuild.ValidateFixture(path)
		if len(errors) > 0 {
			return fmt.Errorf("fixture RED: %d error(s), first: %s", len(errors), errors[0])
		}
		fmt.Println("GREEN: fixture is valid (0 errors)")
	case "validate-pack":
		kp, pp := *kg, *pack
		if kp == "" {
			kp = filepath.Join(abs, "cat_de_roman_esti", "fixtures", "kg_sample.json")
		}
		if pp == "" {
			pp = filepath.Join(abs, "cat_de_roman_esti", "fixtures", "games_pack.json")
		}
		errors := contentbuild.ValidatePack(kp, pp)
		if len(errors) > 0 {
			return fmt.Errorf("games pack RED: %d error(s), first: %s", len(errors), errors[0])
		}
		fmt.Println("games pack GREEN")
	case "prospective-lant-captions":
		if *kg == "" || *pack == "" || *out == "" {
			return fmt.Errorf("prospective-lant-captions requires explicit --kg, --pack and --out")
		}
		if err := contentbuild.WriteProspectiveLantCaptions(abs, *kg, *pack, *out); err != nil {
			return err
		}
		fmt.Printf("Unapproved prospective native Lanț captions written to %s\n", *out)
	}
	return nil
}
