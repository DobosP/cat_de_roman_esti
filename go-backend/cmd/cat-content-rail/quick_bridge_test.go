package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestQuickBridgeDraftRefusesIncompleteMixedAndNonQuickActions(t *testing.T) {
	original := os.Args
	t.Cleanup(func() { os.Args = original })
	for _, args := range [][]string{
		{"quick", "--bridge-draft", "missing"},
		{"world", "--bridge-draft", "missing", "--bridge-frame-sha256", strings.Repeat("a", 64)},
		{"quick", "--bridge-draft", "missing", "--bridge-frame-sha256", strings.Repeat("a", 64), "--write"},
		{"quick", "--bridge-draft", "missing", "--bridge-frame-sha256", strings.Repeat("a", 64), "--source", "source.json"},
		{"quick", "--bridge-draft", "missing", "--bridge-frame-sha256", strings.Repeat("a", 64), "--pending-inventory"},
		{"quick", "--bridge-draft", "missing", "--bridge-frame-sha256", strings.Repeat("a", 64), "--proposal", "proposal.json"},
		{"quick", "--bridge-draft", "missing", "--bridge-frame-sha256", strings.Repeat("a", 64), "--installed-authority-out", "authority.json"},
		{"quick", "--bridge-frame-sha256", strings.Repeat("a", 64)},
	} {
		out := filepath.Join(t.TempDir(), "draft.json")
		os.Args = append(append([]string{"cat-content-rail"}, args...), "--bridge-out", out)
		if err := run(); err == nil || !strings.Contains(err.Error(), "bridge") {
			t.Fatal("bridge draft action escaped its boundary", args, err)
		}
		if _, err := os.Stat(out); !os.IsNotExist(err) {
			t.Fatal("refused bridge action wrote output", args, err)
		}
	}
}

func TestQuickBridgeFullActionsCannotMixOrInventWriteAuthority(t *testing.T) {
	original := os.Args
	t.Cleanup(func() { os.Args = original })
	for _, args := range [][]string{
		{"quick", "--bridge-prepare", "missing", "--bridge-frame-sha256", strings.Repeat("a", 64), "--write"},
		{"quick", "--bridge-propose", "missing", "--bridge-release-sha256", strings.Repeat("a", 64), "--source", "missing"},
		{"quick", "--bridge-install", "missing", "--bridge-install-sha256", strings.Repeat("a", 64), "--bridge-out", "unused"},
		{"quick", "--bridge-view", "missing", "--bridge-member", "source.json", "--write"},
		{"quick", "--bridge-install", "missing"},
		{"world", "--bridge-prepare", "missing", "--bridge-frame-sha256", strings.Repeat("a", 64)},
	} {
		os.Args = append([]string{"cat-content-rail"}, args...)
		if err := run(); err == nil || !strings.Contains(err.Error(), "bridge") {
			t.Fatal("full bridge mode isolation failed", args, err)
		}
	}
}
