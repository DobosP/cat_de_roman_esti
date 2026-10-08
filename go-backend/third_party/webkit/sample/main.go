// The sample is a local qualification app, built as /app in the test image.
package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"embed"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"log"
	"net/http"
	"os"
	"sync/atomic"
	"sync"
	"strings"
	"regexp"
	"sort"
	"html"
	"math"
	"strconv"
	"time"

	"github.com/a-h/templ"
	"github.com/DobosP/roedu-ui/web-kit/assets"
	"github.com/DobosP/roedu-ui/web-kit/csp"
	"github.com/DobosP/roedu-ui/web-kit/engine"
	"github.com/DobosP/roedu-ui/web-kit/health"
	"github.com/DobosP/roedu-ui/web-kit/island"
	"github.com/DobosP/roedu-ui/web-kit/routes"
	"github.com/DobosP/roedu-ui/web-kit/static"
)

//go:embed all:embedfs
var embedded embed.FS

// The image builder supplies these via -X main.gateSHA and -X main.gateTree.
// Empty/source-only metadata never qualifies as a live gate witness.
var gateSHA string
var gateTree string

const sampleEntry = "src/sample/main.ts"
const manifestPath = "embedfs/dist/.vite/manifest.json"
const versionsPath = "embedfs/versions.lock.json"

type appIdentity = health.Identity

type handlerOptions struct {
	RequireManifest bool
	RequireIdentity bool
	GateSHA string
	GateTree string
	CSPStage string
}

func bytesSHA(data []byte) string {
	digest := sha256.Sum256(data)
	return hex.EncodeToString(digest[:])
}

func port() string {
	if p := os.Getenv("PORT"); p != "" {
		return p
	}
	return "8080"
}

func pageRoutes() []routes.Route {
	return []routes.Route{
		{Name: "home", Method: "GET", Path: "/{$}", Template: "home.html", Group: "sample"},
		{Name: "pongo2", Method: "GET", Path: "/pongo2", Template: "home.html", Group: "sample"},
		{Name: "islands", Method: "GET", Path: "/islands", Template: "home.html", Group: "sample"},
		{Name: "behaviors", Method: "GET", Path: "/behaviors", Template: "home.html", Group: "sample"},
		{Name: "motion", Method: "GET", Path: "/motion", Template: "home.html", Group: "sample"},
		{Name: "templ", Method: "GET", Path: "/templ", Template: "sample.templ", Group: "sample"},
	}
}

// This explicit compiled sample does not enable Templ/Shadow in the S0a
// Pongo2-only delivery engine. S0b retains ownership of runtime engine modes.
func pongoRoutes() []routes.Route {
	var out []routes.Route
	for _, route := range pageRoutes() { if route.Name != "templ" { out=append(out,route) } }
	return out
}

func sampleEngineReport(renderer *engine.Engine) []engine.RouteEngine {
	out:=renderer.Report()
	out=append(out,engine.RouteEngine{Route:"templ",Group:"sample",Mode:"Templ",Source:engine.RouteSource})
	sort.Slice(out,func(i,j int)bool{return out[i].Route<out[j].Route})
	return out
}

// newHandler permits the M0 source-only fixture before generated assets exist.
// The executable's HTTP serving path requires both assets and image metadata.
func newHandler() (http.Handler, error) {
	return newHandlerFS(embedded, false)
}

func newHandlerFS(files fs.FS, requireManifest bool) (http.Handler, error) {
	return newHandlerWithOptions(files, handlerOptions{
		RequireManifest: requireManifest,
		RequireIdentity: requireManifest,
		GateSHA: gateSHA,
		GateTree: gateTree,
		CSPStage: os.Getenv("CSP_STAGE"),
	})
}

func sampleCSPStage(stage string) (string, error) {
	if stage == "" { stage = "report-only" }
	if stage != "report-only" && stage != "enforced" { return "", fmt.Errorf("CSP_STAGE must be report-only or enforced") }
	return stage, nil
}

func newHandlerWithOptions(files fs.FS, options handlerOptions) (http.Handler, error) {
	stage, err := sampleCSPStage(options.CSPStage)
	if err != nil { return nil, err }
	mux, _, err := newRouterWithOptions(files, options)
	if err != nil {
		return nil, err
	}
	return csp.Middleware(csp.Policy{ReportOnly: stage == "report-only", TrustedTypes: []string{"roedu-hovercard", "roedu-islands"}})(mux), nil
}

// The routes command exports this very router's registrations, so budgets use
// the same named paths and page metadata as actual HTTP delivery.
func newRouterWithOptions(files fs.FS, options handlerOptions) (*routes.Mux, *engine.Engine, error) {
	stage, err := sampleCSPStage(options.CSPStage)
	if err != nil { return nil, nil, err }
	var violations atomic.Uint64
	var reportMu sync.Mutex
	directives := map[string]uint64{}
	var manifest *assets.Manifest
	var manifestBytes, versionsLockBytes []byte
	identity := appIdentity{SHA: options.GateSHA, TreeSHA256: options.GateTree}
	if data, err := fs.ReadFile(files, manifestPath); err == nil {
		manifestBytes = data
		identity.ManifestSHA256 = bytesSHA(data)
		var loadErr error
		manifest, loadErr = assets.Parse(files, manifestPath, "embedfs/dist", "/static/")
		if loadErr != nil {
			return nil, nil, loadErr
		}
		if manifest.Static(sampleEntry) == "" {
			return nil, nil, fmt.Errorf("sample entry is absent from the asset manifest")
		}
	} else if options.RequireManifest {
		return nil, nil, fmt.Errorf("sample requires built frontend assets")
	}
	if data, err := fs.ReadFile(files, versionsPath); err == nil {
		versionsLockBytes = data
		identity.VersionsLockSHA256 = bytesSHA(data)
	} else if options.RequireIdentity {
		return nil, nil, fmt.Errorf("sample requires embedded versions.lock.json")
	}
	if options.RequireIdentity {
		complete, err := health.NewIdentity(options.GateSHA, options.GateTree, manifestBytes, versionsLockBytes)
		if err != nil { return nil, nil, err }
		identity = *complete
	}
	pages := pageRoutes()
	renderer, err := engine.New(files, engine.Options{TemplateRoot: "embedfs/templates", Routes: pongoRoutes()})
	if err != nil {
		return nil, nil, err
	}
	mux := routes.NewMux()
	auxiliary := []struct {
		route routes.Route
		handler http.Handler
	}{
		{routes.Route{Name: "health", Method: "GET", Path: "/healthz"}, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("Cache-Control", "no-store")
			fmt.Fprintln(w, `{"status":"ok"}`)
		})},
		{routes.Route{Name: "gate-identity", Method: "GET", Path: "/__gate/identity"}, identity.Handler()},
		{routes.Route{Name: "csp-report", Method: "POST", Path: "/csp-report"}, csp.ReportHandler(func(ctx context.Context, reports []csp.Report) {
			reportMu.Lock()
            for _,report := range reports {
                key:=cspSummary(report)
                if _,exists:=directives[key];!exists&&len(directives)>=127 {key="overflow"}
                directives[key]++
            }
            violations.Add(uint64(len(reports)))
            reportMu.Unlock()
		})},
		{routes.Route{Name: "gate-csp", Method: "GET", Path: "/__gate/csp"}, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("Cache-Control", "no-store")
            reportMu.Lock();snapshot:=map[string]uint64{};for key,count:=range directives {snapshot[key]=count};total:=violations.Load();reportMu.Unlock()
			_ = json.NewEncoder(w).Encode(struct {
                Directives map[string]uint64 `json:"directives"`
				Stage string `json:"stage"`
				Violations uint64 `json:"violations"`
			}{Stage: stage, Violations: total,Directives:snapshot})
		})},
		{routes.Route{Name: "hovercard", Method: "GET", Path: "/api/hovercard"}, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/html; charset=utf-8")
			w.Header().Set("Cache-Control", "no-store")
			_, _ = io.WriteString(w, "<p>Sample person</p>")
		})},
		{routes.Route{Name: "hovercard-veto", Method: "GET", Path: "/api/veto"}, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Cache-Control", "no-store")
			http.NotFound(w, r)
		})},
	}
	for _, entry := range auxiliary {
		if err := mux.Handle(entry.route, entry.handler); err != nil {
			return nil, nil, err
		}
	}
	if manifest != nil {
		readDirFS, ok := files.(fs.ReadDirFS)
		if !ok {
			return nil, nil, fmt.Errorf("asset filesystem must support ReadDir")
		}
		if err := mux.Handle(routes.Route{Name: "static", Method: "GET", Path: "/static/"}, http.StripPrefix("/static/", static.Handler(readDirFS, static.Options{Prefix: "embedfs/dist"}))); err != nil {
			return nil, nil, err
		}
	}
	for _, route := range pages {
		handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            // A native same-origin fixture avoids intercepted-document address-space artifacts.
            if r.URL.Query().Get("__gate_tt")!="" {
                if (route.Name!="behaviors"&&route.Name!="templ")||r.URL.Query().Get("__gate_tt")!="enforced" {http.Error(w,"invalid TT fixture",400);return}
                reportOnly:=w.Header().Get("Content-Security-Policy-Report-Only")
                enforced:=w.Header().Get("Content-Security-Policy")
                if enforced=="" {enforced=reportOnly} else {enforced+="; "+strings.Split(reportOnly,"; report-uri ")[0]}
                if !strings.Contains(enforced,"require-trusted-types-for 'script'")||!strings.Contains(enforced,"'nonce-"+csp.Nonce(r.Context())+"'") {http.Error(w,"TT fixture policy missing",500);return}
                w.Header().Set("Content-Security-Policy",enforced)
            }
			ctx := island.WithIDs(r.Context())
			var tags templ.Component=templ.NopComponent
			if manifest != nil {
				ctx = assets.WithManifest(ctx, manifest)
				tags=assets.Tags(ctx,sampleEntry)
			}
			if route.Name=="templ" {
				_ = renderComponentPage(ctx,w,sampleTemplPage(tags,stressIslands()))
				return
			}
			var assetTags bytes.Buffer
			if err := tags.Render(ctx,&assetTags);err!=nil {
				http.Error(w,"sample asset render failed",http.StatusInternalServerError)
				return
			}
			var markup bytes.Buffer
			if err := stressIslands().Render(ctx, &markup); err != nil {
				http.Error(w, "sample island render failed", http.StatusInternalServerError)
				return
			}
			_ = renderer.Render(ctx, w, engine.Page{
				Route: route.Name,
				Template: route.Template,
				Data: map[string]any{
					"assets_tags": assetTags.String(),
					"islands_markup": markup.String(),
					"page_name": route.Name,
				},
			})
		})
		if err := mux.Handle(route, handler); err != nil {
			return nil, nil, err
		}
	}
	return mux, renderer, nil
}

// Standalone compiled templ follows the same atomic response boundary as
// Pongo2: no successful header or partial page leaves the buffer on failure.
func renderComponentPage(ctx context.Context,w http.ResponseWriter,component templ.Component) error {
	fail:=func(err error)error{w.Header().Del("Content-Length");http.Error(w,"template render failed",http.StatusInternalServerError);return err}
	if err:=ctx.Err();err!=nil{return fail(err)}
	var body bytes.Buffer
	if err:=component.Render(ctx,&body);err!=nil{return fail(err)}
	if err:=ctx.Err();err!=nil{return fail(err)}
	w.Header().Set("Content-Type","text/html; charset=utf-8")
	w.Header().Set("Cache-Control","no-cache")
	_,err:=w.Write(body.Bytes());return err
}

// The three behavior payloads use the request's nonce and ordinary JSON's
// HTML escaping. Props cannot close the script or create an executable sink.
func sampleJSONScript(id string,value any) templ.Component {
	return templ.ComponentFunc(func(ctx context.Context,w io.Writer)error {
		if !regexp.MustCompile(`^[A-Za-z][A-Za-z0-9_-]*$`).MatchString(id){return fmt.Errorf("invalid JSON script ID")}
		nonce:=csp.Nonce(ctx);if nonce==""{return fmt.Errorf("JSON script requires request nonce")}
		payload,err:=json.Marshal(value);if err!=nil{return err}
		_,err=fmt.Fprintf(w,`<script type="application/json" id="%s" nonce="%s">%s</script>`,html.EscapeString(id),html.EscapeString(nonce),payload)
		return err
	})
}

func stressIslands() templ.Component {
	skeleton := templ.ComponentFunc(func(ctx context.Context, w io.Writer) error {
		_, err := io.WriteString(w, "<p>Server skeleton</p>")
		return err
	})
	return templ.Join(
		island.Island("stress-counter", island.Options{Props: map[string]any{"count": 0}, Load: "eager", Skeleton: skeleton}),
		island.Island("stress-presence", island.Options{Props: map[string]any{"durationMs": 120}, Load: "visible", Skeleton: skeleton}),
		island.Island("stress-events", island.Options{Props: map[string]any{"count": 0}, Load: "idle", Skeleton: skeleton}),
		island.Island("stress-counter", island.Options{Props: map[string]any{"count": 1}, Load: "interaction", Skeleton: skeleton}),
	)
}

func main() {
	if len(os.Args) > 1 && os.Args[1] == "routes" {
		if len(os.Args) != 2 {
			log.Fatal("usage: routes")
		}
		mux, _, err := newRouterWithOptions(embedded, handlerOptions{})
		if err != nil {
			log.Fatal(err)
		}
		if err := json.NewEncoder(os.Stdout).Encode(routes.Export(mux)); err != nil {
			log.Fatal(err)
		}
		return
	}
	if len(os.Args) > 1 {
		renderer, err := engine.New(embedded, engine.Options{TemplateRoot: "embedfs/templates", Routes: pongoRoutes()})
		if err != nil {
			log.Fatal(err)
		}
		options := health.Options{
			URL: "http://127.0.0.1:" + port() + "/healthz",
			Engines: func() any { return sampleEngineReport(renderer) },
		}
		if err := health.Command(context.Background(), os.Args[1:], os.Stdout, options); err != nil {
			log.Print(err)
			os.Exit(1)
		}
		return
	}
	handler, err := newHandlerFS(embedded, true)
	if err != nil {
		log.Fatal(err)
	}
	server := &http.Server{Addr: ":" + port(), Handler: handler, ReadHeaderTimeout: 5 * time.Second}
	log.Fatal(server.ListenAndServe())
}

var sinkInSummary=regexp.MustCompile(`^(HTML[A-Za-z]*Element|Element|Document|Range|DOMParser) [A-Za-z][A-Za-z0-9]*$`)
var nonceInSummary=regexp.MustCompile(`nonce-[A-Za-z0-9+/_=-]+`)
func cspSummary(report csp.Report) string {
    detail:=map[string]any(report)
    if nested,ok:=report["csp-report"].(map[string]any);ok {detail=nested} else if nested,ok:=report["body"].(map[string]any);ok {detail=nested}
    text:=func(old,current string)string {value,_:=detail[old].(string);if value=="" {value,_=detail[current].(string)};value=nonceInSummary.ReplaceAllString(value,"nonce-[redacted]");value=strings.Split(strings.Split(value,"?")[0],"#")[0];if len(value)>512 {value=value[:512]};return value}
    number:=func(old,current string)string {value,ok:=detail[old].(float64);if !ok {value,ok=detail[current].(float64)};if !ok||math.IsNaN(value)||math.IsInf(value,0)||value<0||value>1e7||math.Trunc(value)!=value {return "unknown"};return strconv.FormatInt(int64(value),10)}
    disposition,_:=detail["disposition"].(string);if disposition!="report"&&disposition!="enforce" {disposition="unknown"}
    sample,_:=detail["script-sample"].(string);if sample=="" {sample,_=detail["sample"].(string)};sink:=strings.TrimSpace(strings.Split(sample,"|")[0]);if len(sink)>80||!sinkInSummary.MatchString(sink) {sink="unknown"}
    return sink+" | "+text("effective-directive","effectiveDirective")+" | "+text("blocked-uri","blockedURL")+" | "+text("source-file","sourceFile")+" | "+text("document-uri","documentURL")+" | "+disposition+" | "+number("line-number","lineNumber")+" | "+number("column-number","columnNumber")
}
