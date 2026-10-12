package httpapi

import (
	"bytes"
	"io"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"sync"
	"testing"
	"testing/fstest"

	"golang.org/x/net/html"
)

// Every route the React app declares (frontend/src/App.tsx), its wildcard
// fallback and a trailing-slash variant that is deliberately not a ported path.
var managedAppRoutes = []string{"/", "/alchimie", "/intrusul", "/perechi", "/cald-rece", "/lant", "/conexiuni", "/clasament", "/not-a-route", "/intrusul/"}

// managedDocumentUI reports the served document's <html data-ui> attribute.
func managedDocumentUI(t *testing.T, body []byte) (string, bool) {
	t.Helper()
	tokens := html.NewTokenizer(bytes.NewReader(body))
	for {
		kind := tokens.Next()
		if kind == html.ErrorToken {
			if tokens.Err() != io.EOF {
				t.Fatal(tokens.Err())
			}
			t.Fatal("served document has no html element")
		}
		if kind != html.StartTagToken {
			continue
		}
		token := tokens.Token()
		if token.Data != "html" {
			continue
		}
		for _, attr := range token.Attr {
			if attr.Key == "data-ui" {
				return attr.Val, true
			}
		}
		return "", false
	}
}

func declareManagedUI(files fstest.MapFS, ui string) {
	files["dist/index.html"].Data = bytes.Replace(files["dist/index.html"].Data, []byte(`<html lang="ro">`), []byte(`<html lang="ro" data-ui="`+ui+`">`), 1)
}

// preactDeliveryFixture declares the current build as the Preact shell and
// gives the frozen bundle its own hashed entry, as real builds do. Stylesheet
// and font files keep one name with identical bytes in both trees.
func preactDeliveryFixture() fstest.MapFS {
	files := managedSPAFixture()
	declareManagedUI(files, "preact")
	const current, frozen = "assets/app-1234abcd.js", "assets/legacy-87654321.js"
	files["legacy/"+frozen] = files["legacy/"+current]
	delete(files, "legacy/"+current)
	files["legacy/.vite/manifest.json"].Data = bytes.ReplaceAll(files["legacy/.vite/manifest.json"].Data, []byte(current), []byte(frozen))
	return files
}

func managedDeliveryServer(t *testing.T, files fstest.MapFS, mode string) *Server {
	t.Helper()
	s := testServer(t)
	s.managedUI, s.managedUIError = newManagedSPA(files, mode)
	if s.managedUIError != nil {
		t.Fatal(s.managedUIError)
	}
	return s
}

func TestManagedDeliveryPortedSetAndDocumentIdentityPerRoute(t *testing.T) {
	if want := map[string]bool{"/": true, "/intrusul": true, "/conexiuni": true}; !reflect.DeepEqual(managedPortedRoutes, want) {
		t.Fatalf("M2 ported route set differs: %v", managedPortedRoutes)
	}
	undeclared := managedSPAFixture()
	declaredReact := managedSPAFixture()
	declareManagedUI(declaredReact, "react")
	for _, tc := range []struct {
		name, mode string
		files      fstest.MapFS
		split      bool
		ui         func(route string) (string, bool)
	}{
		{"current-undeclared", "current", undeclared, false, func(string) (string, bool) { return "", false }},
		{"current-react", "current", declaredReact, false, func(string) (string, bool) { return "react", true }},
		{"current-preact", "current", preactDeliveryFixture(), true, func(route string) (string, bool) {
			if managedPortedRoutes[route] {
				return "preact", true
			}
			return "legacy", true
		}},
		{"legacy-overrides-preact", "legacy", preactDeliveryFixture(), false, func(string) (string, bool) { return "legacy", true }},
	} {
		t.Run(tc.name, func(t *testing.T) {
			t.Setenv("CAT_UI", tc.mode)
			s := managedDeliveryServer(t, tc.files, tc.mode)
			if (s.managedUI.frozen != nil) != tc.split || (s.managedUI.owners != nil) != tc.split {
				t.Fatal("per-route split active without a Preact declaration, or missing with one")
			}
			for _, route := range managedAppRoutes {
				w := managedSPARequest(s, http.MethodGet, route)
				if w.Code != http.StatusOK {
					t.Fatalf("%s: document status %d", route, w.Code)
				}
				wantUI, wantDeclared := tc.ui(route)
				if ui, declared := managedDocumentUI(t, w.Body.Bytes()); ui != wantUI || declared != wantDeclared {
					t.Fatalf("%s: data-ui=%q (declared %v), want %q (declared %v)", route, ui, declared, wantUI, wantDeclared)
				}
				if wantUI == "legacy" {
					assertManagedLegacyIndex(t, w, legacyManifestForTest(t, tc.files))
				} else {
					assertManagedCurrentIndex(t, w, tc.files["dist/index.html"].Data)
				}
				head := managedSPARequest(s, http.MethodHead, route)
				if head.Code != http.StatusOK || head.Body.Len() != 0 || head.Header().Get("Cache-Control") != "no-store" {
					t.Fatalf("%s: HEAD document differs", route)
				}
			}
		})
	}
}

func TestManagedDeliverySplitIgnoresRequestSelectors(t *testing.T) {
	files := preactDeliveryFixture()
	s := managedDeliveryServer(t, files, "current")
	for _, tc := range []struct{ target, ui string }{
		{"/perechi?ui=preact&CAT_UI=current", "legacy"},
		{"/intrusul?ui=legacy&CAT_UI=legacy", "preact"},
		{"/conexiuni?difficulty=easy", "preact"},
		{"/intrusul/?challenge=daily", "legacy"},
	} {
		r := httptest.NewRequest(http.MethodGet, tc.target, nil)
		r.Header.Set("Cookie", "CAT_UI=legacy; ui=legacy")
		r.Header.Set("X-Cat-UI", "legacy")
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		if ui, _ := managedDocumentUI(t, w.Body.Bytes()); w.Code != http.StatusOK || ui != tc.ui {
			t.Fatalf("%s: request values changed document selection: %d %q", tc.target, w.Code, ui)
		}
	}
}

func TestManagedDeliverySplitAssetsKeepSDKMethodCacheAndRefusalContracts(t *testing.T) {
	t.Setenv("CAT_CSP_ENFORCE", "true")
	files := preactDeliveryFixture()
	s := managedDeliveryServer(t, files, "current")
	current, frozen := s.managedUI, s.managedUI.frozen
	wantOwners := map[string]*managedSPA{"assets/app-1234abcd.js": current, "assets/legacy-87654321.js": frozen, "assets/app-1234abcd.css": current}
	for _, font := range managedFixtureFonts {
		wantOwners[font.file] = current // Identical shared bytes dedupe to the current SDK handler.
	}
	if !reflect.DeepEqual(s.managedUI.owners, wantOwners) {
		t.Fatalf("asset owner table differs: %v", s.managedUI.owners)
	}
	for _, row := range []struct{ path, root string }{
		{"/assets/app-1234abcd.js", "dist"}, {"/assets/legacy-87654321.js", "legacy"},
		{"/assets/app-1234abcd.css", "dist"}, {"/" + managedFixtureFonts[0].file, "dist"},
	} {
		w := managedSPARequest(s, http.MethodGet, row.path)
		if w.Code != http.StatusOK || !bytes.Equal(w.Body.Bytes(), files[row.root+row.path].Data) ||
			w.Header().Get("X-Content-Type-Options") != "nosniff" || w.Header().Get("Cache-Control") != "max-age=315360000, public, immutable" {
			t.Fatalf("split asset lost its owner bytes or Cat cache contract: %s %d %v", row.path, w.Code, w.Header())
		}
		if strings.HasSuffix(row.path, ".js") && !strings.Contains(w.Header().Get("Content-Type"), "javascript") {
			t.Fatalf("split asset type differs: %s", row.path)
		}
		head := managedSPARequest(s, http.MethodHead, row.path)
		if head.Code != http.StatusOK || head.Body.Len() != 0 || head.Header().Get("ETag") != w.Header().Get("ETag") {
			t.Fatalf("split asset HEAD differs: %s", row.path)
		}
	}
	for _, route := range []string{"/intrusul", "/perechi", "/assets/legacy-87654321.js", "/assets/app-1234abcd.js"} {
		w := managedSPARequest(s, http.MethodPost, route)
		if w.Code != http.StatusMethodNotAllowed || w.Header().Get("Allow") != "GET, HEAD" || w.Body.Len() != 0 {
			t.Fatalf("split method contract differs: %s %d", route, w.Code)
		}
	}
	for _, route := range []string{"/.vite/manifest.json", "/.keep", "/assets/../index.html", "/assets/missing.js", "/assets/legacy-87654321.js.gz", "/missing.json", "/assets//legacy-87654321.js"} {
		if w := managedSPARequest(s, http.MethodGet, route); w.Code != http.StatusNotFound || w.Body.Len() != 0 {
			t.Fatalf("split private/missing refusal differs: %s %d %s", route, w.Code, w.Body.String())
		}
	}
	if w := managedSPARequest(s, http.MethodGet, "/index.html"); w.Code != http.StatusFound || w.Header().Get("Location") != "/" {
		t.Fatal("split index redirect differs")
	}
	if w := managedSPARequest(s, http.MethodGet, "/api/no-such-endpoint"); w.Code != http.StatusNotFound || w.Header().Get("Content-Type") != "application/json" {
		t.Fatal("split delivery intercepted the native API")
	}
	if w := managedSPARequest(s, http.MethodGet, "/api/health"); w.Code != http.StatusOK || w.Header().Get("Content-Type") != "application/json" {
		t.Fatal("split delivery changed native API availability")
	}
	nonces := map[string]bool{}
	for _, route := range []string{"/intrusul", "/perechi", "/intrusul", "/perechi"} {
		w := managedSPARequest(s, http.MethodGet, route)
		var nonce string
		if route == "/perechi" {
			nonce = assertManagedLegacyIndex(t, w, legacyManifestForTest(t, files))
		} else {
			nonce = assertManagedCurrentIndex(t, w, files["dist/index.html"].Data)
		}
		if w.Header().Get("Content-Security-Policy") == "" || nonces[nonce] {
			t.Fatalf("%s: enforced stage or fresh nonce lost across the split", route)
		}
		nonces[nonce] = true
	}
}

func TestManagedDeliveryRefusesConflictingAssetBytesAndDedupesIdenticalOnes(t *testing.T) {
	// managedSPAFixture keeps one entry name with different bytes per tree.
	conflicting := managedSPAFixture()
	declareManagedUI(conflicting, "preact")
	ui, err := newManagedSPA(conflicting, "current")
	if err == nil || ui != nil || !strings.Contains(err.Error(), "conflicting managed asset bytes") {
		t.Fatalf("one public URL admitted different current/legacy bytes: %v", err)
	}
	s := testServer(t)
	s.managedUI, s.managedUIError = ui, err
	if w := managedSPARequest(s, http.MethodGet, "/intrusul"); w.Code != http.StatusServiceUnavailable || w.Body.String() != `{"detail":"Managed UI unavailable"}` {
		t.Fatal("refused split earned a document response")
	}
	if w := managedSPARequest(s, http.MethodGet, "/api/health"); w.Code != http.StatusOK {
		t.Fatal("refused split changed native API availability")
	}
	// The same trees stay admissible whenever no split is requested.
	for _, mode := range []string{"current", "legacy"} {
		if single, err := newManagedSPA(managedSPAFixture(), mode); err != nil || single.frozen != nil || single.owners != nil {
			t.Fatalf("single-bundle %s admission changed: %v", mode, err)
		}
	}
	// Identical shared bytes dedupe; a byte change in either copy refuses.
	for _, root := range []string{"dist", "legacy"} {
		files := preactDeliveryFixture()
		if _, err := newManagedSPA(files, "current"); err != nil {
			t.Fatal(err)
		}
		files[root+"/"+managedFixtureFonts[1].file].Data = append(files[root+"/"+managedFixtureFonts[1].file].Data, '!')
		if _, err := newManagedSPA(files, "current"); err == nil {
			t.Fatalf("shared asset with differing %s bytes admitted", root)
		}
	}
	// Documents and private files are never asset conflicts: both index.html
	// and both manifests differ in every real split.
	files := preactDeliveryFixture()
	if _, err := newManagedSPA(files, "current"); err != nil || bytes.Equal(files["dist/index.html"].Data, files["legacy/index.html"].Data) ||
		bytes.Equal(files["dist/.vite/manifest.json"].Data, files["legacy/.vite/manifest.json"].Data) {
		t.Fatalf("differing documents or manifests refused the split: %v", err)
	}
}

func TestManagedDeliveryPreactDeclarationNeedsFrozenLegacyAndKnownIdentity(t *testing.T) {
	files := preactDeliveryFixture()
	for name := range files {
		if strings.HasPrefix(name, "legacy/") {
			delete(files, name)
		}
	}
	s := testServer(t)
	s.managedUI, s.managedUIError = newManagedSPA(files, "current")
	if s.managedUI != nil || s.managedUIError == nil {
		t.Fatal("Preact declaration admitted without the frozen legacy bundle")
	}
	if w := managedSPARequest(s, http.MethodGet, "/perechi"); w.Code != http.StatusServiceUnavailable {
		t.Fatal("unported route earned a response without a frozen bundle")
	}
	for _, declared := range []string{"legacy", "vue", "Preact", "preact ", "react preact"} {
		files := preactDeliveryFixture()
		files["dist/index.html"].Data = bytes.Replace(files["dist/index.html"].Data, []byte(`data-ui="preact"`), []byte(`data-ui="`+declared+`"`), 1)
		if ui, err := newManagedSPA(files, "current"); err == nil || ui != nil {
			t.Fatalf("unknown current UI identity admitted: %q", declared)
		}
	}
	for _, mode := range []string{"preact", "react", "split"} {
		if ui, err := newManagedSPA(preactDeliveryFixture(), mode); err == nil || ui != nil {
			t.Fatalf("CAT_UI gained a selection mode: %q", mode)
		}
	}
}

func TestManagedDeliverySplitServesConcurrently(t *testing.T) {
	files := preactDeliveryFixture()
	s := managedDeliveryServer(t, files, "current")
	targets := []string{"/", "/intrusul", "/conexiuni", "/perechi", "/alchimie", "/not-a-route", "/assets/app-1234abcd.js", "/assets/legacy-87654321.js", "/" + managedFixtureFonts[2].file}
	var wg sync.WaitGroup
	failures := make(chan string, len(targets)*8)
	for worker := 0; worker < 8; worker++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for _, target := range targets {
				w := managedSPARequest(s, http.MethodGet, target)
				if w.Code != http.StatusOK {
					failures <- target
					continue
				}
				if strings.HasPrefix(target, "/assets/") {
					continue
				}
				want := "legacy"
				if managedPortedRoutes[target] {
					want = "preact"
				}
				if !bytes.Contains(w.Body.Bytes(), []byte(`data-ui="`+want+`"`)) {
					failures <- target
				}
			}
		}()
	}
	wg.Wait()
	close(failures)
	for target := range failures {
		t.Errorf("concurrent split request differed: %s", target)
	}
}
