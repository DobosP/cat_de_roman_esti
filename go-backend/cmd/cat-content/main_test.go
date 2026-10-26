package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestOutFlagRequiresExplicitProspectiveCommand(t *testing.T) {
	originalExport := exportContent
	defer func() { exportContent = originalExport }()
	exportCalls := 0
	exportContent = func(string, bool) error {
		exportCalls++
		return nil
	}

	for _, tc := range []struct {
		name string
		args []string
	}{
		{name: "default-separated", args: []string{"--out", filepath.Join(t.TempDir(), "default.json")}},
		{name: "default-equals", args: []string{"--out="}},
		{name: "export-separated", args: []string{"export", "--out", filepath.Join(t.TempDir(), "export.json")}},
		{name: "export-equals", args: []string{"export", "--out="}},
		{name: "validate", args: []string{"validate", "--out", filepath.Join(t.TempDir(), "validate.json")}},
		{name: "validate-fixture", args: []string{"validate-fixture", "--out="}},
		{name: "validate-pack", args: []string{"validate-pack", "--out", filepath.Join(t.TempDir(), "pack.json")}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			before := exportCalls
			err := run(tc.args)
			if err == nil || !strings.Contains(err.Error(), "flag provided but not defined: -out") {
				t.Fatalf("irrelevant --out was not rejected by parsing: %v", err)
			}
			if exportCalls != before {
				t.Fatal("Export was invoked for rejected --out")
			}
			for _, arg := range tc.args {
				if strings.HasSuffix(arg, ".json") {
					if _, statErr := os.Stat(arg); !os.IsNotExist(statErr) {
						t.Fatalf("rejected --out created a file: %s (%v)", arg, statErr)
					}
				}
			}
		})
	}
}

func TestProspectiveRejectsOtherCommandFlags(t *testing.T) {
	for _, arg := range []string{"--check", "--check=true"} {
		if err := run([]string{"prospective-lant-captions", arg}); err == nil || !strings.Contains(err.Error(), "flag provided but not defined: -check") {
			t.Fatalf("prospective command accepted irrelevant %s: %v", arg, err)
		}
	}
}
