// Package golden canonicalizes browser DOMs without hiding visible changes.
package golden

import (
	"bytes"
	"encoding/json"
	"fmt"
	stdhtml "html"
	"io"
	"net/url"
	"regexp"
	"sort"
	"strings"

	"golang.org/x/net/html"
)

// Options limits masking to explicitly known data. Assets maps manifest URLs
// to entry names. Oracle allows an empty URL only at the same DOM location and
// attribute as an empty URL in the committed oracle; default is fail-closed.
type Options struct {
	Assets map[string]string
	Oracle []byte
}

var spaces=regexp.MustCompile(`[ \t\r\n\f]+`)
var void=wordSet("area base br col embed hr img input link meta param source track wbr")
var block=wordSet("address article aside blockquote body dd details dialog div dl dt fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 header hgroup hr html li main menu nav ol p pre section summary table tbody td tfoot th thead tr ul")
var boolean=wordSet("allowfullscreen async autofocus autoplay checked controls default defer disabled formnovalidate hidden inert ismap itemscope loop multiple muted nomodule novalidate open playsinline readonly required reversed selected")
var urlAttrs=wordSet("src href action formaction poster")
func wordSet(words string) map[string]bool {out:=map[string]bool{};for _,word:=range strings.Fields(words){out[word]=true};return out}
func attr(n *html.Node,name string) string {for _,a:=range n.Attr{if strings.EqualFold(a.Key,name){return a.Val}};return ""}

// Normalize parses the browser DOM, sorts attributes and decodes entities.
// Hard findings are returned independently of equality and never masked.
func Normalize(input []byte,o Options) ([]byte,[]string) {
	root,err:=html.Parse(bytes.NewReader(input));if err!=nil{return nil,[]string{"HTML parse: "+err.Error()}}
	allowedEmpty:=map[string]bool{}
	if len(o.Oracle)>0 {
		oracle,err:=html.Parse(bytes.NewReader(o.Oracle));if err!=nil{return nil,[]string{"oracle HTML parse: "+err.Error()}}
		walkPaths(oracle,"",func(n *html.Node,path string){if n.Type==html.ElementNode{for _,a:=range n.Attr{if urlAttrs[strings.ToLower(a.Key)] && a.Val==""{allowedEmpty[path+"@"+strings.ToLower(a.Key)]=true}}}})
	}
	var hard []string
	check:=func(value,path string) {
		if strings.Contains(value,"about:invalid#TemplFailedSanitizationURL"){hard=append(hard,"failed URL sanitization at "+path)}
		if strings.Contains(value,"{%") || strings.Contains(value,"{{"){hard=append(hard,"template syntax leak at "+path)}
	}
	walkPaths(root,"",func(n *html.Node,path string){
		if n.Type==html.TextNode || n.Type==html.CommentNode {check(n.Data,path)}
		if n.Type==html.ElementNode {for _,a:=range n.Attr {name:=strings.ToLower(a.Key);check(a.Val,path+"@"+name);if urlAttrs[name] && a.Val=="" && !allowedEmpty[path+"@"+name] {hard=append(hard,"empty URL at "+path+"@"+name)}}}
	})
	var out bytes.Buffer
	var serialize func(*html.Node,string)
	serialize=func(n *html.Node,path string) {
		switch n.Type {
		case html.DocumentNode:
			for child:=n.FirstChild;child!=nil;child=child.NextSibling {serialize(child,nodePath(path,child))}
		case html.DoctypeNode:
			out.WriteString("<!doctype "+strings.ToLower(n.Data)+">")
		case html.CommentNode:
			out.WriteString("<!--"+n.Data+"-->")
		case html.TextNode:
			parent:="";if n.Parent!=nil{parent=strings.ToLower(n.Parent.Data)}
			if parent=="script" || parent=="style" {out.WriteString(n.Data);return}
			if parent=="pre" || parent=="textarea" || ancestor(n,"pre") {out.WriteString(stdhtml.EscapeString(n.Data));return}
			if strings.Trim(n.Data," \t\r\n\f")=="" && dropGap(n){return}
			out.WriteString(stdhtml.EscapeString(spaces.ReplaceAllString(n.Data," ")))
		case html.ElementNode:
			name:=strings.ToLower(n.Data)
			out.WriteByte('<');out.WriteString(name)
			attrs:=append([]html.Attribute{},n.Attr...)
			for i:=range attrs {attrs[i].Key=strings.ToLower(attrs[i].Key)}
			sort.SliceStable(attrs,func(i,j int)bool {left,right:=attrs[i].Namespace+":"+attrs[i].Key,attrs[j].Namespace+":"+attrs[j].Key;if left!=right{return left<right};return attrs[i].Val<attrs[j].Val})
			for _,a:=range attrs {
				key:=a.Key;if a.Namespace!=""{key=a.Namespace+":"+key}
				out.WriteByte(' ');out.WriteString(key)
				if boolean[a.Key] {continue}
				value:=a.Val
				if a.Key=="nonce" {value="{nonce}"} else if a.Key=="value" && name=="input" && attr(n,"name")=="csrfmiddlewaretoken" {value="{csrf}"} else {value=maskAsset(value,o.Assets)}
				out.WriteString(`="`);out.WriteString(stdhtml.EscapeString(value));out.WriteByte('"')
			}
			out.WriteByte('>')
			if void[name]{return}
			if name=="script" && strings.EqualFold(attr(n,"type"),"application/json") {
				var raw strings.Builder;for child:=n.FirstChild;child!=nil;child=child.NextSibling{raw.WriteString(child.Data)}
				var value any;decoder:=json.NewDecoder(strings.NewReader(raw.String()));decoder.UseNumber()
				if err:=decoder.Decode(&value);err!=nil {hard=append(hard,"invalid JSON script at "+path);out.WriteString(raw.String())} else {
					if err:=ensureJSONEnd(decoder);err!=nil{hard=append(hard,"invalid JSON script at "+path)}
					maskJSONCSRF(value);canonical,err:=json.Marshal(value);if err!=nil{hard=append(hard,"invalid JSON script at "+path)};out.Write(canonical)
				}
			} else {for child:=n.FirstChild;child!=nil;child=child.NextSibling{serialize(child,nodePath(path,child))}}
			out.WriteString("</"+name+">")
		}
	}
	serialize(root,"")
	sort.Strings(hard);hard=unique(hard)
	return out.Bytes(),hard
}

func ensureJSONEnd(decoder *json.Decoder) error {var extra any;if err:=decoder.Decode(&extra);err!=nil {if err==io.EOF {return nil};return err};return fmt.Errorf("trailing JSON")}
func unique(values []string) []string {out:=values[:0];for _,value:=range values{if len(out)==0||out[len(out)-1]!=value{out=append(out,value)}};return out}
func ancestor(n *html.Node,tag string) bool {for p:=n.Parent;p!=nil;p=p.Parent{if p.Type==html.ElementNode&&strings.EqualFold(p.Data,tag){return true}};return false}
func dropGap(n *html.Node) bool {
	if n.Parent!=nil && (n.Parent.Data=="head" || n.Parent.Type==html.DocumentNode) {return true}
	left,right:=n.PrevSibling,n.NextSibling
	for left!=nil&&left.Type==html.CommentNode{left=left.PrevSibling};for right!=nil&&right.Type==html.CommentNode{right=right.NextSibling}
	isBlock:=func(node *html.Node)bool{return node!=nil&&node.Type==html.ElementNode&&block[strings.ToLower(node.Data)]}
	return (left==nil||isBlock(left)) && (right==nil||isBlock(right)) && (left!=nil||right!=nil)
}
func nodePath(parent string,n *html.Node) string {
	if n.Type!=html.ElementNode{return parent}
	index:=0;for prev:=n.PrevSibling;prev!=nil;prev=prev.PrevSibling {if prev.Type==html.ElementNode&&prev.Data==n.Data {index++}}
	return fmt.Sprintf("%s/%s[%d]",parent,strings.ToLower(n.Data),index)
}
func walkPaths(n *html.Node,path string,visit func(*html.Node,string)) {
	path=nodePath(path,n);visit(n,path);for child:=n.FirstChild;child!=nil;child=child.NextSibling{walkPaths(child,path,visit)}
}
func maskAsset(value string,assets map[string]string) string {
	if entry,ok:=assets[value];ok{return "{asset:"+entry+"}"}
	parsed,err:=url.Parse(value);if err==nil&&parsed.Scheme==""&&parsed.Host=="" {if entry,ok:=assets[parsed.Path];ok {out:="{asset:"+entry+"}";if parsed.RawQuery!="" {out+="?"+parsed.RawQuery};if parsed.Fragment!="" {out+="#"+parsed.Fragment};return out}}
	return value
}
func maskJSONCSRF(value any) {
	switch v:=value.(type) {case map[string]any:for key,item:=range v {if key=="csrf" {v[key]="{csrf}"} else {maskJSONCSRF(item)}};case []any:for _,item:=range v{maskJSONCSRF(item)}}
}

// Report records a first differing byte and compact context. Equal is true
// only for identical canonical bytes; hard findings must be checked separately.
type Report struct {Offset int `json:"offset"`;Want string `json:"want"`;Got string `json:"got"`}
func Diff(want,got []byte) (Report,bool) {
	if bytes.Equal(want,got){return Report{},true}
	index:=0;for index<len(want)&&index<len(got)&&want[index]==got[index]{index++}
	context:=func(value []byte)string{start:=index-40;if start<0{start=0};end:=index+80;if end>len(value){end=len(value)};return string(value[start:end])}
	return Report{Offset:index,Want:context(want),Got:context(got)},false
}
