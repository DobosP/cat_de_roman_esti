package httpapi

import (
	"bytes"
	"context"
	"encoding/json"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/DobosP/roedu-ui/web-kit/assets"
	"github.com/DobosP/roedu-ui/web-kit/csp"
)

// Independent literal fixture identities; never valid font/browser evidence.
var managedFixtureFonts = []struct{ source, file string }{
	{"node_modules/@fontsource-variable/fredoka/files/fredoka-latin-ext-wght-normal.woff2", "assets/fredoka-latin-ext-1234abcd.woff2"},
	{"node_modules/@fontsource-variable/fredoka/files/fredoka-latin-wght-normal.woff2", "assets/fredoka-latin-2345abcd.woff2"},
	{"node_modules/@fontsource-variable/inter/files/inter-latin-ext-wght-normal.woff2", "assets/inter-latin-ext-3456abcd.woff2"},
	{"node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2", "assets/inter-latin-4567abcd.woff2"},
}

const nonceFixtureFontLinks = "<link rel=\"preload\" href=\"/assets/fredoka-latin-ext-1234abcd.woff2\" as=\"font\" type=\"font/woff2\" crossorigin=\"anonymous\">\r\n" +
	"<link rel=\"preload\" href=\"/assets/fredoka-latin-2345abcd.woff2\" as=\"font\" type=\"font/woff2\" crossorigin=\"anonymous\">\r\n" +
	"<link rel=\"preload\" href=\"/assets/inter-latin-ext-3456abcd.woff2\" as=\"font\" type=\"font/woff2\" crossorigin=\"anonymous\">\r\n" +
	"<link rel=\"preload\" href=\"/assets/inter-latin-4567abcd.woff2\" as=\"font\" type=\"font/woff2\" crossorigin=\"anonymous\">\r\n"

func addManagedFixtureFonts(files fstest.MapFS, root string) {
	var entries map[string]assets.Entry
	if err := json.Unmarshal(files[root+"/.vite/manifest.json"].Data, &entries); err != nil {
		panic(err) // Fixed synthetic fixture construction, never production fallback.
	}
	entry := entries["index.html"]
	for _, font := range managedFixtureFonts {
		entries["font-fixture/"+font.file] = assets.Entry{File: font.file, Src: font.source}
		entry.Assets = append(entry.Assets, font.file)
		files[root+"/"+font.file] = &fstest.MapFile{Data: []byte("NON-RELEASE synthetic bytes: " + font.source)}
	}
	entries["index.html"] = entry
	raw, err := json.Marshal(entries)
	if err != nil {
		panic(err)
	}
	files[root+"/.vite/manifest.json"].Data = raw
	if index, ok := files[root+"/index.html"]; ok {
		index.Data = bytes.Replace(index.Data, []byte("</head>"), []byte(nonceFixtureFontLinks+"</head>"), 1)
	}
}

func TestManagedFontManifestBindings(t *testing.T) {
	manifest := nonceFixtureManifest(t)
	fonts, err := managedFontPreloads(manifest)
	if err != nil || len(fonts) != 4 {
		t.Fatalf("exact four owned source bindings refused: %v", err)
	}
	for _, font := range managedFixtureFonts {
		if seen, ok := fonts["/"+font.file]; !ok || seen || manifest.Static(font.source) != "" {
			t.Fatal("font Src was treated as a Static key or missing nonce obligation")
		}
	}
	changes := []struct {
		name string
		edit func(map[string]assets.Entry)
	}{
		{"missing source", func(e map[string]assets.Entry) { delete(e, "font-fixture/"+managedFixtureFonts[0].file) }},
		{"absent production font set", func(e map[string]assets.Entry) {
			for _, f := range managedFixtureFonts {
				delete(e, "font-fixture/"+f.file)
			}
		}},
		{"duplicate source alias", func(e map[string]assets.Entry) { e["duplicate"] = e["font-fixture/"+managedFixtureFonts[0].file] }},
		{"foreign source", func(e map[string]assets.Entry) {
			k := "font-fixture/" + managedFixtureFonts[0].file
			v := e[k]
			v.Src = "node_modules/foreign/font.woff2"
			e[k] = v
		}},
		{"missing Src", func(e map[string]assets.Entry) {
			k := "font-fixture/" + managedFixtureFonts[0].file
			v := e[k]
			v.Src = ""
			e[k] = v
		}},
		{"two sources one file", func(e map[string]assets.Entry) {
			k := "font-fixture/" + managedFixtureFonts[1].file
			v := e[k]
			v.File = managedFixtureFonts[0].file
			e[k] = v
		}},
		{"wrong font extension", func(e map[string]assets.Entry) {
			k := "font-fixture/" + managedFixtureFonts[0].file
			v := e[k]
			v.File = "assets/app-1234abcd.js"
			e[k] = v
		}},
		{"font entry marked module", func(e map[string]assets.Entry) {
			k := "font-fixture/" + managedFixtureFonts[0].file
			v := e[k]
			v.IsEntry = true
			e[k] = v
		}},
		{"font entry imports code", func(e map[string]assets.Entry) {
			k := "font-fixture/" + managedFixtureFonts[0].file
			v := e[k]
			v.Imports = []string{"_shared"}
			e[k] = v
		}},
		{"filename shadows Static key", func(e map[string]assets.Entry) {
			e[managedFixtureFonts[0].file] = assets.Entry{File: "assets/app-1234abcd.js"}
		}},
		{"orphan startup font", func(e map[string]assets.Entry) { v := e["index.html"]; v.Assets = v.Assets[1:]; e["index.html"] = v }},
		{"dynamic only font", func(e map[string]assets.Entry) {
			v := e["index.html"]
			v.Assets = v.Assets[1:]
			e["index.html"] = v
			v = e["lazy"]
			v.Assets = []string{managedFixtureFonts[0].file}
			e["lazy"] = v
		}},
		{"unbound font asset", func(e map[string]assets.Entry) {
			v := e["index.html"]
			v.Assets = append(v.Assets, "assets/unbound-1234abcd.woff2")
			e["index.html"] = v
		}},
	}
	for _, change := range changes {
		t.Run(change.name, func(t *testing.T) {
			entries := manifest.Entries()
			change.edit(entries)
			raw, err := json.Marshal(entries)
			if err != nil {
				t.Fatal(err)
			}
			files := fstest.MapFS{"dist/.vite/manifest.json": {Data: raw}, "dist/assets/unbound-1234abcd.woff2": {Data: []byte("synthetic unbound")}}
			for _, item := range entries {
				files["dist/"+item.File] = &fstest.MapFile{Data: []byte("synthetic")}
				for _, f := range append(append([]string{}, item.Assets...), item.CSS...) {
					files["dist/"+f] = &fstest.MapFile{Data: []byte("synthetic")}
				}
			}
			candidate, err := assets.Parse(files, "dist/.vite/manifest.json", "dist", "/")
			if err != nil {
				t.Fatal("fixture must reach Cat source binding, not SDK parse refusal", err)
			}
			if got, err := managedFontPreloads(candidate); err == nil || got != nil {
				t.Fatal("invalid managed font binding admitted")
			}
		})
	}
}

func TestManagedFontLinkRefusals(t *testing.T) {
	first := strings.Split(nonceFixtureFontLinks, "\r\n")[0]
	changes := []struct{ name, old, next string }{
		{"missing font", first, ""}, {"duplicate font", first, first + first},
		{"foreign URL", "/assets/fredoka-latin-ext-1234abcd.woff2", "https://foreign.invalid/font.woff2"},
		{"URL credentials", "/assets/fredoka-latin-ext-1234abcd.woff2", "https://user:password@example.com/font.woff2"},
		{"protocol relative", "/assets/fredoka-latin-ext-1234abcd.woff2", "//foreign.invalid/font.woff2"},
		{"query", "/assets/fredoka-latin-ext-1234abcd.woff2", "/assets/fredoka-latin-ext-1234abcd.woff2?x=1"},
		{"fragment", "/assets/fredoka-latin-ext-1234abcd.woff2", "/assets/fredoka-latin-ext-1234abcd.woff2#x"},
		{"wrong file", "/assets/fredoka-latin-ext-1234abcd.woff2", "/assets/inter-latin-4567abcd.woff2"},
		{"missing crossorigin", ` crossorigin="anonymous"`, ""},
		{"credentialed crossorigin", `crossorigin="anonymous"`, `crossorigin="use-credentials"`},
		{"wrong as", `as="font"`, `as="script"`}, {"missing as", ` as="font"`, ""},
		{"wrong media", `type="font/woff2"`, `type="application/octet-stream"`},
		{"mixed rel", `rel="preload"`, `rel="preload stylesheet"`},
		{"source nonce", `as="font"`, `as="font" nonce="forged"`},
		{"extra attribute", `as="font"`, `as="font" media="all"`},
		{"duplicate as", `as="font"`, `as="font" AS="font"`},
	}
	for _, change := range changes {
		t.Run(change.name, func(t *testing.T) {
			input := strings.Replace(nonceFixtureIndex, change.old, change.next, 1)
			if input == nonceFixtureIndex {
				t.Fatal("counterexample did not mutate valid shell")
			}
			if shell, err := newManagedNonceShell([]byte(input), nonceFixtureManifest(t)); err == nil || shell != nil {
				t.Fatal("invalid font preload admitted")
			}
		})
	}
	outside := strings.Replace(strings.Replace(nonceFixtureIndex, first, "", 1), "<body>", "<body>"+first, 1)
	if shell, err := newManagedNonceShell([]byte(outside), nonceFixtureManifest(t)); err == nil || shell != nil {
		t.Fatal("font preload outside head admitted")
	}
}

func TestManagedFontEveryLinkReceivesNonceWithoutRewriting(t *testing.T) {
	shell, err := newManagedNonceShell([]byte(nonceFixtureIndex), nonceFixtureManifest(t))
	if err != nil {
		t.Fatal(err)
	}
	const nonce = "synthetic-font-nonce"
	body, err := shell.render(csp.WithNonce(context.Background(), nonce))
	if err != nil {
		t.Fatal(err)
	}
	for _, font := range managedFixtureFonts {
		link := `<link rel="preload" href="/` + font.file + `" as="font" type="font/woff2" crossorigin="anonymous" nonce="` + nonce + `">`
		if bytes.Count(body, []byte(link)) != 1 {
			t.Fatal("font lost anonymous request/nonce/unique binding")
		}
	}
	body = bytes.Replace(body, []byte(`<meta property="csp-nonce" content="`+nonce+`" nonce="`+nonce+`">`), nil, 1)
	body = bytes.ReplaceAll(body, []byte(` nonce="`+nonce+`"`), nil)
	if !bytes.Equal(body, []byte(nonceFixtureIndex)) {
		t.Fatal("font nonce bridge rewrote raw HTML")
	}
}
