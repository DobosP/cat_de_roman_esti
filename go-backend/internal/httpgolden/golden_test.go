package httpgolden

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
	"net/http"
	"net/http/httptest"
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
	if err != nil || !reflect.DeepEqual(selected, current) || !reflect.DeepEqual(current.Sources, testData(t).Sources) {
		t.Fatal("current source set selected different expected responses", err)
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
