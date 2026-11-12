//go:build linux

package contentbuild

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

func TestQuickPendingPublicationIsPrivateAtomicNoReplaceAndCleansFailedGuard(t *testing.T) {
	dir := t.TempDir()
	if err := os.Chmod(dir, 0700); err != nil {
		t.Fatal(err)
	}
	target := filepath.Join(dir, "bundle.json")
	data := []byte("complete private bundle\n")
	pass := func(write func() error) error { return write() }
	if err := WritePrivatePendingArtifact(target, data, pass); err != nil {
		t.Fatal(err)
	}
	info, _ := os.Stat(target)
	b, _ := os.ReadFile(target)
	if info.Mode().Perm() != 0600 || string(b) != string(data) {
		t.Fatal("private exact output changed")
	}
	if err := WritePrivatePendingArtifact(target, []byte("overwrite"), pass); err == nil {
		t.Fatal("replaced existing output")
	}
	b, _ = os.ReadFile(target)
	if string(b) != string(data) {
		t.Fatal("old output mutated")
	}
	failed := filepath.Join(dir, "failed.json")
	if err := WritePrivatePendingArtifact(failed, data, func(write func() error) error {
		if err := write(); err != nil {
			return err
		}
		return errors.New("post-publication stale readset")
	}); err == nil {
		t.Fatal("guard failure passed")
	}
	if _, err := os.Lstat(failed); !os.IsNotExist(err) {
		t.Fatal("failed output remained")
	}
	entries, _ := os.ReadDir(dir)
	if len(entries) != 1 {
		t.Fatal("temporary partial output remained")
	}
}
func TestQuickPendingPublicationRefusesParentSwapAndSymlinks(t *testing.T) {
	dir, outside := t.TempDir(), t.TempDir()
	if err := os.Chmod(dir, 0700); err != nil {
		t.Fatal(err)
	}
	parent := filepath.Join(dir, "parent")
	if err := os.Mkdir(parent, 0700); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(parent, "bundle.json")
	err := WritePrivatePendingArtifact(path, []byte("private"), func(write func() error) error {
		if err := os.Rename(parent, parent+"-moved"); err != nil {
			return err
		}
		if err := os.Symlink(outside, parent); err != nil {
			return err
		}
		return write()
	})
	if err == nil {
		t.Fatal("parent swap passed")
	}
	for _, p := range []string{filepath.Join(outside, "bundle.json"), filepath.Join(parent+"-moved", "bundle.json")} {
		if _, err := os.Lstat(p); !os.IsNotExist(err) {
			t.Fatal("parent swap wrote an output", p)
		}
	}
	if err := WritePrivatePendingArtifact(path, []byte("private"), func(write func() error) error { return write() }); err == nil {
		t.Fatal("symlinked parent passed")
	}
}
