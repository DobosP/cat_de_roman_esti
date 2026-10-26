//go:build !linux

package contentbuild

import (
	"strings"
	"testing"
)

func TestProspectivePreviewRefusesWithoutOpenat2(t *testing.T) {
	if _, err := readDirect("/missing/kg.json", 1); err == nil || !strings.Contains(err.Error(), "requires Linux openat2") {
		t.Fatalf("non-Linux preview did not refuse: %v", err)
	}
}
