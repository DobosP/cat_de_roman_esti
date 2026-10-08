package assets

import (
	"bytes"
	"context"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/DobosP/roedu-ui/web-kit/csp"
)

func fixture() fstest.MapFS { return fstest.MapFS{
	"dist/.vite/manifest.json":{Data:[]byte(`{"main":{"file":"assets/main-12345678.js","isEntry":true,"imports":["dep"],"css":["assets/main-12345678.css"]},"dep":{"file":"assets/dep-abcdefgh.js","css":["assets/main-12345678.css"]}}`)},
	"dist/assets/main-12345678.js":{Data:[]byte("main")},"dist/assets/dep-abcdefgh.js":{Data:[]byte("dep")},"dist/assets/main-12345678.css":{Data:[]byte("css")},
} }

func TestTagsManifestAndNonce(t *testing.T) {
	m,err:=Parse(fixture(),"dist/.vite/manifest.json","dist","/static/"); if err!=nil { t.Fatal(err) }
	ctx:=WithManifest(csp.WithNonce(context.Background(),"test-nonce"),m)
	var out bytes.Buffer; if err:=Tags(ctx,"main").Render(ctx,&out);err!=nil { t.Fatal(err) }
	s:=out.String()
	if strings.Count(s,`rel="stylesheet"`)!=1 || !strings.Contains(s,`rel="modulepreload"`) || strings.Count(s,`nonce="test-nonce"`)!=4 || !strings.Contains(s,`type="module"`) { t.Fatalf("tags: %s",s) }
	if strings.Count(s,`<meta property="csp-nonce" content="test-nonce" nonce="test-nonce">`) != 1 { t.Fatal("exact nonce meta missing or duplicated") }
	if m.Static("main")!="/static/assets/main-12345678.js" || m.Static("../secret")!="" || m.Static("missing.js")!="" { t.Fatal("Static resolution wrong") }
	if m.Masks()["/static/assets/main-12345678.js"]!="main" { t.Fatal("asset mask missing") }
	out.Reset(); ctx=WithManifest(context.Background(),m)
	if err:=Tags(ctx,"main").Render(ctx,&out);err==nil || out.Len()!=0 { t.Fatal("missing nonce wrote tags") }
	ctx=csp.WithNonce(ctx,"test"); if err:=Tags(ctx,"unknown").Render(ctx,&out);err==nil { t.Fatal("unknown entry accepted") }
}

func TestMalformedManifestFails(t *testing.T) {
	for _,manifest:=range []string{`{}`,`{"main":{"file":"../secret"}}`,`{"main":{"file":"missing.js"}}`,`{"main":{"file":"assets/main-12345678.js","imports":["missing"]}}`,`{`} {
		files:=fixture();files["dist/.vite/manifest.json"]=&fstest.MapFile{Data:[]byte(manifest)}
		if _,err:=Parse(files,"dist/.vite/manifest.json","dist","/static/");err==nil { t.Fatalf("accepted %s",manifest) }
	}
	if _,err:=Parse(fixture(),"dist/.vite/manifest.json","dist","//evil/");err==nil { t.Fatal("cross-origin prefix accepted") }
}
