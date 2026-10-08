// Package csp supplies one cryptographic nonce to both template engines.
package csp

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"unicode"
	"unicode/utf8"

	"github.com/a-h/templ"
	"github.com/flosch/pongo2/v6"
)

type nonceKey struct{}

// Policy defaults to enforced strict CSP. Trusted Types is independently
// report-only so consumers can inventory sinks before enforcing it.
type Policy struct {
	ReportOnly bool
	ReportPath string
	ConnectSrc []string
	ImgSrc []string
	FontSrc []string
	// WorkerSrc adds validated sources to the default 'self'. Keep it empty for
	// same-origin worker URLs; add "blob:" only for an explicitly needed worker.
	WorkerSrc []string
	TrustedTypes []string
}

// Nonce returns the exact nonce stored in templ's rendering context.
func Nonce(ctx context.Context) string {
	if n, ok := ctx.Value(nonceKey{}).(string); ok { return n }
	return templ.GetNonce(ctx)
}

// WithNonce is useful for deterministic rendering tests. Middleware generates
// fresh entropy for each production request.
func WithNonce(ctx context.Context, nonce string) context.Context {
	return context.WithValue(templ.WithNonce(ctx, nonce), nonceKey{}, nonce)
}

func invalidHeaderAtom(value string) bool {
    return !utf8.ValidString(value)||strings.ContainsRune(value,';')||strings.IndexFunc(value,func(r rune)bool{return unicode.IsControl(r)||unicode.IsSpace(r)})>=0
}

func sourceList(base string, additional []string) (string, error) {
	for _, source := range additional {
		if source == "" || invalidHeaderAtom(source) || strings.Contains(strings.ToLower(source), "unsafe-") || strings.Contains(strings.ToLower(source), "nonce-") {
			return "", fmt.Errorf("invalid CSP source")
		}
	}
	if len(additional) == 0 { return base, nil }
	return base + " " + strings.Join(additional, " "), nil
}

func headers(p Policy, nonce string) (string, string, error) {
	connect, err := sourceList("'self'", p.ConnectSrc); if err != nil { return "", "", err }
	img, err := sourceList("'self' data:", p.ImgSrc); if err != nil { return "", "", err }
	font, err := sourceList("'self'", p.FontSrc); if err != nil { return "", "", err }
	worker, err := sourceList("'self'", p.WorkerSrc); if err != nil { return "", "", err }
	reportPath := p.ReportPath
	if reportPath == "" { reportPath = "/csp-report" }
	if !strings.HasPrefix(reportPath, "/") || strings.HasPrefix(reportPath, "//") || invalidHeaderAtom(reportPath)||strings.ContainsRune(reportPath,'\\') { return "", "", fmt.Errorf("invalid CSP report path") }
	policies := p.TrustedTypes
	if len(policies) == 0 { policies = []string{"roedu", "roedu-hovercard", "roedu-islands"} }
	for _, name := range policies { if name == "" || invalidHeaderAtom(name)||strings.ContainsAny(name,"'\"") || name == "*" { return "", "", fmt.Errorf("invalid Trusted Types policy") } }
	strict := "default-src 'self'; script-src 'self' 'nonce-" + nonce + "' 'strict-dynamic'; script-src-attr 'none'; style-src 'self' 'nonce-" + nonce + "'; style-src-attr 'none'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; connect-src " + connect + "; img-src " + img + "; font-src " + font + "; worker-src " + worker + "; report-uri " + reportPath
	tt := "require-trusted-types-for 'script'; trusted-types " + strings.Join(policies, " ") + "; report-uri " + reportPath
	return strict, tt, nil
}

// Middleware produces a fresh nonce before calling the handler. Configuration
// errors and entropy failure return 500 before any handler output is written.
func Middleware(policy Policy) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			var entropy [24]byte
			if _, err := io.ReadFull(rand.Reader, entropy[:]); err != nil { http.Error(w, "CSP nonce unavailable", 500); return }
			nonce := base64.RawStdEncoding.EncodeToString(entropy[:])
			strict, tt, err := headers(policy, nonce)
			if err != nil { http.Error(w, "CSP policy invalid", 500); return }
			if policy.ReportOnly {
				// Both policy parts use the same report endpoint; avoid duplicate directives.
				w.Header().Set("Content-Security-Policy-Report-Only", strict + "; " + strings.Split(tt, "; report-uri ")[0])
			} else {
				w.Header().Set("Content-Security-Policy", strict)
				w.Header().Set("Content-Security-Policy-Report-Only", tt)
			}
			w.Header().Set("X-Content-Type-Options", "nosniff")
			next.ServeHTTP(w, r.WithContext(WithNonce(r.Context(), nonce)))
		})
	}
}

// PongoContext copies caller data and installs request.csp_nonce. It never
// mutates the caller's context or trusts a caller-supplied nonce.
func PongoContext(ctx context.Context, data map[string]any) pongo2.Context {
	out := make(pongo2.Context, len(data)+1)
	for key, value := range data { out[key] = value }
	request := map[string]any{}
	switch v := data["request"].(type) {
	case map[string]any: for key, value := range v { request[key] = value }
	case pongo2.Context: for key, value := range v { request[key] = value }
	}
	request["csp_nonce"] = Nonce(ctx)
	out["request"] = request
	return out
}

// Report is a decoded report envelope. The collector decides storage/metrics;
// this package neither persists reports nor logs private document URLs.
type Report map[string]any

// ReportHandler accepts bounded JSON reports via POST and acknowledges them
// with 204. Browsers send either a legacy object or a Reporting API array.
func ReportHandler(collect func(context.Context, []Report)) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost { w.Header().Set("Allow", "POST"); http.Error(w, "method not allowed", 405); return }
		media := strings.TrimSpace(strings.Split(r.Header.Get("Content-Type"), ";")[0])
		if media != "application/csp-report" && media != "application/reports+json" && media != "application/json" { http.Error(w, "JSON report required", 415); return }
		body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, 64<<10))
		if err != nil { http.Error(w, "report too large", 413); return }
		var reports []Report
		if strings.HasPrefix(strings.TrimSpace(string(body)), "[") { err = json.Unmarshal(body, &reports) } else { var report Report; err = json.Unmarshal(body, &report); if report == nil { err = fmt.Errorf("empty report") }; reports = []Report{report} }
		if err != nil || len(reports) == 0 || len(reports) > 100 { http.Error(w, "invalid report", 400); return }
		for _, report := range reports { if report == nil { http.Error(w, "invalid report", 400); return } }
		if collect != nil { collect(r.Context(), reports) }
		w.Header().Set("Cache-Control", "no-store")
		w.WriteHeader(http.StatusNoContent)
	})
}
