//go:build linux

package contentrails

import (
	"context"
	"os"
	"path/filepath"
	"syscall"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
)

func TestQuickPendingDiscoveryRefusesFIFOWithoutBlocking(t *testing.T) {
	root := t.TempDir()
	for path, b := range map[string][]byte{installedManifestPath: installedAuthorityBytes, installedPinPath: installedPinBytes} {
		out := filepath.Join(root, path)
		if err := os.MkdirAll(filepath.Dir(out), 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(out, b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	a, err := parseInstalledAuthorities(installedAuthorityBytes, InstalledAuthoritiesSHA256)
	if err != nil {
		t.Fatal(err)
	}
	chain := rows(a.raw["source_chain"])
	if len(chain) == 0 {
		t.Fatal("current source chain unexpectedly empty")
	}
	fifo := filepath.Join(root, text(object(chain[0])["path"]))
	if err := os.MkdirAll(filepath.Dir(fifo), 0700); err != nil {
		t.Fatal(err)
	}
	if err := syscall.Mkfifo(fifo, 0600); err != nil {
		t.Fatal(err)
	}
	done := make(chan error, 1)
	go func() { _, err := pendingCurrentSource(root); done <- err }()
	select {
	case err := <-done:
		if err == nil {
			t.Fatal("source-chain FIFO accepted")
		}
	case <-time.After(time.Second):
		t.Fatal("source-chain FIFO blocked initial pending discovery")
	}
}

func TestQuickPendingFrozenCurrentArtifactRequiresExactInstalledMetadata(t *testing.T) {
	snap, err := captureQuickPending(rootPath(t), nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := snap.quickArtifactBound(); err != nil {
		t.Fatal(err)
	}
	name := "cat_de_roman_esti/fixtures/quick_games_v92.json"
	// The semantic rows are unchanged, but the artifact metadata bytes differ.
	snap.files[name] = append(append([]byte{}, snap.files[name]...), ' ')
	if err := snap.quickArtifactBound(); err == nil {
		t.Fatal("whole installed fixture metadata pin was bypassed")
	}
}

func TestQuickPendingCancellationBeforeAndAfterPublicationCleansArtifact(t *testing.T) {
	scratch := t.TempDir()
	if err := os.Chmod(scratch, 0700); err != nil {
		t.Fatal(err)
	}
	input := filepath.Join(scratch, "input")
	if err := os.WriteFile(input, []byte("fixed"), 0600); err != nil {
		t.Fatal(err)
	}
	readset, err := contentops.CaptureRegularReadSet([]string{input})
	if err != nil {
		t.Fatal(err)
	}
	for _, after := range []bool{false, true} {
		ctx, cancel := context.WithCancel(context.Background())
		path := filepath.Join(scratch, "pending.json")
		if !after {
			cancel()
		}
		checks := 0
		err := publishQuickPending(ctx, path, []byte("private complete artifact"), readset, func() error {
			checks++
			if after && checks == 2 {
				cancel()
			}
			return nil
		})
		cancel()
		if err == nil {
			t.Fatal("canceled preparation published successfully", after)
		}
		if _, err := os.Lstat(path); !os.IsNotExist(err) {
			t.Fatal("canceled private publication remained", after)
		}
	}
}
