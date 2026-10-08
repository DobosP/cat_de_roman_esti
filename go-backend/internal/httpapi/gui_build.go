package httpapi

import (
	"io/fs"
	"net/http"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/guibuild"
)

func (s *Server) initGUIBuild(assets, metadata fs.FS, mode string) {
	s.guiBuild = nil
	if (mode != "" && mode != "current") || s.managedUI == nil || s.managedUIError != nil {
		return
	}
	identity, err := guibuild.Load(assets, metadata)
	if err == nil {
		s.guiBuild = identity
	}
}

func (s *Server) serveGUIBuild(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	if r.Method != http.MethodGet && r.Method != http.MethodHead {
		w.Header().Set("Allow", "GET, HEAD")
		write(w, r, http.StatusMethodNotAllowed, map[string]any{"detail": "Method not allowed"})
		return
	}
	if s.StaticRoot != "" || s.managedUI == nil || s.managedUIError != nil || s.guiBuild == nil || s.guiBuild.Validate() != nil {
		write(w, r, http.StatusServiceUnavailable, map[string]any{"detail": "GUI build identity unavailable"})
		return
	}
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Referrer-Policy", "same-origin")
	w.Header().Set("Cross-Origin-Opener-Policy", "same-origin")
	s.guiBuild.ServeHTTP(w, r)
}
