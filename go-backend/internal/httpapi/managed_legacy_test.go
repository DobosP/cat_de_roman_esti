package httpapi

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"io/fs"
	"net/http"
	"net/http/httptest"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/DobosP/roedu-ui/web-kit/assets"
	"github.com/DobosP/roedu-ui/web-kit/csp"
	"golang.org/x/net/html"
)

func legacyManifestForTest(t *testing.T, files fstest.MapFS) *assets.Manifest {
	t.Helper()
	manifest, err := assets.Parse(files, "legacy/.vite/manifest.json", "legacy", "/")
	if err != nil {
		t.Fatal(err)
	}
	return manifest
}

// Independent response expectations use the admitted manifest and literal font
// source identities, never production shell rendering or its font helper.
func assertManagedLegacyIndex(t *testing.T, w *httptest.ResponseRecorder, manifest *assets.Manifest) string {
	t.Helper()
	if w.Code != http.StatusOK {
		t.Fatalf("legacy document status: %d", w.Code)
	}
	policy := w.Header().Get("Content-Security-Policy")
	if policy == "" {
		policy = w.Header().Get("Content-Security-Policy-Report-Only")
	}
	start := strings.Index(policy, "'nonce-")
	if start < 0 {
		t.Fatal("legacy response lacks SDK nonce policy")
	}
	tail := policy[start+len("'nonce-"):]
	end := strings.IndexByte(tail, '\'')
	if end < 0 {
		t.Fatal("legacy policy nonce is unterminated")
	}
	nonce := tail[:end]
	if len(nonce) != 32 || !strings.Contains(policy, "script-src 'self' 'nonce-"+nonce+"' 'strict-dynamic'") ||
		!strings.Contains(policy, "style-src 'self' 'nonce-"+nonce+"'") ||
		!strings.Contains(policy, "script-src-attr 'none';") || !strings.Contains(policy, "style-src-attr 'none';") {
		t.Fatal("legacy SDK policy differs")
	}
	if w.Header().Get("Cache-Control") != "no-store" || w.Header().Get("Content-Length") != strconv.Itoa(w.Body.Len()) {
		t.Fatal("legacy nonce document cache or length differs")
	}
	for key, value := range map[string]string{
		"Content-Type":               "text/html; charset=utf-8",
		"X-Content-Type-Options":     "nosniff",
		"Referrer-Policy":            "same-origin",
		"Cross-Origin-Opener-Policy": "same-origin",
		"X-Frame-Options":            "DENY",
	} {
		if w.Header().Get(key) != value {
			t.Fatalf("legacy security header differs: %s", key)
		}
	}
	entries := manifest.Entries()
	entry, ok := entries["index.html"]
	if !ok || !entry.IsEntry {
		t.Fatal("legacy fixture lacks real manifest entry")
	}
	want := map[string]int{"script:/" + entry.File: 1}
	visited, css := map[string]bool{}, map[string]bool{}
	var visit func(string)
	visit = func(key string) {
		if visited[key] {
			return
		}
		visited[key] = true
		item, exists := entries[key]
		if !exists {
			t.Fatalf("legacy static import missing: %s", key)
		}
		for _, dependency := range item.Imports {
			visit(dependency)
		}
		for _, file := range item.CSS {
			if !css[file] {
				css[file] = true
				want["stylesheet:/"+file]++
			}
		}
		if key != "index.html" {
			want["modulepreload:/"+item.File]++
		}
	}
	visit("index.html")
	fontSources := map[string]bool{
		"node_modules/@fontsource-variable/fredoka/files/fredoka-latin-ext-wght-normal.woff2": false,
		"node_modules/@fontsource-variable/fredoka/files/fredoka-latin-wght-normal.woff2":     false,
		"node_modules/@fontsource-variable/inter/files/inter-latin-ext-wght-normal.woff2":   false,
		"node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2":       false,
	}
	fontURLs := []string{}
	for _, item := range entries {
		if seen, owned := fontSources[item.Src]; owned {
			if seen {
				t.Fatal("legacy expected font source duplicated")
			}
			fontSources[item.Src] = true
			fontURLs = append(fontURLs, "/"+item.File)
			want["preload:/"+item.File]++
		}
	}
	for _, seen := range fontSources {
		if !seen {
			t.Fatal("legacy expected font source omitted")
		}
	}
	sort.Strings(fontURLs)
	// Literal metadata is from the sealed original index, not the renderer.
	wantMetadata := map[string]string{
		"charset":                               "UTF-8",
		"viewport":                              "width=device-width, initial-scale=1, viewport-fit=cover",
		"color-scheme":                          "dark",
		"theme-color":                           "#0d0b20",
		"mobile-web-app-capable":                "yes",
		"apple-mobile-web-app-capable":          "yes",
		"apple-mobile-web-app-status-bar-style": "black-translucent",
		"description":                           "Cât de român ești? Șase jocuri de cuvinte cu oameni, locuri și idei din cultura și viața românească.",
	}
	metadata := map[string]int{}
	got, observedFonts := map[string]int{}, []string{}
	documents, roots, bootstrap, titles := 0, 0, 0, 0
	inScript, inTitle := false, false
	var title strings.Builder
	tokens := html.NewTokenizer(bytes.NewReader(w.Body.Bytes()))
	for {
		kind := tokens.Next()
		if kind == html.ErrorToken {
			if tokens.Err() != io.EOF {
				t.Fatal(tokens.Err())
			}
			break
		}
		token := tokens.Token()
		if kind == html.TextToken {
			if inScript && strings.TrimSpace(token.Data) != "" {
				t.Fatal("legacy generated shell contains inline script")
			}
			if inTitle {
				title.WriteString(token.Data)
			}
			continue
		}
		if kind == html.EndTagToken {
			if token.Data == "script" {
				inScript = false
			}
			if token.Data == "title" {
				inTitle = false
			}
			continue
		}
		if kind != html.StartTagToken && kind != html.SelfClosingTagToken {
			continue
		}
		attrs := map[string]string{}
		for _, attr := range token.Attr {
			if _, duplicate := attrs[attr.Key]; duplicate || attr.Key == "style" || strings.HasPrefix(attr.Key, "on") {
				t.Fatal("legacy generated shell has duplicate or executable inline attributes")
			}
			attrs[attr.Key] = attr.Val
		}
		switch token.Data {
		case "html":
			documents++
			if attrs["lang"] != "ro" || attrs["data-ui"] != "legacy" {
				t.Fatal("legacy document language or UI identity differs")
			}
		case "div":
			if attrs["id"] == "root" {
				roots++
			}
		case "title":
			titles++
			inTitle = true
		case "meta":
			if attrs["property"] == "csp-nonce" {
				bootstrap++
				if len(attrs) != 3 || attrs["content"] != nonce || attrs["nonce"] != nonce {
					t.Fatal("legacy bootstrap nonce differs")
				}
				continue
			}
			key, value := attrs["name"], attrs["content"]
			if charset, present := attrs["charset"]; present {
				if len(attrs) != 1 {
					t.Fatal("legacy charset metadata has unexpected attributes")
				}
				key, value = "charset", charset
			} else if len(attrs) != 2 || key == "charset" {
				t.Fatal("legacy metadata has unexpected attributes")
			}
			expected, known := wantMetadata[key]
			if !known || value != expected {
				t.Fatalf("legacy original metadata differs: %s", key)
			}
			metadata[key]++
		case "script":
			if attrs["nonce"] != nonce || attrs["type"] != "module" || attrs["src"] == "" {
				t.Fatal("legacy module nonce/type/source differs")
			}
			got["script:"+attrs["src"]]++
			inScript = true
		case "link":
			if attrs["nonce"] != nonce {
				t.Fatal("legacy asset link nonce differs")
			}
			if attrs["rel"] == "preload" {
				if attrs["as"] != "font" || attrs["type"] != "font/woff2" || attrs["crossorigin"] != "anonymous" {
					t.Fatal("legacy font preload attributes differ")
				}
				observedFonts = append(observedFonts, attrs["href"])
			}
			got[attrs["rel"]+":"+attrs["href"]]++
		case "style":
			t.Fatal("legacy generated shell contains inline style")
		}
	}
	for key := range wantMetadata {
		if metadata[key] != 1 {
			t.Fatalf("legacy original metadata missing or duplicated: %s", key)
		}
	}
	if documents != 1 || roots != 1 || bootstrap != 1 || titles != 1 || title.String() != "Cât de român ești?" ||
		!reflect.DeepEqual(got, want) || !reflect.DeepEqual(observedFonts, fontURLs) {
		t.Fatalf("legacy document/static closure/fonts/metadata differs: got=%v want=%v fonts=%v wantFonts=%v", got, want, observedFonts, fontURLs)
	}
	return nonce
}

func TestManagedLegacyShellUsesManifestAndPreservesFrozenFixture(t *testing.T) {
	files := managedSPAFixture()
	files["legacy/index.html"].Data = []byte(`<!doctype html><html><head><script src="/assets/raw-legacy-forged.js"></script></head><body>RAW-LEGACY-SENTINEL</body></html>`)
	var entries map[string]assets.Entry
	if err := json.Unmarshal(files["legacy/.vite/manifest.json"].Data, &entries); err != nil {
		t.Fatal(err)
	}
	entry := entries["index.html"]
	entry.Imports, entry.DynamicImports = []string{"shared"}, []string{"lazy"}
	entries["index.html"] = entry
	entries["shared"] = assets.Entry{File: "assets/legacy-shared-87654321.js", CSS: entry.CSS}
	entries["lazy"] = assets.Entry{File: "assets/legacy-lazy-1234abcd.js"}
	files["legacy/assets/legacy-shared-87654321.js"] = &fstest.MapFile{Data: []byte("export const shared = true;")}
	files["legacy/assets/legacy-lazy-1234abcd.js"] = &fstest.MapFile{Data: []byte("export const lazy = true;")}
	encoded, err := json.Marshal(entries)
	if err != nil {
		t.Fatal(err)
	}
	files["legacy/.vite/manifest.json"].Data = encoded
	type snapshot struct {
		data []byte
		mode fs.FileMode
	}
	before := map[string]snapshot{}
	for name, file := range files {
		before[name] = snapshot{append([]byte{}, file.Data...), file.Mode}
	}
	s := testServer(t)
	s.managedUI, s.managedUIError = newManagedSPA(files, "legacy")
	if s.managedUIError != nil {
		t.Fatal(s.managedUIError)
	}
	w := managedSPARequest(s, "GET", "/intrusul?challenge=daily")
	assertManagedLegacyIndex(t, w, legacyManifestForTest(t, files))
	for _, forbidden := range []string{"RAW-LEGACY-SENTINEL", "raw-legacy-forged.js", "legacy-lazy-1234abcd.js"} {
		if strings.Contains(w.Body.String(), forbidden) {
			t.Fatalf("raw index or dynamic child escaped into generated legacy shell: %s", forbidden)
		}
	}
	if len(files) != len(before) {
		t.Fatal("legacy fixture membership changed")
	}
	for name, original := range before {
		if !bytes.Equal(files[name].Data, original.data) || files[name].Mode != original.mode {
			t.Fatalf("frozen input bytes/mode changed: %s", name)
		}
	}
}

func TestManagedLegacyResponseFreshnessStagesAndHead(t *testing.T) {
	for _, enforce := range []string{"", "false", "true"} {
		t.Run("flag="+enforce, func(t *testing.T) {
			t.Setenv("CAT_CSP_ENFORCE", enforce)
			files := managedSPAFixture()
			manifest := legacyManifestForTest(t, files)
			s := testServer(t)
			s.managedUI, s.managedUIError = newManagedSPA(files, "legacy")
			if s.managedUIError != nil {
				t.Fatal(s.managedUIError)
			}
			seen, length := map[string]bool{}, 0
			for _, route := range []string{"/", "/intrusul?challenge=daily", "/alchimie?mode=explore", "/"} {
				r := httptest.NewRequest("GET", route, nil)
				r.Header.Set("X-CSP-Nonce", "attacker-controlled")
				r.Header.Set("If-None-Match", `"stale-document"`)
				w := httptest.NewRecorder()
				s.ServeHTTP(w, r)
				nonce := assertManagedLegacyIndex(t, w, manifest)
				if seen[nonce] || nonce == "attacker-controlled" {
					t.Fatal("legacy request nonce reused or caller-controlled")
				}
				seen[nonce], length = true, w.Body.Len()
				const tt = "require-trusted-types-for 'script'; trusted-types roedu roedu-hovercard roedu-islands; report-uri /csp-report"
				if enforce == "true" {
					if w.Header().Get("Content-Security-Policy") == "" || w.Header().Get("Content-Security-Policy-Report-Only") != tt {
						t.Fatal("legacy enforced/TT-only stage differs")
					}
				} else if w.Header().Get("Content-Security-Policy") != "" || !strings.Contains(w.Header().Get("Content-Security-Policy-Report-Only"), "require-trusted-types-for 'script'") {
					t.Fatal("legacy default/report-only stage differs")
				}
			}
			w := managedSPARequest(s, "HEAD", "/intrusul")
			if w.Code != 200 || w.Body.Len() != 0 || w.Header().Get("Cache-Control") != "no-store" || w.Header().Get("Content-Length") != strconv.Itoa(length) {
				t.Fatal("legacy HEAD body/cache/length differs")
			}
			policy := w.Header().Get("Content-Security-Policy")
			if policy == "" {
				policy = w.Header().Get("Content-Security-Policy-Report-Only")
			}
			for nonce := range seen {
				if strings.Contains(policy, "'nonce-"+nonce+"'") {
					t.Fatal("legacy HEAD reused GET nonce")
				}
			}
			if !strings.Contains(policy, "'nonce-") {
				t.Fatal("legacy HEAD lacks actual SDK policy nonce")
			}
		})
	}
}

func TestManagedLegacyMalformedInputRefusesRawHTML(t *testing.T) {
	changes := []struct {
		name string
		edit func(*testing.T, fstest.MapFS)
	}{
		{"invalid manifest JSON", func(_ *testing.T, files fstest.MapFS) {
			files["legacy/.vite/manifest.json"].Data = []byte("{")
		}},
		{"missing manifest", func(_ *testing.T, files fstest.MapFS) {
			delete(files, "legacy/.vite/manifest.json")
		}},
		{"missing entry asset", func(_ *testing.T, files fstest.MapFS) {
			delete(files, "legacy/assets/app-1234abcd.js")
		}},
		{"missing font file", func(_ *testing.T, files fstest.MapFS) {
			delete(files, "legacy/"+managedFixtureFonts[0].file)
		}},
		{"empty original index", func(_ *testing.T, files fstest.MapFS) {
			files["legacy/index.html"].Data = nil
		}},
		{"wrong font source", func(t *testing.T, files fstest.MapFS) {
			var entries map[string]assets.Entry
			if err := json.Unmarshal(files["legacy/.vite/manifest.json"].Data, &entries); err != nil {
				t.Fatal(err)
			}
			for key, item := range entries {
				if item.Src == managedFixtureFonts[0].source {
					item.Src = "node_modules/unowned/font.woff2"
					entries[key] = item
				}
			}
			encoded, err := json.Marshal(entries)
			if err != nil {
				t.Fatal(err)
			}
			files["legacy/.vite/manifest.json"].Data = encoded
		}},
		{"fonts omitted from startup", func(t *testing.T, files fstest.MapFS) {
			var entries map[string]assets.Entry
			if err := json.Unmarshal(files["legacy/.vite/manifest.json"].Data, &entries); err != nil {
				t.Fatal(err)
			}
			entry := entries["index.html"]
			entry.Assets = nil
			entries["index.html"] = entry
			encoded, err := json.Marshal(entries)
			if err != nil {
				t.Fatal(err)
			}
			files["legacy/.vite/manifest.json"].Data = encoded
		}},
	}
	for _, change := range changes {
		t.Run(change.name, func(t *testing.T) {
			files := managedSPAFixture()
			change.edit(t, files)
			s := testServer(t)
			s.managedUI, s.managedUIError = newManagedSPA(files, "legacy")
			if s.managedUI != nil || s.managedUIError == nil {
				t.Fatal("malformed legacy bundle admitted")
			}
			w := managedSPARequest(s, "GET", "/intrusul")
			if w.Code != 503 || strings.Contains(w.Header().Get("Content-Type"), "text/html") || strings.Contains(w.Body.String(), "<html") {
				t.Fatal("failed legacy admission served raw HTML")
			}
		})
	}
	if shell, err := newManagedLegacyShell(nil); err == nil || shell != nil {
		t.Fatal("nil legacy manifest admitted")
	}
}

func TestManagedLegacyRenderRequiresNonceAndRefusesCanceledRequest(t *testing.T) {
	files := managedSPAFixture()
	shell, err := newManagedLegacyShell(legacyManifestForTest(t, files))
	if err != nil {
		t.Fatal(err)
	}
	if body, err := shell.render(context.Background()); err == nil || body != nil {
		t.Fatal("missing legacy nonce leaked partial HTML")
	}
	ctx, cancel := context.WithCancel(csp.WithNonce(context.Background(), strings.Repeat("n", 32)))
	cancel()
	if body, err := shell.render(ctx); !errors.Is(err, context.Canceled) || body != nil {
		t.Fatal("canceled legacy render leaked partial HTML")
	}
	s := testServer(t)
	s.managedUI, s.managedUIError = newManagedSPA(files, "legacy")
	if s.managedUIError != nil {
		t.Fatal(s.managedUIError)
	}
	r := httptest.NewRequest("GET", "/intrusul", nil).WithContext(ctx)
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != 500 || w.Body.Len() != 0 || w.Header().Get("Cache-Control") != "no-store" {
		t.Fatal("canceled legacy request escaped atomic no-store refusal")
	}
	missing := &managedSPA{index: []byte("RAW-LEGACY-FALLBACK-MUST-NOT-BE-SERVED")}
	if err := missing.installIndexHandler(); err == nil {
		t.Fatal("missing document shell was admitted")
	}
	w = httptest.NewRecorder()
	missing.serveIndex(w, httptest.NewRequest("GET", "/", nil))
	if w.Code != 500 || w.Body.Len() != 0 || w.Header().Get("Cache-Control") != "no-store" {
		t.Fatal("missing document shell served raw fallback or lost atomic refusal")
	}
}

func TestManagedLegacySelectionCannotBeChangedByRequestOrLaterEnvironment(t *testing.T) {
	t.Setenv("CAT_UI", "legacy")
	files := managedSPAFixture()
	// Distinct entry URLs make a wrong manifest observable even if a caller
	// accidentally kept the legacy document marker while changing roots.
	const legacyEntry = "assets/legacy-selected-1234abcd.js"
	files["legacy/"+legacyEntry] = files["legacy/assets/app-1234abcd.js"]
	delete(files, "legacy/assets/app-1234abcd.js")
	files["legacy/.vite/manifest.json"].Data = bytes.Replace(files["legacy/.vite/manifest.json"].Data,
		[]byte("assets/app-1234abcd.js"), []byte(legacyEntry), 1)
	s := testServer(t)
	s.managedUI, s.managedUIError = newManagedSPA(files, "legacy")
	if s.managedUIError != nil {
		t.Fatal(s.managedUIError)
	}
	manifest := legacyManifestForTest(t, files)
	// Selection is made at startup; request values and a later environment edit
	// cannot replace the already admitted manifest or generated document shell.
	t.Setenv("CAT_UI", "current")
	for _, route := range []string{"/?CAT_UI=current", "/intrusul?ui=current&CAT_UI=current"} {
		r := httptest.NewRequest("GET", route, nil)
		r.Header.Set("Cookie", "CAT_UI=current; ui=current")
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		assertManagedLegacyIndex(t, w, manifest)
	}
}
