package httpapi

import (
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func testServer(t *testing.T) *Server {
	t.Helper()
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	return New(c)
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

func TestUnknownRoutesStayNative404AndCannotLeakGameAnswers(t *testing.T) {
	s := testServer(t)
	for _, path := range []string{"/api/legacy-check?seed=17", "/api/no-such-endpoint", "/api/wordgames/unknown/games"} {
		r := httptest.NewRequest("POST", path, nil)
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		if w.Code != 404 || w.Body.String() != `{"detail":"Not Found"}` {
			t.Fatalf("unknownroute escapednative404: %d %s", w.Code, w.Body.String())
		}
	}
	r := httptest.NewRequest("POST", prefix+"?seed=17", nil)
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != 200 || strings.Contains(w.Body.String(), `"solution"`) {
		t.Fatal("native game unavailable or leaked answer")
	}
}
