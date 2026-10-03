package httpapi

import (
	"net/http/httptest"
	"strings"
	"testing"
)

func TestConfiguredHostBoundaryAndRuntimeHeader(t *testing.T) {
	t.Setenv("CAT_DOMAIN", "game.example.org")
	t.Setenv("CAT_ALLOWED_HOSTS", "")
	s := testServer(t)
	for _, host := range []string{"game.example.org", "GAME.EXAMPLE.ORG:443", "game.example.org.", "localhost:8000", "127.0.0.1"} {
		r := httptest.NewRequest("GET", "/healthz", nil)
		r.Host = host
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		if w.Code != 200 || w.Header().Get("X-Cat-Runtime") != "go" {
			t.Fatalf("knownhost%d", w.Code)
		}
	}
	for _, host := range []string{"evil.invalid", "game.example.org.attacker.invalid", "game.example.org bad", ""} {
		r := httptest.NewRequest("GET", "/api/health", nil)
		r.Host = host
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		if w.Code != 400 || w.Body.String() != badHostHTML || w.Header().Get("X-Cat-Runtime") != "go" {
			t.Fatalf("hostboundary%d", w.Code)
		}
	}
	// CORS preflights stop before Django's inner host middleware as well.
	r := httptest.NewRequest("OPTIONS", "/api/health", nil)
	r.Host = "evil.invalid"
	r.Header.Set("Origin", "http://localhost:5173")
	r.Header.Set("Access-Control-Request-Method", "GET")
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != 200 || w.Header().Get("X-Cat-Runtime") != "go" {
		t.Fatal("preflightordering")
	}
}
func TestExplicitHostSuffixRulesAndRuntimeHeaderOnRejections(t *testing.T) {
	t.Setenv("CAT_DOMAIN", "ignored.example.org")
	t.Setenv("CAT_ALLOWED_HOSTS", " .example.org, localhost ")
	s := testServer(t)
	for _, host := range []string{"example.org", "sub.example.org", "localhost"} {
		if !validHost(host, s.allowedHosts) {
			t.Fatal("validconfiguredsuffixrefused")
		}
	}
	if validHost("evil-example.org", s.allowedHosts) {
		t.Fatal("suffixboundaryescaped")
	}
	r := httptest.NewRequest("POST", "/api/wordgames/intrusul/games", strings.NewReader(strings.Repeat("x", MaxRequestBytes+1)))
	r.Host = "localhost"
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != 413 || w.Header().Get("X-Cat-Runtime") != "go" || w.Header().Get("Cache-Control") != "no-store" {
		t.Fatal("operationalheaderabsentrejectedbody")
	}
}
