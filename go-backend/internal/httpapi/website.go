package httpapi

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
)

const unfinalizedLegalSentence = " Operatorul și datele de contact nu sunt încă finalizate."

var legalBannerPattern = regexp.MustCompile(`(?s)<div class="draft">.*?</div>`)
var legalOperatorPattern = regexp.MustCompile(`(?s)Operatorul serviciului este <strong>.*?</strong>\. `)
var legalContactPattern = regexp.MustCompile(`(?s)<a href="mailto:[^"]*">.*?</a>`)
var legalVersionPattern = regexp.MustCompile(`(?s)<p class='draft'>Versiune schiță: <code>.*?</code></p>`)
var immutableViteAsset = regexp.MustCompile(`^/assets/.+-[A-Za-z0-9_-]{8}\.(?:css|js|woff|woff2)$`)

type websiteSettings struct{ operator, contact, donate, consentVersion string }

func websiteConfig() websiteSettings {
	version, ok := os.LookupEnv("CAT_CONSENT_VERSION")
	if !ok {
		version = "2026-07-09"
	}
	return websiteSettings{strings.TrimFunc(os.Getenv("CAT_LEGAL_OPERATOR"), pySpace), strings.TrimFunc(os.Getenv("CAT_LEGAL_CONTACT_EMAIL"), pySpace), strings.TrimFunc(os.Getenv("CAT_DONATE_URL"), pySpace), version}
}
func djangoEscape(text string) string {
	return strings.NewReplacer("&", "&amp;", "<", "&lt;", ">", "&gt;", "\"", "&quot;", "'", "&#x27;").Replace(text)
}
func renderLegal(base string, c websiteSettings) string {
	// Exports use neutral operator/contact settings. Removing their old slots also
	// keeps previously exported pages independent of the runtime configuration.
	base = legalOperatorPattern.ReplaceAllString(base, "")
	base = legalContactPattern.ReplaceAllString(base, "<code>[[PLACEHOLDER: contact]]</code>")
	banner := `<div class="draft"><strong>DRAFT — text în lucru.</strong> Acest document trebuie completat și verificat de un avocat specializat în protecția datelor înainte de publicare.`
	if c.operator == "" || c.contact == "" {
		banner += unfinalizedLegalSentence
	}
	banner += "</div>"
	base = legalBannerPattern.ReplaceAllString(base, banner)
	if c.operator != "" {
		base = strings.ReplaceAll(base, "Pentru orice cerere sau plângere:", "Operatorul serviciului este <strong>"+djangoEscape(c.operator)+"</strong>. Pentru orice cerere sau plângere:")
	}
	if c.contact != "" {
		safe := djangoEscape(c.contact)
		base = strings.ReplaceAll(base, "<code>[[PLACEHOLDER: contact]]</code>", `<a href="mailto:`+safe+`">`+safe+`</a>`)
	}
	base = legalVersionPattern.ReplaceAllString(base, "")
	if c.consentVersion != "" {
		note := "<p class='draft'>Versiune schiță: <code>" + c.consentVersion + "</code></p>"
		base = strings.Replace(base, "\n<footer>", note+"\n<footer>", 1)
	}
	// CAT_MIN_SELF_CONSENT_AGE controls account gates. The Python legal notices
	// describe Romania's statutory 16-year threshold literally, independent of it.
	return base
}
func websiteHeaders(w http.ResponseWriter) {
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Referrer-Policy", "same-origin")
	w.Header().Set("Cross-Origin-Opener-Policy", "same-origin")
	w.Header().Set("X-Frame-Options", "DENY")
}
func websiteBytes(w http.ResponseWriter, r *http.Request, status int, kind string, body []byte) {
	websiteHeaders(w)
	if kind != "" {
		w.Header().Set("Content-Type", kind)
	}
	w.Header().Set("Content-Length", strconv.Itoa(len(body)))
	w.WriteHeader(status)
	if r.Method != "HEAD" {
		_, _ = w.Write(body)
	}
}
func staticFile(root, path string) (string, os.FileInfo, bool) {
	if path == "/" {
		path = "/index.html"
	}
	relative := strings.TrimPrefix(path, "/")
	if relative == "" || strings.Contains(relative, "\\") || strings.Contains(relative, "//") || strings.HasPrefix(relative, "/") || filepath.VolumeName(relative) != "" {
		return "", nil, false
	}
	for _, part := range strings.Split(relative, "/") {
		if part == "." || part == ".." {
			return "", nil, false
		}
	}
	file := filepath.Join(root, filepath.FromSlash(relative))
	canonical, err := filepath.EvalSymlinks(file)
	if err != nil {
		return "", nil, false
	}
	absoluteRoot, err := filepath.Abs(root)
	if err != nil {
		return "", nil, false
	}
	canonical, err = filepath.Abs(canonical)
	if err != nil {
		return "", nil, false
	}
	rel, err := filepath.Rel(absoluteRoot, canonical)
	if err != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		return "", nil, false
	}
	info, err := os.Stat(canonical)
	return canonical, info, err == nil && info.Mode().IsRegular()
}
func staticType(path string) string {
	switch strings.ToLower(filepath.Ext(path)) {
	case ".html":
		return `text/html; charset="utf-8"`
	case ".js", ".mjs":
		return `text/javascript; charset="utf-8"`
	case ".css":
		return `text/css; charset="utf-8"`
	case ".json":
		return "application/json"
	case ".svg":
		return "image/svg+xml"
	case ".png":
		return "image/png"
	case ".ico":
		return "image/vnd.microsoft.icon"
	case ".woff":
		return "font/woff"
	case ".woff2":
		return "font/woff2"
	default:
		return "application/octet-stream"
	}
}

// WhiteNoise supports one range. Malformed/multipart ranges are ignored.
func staticRange(header string, size int64) (start, end int64, status int) {
	start, end, status = 0, size-1, 200
	if !strings.HasPrefix(header, "bytes=") || strings.Contains(header, ",") {
		return
	}
	parts := strings.Split(strings.TrimPrefix(header, "bytes="), "-")
	if len(parts) != 2 {
		return
	}
	if parts[0] == "" {
		suffix, err := strconv.ParseInt(strings.TrimSpace(parts[1]), 10, 64)
		if err != nil || suffix < 0 {
			return
		}
		start = max(0, size-suffix)
		end = size - 1
	} else {
		first, err := strconv.ParseInt(strings.TrimSpace(parts[0]), 10, 64)
		if err != nil || first < 0 {
			return
		}
		start = first
		if parts[1] != "" {
			last, err := strconv.ParseInt(strings.TrimSpace(parts[1]), 10, 64)
			if err != nil {
				return 0, size - 1, 200
			}
			end = min(last, size-1)
		}
	}
	if start >= size || end < start {
		return 0, 0, 416
	}
	return start, end, 206
}
func serveStatic(w http.ResponseWriter, r *http.Request, file string, info os.FileInfo, path string) {
	websiteHeaders(w)
	if r.Method != "GET" && r.Method != "HEAD" {
		w.Header().Set("Allow", "GET, HEAD")
		w.WriteHeader(405)
		return
	}
	cache := "max-age=0, public"
	if immutableViteAsset.MatchString(path) {
		cache = "max-age=315360000, public, immutable"
	}
	w.Header().Set("Cache-Control", cache)
	etag := fmt.Sprintf("\"%x-%x\"", info.ModTime().Unix(), info.Size())
	modified := info.ModTime().UTC().Truncate(time.Second)
	w.Header().Set("ETag", etag)
	w.Header().Set("Last-Modified", modified.Format(http.TimeFormat))
	fresh := false
	if value, present := r.Header["If-None-Match"]; present {
		fresh = len(value) > 0 && value[0] == etag
	} else if date, err := http.ParseTime(r.Header.Get("If-Modified-Since")); err == nil {
		fresh = !date.Before(modified)
	}
	if fresh {
		w.Header().Del("Last-Modified")
		w.WriteHeader(304)
		return
	}
	data, err := os.ReadFile(file)
	if err != nil {
		websiteBytes(w, r, 404, "text/html; charset=utf-8", nil)
		return
	}
	typePath := path
	if strings.HasSuffix(path, "/") {
		typePath = "index.html"
	}
	w.Header().Set("Content-Type", staticType(typePath))
	w.Header().Set("Accept-Ranges", "bytes")
	start, end, status := staticRange(r.Header.Get("Range"), int64(len(data)))
	if status == 416 {
		w.Header().Set("Content-Range", fmt.Sprintf("bytes */%d", len(data)))
		websiteBytes(w, r, 416, "", nil)
		return
	}
	if status == 206 {
		w.Header().Set("Content-Range", fmt.Sprintf("bytes %d-%d/%d", start, end, len(data)))
		data = data[start : end+1]
	}
	websiteBytes(w, r, status, "", data)
}
func (s *Server) website(w http.ResponseWriter, r *http.Request) bool {
	path := r.URL.Path
	switch path {
	case "/api/health", "/api/categories", "/api/manifest":
		w.Header().Set("Allow", "GET, HEAD, OPTIONS")
		if r.Method != "GET" && r.Method != "HEAD" {
			write(w, r, 405, map[string]any{"detail": "Method Not Allowed"})
			return true
		}
		if path == "/api/manifest" {
			write(w, r, 200, s.content.Manifest)
		} else {
			write(w, r, 200, s.content.Metadata[path])
		}
		return true
	case "/api/me":
		write(w, r, 200, map[string]any{"accounts_enabled": false, "authenticated": false, "user": nil, "donate_url": websiteConfig().donate})
		return true
	case "/openapi.json":
		w.Header().Set("Allow", "GET, HEAD, OPTIONS")
		w.Header().Add("Vary", "Accept")
		if r.Method == "OPTIONS" {
			websiteJSON(w, r, 200, openapiType(r), map[string]any{"name": "Spectacular Jsonapi", "description": "", "renders": []string{"application/vnd.oai.openapi+json", "application/json"}, "parses": []string{"application/json"}})
		} else if r.Method != "GET" && r.Method != "HEAD" {
			websiteJSON(w, r, 405, openapiType(r), map[string]any{"detail": "Method \"" + r.Method + "\" not allowed."})
		} else {
			w.Header().Set("Content-Disposition", `inline; filename="cat_de_roman_esti.json"`)
			websiteJSON(w, r, 200, openapiType(r), s.content.Metadata["openapi"])
		}
		return true
	case "/api/submissions":
		w.Header().Set("Allow", "POST, OPTIONS")
		if r.Method != "POST" {
			write(w, r, 405, map[string]any{"detail": "Method Not Allowed"})
		} else {
			s.submit(w, r)
		}
		return true
	case "/legal/privacy", "/legal/terms":
		key := "privacy_html"
		if path == "/legal/terms" {
			key = "terms_html"
		}
		base, _ := s.content.Metadata[key].(string)
		websiteBytes(w, r, 200, "text/html; charset=utf-8", []byte(renderLegal(base, websiteConfig())))
		return true
	}
	if strings.HasPrefix(path, "/api/") {
		return false
	}
	if s.StaticRoot == "" {
		return s.managedWebsite(w, r)
	}
	if file, info, exists := staticFile(s.StaticRoot, path); exists {
		if strings.HasSuffix(path, "/index.html") {
			w.Header().Set("Location", (&url.URL{Path: strings.TrimSuffix(path, "index.html")}).EscapedPath())
			w.Header().Set("Cache-Control", "max-age=0, public")
			websiteHeaders(w)
			w.WriteHeader(302)
		} else {
			serveStatic(w, r, file, info, path)
		}
		return true
	}
	if path != "/" && !strings.HasSuffix(path, "/") {
		if _, _, exists := staticFile(s.StaticRoot, path+"/index.html"); exists {
			w.Header().Set("Location", (&url.URL{Path: path + "/"}).EscapedPath())
			w.Header().Set("Cache-Control", "max-age=0, public")
			websiteHeaders(w)
			w.WriteHeader(302)
			return true
		}
	}
	if strings.HasSuffix(path, "/") && path != "/" {
		if file, info, exists := staticFile(s.StaticRoot, path+"index.html"); exists {
			serveStatic(w, r, file, info, path)
			return true
		}
	}
	if strings.HasPrefix(path, "/assets/") {
		websiteBytes(w, r, 404, "text/html; charset=utf-8", nil)
		return true
	}
	if index, err := os.ReadFile(filepath.Join(s.StaticRoot, "index.html")); err == nil {
		w.Header().Set("Cache-Control", "no-cache")
		websiteBytes(w, r, 200, "text/html; charset=utf-8", index)
		return true
	}
	if path == "/" || path == "" {
		websiteBytes(w, r, 200, "text/html; charset=utf-8", []byte(missingBuildHTML))
		return true
	}
	write(w, r, 404, map[string]any{"detail": "Not Found"})
	return true
}

const missingBuildHTML = `<!doctype html>
<html lang="ro">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>cat_de_roman_esti</title>
  <style>
    body { margin:0; min-height:100vh; display:flex; align-items:center;
      justify-content:center; font-family: system-ui, sans-serif; color:#e8e8f0;
      background: radial-gradient(1200px 800px at 30% 20%, #1b2350, #0a0d1f 70%); }
    .card { max-width: 34rem; padding: 2rem 2.5rem; border-radius: 18px;
      background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
      box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
    h1 { margin:0 0 .5rem; font-size:1.6rem;
      background: linear-gradient(90deg,#ffd166,#ef476f,#118ab2);
      -webkit-background-clip:text; background-clip:text; color:transparent; }
    code { background: rgba(255,255,255,0.08); padding:.15rem .4rem; border-radius:6px; }
    a { color:#84d6ff; }
    p { line-height:1.55; }
  </style>
</head>
<body>
  <div class="card">
    <h1>cat_de_roman_esti</h1>
    <p>The API is live, but the front-end build is missing.</p>
    <p>Build the SPA to play the word-game arcade:</p>
    <p><code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code></p>
    <p>The API is at <a href="/api/health">/api/health</a>.</p>
  </div>
</body>
</html>
`

func openapiType(r *http.Request) string {
	if strings.Contains(r.Header.Get("Accept"), "application/json") && !strings.Contains(r.Header.Get("Accept"), "application/vnd.oai.openapi+json") {
		return "application/json"
	}
	return "application/vnd.oai.openapi+json"
}
func websiteJSON(w http.ResponseWriter, r *http.Request, status int, kind string, value any) {
	var buffer bytes.Buffer
	e := json.NewEncoder(&buffer)
	e.SetEscapeHTML(false)
	if err := e.Encode(value); err != nil {
		write(w, r, 500, map[string]any{"detail": "Internal Server Error"})
		return
	}
	websiteBytes(w, r, status, kind, bytes.TrimSuffix(buffer.Bytes(), []byte("\n")))
}
