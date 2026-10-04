// Package contentbuild builds private serving content from reviewed source records.
// It does not import the embedded serving bundle and does not require Python.
package contentbuild

import (
	"bytes"
	"crypto/sha256"
	_ "embed"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"os"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"sync"
	"unicode/utf8"
)

//go:embed rules_unicode15.json
var rulesBytes []byte

//go:embed rules_provenance.json
var provenanceBytes []byte

const rulesSHA256 = "cd579dc1d8e583e595f454b0d6ac50ec7afaaf72d9fb3725efbc6e5936fe9558"

var rulesOnce sync.Once
var rules map[string]any
var rulesError error

func frozenRules() (map[string]any, error) {
	rulesOnce.Do(func() {
		if SHA256(rulesBytes) != rulesSHA256 {
			rulesError = fmt.Errorf("frozen Unicode 15 rules digest drift")
			return
		}
		var p map[string]any
		if rulesError = json.Unmarshal(provenanceBytes, &p); rulesError != nil {
			return
		}
		if p["rules_sha256"] != rulesSHA256 || p["unicode_version"] != "15.0.0" {
			rulesError = fmt.Errorf("frozen rules provenance drift")
			return
		}
		rules, rulesError = decodeObject(rulesBytes)
	})
	return rules, rulesError
}
func decodeObject(b []byte) (map[string]any, error) {
	if !utf8.Valid(b) {
		return nil, fmt.Errorf("source is not valid UTF-8")
	}
	d := json.NewDecoder(bytes.NewReader(b))
	d.UseNumber()
	var v map[string]any
	if err := d.Decode(&v); err != nil {
		return nil, err
	}
	if v == nil {
		return nil, fmt.Errorf("JSON object required")
	}
	var tail any
	if d.Decode(&tail) != io.EOF {
		return nil, fmt.Errorf("trailing JSON")
	}
	return v, nil
}
func ReadObject(path string, max int64) (map[string]any, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > max {
		return nil, fmt.Errorf("source exceeds %d byte bound or is not a regular file", max)
	}
	b, err := io.ReadAll(io.LimitReader(f, max+1))
	if err != nil {
		return nil, err
	}
	if int64(len(b)) > max {
		return nil, fmt.Errorf("source exceeds byte bound")
	}
	return decodeObject(b)
}
func SHA256(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func TextSHA256(b []byte) string {
	return SHA256(bytes.ReplaceAll(bytes.ReplaceAll(b, []byte("\r\n"), []byte("\n")), []byte("\r"), []byte("\n")))
}

// Canonical matches the former Python compact, UTF-8, sorted-key encoding.
// Number lexemes from source JSON remain intact; typed float values keep their .0.
func Canonical(v any) ([]byte, error) {
	var b bytes.Buffer
	err := writeJSON(&b, v)
	return b.Bytes(), err
}
func writeJSON(b *bytes.Buffer, v any) error {
	switch t := v.(type) {
	case nil:
		b.WriteString("null")
	case string:
		var s bytes.Buffer
		e := json.NewEncoder(&s)
		e.SetEscapeHTML(false)
		if err := e.Encode(t); err != nil {
			return err
		}
		x := bytes.TrimSuffix(s.Bytes(), []byte("\n"))
		x = unescapeSeparators(x)
		b.Write(x)
	case bool:
		if t {
			b.WriteString("true")
		} else {
			b.WriteString("false")
		}
	case json.Number:
		if !json.Valid([]byte(string(t))) {
			return fmt.Errorf("invalid JSON number")
		}
		if strings.ContainsAny(string(t), ".eE") {
			n, e := t.Float64()
			if e != nil {
				return e
			}
			return writeJSON(b, n)
		}
		if _, e := strconv.ParseInt(string(t), 10, 64); e != nil {
			return e
		}
		b.WriteString(string(t))
	case float64:
		if math.IsNaN(t) || math.IsInf(t, 0) {
			return fmt.Errorf("non-finite JSON number")
		}
		format := byte('g')
		if t == 0 || math.Abs(t) >= 1e-4 && math.Abs(t) < 1e16 {
			format = 'f'
		}
		s := strconv.FormatFloat(t, format, -1, 64)
		if !strings.ContainsAny(s, ".eE") {
			s += ".0"
		}
		b.WriteString(s)
	case float32:
		return writeJSON(b, float64(t))
	case int:
		b.WriteString(strconv.Itoa(t))
	case int64:
		b.WriteString(strconv.FormatInt(t, 10))
	case uint32:
		b.WriteString(strconv.FormatUint(uint64(t), 10))
	case map[string]any:
		keys := make([]string, 0, len(t))
		for k := range t {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		b.WriteByte('{')
		for i, k := range keys {
			if i > 0 {
				b.WriteByte(',')
			}
			if err := writeJSON(b, k); err != nil {
				return err
			}
			b.WriteByte(':')
			if err := writeJSON(b, t[k]); err != nil {
				return err
			}
		}
		b.WriteByte('}')
	default:
		rv := reflect.ValueOf(v)
		if rv.Kind() == reflect.Slice || rv.Kind() == reflect.Array {
			b.WriteByte('[')
			for i := 0; i < rv.Len(); i++ {
				if i > 0 {
					b.WriteByte(',')
				}
				if err := writeJSON(b, rv.Index(i).Interface()); err != nil {
					return err
				}
			}
			b.WriteByte(']')
			return nil
		}
		blob, err := json.Marshal(v)
		if err != nil {
			return err
		}
		var x any
		d := json.NewDecoder(bytes.NewReader(blob))
		d.UseNumber()
		if err := d.Decode(&x); err != nil {
			return err
		}
		return writeJSON(b, x)
	}
	return nil
}
func object(v any) map[string]any { r, _ := v.(map[string]any); return r }
func array(v any) []any           { r, _ := v.([]any); return r }
func str(v any) string            { r, _ := v.(string); return r }
func integer(v any) (int, bool) {
	n, ok := v.(json.Number)
	if ok {
		i, e := strconv.Atoi(string(n))
		return i, e == nil
	}
	i, ok := v.(int)
	return i, ok
}
func number(v any) float64 {
	switch n := v.(type) {
	case json.Number:
		x, _ := n.Float64()
		return x
	case float64:
		return n
	case int:
		return float64(n)
	}
	return 0
}
func stringsOf(v any) []string {
	if ss, ok := v.([]string); ok {
		return append([]string{}, ss...)
	}
	r := []string{}
	for _, a := range array(v) {
		r = append(r, str(a))
	}
	return r
}
func valueDigest(v any) string {
	b, err := Canonical(v)
	if err != nil {
		return ""
	}
	return SHA256(b)
}
func equal(a, b any) bool {
	aa, e := Canonical(a)
	bb, f := Canonical(b)
	return e == nil && f == nil && bytes.Equal(aa, bb)
}
func copyObject(m map[string]any) map[string]any {
	n := map[string]any{}
	for k, v := range m {
		n[k] = v
	}
	return n
}
func exact(m map[string]any, keys ...string) bool {
	if len(m) != len(keys) {
		return false
	}
	for _, k := range keys {
		if _, ok := m[k]; !ok {
			return false
		}
	}
	return true
}
func pySpace(c rune) bool {
	return c == 0x20 || c >= 0x9 && c <= 0xd || c >= 0x1c && c <= 0x1f || c == 0x85 || c == 0xa0 || c == 0x1680 || c >= 0x2000 && c <= 0x200a || c == 0x2028 || c == 0x2029 || c == 0x202f || c == 0x205f || c == 0x3000
}

// Normalize uses the frozen Unicode 15 NFKD/combining-removal/casefold mapping.
func Normalize(s string) string {
	r, e := frozenRules()
	if e != nil {
		panic(e)
	}
	m := object(r["normalization_map"])
	var b strings.Builder
	for _, c := range s {
		v, ok := m[string(c)]
		if ok {
			b.WriteString(str(v))
		} else {
			b.WriteRune(c)
		}
	}
	return strings.Join(strings.FieldsFunc(b.String(), pySpace), " ")
}
func upper(s string, r map[string]any) string {
	if v, ok := object(r["uppercase_map"])[s]; ok {
		return str(v)
	}
	return s
}
func letter(c rune, r map[string]any) bool {
	for _, v := range array(r["letter_ranges"]) {
		p := array(v)
		if float64(c) >= number(p[0]) && float64(c) <= number(p[1]) {
			return true
		}
	}
	return false
}
func labelPattern(s string, r map[string]any) string {
	var b strings.Builder
	start := true
	for _, c := range s {
		if letter(c, r) {
			if start {
				b.WriteString(upper(string(c), r))
				start = false
			} else {
				b.WriteByte('_')
			}
		} else {
			b.WriteRune(c)
			start = pySpace(c)
		}
	}
	return b.String()
}

func boolValue(v any) bool {
	switch t := v.(type) {
	case bool:
		return t
	case json.Number:
		return number(t) != 0
	case int:
		return t != 0
	case float64:
		return t != 0
	case string:
		return contains([]string{"1", "true", "yes", "t"}, strings.ToLower(strings.TrimSpace(t)))
	}
	return v != nil
}
func errorSummary(errors []string) string {
	n := len(errors)
	if n > 10 {
		errors = errors[:10]
	}
	return fmt.Sprintf("%d errors: %s", n, strings.Join(errors, "; "))
}

func indentedDigest(v any) string {
	compact, err := Canonical(v)
	if err != nil {
		return ""
	}
	var b bytes.Buffer
	if json.Indent(&b, compact, "", "  ") != nil {
		return ""
	}
	b.WriteByte('\n')
	return SHA256(b.Bytes())
}

// Decode only actual JSON separator escapes; a quoted literal backslash-u
// sequence must retain its identity in portable source/dossier hashes.
func unescapeSeparators(encoded []byte) []byte {
	out := make([]byte, 0, len(encoded))
	for i := 0; i < len(encoded); {
		if encoded[i] == '\\' && i+1 < len(encoded) {
			if encoded[i+1] == '\\' {
				out = append(out, encoded[i:i+2]...)
				i += 2
				continue
			}
			if i+6 <= len(encoded) && encoded[i+1] == 'u' {
				switch string(encoded[i+2 : i+6]) {
				case "2028":
					out = append(out, []byte("\u2028")...)
					i += 6
					continue
				case "2029":
					out = append(out, []byte("\u2029")...)
					i += 6
					continue
				}
			}
			out = append(out, encoded[i:i+2]...)
			i += 2
			continue
		}
		out = append(out, encoded[i])
		i++
	}
	return out
}
