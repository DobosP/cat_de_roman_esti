// Package assets loads an embedded Vite manifest once at startup.
package assets

import (
	"context"
	"embed"
	"encoding/json"
	"fmt"
	"html"
	"io"
	"io/fs"
	"path"
	"sort"
	"strings"
	"sync"
	"sync/atomic"

	"github.com/a-h/templ"
	"github.com/DobosP/roedu-ui/web-kit/csp"
)

type Entry struct {
	File string `json:"file"`
	Src string `json:"src"`
	IsEntry bool `json:"isEntry"`
	CSS []string `json:"css"`
	Imports []string `json:"imports"`
	DynamicImports []string `json:"dynamicImports"`
	Assets []string `json:"assets"`
}

// Manifest is immutable after construction. Use WithManifest for multiple
// manifests in one process; Load also installs the startup default for Static.
type Manifest struct { entries map[string]Entry; filesystem fs.FS; root string; prefix string }
type manifestKey struct{}
var loaded sync.Map
var defaultManifest atomic.Pointer[Manifest]

// Load locates the manifest under the embed layout (or at the FS root), caches
// the parsed value by embed.FS, and rejects dangling or unsafe asset paths.
func Load(files embed.FS) (*Manifest, error) {
	if cached, ok := loaded.Load(files); ok { m := cached.(*Manifest); defaultManifest.Store(m); return m,nil }
	for _, name := range []string{"embedfs/dist/.vite/manifest.json", "embedfs/dist/manifest.json", ".vite/manifest.json", "manifest.json"} {
		if _, err := fs.Stat(files,name); err != nil { continue }
		root := path.Dir(name); if path.Base(root)==".vite" { root=path.Dir(root) }
		m, err := Parse(files,name,root,"/static/")
		if err != nil { return nil,err }
		actual,_ := loaded.LoadOrStore(files,m); m=actual.(*Manifest); defaultManifest.Store(m); return m,nil
	}
	return nil,fmt.Errorf("embedded Vite manifest not found")
}

// Parse is the explicit loader for a caller-controlled fs.FS. Paths in the
// manifest must be relative to root; prefix is a same-origin absolute URL path.
func Parse(files fs.FS, manifestPath, root, prefix string) (*Manifest,error) {
	if files==nil { return nil,fmt.Errorf("nil asset filesystem") }
	if !strings.HasPrefix(prefix,"/") || strings.HasPrefix(prefix,"//") || strings.ContainsAny(prefix,"?\"'<>#\\\r\n") { return nil,fmt.Errorf("invalid asset URL prefix") }
	if !strings.HasSuffix(prefix,"/") { prefix+="/" }
	data,err := fs.ReadFile(files,manifestPath); if err!=nil { return nil,err }
	entries:=map[string]Entry{}
	if err=json.Unmarshal(data,&entries); err!=nil { return nil,fmt.Errorf("asset manifest JSON: %w",err) }
	if len(entries)==0 { return nil,fmt.Errorf("empty asset manifest") }
	m:=&Manifest{entries:entries,filesystem:files,root:root,prefix:prefix}
	for key,e:=range entries {
		if key=="" || e.File=="" { return nil,fmt.Errorf("asset entry missing name or file") }
		for _,file:=range append(append([]string{e.File},e.CSS...),e.Assets...) {
			if !validPath(file) { return nil,fmt.Errorf("unsafe asset path for %s",key) }
			if info,err:=fs.Stat(files,path.Join(root,file)); err!=nil || info.IsDir() { return nil,fmt.Errorf("asset file missing for %s: %s",key,file) }
		}
		for _,dep:=range append(append([]string{},e.Imports...),e.DynamicImports...) { if _,ok:=entries[dep]; !ok { return nil,fmt.Errorf("unknown asset import %s",dep) } }
	}
	return m,nil
}

func validPath(s string) bool { return fs.ValidPath(s) && !strings.ContainsAny(s,"?\"'<>#\\\r\n") }
func WithManifest(ctx context.Context,m *Manifest) context.Context { return context.WithValue(ctx,manifestKey{},m) }
func fromContext(ctx context.Context) *Manifest { if m,ok:=ctx.Value(manifestKey{}).(*Manifest); ok { return m }; return defaultManifest.Load() }

// Entries returns a copy suitable for inspection and golden asset masks.
func (m *Manifest) Entries() map[string]Entry {
	out:=make(map[string]Entry,len(m.entries))
	for k,e:=range m.entries { e.CSS=append([]string{},e.CSS...); e.Imports=append([]string{},e.Imports...); e.DynamicImports=append([]string{},e.DynamicImports...); e.Assets=append([]string{},e.Assets...); out[k]=e }
	return out
}

// Static maps an entry key or existing dist-relative filename to a URL. Invalid
// and unknown paths return empty, which the golden hard-failure check catches.
func Static(name string) string { m:=defaultManifest.Load(); if m==nil { return "" }; return m.Static(name) }
func (m *Manifest) Static(name string) string {
	if e,ok:=m.entries[name]; ok { return m.prefix+e.File }
	if !validPath(name) { return "" }
	if info,err:=fs.Stat(m.filesystem,path.Join(m.root,name)); err!=nil || info.IsDir() { return "" }
	return m.prefix+name
}

// Tags emits each dependency's modulepreload and CSS once, followed by the
// entry module. Every tag carries the request nonce; absence fails closed.
func Tags(ctx context.Context,entry string) templ.Component {
	return templ.ComponentFunc(func(renderCtx context.Context,w io.Writer) error {
		m:=fromContext(ctx); if m==nil { return fmt.Errorf("asset manifest not loaded") }
		e,ok:=m.entries[entry]; if !ok { return fmt.Errorf("unknown asset entry %s",entry) }
		nonce:=csp.Nonce(ctx); if nonce=="" { nonce=csp.Nonce(renderCtx) }; if nonce=="" { return fmt.Errorf("asset tags require CSP nonce") }
		var b strings.Builder
		visited:=map[string]bool{}; css:=map[string]bool{}; nonceAttr:=html.EscapeString(nonce)
		fmt.Fprintf(&b,`<meta property="csp-nonce" content="%s" nonce="%s">`,nonceAttr,nonceAttr)
		var visit func(string) error
		visit=func(key string) error {
			if visited[key] { return nil }; visited[key]=true
			item,ok:=m.entries[key]; if !ok { return fmt.Errorf("unknown import %s",key) }
			for _,dep:=range item.Imports { if err:=visit(dep);err!=nil{return err} }
			for _,file:=range item.CSS { if !css[file] { css[file]=true; fmt.Fprintf(&b,`<link rel="stylesheet" href="%s" nonce="%s">`,html.EscapeString(m.prefix+file),nonceAttr) } }
			if key!=entry { fmt.Fprintf(&b,`<link rel="modulepreload" href="%s" nonce="%s">`,html.EscapeString(m.prefix+item.File),nonceAttr) }
			return nil
		}
		if err:=visit(entry);err!=nil { return err }
		fmt.Fprintf(&b,`<script type="module" src="%s" nonce="%s"></script>`,html.EscapeString(m.prefix+e.File),nonceAttr)
		_,err:=io.WriteString(w,b.String()); return err
	})
}

// Masks maps concrete URLs to stable entry names without touching text nodes.
func (m *Manifest) Masks() map[string]string {
	out:=map[string]string{}
	keys:=make([]string,0,len(m.entries)); for key:=range m.entries { keys=append(keys,key) }; sort.Strings(keys)
	for _,key:=range keys { e:=m.entries[key]; out[m.prefix+e.File]=key; for _,file:=range e.CSS { if _,exists:=out[m.prefix+file]; !exists { out[m.prefix+file]=key+":css" } } }
	return out
}
