package main

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"io/fs"
	"net/http"
	"net/http/httptest"
	"reflect"
	"regexp"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/a-h/templ"
	"github.com/DobosP/roedu-ui/web-kit/csp"
	"github.com/DobosP/roedu-ui/web-kit/engine"
	"github.com/DobosP/roedu-ui/web-kit/routes"
	"golang.org/x/net/html"
)

func templFixture(t *testing.T,stage string) (http.Handler,fstest.MapFS) {
	t.Helper()
	page,err:=fs.ReadFile(embedded,"embedfs/templates/home.html");if err!=nil{t.Fatal(err)}
	files:=fstest.MapFS{
		"embedfs/templates/home.html":{Data:page},
		manifestPath:{Data:[]byte(`{"src/sample/main.ts":{"file":"assets/sample-1234abcd.js","isEntry":true,"css":["assets/sample-1234abcd.css"]}}`)},
		"embedfs/dist/assets/sample-1234abcd.js":{Data:[]byte("console.log('fixture');")},
		"embedfs/dist/assets/sample-1234abcd.css":{Data:[]byte(".roedu-root{color:black}")},
		versionsPath:{Data:[]byte(`{"schema":1,"fixture":"versions"}`)},
	}
	h,err:=newHandlerWithOptions(files,handlerOptions{RequireManifest:true,RequireIdentity:true,GateSHA:strings.Repeat("a",40),GateTree:strings.Repeat("b",64),CSPStage:stage});if err!=nil{t.Fatal(err)}
	return h,files
}

func TestCompiledTemplPreservesSevenJSONAndBehaviorBindings(t *testing.T) {
	for _,stage:=range []string{"report-only","enforced"} {
		h,_:=templFixture(t,stage)
		var expected map[string]any
		for _,path:=range []string{"/pongo2","/templ"} {
			w:=httptest.NewRecorder();h.ServeHTTP(w,httptest.NewRequest("GET",path,nil))
			if w.Code!=200{t.Fatalf("%s %s: %d %s",stage,path,w.Code,w.Body.String())}
			if path=="/templ"&&!strings.Contains(w.Body.String(),"Compiled templ delivery is ready."){t.Fatal("compiled page was not served")}
			header:=sampleCSPHeader(t,w.Header(),stage)
			nonceMatch:=regexp.MustCompile(`'nonce-([^']+)'`).FindStringSubmatch(header);if len(nonceMatch)!=2{t.Fatal("CSP nonce missing")}
			nonce:=nonceMatch[1]
			doc,err:=html.Parse(strings.NewReader(w.Body.String()));if err!=nil{t.Fatal(err)}
			props:=map[string]any{};references:=map[string]int{};modes:=map[string]bool{};controls:=map[string]bool{};modules:=0;links:=0
			attr:=func(n *html.Node,key string)string{for _,a:=range n.Attr{if a.Key==key{return a.Val}};return ""}
			var walk func(*html.Node)
			walk=func(n *html.Node){
				if n.Type==html.ElementNode {
					if attr(n,"style")!=""{t.Fatal("inline style in compiled/native sample")}
					if id:=attr(n,"data-props");id!=""{references[id]++}
					if key:=attr(n,"data-island");key!=""{modes[attr(n,"data-load")]=true}
					for _,a:=range n.Attr{if a.Key=="style"{t.Fatal("inline style attribute")};if strings.HasPrefix(a.Key,"on"){t.Fatal("inline handler attribute")};if strings.HasPrefix(a.Key,"data-wizard-")||strings.HasPrefix(a.Key,"data-comfort")||a.Key=="data-speak"||a.Key=="data-hovercard-user"{controls[a.Key+"="+a.Val]=true}}
					if n.Data=="script" {
						if attr(n,"nonce")!=nonce{t.Fatal("script/header nonce diverged")}
						if attr(n,"type")=="module"{modules++;if attr(n,"src")!="/static/assets/sample-1234abcd.js"{t.Fatal("module not from actual manifest")}}
						if attr(n,"type")=="application/json"{id:=attr(n,"id");if _,exists:=props[id];exists{t.Fatal("duplicate JSON ID")};if n.FirstChild==nil{t.Fatal("missing JSON text")};var value any;if err:=json.Unmarshal([]byte(n.FirstChild.Data),&value);err!=nil{t.Fatal(err)};props[id]=value}
					}
					if n.Data=="link"&&(attr(n,"rel")=="stylesheet"||attr(n,"rel")=="modulepreload"){links++;if attr(n,"nonce")!=nonce{t.Fatal("asset link nonce diverged")};if attr(n,"rel")=="stylesheet"&&attr(n,"href")!="/static/assets/sample-1234abcd.css"{t.Fatal("stylesheet is not from actual manifest")}}
				}
				for child:=n.FirstChild;child!=nil;child=child.NextSibling{walk(child)}
			};walk(doc)
			if len(props)!=7||len(references)!=7||modules!=1||links<1{t.Fatalf("incomplete native bindings: JSON=%d refs=%d modules=%d links=%d",len(props),len(references),modules,links)}
			for id:=range props{if references[id]!=1{t.Fatalf("JSON id lacks exactly one host binding: %s",id)}}
			for _,mode:=range []string{"eager","visible","idle","interaction"}{if !modes[mode]{t.Fatalf("missing load mode %s",mode)}}
			for _,control:=range []string{"data-wizard-next=","data-wizard-back=","data-wizard-submit=","data-speak=","data-comfort=size","data-comfort=spacing","data-comfort=font","data-comfort=focus","data-comfort=reset","data-hovercard-user=sample-user"}{if !controls[control]{t.Fatalf("missing equivalent behavior control %s",control)}}
			if expected==nil{expected=props}else if !reflect.DeepEqual(expected,props){t.Fatal("templ/Pongo2 JSON payload semantics differ")}
		}
	}
}

func TestCompiledTemplNativeTrustedTypesAndRouteReport(t *testing.T) {
	for _,stage:=range []string{"report-only","enforced"}{
		h,files:=templFixture(t,stage);w:=httptest.NewRecorder();h.ServeHTTP(w,httptest.NewRequest("GET","/templ?__gate_tt=enforced",nil))
		if w.Code!=200{t.Fatalf("native templ TT fixture: %d",w.Code)}
		policy:=w.Header().Get("Content-Security-Policy");if !strings.Contains(policy,"trusted-types roedu-hovercard roedu-islands")||!strings.Contains(policy,"require-trusted-types-for 'script'"){t.Fatal("same native TT enforcement absent")}
		nonce:=regexp.MustCompile(`'nonce-([^']+)'`).FindStringSubmatch(policy);if len(nonce)!=2{t.Fatal("native TT nonce missing")}
		for _,tag:=range regexp.MustCompile(`<script[^>]*>`).FindAllString(w.Body.String(),-1){if !strings.Contains(tag,`nonce="`+nonce[1]+`"`){t.Fatal("native templ TT renderer nonce differs")}}
		mux,renderer,err:=newRouterWithOptions(files,handlerOptions{});if err!=nil{t.Fatal(err)}
		found:=false;for _,route:=range routes.Export(mux){if route.Name=="templ"{found=true;if route.Template!="sample.templ"||route.Path!="/templ"{t.Fatal("actual templ route metadata differs")}}};if !found{t.Fatal("actual mux omitted templ route")}
		for _,row:=range sampleEngineReport(renderer){if row.Route=="templ"&&row.Mode!="Templ"{t.Fatal("templ engine report wrong")};if row.Route!="templ"&&row.Mode!="Pongo2"{t.Fatal("S0a sample enabled runtime templ kit")}}
	}
}

func TestSamplePongoAndCompiledTemplFailuresAreAtomic(t *testing.T) {
	w:=httptest.NewRecorder()
	broken:=templ.ComponentFunc(func(ctx context.Context,w io.Writer)error{_,_=io.WriteString(w,"PRIVATE PARTIAL TEMPLATE");return context.Canceled})
	if err:=renderComponentPage(context.Background(),w,broken);err==nil||w.Code!=500||w.Body.String()!="template render failed\n"{t.Fatalf("templ non-atomic failure: %d %q",w.Code,w.Body.String())}
	files:=fstest.MapFS{"broken.html":{Data:[]byte(`PRIVATE PARTIAL PONGO {{ fail() }}`)}}
	e,err:=engine.New(files,engine.Options{});if err!=nil{t.Fatal(err)}
	w=httptest.NewRecorder();err=e.Render(context.Background(),w,engine.Page{Template:"broken.html",Data:map[string]any{"fail":func()(string,error){return "",context.Canceled}}})
	if err==nil||w.Code!=500||w.Body.String()!="template render failed\n"{t.Fatalf("Pongo2 non-atomic failure: %d %q",w.Code,w.Body.String())}
}

func TestBehaviorJSONScriptEscapesAndRequiresNonce(t *testing.T) {
	payload:="</script><script>bad()</script> & \"quoted\" \u2028\u2029"
	var out bytes.Buffer
	if err:=sampleJSONScript("fixture-props",map[string]any{"payload":payload}).Render(csp.WithNonce(context.Background(),"fixture-nonce"),&out);err!=nil{t.Fatal(err)}
	if strings.Count(out.String(),"<script")!=1||strings.Contains(out.String(),"<script>bad()"){t.Fatal("JSON created an executable script sink")}
	doc,err:=html.Parse(strings.NewReader(out.String()));if err!=nil{t.Fatal(err)}
	var value map[string]string;var walk func(*html.Node);walk=func(n *html.Node){if n.Type==html.ElementNode&&n.Data=="script"{if err:=json.Unmarshal([]byte(n.FirstChild.Data),&value);err!=nil{t.Fatal(err)}};for c:=n.FirstChild;c!=nil;c=c.NextSibling{walk(c)}};walk(doc)
	if value["payload"]!=payload{t.Fatal("JSON escaping changed props")}
	out.Reset();if err:=sampleJSONScript("fixture-props",nil).Render(context.Background(),&out);err==nil||out.Len()!=0{t.Fatal("missing nonce emitted JSON")}
}
