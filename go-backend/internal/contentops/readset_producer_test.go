//go:build linux

package contentops

import (
	"io"
	"os"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
)

func pendingProducerBinding(t *testing.T, path string) contentbuild.PendingInputFingerprint {
	t.Helper()
	fingerprint, err := contentbuild.ReadPendingFingerprint(path, MaxPendingProducerBytes)
	if err != nil {
		t.Fatal(err)
	}
	return fingerprint
}

func TestQuickPendingProducerHasExplicitCapWithoutRaisingDocumentLimits(t *testing.T) {
	dir := t.TempDir()
	producer := filepath.Join(dir, "synthetic-producer")
	file, err := os.OpenFile(producer, os.O_CREATE|os.O_EXCL|os.O_RDWR, 0700)
	if err != nil {
		t.Fatal(err)
	}
	// Sparse synthetic bytes exercise 64 MiB capacity without a retained large
	// artifact or any claim that these bytes are an authenticated executable.
	if err := file.Truncate(64 << 20); err != nil {
		_ = file.Close()
		t.Fatal(err)
	}
	if err := file.Close(); err != nil {
		t.Fatal(err)
	}
	if _, err := CaptureRegularReadSet([]string{producer}); err == nil {
		t.Fatal("global document cap was raised")
	}
	fp := pendingProducerBinding(t, producer)
	set, err := CaptureRegularReadSetWithProducer(nil, producer, fp.SHA256, fp.Bytes)
	if err != nil {
		t.Fatal("explicit 64 MiB producer refused", err)
	}
	if err := set.Verify(); err != nil {
		t.Fatal(err)
	}
	if len(set.entries) != 0 || set.producer == nil {
		t.Fatal("producer was retained as a document body")
	}
	if _, err := CaptureRegularReadSetWithProducer([]string{producer}, producer, fp.SHA256, fp.Bytes); err == nil {
		t.Fatal("producer document-role collision bypassed cap")
	}
	if _, err := CaptureRegularReadSetWithProducer(nil, producer, strings.Repeat("a", 64), fp.Bytes); err == nil {
		t.Fatal("wrong bound producer hash passed")
	}
	oversize := filepath.Join(dir, "too-large")
	f, err := os.Create(oversize)
	if err != nil {
		t.Fatal(err)
	}
	if err := f.Truncate(MaxPendingProducerBytes + 1); err != nil {
		_ = f.Close()
		t.Fatal(err)
	}
	if err := f.Close(); err != nil {
		t.Fatal(err)
	}
	if _, err := CaptureRegularReadSetWithProducer(nil, oversize, strings.Repeat("a", 64), MaxPendingProducerBytes+1); err == nil {
		t.Fatal("producer descriptor cap passed")
	}
	if _, err := contentbuild.ReadPendingFingerprint(oversize, MaxPendingProducerBytes); err == nil {
		t.Fatal("producer physical file cap passed")
	}
}

func TestQuickPendingProducerMutationReplacementMissingAndSpecialRefuse(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "producer")
	body := []byte("fixed synthetic producer bytes")
	write := func() {
		if err := os.WriteFile(path, body, 0700); err != nil {
			t.Fatal(err)
		}
	}
	capture := func() ReadSet {
		fp := pendingProducerBinding(t, path)
		set, err := CaptureRegularReadSetWithProducer(nil, path, fp.SHA256, fp.Bytes)
		if err != nil {
			t.Fatal(err)
		}
		return set
	}
	write()
	set := capture()
	if err := os.WriteFile(path, []byte("changed synthetic producer bytes"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := set.Verify(); err == nil {
		t.Fatal("changed producer bytes passed")
	}
	write()
	set = capture()
	if err := os.Rename(path, path+"-old"); err != nil {
		t.Fatal(err)
	}
	write()
	if err := set.Verify(); err == nil {
		t.Fatal("same-byte different producer inode passed")
	}
	set = capture()
	if err := os.Chmod(path, 0600); err != nil {
		t.Fatal(err)
	}
	if err := set.Verify(); err == nil {
		t.Fatal("producer mode change passed")
	}
	if err := os.Remove(path); err != nil {
		t.Fatal(err)
	}
	if err := set.Verify(); err == nil {
		t.Fatal("missing producer passed")
	}
	if err := os.Symlink(path+"-old", path); err != nil {
		t.Fatal(err)
	}
	if _, err := CaptureRegularReadSetWithProducer(nil, path, strings.Repeat("a", 64), int64(len(body))); err == nil {
		t.Fatal("producer symlink passed")
	}
	if err := os.Remove(path); err != nil {
		t.Fatal(err)
	}
	if err := syscall.Mkfifo(path, 0600); err != nil {
		t.Fatal(err)
	}
	done := make(chan error, 1)
	go func() {
		_, err := CaptureRegularReadSetWithProducer(nil, path, strings.Repeat("a", 64), int64(len(body)))
		done <- err
	}()
	select {
	case err := <-done:
		if err == nil {
			t.Fatal("producer FIFO accepted")
		}
	case <-time.After(time.Second):
		t.Fatal("producer FIFO blocked")
	}
}

// The independent QP-2 control used CaptureRegularReadSet directly and failed
// genuinely on frozen v2 (original source/hash and failure remain immutable).
// This adaptation also proves that API still refuses the actual executable as
// a document, while its explicit producer role succeeds without stripping it.
func TestQuickPendingActualCompiledProducerReadset(t *testing.T) {
	path := os.Getenv("PENDING_REVIEW_TOOL")
	if path == "" {
		t.Skip("actual-producer qualification requires PENDING_REVIEW_TOOL and PENDING_REVIEW_TOOL_SHA256; hermetic synthetic tests do not establish it")
	}
	if !filepath.IsAbs(path) || filepath.Clean(path) != path {
		t.Fatal("PENDING_REVIEW_TOOL must be canonical absolute actual pinned producer")
	}
	expected := os.Getenv("PENDING_REVIEW_TOOL_SHA256")
	if !validHex(expected) {
		t.Fatal("PENDING_REVIEW_TOOL_SHA256 must bind the actual unstripped producer")
	}
	fp := pendingProducerBinding(t, path)
	if fp.Bytes <= MaxDocumentBytes || fp.Bytes > MaxPendingProducerBytes || fp.SHA256 != expected {
		t.Fatalf("actual producer hash/size does not exercise QP-2: %d bytes, %s", fp.Bytes, fp.SHA256)
	}
	if _, err := CaptureRegularReadSet([]string{path}); err == nil {
		t.Fatal("actual producer bypassed document cap")
	}
	dir := t.TempDir()
	document := filepath.Join(dir, "document")
	if err := os.WriteFile(document, []byte("fixed document"), 0600); err != nil {
		t.Fatal(err)
	}
	set, err := CaptureRegularReadSetWithProducer([]string{document}, path, expected, fp.Bytes)
	if err != nil {
		t.Fatal("actual unstripped producer refused explicit snapshot", err)
	}
	if err := set.Verify(); err != nil {
		t.Fatal(err)
	}
	if err := GuardedTransaction(dir, nil, set, func() error { return nil }); err != nil {
		t.Fatal("actual producer did not traverse guarded verification", err)
	}
	// Mutate an owned copy, never Root's actual compiled producer.
	copyPath := filepath.Join(dir, "producer-copy")
	source, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	copyFile, err := os.OpenFile(copyPath, os.O_CREATE|os.O_EXCL|os.O_RDWR, 0700)
	if err != nil {
		_ = source.Close()
		t.Fatal(err)
	}
	_, err = io.Copy(copyFile, source)
	_ = source.Close()
	if err != nil {
		_ = copyFile.Close()
		t.Fatal(err)
	}
	if err = copyFile.Close(); err != nil {
		t.Fatal(err)
	}
	copySet, err := CaptureRegularReadSetWithProducer([]string{document}, copyPath, expected, fp.Bytes)
	if err != nil {
		t.Fatal(err)
	}
	err = GuardedTransaction(dir, nil, copySet, func() error {
		f, e := os.OpenFile(copyPath, os.O_WRONLY, 0)
		if e != nil {
			return e
		}
		_, e = f.WriteAt([]byte{0xff}, 0)
		closeErr := f.Close()
		if e != nil {
			return e
		}
		return closeErr
	})
	if err == nil {
		t.Fatal("changed actual-byte producer copy passed guarded verification")
	}
	t.Logf("actual unstripped producer %d bytes sha256=%s; source executable remained read-only", fp.Bytes, fp.SHA256)
}
