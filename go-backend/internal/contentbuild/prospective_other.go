//go:build !linux

package contentbuild

import (
	"fmt"
	"os"
	"runtime"
)

// openNoSymlinkPath needs Linux openat2 to refuse symlinks along the whole
// path. Other platforms still build the content tools but refuse the
// prospective preview rather than fall back to weaker pathname checks.
func openNoSymlinkPath(path string, flags int, mode uint32) (*os.File, error) {
	return nil, fmt.Errorf("prospective preview requires Linux openat2; unsupported on %s", runtime.GOOS)
}
