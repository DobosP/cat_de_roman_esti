package httpapi

import (
	"bytes"
	"context"
	"fmt"
	stdhtml "html"
	"io"
	"net/http"
	"os"
	"strings"

	"github.com/DobosP/roedu-ui/web-kit/assets"
	"github.com/DobosP/roedu-ui/web-kit/csp"
	"golang.org/x/net/html"
)

// Only current, trusted build bytes are admitted here. Tokenization records
// insertion offsets; it never serializes HTML or rewrites existing attributes.
// SDK Tags emits a replacement asset block. Cat instead retains its exact
// metadata, crossorigin attributes and tag order, using the SDK's actual nonce.
type managedNonceShell struct {
	index        []byte
	metaOffset   int
	nonceOffsets []int
}

func managedTagInsertion(raw []byte, start int) (int, error) {
	end := len(raw) - 1
	if end < 1 || raw[end] != '>' {
		return 0, fmt.Errorf("unfinished managed tag")
	}
	for end > 0 && (raw[end-1] == ' ' || raw[end-1] == '\t' || raw[end-1] == '\r' || raw[end-1] == '\n') {
		end--
	}
	if end > 0 && raw[end-1] == '/' {
		end--
	}
	return start + end, nil
}

// x/net/html removes duplicate attributes while tokenizing, before Token or
// TagAttr exposes them. Check raw names without rewriting bytes or treating
// attribute-like text inside a quoted/unquoted value as another attribute.
func checkManagedRawAttributes(raw []byte) error {
	space := func(c byte) bool {
		return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f'
	}
	end := len(raw) - 1
	if end < 2 || raw[0] != '<' || raw[end] != '>' {
		return fmt.Errorf("malformed managed raw tag")
	}
	i := 1
	for i < end && !space(raw[i]) && raw[i] != '/' {
		i++
	}
	names := map[string]bool{}
	for i < end {
		for i < end && space(raw[i]) {
			i++
		}
		if i == end {
			break
		}
		if raw[i] == '/' {
			if i+1 != end {
				return fmt.Errorf("ambiguous managed self-closing tag")
			}
			break
		}
		start := i
		for i < end && !space(raw[i]) && raw[i] != '=' && raw[i] != '/' {
			if raw[i] < 0x21 || raw[i] > 0x7e || strings.ContainsRune("\"'<>`", rune(raw[i])) {
				return fmt.Errorf("unsupported managed raw attribute name")
			}
			i++
		}
		if i == start {
			return fmt.Errorf("empty managed raw attribute name")
		}
		name := strings.ToLower(string(raw[start:i])) // Admitted names are ASCII.
		if names[name] {
			return fmt.Errorf("duplicate managed attribute")
		}
		names[name] = true
		for i < end && space(raw[i]) {
			i++
		}
		if i == end || raw[i] != '=' {
			continue // Boolean attribute, such as crossorigin.
		}
		i++
		for i < end && space(raw[i]) {
			i++
		}
		if i == end {
			return fmt.Errorf("missing managed raw attribute value")
		}
		if raw[i] == '\'' || raw[i] == '"' {
			quote := raw[i]
			i++
			for i < end && raw[i] != quote {
				if raw[i] == 0 {
					return fmt.Errorf("invalid managed raw attribute value")
				}
				i++
			}
			if i == end {
				return fmt.Errorf("unfinished managed quoted attribute")
			}
			i++
			if i < end && !space(raw[i]) && raw[i] != '/' {
				return fmt.Errorf("unseparated managed raw attribute")
			}
		} else {
			start = i
			for i < end && !space(raw[i]) {
				if raw[i] == 0 || strings.ContainsRune("\"'<=`>", rune(raw[i])) {
					return fmt.Errorf("ambiguous managed unquoted attribute")
				}
				i++
			}
			if i == start {
				return fmt.Errorf("missing managed unquoted attribute")
			}
		}
	}
	return nil
}

func newManagedNonceShell(index []byte, manifest *assets.Manifest) (*managedNonceShell, error) {
	if manifest == nil {
		return nil, fmt.Errorf("managed nonce shell requires manifest")
	}
	entries := manifest.Entries()
	entry, ok := entries["index.html"]
	if !ok || !entry.IsEntry {
		return nil, fmt.Errorf("managed nonce shell requires index entry")
	}
	css, preloads, visited := map[string]bool{}, map[string]bool{}, map[string]bool{}
	var visit func(string) error
	visit = func(key string) error {
		if visited[key] {
			return nil
		}
		visited[key] = true
		item, ok := entries[key]
		if !ok {
			return fmt.Errorf("unknown managed import")
		}
		for _, dep := range item.Imports {
			if err := visit(dep); err != nil {
				return err
			}
		}
		for _, file := range item.CSS {
			css[manifest.Static(file)] = false
		}
		if key != "index.html" {
			preloads[manifest.Static(item.File)] = false
		}
		return nil
	}
	if err := visit("index.html"); err != nil {
		return nil, err
	}
	for url := range css {
		if url == "" {
			return nil, fmt.Errorf("unknown managed stylesheet")
		}
	}
	for url := range preloads {
		if url == "" {
			return nil, fmt.Errorf("unknown managed preload")
		}
	}
	entryURL := manifest.Static("index.html")
	if entryURL == "" {
		return nil, fmt.Errorf("unknown managed module")
	}
	shell := &managedNonceShell{index: append([]byte(nil), index...)}
	z := html.NewTokenizer(bytes.NewReader(index))
	position, htmls, htmlEnds, heads, headEnds, bodies, bodyEnds, modules, roots, rootEnds := 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	inHead, inScript := false, false
	for {
		kind := z.Next()
		raw := z.Raw()
		start := position
		position += len(raw)
		// Token/TagName/TagAttr can normalize the tokenizer's buffer in place.
		// Read raw names and insertion bytes from our exact immutable copy.
		raw = shell.index[start:position]
		if kind == html.ErrorToken {
			if z.Err() != io.EOF {
				return nil, fmt.Errorf("managed HTML tokenization: %w", z.Err())
			}
			if len(raw) != 0 {
				return nil, fmt.Errorf("unfinished managed HTML token")
			}
			break
		}
		if kind == html.StartTagToken || kind == html.SelfClosingTagToken {
			if err := checkManagedRawAttributes(raw); err != nil {
				return nil, err
			}
		}
		token := z.Token()
		if inScript {
			if kind == html.TextToken && strings.TrimSpace(token.Data) == "" {
				continue
			}
			if kind == html.EndTagToken && token.Data == "script" {
				if strings.ToLower(string(raw)) != "</script>" {
					return nil, fmt.Errorf("malformed managed script close")
				}
				inScript = false
				continue
			}
			return nil, fmt.Errorf("managed module contains inline or malformed content")
		}
		if kind == html.EndTagToken {
			if strings.ToLower(string(raw)) != "</"+token.Data+">" {
				return nil, fmt.Errorf("unsupported managed closing tag")
			}
			switch token.Data {
			case "html":
				if htmls != 1 || htmlEnds != 0 || bodyEnds != 1 {
					return nil, fmt.Errorf("malformed managed html")
				}
				htmlEnds++
			case "title":
				if !inHead {
					return nil, fmt.Errorf("managed title outside head")
				}
			case "head":
				if !inHead || heads != 1 || headEnds != 0 {
					return nil, fmt.Errorf("malformed managed head")
				}
				inHead = false
				headEnds++
			case "body":
				if bodies != 1 || bodyEnds != 0 {
					return nil, fmt.Errorf("malformed managed body")
				}
				bodyEnds++
			case "div":
				if roots != 1 || rootEnds != 0 {
					return nil, fmt.Errorf("malformed managed root")
				}
				rootEnds++
			case "script":
				return nil, fmt.Errorf("unmatched managed script")
			}
			continue
		}
		if kind != html.StartTagToken && kind != html.SelfClosingTagToken {
			continue
		}
		attrs := map[string]string{}
		for _, attr := range token.Attr {
			if _, duplicate := attrs[attr.Key]; duplicate {
				return nil, fmt.Errorf("duplicate managed attribute")
			}
			if attr.Namespace != "" || attr.Key == "nonce" || attr.Key == "style" || strings.HasPrefix(attr.Key, "on") {
				return nil, fmt.Errorf("unsupported managed attribute")
			}
			attrs[attr.Key] = attr.Val
		}
		switch token.Data {
		case "html":
			if kind != html.StartTagToken || htmls != 0 || heads != 0 {
				return nil, fmt.Errorf("unsupported managed html")
			}
			htmls++
		case "head":
			if kind != html.StartTagToken || htmls != 1 || htmlEnds != 0 || heads != 0 || bodies != 0 || len(attrs) != 0 {
				return nil, fmt.Errorf("unsupported managed head")
			}
			heads++
			inHead = true
			shell.metaOffset = position
		case "body":
			if kind != html.StartTagToken || inHead || headEnds != 1 || bodies != 0 {
				return nil, fmt.Errorf("unsupported managed body")
			}
			bodies++
		case "div":
			if inHead || bodies != 1 || bodyEnds != 0 || roots != 0 || attrs["id"] != "root" || len(attrs) != 1 ||
				kind != html.StartTagToken {
				return nil, fmt.Errorf("unsupported managed root")
			}
			roots++
		case "title", "meta", "script", "link":
			// Individual supported tags are checked below.
		default:
			return nil, fmt.Errorf("unsupported managed shell tag")
		}
		switch token.Data {
		case "base", "style":
			return nil, fmt.Errorf("unsupported managed shell tag")
		case "meta":
			if strings.EqualFold(attrs["property"], "csp-nonce") || strings.EqualFold(attrs["name"], "csp-nonce") ||
				strings.EqualFold(attrs["http-equiv"], "Content-Security-Policy") ||
				strings.EqualFold(attrs["http-equiv"], "Content-Security-Policy-Report-Only") {
				return nil, fmt.Errorf("duplicate managed nonce or policy bootstrap")
			}
		case "script":
			if kind != html.StartTagToken || !inHead || modules != 0 || attrs["type"] != "module" || attrs["src"] != entryURL {
				return nil, fmt.Errorf("unowned managed script")
			}
			for key, value := range attrs {
				if key != "type" && key != "src" && (key != "crossorigin" || (value != "" && value != "anonymous")) {
					return nil, fmt.Errorf("unsupported managed script attribute")
				}
			}
			offset, err := managedTagInsertion(raw, start)
			if err != nil {
				return nil, err
			}
			shell.nonceOffsets = append(shell.nonceOffsets, offset)
			modules++
			inScript = true
		case "link":
			rel := strings.Fields(strings.ToLower(attrs["rel"]))
			assetRel := ""
			for _, part := range rel {
				if part == "stylesheet" || part == "modulepreload" {
					assetRel = part
				}
			}
			if assetRel == "" {
				continue
			}
			if !inHead || len(rel) != 1 {
				return nil, fmt.Errorf("unsupported managed asset link")
			}
			for key, value := range attrs {
				if key != "rel" && key != "href" && (key != "crossorigin" || (value != "" && value != "anonymous")) {
					return nil, fmt.Errorf("unsupported managed asset link attribute")
				}
			}
			expected := css
			if assetRel == "modulepreload" {
				expected = preloads
			}
			seen, exists := expected[attrs["href"]]
			if !exists || seen {
				return nil, fmt.Errorf("unowned or duplicate managed asset link")
			}
			expected[attrs["href"]] = true
			offset, err := managedTagInsertion(raw, start)
			if err != nil {
				return nil, err
			}
			shell.nonceOffsets = append(shell.nonceOffsets, offset)
		}
	}
	if position != len(index) || htmls != 1 || htmlEnds != 1 || heads != 1 || headEnds != 1 || bodies != 1 || bodyEnds != 1 || modules != 1 || roots != 1 || rootEnds != 1 || inScript {
		return nil, fmt.Errorf("incomplete managed nonce shell")
	}
	for _, seen := range css {
		if !seen {
			return nil, fmt.Errorf("managed stylesheet omitted")
		}
	}
	for _, seen := range preloads {
		if !seen {
			return nil, fmt.Errorf("managed preload omitted")
		}
	}
	return shell, nil
}

func (s *managedNonceShell) render(ctx context.Context) ([]byte, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	nonce := csp.Nonce(ctx)
	if nonce == "" {
		return nil, fmt.Errorf("managed shell requires request nonce")
	}
	escaped := stdhtml.EscapeString(nonce)
	meta := []byte(`<meta property="csp-nonce" content="` + escaped + `" nonce="` + escaped + `">`)
	attribute := []byte(` nonce="` + escaped + `"`)
	var output bytes.Buffer
	position := 0
	output.Write(s.index[:s.metaOffset])
	output.Write(meta)
	position = s.metaOffset
	for _, offset := range s.nonceOffsets {
		output.Write(s.index[position:offset])
		output.Write(attribute)
		position = offset
	}
	output.Write(s.index[position:])
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	return output.Bytes(), nil
}

func (s *managedSPA) serveIndex(w http.ResponseWriter, r *http.Request) {
	if s.nonceShell == nil {
		// Frozen legacy rollback retains its exact raw index and prior policy.
		w.Header().Set("Cache-Control", "no-cache")
		websiteBytes(w, r, 200, "text/html; charset=utf-8", s.index)
		return
	}
	body, err := s.nonceShell.render(r.Context())
	if err != nil {
		websiteBytes(w, r, 500, "text/html; charset=utf-8", nil)
		return
	}
	// A nonce-bearing document must not be stored or replayed by a cache.
	w.Header().Set("Cache-Control", "no-store")
	websiteBytes(w, r, 200, "text/html; charset=utf-8", body)
}

func (s *managedSPA) installIndexHandler() error {
	s.indexHandler = http.HandlerFunc(s.serveIndex)
	if s.nonceShell != nil {
		// This existing app flag selects actual stage B; no caller nonce, relaxed
		// source list, inline exception or Trusted Types waiver is accepted.
		flag := os.Getenv("CAT_CSP_ENFORCE")
		if flag != "" && flag != "false" && flag != "true" {
			return fmt.Errorf("CAT_CSP_ENFORCE must be true or false")
		}
		s.indexHandler = managedNonceNoStore(csp.Middleware(csp.Policy{ReportOnly: flag != "true"})(s.indexHandler))
	}
	return nil
}

// Keep the current document non-cacheable before SDK middleware can refuse
// entropy/policy and before rendering can fail. Legacy/assets/APIs never use it.
func managedNonceNoStore(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-store")
		next.ServeHTTP(w, r)
	})
}
