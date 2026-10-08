package budget_test

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/DobosP/roedu-ui/web-kit/budget"
	"github.com/DobosP/roedu-ui/web-kit/routes"
)

type Budgets = budget.Budgets
type Manifest = budget.Manifest
type Config = budget.Config
type Report = budget.Report
type Limit = budget.Limit
type RouteBudget = budget.RouteBudget

var Load = budget.Load
var LoadManifest = budget.LoadManifest
var LoadConfig = budget.LoadConfig
var Evaluate = budget.Evaluate

const fixtureBudgets = `{"schema":1,"measured_at":null,"source":"unit fixture","js":{"server-page":{"limit_gz":10240},"island-route":{"limit_gz":35840},"cat-initial":{"limit_gz":40960,"target_gz":30720},"vendor-gated":{"maplibre":{"limit_gz":317440}}},"css":{"global":{"limit_gz":null}},"routes":{},"vitals":{"lcp_ms":2500,"inp_ms":200,"throttle":{"cpu":4,"rtt_ms":150,"down_kbps":1600}}}`
const fixtureManifest = `{"main":{"file":"main-12345678.js","imports":["dep"],"css":["global.css"],"dynamicImports":["vendor"]},"island":{"file":"island-12345678.js","imports":["dep"],"css":["global.css","island.css"]},"dep":{"file":"shared-12345678.js"},"vendor":{"file":"vendor-12345678.js"}}`
const fixtureConfig = `{"schema":1,"routes":{"home":{"class":"server-page","entries":["main"],"islands":["island"],"widgets":[],"vendors":[{"name":"maplibre","entry":"vendor","eager":false}]}},"global_css":["global.css"],"vendors":{"maplibre":"vendor"}}`

func fixture(t *testing.T) (*Budgets, *Manifest, []routes.Route, *Config) {
	t.Helper()
	files := fstest.MapFS{
		".vite/manifest.json": {Data: []byte(fixtureManifest)},
		"main-12345678.js": {Data: []byte("console.log('main');")},
		"island-12345678.js": {Data: []byte("console.log('island');")},
		"shared-12345678.js": {Data: []byte("console.log('shared');")},
		"vendor-12345678.js": {Data: []byte("console.log('vendor');")},
		"global.css": {Data: []byte("body{color:black}")},
		"island.css": {Data: []byte(".island{display:block}")},
	}
	b, err := Load([]byte(fixtureBudgets))
	if err != nil { t.Fatal(err) }
	m, err := LoadManifest(files, ".vite/manifest.json")
	if err != nil { t.Fatal(err) }
	c, err := LoadConfig([]byte(fixtureConfig))
	if err != nil { t.Fatal(err) }
	table := routes.Export(routes.Table{{Name: "home", Method: "GET", Path: "/", Template: "home.html"}, {Name: "health", Method: "GET", Path: "/healthz"}})
	return b, m, table, c
}

func TestRouteBudgets(t *testing.T) {
	b, m, table, c := fixture(t)
	report := runRouteBudgetHelper(t, b, m, table, c)
	if report.GlobalCSS.Status != "recorded" || report.GlobalCSS.ActualGZ <= 0 || report.Routes[0].CSS.Status != "recorded" {
		t.Fatal("null CSS limit did not report actual bytes")
	}
	if len(report.Routes) != 1 || len(report.Routes[0].JS.Files) != 3 || len(report.Routes[0].CSS.Files) != 2 || len(report.NonPageRoutes) != 1 {
		t.Fatalf("dependency/global CSS dedup failed: %#v", report)
	}
	if len(report.Vendors) != 1 || len(report.Vendors[0].Files) != 1 { t.Fatal("gated vendor was not independently measured") }
	binding := c.Routes["home"]
	binding.Vendors[0].Eager = true
	c.Routes["home"] = binding
	eager, err := Evaluate(b, m, table, c)
	if err != nil || len(eager.Routes[0].JS.Files) != 4 || eager.Routes[0].JS.ActualGZ <= report.Routes[0].JS.ActualGZ {
		t.Fatal("eager vendor did not enter initial route bytes")
	}
}

// Alias keeps the package's exported TestRouteBudgets helper and this executed
// test entry distinct, so consumers call budget.TestRouteBudgets unchanged.
func runRouteBudgetHelper(t testing.TB, b *Budgets, m *Manifest, table []routes.Route, c *Config) Report {
	return budget.TestRouteBudgets(t, b, m, table, c)
}

func TestMissingLimitsAndOverridesFail(t *testing.T) {
	for _, bad := range []string{
		strings.Replace(fixtureBudgets, `"limit_gz":10240`, `"target_gz":100`, 1),
		strings.Replace(fixtureBudgets, `"limit_gz":null`, `"unused":null`, 1),
		strings.Replace(fixtureBudgets, `"lcp_ms":2500,`, "", 1),
		strings.Replace(fixtureBudgets, `"limit_gz":10240`, `"limit_gz":-1`, 1),
		strings.Replace(fixtureBudgets, `"limit_gz":10240`, `"limit_gz":1.5`, 1),
		strings.Replace(fixtureBudgets, `,"target_gz":30720`, "", 1),
		strings.Replace(fixtureBudgets, `"measured_at":null,`, "", 1),
		strings.Replace(fixtureBudgets, `"measured_at":null`, `"measured_at":"not-a-sha"`, 1),
		strings.Replace(fixtureBudgets, `"source":"unit fixture"`, `"source":null`, 1),
		strings.Replace(fixtureBudgets, `"limit_gz":10240`, `"limit_gz":null`, 1),
		strings.Replace(fixtureBudgets, `"limit_gz":317440`, `"limit_gz":null`, 1),
		strings.Replace(fixtureBudgets, `"rtt_ms":150,`, "", 1),
		strings.Replace(fixtureBudgets, `"rtt_ms":150`, `"rtt_ms":null`, 1),
		fixtureBudgets + " trailing",
	} {
		if _, err := Load([]byte(bad)); err == nil { t.Fatalf("invalid budget accepted: %s", bad) }
	}
	for _, bad := range []string{
		strings.Replace(fixtureConfig, `"entries":["main"]`, `"limit_gz":999999`, 1),
		strings.Replace(fixtureConfig, `"global_css":["global.css"],`, "", 1),
		strings.Replace(fixtureConfig, `"entries":["main"]`, `"entries":null`, 1),
		strings.Replace(fixtureConfig, `,"eager":false`, "", 1),
	} {
		if _, err := LoadConfig([]byte(bad)); err == nil { t.Fatalf("config override/missing list accepted: %s", bad) }
	}
}

func TestBudgetSchemaAllowsZeroRTTAndActualMeasuredSHA(t *testing.T) {
	data := strings.Replace(fixtureBudgets, `"rtt_ms":150`, `"rtt_ms":0`, 1)
	data = strings.Replace(data, `"measured_at":null`, `"measured_at":"`+strings.Repeat("a",40)+`"`, 1)
	b, err := Load([]byte(data))
	if err != nil || b.MeasuredAt == nil || *b.MeasuredAt != strings.Repeat("a",40) || b.Vitals.Throttle.RTTMS != 0 { t.Fatal("valid explicit schema metadata/zero RTT rejected") }
	withoutSource := strings.Replace(fixtureBudgets, `"source":"unit fixture",`, "", 1)
	if _, err := Load([]byte(withoutSource)); err != nil { t.Fatal("optional source was required") }
}

func TestLimitAndBindingMutations(t *testing.T) {
	b, m, table, c := fixture(t)
	zero := int64(0)
	b.Classes["server-page"] = Limit{LimitGZ: &zero}
	report, err := Evaluate(b, m, table, c)
	if err != nil || report.Status != "fail" || report.Routes[0].JS.Status != "fail" { t.Fatal("JS exceed mutation passed") }
	b, m, table, c = fixture(t)
	b.GlobalCSS = Limit{LimitGZ: &zero}
	report, err = Evaluate(b, m, table, c)
	if err != nil || report.Status != "fail" || report.GlobalCSS.Status != "fail" { t.Fatal("CSS exceed mutation passed") }
	b, m, table, c = fixture(t)
	b.Vendors["maplibre"] = Limit{LimitGZ: &zero}
	report, err = Evaluate(b, m, table, c)
	if err != nil || report.Status != "fail" || report.Vendors[0].Status != "fail" { t.Fatal("gated vendor exceed mutation passed") }
	b, m, table, c = fixture(t)
	delete(c.Routes, "home")
	if _, err := Evaluate(b, m, table, c); err == nil { t.Fatal("missing route binding passed") }
	b, m, table, c = fixture(t)
	binding := c.Routes["home"]
	binding.Entries = []string{"missing"}
	c.Routes["home"] = binding
	if _, err := Evaluate(b, m, table, c); err == nil { t.Fatal("missing manifest entry passed") }
	b, m, table, c = fixture(t)
	b.Routes["home"] = RouteBudget{Class: "island-route", Islands: []string{"island"}}
	if _, err := Evaluate(b, m, table, c); err == nil { t.Fatal("committed route class was overridden") }
	b.Routes["home"] = RouteBudget{Class: "server-page", Islands: []string{"different"}}
	if _, err := Evaluate(b, m, table, c); err == nil { t.Fatal("committed route islands were overridden") }
}

func TestGzipWitnessAndUnusedLimits(t *testing.T) {
	b, m, table, c := fixture(t)
	files := m.Files.(fstest.MapFS)
	var compressed bytes.Buffer
	writer := gzip.NewWriter(&compressed)
	_, _ = writer.Write(files["main-12345678.js"].Data)
	_ = writer.Close()
	files["main-12345678.js.gz"] = &fstest.MapFile{Data: compressed.Bytes()}
	report, err := Evaluate(b, m, table, c)
	if err != nil { t.Fatal(err) }
	if len(report.UnusedLimits) != 2 || report.UnusedLimits[0].TargetGZ == nil { t.Fatal("unused class limits/target were not explicitly reported") }
	files["main-12345678.js.gz"] = &fstest.MapFile{Data: []byte("not gzip")}
	if _, err := Evaluate(b, m, table, c); err == nil { t.Fatal("invalid sidecar was accepted") }
	var stale bytes.Buffer
	writer = gzip.NewWriter(&stale)
	_, _ = writer.Write([]byte("wrong original"))
	_ = writer.Close()
	files["main-12345678.js.gz"] = &fstest.MapFile{Data: stale.Bytes()}
	if _, err := Evaluate(b, m, table, c); err == nil { t.Fatal("stale gzip sidecar was accepted") }
	data, err := json.Marshal(report)
	if err != nil || !strings.Contains(string(data), `"status":"recorded"`) { t.Fatal("actual record status missing from JSON") }
}
