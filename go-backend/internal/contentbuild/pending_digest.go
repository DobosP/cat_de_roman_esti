package contentbuild

import (
	"crypto/sha256"
	"fmt"
	"io"
	"os"
)

// PendingInputFingerprint is a compact bounded regular-file snapshot. Identity
// and metadata are private verification inputs; no executable body is retained.
type PendingInputFingerprint struct {
	SHA256   string
	Bytes    int64
	Mode     os.FileMode
	Identity os.FileInfo
	Metadata string
}

// ReadPendingFingerprint hashes a held no-symlink/nonblocking regular file and
// checks its descriptor and pathname identity on both sides of the read.
func ReadPendingFingerprint(path string, max int64) (PendingInputFingerprint, error) {
	if max < 1 {
		return PendingInputFingerprint{}, fmt.Errorf("pending fingerprint requires a positive byte bound")
	}
	file, err := openNoSymlinkPath(path, os.O_RDONLY, 0)
	if err != nil {
		return PendingInputFingerprint{}, err
	}
	defer file.Close()
	before, err := file.Stat()
	if err != nil || !before.Mode().IsRegular() || before.Size() < 1 || before.Size() > max {
		return PendingInputFingerprint{}, fmt.Errorf("pending fingerprint source exceeds bound or is not nonempty regular file")
	}
	metadata, err := pendingFileMetadata(file)
	if err != nil {
		return PendingInputFingerprint{}, err
	}
	hash := sha256.New()
	n, err := io.CopyBuffer(hash, io.LimitReader(file, max+1), make([]byte, 64<<10))
	if err != nil || n > max {
		return PendingInputFingerprint{}, fmt.Errorf("pending fingerprint read exceeds bound or failed")
	}
	after, err := file.Stat()
	afterMetadata, metadataErr := pendingFileMetadata(file)
	if err != nil || metadataErr != nil || !os.SameFile(before, after) || before.Size() != n || after.Size() != n || before.Mode() != after.Mode() || !before.ModTime().Equal(after.ModTime()) || metadata != afterMetadata {
		return PendingInputFingerprint{}, fmt.Errorf("pending fingerprint descriptor changed during read")
	}
	current, err := openNoSymlinkPath(path, os.O_RDONLY, 0)
	if err != nil {
		return PendingInputFingerprint{}, err
	}
	defer current.Close()
	currentInfo, err := current.Stat()
	currentMetadata, metadataErr := pendingFileMetadata(current)
	if err != nil || metadataErr != nil || !os.SameFile(after, currentInfo) || after.Size() != currentInfo.Size() || after.Mode() != currentInfo.Mode() || !after.ModTime().Equal(currentInfo.ModTime()) || afterMetadata != currentMetadata {
		return PendingInputFingerprint{}, fmt.Errorf("pending fingerprint pathname identity changed")
	}
	return PendingInputFingerprint{fmt.Sprintf("%x", hash.Sum(nil)), n, after.Mode(), after, afterMetadata}, nil
}
