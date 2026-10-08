package island

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"strings"
	"testing"

	"github.com/a-h/templ"
	"github.com/DobosP/roedu-ui/web-kit/csp"
	"golang.org/x/net/html"
)

func TestLoaderMarkupContract(t *testing.T) {
	ctx:=WithIDs(csp.WithNonce(context.Background(),"request-nonce"))
	props:=map[string]any{"text":"</script><script>alert(1)</script>","count":3}
	var out bytes.Buffer
	if err:=Island("stress",Options{Props:props,Load:"visible",Skeleton:templ.ComponentFunc(func(ctx context.Context,w io.Writer) error { _,err:=io.WriteString(w,"<p>Server skeleton</p>");return err })}).Render(ctx,&out);err!=nil { t.Fatal(err) }
	root,err:=html.Parse(strings.NewReader(out.String()));if err!=nil { t.Fatal(err) }
	var host,script *html.Node
	var walk func(*html.Node);walk=func(n *html.Node) { if n.Type==html.ElementNode { if n.Data=="div" {host=n};if n.Data=="script" { if script!=nil {t.Fatal("script breakout")};script=n } };for c:=n.FirstChild;c!=nil;c=c.NextSibling {walk(c)} };walk(root)
	attr:=func(n *html.Node,key string) string {for _,a:=range n.Attr {if a.Key==key{return a.Val}};return ""}
	if host==nil || script==nil {t.Fatal("loader host or JSON script missing")}
	if attr(host,"data-island")!="stress" || attr(host,"data-load")!="visible" || attr(host,"data-props")!=attr(script,"id") || attr(script,"type")!="application/json" || attr(script,"nonce")!="request-nonce" {t.Fatal("npm loader selector contract diverged")}
	var decoded map[string]any;if err:=json.Unmarshal([]byte(script.FirstChild.Data),&decoded);err!=nil || decoded["text"]!=props["text"] || decoded["count"]!=float64(3) {t.Fatal("JSON payload changed")}
	out.Reset();if err:=Island("stress",props).Render(ctx,&out);err!=nil {t.Fatal(err)}
	if !strings.Contains(out.String(),`data-props="roedu-props-2"`) {t.Fatal("duplicate props ID")}
}

func TestIslandFailsClosedAndKillSwitch(t *testing.T) {
	ctx:=csp.WithNonce(context.Background(),"nonce")
	for _,component:=range []templ.Component{Island("<unsafe>",nil),Island("safe",Options{Load:"invalid"}),Island("safe",make(chan int)),Island("safe",Options{Legacy:"//other/script.js"}),Island("safe",Options{ID:"bad id"})} {
		var out bytes.Buffer;if err:=component.Render(ctx,&out);err==nil || out.Len()!=0 {t.Fatal("invalid island wrote markup")}
	}
	var out bytes.Buffer;if err:=Island("safe",nil).Render(context.Background(),&out);err==nil {t.Fatal("missing nonce accepted")}
	skeleton:=templ.ComponentFunc(func(ctx context.Context,w io.Writer) error {_,err:=io.WriteString(w,"<p>Fallback</p>");return err})
	if err:=Island("safe",Options{Disabled:true,Skeleton:skeleton}).Render(context.Background(),&out);err!=nil || out.String()!="<p>Fallback</p>" {t.Fatal("kill switch did not preserve skeleton")}
}
