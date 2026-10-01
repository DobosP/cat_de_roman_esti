package httpapi

import (
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

type transportFunc func(*http.Request) (*http.Response, error)

func (f transportFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func testServer(t *testing.T) *Server {
	t.Helper()
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	return New(c, nil)
}

func TestChunkedBodiesBoundedBeforeDispatch(t *testing.T) {
	s := testServer(t)
	for _, path := range []string{prefix, prefix + "/missing/hint", prefix + "/missing", "/healthz"} {
		r := httptest.NewRequest("POST", path, strings.NewReader(strings.Repeat(" ", MaxRequestBytes+1)))
		r.ContentLength = -1
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		if w.Code != 413 || w.Body.String() != `{"detail":"Request body too large"}` {
			t.Fatalf("%s: %d %s", path, w.Code, w.Body.String())
		}
	}
}

func TestLocalCorsPreflight(t *testing.T) {
	s := testServer(t)
	for _, origin := range []string{"http://localhost:5173", "http://127.0.0.1:9000", "http://localhost"} {
		r := httptest.NewRequest("OPTIONS", prefix, nil)
		r.Header.Set("Origin", origin)
		r.Header.Set("Access-Control-Request-Method", "POST")
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		if w.Code != 200 || w.Body.Len() != 0 || w.Header().Get("Access-Control-Allow-Origin") != origin || w.Header().Get("Access-Control-Allow-Credentials") != "true" {
			t.Fatalf("CORS parity failed: %v", w.Result())
		}
	}
	r := httptest.NewRequest("OPTIONS", prefix, nil)
	r.Header.Set("Origin", "http://localhost.attacker.invalid:5173")
	r.Header.Set("Access-Control-Request-Method", "POST")
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != 405 || w.Header().Get("Access-Control-Allow-Origin") != "" {
		t.Fatal("untrusted origin accepted")
	}
}

func TestRemainingRoutesDelegateWithoutNativeGameLeaks(t *testing.T) {
	s := testServer(t)
	target, _ := url.Parse("http://127.0.0.1:8000")
	s = New(s.content, target)
	calls := 0
	s.proxy.Transport = transportFunc(func(r *http.Request) (*http.Response, error) {
		calls++
		if r.URL.Path != "/api/wordgames/perechi/games" || r.URL.RawQuery != "seed=17" {
			t.Fatalf("proxy changed route: %s", r.URL)
		}
		return &http.Response{StatusCode: 200, Header: make(http.Header), Body: io.NopCloser(strings.NewReader(`{"legacy":true}`))}, nil
	})
	r := httptest.NewRequest("POST", "/api/wordgames/perechi/games?seed=17", nil)
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != 200 || w.Body.String() != `{"legacy":true}` || calls != 1 {
		t.Fatal("legacy delegation failed")
	}
	r = httptest.NewRequest("POST", prefix+"?seed=17", nil)
	w = httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != 200 || calls != 1 || strings.Contains(w.Body.String(), `"solution"`) {
		t.Fatal("native game delegated or leaked answer")
	}
}
