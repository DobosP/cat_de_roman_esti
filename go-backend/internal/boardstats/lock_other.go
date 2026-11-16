//go:build !darwin && !dragonfly && !freebsd && !linux && !netbsd && !openbsd && !windows

package boardstats

import (
	"errors"
	"os"
)

func takeLock(_ *os.File) error {
	return errors.New("board stats directory locking is unavailable on this platform")
}

func syncDirectory(_ *os.Root) error { return nil }
