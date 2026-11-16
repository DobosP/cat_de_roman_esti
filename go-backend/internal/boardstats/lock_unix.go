//go:build darwin || dragonfly || freebsd || linux || netbsd || openbsd

package boardstats

import (
	"errors"
	"os"

	"golang.org/x/sys/unix"
)

func takeLock(f *os.File) error {
	err := unix.Flock(int(f.Fd()), unix.LOCK_EX|unix.LOCK_NB)
	if errors.Is(err, unix.EWOULDBLOCK) {
		return ErrLocked
	}
	return err
}

func syncDirectory(dir *os.Root) error {
	f, err := dir.Open(".")
	if err != nil {
		return err
	}
	return errors.Join(f.Sync(), f.Close())
}
