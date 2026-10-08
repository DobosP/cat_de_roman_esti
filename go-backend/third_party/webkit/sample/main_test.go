package main

import (
	"context"
	"bytes"
	"os/exec"
	"sync"
	"fmt"
	"io/fs"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"regexp"
	"strings"
	"testing"
	"testing/fstest"
	"time"

	"encoding/json"
	"github.com/DobosP/roedu-ui/web-kit/csp"
	"github.com/DobosP/roedu-ui/web-kit/island"
	"github.com/a-h/templ"
	"github.com/DobosP/roedu-ui/web-kit/routes"
	"github.com/jackc/pgx/v5/pgconn"
)

func TestEmbeddedPageAndHealth(t *testing.T) {
	h, err := newHandler(); if err != nil { t.Fatal(err) }
	for _, path := range []string{"/", "/healthz"} {
		r := httptest.NewRecorder(); h.ServeHTTP(r, httptest.NewRequest(http.MethodGet, path, nil))
		if r.Code != 200 || r.Body.Len() == 0 { t.Fatalf("%s: %d %q", path, r.Code, r.Body.String()) }
	}
	r := httptest.NewRecorder(); h.ServeHTTP(r, httptest.NewRequest(http.MethodGet, "/", nil))
	if !strings.Contains(r.Body.String(), "RO-EDU core sample") { t.Fatal("embedded template missing") }
}

func TestManifestRequiredAndNonceShared(t *testing.T) {
	page, err := fs.ReadFile(embedded, "embedfs/templates/home.html")
	if err != nil { t.Fatal(err) }
	files := fstest.MapFS{"embedfs/templates/home.html": {Data: page}}
	if _, err := newHandlerFS(files, true); err == nil { t.Fatal("runtime accepted missing manifest") }
	files[manifestPath] = &fstest.MapFile{Data: []byte(`{"src/sample/main.ts":{"file":"assets/sample-1234abcd.js","isEntry":true}}`)}
	files["embedfs/dist/assets/sample-1234abcd.js"] = &fstest.MapFile{Data: []byte("console.log('fixture');")}
	files[versionsPath] = &fstest.MapFile{Data: []byte(`{"schema":1,"fixture":"versions"}`)}
	options := handlerOptions{RequireManifest: true, RequireIdentity: true, GateSHA: strings.Repeat("a", 40), GateTree: strings.Repeat("b", 64)}
	h, err := newHandlerWithOptions(files, options)
	if err != nil { t.Fatal(err) }
	w := httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest("GET", "/islands", nil))
	if w.Code != 200 { t.Fatalf("page status %d: %s", w.Code, w.Body.String()) }
	nonce := regexp.MustCompile(`'nonce-([^']+)'`).FindStringSubmatch(sampleCSPHeader(t,w.Header(),options.CSPStage))
	if len(nonce) != 2 { t.Fatal("CSP nonce absent") }
	if strings.Contains(w.Body.String(), "{{") || strings.Contains(w.Body.String(), "{%") { t.Fatal("Pongo2 syntax leaked") }
	if !strings.Contains(w.Body.String(), `type="module" src="/static/assets/sample-1234abcd.js"`) { t.Fatal("real manifest tag absent") }
	for _,tag := range regexp.MustCompile(`<script[^>]*>`).FindAllString(w.Body.String(), -1) {
		if !strings.Contains(tag, `nonce="`+nonce[1]+`"`) { t.Fatalf("script nonce diverged: %s",tag) }
	}
	for _,mode := range []string{"eager", "visible", "idle", "interaction"} {
		if !strings.Contains(w.Body.String(), `data-load="`+mode+`"`) { t.Fatalf("load mode missing: %s",mode) }
	}
	w = httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest("GET", "/api/veto", nil))
	if w.Code != 404 { t.Fatal("veto was not an HTTP non-OK result") }
	w = httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest("GET", "/__gate/identity", nil))
	var identity appIdentity
	if err := json.Unmarshal(w.Body.Bytes(), &identity); err != nil { t.Fatal(err) }
	if identity.SHA != options.GateSHA || identity.TreeSHA256 != options.GateTree || identity.ManifestSHA256 != bytesSHA(files[manifestPath].Data) || identity.VersionsLockSHA256 != bytesSHA(files[versionsPath].Data) {
		t.Fatal("live identity did not bind exact embedded bytes and build metadata")
	}
	if _, err := newHandlerWithOptions(files, handlerOptions{RequireManifest: true, RequireIdentity: true}); err == nil { t.Fatal("empty image identity was accepted") }
	delete(files, versionsPath)
	if _, err := newHandlerWithOptions(files, options); err == nil { t.Fatal("missing embedded lock identity was accepted") }
}

func TestSampleRoutesMatchActualRegistration(t *testing.T) {
	mux, _, err := newRouterWithOptions(embedded, handlerOptions{})
	if err != nil { t.Fatal(err) }
	h := csp.Middleware(csp.Policy{})(mux)
	table := routes.Export(mux)
	pages := 0
	for _,route := range table {
		if route.Template == "" { continue }
		pages++
		path := strings.Replace(route.Path, "{$}", "", 1)
		w := httptest.NewRecorder()
		h.ServeHTTP(w, httptest.NewRequest(route.Method, path, nil))
		if w.Code != 200 || !strings.Contains(w.Body.String(), "RO-EDU core sample") { t.Fatalf("exported page %s was not served: %d",route.Name,w.Code) }
	}
	if pages != len(pageRoutes()) || len(table) < pages+5 { t.Fatal("route inventory omitted actual registrations") }
}

// This agreement test feeds actual Go-emitted DOM to the current TypeScript
// loader in real Chromium. No source substring or cached external-input proxy.
func TestGoEmitterMatchesNPMLoader(t *testing.T) {
    nonce := "contract-nonce"
    ctx := island.WithIDs(csp.WithNonce(context.Background(),nonce))
    message := "</script><script>bad()</script> & \"quoted\" \u2028\u2029"
    var markup bytes.Buffer
    skeleton := templ.ComponentFunc(func(ctx context.Context,w io.Writer) error { _,err:=io.WriteString(w,"<p>Server skeleton</p>");return err })
    for _,mode := range []string{"eager","visible","idle","interaction"} {
        component := island.Island("contract-"+mode,island.Options{Props:map[string]any{"message":message,"mode":mode},Load:mode,Skeleton:skeleton})
        if err:=component.Render(ctx,&markup);err!=nil { t.Fatal(err) }
    }
    payload,err:=json.Marshal(map[string]any{"html":markup.String(),"nonce":nonce,"expected":map[string]string{"message":message}})
    if err!=nil { t.Fatal(err) }
    command:=exec.Command("node","web-kit/scripts/island-contract-test.mjs")
    command.Dir="../..";command.Stdin=bytes.NewReader(payload)
    output,err:=command.CombinedOutput()
    if err!=nil { t.Fatalf("actual Go-to-loader browser agreement: %v\n%s",err,output) }
    var report struct {Schema int `json:"schema"`; ScriptCount int `json:"script_count"`; Aborted int `json:"aborted"`; Disposed int `json:"disposed"`; Events []json.RawMessage `json:"events"`}
    if err:=json.Unmarshal(output,&report);err!=nil { t.Fatalf("actual browser report: %v\n%s",err,output) }
    if report.Schema!=1||report.ScriptCount!=4||report.Aborted!=4||report.Disposed!=4||len(report.Events)!=4 { t.Fatalf("incomplete Go-to-loader browser agreement: %s",output) }
}

// The unit runner selects other tests and records pg-live=no-dsn separately.
// The full runner must set GATE_DB_DSN and run this test; no t.Skip is used.
func TestPostgresLive(t *testing.T) {
	dsn := os.Getenv("GATE_DB_DSN")
	if dsn == "" { t.Log("pg-live: skipped reason=no-dsn"); return }
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second); defer cancel()
	conn, err := pgconn.Connect(ctx, dsn)
	if err != nil { t.Fatal("Postgres connection failed") }
	defer conn.Close(context.Background())
	if err := conn.Ping(ctx); err != nil { t.Fatal("Postgres ping failed") }
	result, err := conn.Exec(ctx, "SELECT 16 = current_setting('server_version_num')::int / 10000 AS expected_major").ReadAll()
	if err != nil || len(result) != 1 || len(result[0].Rows) != 1 || string(result[0].Rows[0][0]) != "t" { t.Fatal("Postgres live check requires major 16") }
}


func sampleCSPHeader(t *testing.T, headers http.Header, requested string) string {
	t.Helper()
	stage, err := sampleCSPStage(requested)
	if err != nil { t.Fatal(err) }
	key := "Content-Security-Policy"
	if stage == "report-only" {
		key = "Content-Security-Policy-Report-Only"
		if headers.Get("Content-Security-Policy") != "" { t.Fatal("report-only sample unexpectedly enforced CSP") }
	}
	value := headers.Get(key)
	if !strings.Contains(value, "script-src") || !strings.Contains(value, "'nonce-") { t.Fatalf("%s stage header missing nonce policy",stage) }
	return value
}

func TestSampleCSPStagesAndEnvironment(t *testing.T) {
	for _, stage := range []string{"", "report-only", "enforced"} {
		handler, err := newHandlerWithOptions(embedded, handlerOptions{CSPStage:stage})
		if err != nil { t.Fatal(err) }
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, httptest.NewRequest("GET", "/", nil))
		_ = sampleCSPHeader(t,w.Header(),stage)
	}
	if _, err := newHandlerWithOptions(embedded, handlerOptions{CSPStage:"invalid"}); err == nil { t.Fatal("unknown CSP stage accepted") }
	t.Setenv("CSP_STAGE","enforced")
	handler, err := newHandler()
	if err != nil { t.Fatal(err) }
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, httptest.NewRequest("GET", "/", nil))
	_ = sampleCSPHeader(t,w.Header(),"enforced")
}

func TestSampleCSPCountsActualReportsWithoutReset(t *testing.T) {
	for _, stage := range []string{"report-only", "enforced"} {
		t.Run(stage,func(t *testing.T) {
			handler, err := newHandlerWithOptions(embedded,handlerOptions{CSPStage:stage})
			if err != nil { t.Fatal(err) }
			read := func(expected uint64) {
				w := httptest.NewRecorder()
				handler.ServeHTTP(w,httptest.NewRequest("GET","/__gate/csp",nil))
				var report struct { Stage string `json:"stage"`; Violations uint64 `json:"violations"` }
				if err := json.Unmarshal(w.Body.Bytes(),&report); err != nil { t.Fatal(err) }
				if report.Stage != stage || report.Violations != expected || w.Code != 200 { t.Fatalf("actual report count: stage=%s violations=%d",report.Stage,report.Violations) }
				_ = sampleCSPHeader(t,w.Header(),stage)
			}
			post := func(content,body string,expected int) {
				r := httptest.NewRequest("POST","/csp-report",strings.NewReader(body))
				r.Header.Set("Content-Type",content)
				w := httptest.NewRecorder();handler.ServeHTTP(w,r)
				if w.Code != expected { t.Fatalf("report endpoint status %d",w.Code) }
			}
			read(0)
			post("application/csp-report",`{"csp-report":{"effective-directive":"script-src"}}`,204)
			post("application/reports+json",`[{"type":"csp-violation"},{"type":"csp-violation"}]`,204)
			read(3)
			post("application/json",`not JSON`,400)
			read(3)
			w := httptest.NewRecorder()
			handler.ServeHTTP(w,httptest.NewRequest("POST","/__gate/csp/reset",nil))
			if w.Code != 404 { t.Fatal("counter reset endpoint exists") }
			read(3)
			statuses := make(chan int,8)
			for range 8 {
				go func() {
					r := httptest.NewRequest("POST","/csp-report",strings.NewReader(`{"csp-report":{"effective-directive":"style-src"}}`))
					r.Header.Set("Content-Type","application/csp-report")
					w := httptest.NewRecorder();handler.ServeHTTP(w,r);statuses <- w.Code
				}()
			}
			for range 8 { if code := <-statuses; code != 204 { t.Fatalf("parallel report status %d",code) } }
			read(11)
			fresh, err := newHandlerWithOptions(embedded,handlerOptions{CSPStage:stage})
			if err != nil { t.Fatal(err) }
			w = httptest.NewRecorder();fresh.ServeHTTP(w,httptest.NewRequest("GET","/__gate/csp",nil))
			var report struct { Violations uint64 `json:"violations"` }
			if err := json.Unmarshal(w.Body.Bytes(),&report); err != nil || report.Violations != 0 { t.Fatal("counter leaked between handler instances") }
		})
	}
}

// The strong TT page is the real HTTP response with the same rendering nonce.
func TestNativeTrustedTypesFixture(t *testing.T) {
  for _,stage:=range []string{"report-only","enforced"} {
    handler,err:=newHandlerWithOptions(embedded,handlerOptions{CSPStage:stage});if err!=nil {t.Fatal(err)}
    w:=httptest.NewRecorder();handler.ServeHTTP(w,httptest.NewRequest("GET","/behaviors?__gate_tt=enforced",nil))
    if w.Code!=200 {t.Fatalf("native TT fixture %s: %d %s",stage,w.Code,w.Body.String())}
    policy:=w.Header().Get("Content-Security-Policy")
    if !strings.Contains(policy,"require-trusted-types-for 'script'")||!strings.Contains(policy,"trusted-types roedu-hovercard roedu-islands") {t.Fatal("native TT enforcement absent")}
    matches:=regexp.MustCompile(`'nonce-([^']+)'`).FindStringSubmatch(policy);if len(matches)!=2 {t.Fatal("native TT nonce absent")}
    for _,tag:=range regexp.MustCompile(`<script[^>]*>`).FindAllString(w.Body.String(),-1) {if !strings.Contains(tag,`nonce="`+matches[1]+`"`) {t.Fatal("native TT renderer nonce diverged")}}
  }
}

func TestCSPSummaryConservesCountsAndRedacts(t *testing.T) {
    handler,err:=newHandlerWithOptions(embedded,handlerOptions{CSPStage:"report-only"});if err!=nil {t.Fatal(err)}
    var workers sync.WaitGroup
    for i:=0;i<150;i++ {workers.Add(1);go func(i int){defer workers.Done();payload:=fmt.Sprintf(`{"body":{"effectiveDirective":"directive-%d nonce-TestNonce","blockedURL":"http://example.test/x?nonce=TestNonce","documentURL":"http://example.test/page#TestNonce","sourceFile":"nonce-TestNonce","disposition":{"nonce":"TestNonce"},"lineNumber":{"bad":"TestNonce"},"columnNumber":1}}`,i);w:=httptest.NewRecorder();r:=httptest.NewRequest("POST","/csp-report",strings.NewReader(payload));r.Header.Set("Content-Type","application/reports+json");handler.ServeHTTP(w,r);if w.Code!=204 {t.Errorf("report status %d",w.Code)}}(i)}
    for i:=0;i<30;i++ {w:=httptest.NewRecorder();handler.ServeHTTP(w,httptest.NewRequest("GET","/__gate/csp",nil));var snapshot struct{Violations uint64 `json:"violations"`;Directives map[string]uint64 `json:"directives"`};if err:=json.Unmarshal(w.Body.Bytes(),&snapshot);err!=nil {t.Fatal(err)};var total uint64;for key,count:=range snapshot.Directives {total+=count;if strings.Contains(key,"TestNonce")||len(key)>4096 {t.Fatal("unbounded/unredacted CSP summary")}};if total!=snapshot.Violations {t.Fatalf("CSP snapshot lost counts: %d != %d",total,snapshot.Violations)}}
    workers.Wait();w:=httptest.NewRecorder();handler.ServeHTTP(w,httptest.NewRequest("GET","/__gate/csp",nil));var final struct{Violations uint64 `json:"violations"`;Directives map[string]uint64 `json:"directives"`};if err:=json.Unmarshal(w.Body.Bytes(),&final);err!=nil {t.Fatal(err)};if final.Violations!=150||len(final.Directives)>128||final.Directives["overflow"]==0 {t.Fatalf("bounded conservation failed: %s",w.Body.String())}
    summary:=cspSummary(csp.Report{"body":map[string]any{"effectiveDirective":"script-src","disposition":"enforce","lineNumber":float64(20),"columnNumber":float64(36)}});if !strings.HasSuffix(summary," | enforce | 20 | 36") {t.Fatal("Reporting API typed fields missing")}
}

func TestCSPSummaryKeepsOnlyKnownSinkPrefix(t *testing.T) {
    summary:=cspSummary(csp.Report{"csp-report":map[string]any{"script-sample":"HTMLScriptElement text|nonce-TestNonce payload", "effective-directive":"require-trusted-types-for", "disposition":"report"}})
    if !strings.HasPrefix(summary,"HTMLScriptElement text | ")||strings.Contains(summary,"TestNonce")||strings.Contains(summary,"payload") {t.Fatal("bounded sink category leaked content")}
    if !strings.HasPrefix(cspSummary(csp.Report{"body":map[string]any{"sample":"payload nonce-TestNonce"}}),"unknown | ") {t.Fatal("arbitrary sample accepted as sink category")}
}
