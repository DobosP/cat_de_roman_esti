package contentbuild

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"testing"
)

func exportRoot(t *testing.T) string {
	t.Helper()
	base := os.Getenv("GOTMPDIR")
	if base == "" {
		base = os.Getenv("TMPDIR")
	}
	if base == "" {
		home, e := os.UserHomeDir()
		if e != nil {
			t.Fatal(e)
		}
		base = filepath.Join(home, "work", "_temp", "cat-content-tests")
	}
	if e := os.MkdirAll(base, 0700); e != nil {
		t.Fatal(e)
	}
	root, e := os.MkdirTemp(base, "export-transaction-")
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { os.RemoveAll(root) })
	if e := os.MkdirAll(filepath.Join(root, "go-backend/internal/content"), 0700); e != nil {
		t.Fatal(e)
	}
	return root
}
func TestExportTransactionPartialWriteAndGateRollback(t *testing.T) {
	for _, missing := range []bool{false, true} {
		for _, mid := range []bool{false, true} {
			t.Run(map[bool]string{true: "absent", false: "existing"}[missing]+map[bool]string{true: "-midwrite", false: "-postgate"}[mid], func(t *testing.T) {
				root := exportRoot(t)
				paths := []string{filepath.Join(root, "go-backend/internal/content/bundled.json"), filepath.Join(root, "go-backend/internal/content/digest.go")}
				if !missing {
					for _, p := range paths {
						if e := os.WriteFile(p, []byte("original:"+filepath.Base(p)), 0640); e != nil {
							t.Fatal(e)
						}
					}
				}
				produce := func() ([]byte, []byte, error) {
					if _, e := os.Stat(filepath.Join(root, ".cat-content-ops.lock")); e != nil {
						t.Fatal("build was invoked without source operator lock")
					}
					return []byte("new bundle"), []byte("new pin"), nil
				}
				verify := func() error { return errors.New("synthetic stale post-gate") }
				var hook func(int) error
				if mid {
					hook = func(i int) error {
						if i == 0 {
							return errors.New("synthetic partial replacement")
						}
						return nil
					}
				}
				if e := exportTransaction(root, produce, verify, hook); e == nil {
					t.Fatal("failure not returned")
				}
				for _, p := range paths {
					b, e := os.ReadFile(p)
					if missing {
						if !os.IsNotExist(e) {
							t.Fatal("absent target not removed on rollback")
						}
					} else {
						if e != nil || !bytes.Equal(b, []byte("original:"+filepath.Base(p))) {
							t.Fatal("existing bytes not restored")
						}
						info, e := os.Stat(p)
						if e != nil || info.Mode().Perm() != 0640 {
							t.Fatal("existing mode not restored")
						}
					}
				}
				if _, e := os.Stat(filepath.Join(root, ".cat-content-ops.lock")); !os.IsNotExist(e) {
					t.Fatal("lock leaked")
				}
			})
		}
	}
}
func TestExportTransactionLockSymlinkAndSuccessfulPair(t *testing.T) {
	root := exportRoot(t)
	produce := func() ([]byte, []byte, error) { return []byte("bundle"), []byte("pin"), nil }
	lock := filepath.Join(root, ".cat-content-ops.lock")
	if e := os.WriteFile(lock, []byte("another operator"), 0600); e != nil {
		t.Fatal(e)
	}
	if e := exportTransaction(root, produce, nil, nil); e == nil {
		t.Fatal("concurrent content operator lock ignored")
	}
	os.Remove(lock)
	victim := filepath.Join(root, "victim")
	if e := os.WriteFile(victim, []byte("preserved"), 0600); e != nil {
		t.Fatal(e)
	}
	out := filepath.Join(root, "go-backend/internal/content/bundled.json")
	if e := os.Symlink(victim, out); e != nil {
		t.Fatal(e)
	}
	if e := exportTransaction(root, produce, nil, nil); e == nil {
		t.Fatal("symlink output followed")
	}
	b, _ := os.ReadFile(victim)
	if string(b) != "preserved" {
		t.Fatal("symlink victim changed")
	}
	os.Remove(out)
	if e := exportTransaction(root, produce, func() error {
		b, e := os.ReadFile(out)
		if e != nil || string(b) != "bundle" {
			return errors.New("bundle incomplete")
		}
		b, e = os.ReadFile(filepath.Join(filepath.Dir(out), "digest.go"))
		if e != nil || string(b) != "pin" {
			return errors.New("pin incomplete")
		}
		return nil
	}, nil); e != nil {
		t.Fatal(e)
	}
}
func TestCanonicalLiteralSeparatorEscapeRoundTrips(t *testing.T) {
	for _, s := range []string{`\u2028`, `\u2029`, `prefix\\u2028`, "\u2028", `backslash\` + "\u2029"} {
		b, e := Canonical(map[string]any{"s": s})
		if e != nil {
			t.Fatal(e)
		}
		m, e := decodeObject(b)
		if e != nil || m["s"] != s {
			t.Fatalf("%q canonical %s fails identity: %v", s, b, e)
		}
	}
}
