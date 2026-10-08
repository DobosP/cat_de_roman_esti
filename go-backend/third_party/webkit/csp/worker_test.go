package csp

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/a-h/templ"
)

func TestWorkerSourcesDefaultSelfAndExplicitBlob(t *testing.T) {
	for _, reportOnly := range []bool{false,true} {
		for _, tc := range []struct { sources []string; expected string }{
			{nil,"worker-src 'self'"},
			{[]string{"blob:"},"worker-src 'self' blob:"},
		} {
			called := false
			h := Middleware(Policy{ReportOnly:reportOnly,WorkerSrc:tc.sources})(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request) {
				called=true
				key := "Content-Security-Policy"
				if reportOnly {key="Content-Security-Policy-Report-Only"}
				header := w.Header().Get(key)
				found := ""
				for _, directive := range strings.Split(header,";") {if strings.HasPrefix(strings.TrimSpace(directive),"worker-src "){found=strings.TrimSpace(directive)}}
				if found != tc.expected {t.Fatalf("worker policy: %q",found)}
				nonce := Nonce(r.Context())
				if nonce=="" || nonce!=templ.GetNonce(r.Context()) || !strings.Contains(header,"script-src 'self' 'nonce-"+nonce+"' 'strict-dynamic'") || !strings.Contains(header,"style-src 'self' 'nonce-"+nonce+"'") {t.Fatal("worker policy changed shared nonce")}
				if reportOnly && strings.Count(header,"report-uri ")!=1 {t.Fatal("duplicate report-uri fix was lost")}
				if !strings.Contains(w.Header().Get("Content-Security-Policy-Report-Only"),"require-trusted-types-for 'script'") {t.Fatal("Trusted Types report-only policy was lost")}
			}))
			w := httptest.NewRecorder();h.ServeHTTP(w,httptest.NewRequest("GET","/",nil))
			if !called || w.Code!=200 {t.Fatalf("valid worker policy failed: %d",w.Code)}
		}
	}
}

func TestWorkerSourceInjectionFailsBeforeHandler(t *testing.T) {
	for _, value := range []string{"", "blob:; script-src 'unsafe-inline'", "https://worker.example\r\nimg-src *", "'unsafe-inline'", "'nonce-forged'"} {
		called := false
		h := Middleware(Policy{WorkerSrc:[]string{value}})(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){called=true}))
		w := httptest.NewRecorder();h.ServeHTTP(w,httptest.NewRequest("GET","/",nil))
		if w.Code!=500 || called {t.Fatal("invalid worker source reached handler")}
	}
}

func TestEveryHeaderInputRejectsControlsAndMixedCaseForbiddenSources(t *testing.T) {
    for _,value:=range []string{"'UNSAFE-INLINE'","'NoNcE-forged'","https://worker.example\x00","https://worker.example\x7f","https://worker.example\f","https://worker.example\u00a0","https://worker.example\u0085"} {
        for _,policy:=range []Policy{{WorkerSrc:[]string{value}},{ConnectSrc:[]string{value}},{ImgSrc:[]string{value}},{FontSrc:[]string{value}}} {
            called:=false;w:=httptest.NewRecorder();Middleware(policy)(http.HandlerFunc(func(http.ResponseWriter,*http.Request){called=true})).ServeHTTP(w,httptest.NewRequest("GET","/",nil));if w.Code!=500||called {t.Fatalf("unsafe source reached handler: %q",value)}
        }
    }
    for _,value:=range []string{"\x00","\x7f","\f","\u00a0","\u0085"} {
        for _,policy:=range []Policy{{ReportPath:"/csp"+value},{TrustedTypes:[]string{"roedu"+value}}} {
            called:=false;w:=httptest.NewRecorder();Middleware(policy)(http.HandlerFunc(func(http.ResponseWriter,*http.Request){called=true})).ServeHTTP(w,httptest.NewRequest("GET","/",nil));if w.Code!=500||called {t.Fatal("unsafe header input reached handler")}
        }
    }
}
