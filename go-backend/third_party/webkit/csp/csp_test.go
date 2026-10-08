package csp

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/a-h/templ"
)

func TestNonceSharedAcrossEnginesAndFresh(t *testing.T) {
	var seen []string
	h := Middleware(Policy{})(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		n := Nonce(r.Context()); if n == "" || n != templ.GetNonce(r.Context()) { t.Fatal("templ nonce diverged") }
		data := map[string]any{"request":map[string]any{"csp_nonce":"caller", "path":"/"}}
		p := PongoContext(r.Context(), data)
		if p["request"].(map[string]any)["csp_nonce"] != n { t.Fatal("pongo2 nonce diverged") }
		if data["request"].(map[string]any)["csp_nonce"] != "caller" { t.Fatal("caller context mutated") }
		seen = append(seen, n)
		if !strings.Contains(w.Header().Get("Content-Security-Policy"), "'nonce-"+n+"'") { t.Fatal("header nonce diverged") }
		if !strings.Contains(w.Header().Get("Content-Security-Policy-Report-Only"), "require-trusted-types-for 'script'") { t.Fatal("Trusted Types missing") }
	}))
	for range 2 { h.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/", nil)) }
	if seen[0] == seen[1] { t.Fatal("nonce reused between requests") }
}

func TestPolicyFailsClosed(t *testing.T) {
	called := false
	h := Middleware(Policy{ConnectSrc:[]string{"'unsafe-inline'"}})(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { called=true }))
	w := httptest.NewRecorder(); h.ServeHTTP(w, httptest.NewRequest("GET", "/", nil))
	if w.Code != 500 || called { t.Fatal("invalid policy reached handler") }
	h = Middleware(Policy{ReportOnly:true})(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request) {}))
	w = httptest.NewRecorder(); h.ServeHTTP(w, httptest.NewRequest("GET", "/", nil))
	if w.Header().Get("Content-Security-Policy") != "" || !strings.Contains(w.Header().Get("Content-Security-Policy-Report-Only"), "script-src-attr 'none'") { t.Fatal("report-only policy wrong") }
}

func TestReports(t *testing.T) {
	count := 0
	h := ReportHandler(func(ctx context.Context, reports []Report) { count += len(reports) })
	for _, tc := range []struct{method, content, body string; code int}{
		{"POST","application/csp-report",`{"csp-report":{"effective-directive":"script-src"}}`,204},
		{"POST","application/reports+json",`[{"type":"csp-violation"}]`,204},
		{"GET","application/json",`{}`,405}, {"POST","text/html",`{}`,415},
		{"POST","application/json",`null`,400}, {"POST","application/json",`[null]`,400},
		{"POST","application/json",`{`,400}, {"POST","application/json", strings.Repeat("x",65537),413},
	} {
		r := httptest.NewRequest(tc.method,"/csp-report",strings.NewReader(tc.body)); r.Header.Set("Content-Type",tc.content)
		w := httptest.NewRecorder(); h.ServeHTTP(w,r); if w.Code != tc.code { t.Fatalf("%s %s: %d",tc.method,tc.content,w.Code) }
	}
	if count != 2 { t.Fatalf("collector count %d",count) }
}
