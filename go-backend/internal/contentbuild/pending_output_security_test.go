//go:build linux

package contentbuild

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/testfixture"
	"golang.org/x/sys/unix"
)

const pendingParentModeRefusal = "pending output parent must be owned by effective UID with mode 0700"

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
			dir := filepath.Join(testfixture.NativePendingDir(t), "output")
			if err := os.Mkdir(dir, 0700); err != nil {
				t.Fatal(err)
			}
			if mode == 01777 {
				mode = os.ModeSticky | 0777
			}
			if err := os.Chmod(dir, mode); err != nil {
				t.Fatal(err)
			}
			called := false
			out := filepath.Join(dir, "bundle.json")
			err := WritePrivatePendingArtifact(out, []byte("private"), func(commit func() error) error {
				called = true
				return commit()
			})
			if mode == 0700 {
				if err != nil || !called {
					t.Fatal("private owned parent refused", err)
				}
				return
			}
			if called || err == nil || err.Error() != pendingParentModeRefusal {
				t.Fatal("expected refusal for nonprivate parent before guard", mode, called, err)
			}
			if _, err := os.Lstat(out); !os.IsNotExist(err) {
				t.Fatal("refused parent created output", err)
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
	if err := ValidatePrivatePendingParent(filepath.Join(leaf, "bundle.json")); err == nil || err.Error() != "pending scratch ancestor is writable without sticky protection" {
		t.Fatal("expected unprotected writable ancestor refusal", err)
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
	if err := privatePendingDirectoryMode(&stat, operator, operator, true); err == nil || err.Error() != "pending scratch ancestor must be a trusted owned directory" {
		t.Fatal("expected foreign output parent owner refusal", err)
	}
}

func TestQuickPendingAnonymousFDIsNotAVisibleTemporaryName(t *testing.T) {
	for _, kind := range []string{"regular", "symlink"} {
		t.Run(kind, func(t *testing.T) {
			dir := testfixture.NativePendingDir(t)
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
				if len(entries) != 1 || entries[0].Name() != filepath.Base(target) {
					return fmt.Errorf("visible publication staging entry exists: %v", entries)
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
			dir := testfixture.NativePendingDir(t)
			out := filepath.Join(dir, "bundle.json")
			target := filepath.Join(dir, "foreign-target")
			if err := os.WriteFile(target, []byte("foreign"), 0644); err != nil {
				t.Fatal(err)
			}
			var changed os.FileInfo
			err := WritePrivatePendingArtifact(out, []byte("private"), func(commit func() error) error {
				if err := commit(); err != nil {
					t.Fatal("initial publication failed", err)
				}
				if kind != "same_inode_mode" {
					if err := os.Remove(out); err != nil {
						t.Fatal(err)
					}
				}
				var err error
				switch kind {
				case "same_inode_mode":
					err = os.Chmod(out, 0644)
				case "symlink":
					err = os.Symlink(target, out)
				default:
					err = os.WriteFile(out, []byte("replacement"), 0644)
				}
				if err != nil {
					t.Fatal(err)
				}
				info, err := os.Lstat(out)
				if err != nil {
					t.Fatal(err)
				}
				changed = info
				return nil
			})
			if changed == nil {
				t.Fatal("publication guard did not change the destination", err)
			}
			if kind == "symlink" {
				if !errors.Is(err, unix.ELOOP) {
					t.Fatal("expected published symlink refusal", err)
				}
			} else if err == nil || !strings.HasPrefix(err.Error(), "published pending inode/type/private mode differs") {
				t.Fatal("expected published inode or mode refusal", err)
			}
			if kind == "same_inode_mode" {
				if _, err := os.Lstat(out); !os.IsNotExist(err) {
					t.Fatal("corrupt owned output was not cleaned", err)
				}
				return
			}
			info, err := os.Lstat(out)
			if err != nil || !os.SameFile(changed, info) {
				t.Fatal("another writer's replacement inode was not preserved", err)
			}
			actual, err := os.ReadFile(out)
			want := "replacement"
			if kind == "symlink" {
				want = "foreign"
			}
			if err != nil || string(actual) != want {
				t.Fatal("replacement/foreign target changed", err)
			}
		})
	}
}

func TestQuickPendingParentModeChangeBeforeCommitRefusesWithoutOutput(t *testing.T) {
	dir := filepath.Join(testfixture.NativePendingDir(t), "output")
	if err := os.Mkdir(dir, 0700); err != nil {
		t.Fatal(err)
	}
	out := filepath.Join(dir, "bundle.json")
	changed := false
	err := WritePrivatePendingArtifact(out, []byte("private"), func(commit func() error) error {
		if err := os.Chmod(dir, 0777); err != nil {
			t.Fatal(err)
		}
		changed = true
		return commit()
	})
	if !changed || err == nil || err.Error() != pendingParentModeRefusal {
		t.Fatal("expected refusal after changing the parent mode before fd link", changed, err)
	}
	if err := os.Chmod(dir, 0700); err != nil {
		t.Fatal(err)
	}
	entries, err := os.ReadDir(dir)
	if err != nil || len(entries) != 0 {
		t.Fatal("anonymous failed staging left output or temporary names", err)
	}
}
