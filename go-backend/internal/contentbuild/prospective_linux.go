//go:build linux

package contentbuild

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/sys/unix"
)

// openNoSymlinkPath opens an absolute canonical path with Linux openat2 so no
// component, including the final one, may be a symlink. Reads are opened
// non-blocking, so a FIFO is refused by the regular-file check instead of
// waiting for a writer.
func openNoSymlinkPath(path string, flags int, mode uint32) (*os.File, error) {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path {
		return nil, fmt.Errorf("path must be absolute and canonical without symlinks")
	}
	resolved, err := filepath.EvalSymlinks(path)
	if err != nil && flags&os.O_CREATE == 0 {
		return nil, fmt.Errorf("resolve canonical path without symlinks: %w", err)
	}
	if err == nil && resolved != path {
		return nil, fmt.Errorf("path must be absolute and canonical without symlinks")
	}
	if flags&os.O_CREATE != 0 {
		resolvedParent, parentErr := filepath.EvalSymlinks(filepath.Dir(path))
		if parentErr != nil {
			return nil, fmt.Errorf("resolve canonical parent without symlinks: %w", parentErr)
		}
		if resolvedParent != filepath.Dir(path) {
			return nil, fmt.Errorf("path must be absolute and canonical without symlinks")
		}
	}
	rootFD, err := unix.Open(string(filepath.Separator), unix.O_RDONLY|unix.O_DIRECTORY|unix.O_CLOEXEC|unix.O_NOFOLLOW, 0)
	if err != nil {
		return nil, err
	}
	rel := strings.TrimPrefix(path, string(filepath.Separator))
	if flags&os.O_CREATE == 0 {
		flags |= unix.O_NONBLOCK
	}
	how := &unix.OpenHow{
		Flags:   uint64(flags | unix.O_NOFOLLOW | unix.O_CLOEXEC),
		Mode:    uint64(mode),
		Resolve: uint64(unix.RESOLVE_BENEATH | unix.RESOLVE_NO_SYMLINKS),
	}
	fd, openErr := unix.Openat2(rootFD, rel, how)
	_ = unix.Close(rootFD)
	if openErr != nil {
		return nil, fmt.Errorf("open complete path without symlinks: %w", openErr)
	}
	return os.NewFile(uintptr(fd), path), nil
}
