package health

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestCommand(t *testing.T) {
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) }))
	defer s.Close()
	var out bytes.Buffer
	o := Options{URL: s.URL, Engines: func() any { return []string{"Pongo2"} }}
	if err := Command(context.Background(), []string{"healthcheck"}, &out, o); err != nil || out.String() != "healthy\n" { t.Fatalf("command: %q %v", out.String(), err) }
	out.Reset()
	if err := Command(context.Background(), []string{"healthcheck", "--engines"}, &out, o); err != nil || !strings.Contains(out.String(), "Pongo2") { t.Fatalf("engines: %q %v", out.String(), err) }
	for _, args := range [][]string{nil, {"shell"}, {"healthcheck", "--unknown"}, {"healthcheck", "--engines", "extra"}} {
		if err := Command(context.Background(), args, &out, o); err == nil { t.Fatalf("accepted invalid args: %v", args) }
	}
	if err := Command(context.Background(), []string{"healthcheck", "--engines"}, &out, Options{URL:s.URL}); err == nil { t.Fatal("missing engine callback accepted") }
}

func TestUnhealthyAndCanceled(t *testing.T) {
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { http.Error(w, "unhealthy", 503) }))
	defer s.Close()
	if err := Command(context.Background(), []string{"healthcheck"}, &bytes.Buffer{}, Options{URL:s.URL}); err == nil { t.Fatal("503 passed") }
	ctx, cancel := context.WithCancel(context.Background()); cancel()
	if err := Command(ctx, []string{"healthcheck"}, &bytes.Buffer{}, Options{URL:s.URL}); err == nil { t.Fatal("canceled check passed") }
}
