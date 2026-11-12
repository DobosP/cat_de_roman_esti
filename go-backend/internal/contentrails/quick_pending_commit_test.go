//go:build linux

package contentrails

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/testfixture"
)

func TestQuickPendingInputMutationBeforeFDLinkIsRefusedAndCleanedUnderGuard(t *testing.T) {
	dir := testfixture.NativePendingDir(t)
	input, out := filepath.Join(dir, "input"), filepath.Join(dir, "pending.json")
	if err := os.WriteFile(input, []byte("frozen"), 0600); err != nil {
		t.Fatal(err)
	}
	set, err := contentops.CaptureRegularReadSet([]string{input})
	if err != nil {
		t.Fatal(err)
	}
	const changedInput = "changed before fd link"
	linked := false
	err = contentbuild.WritePrivatePendingArtifact(out, []byte("complete pending bundle"), func(commit func() error) error {
		return contentops.GuardedTransaction(dir, nil, set, func() error {
			if _, err := os.Stat(filepath.Join(dir, ".cat-content-ops.lock")); err != nil {
				return err
			}
			// This mutation occurs after the guard's first verification but
			// before the fd link. The post-commit verification must reject it.
			if err := os.WriteFile(input, []byte(changedInput), 0600); err != nil {
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
	if !linked || err == nil || err.Error() != "strict pending readset changed: "+input {
		t.Fatal("expected readset refusal after the guarded fd link", linked, err)
	}
	actual, err := os.ReadFile(input)
	if err != nil || string(actual) != changedInput {
		t.Fatal("input mutation did not persist", err)
	}
	if _, err := os.Lstat(out); !os.IsNotExist(err) {
		t.Fatal("owned output survived changed input", err)
	}
	if _, err := os.Lstat(filepath.Join(dir, ".cat-content-ops.lock")); !os.IsNotExist(err) {
		t.Fatal("guard lock leaked", err)
	}
}
