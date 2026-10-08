package httpapi

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io/fs"
	"net/http/httptest"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/DobosP/cat_de_roman_esti/go-backend/embedfs"
)

func managedSPAFixture() fstest.MapFS {
	files := fstest.MapFS{}
	for _, root := range []string{"dist", "legacy"} {
		files[root+"/index.html"] = &fstest.MapFile{Data: []byte("<!doctype html><html lang=\"ro\"><head><script type=\"module\" crossorigin src=\"/assets/app-1234abcd.js\"></script><link rel=\"stylesheet\" crossorigin href=\"/assets/app-1234abcd.css\"></head><body><div id=\"root\"></div><!--" + root + "--></body></html>")}
		files[root+"/.vite/manifest.json"] = &fstest.MapFile{Data: []byte(`{"index.html":{"file":"assets/app-1234abcd.js","isEntry":true,"css":["assets/app-1234abcd.css"]}}`)}
		files[root+"/assets/app-1234abcd.js"] = &fstest.MapFile{Data: []byte("console.log('" + root + "');")}
		files[root+"/assets/app-1234abcd.css"] = &fstest.MapFile{Data: []byte("body{color:navy}")}
		files[root+"/.keep"] = &fstest.MapFile{}
	}
	return files
}

func managedSPARequest(s *Server, method, path string) *httptest.ResponseRecorder {
	w := httptest.NewRecorder()
	s.ServeHTTP(w, httptest.NewRequest(method, path, nil))
	return w
}

// This case deliberately requires the actual owning build/sync before Go tests:
// checked-in .keep files cannot masquerade as a usable production UI bundle.
func TestManagedSPACompiledCurrentAndFrozenLegacy(t *testing.T) {
	for _, mode := range []string{"current", "legacy"} {
		t.Run(mode, func(t *testing.T) {
			t.Setenv("CAT_UI", mode)
			root := "dist"
			if mode == "legacy" {
				root = "legacy"
			}
			index, err := fs.ReadFile(embedfs.Files, root+"/index.html")
			if err != nil {
				t.Fatalf("owning frontend build and assets-sync required: %v", err)
			}
			s := testServer(t)
			if s.StaticRoot != "" || s.managedUIError != nil || s.managedUI == nil {
				t.Fatalf("default server did not admit compiled %s: %v", mode, s.managedUIError)
			}
			w := managedSPARequest(s, "GET", "/intrusul?challenge=daily")
			if w.Code != 200 {
				t.Fatal("compiled selected tree was not the SPA deep-link response")
			}
			if mode == "legacy" {
				if !bytes.Equal(w.Body.Bytes(), index) {
					t.Fatal("compiled frozen legacy response changed bytes")
				}
			} else {
				assertManagedCurrentIndex(t, w, index)
			}
			if mode == "legacy" && fmt.Sprintf("%x", sha256.Sum256(index)) != "6ef9e2cd5334b0e89fe078f0bf2c3c9b3b94360ad013c7740db5cc205bd3feeb" {
				t.Fatal("compiled rollback index differs from the sealed thirty-file original")
			}
			manifestBytes, err := fs.ReadFile(embedfs.Files, root+"/.vite/manifest.json")
			if err != nil {
				t.Fatal(err)
			}
			var manifest map[string]struct {
				File string `json:"file"`
			}
			if err := json.Unmarshal(manifestBytes, &manifest); err != nil {
				t.Fatal(err)
			}
			entry := manifest["index.html"].File
			asset, err := fs.ReadFile(embedfs.Files, root+"/"+entry)
			if err != nil {
				t.Fatal(err)
			}
			w = managedSPARequest(s, "GET", "/"+entry)
			if w.Code != 200 || !bytes.Equal(w.Body.Bytes(), asset) {
				t.Fatal("SDK static response differs from the selected compiled manifest entry")
			}
		})
	}
}

func TestManagedSPADeepLinksAndAPIRouting(t *testing.T) {
	s := testServer(t)
	var err error
	s.managedUI, err = newManagedSPA(managedSPAFixture(), "current")
	if err != nil {
		t.Fatal(err)
	}
	s.managedUIError = nil
	for _, path := range []string{"/", "/intrusul", "/alchimie?mode=explore", "/not-a-route"} {
		w := managedSPARequest(s, "GET", path)
		if w.Code != 200 {
			t.Fatalf("SPA fallback failed for %s: %d", path, w.Code)
		}
		assertManagedCurrentIndex(t, w, s.managedUI.index)
	}
	for _, path := range []string{"/api", "/api/no-such-endpoint", "/api/wordgames/unknown/games"} {
		w := managedSPARequest(s, "GET", path)
		if w.Code != 404 || w.Body.String() != `{"detail":"Not Found"}` || w.Header().Get("Content-Type") != "application/json" {
			t.Fatalf("API route received SPA fallback: %s %d %s", path, w.Code, w.Body.String())
		}
	}
	w := managedSPARequest(s, "GET", "/api/health")
	if w.Code != 200 || w.Header().Get("Content-Type") != "application/json" {
		t.Fatal("known API stopped being native JSON")
	}
}

func TestManagedSPASDKAssetsAndMethodContracts(t *testing.T) {
	s := testServer(t)
	files := managedSPAFixture()
	var err error
	s.managedUI, err = newManagedSPA(files, "")
	if err != nil {
		t.Fatal(err)
	}
	s.managedUIError = nil
	asset := "/assets/app-1234abcd.js"
	w := managedSPARequest(s, "GET", asset)
	if w.Code != 200 || !bytes.Equal(w.Body.Bytes(), files["dist"+asset].Data) || !strings.Contains(w.Header().Get("Content-Type"), "javascript") || w.Header().Get("X-Content-Type-Options") != "nosniff" {
		t.Fatalf("actual SDK static handler did not serve selected embedded bytes: %d %v", w.Code, w.Header())
	}
	w = managedSPARequest(s, "HEAD", asset)
	if w.Code != 200 || w.Body.Len() != 0 {
		t.Fatal("embedded asset HEAD exposed a body")
	}
	for _, path := range []string{"/", "/intrusul", asset} {
		w = managedSPARequest(s, "POST", path)
		if w.Code != 405 || w.Header().Get("Allow") != "GET, HEAD" || w.Body.Len() != 0 {
			t.Fatalf("managed UI method contract: %s", path)
		}
	}
	w = managedSPARequest(s, "POST", "/index.html")
	if w.Code != 302 || w.Header().Get("Location") != "/" {
		t.Fatal("index redirect changed")
	}
}

func TestManagedSPARefusesPrivateAndMissingAssets(t *testing.T) {
	s := testServer(t)
	var err error
	s.managedUI, err = newManagedSPA(managedSPAFixture(), "")
	if err != nil {
		t.Fatal(err)
	}
	s.managedUIError = nil
	for _, path := range []string{"/.vite/manifest.json", "/.keep", "/assets/../index.html", "/assets/escape%5C.js", "/assets/missing.js", "/assets/app-1234abcd.js.gz", "/missing.json", "/assets//app-1234abcd.js"} {
		w := managedSPARequest(s, "GET", path)
		if w.Code != 404 || w.Body.Len() != 0 {
			t.Fatalf("private or missing asset escaped refusal: %s %d %s", path, w.Code, w.Body.String())
		}
	}
}

func TestManagedSPARejectsMalformedOrUnconfinedInput(t *testing.T) {
	if _, err := newManagedSPA(managedSPAFixture(), "../../private"); err == nil {
		t.Fatal("unbounded CAT_UI selection accepted")
	}
	for _, change := range []func(fstest.MapFS){
		func(files fstest.MapFS) { delete(files, "dist/assets/app-1234abcd.js") },
		func(files fstest.MapFS) {
			files["dist/.vite/manifest.json"].Data = []byte(`{"index.html":{"file":"../private.js","isEntry":true}}`)
		},
		func(files fstest.MapFS) {
			files["dist/.vite/manifest.json"].Data = []byte(`{"index.html":{"file":"assets/app-1234abcd.js","imports":["missing"],"isEntry":true}}`)
		},
		func(files fstest.MapFS) { files["dist/index.html"].Data = nil },
		func(files fstest.MapFS) {
			files["dist/assets/escape.js"] = &fstest.MapFile{Mode: fs.ModeSymlink, Data: []byte("private")}
		},
	} {
		files := managedSPAFixture()
		change(files)
		if _, err := newManagedSPA(files, "current"); err == nil {
			t.Fatal("invalid managed bundle admitted")
		}
	}
}

func TestManagedSPAUnbuiltScaffoldDoesNotAdmitUI(t *testing.T) {
	s := testServer(t)
	s.managedUI, s.managedUIError = newManagedSPA(fstest.MapFS{"dist/.keep": &fstest.MapFile{}}, "current")
	if s.managedUI != nil || s.managedUIError == nil {
		t.Fatal("empty scaffold became a usable UI bundle")
	}
	w := managedSPARequest(s, "GET", "/")
	if w.Code != 503 || w.Body.String() != `{"detail":"Managed UI unavailable"}` {
		t.Fatal("unbuilt UI earned a successful response")
	}
	w = managedSPARequest(s, "GET", "/api/health")
	if w.Code != 200 || w.Header().Get("Content-Type") != "application/json" {
		t.Fatal("UI admission failure changed native API availability")
	}
}

func TestManagedSPANonHexViteCacheUsesActualSDKStatus(t *testing.T) {
	s := testServer(t)
	files := managedSPAFixture()
	asset := "/assets/AccountBar-B_1k6UL8.js"
	files["dist"+asset] = &fstest.MapFile{Data: []byte("console.log('non-hex-vite-hash');")}
	files["dist/.vite/manifest.json"].Data = []byte(`{"index.html":{"file":"assets/AccountBar-B_1k6UL8.js","isEntry":true,"css":["assets/app-1234abcd.css"]}}`)
	files["dist/index.html"].Data = bytes.Replace(files["dist/index.html"].Data, []byte("/assets/app-1234abcd.js"), []byte(asset), 1)
	var err error
	s.managedUI, err = newManagedSPA(files, "current")
	if err != nil {
		t.Fatal(err)
	}
	s.managedUIError = nil
	var validator string
	for _, method := range []string{"GET", "HEAD"} {
		w := managedSPARequest(s, method, asset)
		if w.Code != 200 || w.Header().Get("Cache-Control") != "max-age=315360000, public, immutable" {
			t.Fatalf("non-hex Vite hash lost Cat's cache contract: %s %d %v", method, w.Code, w.Header())
		}
		if method == "GET" && !bytes.Equal(w.Body.Bytes(), files["dist"+asset].Data) {
			t.Fatal("cache adapter changed SDK asset bytes")
		}
		if method == "HEAD" && w.Body.Len() != 0 {
			t.Fatal("cache adapter changed SDK HEAD")
		}
		if method == "GET" {
			validator = w.Header().Get("ETag")
			if validator == "" {
				t.Fatal("actual SDK asset response has no conditional validator")
			}
		} else if w.Header().Get("ETag") != validator {
			t.Fatal("SDK HEAD validator differs from GET")
		}
	}
	rangeRequest := httptest.NewRequest("GET", asset, nil)
	rangeRequest.Header.Set("Range", "bytes=2-5")
	rangeResponse := httptest.NewRecorder()
	s.ServeHTTP(rangeResponse, rangeRequest)
	if rangeResponse.Code != 206 || !bytes.Equal(rangeResponse.Body.Bytes(), files["dist"+asset].Data[2:6]) || rangeResponse.Header().Get("Content-Range") != fmt.Sprintf("bytes 2-5/%d", len(files["dist"+asset].Data)) || rangeResponse.Header().Get("Content-Length") != "4" || rangeResponse.Header().Get("ETag") != validator || rangeResponse.Header().Get("Cache-Control") != "max-age=315360000, public, immutable" {
		t.Fatalf("positive SDK range lost bytes, validator or Cat caching: %d %v %q", rangeResponse.Code, rangeResponse.Header(), rangeResponse.Body.String())
	}
	conditionalRequest := httptest.NewRequest("GET", asset, nil)
	conditionalRequest.Header.Set("If-None-Match", validator)
	conditionalResponse := httptest.NewRecorder()
	s.ServeHTTP(conditionalResponse, conditionalRequest)
	if conditionalResponse.Code != 304 || conditionalResponse.Body.Len() != 0 || conditionalResponse.Header().Get("ETag") != validator || conditionalResponse.Header().Get("Content-Range") != "" || conditionalResponse.Header().Get("Cache-Control") != "max-age=315360000, public, immutable" {
		t.Fatalf("matching actual SDK validator lost conditional cache contract: %d %v", conditionalResponse.Code, conditionalResponse.Header())
	}
	conditionalRequest = httptest.NewRequest("GET", asset, nil)
	conditionalRequest.Header.Set("If-None-Match", `"cat-unmatched-validator"`)
	conditionalResponse = httptest.NewRecorder()
	s.ServeHTTP(conditionalResponse, conditionalRequest)
	if conditionalResponse.Code != 200 || !bytes.Equal(conditionalResponse.Body.Bytes(), files["dist"+asset].Data) || conditionalResponse.Header().Get("ETag") != validator || conditionalResponse.Header().Get("Cache-Control") != "max-age=315360000, public, immutable" {
		t.Fatal("nonmatching validator incorrectly suppressed the actual SDK asset")
	}
	r := httptest.NewRequest("GET", asset, nil)
	r.Header.Set("Range", "bytes=999999-")
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != 416 || strings.Contains(w.Header().Get("Cache-Control"), "immutable") {
		t.Fatalf("failed SDK range gained immutable caching: %d %v", w.Code, w.Header())
	}
	for _, path := range []string{"/assets/Missing-B_1k6UL8.js", "/assets/../AccountBar-B_1k6UL8.js", "/.vite/manifest.json"} {
		w = managedSPARequest(s, "GET", path)
		if w.Code != 404 || strings.Contains(w.Header().Get("Cache-Control"), "immutable") {
			t.Fatalf("refused asset gained immutable caching: %s %d %v", path, w.Code, w.Header())
		}
	}
	w = managedSPARequest(s, "POST", asset)
	if w.Code != 405 || strings.Contains(w.Header().Get("Cache-Control"), "immutable") {
		t.Fatal("non-GET/HEAD request gained immutable caching")
	}
}
