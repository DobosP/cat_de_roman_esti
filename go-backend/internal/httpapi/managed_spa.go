package httpapi

import (
	"fmt"
	"io/fs"
	"net/http"
	"path"
	"strings"

	"github.com/DobosP/roedu-ui/web-kit/assets"
	"github.com/DobosP/roedu-ui/web-kit/csp"
	kitstatic "github.com/DobosP/roedu-ui/web-kit/static"
)

type managedSPA struct {
	files        fs.FS
	index        []byte
	static       http.Handler
	nonceShell   *managedNonceShell
	indexHandler http.Handler
}

// The SDK recognizes hexadecimal hashes. Cat's Vite hashes also contain other
// letters, underscores and hyphens; retain its cache policy after the actual
// SDK status is known, without changing SDK byte/range/conditional serving.
type managedAssetResponse struct {
	http.ResponseWriter
	immutable           bool
	wroteHeader         bool
	deferredNotModified bool
}

func (w *managedAssetResponse) WriteHeader(status int) {
	if w.wroteHeader {
		return
	}
	w.wroteHeader = true
	if status == http.StatusOK || status == http.StatusPartialContent || status == http.StatusNotModified {
		if w.immutable {
			w.Header().Set("Cache-Control", "max-age=315360000, public, immutable")
		} else {
			w.Header().Set("Cache-Control", "max-age=0, public")
		}
	} else {
		w.Header().Set("Cache-Control", "no-cache")
	}
	if status == http.StatusNotModified && w.Header().Get("ETag") == "" {
		// Resolve missing SDK metadata only after its handler returns, avoiding
		// re-entry while it is committing this conditional response.
		w.deferredNotModified = true
		return
	}
	w.ResponseWriter.WriteHeader(status)
}

func (w *managedAssetResponse) Write(data []byte) (int, error) {
	if !w.wroteHeader {
		w.WriteHeader(http.StatusOK)
	}
	if w.deferredNotModified {
		return 0, http.ErrBodyNotAllowed
	}
	return w.ResponseWriter.Write(data)
}

func (w *managedAssetResponse) Unwrap() http.ResponseWriter { return w.ResponseWriter }

// This observer records only SDK headers/status; it never stores a body or
// makes a network request. A nonempty body disqualifies a metadata observation.
type managedAssetMetadata struct {
	header      http.Header
	status      int
	bodyWritten bool
}

func (w *managedAssetMetadata) Header() http.Header { return w.header }
func (w *managedAssetMetadata) WriteHeader(status int) {
	if w.status == 0 {
		w.status = status
	}
}
func (w *managedAssetMetadata) Write(data []byte) (int, error) {
	if w.status == 0 {
		w.status = http.StatusOK
	}
	if len(data) != 0 {
		w.bodyWritten = true
	}
	return len(data), nil
}

func managedAssetETag(handler http.Handler, r *http.Request) string {
	head := r.Clone(r.Context())
	head.Header = r.Header.Clone()
	head.Method, head.Body, head.ContentLength, head.GetBody = http.MethodHead, http.NoBody, 0, nil
	head.TransferEncoding, head.Trailer = nil, nil
	for key := range head.Header {
		for _, condition := range []string{"If-Match", "If-None-Match", "If-Modified-Since", "If-Unmodified-Since", "Range", "If-Range"} {
			if strings.EqualFold(key, condition) {
				delete(head.Header, key)
			}
		}
	}
	metadata := &managedAssetMetadata{header: make(http.Header)}
	handler.ServeHTTP(metadata, head)
	if metadata.status == 0 {
		metadata.status = http.StatusOK
	}
	etag := metadata.header.Get("ETag")
	if metadata.status != http.StatusOK || metadata.bodyWritten || len(etag) > 1024 || strings.ContainsAny(etag, "\r\n") {
		return ""
	}
	return etag
}

func (w *managedAssetResponse) finish(handler http.Handler, r *http.Request) {
	if w.deferredNotModified {
		if w.Header().Get("ETag") == "" {
			if etag := managedAssetETag(handler, r); etag != "" {
				w.Header().Set("ETag", etag)
			}
		}
		w.ResponseWriter.WriteHeader(http.StatusNotModified)
		return
	}
	// A successful SDK HEAD can return headers without writing a status or body.
	if !w.wroteHeader {
		w.WriteHeader(http.StatusOK)
	}
}

// Selection is bounded to the two compiled trees. StaticRoot remains an
// explicit disk override for existing independent qualification tools/tests.
func newManagedSPA(files fs.ReadDirFS, mode string) (*managedSPA, error) {
	root := "dist"
	switch mode {
	case "", "current":
	case "legacy":
		root = "legacy"
	default:
		return nil, fmt.Errorf("CAT_UI must be current or legacy")
	}
	err := fs.WalkDir(files, root, func(name string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		info, err := entry.Info()
		if err != nil {
			return err
		}
		if !info.IsDir() && !info.Mode().IsRegular() {
			return fmt.Errorf("nonregular managed UI entry: %s", name)
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	manifest, err := assets.Parse(files, root+"/.vite/manifest.json", root, "/")
	if err != nil {
		return nil, err
	}
	if !manifest.Entries()["index.html"].IsEntry {
		return nil, fmt.Errorf("managed UI has no index.html entry")
	}
	index, err := fs.ReadFile(files, root+"/index.html")
	if err != nil {
		return nil, err
	}
	if len(index) == 0 {
		return nil, fmt.Errorf("empty managed UI index")
	}
	selected, err := fs.Sub(files, root)
	if err != nil {
		return nil, err
	}
	ui := &managedSPA{files: selected, index: index, static: kitstatic.Handler(files, kitstatic.Options{Prefix: root})}
	if root == "dist" {
		ui.nonceShell, err = newManagedNonceShell(index, manifest)
		if err != nil {
			return nil, err
		}
	}
	if err := ui.installIndexHandler(); err != nil {
		return nil, err
	}
	return ui, nil
}

func (s *Server) managedWebsite(w http.ResponseWriter, r *http.Request) bool {
	requestPath := r.URL.Path
	if requestPath == "/csp-report" {
		// Acknowledge bounded browser reports without retaining private URLs,
		// samples or user data. Host/body/CORS/account ordering already ran.
		websiteHeaders(w)
		csp.ReportHandler(nil).ServeHTTP(w, r)
		return true
	}
	if requestPath == "/api" || strings.HasPrefix(requestPath, "/api/") {
		return false
	}
	// Embedded files have no disk escape; private manifests and scaffold are
	// still refused rather than accidentally receiving the SPA fallback.
	for _, part := range strings.Split(requestPath, "/") {
		if strings.HasPrefix(part, ".") || strings.ContainsAny(part, "\\\x00") {
			websiteBytes(w, r, 404, "text/html; charset=utf-8", nil)
			return true
		}
	}
	if !strings.HasPrefix(requestPath, "/") || strings.Contains(requestPath, "//") {
		websiteBytes(w, r, 404, "text/html; charset=utf-8", nil)
		return true
	}
	if s.managedUI == nil {
		write(w, r, 503, map[string]any{"detail": "Managed UI unavailable"})
		return true
	}
	if requestPath == "/index.html" {
		w.Header().Set("Location", "/")
		w.Header().Set("Cache-Control", "max-age=0, public")
		websiteHeaders(w)
		w.WriteHeader(302)
		return true
	}
	if r.Method != http.MethodGet && r.Method != http.MethodHead {
		websiteHeaders(w)
		w.Header().Set("Allow", "GET, HEAD")
		w.WriteHeader(405)
		return true
	}
	relative := strings.TrimPrefix(requestPath, "/")
	if relative != "" {
		if info, err := fs.Stat(s.managedUI.files, relative); err == nil && info.Mode().IsRegular() {
			websiteHeaders(w)
			response := &managedAssetResponse{ResponseWriter: w, immutable: immutableViteAsset.MatchString(requestPath)}
			s.managedUI.static.ServeHTTP(response, r)
			response.finish(s.managedUI.static, r)
			return true
		}
	}
	if strings.HasPrefix(requestPath, "/assets/") || path.Ext(requestPath) != "" {
		websiteBytes(w, r, 404, "text/html; charset=utf-8", nil)
		return true
	}
	websiteHeaders(w)
	s.managedUI.indexHandler.ServeHTTP(w, r)
	return true
}
