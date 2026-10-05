package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestInstalledAuthorityOutputRefusesIncompleteOrMixedModes(t *testing.T) {
	original := os.Args
	t.Cleanup(func() { os.Args = original })
	for _, args := range [][]string{
		{"quick"},
		{"world", "--write"},
		{"extensions", "--check"},
		{"quick", "--candidate-out", "unused.json"},
		{"all"},
		{"reserve"},
	} {
		out := filepath.Join(t.TempDir(), "authority.json")
		os.Args = append(append([]string{"cat-content-rail"}, args...), "--installed-authority-out", out)
		err := run()
		if err == nil || !strings.Contains(err.Error(), "installed-authority output requires") {
			t.Fatal("draft metadata bypassed exact complete independent evidence or mode separation", args, err)
		}
		if _, err = os.Stat(out); !os.IsNotExist(err) {
			t.Fatal("refused authority mode created an output", args, err)
		}
	}
}
