//go:build linux

package contentbuild

import (
	"os"
	"path/filepath"
	"testing"
)

func TestIndependentPendingRejectsWritableParentBeforeStaging(t *testing.T) {
	dir := filepath.Join(privatePendingTestDir(t), "writable")
	if err := os.Mkdir(dir, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(dir, 0777); err != nil {
		t.Fatal(err)
	}
	output := filepath.Join(dir, "bundle.json")
	err := WritePrivatePendingArtifact(output, []byte("the requested private bundle"), func(func() error) error {
		t.Fatal("writable parent reached the publication guard")
		return nil
	})
	if err == nil || err.Error() != pendingParentModeRefusal {
		t.Fatal("expected writable parent refusal before staging", err)
	}
	entries, err := os.ReadDir(dir)
	if err != nil || len(entries) != 0 {
		t.Fatal("writable parent received a staging entry or output", err)
	}
}
