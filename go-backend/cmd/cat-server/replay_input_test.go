package main

import (
	"strings"
	"testing"
)

func TestPrivateReplaySchemaUnicodeAndURIRefusals(t *testing.T) {
	for _, raw := range []string{`{"Path":"/","Unknown":1}`, `{"Path":"/","Method":"GET","method":"POST"}`, `{"Path":"/","Method":"GET","Method":"POST"}`, `{"Path":"\ud800"}`, `{"Path":"/","Headers":{"x":"\udfff"}}`, `{"Path":"http://example.invalid/"}`, `{"Path":"/\u0000"}`, `{"Path":"/","Method":"GET injected"}`, `{"Path":"/","Headers":{"x":"a\r\nb"}}`, `{"Path":"/","Headers":{"x":1}}`, `null`, `{"path":"/","method":null}`, `{"path":"/","body":null}`, `{"path":"/","headers":null}`, `{"path":"/","headers":{"X-Test":null}}`} {
		if _, err := decodeReplayInput([]byte(raw)); err == nil {
			t.Fatal("malformed private IPC accepted", raw)
		}
	}
	input, err := decodeReplayInput([]byte(`{"Method":"POST","Path":"/api/wordgames/contexto/games/fixture/guess","Body":"{\"text\":\"\\ud800\"}"}`))
	if err != nil || !strings.Contains(input.Body, `\ud800`) {
		t.Fatal("domain negative raw body was repaired or rejected", err)
	}
}
