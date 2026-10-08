package routes

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRouteExportMatchesServer(t *testing.T) {
	m:=NewMux()
	for _,route:=range []Route{{Name:"home",Method:"GET",Path:"/{$}",Template:"home.html",Group:"G0"},{Name:"about",Method:"GET",Path:"/about",Template:"about.html",Group:"G0"}} {
		if err:=m.Handle(route,http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){w.WriteHeader(200)}));err!=nil {t.Fatal(err)}
	}
	routes:=Export(m);if len(routes)!=2 || routes[0].Name!="about" || routes[1].Name!="home" {t.Fatal("export order wrong")}
	routes[0].Name="mutated";if Export(m)[0].Name!="about" {t.Fatal("export aliases mux")}
	w:=httptest.NewRecorder();m.ServeHTTP(w,httptest.NewRequest("GET","/about",nil));if w.Code!=200 {t.Fatal("exported route missing from server")}
	if err:=m.Handle(Route{Name:"home",Method:"GET",Path:"/other"},http.NotFoundHandler());err==nil {t.Fatal("duplicate name accepted")}
	if err:=m.Handle(Route{Name:"collision",Method:"GET",Path:"/about"},http.NotFoundHandler());err==nil || len(Export(m))!=2 {t.Fatal("conflicting pattern entered inventory")}
	if len(Export(Table{{Name:"x",Method:"GET",Path:"/x"}}))!=1 {t.Fatal("manifest adapter failed")}
}
