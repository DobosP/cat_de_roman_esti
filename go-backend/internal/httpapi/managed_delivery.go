package httpapi

import (
	"bytes"
	"fmt"
	"io/fs"
	"strings"
)

// managedUIPreact is the <html data-ui> value a current build declares once it
// is the Preact shell. Only that declaration activates the per-route split; an
// environment mode, request value or Go constant never does.
const managedUIPreact = "preact"

// managedPortedRoutes is the Go-side M2 pilot set (PROGRAM E3/E6). A Preact
// current bundle serves exactly these document paths; every other path, deep
// link or client-side fallback is served by the frozen legacy shell. Matching
// is on the exact request path: queries, cookies and headers never select.
var managedPortedRoutes = map[string]bool{"/": true, "/intrusul": true, "/conexiuni": true}

// document chooses the bundle whose nonce shell answers a document request.
func (ui *managedSPA) document(requestPath string) *managedSPA {
	if ui.frozen == nil || managedPortedRoutes[requestPath] {
		return ui
	}
	return ui.frozen
}

// assetOwner chooses the bundle whose SDK static handler serves a public
// file. A single bundle keeps the existing regular-file check; a split uses
// the owner table admitted at startup.
func (ui *managedSPA) assetOwner(relative string) *managedSPA {
	if ui.owners != nil {
		return ui.owners[relative]
	}
	if info, err := fs.Stat(ui.files, relative); err == nil && info.Mode().IsRegular() {
		return ui
	}
	return nil
}

// managedAssetOwners maps every public file of both bundles to one owner.
// Documents and private paths are never assets. A file present in both
// trees is admitted only with identical bytes, served from the current
// bundle; different bytes behind one URL refuse the whole split.
func managedAssetOwners(current, frozen *managedSPA) (map[string]*managedSPA, error) {
	owners := map[string]*managedSPA{}
	for _, owner := range []*managedSPA{current, frozen} {
		err := fs.WalkDir(owner.files, ".", func(name string, entry fs.DirEntry, err error) error {
			if err != nil {
				return err
			}
			if entry.IsDir() || name == "index.html" {
				return nil
			}
			for _, part := range strings.Split(name, "/") {
				if strings.HasPrefix(part, ".") {
					return nil // Private manifests and scaffold stay refused before dispatch.
				}
			}
			if !entry.Type().IsRegular() {
				return fmt.Errorf("nonregular managed UI entry: %s", name)
			}
			previous, shared := owners[name]
			if !shared {
				owners[name] = owner
				return nil
			}
			a, err := fs.ReadFile(previous.files, name)
			if err != nil {
				return err
			}
			b, err := fs.ReadFile(owner.files, name)
			if err != nil {
				return err
			}
			if !bytes.Equal(a, b) {
				return fmt.Errorf("conflicting managed asset bytes: %s", name)
			}
			return nil
		})
		if err != nil {
			return nil, err
		}
	}
	return owners, nil
}
