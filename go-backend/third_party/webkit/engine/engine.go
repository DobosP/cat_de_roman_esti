// Package engine is the S0a atomic Pongo2 renderer. Templ and Shadow modes are
// reserved contract values; S0b supplies their implementation.
package engine

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"net/http"
	"sort"
	"strings"

	"github.com/a-h/templ"
	"github.com/flosch/pongo2/v6"
	"github.com/DobosP/roedu-ui/web-kit/csp"
	"github.com/DobosP/roedu-ui/web-kit/island"
	"github.com/DobosP/roedu-ui/web-kit/routes"
)

type Mode int
const (Pongo2 Mode=iota; Templ; Shadow)
func (m Mode) String() string {switch m {case Pongo2:return "Pongo2";case Templ:return "Templ";case Shadow:return "Shadow"};return "Unknown"}
type Source string
const (EnvOff Source="env-off";EnvOn Source="env-on";RouteSource Source="route";GroupSource Source="group";DefaultSource Source="default")
type Env struct {Column string;On,Off string;Routes []routes.Route}
type Registry struct {def Mode;byGroup,byRoute map[string]Mode;groupOf map[string]string;known map[string]bool;off map[string]bool}
type column struct {Test string `json:"test"`;Prod string `json:"prod"`}
type group struct {Test string `json:"test"`;Prod string `json:"prod"`;Routes []string `json:"routes"`}
type config struct {Schema int `json:"schema"`;Default column `json:"default"`;Groups map[string]group `json:"groups"`;Routes map[string]column `json:"routes"`}

func parseMode(mode string) (Mode,error) {
	switch mode {case "Pongo2":return Pongo2,nil;case "Templ","Shadow":return Pongo2,fmt.Errorf("mode %s requires the S0b templ kit",mode);default:return Pongo2,fmt.Errorf("unknown engine mode %q",mode)}
}

// Load validates both explicit environment columns and the authoritative route
// table. Unknown environment names select production. S0a rejects every mode
// except Pongo2 instead of silently serving another engine.
func Load(static []byte,env Env) (*Registry,error) {
	var cfg config
	decoder:=json.NewDecoder(bytes.NewReader(static));decoder.DisallowUnknownFields()
	if err:=decoder.Decode(&cfg);err!=nil {return nil,err}
	if err:=decoder.Decode(new(any));err!=io.EOF {return nil,fmt.Errorf("trailing engine configuration")}
	if cfg.Schema!=1 {return nil,fmt.Errorf("engine schema must be 1")}
	validate:=func(c column)(Mode,error) {
		if c.Test=="" || c.Prod=="" {return Pongo2,fmt.Errorf("engine requires explicit test and prod columns")}
		if _,err:=parseMode(c.Test);err!=nil{return Pongo2,err};if _,err:=parseMode(c.Prod);err!=nil{return Pongo2,err}
		if env.Column=="test" {return parseMode(c.Test)};return parseMode(c.Prod)
	}
	def,err:=validate(cfg.Default);if err!=nil{return nil,err}
	r:=&Registry{def:def,byGroup:map[string]Mode{},byRoute:map[string]Mode{},groupOf:map[string]string{},known:map[string]bool{},off:map[string]bool{}}
	for _,route:=range env.Routes {if route.Name=="" || r.known[route.Name] {return nil,fmt.Errorf("invalid or duplicate route name")};r.known[route.Name]=true}
	for name,g:=range cfg.Groups {
		if name=="" {return nil,fmt.Errorf("empty engine group")}
		mode,err:=validate(column{g.Test,g.Prod});if err!=nil{return nil,err};r.byGroup[name]=mode
		for _,route:=range g.Routes {if !r.known[route] {return nil,fmt.Errorf("unknown group route %s",route)};if _,ok:=r.groupOf[route];ok {return nil,fmt.Errorf("route in multiple groups: %s",route)};r.groupOf[route]=name}
	}
	for name,c:=range cfg.Routes {if !r.known[name] {return nil,fmt.Errorf("unknown route override %s",name)};mode,err:=validate(c);if err!=nil{return nil,err};r.byRoute[name]=mode}
	checkOverride:=func(value string)([]string,error) {
		var names []string;for _,name:=range strings.Split(value,",") {name=strings.TrimSpace(name);if name==""{continue};if name!="all" && !r.known[name] {if _,ok:=r.byGroup[name];!ok {return nil,fmt.Errorf("unknown engine override %s",name)}};names=append(names,name)};return names,nil
	}
	on,err:=checkOverride(env.On);if err!=nil{return nil,err};if len(on)>0 {return nil,fmt.Errorf("Templ override requires the S0b templ kit")}
	off,err:=checkOverride(env.Off);if err!=nil{return nil,err};for _,name:=range off {r.off[name]=true}
	return r,nil
}

func (r *Registry) Resolve(route string) (Mode,Source) {
	if r==nil{return Pongo2,DefaultSource}
	group:=r.groupOf[route]
	if r.off["all"] || r.off[route] || (group!="" && r.off[group]) {return Pongo2,EnvOff}
	if mode,ok:=r.byRoute[route];ok{return mode,RouteSource};if mode,ok:=r.byGroup[group];ok{return mode,GroupSource};return r.def,DefaultSource
}

type RouteEngine struct {Route string `json:"route"`;Group string `json:"group"`;Mode string `json:"mode"`;Source Source `json:"source"`}
type Page struct {Route,Template string;Data map[string]any;Comp func(context.Context) templ.Component}
type Options struct {TemplateRoot string;Registry *Registry;Routes []routes.Route}
type Engine struct {set *pongo2.TemplateSet;registry *Registry;table []routes.Route}

// NewFSLoader exposes the v6.1 native fs.FS boundary (no disk loader or source
// translator). Restrict its filesystem with fs.Sub before construction.
func NewFSLoader(files fs.FS) *pongo2.FSLoader {return pongo2.NewFSLoader(files)}
func New(files fs.FS,o Options) (*Engine,error) {
	if files==nil{return nil,fmt.Errorf("template filesystem required")}
	if o.TemplateRoot!="" {var err error;files,err=fs.Sub(files,o.TemplateRoot);if err!=nil{return nil,err}}
	return &Engine{set:pongo2.NewSet("webkit",NewFSLoader(files)),registry:o.Registry,table:routes.Export(routes.Table(o.Routes))},nil
}

// Render buffers every byte before touching response headers. A template
// failure returns a generic 500 and never leaks its partial output or context.
func (e *Engine) Render(ctx context.Context,w http.ResponseWriter,p Page) error {
	ctx=island.WithIDs(ctx)
	fail:=func(err error)error {w.Header().Del("Content-Length");http.Error(w,"template render failed",http.StatusInternalServerError);return err}
	if e==nil || e.set==nil{return fail(fmt.Errorf("engine not initialized"))}
	if err:=ctx.Err();err!=nil{return fail(err)}
	if !fs.ValidPath(p.Template) {return fail(fmt.Errorf("invalid template path"))}
	mode,_:=e.registry.Resolve(p.Route);if mode!=Pongo2 {return fail(fmt.Errorf("unsupported engine mode"))}
	template,err:=e.set.FromCache(p.Template);if err!=nil{return fail(err)}
	var body bytes.Buffer
	if err:=template.ExecuteWriterUnbuffered(csp.PongoContext(ctx,p.Data),&body);err!=nil{return fail(err)}
	if err:=ctx.Err();err!=nil{return fail(err)}
	w.Header().Set("Content-Type","text/html; charset=utf-8")
	w.Header().Set("Cache-Control","no-cache")
	_,err=w.Write(body.Bytes());return err
}
func (e *Engine) Report() []RouteEngine {
	out:=make([]RouteEngine,0,len(e.table))
	for _,route:=range e.table {mode,source:=e.registry.Resolve(route.Name);group:=route.Group;if e.registry!=nil {if value:=e.registry.groupOf[route.Name];value!=""{group=value}};out=append(out,RouteEngine{route.Name,group,mode.String(),source})}
	sort.Slice(out,func(i,j int)bool{return out[i].Route<out[j].Route});return out
}
