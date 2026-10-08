package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DobosP/roedu-ui/web-kit/budget"
	"github.com/DobosP/roedu-ui/web-kit/routes"
)

const limitsJSON = `{"schema":1,"measured_at":null,"js":{"server-page":{"limit_gz":10240},"island-route":{"limit_gz":35840},"cat-initial":{"limit_gz":40960,"target_gz":30720},"vendor-gated":{"maplibre":{"limit_gz":317440}}},"css":{"global":{"limit_gz":null}},"routes":{},"vitals":{"lcp_ms":2500,"inp_ms":200,"throttle":{"cpu":4,"rtt_ms":150,"down_kbps":1600}}}`

func commandFixture(t *testing.T) ([]string, string, string) {
	t.Helper()
	root := t.TempDir()
	write := func(name, content string) {
		filename := filepath.Join(root, name)
		if err := os.MkdirAll(filepath.Dir(filename), 0755); err != nil { t.Fatal(err) }
		if err := os.WriteFile(filename, []byte(content), 0644); err != nil { t.Fatal(err) }
	}
	write("budgets.json", limitsJSON)
	write("assets/.vite/manifest.json", `{"main":{"file":"main-12345678.js","css":["app.css"]}}`)
	write("assets/main-12345678.js", "console.log('real fixture bytes');")
	write("assets/app.css", "body{color:black}")
	write("config.json", `{"schema":1,"routes":{"home":{"class":"server-page","entries":["main"],"islands":[],"widgets":[],"vendors":[]}},"global_css":["app.css"],"vendors":{}}`)
	mux := routes.NewMux()
	if err := mux.Handle(routes.Route{Name: "home", Method: "GET", Path: "/", Template: "home.html"}, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(200) })); err != nil { t.Fatal(err) }
	exported, err := json.Marshal(routes.Export(mux))
	if err != nil { t.Fatal(err) }
	write("routes.json", string(exported))
	out := filepath.Join(root, "measurements/result.json")
	return []string{"--budgets", filepath.Join(root, "budgets.json"), "--manifest", ".vite/manifest.json", "--assets", filepath.Join(root, "assets"), "--config", filepath.Join(root, "config.json"), "--routes", filepath.Join(root, "routes.json"), "--out", out}, out, root
}

func TestCommandMeasuresActualAssets(t *testing.T) {
	args, output, _ := commandFixture(t)
	var stdout bytes.Buffer
	if err := run(args, &stdout); err != nil { t.Fatal(err) }
	data, err := os.ReadFile(output)
	if err != nil || !bytes.Equal(data, stdout.Bytes()) { t.Fatal("measurement output was not written") }
	var report budget.Report
	if err := json.Unmarshal(data, &report); err != nil { t.Fatal(err) }
	if report.Status != "pass" || len(report.Routes) != 1 || report.Routes[0].JS.ActualGZ <= 0 || report.GlobalCSS.Status != "recorded" { t.Fatalf("report wrong: %#v",report) }
}

func TestCommandRejectsMissingOverrideAndExceed(t *testing.T) {
	if err := run(nil, &bytes.Buffer{}); err == nil { t.Fatal("missing paths accepted") }
	args, output, root := commandFixture(t)
	if err := run(append(args, "--limit-gz", "1000000"), &bytes.Buffer{}); err == nil { t.Fatal("limit override accepted") }
	if err := os.WriteFile(filepath.Join(root,"budgets.json"), []byte(strings.Replace(limitsJSON,`"limit_gz":10240`,`"limit_gz":0`,1)),0644); err != nil { t.Fatal(err) }
	if err := run(args, &bytes.Buffer{}); err == nil { t.Fatal("over-limit command succeeded") }
	data, err := os.ReadFile(output)
	if err != nil || !strings.Contains(string(data), `"status": "fail"`) { t.Fatal("failed actual measurements were not retained") }
	if err := os.WriteFile(filepath.Join(root,"routes.json"), []byte(`[{"name":"other","method":"GET","path":"/other","template":"other.html"}]`),0644); err != nil { t.Fatal(err) }
	if err := run(args, &bytes.Buffer{}); err == nil { t.Fatal("binding disconnected from Go route table") }
}
