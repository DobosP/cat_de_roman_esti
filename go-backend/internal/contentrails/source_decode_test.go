package contentrails

import (
	"os"
	"path/filepath"
	"testing"
)

func TestSourceReadersKeepUTF8AndByteCapErrorPrecedence(t *testing.T) {
	tooLarge := make([]byte, MaxBytes+1)
	tooLarge[0] = 0xff
	for _, tc := range []struct {
		name      string
		raw       []byte
		readError string
		srcError  string
	}{
		{"invalid-utf8", []byte{'{', '"', 'x', '"', ':', '"', 0xff, '"', '}'}, "invalid UTF-8 JSON", "invalid UTF-8 JSON"},
		{"cap-before-invalid-utf8", tooLarge, "rail JSON byte cap", "authored source byte cap exceeded"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			path := filepath.Join(t.TempDir(), "input.json")
			if err := os.WriteFile(path, tc.raw, 0600); err != nil {
				t.Fatal(err)
			}
			value, err := Read(path)
			if value != nil || err == nil || err.Error() != tc.readError {
				t.Fatalf("Read: value=%v err=%v; want nil and %q", value, err, tc.readError)
			}
			source, err := decodeSource(tc.raw, "", -1)
			if source != nil || err == nil || err.Error() != tc.srcError {
				t.Fatalf("decodeSource: source=%v err=%v; want nil and %q", source, err, tc.srcError)
			}
		})
	}
}
