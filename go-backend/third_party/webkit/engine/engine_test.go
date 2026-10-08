package engine

import (
	"context"
	"net/http/httptest"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/DobosP/roedu-ui/web-kit/csp"
	"github.com/DobosP/roedu-ui/web-kit/routes"
)

func TestAtomicPongoRenderAndEmbeddedIncludes(t *testing.T) {
	files:=fstest.MapFS{"templates/home.html":{Data:[]byte(`<h1>{{ title }}</h1>{% include "nonce.html" %}`)},"templates/nonce.html":{Data:[]byte(`<script nonce="{{ request.csp_nonce }}" src="/app.js"></script>`)},"templates/broken.html":{Data:[]byte(`PRIVATE PARTIAL BODY {{ fail() }}`)}}
	e,err:=New(files,Options{TemplateRoot:"templates",Routes:[]routes.Route{{Name:"home",Method:"GET",Path:"/",Group:"G0"}}});if err!=nil {t.Fatal(err)}
	ctx:=csp.WithNonce(context.Background(),"nonce")
	w:=httptest.NewRecorder();if err:=e.Render(ctx,w,Page{Route:"home",Template:"home.html",Data:map[string]any{"title":"<Title>"}});err!=nil {t.Fatal(err)}
	if w.Code!=200 || !strings.Contains(w.Body.String(),"&lt;Title&gt;") || !strings.Contains(w.Body.String(),`nonce="nonce"`) {t.Fatalf("render %d %q",w.Code,w.Body.String())}
	w=httptest.NewRecorder();err=e.Render(ctx,w,Page{Route:"home",Template:"broken.html",Data:map[string]any{"fail":func()(string,error){return "",context.Canceled}}})
	if err==nil || w.Code!=500 || strings.Contains(w.Body.String(),"PRIVATE PARTIAL BODY") || w.Body.String()!="template render failed\n" {t.Fatalf("non-atomic failure %d %q %v",w.Code,w.Body.String(),err)}
	if report:=e.Report();len(report)!=1 || report[0].Mode!="Pongo2" {t.Fatal("engine report wrong")}
}

func TestRegistryPongoOnlyAndColumns(t *testing.T) {
	table:=[]routes.Route{{Name:"home"},{Name:"about"}}
	good:=`{"schema":1,"default":{"test":"Pongo2","prod":"Pongo2"},"groups":{"G0":{"test":"Pongo2","prod":"Pongo2","routes":["home"]}},"routes":{"about":{"test":"Pongo2","prod":"Pongo2"}}}`
	r,err:=Load([]byte(good),Env{Column:"unknown",Off:"G0",Routes:table});if err!=nil {t.Fatal(err)}
	if mode,source:=r.Resolve("home");mode!=Pongo2 || source!=EnvOff {t.Fatal("off precedence wrong")};if _,source:=r.Resolve("about");source!=RouteSource {t.Fatal("route precedence wrong")}
	for _,bad:=range []string{strings.Replace(good,`"prod":"Pongo2"`,`"prod":"Templ"`,1),strings.Replace(good,`"prod":"Pongo2"`,`"prod":"Unknown"`,1),strings.Replace(good,`"test":"Pongo2",`,"",1),strings.Replace(good,`["home"]`,`["missing"]`,1),good+` {}`,good+` garbage`} {
		if _,err:=Load([]byte(bad),Env{Routes:table});err==nil {t.Fatalf("accepted invalid config %s",bad)}
	}
	if _,err:=Load([]byte(good),Env{Routes:table,Off:"missing"});err==nil {t.Fatal("unknown override ignored")}
	if _,err:=Load([]byte(good),Env{Routes:table,On:"home"});err==nil {t.Fatal("Templ enabled before S0b")}
}
