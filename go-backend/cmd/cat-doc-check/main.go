package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/doccheck"
	"os"
)

func main() {
	root := flag.String("root", "..", "repository root")
	inventory := flag.String("inventory", "", "optional source Markdown inventory, verified against the physical tree")
	flag.Parse()
	if flag.NArg() != 0 {
		fmt.Fprintln(os.Stderr, "unexpected argument")
		os.Exit(2)
	}
	var report doccheck.Report
	var err error
	if *inventory == "" {
		report, err = doccheck.Check(*root)
	} else {
		report, err = doccheck.CheckInventory(*root, *inventory)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err = json.NewEncoder(os.Stdout).Encode(report); err != nil {
		os.Exit(1)
	}
	if !report.Green() {
		os.Exit(1)
	}
}
