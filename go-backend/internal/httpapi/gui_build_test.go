package httpapi

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/guibuild"
	"github.com/DobosP/roedu-ui/web-kit/health"
)

// These are explicit synthetic fixtures, not a compiled-image qualification.
func guiBuildFixture(t *testing.T) (fstest.MapFS, fstest.MapFS, *health.Identity) {
	t.Helper()
	assets := fstest.MapFS{
		"dist/index.html":             &fstest.MapFile{Data: []byte(`<!doctype html><html><head><script type="module" src="/assets/app-1234abcd.js"></script></head><body><div id="root"></div></body></html>`)},
		guibuild.ManifestPath:         &fstest.MapFile{Data: []byte(`{"index.html":{"file":"assets/app-1234abcd.js","isEntry":true}}`)},
		"dist/assets/app-1234abcd.js": &fstest.MapFile{Data: []byte("console.log('fixture')")},
	}
	lock := []byte("{\n  \"schema\": 2, \"test_fixture\": true\n}\n")
	identity, err := health.NewIdentity(strings.Repeat("a", 40), strings.Repeat("b", 64), assets[guibuild.ManifestPath].Data, lock)
	if err != nil {
		t.Fatal(err)
	}
	descriptor, err := json.Marshal(identity)
	if err != nil {
		t.Fatal(err)
	}
	metadata := fstest.MapFS{
		guibuild.DescriptorPath:   &fstest.MapFile{Data: descriptor},
		guibuild.VersionsLockPath: &fstest.MapFile{Data: lock},
	}
	return assets, metadata, identity
}

func guiBuildServer(t *testing.T, assets, metadata fstest.MapFS, mode string) *Server {
	t.Helper()
	s := &Server{allowedHosts: []string{"localhost"}}
	s.managedUI, s.managedUIError = newManagedSPA(assets, "current")
	if s.managedUIError != nil {
		t.Fatal(s.managedUIError)
	}
	s.initGUIBuild(assets, metadata, mode)
	return s
}

func guiBuildRequest(s *Server, method, path string) *httptest.ResponseRecorder {
	w := httptest.NewRecorder()
	s.ServeHTTP(w, httptest.NewRequest(method, "http://localhost:8080"+path, nil))
	return w
}

func TestGUIBuildEndpointUsesExactCompiledBinding(t *testing.T) {
	assets, metadata, expected := guiBuildFixture(t)
	s := guiBuildServer(t, assets, metadata, "current")
	w := guiBuildRequest(s, http.MethodGet, "/api/gui-build")
	if w.Code != http.StatusOK || w.Header().Get("Cache-Control") != "no-store" {
		t.Fatalf("identity response: %d %s", w.Code, w.Body.String())
	}
	var fields map[string]string
	if err := json.Unmarshal(w.Body.Bytes(), &fields); err != nil {
		t.Fatal(err)
	}
	if len(fields) != 4 || fields["sha"] != expected.SHA || fields["tree_sha256"] != expected.TreeSHA256 || fields["manifest_sha256"] != expected.ManifestSHA256 || fields["versions_lock_sha256"] != expected.VersionsLockSHA256 {
		t.Fatalf("exact identity fields differ: %v", fields)
	}
	if w.Header().Get("Content-Type") != "application/json" {
		t.Fatal("identity must be JSON")
	}
	for key, value := range map[string]string{"X-Content-Type-Options": "nosniff", "Referrer-Policy": "same-origin", "Cross-Origin-Opener-Policy": "same-origin"} {
		if w.Header().Get(key) != value {
			t.Fatalf("missing identity header %s", key)
		}
	}
	head := guiBuildRequest(s, http.MethodHead, "/api/gui-build")
	if head.Code != http.StatusOK || head.Body.Len() != 0 || head.Header().Get("Cache-Control") != "no-store" {
		t.Fatal("HEAD identity contract differs")
	}
	for _, method := range []string{http.MethodPost, http.MethodPut, http.MethodDelete, http.MethodOptions} {
		w := guiBuildRequest(s, method, "/api/gui-build")
		if w.Code != http.StatusMethodNotAllowed || w.Header().Get("Allow") != "GET, HEAD" || w.Header().Get("Cache-Control") != "no-store" {
			t.Fatalf("mutation accepted: %s %d", method, w.Code)
		}
	}
}

func TestGUIBuildEndpointUnavailableBindings(t *testing.T) {
	cases := []struct {
		name   string
		change func(fstest.MapFS, fstest.MapFS)
	}{
		{"missing descriptor", func(_, metadata fstest.MapFS) { delete(metadata, guibuild.DescriptorPath) }},
		{"missing lock", func(_, metadata fstest.MapFS) { delete(metadata, guibuild.VersionsLockPath) }},
		{"invalid descriptor", func(_, metadata fstest.MapFS) {
			metadata[guibuild.DescriptorPath].Data = []byte(`{"sha":"placeholder"}`)
		}},
		{"changed manifest", func(assets, _ fstest.MapFS) {
			assets[guibuild.ManifestPath].Data = append(assets[guibuild.ManifestPath].Data, '\n')
		}},
		{"changed lock", func(_, metadata fstest.MapFS) {
			metadata[guibuild.VersionsLockPath].Data = []byte(`{"schema":2,"different":true}`)
		}},
	}
	for _, item := range cases {
		t.Run(item.name, func(t *testing.T) {
			assets, metadata, _ := guiBuildFixture(t)
			item.change(assets, metadata)
			s := guiBuildServer(t, assets, metadata, "current")
			for _, method := range []string{http.MethodGet, http.MethodHead} {
				w := guiBuildRequest(s, method, "/api/gui-build")
				if w.Code != http.StatusServiceUnavailable || w.Header().Get("Cache-Control") != "no-store" {
					t.Fatalf("bad binding response: %d", w.Code)
				}
				if method == http.MethodHead && w.Body.Len() != 0 {
					t.Fatal("unavailable HEAD has a body")
				}
				if method == http.MethodGet && w.Body.String() != `{"detail":"GUI build identity unavailable"}` {
					t.Fatal("unavailable identity leaks metadata or internal error")
				}
			}
		})
	}
}

func TestGUIBuildEndpointRejectsLegacyAndDiskOverride(t *testing.T) {
	for _, mode := range []string{"legacy", "unsupported"} {
		assets, metadata, _ := guiBuildFixture(t)
		s := guiBuildServer(t, assets, metadata, mode)
		if w := guiBuildRequest(s, "GET", "/api/gui-build"); w.Code != 503 {
			t.Fatalf("mode %s claimed current identity", mode)
		}
	}
	assets, metadata, _ := guiBuildFixture(t)
	s := guiBuildServer(t, assets, metadata, "")
	s.StaticRoot = "explicit-test-disk-override"
	if w := guiBuildRequest(s, "GET", "/api/gui-build"); w.Code != 503 {
		t.Fatal("disk override claimed compiled current identity")
	}
	s.StaticRoot = ""
	s.guiBuild = &health.Identity{}
	if w := guiBuildRequest(s, "GET", "/api/gui-build"); w.Code != 503 {
		t.Fatal("invalid identity did not fail closed")
	}
	s.managedUI = nil
	if w := guiBuildRequest(s, "GET", "/api/gui-build"); w.Code != 503 {
		t.Fatal("unavailable managed UI claimed identity")
	}
}

func TestGUIBuildEndpointIgnoresSpoofedRuntimeIdentity(t *testing.T) {
	assets, metadata, expected := guiBuildFixture(t)
	for _, stage := range []string{"before", "after"} {
		t.Run(stage, func(t *testing.T) {
			var s *Server
			if stage == "after" {
				s = guiBuildServer(t, assets, metadata, "current")
			}
			for _, key := range []string{"GATE_SHA", "GATE_TREE_SHA256", "GATE_MANIFEST_SHA256", "GATE_VERSIONS_LOCK_SHA256", "GATE_APP_IMAGE_ID"} {
				t.Setenv(key, strings.Repeat("c", 64))
			}
			if stage == "before" {
				s = guiBuildServer(t, assets, metadata, "current")
			}
			w := guiBuildRequest(s, "GET", "/api/gui-build")
			var actual health.Identity
			if w.Code != 200 {
				t.Fatal("baked identity disappeared after env spoof")
			}
			if err := json.Unmarshal(w.Body.Bytes(), &actual); err != nil {
				t.Fatal(err)
			}
			if actual != *expected {
				t.Fatal("ambient runtime claims changed baked identity")
			}
			missing := guiBuildServer(t, assets, fstest.MapFS{}, "current")
			if w := guiBuildRequest(missing, "GET", "/api/gui-build"); w.Code != 503 {
				t.Fatal("environment filled absent embedded identity")
			}
		})
	}
}

func TestGUIBuildPrivateFilesAndHealthRemainBounded(t *testing.T) {
	assets, metadata, _ := guiBuildFixture(t)
	s := guiBuildServer(t, assets, metadata, "current")
	for _, path := range []string{"/.gui-build.json", "/.vite/manifest.json", "/build/dist/.gui-build.json"} {
		if w := guiBuildRequest(s, "GET", path); w.Code != 404 || strings.Contains(w.Body.String(), strings.Repeat("a", 40)) {
			t.Fatalf("private metadata response: %s %d", path, w.Code)
		}
	}
	if w := guiBuildRequest(s, "GET", "/healthz"); w.Code != 200 || w.Body.String() != `{"ok":true}` {
		t.Fatal("ordinary health changed")
	}
	for _, shape := range []string{"oversize", "host"} {
		r := httptest.NewRequest("GET", "http://localhost:8080/api/gui-build", nil)
		if shape == "oversize" {
			r.ContentLength = MaxRequestBytes + 1
		} else {
			s.allowedHosts = []string{"allowed.test"}
			r.Host = "refused.test"
		}
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		want := 413
		if shape == "host" {
			want = 400
		}
		if w.Code != want {
			t.Fatal(fmt.Sprintf("outer %s guard bypassed: %d", shape, w.Code))
		}
	}
}
