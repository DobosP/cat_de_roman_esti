// Package routes exposes named HTTP routes to gates without router internals.
package routes

import (
	"fmt"
	"net/http"
	"sort"
	"strings"
	"sync"
)

type Route struct {
	Name string `json:"name"`
	Method string `json:"method"`
	Path string `json:"path"`
	Template string `json:"template,omitempty"`
	Group string `json:"group,omitempty"`
}

// Source is the explicit adapter boundary for a consumer router. Go's standard
// ServeMux does not expose registrations, so applications supply this method or
// register through Mux. Export never guesses routes by probing URLs.
type Source interface { Routes() []Route }

// Export returns a detached, deterministically sorted route inventory.
func Export(mux Source) []Route {
	if mux==nil { return nil }
	out:=append([]Route{},mux.Routes()...)
	sort.Slice(out,func(i,j int) bool {if out[i].Name!=out[j].Name{return out[i].Name<out[j].Name};if out[i].Method!=out[j].Method{return out[i].Method<out[j].Method};return out[i].Path<out[j].Path})
	return out
}

// Table adapts an existing, authoritative manifest to Source.
type Table []Route
func (t Table) Routes() []Route {return append([]Route{},t...)}

type Mux struct { mux *http.ServeMux; mu sync.RWMutex; table []Route }
func NewMux() *Mux {return &Mux{mux:http.NewServeMux()}}

// Handle validates names and registers the same route in HTTP and the export
// inventory. Conflicting patterns fail without leaving an inventory entry.
func (m *Mux) Handle(route Route,handler http.Handler) (err error) {
	if m==nil || m.mux==nil || handler==nil {return fmt.Errorf("route mux or handler missing")}
	if route.Name=="" || route.Method=="" || route.Path=="" || !strings.HasPrefix(route.Path,"/") || strings.ContainsAny(route.Method," \r\n\t") {return fmt.Errorf("route name, method and absolute path required")}
	m.mu.Lock();defer m.mu.Unlock()
	for _,existing:=range m.table {if existing.Name==route.Name {return fmt.Errorf("duplicate route name %s",route.Name)}}
	defer func(){if value:=recover();value!=nil {err=fmt.Errorf("route registration failed: %v",value)}}()
	m.mux.Handle(route.Method+" "+route.Path,handler)
	m.table=append(m.table,route)
	return nil
}
func (m *Mux) Routes() []Route {m.mu.RLock();defer m.mu.RUnlock();return append([]Route{},m.table...)}
func (m *Mux) ServeHTTP(w http.ResponseWriter,r *http.Request) {m.mux.ServeHTTP(w,r)}
