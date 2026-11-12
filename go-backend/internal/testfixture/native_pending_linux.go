//go:build linux

// Package testfixture provides fixtures used only by tests.
package testfixture

import (
	"errors"
	"os"
	"testing"

	"golang.org/x/sys/unix"
)

// NativePendingDir returns a private test directory that supports O_TMPFILE.
func NativePendingDir(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	if err := os.Chmod(dir, 0700); err != nil {
		t.Fatal(err)
	}
	err := probePendingOpen(t, dir)
	if err == nil {
		return dir
	}
	if !errors.Is(err, unix.EOPNOTSUPP) {
		t.Fatalf("open anonymous pending test inode in %s: %v", dir, err)
	}

	// The owning SDK's /tmp can be an overlay without O_TMPFILE support.
	scratch, err := os.MkdirTemp("/dev/shm", "cat-native-pending-")
	if err != nil {
		t.Fatalf("default test filesystem lacks O_TMPFILE and /dev/shm scratch failed: %v", err)
	}
	t.Cleanup(func() {
		if err := os.RemoveAll(scratch); err != nil {
			t.Errorf("clean private pending test directory %s: %v", scratch, err)
		}
	})
	if err := os.Chmod(scratch, 0700); err != nil {
		t.Fatal(err)
	}
	if err := probePendingOpen(t, scratch); err != nil {
		t.Fatalf("open anonymous pending test inode in %s: %v", scratch, err)
	}
	return scratch
}

func probePendingOpen(t *testing.T, dir string) error {
	t.Helper()
	fd, err := unix.Open(dir, unix.O_TMPFILE|unix.O_RDWR|unix.O_CLOEXEC, 0600)
	if err != nil {
		return err
	}
	if err := unix.Close(fd); err != nil {
		t.Fatalf("close anonymous pending test inode in %s: %v", dir, err)
	}
	return nil
}
