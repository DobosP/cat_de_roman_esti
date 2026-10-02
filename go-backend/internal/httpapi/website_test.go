package httpapi

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestWebsiteLegalPythonConfigurationParity(t *testing.T) {
	raw, e := os.ReadFile("testdata/website_python.json")
	if e != nil {
		t.Fatal(e)
	}
	var data struct {
		Cases []struct {
			Name, Operator, Contact, Version, Privacy, Terms string
			Age                                              int
		}
		PlaceholderSHA256 string `json:"placeholder_sha256"`
	}
	if e = json.Unmarshal(raw, &data); e != nil {
		t.Fatal(e)
	}
	s := testServer(t)
	for _, c := range data.Cases {
		t.Run(c.Name, func(t *testing.T) {
			t.Setenv("CAT_LEGAL_OPERATOR", c.Operator)
			t.Setenv("CAT_LEGAL_CONTACT_EMAIL", c.Contact)
			t.Setenv("CAT_CONSENT_VERSION", c.Version)
			t.Setenv("CAT_MIN_SELF_CONSENT_AGE", fmt.Sprint(c.Age))
			for path, want := range map[string]string{"/legal/privacy": c.Privacy, "/legal/terms": c.Terms} {
				r := httptest.NewRequest("GET", path, nil)
				w := httptest.NewRecorder()
				if !s.website(w, r) || w.Code != 200 {
					t.Fatal("missing legalpage")
				}
				if got := fmt.Sprintf("%x", sha256.Sum256(w.Body.Bytes())); got != want {
					t.Fatalf("%s HTML differsPython: %s wanted%s", path, got, want)
				}
				if w.Header().Get("Content-Type") != "text/html; charset=utf-8" {
					t.Fatal("legal MIME changed")
				}
			}
		})
	}
	if fmt.Sprintf("%x", sha256.Sum256([]byte(missingBuildHTML))) != data.PlaceholderSHA256 {
		t.Fatal("missing build placeholder differsPython")
	}
}
func TestWebsiteMetadataDonationMethodsAndExplicitSubmissionsRefusal(t *testing.T) {
	s := testServer(t)
	t.Setenv("CAT_DONATE_URL", "\x1c https://example.org/donate \u2007")
	for _, method := range []string{"GET", "HEAD", "POST", "OPTIONS", "DELETE"} {
		w := httptest.NewRecorder()
		s.website(w, httptest.NewRequest(method, "/api/me", nil))
		if w.Code != 200 {
			t.Fatalf("anonymousme%d", w.Code)
		}
		if method == "HEAD" {
			if w.Body.Len() != 0 {
				t.Fatal("HEAD body exposed")
			}
			continue
		}
		var v map[string]any
		_ = json.Unmarshal(w.Body.Bytes(), &v)
		if v["donate_url"] != "https://example.org/donate" || v["accounts_enabled"] != false || v["authenticated"] != false || v["user"] != nil {
			t.Fatal("me config drift")
		}
	}
	for _, path := range []string{"/api/health", "/api/categories", "/api/manifest"} {
		for _, method := range []string{"GET", "HEAD", "POST", "OPTIONS"} {
			w := httptest.NewRecorder()
			s.website(w, httptest.NewRequest(method, path, nil))
			status := 200
			if method == "POST" || method == "OPTIONS" {
				status = 405
			}
			if w.Code != status || w.Header().Get("Allow") != "GET, HEAD, OPTIONS" {
				t.Fatal("metadata methods drift")
			}
		}
	}
	for _, method := range []string{"POST", "OPTIONS"} {
		w := httptest.NewRecorder()
		s.website(w, httptest.NewRequest(method, "/api/submissions", strings.NewReader("malformed")))
		status := 503
		if method == "OPTIONS" {
			status = 405
		}
		if w.Code != status {
			t.Fatal("submissions refusal")
		}
	}
	w := httptest.NewRecorder()
	s.website(w, httptest.NewRequest("OPTIONS", "/openapi.json", nil))
	if w.Code != 200 || w.Header().Get("Content-Type") != "application/vnd.oai.openapi+json" || !strings.Contains(w.Body.String(), "Spectacular Jsonapi") {
		t.Fatal("schema OPTIONS metadata differs")
	}
}
func TestWebsiteStaticMethodsCacheConditionalRangesAndFallback(t *testing.T) {
	s := testServer(t)
	root := t.TempDir()
	s.StaticRoot = root
	_ = os.Mkdir(filepath.Join(root, "assets"), 0700)
	index := []byte("<main>arcade</main>")
	_ = os.WriteFile(filepath.Join(root, "index.html"), index, 0600)
	asset := "/assets/code-rz8M-4-f.js"
	file := filepath.Join(root, "assets", "code-rz8M-4-f.js")
	_ = os.WriteFile(file, []byte("0123456789"), 0600)
	modified := time.Unix(1700000000, 0)
	_ = os.Chtimes(file, modified, modified)
	request := func(method, path string, headers map[string]string) *httptest.ResponseRecorder {
		r := httptest.NewRequest(method, path, nil)
		for k, v := range headers {
			r.Header.Set(k, v)
		}
		w := httptest.NewRecorder()
		s.website(w, r)
		return w
	}
	w := request("GET", "/", nil)
	if w.Code != 200 || !strings.HasPrefix(w.Header().Get("Content-Type"), "text/html") || w.Body.String() != string(index) {
		t.Fatal("root must render the SPA as HTML")
	}
	w = request("GET", asset, nil)
	if w.Code != 200 || w.Body.String() != "0123456789" || w.Header().Get("Cache-Control") != "max-age=315360000, public, immutable" || w.Header().Get("ETag") != "\"6553f100-a\"" {
		t.Fatalf("staticfile contract%v", w.Header())
	}
	for _, method := range []string{"POST", "OPTIONS"} {
		w = request(method, asset, nil)
		if w.Code != 405 || w.Header().Get("Allow") != "GET, HEAD" || w.Body.Len() != 0 {
			t.Fatal("static method restrictions")
		}
	}
	w = request("GET", asset, map[string]string{"If-None-Match": "\"6553f100-a\""})
	if w.Code != 304 || w.Body.Len() != 0 {
		t.Fatal("conditional static file")
	}
	w = request("GET", asset, map[string]string{"If-Modified-Since": "Tue, 14 Nov 2023 22:13:20 GMT"})
	if w.Code != 304 {
		t.Fatal("modified since")
	}
	w = request("GET", asset, map[string]string{"Range": "bytes=2-5"})
	if w.Code != 206 || w.Body.String() != "2345" || w.Header().Get("Content-Range") != "bytes 2-5/10" {
		t.Fatal("single byte range")
	}
	w = request("GET", asset, map[string]string{"Range": "bytes=100-"})
	if w.Code != 416 {
		t.Fatal("out ofrange status")
	}
	w = request("GET", asset, map[string]string{"Range": "bytes=0-1,5-6"})
	if w.Code != 200 {
		t.Fatal("unsupportedmultipartmustignore")
	}
	w = request("POST", "/index.html", nil)
	if w.Code != 302 || w.Header().Get("Location") != "/" {
		t.Fatal("index redirect")
	}
	w = request("GET", "/not-a-route", nil)
	if w.Code != 200 || w.Body.String() != string(index) || w.Header().Get("Cache-Control") != "no-cache" {
		t.Fatal("SPAdeep fallback")
	}
	w = request("GET", "/assets/missing.js", nil)
	if w.Code != 404 || w.Body.Len() != 0 {
		t.Fatal("missingassetgotSPA")
	}
	outside := filepath.Join(t.TempDir(), "private.js")
	_ = os.WriteFile(outside, []byte("private"), 0600)
	if os.Symlink(outside, filepath.Join(root, "assets", "escape.js")) == nil {
		w = request("GET", "/assets/escape.js", nil)
		if w.Code != 404 || strings.Contains(w.Body.String(), "private") {
			t.Fatal("staticrootescape")
		}
	}
	s.StaticRoot = t.TempDir()
	w = request("GET", "/", nil)
	if w.Code != 200 || !strings.Contains(w.Body.String(), "npm run build") {
		t.Fatal("no-build root placeholder")
	}
	w = request("GET", "/intrusul", nil)
	if w.Code != 404 {
		t.Fatal("no-builddeep link status")
	}
}
