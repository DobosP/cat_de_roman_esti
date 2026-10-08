package golden

import (
	"bytes"
	"strings"
	"testing"
)

func normalize(t *testing.T,input string,o Options) []byte {t.Helper();out,hard:=Normalize([]byte(input),o);if len(hard)>0{t.Fatalf("unexpected hard findings: %v",hard)};return out}
func TestCanonicalDOM(t *testing.T) {
	left:=`<!DOCTYPE html><HTML><HEAD><title>Page</title></HEAD><BODY><input disabled="disabled" class="x" checked="checked"><p title="&mdash;">a &mdash; b &amp; c</p></BODY></HTML>`
	right:=`<!doctype html><html><head>
<title>Page</title>
</head><body><input checked class="x" disabled/><p title="—">a — b &amp; c</p></body></html>`
	if !bytes.Equal(normalize(t,left,Options{}),normalize(t,right,Options{})){t.Fatal("attribute/entity/void normalization diverged")}
}
func TestWhitespacePresence(t *testing.T) {
	inlineGap:=normalize(t,"<p><img src=\"/x.png\">\n<a href=\"/a\">link</a></p>",Options{})
	inlineNone:=normalize(t,"<p><img src=\"/x.png\"><a href=\"/a\">link</a></p>",Options{})
	if bytes.Equal(inlineGap,inlineNone){t.Fatal("visible img-newline-a gap was erased")}
	if !bytes.Equal(normalize(t,"<div>\n<p>A</p>\n<p>B</p>\n</div>",Options{}),normalize(t,"<div><p>A</p><p>B</p></div>",Options{})){t.Fatal("inter-block whitespace retained")}
	if !bytes.Equal(normalize(t,"<p> a\n\t b </p>",Options{}),normalize(t,"<p> a b </p>",Options{})){t.Fatal("text-run collapse wrong")}
	if bytes.Equal(normalize(t,"<p> a </p>",Options{}),normalize(t,"<p>a</p>",Options{})){t.Fatal("leading/trailing presence erased")}
	if bytes.Equal(normalize(t,"<pre>a  b\n</pre>",Options{}),normalize(t,"<pre>a b</pre>",Options{})){t.Fatal("preformatted content changed")}
}
func TestMasksOnlyKnownAttributesAndJSONCSRF(t *testing.T) {
	o:=Options{Assets:map[string]string{"/static/app-1234abcd.js":"app","/static/app-5678abcd.js":"app"}}
	left:=`<script src="/static/app-1234abcd.js" nonce="first"></script><input name="csrfmiddlewaretoken" value="one"><script type="application/json" nonce="first">{"b":2,"csrf":"one","a":{"csrf":"nested"}}</script><p>nonce first /static/app-1234abcd.js</p>`
	right:=`<script nonce="second" src="/static/app-5678abcd.js"></script><input value="two" name="csrfmiddlewaretoken"><script nonce="second" type="application/json">{"a":{"csrf":"new"},"csrf":"two","b":2}</script><p>nonce first /static/app-1234abcd.js</p>`
	if !bytes.Equal(normalize(t,left,o),normalize(t,right,o)){t.Fatal("known mask or sorted JSON failed")}
	changed:=strings.Replace(right,"nonce first /static/app-1234abcd.js","nonce second /static/app-5678abcd.js",1)
	if bytes.Equal(normalize(t,left,o),normalize(t,changed,o)){t.Fatal("text content was masked")}
	changed=strings.Replace(right,`"b":2`,`"b":3`,1)
	if bytes.Equal(normalize(t,left,o),normalize(t,changed,o)){t.Fatal("non-CSRF JSON was masked")}
}
func TestHardFindingsAndOracleEmptyURLs(t *testing.T) {
	for _,input:=range []string{`<a href="about:invalid#TemplFailedSanitizationURL">x</a>`,`<p>{{ user }}</p>`,`<p>{% if x %}</p>`,`<img src="">`,`<a href="">x</a>`,`<form action=""></form>`,`<script type="application/json">{broken}</script>`} {
		if _,hard:=Normalize([]byte(input),Options{});len(hard)==0{t.Fatalf("hard error ignored: %s",input)}
	}
	o:=Options{Oracle:[]byte(`<a href="">same documented empty URL</a>`)}
	if _,hard:=Normalize([]byte(`<a href="">same documented empty URL</a>`),o);len(hard)!=0{t.Fatalf("oracle URL rejected %v",hard)}
	if _,hard:=Normalize([]byte(`<a href=""></a><a href=""></a>`),o);len(hard)!=1{t.Fatalf("new empty URL missed %v",hard)}
}
func TestEveryMutationDiffs(t *testing.T) {
	base:=`<main><p class="answer" data-state="yes">One</p><a href="/two">Two</a></main>`
	want:=normalize(t,base,Options{})
	mutations:=map[string]string{
		"drop-attribute":strings.Replace(base,` class="answer"`,"",1),
		"flip-branch":strings.Replace(base,`data-state="yes"`,`data-state="no"`,1),
		"one-character":strings.Replace(base,"One","Ona",1),
		"swap-siblings":`<main><a href="/two">Two</a><p class="answer" data-state="yes">One</p></main>`,
	}
	for name,input:=range mutations {t.Run(name,func(t *testing.T){got:=normalize(t,input,Options{});report,equal:=Diff(want,got);if equal||report.Want==report.Got{t.Fatal("mutation produced no diff")}})}
}
