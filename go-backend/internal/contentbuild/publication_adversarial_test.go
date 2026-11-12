//go:build linux

// Proposed independent refusal control. NOT EXECUTED by this reviewer.
// Run only inside the owning pinned SDK after coordinating cache ownership.
// Add through a Go overlay or copy into the author's next revision; never edit
// frozen source. Current v2 is expected to FAIL this test (returns nil).
package contentbuild

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestIndependentPendingRejectsTemporaryNameSubstitution(t *testing.T) {
	for _, kind := range []string{"regular", "symlink"} {
		t.Run(kind, func(t *testing.T) {
			dir := t.TempDir()
			// Exercise the currently accepted shared-writable parent mode.
			if err := os.Chmod(dir, 0777); err != nil {
				t.Fatal(err)
			}
			output := filepath.Join(dir, "bundle.json")
			replacement := []byte("attacker replacement; not the requested private bundle")
			target := filepath.Join(dir, "attacker-target")
			if err := os.WriteFile(target, replacement, 0644); err != nil {
				t.Fatal(err)
			}
			err := WritePrivatePendingArtifact(output, []byte("the requested private bundle"), func(publish func() error) error {
				entries, err := os.ReadDir(dir)
				if err != nil {
					return err
				}
				temp := ""
				for _, entry := range entries {
					if strings.HasPrefix(entry.Name(), ".quick-pending-") {
						temp = filepath.Join(dir, entry.Name())
					}
				}
				if temp == "" {
					return fmt.Errorf("publication staging name not found")
				}
				if err := os.Remove(temp); err != nil {
					return err
				}
				if kind == "symlink" {
					if err := os.Symlink(target, temp); err != nil {
						return err
					}
				} else if err := os.WriteFile(temp, replacement, 0644); err != nil {
					return err
				}
				return publish()
			})
			if err == nil {
				t.Fatal("published a replacement temporary name instead of the held private inode")
			}
		})
	}
}
