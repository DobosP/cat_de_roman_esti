package boardstats

import (
	"errors"
	"os"

	"golang.org/x/sys/windows"
)

func takeLock(f *os.File) error {
	var offset windows.Overlapped
	err := windows.LockFileEx(windows.Handle(f.Fd()),
		windows.LOCKFILE_EXCLUSIVE_LOCK|windows.LOCKFILE_FAIL_IMMEDIATELY, 0, 1, 0, &offset)
	if errors.Is(err, windows.ERROR_LOCK_VIOLATION) {
		return ErrLocked
	}
	return err
}

// Windows does not provide directory fsync through os.File.
func syncDirectory(_ *os.Root) error { return nil }
