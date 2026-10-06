package httpgolden

import (
	"bytes"
	"compress/gzip"
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func testData(t *testing.T) *content.Content {
	t.Helper()
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	return c
}
func TestCurrentIndependentHTTPParity(t *testing.T) {
	data := testData(t)
	c, err := ForSources(data.Sources)
	if err != nil {
		t.Fatal(err)
	}
	client, _ := NewClient(Local(httpapi.New(data)), MaxCases)
	report, err := Replay(context.Background(), client, c, data)
	if err != nil {
		t.Fatal(err)
	}
	if !report.OK || report.Requests != 1207 {
		t.Fatal("incomplete independent parity")
	}
}

func TestHistoricalFrozenCorpusAndExactReviewedSelection(t *testing.T) {
	original, err := Frozen()
	if err != nil {
		t.Fatal(err)
	}
	if FrozenSHA256 != "9041e05f13190a06a526c1aeed1f264d467483cd267ffcdb24f422ed9430b2cb" || len(original.Cases) != 1207 || len(original.Sources) != 8 || original.Reference != "Django application, scripts/check_go_parity.py at ae70c16935d402719b95405685bccbbbea13a3bd" {
		t.Fatal("historical independent corpus identity/count/source assurance changed")
	}
	selected, err := ForSources(original.Sources)
	if err != nil || !reflect.DeepEqual(selected, original) {
		t.Fatal("historical source set selected different expected responses", err)
	}
	current, err := reviewedV12()
	if err != nil {
		t.Fatal(err)
	}
	if len(current.Cases) != 1207 || len(current.Sources) != 8 || !strings.Contains(current.Reference, "Independent Django application; V1.2") || reflect.DeepEqual(current.Sources, original.Sources) {
		t.Fatal("current independent corpus lacks its own source/capture identity")
	}
	selected, err = ForSources(current.Sources)
	if err != nil || !reflect.DeepEqual(selected, current) {
		t.Fatal("V1.2 source set selected different expected responses", err)
	}
	latest, err := reviewedV13()
	if err != nil {
		t.Fatal(err)
	}
	if V13SHA256 != "67d009c7eaa710bd98281b3300d3df4dc4ed4e224a157934abd7e19bce112670" || len(latest.Cases) != 1207 || len(latest.Sources) != 8 || !strings.Contains(latest.Reference, "Independent Django application; V1.3") || reflect.DeepEqual(latest.Sources, current.Sources) || reflect.DeepEqual(latest.Sources, original.Sources) {
		t.Fatal("V1.3 independent corpus lacks its own exact source/capture identity")
	}
	selected, err = ForSources(latest.Sources)
	if err != nil || !reflect.DeepEqual(selected, latest) || !reflect.DeepEqual(latest.Sources, historicalV13Data(t).Sources) {
		t.Fatal("current V1.3 source set selected different expected responses", err)
	}
}

func TestUnknownMixedAndPartialSourcesRefuseWithoutRequests(t *testing.T) {
	data := testData(t)
	client, _ := NewClient(Local(httpapi.New(data)), MaxCases)
	for _, mutate := range []func(map[string]string){
		func(s map[string]string) { s["kg_sample.json"] = strings.Repeat("0", 64) },
		func(s map[string]string) { delete(s, "kg_sample.json") },
		func(s map[string]string) { s["extra-unreviewed-source.json"] = strings.Repeat("0", 64) },
		func(s map[string]string) {
			s["kg_sample.json"] = "1c74e5fe387b20ed196f76588d1ef96658743776817532c09a17ab9dd0a39b64"
		},
	} {
		sources := map[string]string{}
		for k, v := range data.Sources {
			sources[k] = v
		}
		mutate(sources)
		if _, err := ForSources(sources); err == nil || client.Count() != 0 {
			t.Fatal("unreviewed/mixed source set acquired expectations or made requests")
		}
	}
	original, err := Frozen()
	if err != nil {
		t.Fatal(err)
	}
	if _, err = Replay(context.Background(), client, original, data); err == nil || client.Count() != 0 {
		t.Fatal("historical corpus replay against changed content did not refuse before requests")
	}
}
func TestReferenceSourceBindingAndMismatchFailClosed(t *testing.T) {
	data := testData(t)
	c, err := ForSources(data.Sources)
	if err != nil {
		t.Fatal(err)
	}
	c.Sources["kg_sample.json"] = strings.Repeat("0", 64)
	client, _ := NewClient(Local(httpapi.New(data)), MaxCases)
	if _, err = Replay(context.Background(), client, c, data); err == nil || client.Count() != 0 {
		t.Fatal("source drift must refuse before requests")
	}
	c, err = ForSources(data.Sources)
	if err != nil {
		t.Fatal(err)
	}
	c.Cases[0].Status = 500
	if _, err = Replay(context.Background(), client, c, data); err == nil {
		t.Fatal("expected response mismatch accepted")
	}
}
func TestSessionAliasesKeepPrefixAndEscapedIdentityDistinct(t *testing.T) {
	aliases := map[string]string{"session-1": "a111", "session-10": "b222"}
	if got := replace("/session-10?previous_game_id=session-1", aliases); got != "/b222?previous_game_id=a111" {
		t.Fatal(got)
	}
	if got := replace("/%73ession-10", aliases); got != "/%62222" {
		t.Fatal(got)
	}
}
func TestBoundedAnonymousHTTPClient(t *testing.T) {
	for _, origin := range []string{"file:///x", "https://user:pass@example.com", "https://example.com/path", "https://example.com?token=x", "https://example.com#x", "//example.com"} {
		if _, err := HTTP(origin); err == nil {
			t.Fatalf("unsafe origin accepted: %s", origin)
		}
	}
	targetRequests := 0
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { targetRequests++; fmt.Fprint(w, "{}") }))
	defer target.Close()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/redirect":
			http.Redirect(w, r, target.URL, 302)
		case "/large":
			_, _ = w.Write(bytes.Repeat([]byte{'x'}, MaxResponse+1))
		default:
			fmt.Fprint(w, "{}")
		}
	}))
	defer server.Close()
	transport, err := HTTP(server.URL)
	if err != nil {
		t.Fatal(err)
	}
	client, _ := NewClient(transport, 3)
	defer client.Close()
	ctx := context.Background()
	if r, err := client.Do(ctx, Request{Method: "GET", Path: "/redirect"}); err != nil || r.Status != 302 || targetRequests != 0 {
		t.Fatal("redirect followed")
	}
	if _, err := client.Do(ctx, Request{Method: "GET", Path: "/large"}); err == nil {
		t.Fatal("oversized response accepted")
	}
	for _, r := range []Request{{Method: "GET", Path: "//example.com"}, {Method: "GET", Path: "/", Headers: map[string]string{"Authorization": "synthetic"}}, {Method: "GET", Path: "/", Headers: map[string]string{"Cookie": "synthetic"}}, {Method: "POST", Path: "/", Body: strings.Repeat("x", MaxRequest+1)}} {
		if _, err := client.Do(ctx, r); err == nil {
			t.Fatal("request bound bypassed")
		}
	}
	if _, err := client.Do(ctx, Request{Method: "GET", Path: "/"}); err != nil {
		t.Fatal(err)
	}
	if _, err := client.Do(ctx, Request{Method: "GET", Path: "/"}); err == nil {
		t.Fatal("request count bound bypassed")
	}
}
func TestCorpusLimitsTrailingFieldsAndMalformedRecords(t *testing.T) {
	for _, raw := range []string{"{}", "null", "[]", "{\"schema_version\":1,\"unknown\":true}", "{} {}"} {
		if _, err := ReadCorpus(strings.NewReader(raw), false); err == nil {
			t.Fatal("invalid corpus accepted")
		}
	}
	if _, err := ReadCorpus(bytes.NewReader([]byte("not gzip")), true); err == nil {
		t.Fatal("bad compression accepted")
	}
}
func TestCaptureCanReplayButDoesNotClaimIndependentReference(t *testing.T) {
	data := testData(t)
	client, _ := NewClient(Local(httpapi.New(data)), 600)
	c, err := Capture(context.Background(), client, data, "synthetic native test capture; not independent reference")
	if err != nil {
		t.Fatal(err)
	}
	raw, _ := json.Marshal(c)
	decoded, err := ReadCorpus(bytes.NewReader(raw), false)
	if err != nil {
		t.Fatal(err)
	}
	fresh, _ := NewClient(Local(httpapi.New(data)), 600)
	if _, err = Replay(context.Background(), fresh, decoded, data); err != nil {
		t.Fatal(err)
	}
	if _, err = Capture(context.Background(), client, data, ""); err == nil {
		t.Fatal("unnamed reference accepted")
	}
}
func TestBenchmarkBounds(t *testing.T) {
	data := testData(t)
	client, _ := NewClient(Local(httpapi.New(data)), MaxCalls)
	for _, cfg := range []BenchmarkConfig{{Flows: 901, Concurrency: 1, Workload: "creates"}, {Flows: 1, Warmup: 101, Concurrency: 1, Workload: "creates"}, {Flows: 1, Concurrency: 65, Workload: "creates"}} {
		if _, err := Benchmark(context.Background(), client, data, cfg); err == nil {
			t.Fatal("benchmark bound bypassed")
		}
	}
}

func TestLocalTransportByteAndDeadlineBounds(t *testing.T) {
	large := Local(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { _, _ = w.Write(bytes.Repeat([]byte{'x'}, MaxResponse+1)) }))
	client, _ := NewClient(large, 2)
	if _, err := client.Do(context.Background(), Request{Method: "GET", Path: "/"}); err == nil {
		t.Fatal("offline response cap bypass")
	}
	if _, err := client.Do(context.Background(), Request{Method: "GET", Path: "/\x00"}); err == nil {
		t.Fatal("invalid URI accepted")
	}
	slow := Local(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { <-r.Context().Done() }))
	bounded, _ := NewClient(slow, 1)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err := bounded.Do(ctx, Request{Method: "GET", Path: "/"}); err == nil {
		t.Fatal("cancelled offline request accepted")
	}
}

func historicalV13Data(t *testing.T) *content.Content {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join("../../..", "docs/reviews/v1-4-time-links-and-predicates/reference/historical-v1-3-bundled.json.gz"))
	if err != nil {
		t.Fatal(err)
	}
	z, err := gzip.NewReader(bytes.NewReader(raw))
	if err != nil {
		t.Fatal(err)
	}
	defer z.Close()
	b, err := io.ReadAll(io.LimitReader(z, (16<<20)+1))
	if err != nil || len(b) > 16<<20 || fmt.Sprintf("%x", sha256.Sum256(b)) != "b9189ef3befe94978dc2ddfc180f463a34556982178ee378f679cc83bc2cea6f" {
		t.Fatal("historical V1.3 exact bytes refused", err)
	}
	c, err := content.Decode(b)
	if err != nil {
		t.Fatal(err)
	}
	return c
}

func TestV14IndependentCorpusRetainsExactSourceScope(t *testing.T) {
	c, err := reviewedV14()
	if err != nil {
		t.Fatal(err)
	}
	if V14SHA256 != "9d49bd38bbc20c7ebf3a834cada064bf7e4b48018e53890075106dc8f844cb1a" || len(c.Cases) != 1207 || len(c.Sources) != 8 || !strings.Contains(c.Reference, "prospective V1.4 reviewed sources at baseline46641d6f9963f92941d12f5955e5eb40a2d8fb56") || !reflect.DeepEqual(c.Sources, historicalV14Data(t).Sources) {
		t.Fatal("V1.4 independent corpus source/capture identity drift")
	}
	selected, err := ForSources(c.Sources)
	if err != nil || !reflect.DeepEqual(selected, c) {
		t.Fatal("V1.4 selected different independent responses", err)
	}
	for _, read := range []func() (*Corpus, error){Frozen, reviewedV12, reviewedV13} {
		old, err := read()
		if err != nil || reflect.DeepEqual(old.Sources, c.Sources) {
			t.Fatal("V1.4 replaced historical source scope", err)
		}
	}
}

// The V1.4 source assertion above belongs to its exact frozen predecessor.
// Current HTTP replay uses testData and ForSources, selecting V1.5 independently.
func historicalV14Data(t *testing.T) *content.Content {
	t.Helper()
	f, err := os.Open(filepath.Join("..", "alchimie_explore", "testdata", "bundled-v1-4.json.gz"))
	if err != nil {
		t.Fatal(err)
	}
	compressed, err := io.ReadAll(io.LimitReader(f, (2<<20)+1))
	closeErr := f.Close()
	if err != nil || closeErr != nil || len(compressed) > 2<<20 || fmt.Sprintf("%x", sha256.Sum256(compressed)) != "76245d7d5fd3266981c92e3ad7a7e323395b8edd919a4208a56b01bf3bc5f5d3" {
		t.Fatal("historical V1.4 compressed archive refused", err)
	}
	z, err := gzip.NewReader(bytes.NewReader(compressed))
	if err != nil {
		t.Fatal(err)
	}
	b, err := io.ReadAll(io.LimitReader(z, (8<<20)+1))
	closeErr = z.Close()
	if err != nil || closeErr != nil || len(b) > 8<<20 || fmt.Sprintf("%x", sha256.Sum256(b)) != "d1d3f721525e06f247727d6998bd91a9e38bf26610bde9eba55406dabcfd54c2" {
		t.Fatal("historical V1.4 exact bytes refused", err)
	}
	c, err := content.Decode(b)
	if err != nil {
		t.Fatal(err)
	}
	return c
}

func TestV15IndependentCorpusRetainsExactWorldOnlySourceScope(t *testing.T) {
	c, err := reviewedV15()
	if err != nil {
		t.Fatal(err)
	}
	if V15SHA256 != "22995196184b991996b56dccf50e5032f27814d7403fff411a120fa11c76a519" || len(c.Cases) != 1207 || len(c.Sources) != 8 || !strings.Contains(c.Reference, "Independent Django application; V1.5 reviewed world-only sources") || !reflect.DeepEqual(c.Sources, testData(t).Sources) {
		t.Fatal("V1.5 independent corpus source/capture identity drift")
	}
	if c.Sources["alchimie_discovery_world_v92.json"] != "196e0b72310e6ec7b9b18254b4b95a307d9ae7a9ecb97f3670b66f24ff071086" {
		t.Fatal("V1.5 selected an unreviewed world source")
	}
	selected, err := ForSources(c.Sources)
	if err != nil || !reflect.DeepEqual(selected, c) {
		t.Fatal("V1.5 source set selected different independent responses", err)
	}
	v14, err := reviewedV14()
	if err != nil {
		t.Fatal(err)
	}
	for name, expected := range v14.Sources {
		if name != "alchimie_discovery_world_v92.json" && c.Sources[name] != expected {
			t.Fatalf("world-only HTTP reference changed another source %s", name)
		}
	}
	if reflect.DeepEqual(c.Sources, v14.Sources) {
		t.Fatal("V1.5 reused the prior world source identity")
	}
	for _, read := range []func() (*Corpus, error){Frozen, reviewedV12, reviewedV13, reviewedV14} {
		old, err := read()
		if err != nil || reflect.DeepEqual(old.Sources, c.Sources) {
			t.Fatal("V1.5 replaced a historical source scope", err)
		}
		selected, err := ForSources(old.Sources)
		if err != nil || !reflect.DeepEqual(selected, old) {
			t.Fatal("historical selector was lost during V1.5 adoption", err)
		}
	}
}

func TestV15UnknownPartialAndMixedWorldSourcesRefuseBeforeRequests(t *testing.T) {
	data := testData(t)
	client, err := NewClient(Local(httpapi.New(data)), MaxCases)
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	for name, mutate := range map[string]func(map[string]string){
		"unknown-world": func(s map[string]string) { s["alchimie_discovery_world_v92.json"] = strings.Repeat("0", 64) },
		"missing-world": func(s map[string]string) { delete(s, "alchimie_discovery_world_v92.json") },
		"extra-source":  func(s map[string]string) { s["unreviewed-world.json"] = strings.Repeat("0", 64) },
		"same-kg-with-mixed-source": func(s map[string]string) {
			s["quick_games_v92.json"] = "cc242a902fd4c040f0e52da94ec95683a9bbcdab41f4b9fb72de5a9c5ff5659c"
		},
	} {
		t.Run(name, func(t *testing.T) {
			sources := map[string]string{}
			for key, value := range data.Sources {
				sources[key] = value
			}
			mutate(sources)
			if _, err := ForSources(sources); err == nil || client.Count() != 0 {
				t.Fatal("unreviewed world source acquired expectations or made requests")
			}
		})
	}
	v14, err := reviewedV14()
	if err != nil {
		t.Fatal(err)
	}
	if _, err = Replay(context.Background(), client, v14, data); err == nil || client.Count() != 0 {
		t.Fatal("same-KG Source4 replay against Source5 did not refuse before requests")
	}
}
