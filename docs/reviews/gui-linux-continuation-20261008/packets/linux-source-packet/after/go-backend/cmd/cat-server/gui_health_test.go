package main

import (
	"bytes"
	"strings"
	"testing"
)

func TestGUIHealthcheckRejectsUnsupportedInvocation(t *testing.T) {
	for _, args := range [][]string{{}, {"other"}, {"healthcheck", "unexpected"}, {"healthcheck", "--engines", "extra"}} {
		var output bytes.Buffer
		if err := guiHealthcheck(args, &output); err == nil || !strings.Contains(err.Error(), "usage:") || output.Len() != 0 {
			t.Fatalf("unsupported healthcheck accepted: args=%v, error=%v, output=%q", args, err, output.String())
		}
	}
}
