package httpapi

import (
	"fmt"
	"strings"

	"github.com/DobosP/roedu-ui/web-kit/assets"
)

// The source identities match frontend/scripts/check-bundle-budget.mjs, not
// generated hash names. The existing managed FS walk and SDK Parse own file
// regularity/existence; this adds the exact source/file/URL and startup binding.
func managedFontPreloads(manifest *assets.Manifest) (map[string]bool, error) {
	if manifest == nil {
		return nil, fmt.Errorf("managed fonts require manifest")
	}
	wanted := map[string]bool{
		"node_modules/@fontsource-variable/fredoka/files/fredoka-latin-ext-wght-normal.woff2": false,
		"node_modules/@fontsource-variable/fredoka/files/fredoka-latin-wght-normal.woff2":     false,
		"node_modules/@fontsource-variable/inter/files/inter-latin-ext-wght-normal.woff2":     false,
		"node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2":         false,
	}
	entries := manifest.Entries()
	fonts, byFile := map[string]bool{}, map[string]bool{}
	for key, item := range entries {
		if !strings.HasSuffix(item.Src, ".woff2") && !strings.HasSuffix(item.File, ".woff2") {
			continue
		}
		seen, owned := wanted[item.Src]
		if !owned || seen || item.IsEntry || len(item.CSS)+len(item.Imports)+len(item.DynamicImports)+len(item.Assets) != 0 {
			return nil, fmt.Errorf("unowned, duplicate or malformed managed font source")
		}
		name := strings.TrimPrefix(item.File, "assets/")
		if name == item.File || name == "" || !strings.HasSuffix(name, ".woff2") || name[0] == '.' {
			return nil, fmt.Errorf("managed font must be a confined WOFF2 asset")
		}
		for _, c := range name {
			if !(c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || c == '.' || c == '-' || c == '_') {
				return nil, fmt.Errorf("unsafe managed font filename")
			}
		}
		url := manifest.Static(key) // Static resolves a key/file, never Entry.Src.
		if url != "/"+item.File || manifest.Static(item.File) != url || byFile[item.File] {
			return nil, fmt.Errorf("unowned or duplicate managed font file")
		}
		if _, duplicate := fonts[url]; duplicate {
			return nil, fmt.Errorf("duplicate managed font URL")
		}
		wanted[item.Src], byFile[item.File], fonts[url] = true, true, false
	}
	for _, seen := range wanted {
		if !seen {
			return nil, fmt.Errorf("required managed font source omitted")
		}
	}
	for _, item := range entries {
		for _, file := range item.Assets {
			if strings.HasSuffix(file, ".woff2") && (!byFile[file] || manifest.Static(file) != "/"+file) {
				return nil, fmt.Errorf("unbound managed font asset")
			}
		}
	}
	startup, visited := map[string]bool{}, map[string]bool{}
	var visit func(string) error
	visit = func(key string) error {
		if visited[key] {
			return nil
		}
		visited[key] = true
		item, ok := entries[key]
		if !ok {
			return fmt.Errorf("missing managed font startup owner")
		}
		for _, file := range item.Assets {
			if byFile[file] {
				startup[file] = true
			}
		}
		for _, key := range item.Imports {
			if err := visit(key); err != nil {
				return err
			}
		}
		return nil
	}
	if err := visit("index.html"); err != nil {
		return nil, err
	}
	if len(startup) != len(wanted) {
		return nil, fmt.Errorf("required fonts are not owned by the static startup graph")
	}
	return fonts, nil
}
