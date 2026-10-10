package httpapi

import (
	"bytes"
	"context"
	"fmt"
	stdhtml "html"
	"sort"

	"github.com/DobosP/roedu-ui/web-kit/assets"
	"github.com/DobosP/roedu-ui/web-kit/csp"
)

// Frozen index.html remains an archive member, never a served template. This
// document retains its Romanian metadata while the selected manifest and SDK
// own every asset tag. No frozen file is rewritten to add nonces or preloads.
const managedLegacyHead = `<!doctype html>
<html lang="ro" data-ui="legacy"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0d0b20">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="description" content="Cât de român ești? Șase jocuri de cuvinte cu oameni, locuri și idei din cultura și viața românească.">
<title>Cât de român ești?</title>
`

type managedLegacyShell struct {
	manifest *assets.Manifest
	fonts    []string
}

func newManagedLegacyShell(manifest *assets.Manifest) (*managedLegacyShell, error) {
	if manifest == nil || !manifest.Entries()["index.html"].IsEntry || manifest.Static("index.html") == "" {
		return nil, fmt.Errorf("legacy shell requires manifest index entry")
	}
	owned, err := managedFontPreloads(manifest)
	if err != nil {
		return nil, err
	}
	fonts := make([]string, 0, len(owned))
	for url := range owned {
		fonts = append(fonts, url)
	}
	sort.Strings(fonts)
	return &managedLegacyShell{manifest: manifest, fonts: fonts}, nil
}

func (s *managedLegacyShell) render(ctx context.Context) ([]byte, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	nonce := csp.Nonce(ctx)
	if nonce == "" {
		return nil, fmt.Errorf("legacy shell requires request nonce")
	}
	ctx = assets.WithManifest(ctx, s.manifest)
	var tags bytes.Buffer
	if err := assets.Tags(ctx, "index.html").Render(ctx, &tags); err != nil {
		return nil, err
	}
	var output bytes.Buffer
	output.WriteString(managedLegacyHead)
	output.Write(tags.Bytes())
	for _, url := range s.fonts {
		fmt.Fprintf(&output, `<link rel="preload" href="%s" as="font" type="font/woff2" crossorigin="anonymous" nonce="%s">`, stdhtml.EscapeString(url), stdhtml.EscapeString(nonce))
	}
	output.WriteString("</head><body><div id=\"root\"></div></body></html>\n")
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	return output.Bytes(), nil
}
