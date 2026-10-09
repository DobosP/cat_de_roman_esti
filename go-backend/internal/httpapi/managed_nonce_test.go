package httpapi

import (
	"bytes"
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/DobosP/roedu-ui/web-kit/assets"
	"github.com/DobosP/roedu-ui/web-kit/csp"
)

// Inert synthetic source data; authored NOT RUN. No image/browser/M1 proof.
const nonceFixtureIndex = "<!doctype html>\r\n<html lang=\"ro\"><head>\r\n<title>Cât &amp; de român?</title><!--exact metadata-->\r\n<script type=\"module\" crossorigin src=\"/assets/app-1234abcd.js\"></script>\r\n<link rel=\"modulepreload\" crossorigin href=\"/assets/shared-87654321.js\" />\r\n<link rel=\"stylesheet\" crossorigin href=\"/assets/app-1234abcd.css\">\r\n" + nonceFixtureFontLinks + "</head><body><div id=\"root\"></div></body></html>\r\n"

func nonceFixtureManifest(t *testing.T) *assets.Manifest {
	t.Helper()
	files := fstest.MapFS{
		"dist/.vite/manifest.json":       {Data: []byte(`{"index.html":{"file":"assets/app-1234abcd.js","isEntry":true,"imports":["_shared"],"dynamicImports":["lazy"],"css":["assets/app-1234abcd.css"]},"_shared":{"file":"assets/shared-87654321.js"},"lazy":{"file":"assets/lazy-1234abcd.js"}}`)},
		"dist/assets/app-1234abcd.js":    {Data: []byte("export {};")},
		"dist/assets/shared-87654321.js": {Data: []byte("export {};")},
		"dist/assets/lazy-1234abcd.js":   {Data: []byte("export {};")},
		"dist/assets/app-1234abcd.css":   {Data: []byte("body{color:navy}")},
	}
	addManagedFixtureFonts(files, "dist")
	manifest, err := assets.Parse(files, "dist/.vite/manifest.json", "dist", "/")
	if err != nil {
		t.Fatal(err)
	}
	return manifest
}

func assertManagedCurrentIndex(t *testing.T, w *httptest.ResponseRecorder, original []byte) string {
	t.Helper()
	policy := w.Header().Get("Content-Security-Policy")
	if policy == "" {
		policy = w.Header().Get("Content-Security-Policy-Report-Only")
	}
	const marker = "'nonce-"
	start := strings.Index(policy, marker)
	if start < 0 {
		t.Fatalf("missing request nonce: %s", policy)
	}
	tail := policy[start+len(marker):]
	end := strings.IndexByte(tail, '\'')
	if end < 0 {
		t.Fatal("unterminated header nonce")
	}
	nonce := tail[:end]
	if len(nonce) != 32 || !strings.Contains(policy, "script-src 'self' 'nonce-"+nonce+"' 'strict-dynamic'") ||
		!strings.Contains(policy, "style-src 'self' 'nonce-"+nonce+"'") ||
		!strings.Contains(policy, "script-src-attr 'none';") || !strings.Contains(policy, "style-src-attr 'none';") {
		t.Fatal("SDK policy changed")
	}
	meta := `<meta property="csp-nonce" content="` + nonce + `" nonce="` + nonce + `">`
	if bytes.Count(w.Body.Bytes(), []byte(meta)) != 1 {
		t.Fatal("header/bootstrap mismatch")
	}
	unbridged := bytes.Replace(w.Body.Bytes(), []byte(meta), nil, 1)
	unbridged = bytes.ReplaceAll(unbridged, []byte(` nonce="`+nonce+`"`), nil)
	if !bytes.Equal(unbridged, original) {
		t.Fatal("nonce bridge changed original bytes")
	}
	if w.Header().Get("Cache-Control") != "no-store" || w.Header().Get("Content-Length") != strconv.Itoa(w.Body.Len()) {
		t.Fatal("dynamic cache/length changed")
	}
	for key, value := range map[string]string{"X-Content-Type-Options": "nosniff", "Referrer-Policy": "same-origin",
		"Cross-Origin-Opener-Policy": "same-origin", "X-Frame-Options": "DENY", "Content-Type": "text/html; charset=utf-8"} {
		if w.Header().Get(key) != value {
			t.Fatalf("privacy/security header changed: %s", key)
		}
	}
	return nonce
}

func TestManagedNonceShellBytePreservationAndSDKContext(t *testing.T) {
	input := []byte(nonceFixtureIndex)
	shell, err := newManagedNonceShell(input, nonceFixtureManifest(t))
	if err != nil {
		t.Fatal(err)
	}
	input[0] = 'X' // Admitted shell owns its immutable bytes.
	const nonce = "synthetic-source-only-nonce"
	body, err := shell.render(csp.WithNonce(context.Background(), nonce))
	if err != nil {
		t.Fatal(err)
	}
	meta := `<meta property="csp-nonce" content="` + nonce + `" nonce="` + nonce + `">`
	stripped := bytes.Replace(body, []byte(meta), nil, 1)
	stripped = bytes.ReplaceAll(stripped, []byte(` nonce="`+nonce+`"`), nil)
	if !bytes.Equal(stripped, []byte(nonceFixtureIndex)) || bytes.Count(body, []byte(` nonce="`+nonce+`"`)) != 8 ||
		bytes.Contains(body, []byte("lazy-1234abcd.js")) {
		t.Fatal("bytes/static graph/nonce count changed")
	}
	if body, err := shell.render(context.Background()); err == nil || body != nil {
		t.Fatal("missing nonce leaked partial HTML")
	}
	body, err = shell.render(csp.WithNonce(context.Background(), `"><script>alert(1)</script>`))
	if err != nil || bytes.Contains(body, []byte(`<script>alert(1)</script>`)) {
		t.Fatal("nonce not escaped")
	}
}

func TestManagedNonceShellRefusals(t *testing.T) {
	manifest := nonceFixtureManifest(t)
	module := `<script type="module" crossorigin src="/assets/app-1234abcd.js"></script>`
	style := `<link rel="stylesheet" crossorigin href="/assets/app-1234abcd.css">`
	preload := `<link rel="modulepreload" crossorigin href="/assets/shared-87654321.js" />`
	changes := []struct{ name, old, next string }{
		{"missing module", module, ""}, {"duplicate module", module, module + module},
		{"wrong module", "/assets/app-1234abcd.js", "/assets/lazy-1234abcd.js"},
		{"external module", "/assets/app-1234abcd.js", "https://invalid.example/app.js"},
		{"malformed script close", "</script>", "</script forged>"},
		{"inline script", "</script>", "alert(1)</script>"}, {"unterminated script", "</script>", ""},
		{"duplicate src", " crossorigin src=", ` src="/assets/app-1234abcd.js" crossorigin src=`},
		{"duplicate src mixed case", " crossorigin src=", ` SRC="/assets/app-1234abcd.js" crossorigin src=`},
		{"duplicate src HTML whitespace", " crossorigin src=", "\tSRC='/assets/app-1234abcd.js'\f crossOrigin\r\nsrc="},
		{"forged nonce", " crossorigin src=", ` nonce="forged" crossorigin src=`},
		{"unbound attribute", " crossorigin src=", ` integrity="unbound" crossorigin src=`},
		{"credentialed module", " crossorigin src=", ` crossorigin="use-credentials" src=`},
		{"wrong type", `type="module"`, `type="text/javascript"`},
		{"missing style", style, ""}, {"duplicate style", style, style + style},
		{"unowned style", "/assets/app-1234abcd.css", "/assets/other.css"},
		{"alternate style", `rel="stylesheet"`, `rel="alternate stylesheet"`},
		{"missing preload", preload, ""}, {"duplicate preload", preload, preload + preload},
		{"dynamic preload", "/assets/shared-87654321.js", "/assets/lazy-1234abcd.js"},
		{"duplicate html", "<html lang=\"ro\">", "<html lang=\"ro\"><html>"},
		{"missing html close", "</html>", ""},
		{"malformed head close", "</head>", "</head forged>"},
		{"trailing unfinished script", "</html>", "</html><script"},
		{"duplicate head", "<head>", "<head><head>"}, {"missing head close", "</head>", ""},
		{"duplicate head attr", "<head>", `<head id="a" id="b">`},
		{"forged head nonce", "<head>", `<head nonce="forged">`},
		{"nonce meta property", "<head>", `<head><meta property="csp-nonce" content="forged">`},
		{"nonce meta name", "<head>", `<head><meta name="CSP-NONCE" content="forged">`},
		{"duplicate meta attr", "<head>", `<head><meta property="x" property="csp-nonce">`},
		{"duplicate meta attr mixed case", "<head>", `<head><meta PROPERTY='x' property="csp-nonce">`},
		{"duplicate unquoted meta attr", "<head>", `<head><meta property=x PROPERTY=csp-nonce>`},
		{"policy meta", "<head>", `<head><meta http-equiv="Content-Security-Policy" content="default-src *">`},
		{"base URL", "<head>", `<head><base href="https://invalid.example/">`},
		{"inline style", "<head>", "<head><style>body{color:red}</style>"},
		{"style attr", "<body>", `<body style="color:red">`},
		{"inline handler", "<body>", `<body onload="alert(1)">`},
		{"inert module", module, "<template>" + module + "</template>"},
		{"missing root", `<div id="root"></div>`, ""},
		{"duplicate root", `<div id="root"></div>`, `<div id="root"></div><div id="root"></div>`},
	}
	for _, fixture := range changes {
		t.Run(fixture.name, func(t *testing.T) {
			source := strings.Replace(nonceFixtureIndex, fixture.old, fixture.next, 1)
			if source == nonceFixtureIndex {
				t.Fatal("counterexample failed to mutate source")
			}
			if shell, err := newManagedNonceShell([]byte(source), manifest); err == nil || shell != nil {
				t.Fatal("invalid shell admitted")
			}
		})
	}
	bodyModule := strings.Replace(strings.Replace(nonceFixtureIndex, module, "", 1), "<body>", "<body>"+module, 1)
	if shell, err := newManagedNonceShell([]byte(bodyModule), manifest); err == nil || shell != nil {
		t.Fatal("module in body admitted")
	}
	if shell, err := newManagedNonceShell([]byte(nonceFixtureIndex), nil); err == nil || shell != nil {
		t.Fatal("nil manifest admitted")
	}
	// Valid raw boundaries must still admit an unchanged shell. These values
	// contain name-like text, entities and URL slashes but no duplicate names.
	for _, boundary := range []struct{ old, next string }{
		{"<head>", `<head><meta name="description" content='property="x" property="y" / &amp; src=sample'>`},
		{"<head>", `<head><meta name='description' content="property='x' property='y' / &quot;src=sample&quot;">`},
		{"<head>", `<head><meta name=description content=/assets/path/to/value/>`},
		{`src="/assets/app-1234abcd.js"`, `src=/assets/app-1234abcd.js`},
		{`src="/assets/app-1234abcd.js"`, `src='/assets/app&#45;1234abcd.js'`},
		{`href="/assets/app-1234abcd.css"`, `href='/assets/app&#45;1234abcd.css'`},
	} {
		source := strings.Replace(nonceFixtureIndex, boundary.old, boundary.next, 1)
		shell, err := newManagedNonceShell([]byte(source), manifest)
		if err != nil || shell == nil {
			t.Fatalf("valid raw value boundary refused: %s: %v", boundary.next, err)
		}
		if !bytes.Equal(shell.index, []byte(source)) {
			t.Fatal("raw boundary admission rewrote original bytes")
		}
		body, err := shell.render(csp.WithNonce(context.Background(), "raw-boundary-test-nonce"))
		if err != nil {
			t.Fatal(err)
		}
		body = bytes.Replace(body, []byte(`<meta property="csp-nonce" content="raw-boundary-test-nonce" nonce="raw-boundary-test-nonce">`), nil, 1)
		body = bytes.ReplaceAll(body, []byte(` nonce="raw-boundary-test-nonce"`), nil)
		if !bytes.Equal(body, []byte(source)) {
			t.Fatal("nonce insertion changed original raw value or byte offset")
		}
	}
}

func TestManagedNonceResponseFreshnessAndStages(t *testing.T) {
	for _, enforce := range []string{"false", "true"} {
		t.Run(enforce, func(t *testing.T) {
			t.Setenv("CAT_CSP_ENFORCE", enforce)
			files := managedSPAFixture()
			s := testServer(t)
			var err error
			s.managedUI, err = newManagedSPA(files, "current")
			if err != nil {
				t.Fatal(err)
			}
			seen := map[string]bool{}
			for _, route := range []string{"/", "/intrusul?challenge=daily", "/alchimie?mode=explore", "/"} {
				r := httptest.NewRequest("GET", route, nil)
				r.Header.Set("X-CSP-Nonce", "attacker-controlled")
				r.Header.Set("If-None-Match", `"stale-document"`)
				w := httptest.NewRecorder()
				s.ServeHTTP(w, r)
				if w.Code != 200 {
					t.Fatal(w.Code)
				}
				nonce := assertManagedCurrentIndex(t, w, files["dist/index.html"].Data)
				if seen[nonce] {
					t.Fatal("request/deep-link nonce reused")
				}
				seen[nonce] = true
				const tt = "require-trusted-types-for 'script'; trusted-types roedu roedu-hovercard roedu-islands; report-uri /csp-report"
				if enforce == "true" {
					if w.Header().Get("Content-Security-Policy") == "" || w.Header().Get("Content-Security-Policy-Report-Only") != tt {
						t.Fatal("enforced/TT-only policy changed")
					}
				} else if w.Header().Get("Content-Security-Policy") != "" || !strings.Contains(w.Header().Get("Content-Security-Policy-Report-Only"), "require-trusted-types-for 'script'") {
					t.Fatal("preliminary actual policy changed")
				}
			}
			w := managedSPARequest(s, "HEAD", "/intrusul")
			if w.Code != 200 || w.Body.Len() != 0 || w.Header().Get("Cache-Control") != "no-store" || w.Header().Get("Content-Length") == "" {
				t.Fatal("HEAD changed")
			}
			for _, route := range []string{"/api/health", "/assets/app-1234abcd.js"} {
				w = managedSPARequest(s, "GET", route)
				if w.Code != 200 || w.Header().Get("Content-Security-Policy") != "" {
					t.Fatal("nonce changed API/assets route")
				}
				if strings.HasPrefix(route, "/assets/") && !bytes.Equal(w.Body.Bytes(), files["dist"+route].Data) {
					t.Fatal("asset bytes changed")
				}
			}
		})
	}
}

func TestManagedNonceLegacyAndInvalidFlag(t *testing.T) {
	t.Setenv("CAT_CSP_ENFORCE", "true")
	files := managedSPAFixture()
	s := testServer(t)
	var err error
	s.managedUI, err = newManagedSPA(files, "legacy")
	if err != nil {
		t.Fatal(err)
	}
	w := managedSPARequest(s, "GET", "/intrusul")
	if w.Code != 200 || !bytes.Equal(w.Body.Bytes(), files["legacy/index.html"].Data) ||
		w.Header().Get("Content-Security-Policy") != "" || w.Header().Get("Content-Security-Policy-Report-Only") != "" ||
		w.Header().Get("Cache-Control") != "no-cache" {
		t.Fatal("legacy bytes/policy changed")
	}
	t.Setenv("CAT_CSP_ENFORCE", "TRUE")
	if ui, err := newManagedSPA(files, "current"); err == nil || ui != nil {
		t.Fatal("invalid flag silently weakened policy")
	}
	s.managedUI, s.managedUIError = newManagedSPA(files, "current")
	if w := managedSPARequest(s, "GET", "/"); w.Code != 503 {
		t.Fatal("invalid admission returned raw HTML")
	}
}

func TestManagedCSPReportReceiverBoundsWithoutPersistence(t *testing.T) {
	t.Setenv("CAT_CSP_ENFORCE", "true")
	s := testServer(t)
	s.allowedHosts = []string{"example.com"}
	var err error
	s.managedUI, err = newManagedSPA(managedSPAFixture(), "current")
	if err != nil {
		t.Fatal(err)
	}
	cases := []struct {
		name, method, media, body string
		status                    int
	}{
		{"legacy object", "POST", "application/csp-report", `{"csp-report":{"blocked-uri":"synthetic-private-path","script-sample":"synthetic-sample"}}`, 204},
		{"report array", "POST", "application/reports+json", `[{"type":"csp-violation","body":{"documentURL":"synthetic-private-query"}}]`, 204},
		{"json object", "POST", "application/json", `{"synthetic":true}`, 204},
		{"GET", "GET", "application/json", "", 405},
		{"HEAD", "HEAD", "application/json", "", 405},
		{"wrong media", "POST", "text/plain", `{"synthetic":true}`, 415},
		{"malformed", "POST", "application/json", "{", 400},
		{"null", "POST", "application/json", "null", 400},
		{"empty array", "POST", "application/json", "[]", 400},
		{"null member", "POST", "application/json", "[null]", 400},
		{"too many reports", "POST", "application/reports+json", "[" + strings.Repeat("{},", 100) + "{}]", 400},
		{"oversize", "POST", "application/json", strings.Repeat("x", MaxRequestBytes+1), 413},
	}
	for _, fixture := range cases {
		t.Run(fixture.name, func(t *testing.T) {
			r := httptest.NewRequest(fixture.method, "/csp-report", strings.NewReader(fixture.body))
			r.Header.Set("Content-Type", fixture.media)
			w := httptest.NewRecorder()
			s.ServeHTTP(w, r)
			if w.Code != fixture.status || w.Header().Get("Referrer-Policy") != "same-origin" {
				t.Fatal("report contract changed", w.Code)
			}
			if fixture.status == 204 && (w.Body.Len() != 0 || w.Header().Get("Cache-Control") != "no-store") {
				t.Fatal("report echoed data or lost no-store")
			}
			if strings.Contains(w.Body.String(), "synthetic-private") || strings.Contains(w.Body.String(), "synthetic-sample") {
				t.Fatal("report payload escaped")
			}
			if fixture.status == 405 && w.Header().Get("Allow") != "POST" {
				t.Fatal("report method boundary changed")
			}
		})
	}
	r := httptest.NewRequest("POST", "/csp-report", strings.NewReader("{}"))
	r.Host = "unadmitted.invalid"
	r.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != 400 {
		t.Fatal("report receiver bypassed host refusal")
	}
}

// Cancellation/error cases are authored NOT RUN. Actual SDK entropy failure is
// not injected by changing crypto/rand.Reader or vendor source. The outer wrapper
// precedes that same shipped middleware; the actual invalid-policy branch below
// causally checks an SDK refusal before the renderer can be called.
func TestManagedNonceCanceledContextAndRequestRefuseHTML(t *testing.T) {
	shell, err := newManagedNonceShell([]byte(nonceFixtureIndex), nonceFixtureManifest(t))
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(csp.WithNonce(context.Background(), "synthetic-source-only-nonce"))
	cancel()
	if body, err := shell.render(ctx); !errors.Is(err, context.Canceled) || body != nil {
		t.Fatal("canceled context produced HTML")
	}
	t.Setenv("CAT_CSP_ENFORCE", "true")
	s := testServer(t)
	s.managedUI, err = newManagedSPA(managedSPAFixture(), "current")
	if err != nil {
		t.Fatal(err)
	}
	r := httptest.NewRequest("GET", "/intrusul", nil).WithContext(ctx)
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != 500 || w.Body.Len() != 0 || w.Header().Get("Cache-Control") != "no-store" ||
		w.Header().Get("Referrer-Policy") != "same-origin" {
		t.Fatal("canceled current document escaped refusal/no-store")
	}
}

func TestManagedNonceRenderAndSDKRefusalsAreNoStore(t *testing.T) {
	shell, err := newManagedNonceShell([]byte(nonceFixtureIndex), nonceFixtureManifest(t))
	if err != nil {
		t.Fatal(err)
	}
	ui := &managedSPA{nonceShell: shell}
	w := httptest.NewRecorder()
	managedNonceNoStore(http.HandlerFunc(ui.serveIndex)).ServeHTTP(w, httptest.NewRequest("GET", "/", nil))
	if w.Code != 500 || w.Body.Len() != 0 || w.Header().Get("Cache-Control") != "no-store" {
		t.Fatal("missing-nonce render refusal cacheable")
	}
	called := false
	invalid := csp.Middleware(csp.Policy{ReportPath: "//refused"})(http.HandlerFunc(func(http.ResponseWriter, *http.Request) { called = true }))
	w = httptest.NewRecorder()
	managedNonceNoStore(invalid).ServeHTTP(w, httptest.NewRequest("GET", "/", nil))
	if w.Code != 500 || called || w.Body.String() != "CSP policy invalid\n" || w.Header().Get("Cache-Control") != "no-store" ||
		strings.Contains(w.Body.String(), "<html") || w.Header().Get("Content-Security-Policy") != "" {
		t.Fatal("SDK pre-render refusal lost no-store")
	}
}
