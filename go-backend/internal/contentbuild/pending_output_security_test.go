//go:build linux

package contentbuild

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"golang.org/x/sys/unix"
)

func privatePendingTestDir(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	if err := os.Chmod(dir, 0700); err != nil {
		t.Fatal(err)
	}
	return dir
}

func TestQuickPendingPrivateParentOwnershipModesAndAncestors(t *testing.T) {
	for _, mode := range []os.FileMode{0755, 0777, 0770, 01777, 0700} {
		t.Run(fmt.Sprintf("mode_%o", mode), func(t *testing.T) {
			dir := privatePendingTestDir(t)
			if mode == 01777 {
				mode = os.ModeSticky | 0777
			}
			if err := os.Chmod(dir, mode); err != nil {
				t.Fatal(err)
			}
			called := false
			out := filepath.Join(dir, "bundle.json")
			err := WritePrivatePendingArtifact(out, []byte("private"), func(commit func() error) error { called = true; return commit() })
			if mode == 0700 {
				if err != nil || !called {
					t.Fatal("private owned parent refused", err)
				}
				return
			}
			if err == nil || called {
				t.Fatal("nonprivate output parent admitted or guard invoked", mode, err)
			}
			if _, err := os.Lstat(out); !os.IsNotExist(err) {
				t.Fatal("refused parent created output")
			}
		})
	}
	base := privatePendingTestDir(t)
	shared := filepath.Join(base, "shared")
	leaf := filepath.Join(shared, "owned")
	if err := os.Mkdir(shared, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(leaf, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(shared, 0777); err != nil {
		t.Fatal(err)
	}
	if err := ValidatePrivatePendingParent(filepath.Join(leaf, "bundle.json")); err == nil {
		t.Fatal("unprotected writable ancestor admitted")
	}
	if err := os.Chmod(shared, os.ModeSticky|0777); err != nil {
		t.Fatal(err)
	}
	if err := ValidatePrivatePendingParent(filepath.Join(leaf, "bundle.json")); err != nil {
		t.Fatal("trusted sticky ancestor over private owned child refused", err)
	}
	operator := uint32(os.Geteuid())
	other := operator + 1
	if other == 0 {
		other++
	}
	stat := unix.Stat_t{Mode: unix.S_IFDIR | 0700, Uid: other}
	if err := privatePendingDirectoryMode(&stat, operator, operator, true); err == nil {
		t.Fatal("foreign output parent owner admitted")
	}
}

func TestQuickPendingAnonymousFDIsNotAVisibleTemporaryName(t *testing.T) {
	for _, kind := range []string{"regular", "symlink"} {
		t.Run(kind, func(t *testing.T) {
			dir := privatePendingTestDir(t)
			out := filepath.Join(dir, "bundle.json")
			fake := filepath.Join(dir, ".quick-pending-attacker")
			target := filepath.Join(dir, "attacker-target")
			body := []byte("the exact private pending bundle")
			if err := os.WriteFile(target, []byte("foreign bytes"), 0644); err != nil {
				t.Fatal(err)
			}
			err := WritePrivatePendingArtifact(out, body, func(commit func() error) error {
				entries, err := os.ReadDir(dir)
				if err != nil {
					return err
				}
				for _, entry := range entries {
					if strings.HasPrefix(entry.Name(), ".quick-pending-") {
						return fmt.Errorf("visible publication staging basename exists")
					}
				}
				if kind == "regular" {
					err = os.WriteFile(fake, []byte("foreign bytes"), 0644)
				} else {
					err = os.Symlink(target, fake)
				}
				if err != nil {
					return err
				}
				return commit()
			})
			if err != nil {
				t.Fatal(err)
			}
			actual, err := os.ReadFile(out)
			if err != nil || !bytes.Equal(actual, body) {
				t.Fatal("not the held requested inode bytes", err)
			}
			info, err := os.Lstat(out)
			if err != nil || !info.Mode().IsRegular() || info.Mode().Perm() != 0600 {
				t.Fatal("published wrong inode type/mode", err)
			}
			foreign, err := os.ReadFile(fake)
			if err != nil || string(foreign) != "foreign bytes" {
				t.Fatal("unrelated temporary basename was consumed or changed", err)
			}
		})
	}
}

func TestQuickPendingPublishedReplacementIsRefusedAndPreserved(t *testing.T) {
	for _, kind := range []string{"regular", "symlink", "same_inode_mode"} {
		t.Run(kind, func(t *testing.T) {
			dir := privatePendingTestDir(t)
			out := filepath.Join(dir, "bundle.json")
			target := filepath.Join(dir, "foreign-target")
			if err := os.WriteFile(target, []byte("foreign"), 0644); err != nil {
				t.Fatal(err)
			}
			err := WritePrivatePendingArtifact(out, []byte("private"), func(commit func() error) error {
				if err := commit(); err != nil {
					return err
				}
				if kind == "same_inode_mode" {
					return os.Chmod(out, 0644)
				}
				if err := os.Remove(out); err != nil {
					return err
				}
				if kind == "symlink" {
					return os.Symlink(target, out)
				}
				return os.WriteFile(out, []byte("replacement"), 0644)
			})
			if err == nil {
				t.Fatal("changed destination reported success")
			}
			if kind == "same_inode_mode" {
				if _, e := os.Lstat(out); !os.IsNotExist(e) {
					t.Fatal("corrupt owned output was not cleaned")
				}
				return
			}
			actual, e := os.ReadFile(out)
			if e != nil {
				t.Fatal("another writer's replacement was removed", e)
			}
			want := "replacement"
			if kind == "symlink" {
				want = "foreign"
			}
			if string(actual) != want {
				t.Fatal("replacement/foreign target changed")
			}
		})
	}
}

func TestQuickPendingParentModeChangeBeforeCommitRefusesWithoutOutput(t *testing.T) {
	dir := privatePendingTestDir(t)
	out := filepath.Join(dir, "bundle.json")
	err := WritePrivatePendingArtifact(out, []byte("private"), func(commit func() error) error {
		if err := os.Chmod(dir, 0777); err != nil {
			return err
		}
		return commit()
	})
	if err == nil {
		t.Fatal("parent lost private control before fd link")
	}
	if err := os.Chmod(dir, 0700); err != nil {
		t.Fatal(err)
	}
	entries, err := os.ReadDir(dir)
	if err != nil || len(entries) != 0 {
		t.Fatal("anonymous failed staging left output or temporary names", err)
	}
}
