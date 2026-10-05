// Package apppack decodes the tagged, public RO-EDU app-pack INPUT contract.
// It does not fetch a product, activate data, publish a bundle or generate the
// separate public mobile output projection.
package apppack

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"os"
	"strings"
	"unicode/utf8"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/roeduclient"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
)

const App = "cat_de_roman_esti"
const Layer = "redistributable"
const SchemaVersion = 1
const MaxFileBytes = 16 << 20
const MaxPacks = 512

var products = []string{"kg_nodes", "kg_edges", "kg_puzzles"}
var packProducts = map[string]string{
	"roedu:cat_de_roman_esti:kg_nodes:v1":   "kg_nodes",
	"roedu:cat_de_roman_esti:kg_edges:v1":   "kg_edges",
	"roedu:cat_de_roman_esti:kg_puzzles:v1": "kg_puzzles",
}
var kindProducts = map[string]string{"kg_node": "kg_nodes", "kg_edge": "kg_edges", "kg_puzzle": "kg_puzzles"}

// Limits cap all scanned rows, including withheld rows, as well as accepted
// per-product records. Callers can lower the fixed offline contract ceilings.
type Limits struct {
	Bytes                        int64
	Packs, Nodes, Edges, Puzzles int
}

func DefaultLimits() Limits { return Limits{MaxFileBytes, MaxPacks, 10000, 50000, 5000} }
func (l Limits) validate() error {
	if l.Bytes < 1 || l.Bytes > MaxFileBytes || l.Packs < 1 || l.Packs > MaxPacks || l.Nodes < 1 || l.Nodes > 10000 || l.Edges < 1 || l.Edges > 50000 || l.Puzzles < 1 || l.Puzzles > 5000 {
		return errors.New("invalid app-pack input bounds")
	}
	return nil
}
func (l Limits) cap(product string) int {
	switch product {
	case "kg_nodes":
		return l.Nodes
	case "kg_edges":
		return l.Edges
	case "kg_puzzles":
		return l.Puzzles
	}
	return 0
}
func object(v any) roeduclient.Record { r, _ := v.(map[string]any); return r }
func text(v any) string               { s, _ := v.(string); return s }
func list(v any) ([]any, bool) {
	switch a := v.(type) {
	case []any:
		return a, true
	case []roeduclient.Record:
		out := make([]any, len(a))
		for i, v := range a {
			out[i] = v
		}
		return out, true
	}
	return nil, false
}
func schemaOne(v any) bool {
	switch n := v.(type) {
	case json.Number:
		f, e := n.Float64()
		return e == nil && f == 1
	case int:
		return n == 1
	case int64:
		return n == 1
	case float64:
		return n == 1
	}
	return false
}

// Python 3.12 strip() whitespace is fixed here rather than inherited from a
// future Go Unicode table. In particular U+001C..U+001F are whitespace too.
func pySpace(c rune) bool {
	return c == 0x20 || c >= 0x9 && c <= 0xd || c >= 0x1c && c <= 0x1f || c == 0x85 || c == 0xa0 || c == 0x1680 || c >= 0x2000 && c <= 0x200a || c == 0x2028 || c == 0x2029 || c == 0x202f || c == 0x205f || c == 0x3000
}
func publicLegal(r roeduclient.Record) bool {
	access, basis := text(r["access_type"]), text(r["legal_basis"])
	return r["redistributable"] == true && r["gdpr_relevant"] == false && strings.TrimFunc(basis, pySpace) != "" && (access == "public_document" || access == "open_license" || access == "public_domain")
}

// RecordsFromAppPacks withholds unsupported packs/items and returns detached
// public records in the original encounter order. Withholding is a valid empty
// result; malformed JSON or exceeded resource bounds is an error.
func RecordsFromAppPacks(raw roeduclient.Record) (map[string][]roeduclient.Record, error) {
	return recordsWithLimits(raw, DefaultLimits())
}
func recordsWithLimits(raw roeduclient.Record, limits Limits) (map[string][]roeduclient.Record, error) {
	if err := limits.validate(); err != nil {
		return nil, err
	}
	out := map[string][]roeduclient.Record{}
	for _, p := range products {
		out[p] = []roeduclient.Record{}
	}
	var selected any = raw
	if packs, exists := raw["packs"]; exists {
		selected = packs
	}
	packs, ok := list(selected)
	if !ok {
		packs = []any{selected}
	}
	if len(packs) > limits.Packs {
		return nil, errors.New("app-pack pack cap exceeded")
	}
	scanned := 0
	totalCap := limits.Nodes + limits.Edges + limits.Puzzles
	for _, v := range packs {
		pack := object(v)
		if pack == nil {
			continue
		}
		items, _ := list(pack["items"])
		if len(items) > totalCap-scanned {
			return nil, errors.New("app-pack scanned record cap exceeded")
		}
		scanned += len(items)
		product := packProducts[text(pack["pack_id"])]
		if text(pack["app"]) != App || text(pack["layer"]) != Layer || !schemaOne(pack["schema_version"]) || product == "" {
			continue
		}
		for _, v := range items {
			item := object(v)
			if item == nil || kindProducts[text(item["kind"])] != product || !publicLegal(item) {
				continue
			}
			if len(out[product]) >= limits.cap(product) {
				return nil, fmt.Errorf("app-pack %s record cap exceeded", product)
			}
			copied, err := clone(item, 0)
			if err != nil {
				return nil, err
			}
			record := object(copied)
			if provenance := object(record["provenance"]); provenance != nil {
				for _, key := range []string{"source_url", "sha256", "internal_path", "llms_txt"} {
					delete(provenance, key)
				}
			}
			out[product] = append(out[product], record)
		}
	}
	return out, nil
}
func clone(v any, depth int) (any, error) {
	if depth > 64 {
		return nil, errors.New("app-pack record nesting cap exceeded")
	}
	switch x := v.(type) {
	case nil, bool, int, int64, uint64:
		return x, nil
	case json.Number:
		f, e := x.Float64()
		if e != nil || math.IsNaN(f) || math.IsInf(f, 0) {
			return nil, errors.New("app-pack non-finite number")
		}
		return x, nil
	case float64:
		if math.IsNaN(x) || math.IsInf(x, 0) {
			return nil, errors.New("app-pack non-finite number")
		}
		return x, nil
	case string:
		if !utf8.ValidString(x) {
			return nil, errors.New("app-pack invalid UTF-8 record")
		}
		return x, nil
	case map[string]any:
		out := map[string]any{}
		for k, v := range x {
			if !utf8.ValidString(k) {
				return nil, errors.New("app-pack invalid UTF-8 record key")
			}
			copy, e := clone(v, depth+1)
			if e != nil {
				return nil, e
			}
			out[k] = copy
		}
		return out, nil
	case []string:
		return append([]string{}, x...), nil
	case []any:
		out := make([]any, len(x))
		for i, v := range x {
			copy, e := clone(v, depth+1)
			if e != nil {
				return nil, e
			}
			out[i] = copy
		}
		return out, nil
	case []roeduclient.Record:
		out := make([]any, len(x))
		for i, v := range x {
			copy, e := clone(v, depth+1)
			if e != nil {
				return nil, e
			}
			out[i] = copy
		}
		return out, nil
	}
	return nil, errors.New("app-pack record contains a non-JSON value")
}

// DecodeBundle accepts either {"packs":[...]} or a single pack object. It preserves
// every admitted item field and strips only the documented unsafe provenance keys.
func DecodeBundle(raw []byte) (roeduclient.Bundle, error) {
	return DecodeBundleWithLimits(raw, DefaultLimits())
}
func DecodeBundleWithLimits(raw []byte, limits Limits) (roeduclient.Bundle, error) {
	if e := limits.validate(); e != nil {
		return roeduclient.Bundle{}, e
	}
	if int64(len(raw)) > limits.Bytes {
		return roeduclient.Bundle{}, errors.New("app-pack file byte cap exceeded")
	}
	if e := strictjson.Validate(raw); e != nil {
		return roeduclient.Bundle{}, fmt.Errorf("app-pack invalid private JSON: %w", e)
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	var input roeduclient.Record
	if e := decoder.Decode(&input); e != nil || input == nil {
		return roeduclient.Bundle{}, errors.New("app-pack root must be an object")
	}
	records, e := recordsWithLimits(input, limits)
	if e != nil {
		return roeduclient.Bundle{}, e
	}
	nodes, edges, puzzles := records["kg_nodes"], records["kg_edges"], records["kg_puzzles"]
	meta := roeduclient.Record{"build_version": "roedu-app-pack-v1", "source_format": "roedu_app_pack_v1", "app": App, "layer": Layer, "schema_version": SchemaVersion, "counts": roeduclient.Record{"nodes": len(nodes), "edges": len(edges), "puzzles": len(puzzles)}}
	return roeduclient.Bundle{Meta: meta, Nodes: nodes, Edges: edges, Puzzles: puzzles}, nil
}

// ReadFixture reads one bounded regular input file without modifying it or
// querying a producer. No output/mobile projection is installed by this decoder.
func ReadFixture(path string) (roeduclient.Bundle, error) {
	return ReadFixtureWithLimits(path, DefaultLimits())
}
func ReadFixtureWithLimits(path string, limits Limits) (roeduclient.Bundle, error) {
	if e := limits.validate(); e != nil {
		return roeduclient.Bundle{}, e
	}
	file, e := os.Open(path)
	if e != nil {
		return roeduclient.Bundle{}, e
	}
	defer file.Close()
	info, e := file.Stat()
	if e != nil {
		return roeduclient.Bundle{}, e
	}
	if !info.Mode().IsRegular() || info.Size() > limits.Bytes {
		return roeduclient.Bundle{}, errors.New("app-pack fixture not regular or exceeds byte cap")
	}
	raw, e := io.ReadAll(io.LimitReader(file, limits.Bytes+1))
	if e != nil {
		return roeduclient.Bundle{}, e
	}
	return DecodeBundleWithLimits(raw, limits)
}
