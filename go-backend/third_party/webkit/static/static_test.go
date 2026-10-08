package static

import (
	"bytes"
	"compress/gzip"
	"io"
	"net/http/httptest"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/vearutop/statigz"
	"github.com/vearutop/statigz/brotli"
)

func TestCompressedAssetsAndCache(t *testing.T) {
	body:=[]byte("console.log('core');")
	var gz bytes.Buffer;z:=gzip.NewWriter(&gz);_,_=z.Write(body);_=z.Close()
	s:=&statigz.Server{};brotli.AddEncoding(s)
	var br []byte;for _,encoding:=range s.Encodings {if encoding.ContentEncoding=="br" {var err error;br,err=encoding.Encoder(bytes.NewReader(body));if err!=nil {t.Fatal(err)}}}
	if len(br)==0 {t.Fatal("Brotli encoder missing")}
	files:=fstest.MapFS{"app-1234abcd.js":{Data:body},"app-1234abcd.js.gz":{Data:gz.Bytes()},"app-1234abcd.js.br":{Data:br},"page.html":{Data:[]byte("<h1>Page</h1>")},".vite/manifest.json":{Data:[]byte("{}")}}
	h:=Handler(files,Options{})
	for _,encoding:=range []string{"gzip","br","zstd",""} {
		r:=httptest.NewRequest("GET","/app-1234abcd.js",nil);r.Header.Set("Accept-Encoding",encoding)
		w:=httptest.NewRecorder();h.ServeHTTP(w,r)
		if w.Code!=200 || !strings.Contains(w.Header().Get("Cache-Control"),"immutable") || w.Header().Get("ETag")=="" {t.Fatalf("asset %s: %d %v",encoding,w.Code,w.Header())}
		if encoding=="gzip" && w.Header().Get("Content-Encoding")!="gzip" {t.Fatal("gzip sidecar not served")}
		if encoding=="br" && w.Header().Get("Content-Encoding")!="br" {t.Fatal("Brotli sidecar not served")}
		if (encoding=="zstd" || encoding=="") && (w.Header().Get("Content-Encoding")!="" || !bytes.Equal(w.Body.Bytes(),body)) {t.Fatal("uncompressed fallback wrong")}
		if encoding=="gzip" {rd,err:=gzip.NewReader(w.Body);if err!=nil {t.Fatal(err)};got,_:=io.ReadAll(rd);_=rd.Close();if !bytes.Equal(got,body){t.Fatal("gzip body differs")}}
	}
	for _,tc:=range []struct{path string;code int}{{"/page.html",200},{"/.vite/manifest.json",404},{"/../secret",404},{"/app-1234abcd.js.zst",404},{"/app-1234abcd.js.gz",404},{"/missing-1234abcd.js",404}} {
		w:=httptest.NewRecorder();h.ServeHTTP(w,httptest.NewRequest("GET",tc.path,nil));if w.Code!=tc.code {t.Fatalf("%s: %d",tc.path,w.Code)}
		if tc.code==200 && w.Header().Get("Cache-Control")!="no-cache" {t.Fatal("HTML cache policy wrong")}
	}
}
