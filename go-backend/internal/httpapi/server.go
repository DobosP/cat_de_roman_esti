// Package httpapi serves the anonymous six-game arcade and exploration API.
package httpapi

import (
	"bytes"
	"encoding/json"
	"io"
	"math/big"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"
	"unicode"
	"unicode/utf8"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/accounts"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/alchimie"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/alchimie_explore"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/conexiuni"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contexto"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/intrusul"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/lant"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/perechi"
	"github.com/DobosP/cat_de_roman_esti/shared-go/authcore"
)

const prefix = "/api/wordgames/intrusul/games"
const MaxRequestBytes = 64 * 1024

var localOrigin = regexp.MustCompile(`^http://(localhost|127\.0\.0\.1)(:\d+)?$`)

type Server struct {
	submissions         submissionQueue
	Accounts            *accounts.Service
	Auth                *authcore.Service
	authMux             *http.ServeMux
	authOrigin          string
	accountGameLifetime time.Duration
	game                *intrusul.Service
	content             *content.Content
	StaticRoot          string
	allowedHosts        []string
	perechi             *perechi.Service
	conexiuni           *conexiuni.Service
	contexto            *contexto.Service
	lant                *lant.Service
	alchimie            *alchimie.Service
	explorer            *alchimie_explore.Service
}

func New(c *content.Content) *Server {
	s := &Server{game: intrusul.New(c), content: c, allowedHosts: configuredHosts()}
	s.StaticRoot = defaultStaticRoot()
	s.perechi = perechi.New(c)
	s.conexiuni = conexiuni.New(c)
	s.contexto = contexto.New(c)
	s.lant = lant.New(c)
	s.alchimie = alchimie.New(c)
	s.explorer = alchimie_explore.New(c)
	return s
}

func write(w http.ResponseWriter, r *http.Request, status int, body any) {
	var b bytes.Buffer
	enc := json.NewEncoder(&b)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(body); err != nil {
		http.Error(w, "Internal Server Error", 500)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Referrer-Policy", "same-origin")
	w.Header().Set("Cross-Origin-Opener-Policy", "same-origin")
	if status == 413 {
		w.Header().Set("Cache-Control", "no-store")
	}
	w.WriteHeader(status)
	if r.Method != http.MethodHead {
		_, _ = w.Write(bytes.TrimSuffix(b.Bytes(), []byte("\n")))
	}
}

func (s *Server) serveHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("X-Cat-Runtime", "go")
	if r.ContentLength > MaxRequestBytes {
		write(w, r, 413, map[string]any{"detail": "Request body too large"})
		return
	}
	// Keep the established size/preflight precedence while refusing configured
	// hosts before an upload can occupy the anonymous handler.
	origin := r.Header.Get("Origin")
	localCORS := localOrigin.MatchString(origin) && (s.Auth == nil || origin == s.authOrigin)
	preflight := localCORS && r.Method == "OPTIONS" && r.Header.Get("Access-Control-Request-Method") != ""
	if !preflight && !validHost(r.Host, s.allowedHosts) {
		w.Header().Add("Vary", "origin")
		if localCORS {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Access-Control-Allow-Credentials", "true")
		}
		websiteBytes(w, r, 400, "text/html; charset=utf-8", []byte(badHostHTML))
		return
	}
	if r.Body != nil {
		raw, err := io.ReadAll(io.LimitReader(r.Body, MaxRequestBytes+1))
		if err != nil {
			write(w, r, 400, map[string]any{"detail": "Request body unreadable"})
			_ = r.Body.Close()
			return
		}
		if len(raw) > MaxRequestBytes {
			write(w, r, 413, map[string]any{"detail": "Request body too large"})
			_ = r.Body.Close()
			return
		}
		_ = r.Body.Close()
		r.Body = io.NopCloser(bytes.NewReader(raw))
	}
	{
		w.Header().Add("Vary", "origin")
		if origin := r.Header.Get("Origin"); localOrigin.MatchString(origin) && (s.Auth == nil || origin == s.authOrigin) {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Access-Control-Allow-Credentials", "true")
			if r.Method == "OPTIONS" && r.Header.Get("Access-Control-Request-Method") != "" {
				w.Header().Set("Access-Control-Allow-Headers", "accept, authorization, content-type, user-agent, x-csrftoken, x-requested-with")
				w.Header().Set("Access-Control-Allow-Methods", "DELETE, GET, OPTIONS, PATCH, POST, PUT")
				w.Header().Set("Access-Control-Max-Age", "86400")
				w.Header().Set("Content-Length", "0")
				w.WriteHeader(200)
				return
			}
		}
	}
	if !validHost(r.Host, s.allowedHosts) {
		websiteBytes(w, r, 400, "text/html; charset=utf-8", []byte(badHostHTML))
		return
	}
	if r.URL.Path == "/healthz" {
		write(w, r, 200, map[string]any{"ok": true})
		return
	}
	if !strings.HasPrefix(r.URL.Path, "/api/wordgames/intrusul") {
		if s.arcade(w, r) {
			return
		}
		if s.website(w, r) {
			return
		}
		s.standalone(w, r)
		return
	}
	if r.ContentLength > MaxRequestBytes {
		write(w, r, 413, map[string]any{"detail": "Request body too large"})
		return
	}
	var body map[string]any
	var err *intrusul.Error
	if r.URL.Path == prefix {
		if r.Method != "POST" {
			write(w, r, 405, map[string]any{"detail": "Method Not Allowed"})
			return
		}
		q := queryValues(r.URL.RawQuery)
		seed, failure := queryInt(q, "seed")
		if failure != nil {
			write(w, r, 422, failure)
			return
		}
		starter, failure := queryInt(q, "starter")
		if failure != nil {
			write(w, r, 422, failure)
			return
		}
		category := last(q, "category")
		if q.Has("category") && s.content.CategoryLabels[category] == "" {
			write(w, r, 400, map[string]any{"detail": "Categorie necunoscută."})
			return
		}
		if starter != nil && starter.Cmp(big.NewInt(0)) != 0 && starter.Cmp(big.NewInt(1)) != 0 {
			write(w, r, 400, map[string]any{"detail": "starter trebuie să fie 0 sau 1."})
			return
		}
		body, err = s.game.Create(seed, last(q, "daily"), category, last(q, "previous_game_id"), starter != nil && starter.Sign() != 0)
	} else {
		if !strings.HasPrefix(r.URL.Path, prefix+"/") {
			write(w, r, 404, map[string]any{"detail": "Not Found"})
			return
		}
		parts := strings.Split(strings.TrimPrefix(r.URL.Path, prefix+"/"), "/")
		if len(parts) == 0 || parts[0] == "" || len(parts) > 2 || (len(parts) == 2 && parts[1] != "guess" && parts[1] != "hint") {
			write(w, r, 404, map[string]any{"detail": "Not Found"})
			return
		}
		if len(parts) == 1 {
			if r.Method != "GET" && r.Method != "HEAD" {
				write(w, r, 405, map[string]any{"detail": "Method Not Allowed"})
				return
			}
			body, err = s.game.Get(parts[0])
		} else {
			if r.Method != "POST" {
				write(w, r, 405, map[string]any{"detail": "Method Not Allowed"})
				return
			}
			if parts[1] == "hint" {
				body, err = s.game.Hint(parts[0])
			} else {
				body, err = s.game.GuessInput(parts[0], func() (string, *intrusul.Error) {
					id, failure, status := guessID(r)
					if failure != nil {
						return "", &intrusul.Error{Status: status, Detail: failure["detail"]}
					}
					return id, nil
				})
			}
		}
	}
	if err != nil {
		write(w, r, err.Status, map[string]any{"detail": err.Detail})
		return
	}
	write(w, r, 200, body)
}

func (s *Server) standalone(w http.ResponseWriter, r *http.Request) {
	write(w, r, 404, map[string]any{"detail": "Not Found"})
}

func last(q url.Values, key string) string {
	values := q[key]
	if len(values) == 0 {
		return ""
	}
	return values[len(values)-1]
}

// Django treats semicolons as data and preserves malformed percent escapes.
func queryValues(raw string) url.Values {
	values := make(url.Values)
	for _, part := range strings.Split(raw, "&") {
		if part == "" {
			continue
		}
		key, value, _ := strings.Cut(part, "=")
		decode := func(s string) string {
			var b strings.Builder
			for i := 0; i < len(s); i++ {
				if s[i] == '+' {
					b.WriteByte(' ')
					continue
				}
				if s[i] == '%' && i+2 < len(s) {
					if decoded, err := url.QueryUnescape(s[i : i+3]); err == nil {
						b.WriteString(decoded)
						i += 2
						continue
					}
				}
				b.WriteByte(s[i])
			}
			return pythonUTF8(b.String())
		}
		values.Add(decode(key), decode(value))
	}
	return values
}

// Python's UTF-8 replacement decoder consumes a valid truncated prefix as one
// error, while preserving separate errors for independently invalid bytes.
func pythonUTF8(s string) string {
	var b strings.Builder
	for len(s) > 0 {
		r, n := utf8.DecodeRuneInString(s)
		if r != utf8.RuneError || n > 1 {
			b.WriteString(s[:n])
			s = s[n:]
			continue
		}
		need := 1
		switch {
		case s[0] >= 0xc2 && s[0] <= 0xdf:
			need = 2
		case s[0] >= 0xe0 && s[0] <= 0xef:
			need = 3
		case s[0] >= 0xf0 && s[0] <= 0xf4:
			need = 4
		}
		consumed := 1
		for consumed < need && consumed < len(s) {
			c := s[consumed]
			if c < 0x80 || c > 0xbf {
				break
			}
			if consumed == 1 && ((s[0] == 0xe0 && c < 0xa0) || (s[0] == 0xed && c > 0x9f) || (s[0] == 0xf0 && c < 0x90) || (s[0] == 0xf4 && c > 0x8f)) {
				break
			}
			consumed++
		}
		b.WriteRune(utf8.RuneError)
		s = s[consumed:]
	}
	return b.String()
}

func pySpace(r rune) bool { return unicode.IsSpace(r) || r >= 0x1c && r <= 0x1f }

func decimal(r rune) (int, bool) {
	return decimalValue(r)
}

func queryInt(q url.Values, key string) (*big.Int, map[string]any) {
	if !q.Has(key) {
		return nil, nil
	}
	raw := last(q, key)
	fail := func() (*big.Int, map[string]any) {
		return nil, map[string]any{"detail": []map[string]any{{"type": "int_parsing", "loc": []string{"query", key}, "msg": "Input should be a valid integer, unable to parse string as an integer", "input": raw}}}
	}
	text := []rune(strings.TrimFunc(raw, unicode.IsSpace))
	var b strings.Builder
	count := 0
	for i, r := range text {
		if i == 0 && (r == '+' || r == '-') {
			b.WriteRune(r)
			continue
		}
		if r == '_' {
			if i == 0 || i+1 == len(text) {
				return fail()
			}
			if _, ok := decimal(text[i-1]); !ok {
				return fail()
			}
			if _, ok := decimal(text[i+1]); !ok {
				return fail()
			}
			continue
		}
		n, ok := decimal(r)
		if !ok {
			return fail()
		}
		b.WriteByte(byte('0' + n))
		count++
	}
	if count == 0 || count > 4300 {
		return fail()
	}
	n, ok := new(big.Int).SetString(b.String(), 10)
	if !ok {
		return fail()
	}
	return n, nil
}

func guessID(r *http.Request) (string, map[string]any, int) {
	raw, err := io.ReadAll(io.LimitReader(r.Body, MaxRequestBytes+1))
	if err != nil {
		return "", map[string]any{"detail": "Request body unreadable"}, 400
	}
	if len(raw) > MaxRequestBytes {
		return "", map[string]any{"detail": "Request body too large"}, 413
	}
	var value any
	if len(bytes.TrimSpace(raw)) > 0 {
		d := json.NewDecoder(bytes.NewReader(raw))
		d.UseNumber()
		err = d.Decode(&value)
		if err == nil {
			var trailing any
			if d.Decode(&trailing) != io.EOF {
				err = extraData{}
			}
		}
		if err != nil {
			return "", map[string]any{"detail": []map[string]any{{"type": "json_invalid", "loc": []string{"body"}, "msg": "JSON decode error", "input": map[string]any{}, "ctx": map[string]string{"error": jsonMessage(raw, err)}}}}, 422
		}
	}
	obj, ok := value.(map[string]any)
	if !ok {
		return "", map[string]any{"detail": []map[string]any{{"type": "model_type", "loc": []string{"body"}, "msg": "Input should be a valid dictionary or instance of GuessBody", "input": value, "ctx": map[string]string{"class_name": "GuessBody"}}}}, 422
	}
	id, present := obj["id"]
	if !present {
		return "", map[string]any{"detail": []map[string]any{{"type": "missing", "loc": []string{"body", "id"}, "msg": "Field required", "input": obj}}}, 422
	}
	str, ok := id.(string)
	if !ok {
		return "", map[string]any{"detail": []map[string]any{{"type": "string_type", "loc": []string{"body", "id"}, "msg": "Input should be a valid string", "input": id}}}, 422
	}
	return strings.TrimFunc(str, pySpace), nil, 200
}

type extraData struct{}

func (extraData) Error() string { return "Extra data" }

func jsonMessage(raw []byte, err error) string {
	msg := err.Error()
	if _, ok := err.(extraData); ok {
		return "Extra data"
	}
	if strings.Contains(msg, "beginning of object key string") {
		return "Expecting property name enclosed in double quotes"
	}
	if strings.Contains(msg, "after object key:value pair") || strings.Contains(msg, "after array element") {
		return "Expecting ',' delimiter"
	}
	if strings.Contains(msg, "after object key") {
		return "Expecting ':' delimiter"
	}
	if strings.Contains(msg, "hexadecimal") || strings.Contains(msg, "Unicode escape") {
		return "Invalid \\uXXXX escape"
	}
	if strings.Contains(msg, "escape") {
		return "Invalid \\escape"
	}
	if strings.Contains(msg, "in string literal") {
		return "Invalid control character at"
	}
	if strings.Contains(msg, "unexpected EOF") || strings.Contains(msg, "unexpected end") || err == io.EOF {
		quoted, escape, lastWasKey := false, false, false
		var stack []byte
		var previous byte
		for _, c := range raw {
			if escape {
				escape = false
				continue
			}
			if quoted && c == '\\' {
				escape = true
				continue
			}
			if c == '"' {
				if !quoted {
					lastWasKey = len(stack) > 0 && stack[len(stack)-1] == '{' && (previous == '{' || previous == ',')
				}
				quoted = !quoted
				if !quoted {
					previous = '"'
				}
				continue
			}
			if !quoted {
				if c == '{' || c == '[' {
					stack = append(stack, c)
				}
				if (c == '}' || c == ']') && len(stack) > 0 {
					stack = stack[:len(stack)-1]
				}
				if c != ' ' && c != '\n' && c != '\r' && c != '\t' {
					previous = c
				}
			}
		}
		if quoted {
			return "Unterminated string starting at"
		}
		trim := bytes.TrimSpace(raw)
		if len(trim) > 0 {
			switch trim[len(trim)-1] {
			case '{':
				return "Expecting property name enclosed in double quotes"
			case ',':
				if len(stack) > 0 && stack[len(stack)-1] == '[' {
					return "Expecting value"
				}
				return "Expecting property name enclosed in double quotes"
			case ':', '[':
				return "Expecting value"
			case '"':
				if lastWasKey {
					return "Expecting ':' delimiter"
				}
				return "Expecting ',' delimiter"
			default:
				return "Expecting ',' delimiter"
			}
		}
	}
	return "Expecting value"
}
