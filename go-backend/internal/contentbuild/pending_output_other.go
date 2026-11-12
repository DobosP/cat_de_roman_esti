//go:build !linux

package contentbuild

import (
	"fmt"
	"os"
	"runtime"
)

// Compile-only portability does not imply race-safe publication on this OS.
func WritePrivatePendingArtifact(path string, data []byte, guard func(func() error) error) error {
	return fmt.Errorf("private pending preparation requires Linux openat2/linkat; unsupported on %s", runtime.GOOS)
}

func ValidatePrivatePendingParent(output string) error {
	return fmt.Errorf("private pending parent validation requires Linux openat2; unsupported on %s", runtime.GOOS)
}

func pendingFileMetadata(file *os.File) (string, error) {
	return "", fmt.Errorf("private pending fingerprint metadata requires Linux; unsupported on %s", runtime.GOOS)
}
