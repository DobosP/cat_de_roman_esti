//go:build linux

package contentbuild

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/testfixture"
	"golang.org/x/sys/unix"
)

func TestQuickPendingPublicationIsPrivateAtomicNoReplaceAndCleansFailedGuard(t *testing.T) {
	dir := testfixture.NativePendingDir(t)
	target := filepath.Join(dir, "bundle.json")
	data := []byte("complete private bundle\n")
	pass := func(write func() error) error { return write() }
	if err := WritePrivatePendingArtifact(target, data, pass); err != nil {
		t.Fatal(err)
	}
	info, err := os.Stat(target)
	if err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(target)
	if err != nil || info.Mode().Perm() != 0600 || string(b) != string(data) {
		t.Fatal("private exact output changed", err)
	}
	if err := WritePrivatePendingArtifact(target, []byte("overwrite"), pass); !errors.Is(err, unix.EEXIST) {
		t.Fatal("expected existing output refusal", err)
	}
	b, err = os.ReadFile(target)
	if err != nil || string(b) != string(data) {
		t.Fatal("old output mutated", err)
	}
	failed := filepath.Join(dir, "failed.json")
	guardFailure := errors.New("post-publication stale readset")
	if err := WritePrivatePendingArtifact(failed, data, func(write func() error) error {
		if err := write(); err != nil {
			return err
		}
		b, err := os.ReadFile(failed)
		if err != nil || string(b) != string(data) {
			t.Fatal("guard did not observe the committed artifact", err)
		}
		return guardFailure
	}); !errors.Is(err, guardFailure) {
		t.Fatal("expected post-publication guard failure", err)
	}
	if _, err := os.Lstat(failed); !os.IsNotExist(err) {
		t.Fatal("failed output remained", err)
	}
	entries, err := os.ReadDir(dir)
	if err != nil || len(entries) != 1 {
		t.Fatal("temporary partial output remained", err)
	}
}

func TestQuickPendingPublicationRefusesParentSwapAndSymlinks(t *testing.T) {
	dir, outside := testfixture.NativePendingDir(t), t.TempDir()
	parent := filepath.Join(dir, "parent")
	moved := parent + "-moved"
	if err := os.Mkdir(parent, 0700); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(parent, "bundle.json")
	swapped := false
	err := WritePrivatePendingArtifact(path, []byte("private"), func(write func() error) error {
		if err := os.Rename(parent, moved); err != nil {
			t.Fatal(err)
		}
		if err := os.Symlink(outside, parent); err != nil {
			t.Fatal(err)
		}
		swapped = true
		return write()
	})
	if !swapped || err == nil || !strings.HasPrefix(err.Error(), "open pending ancestor without symlinks: ") {
		t.Fatal("expected refusal after swapping the parent for a symlink", swapped, err)
	}
	for _, p := range []string{filepath.Join(outside, "bundle.json"), filepath.Join(moved, "bundle.json")} {
		if _, err := os.Lstat(p); !os.IsNotExist(err) {
			t.Fatal("parent swap wrote an output", p, err)
		}
	}
	err = WritePrivatePendingArtifact(path, []byte("private"), func(func() error) error {
		t.Fatal("symlinked parent reached the guard")
		return nil
	})
	if err == nil || !strings.HasPrefix(err.Error(), "open pending ancestor without symlinks: ") {
		t.Fatal("expected symlinked parent refusal before staging", err)
	}
}
