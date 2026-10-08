package httpapi

import (
	"bytes"
	"context"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/DobosP/roedu-ui/web-kit/assets"
	"github.com/DobosP/roedu-ui/web-kit/csp"
)

// Synthetic public SDK contract, authored NOT RUN before owner kit installation.
// This does not install an app handler or qualify serving, auth, privacy or CSP.
func guiKitSyntheticAssets(manifest string) fstest.MapFS {
	return fstest.MapFS{
		"dist/.vite/manifest.json": {
			Data: []byte(manifest),
		},
		"dist/assets/cat-main-a1b2c3d4.js": {
			Data: []byte("export const fixture = true;\n"),
		},
		"dist/assets/cat-main-e5f6a7b8.css": {
			Data: []byte(".fixture { display: block; }\n"),
		},
		"dist/assets/shared-12345678.js": {
			Data: []byte("export const shared = true;\n"),
		},
		"dist/assets/intrusul-89abcdef.js": {
			Data: []byte("export const lazyFixture = true;\n"),
		},
	}
}

func TestGUIKitAssetsManifestNonceContract(t *testing.T) {
	const manifestJSON = `{
		"index.html": {
			"file": "assets/cat-main-a1b2c3d4.js", "isEntry": true,
			"imports": ["_shared.js"], "dynamicImports": ["src/screens/Intrusul.tsx"],
			"css": ["assets/cat-main-e5f6a7b8.css"]
		},
		"_shared.js": {
			"file": "assets/shared-12345678.js",
			"css": ["assets/cat-main-e5f6a7b8.css"]
		},
		"src/screens/Intrusul.tsx": {"file": "assets/intrusul-89abcdef.js"}
	}`
	const nonce = "synthetic-cat-nonce"
	manifest, err := assets.Parse(guiKitSyntheticAssets(manifestJSON), "dist/.vite/manifest.json", "dist", "/")
	if err != nil {
		t.Fatal(err)
	}

	t.Run("root asset URLs and nonced static tags", func(t *testing.T) {
		entryURL := manifest.Static("index.html")
		if entryURL != "/assets/cat-main-a1b2c3d4.js" || !immutableViteAsset.MatchString(entryURL) {
			t.Fatalf("SDK URL does not fit Cat's root asset contract: %q", entryURL)
		}
		ctx := assets.WithManifest(csp.WithNonce(context.Background(), nonce), manifest)
		var output bytes.Buffer
		if err := assets.Tags(ctx, "index.html").Render(ctx, &output); err != nil {
			t.Fatal(err)
		}
		body := output.String()
		if output.Len() == 0 || !strings.Contains(body, `type="module"`) || !strings.Contains(body, `src="`+entryURL+`"`) {
			t.Fatalf("missing real entry module output: %q", body)
		}
		if strings.Count(body, `rel="stylesheet"`) != 1 || strings.Count(body, `href="/assets/cat-main-e5f6a7b8.css"`) != 1 {
			t.Fatalf("shared stylesheet must be emitted exactly once: %q", body)
		}
		if strings.Count(body, `rel="modulepreload"`) != 1 || strings.Count(body, `href="/assets/shared-12345678.js"`) != 1 {
			t.Fatalf("real static dependency preload missing or duplicated: %q", body)
		}
		if strings.Count(body, `nonce="`+nonce+`"`) != 4 || !strings.Contains(body, `property="csp-nonce"`) {
			t.Fatalf("entry, CSS, preload and nonce meta must carry the same nonce: %q", body)
		}
		openTags := 0
		for _, fragment := range strings.Split(body, ">") {
			fragment = strings.TrimSpace(fragment)
			if strings.HasPrefix(fragment, "<meta ") || strings.HasPrefix(fragment, "<link ") || strings.HasPrefix(fragment, "<script ") {
				openTags++
				if !strings.Contains(fragment, `nonce="`+nonce+`"`) {
					t.Fatalf("an emitted tag lost its request nonce: %q", fragment)
				}
			}
		}
		if openTags != 4 {
			t.Fatalf("expected one module, CSS, preload and nonce-meta tag, got %d", openTags)
		}
		if strings.Contains(body, "intrusul-89abcdef.js") {
			t.Fatalf("dynamic route must not become an eager asset tag: %q", body)
		}
	})

	t.Run("render refusals write no partial tags", func(t *testing.T) {
		for _, fixture := range []struct {
			name, entry, nonce string
		}{
			{name: "missing nonce", entry: "index.html"},
			{name: "unknown entry", entry: "missing.html", nonce: nonce},
		} {
			t.Run(fixture.name, func(t *testing.T) {
				ctx := assets.WithManifest(context.Background(), manifest)
				if fixture.nonce != "" {
					ctx = csp.WithNonce(ctx, fixture.nonce)
				}
				var output bytes.Buffer
				if err := assets.Tags(ctx, fixture.entry).Render(ctx, &output); err == nil {
					t.Fatal("expected a real SDK refusal")
				}
				if output.Len() != 0 {
					t.Fatalf("refused render leaked partial tags: %q", output.String())
				}
			})
		}
	})

	t.Run("invalid manifest and prefix refusals", func(t *testing.T) {
		for _, fixture := range []struct {
			name, manifest, prefix string
		}{
			{name: "malformed JSON", manifest: `{`, prefix: "/"},
			{name: "empty manifest", manifest: `{}`, prefix: "/"},
			{name: "unsafe file", manifest: `{"index.html":{"file":"../outside.js"}}`, prefix: "/"},
			{name: "missing file", manifest: `{"index.html":{"file":"assets/missing-12345678.js"}}`, prefix: "/"},
			{name: "dangling static import", manifest: `{"index.html":{"file":"assets/cat-main-a1b2c3d4.js","imports":["missing"]}}`, prefix: "/"},
			{name: "dangling dynamic import", manifest: `{"index.html":{"file":"assets/cat-main-a1b2c3d4.js","dynamicImports":["missing"]}}`, prefix: "/"},
			{name: "cross-origin prefix", manifest: manifestJSON, prefix: "//example.invalid/"},
		} {
			t.Run(fixture.name, func(t *testing.T) {
				if parsed, err := assets.Parse(guiKitSyntheticAssets(fixture.manifest), "dist/.vite/manifest.json", "dist", fixture.prefix); err == nil || parsed != nil {
					t.Fatal("invalid fixture must not produce an accepted SDK manifest")
				}
			})
		}
	})
}
