//go:build linux

package contentrails

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
)

func TestQuickPendingInputMutationBeforeFDLinkIsRefusedAndCleanedUnderGuard(t *testing.T) {
	dir := t.TempDir()
	if err := os.Chmod(dir, 0700); err != nil {
		t.Fatal(err)
	}
	input, out := filepath.Join(dir, "input"), filepath.Join(dir, "pending.json")
	if err := os.WriteFile(input, []byte("frozen"), 0600); err != nil {
		t.Fatal(err)
	}
	set, err := contentops.CaptureRegularReadSet([]string{input})
	if err != nil {
		t.Fatal(err)
	}
	linked := false
	err = contentbuild.WritePrivatePendingArtifact(out, []byte("complete pending bundle"), func(commit func() error) error {
		return contentops.GuardedTransaction(dir, nil, set, func() error {
			if _, err := os.Stat(filepath.Join(dir, ".cat-content-ops.lock")); err != nil {
				return err
			}
			// This mutation occurs after the guard's first verification but
			// before the fd link. The post-commit verification must reject it.
			if err := os.WriteFile(input, []byte("changed before fd link"), 0600); err != nil {
				return err
			}
			if err := commit(); err != nil {
				return err
			}
			if _, err := os.Stat(filepath.Join(dir, ".cat-content-ops.lock")); err != nil {
				return err
			}
			if _, err := os.Stat(out); err != nil {
				return err
			}
			linked = true
			return nil
		})
	})
	if err == nil || !linked {
		t.Fatal("guarded actual fd-link boundary was not exercised/refused", linked, err)
	}
	if _, err := os.Lstat(out); !os.IsNotExist(err) {
		t.Fatal("owned output survived changed input")
	}
	if _, err := os.Lstat(filepath.Join(dir, ".cat-content-ops.lock")); !os.IsNotExist(err) {
		t.Fatal("guard lock leaked")
	}
}
