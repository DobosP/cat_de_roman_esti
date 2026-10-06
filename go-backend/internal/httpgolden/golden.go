package httpgolden

import (
	"bytes"
	"compress/gzip"
	"context"
	"crypto/sha256"
	_ "embed"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
	"io"
	"reflect"
	"sort"
	"strings"
	"time"
)

//go:embed testdata/python-http-parity.json.gz
var frozen []byte

//go:embed testdata/python-http-parity-v1-2.json.gz
var frozenV12 []byte

//go:embed testdata/python-http-parity-v1-3.json.gz
var frozenV13 []byte

//go:embed testdata/python-http-parity-v1-4.json.gz
var frozenV14 []byte

//go:embed testdata/python-http-parity-v1-5.json.gz
var frozenV15 []byte

const FrozenSHA256 = "9041e05f13190a06a526c1aeed1f264d467483cd267ffcdb24f422ed9430b2cb"
const V12SHA256 = "6293a0dde67ee0b0e5929cc1103bd80795e0aff1af2ba5fdf53e983ab79351fd"
const V13SHA256 = "67d009c7eaa710bd98281b3300d3df4dc4ed4e224a157934abd7e19bce112670"
const V14SHA256 = "9d49bd38bbc20c7ebf3a834cada064bf7e4b48018e53890075106dc8f844cb1a"
const V15SHA256 = "22995196184b991996b56dccf50e5032f27814d7403fff411a120fa11c76a519"
const MaxCorpusBytes = 32 * 1024 * 1024
const MaxCases = 4096

type Case struct {
	Request Request `json:"request"`
	Status  int     `json:"status"`
	Body    any     `json:"body"`
}
type Corpus struct {
	SchemaVersion int               `json:"schema_version"`
	Reference     string            `json:"reference"`
	Sources       map[string]string `json:"sources"`
	Cases         []Case            `json:"cases"`
}
type Report struct {
	OK                 bool              `json:"ok"`
	Mode               string            `json:"mode"`
	Requests           int               `json:"requests"`
	Reference          string            `json:"reference,omitempty"`
	ElapsedSeconds     float64           `json:"elapsed_seconds"`
	ContentHash        string            `json:"content_hash,omitempty"`
	GamesCompleted     int               `json:"games_completed,omitempty"`
	ExplorationRestore bool              `json:"exploration_restore,omitempty"`
	AssetsVerified     int               `json:"assets_verified,omitempty"`
	LegalSHA256        map[string]string `json:"legal_sha256,omitempty"`
	AccountsEnabled    bool              `json:"accounts_enabled"`
}

func ReadCorpus(r io.Reader, compressed bool) (*Corpus, error) {
	if compressed {
		z, err := gzip.NewReader(r)
		if err != nil {
			return nil, err
		}
		defer z.Close()
		r = z
	}
	raw, err := io.ReadAll(io.LimitReader(r, MaxCorpusBytes+1))
	if err != nil {
		return nil, err
	}
	if len(raw) > MaxCorpusBytes {
		return nil, fmt.Errorf("corpus byte budget exceeded")
	}
	if err = strictjson.Validate(raw); err != nil {
		return nil, err
	}
	var c Corpus
	d := json.NewDecoder(bytes.NewReader(raw))
	d.UseNumber()
	d.DisallowUnknownFields()
	if err = d.Decode(&c); err != nil {
		return nil, err
	}
	var extra any
	if d.Decode(&extra) != io.EOF {
		return nil, fmt.Errorf("trailing corpus JSON")
	}
	if c.SchemaVersion != 1 || c.Reference == "" || len(c.Cases) < 1 || len(c.Cases) > MaxCases || len(c.Sources) < 8 {
		return nil, fmt.Errorf("incomplete source-bound corpus")
	}
	return &c, nil
}
func Frozen() (*Corpus, error) {
	if fmt.Sprintf("%x", sha256.Sum256(frozen)) != FrozenSHA256 {
		return nil, fmt.Errorf("independent HTTP corpus digest drift")
	}
	c, err := ReadCorpus(bytes.NewReader(frozen), true)
	if err == nil && len(c.Cases) != 1207 {
		return nil, fmt.Errorf("expected 1207 independent HTTP cases")
	}
	return c, err
}

func reviewedV12() (*Corpus, error) {
	if fmt.Sprintf("%x", sha256.Sum256(frozenV12)) != V12SHA256 {
		return nil, fmt.Errorf("independent V1.2 HTTP corpus digest drift")
	}
	c, err := ReadCorpus(bytes.NewReader(frozenV12), true)
	if err == nil && len(c.Cases) != 1207 {
		return nil, fmt.Errorf("expected 1207 independent V1.2 HTTP cases")
	}
	return c, err
}

func reviewedV13() (*Corpus, error) {
	if fmt.Sprintf("%x", sha256.Sum256(frozenV13)) != V13SHA256 {
		return nil, fmt.Errorf("independent V1.3 HTTP corpus digest drift")
	}
	c, err := ReadCorpus(bytes.NewReader(frozenV13), true)
	if err == nil && len(c.Cases) != 1207 {
		return nil, fmt.Errorf("expected 1207 independent V1.3 HTTP cases")
	}
	return c, err
}

func reviewedV14() (*Corpus, error) {
	if fmt.Sprintf("%x", sha256.Sum256(frozenV14)) != V14SHA256 {
		return nil, fmt.Errorf("independent V1.4 HTTP corpus digest drift")
	}
	c, err := ReadCorpus(bytes.NewReader(frozenV14), true)
	if err == nil && len(c.Cases) != 1207 {
		return nil, fmt.Errorf("expected 1207 independent V1.4 HTTP cases")
	}
	return c, err
}

func reviewedV15() (*Corpus, error) {
	if fmt.Sprintf("%x", sha256.Sum256(frozenV15)) != V15SHA256 {
		return nil, fmt.Errorf("independent V1.5 HTTP corpus digest drift")
	}
	c, err := ReadCorpus(bytes.NewReader(frozenV15), true)
	if err == nil && (len(c.Cases) != 1207 || len(c.Sources) != 8) {
		return nil, fmt.Errorf("expected 1207 independent V1.5 HTTP cases and exact eight sources")
	}
	return c, err
}

// ForSources selects an independently captured reviewed corpus only when its
// entire source identity equals the requested export. Historical Frozen remains
// immutable; unknown, partial or mixed source sets never gain expected responses.
func ForSources(sources map[string]string) (*Corpus, error) {
	original, err := Frozen()
	if err != nil {
		return nil, err
	}
	current, err := reviewedV12()
	if err != nil {
		return nil, err
	}
	latest, err := reviewedV13()
	if err != nil {
		return nil, err
	}
	v14, err := reviewedV14()
	if err != nil {
		return nil, err
	}
	v15, err := reviewedV15()
	if err != nil {
		return nil, err
	}
	for _, c := range []*Corpus{original, current, latest, v14, v15} {
		if reflect.DeepEqual(c.Sources, sources) {
			return c, nil
		}
	}
	return nil, fmt.Errorf("no independently reviewed HTTP corpus matches exact source digests")
}
func replace(text string, aliases map[string]string) string {
	keys := []string{}
	for k := range aliases {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool { return len(keys[i]) > len(keys[j]) })
	for _, k := range keys {
		v := aliases[k]
		text = strings.ReplaceAll(text, fmt.Sprintf("%%%02x", k[0])+k[1:], fmt.Sprintf("%%%02x", v[0])+v[1:])
		text = strings.ReplaceAll(text, k, v)
	}
	return text
}
func normalized(v any, aliases map[string]string) any {
	switch x := v.(type) {
	case string:
		return replace(x, aliases)
	case map[string]any:
		y := map[string]any{}
		for k, v := range x {
			y[k] = normalized(v, aliases)
		}
		return y
	case []any:
		y := make([]any, len(x))
		for i, v := range x {
			y[i] = normalized(v, aliases)
		}
		return y
	}
	return v
}
func Replay(ctx context.Context, client *Client, c *Corpus, data *content.Content) (Report, error) {
	start := time.Now()
	if !reflect.DeepEqual(c.Sources, data.Sources) {
		return Report{}, fmt.Errorf("reference source digest binding differs from current reviewed export")
	}
	aliases := map[string]string{}
	reverse := map[string]string{}
	for index, row := range c.Cases {
		request := row.Request
		request.Path = replace(request.Path, aliases)
		request.Body = replace(request.Body, aliases)
		got, err := client.Do(ctx, request)
		if err != nil {
			return Report{}, fmt.Errorf("case %d: %w", index, err)
		}
		if row.Status == 200 && got.Status == 200 {
			expected, eok := row.Body.(map[string]any)
			actual, aok := got.Body.(map[string]any)
			if eok && aok {
				eid, _ := expected["game_id"].(string)
				aid, _ := actual["game_id"].(string)
				if eid != "" && aid != "" {
					if old, ok := aliases[eid]; ok && old != aid {
						return Report{}, fmt.Errorf("case %d: session identity changed", index)
					}
					aliases[eid] = aid
					reverse[aid] = eid
				}
			}
		}
		if row.Status != got.Status || !reflect.DeepEqual(row.Body, normalized(got.Body, reverse)) {
			return Report{}, fmt.Errorf("independent HTTP reference mismatch at case %d (%s %s), expected status %d, got %d", index, request.Method, strings.Split(row.Request.Path, "?")[0], row.Status, got.Status)
		}
	}
	return Report{OK: true, Mode: "golden_replay", Requests: len(c.Cases), Reference: c.Reference, ElapsedSeconds: time.Since(start).Seconds(), ContentHash: data.Manifest["content_hash"].(string)}, nil
}
