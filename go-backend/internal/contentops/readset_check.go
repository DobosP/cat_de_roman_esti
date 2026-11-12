package contentops

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
)

// MaxPendingProducerBytes is exclusive to the explicitly declared producing
// executable. Document and source members retain MaxDocumentBytes (32 MiB).
const MaxPendingProducerBytes = 256 << 20

type pendingProducerSnapshot struct {
	path        string
	fingerprint contentbuild.PendingInputFingerprint
}

// CaptureRegularReadSetWithProducer adds one explicit self-binary fingerprint
// without changing any document limit. The expected hash/length must come from
// the already bound native tool descriptor. A path cannot occupy both roles.
func CaptureRegularReadSetWithProducer(paths []string, producerPath, expectedSHA string, expectedBytes int64) (ReadSet, error) {
	if !filepath.IsAbs(producerPath) || filepath.Clean(producerPath) != producerPath || !validHex(expectedSHA) || expectedBytes < 1 || expectedBytes > MaxPendingProducerBytes {
		return ReadSet{}, errors.New("pending producer path/hash/byte bound")
	}
	for _, path := range paths {
		if path == producerPath {
			return ReadSet{}, errors.New("pending producer also declared as a document")
		}
	}
	set, err := CaptureRegularReadSet(paths)
	if err != nil {
		return ReadSet{}, err
	}
	fingerprint, err := contentbuild.ReadPendingFingerprint(producerPath, MaxPendingProducerBytes)
	if err != nil {
		return ReadSet{}, err
	}
	if fingerprint.SHA256 != expectedSHA || fingerprint.Bytes != expectedBytes {
		return ReadSet{}, errors.New("pending producer differs from bound tool descriptor")
	}
	set.producer = &pendingProducerSnapshot{producerPath, fingerprint}
	return set, nil
}

// CaptureRegularReadSet is a strict, existing-file-only snapshot for private
// pending evidence. The native no-symlink opener refuses special files without
// blocking. Other platforms compile but refuse this Linux-only operation.
func CaptureRegularReadSet(paths []string) (ReadSet, error) {
	entries := map[string]snapshot{}
	for _, path := range paths {
		if !filepath.IsAbs(path) || filepath.Clean(path) != path {
			return ReadSet{}, errors.New("strict readset requires canonical absolute paths")
		}
		s, err := takeRegularSnapshot(path)
		if err != nil {
			return ReadSet{}, err
		}
		entries[path] = s
	}
	return ReadSet{entries: entries, regularOnly: true}, nil
}

func takeRegularSnapshot(path string) (snapshot, error) {
	b, err := contentbuild.ReadPendingInput(path, MaxDocumentBytes)
	if err != nil {
		return snapshot{}, err
	}
	info, err := os.Lstat(path)
	if err != nil || !info.Mode().IsRegular() {
		return snapshot{}, errors.New("strict readset requires regular non-symlink members")
	}
	return snapshot{blob: b, exists: true, mode: info.Mode().Perm()}, nil
}

// Verify rechecks a captured readset without creating a write lock or output.
// Publication still uses GuardedTransaction around its publication callback.
func (s ReadSet) Verify() error {
	if len(s.entries) == 0 && s.producer == nil {
		return errors.New("missing immutable read set")
	}
	if !s.regularOnly {
		return checkSnapshots(s.entries)
	}
	for path, expected := range s.entries {
		actual, err := takeRegularSnapshot(path)
		if err != nil || !actual.exists || digest(actual.blob) != digest(expected.blob) || actual.mode != expected.mode {
			return fmt.Errorf("strict pending readset changed: %s", path)
		}
	}
	if s.producer != nil {
		actual, err := contentbuild.ReadPendingFingerprint(s.producer.path, MaxPendingProducerBytes)
		expected := s.producer.fingerprint
		if err != nil || actual.SHA256 != expected.SHA256 || actual.Bytes != expected.Bytes || actual.Mode != expected.Mode || actual.Metadata != expected.Metadata || actual.Identity == nil || !os.SameFile(actual.Identity, expected.Identity) || !actual.Identity.ModTime().Equal(expected.Identity.ModTime()) {
			return errors.New("strict pending producer identity/digest/metadata changed")
		}
	}
	return nil
}
