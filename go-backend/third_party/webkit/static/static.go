// Package static serves only gzip/Brotli precompressed embedded assets.
package static

import (
	"io/fs"
	"net/http"
	"path"
	"regexp"
	"strings"

	"github.com/vearutop/statigz"
	"github.com/vearutop/statigz/brotli"
)

type Options struct { Prefix string }
var hashed=regexp.MustCompile(`(?:^|[-.])[a-fA-F0-9]{8}(?:[-.])`)

// Handler indexes the FS once via statigz. Prefix is the embedded directory,
// not an HTTP mount prefix; use http.StripPrefix for a /static/ mount.
func Handler(files fs.ReadDirFS,o Options) http.Handler {
	opts:=[]func(*statigz.Server){brotli.AddEncoding}
	if o.Prefix!="" {opts=append(opts,statigz.FSPrefix(o.Prefix))}
	server:=statigz.FileServer(files,opts...)
	return http.HandlerFunc(func(w http.ResponseWriter,r *http.Request) {
		if r.Method!=http.MethodGet && r.Method!=http.MethodHead {w.Header().Set("Allow","GET, HEAD");http.Error(w,"method not allowed",405);return}
		for _,part:=range strings.Split(r.URL.Path,"/") {
			if strings.HasPrefix(part,".") || strings.ContainsAny(part,"\\\x00") {http.NotFound(w,r);return}
		}
		for _,ext:=range []string{".zst",".gz",".br"} {if strings.HasSuffix(r.URL.Path,ext) {http.NotFound(w,r);return}}
		w.Header().Set("Cache-Control","no-cache")
		if !server.Found(r) {http.NotFound(w,r);return}
		if path.Ext(r.URL.Path)!=".html" && hashed.MatchString(path.Base(r.URL.Path)) {w.Header().Set("Cache-Control","public, max-age=31536000, immutable")}
		w.Header().Set("X-Content-Type-Options","nosniff")
		w.Header().Add("Vary","Accept-Encoding")
		server.ServeHTTP(w,r)
	})
}
