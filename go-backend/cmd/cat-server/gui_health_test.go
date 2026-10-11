package main

import (
	"bytes"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestGUIHealthcheckRejectsUnsupportedInvocation(t *testing.T) {
	t.Setenv("PORT", "")
	for _, args := range [][]string{{}, {"other"}, {"healthcheck", "unexpected"}, {"healthcheck", "--engines", "extra"}} {
		var output bytes.Buffer
		if err := guiHealthcheck(args, &output); err == nil || !strings.Contains(err.Error(), "usage:") || output.Len() != 0 {
			t.Fatalf("unsupported healthcheck accepted: args=%v, error=%v, output=%q", args, err, output.String())
		}
	}
}

func TestGUIListenAddressReadsPortWithDefault8000(t *testing.T) {
	for _, c := range []struct{ port, want string }{{"", ":8000"}, {"8080", ":8080"}, {"1", ":1"}, {"65535", ":65535"}, {"08000", ":8000"}} {
		t.Setenv("PORT", c.port)
		if got, err := listenAddress("", false); err != nil || got != c.want {
			t.Fatalf("PORT=%q: listen=%q, error=%v; want %q", c.port, got, err, c.want)
		}
	}
}

func TestGUIListenAddressRefusesInvalidPort(t *testing.T) {
	for _, port := range []string{"abc", "0", "00000", "65536", "123456", "-1", "+80", " 80", "80 ", "8.0", "0x50", "٨٠", "８０", ":8000"} {
		t.Setenv("PORT", port)
		if got, err := listenAddress("", false); err == nil || got != "" || !strings.Contains(err.Error(), "PORT") || strings.Contains(err.Error(), port) {
			t.Fatalf("PORT=%q accepted or echoed: listen=%q, error=%v", port, got, err)
		}
		var output bytes.Buffer
		if err := guiHealthcheck([]string{"healthcheck"}, &output); err == nil || !strings.Contains(err.Error(), "PORT") || output.Len() != 0 {
			t.Fatalf("healthcheck PORT=%q accepted: error=%v, output=%q", port, err, output.String())
		}
	}
}

func TestGUIExplicitListenWinsOverPort(t *testing.T) {
	for _, port := range []string{"", "8080", "abc"} {
		t.Setenv("PORT", port)
		if got, err := listenAddress("127.0.0.1:8081", true); err != nil || got != "127.0.0.1:8081" {
			t.Fatalf("PORT=%q overrode explicit -listen: listen=%q, error=%v", port, got, err)
		}
	}
}

func TestGUIHealthcheckProbesPortOnLoopback(t *testing.T) {
	paths := make(chan string, 1)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		paths <- r.URL.Path
		w.Write([]byte(`{"ok":true}`))
	}))
	defer server.Close()
	host, port, err := net.SplitHostPort(server.Listener.Addr().String())
	if err != nil || host != "127.0.0.1" {
		t.Fatalf("test server not on IPv4 loopback: %v %q", err, host)
	}
	t.Setenv("PORT", port)
	var output bytes.Buffer
	if err := guiHealthcheck([]string{"healthcheck"}, &output); err != nil || output.String() != "healthy\n" {
		t.Fatalf("healthcheck on PORT=%s: error=%v, output=%q", port, err, output.String())
	}
	if path := <-paths; path != "/healthz" {
		t.Fatalf("healthcheck probed %q", path)
	}
}
