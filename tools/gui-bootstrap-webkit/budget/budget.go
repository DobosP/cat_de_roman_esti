// Package budget measures route assets against the committed budget file.
package budget

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"math"
	"path"
	"regexp"
	"sort"
	"testing"

	"github.com/DobosP/roedu-ui/web-kit/assets"
	"github.com/DobosP/roedu-ui/web-kit/routes"
)

// Limit never supplies a fallback: LimitGZ=nil means explicit JSON null.
// A missing limit_gz key is an error when loading committed budgets.
type Limit struct {
	LimitGZ *int64 `json:"limit_gz"`
	TargetGZ *int64 `json:"target_gz,omitempty"`
}

func (l *Limit) UnmarshalJSON(data []byte) error {
	var raw map[string]json.RawMessage
	if err := json.Unmarshal(data, &raw); err != nil { return err }
	value, present := raw["limit_gz"]
	if !present { return fmt.Errorf("missing limit_gz") }
	for key := range raw {
		if key != "limit_gz" && key != "target_gz" { return fmt.Errorf("unknown limit field %s", key) }
	}
	if err := json.Unmarshal(value, &l.LimitGZ); err != nil { return err }
	if l.LimitGZ != nil && *l.LimitGZ < 0 { return fmt.Errorf("negative limit_gz") }
	if target, exists := raw["target_gz"]; exists {
		if err := json.Unmarshal(target, &l.TargetGZ); err != nil { return err }
		if l.TargetGZ == nil || *l.TargetGZ < 0 { return fmt.Errorf("invalid target_gz") }
	}
	return nil
}

type RouteBudget struct {
	Class string `json:"class"`
	Islands []string `json:"islands"`
	Widgets []string `json:"widgets"`
}

func (r *RouteBudget) UnmarshalJSON(data []byte) error {
	var raw map[string]json.RawMessage
	if err := json.Unmarshal(data, &raw); err != nil || raw == nil { return fmt.Errorf("route budget must be an object") }
	for _, name := range []string{"class", "islands", "widgets"} {
		value, present := raw[name]
		if !present || bytes.Equal(bytes.TrimSpace(value), []byte("null")) { return fmt.Errorf("route budget requires nonnull %s", name) }
	}
	for name := range raw { if name != "class" && name != "islands" && name != "widgets" { return fmt.Errorf("unknown route budget field %s", name) } }
	if err := json.Unmarshal(raw["class"], &r.Class); err != nil { return err }
	decodeNames := func(data []byte) ([]string, error) {
		var items []json.RawMessage
		if err := json.Unmarshal(data, &items); err != nil { return nil, err }
		values := make([]string, len(items))
		for index, item := range items {
			if bytes.Equal(bytes.TrimSpace(item), []byte("null")) { return nil, fmt.Errorf("route asset names must be strings") }
			if err := json.Unmarshal(item, &values[index]); err != nil { return nil, err }
		}
		return values, nil
	}
	var err error
	if r.Islands, err = decodeNames(raw["islands"]); err != nil { return err }
	if r.Widgets, err = decodeNames(raw["widgets"]); err != nil { return err }
	return nil
}

type Throttle struct {
	CPU float64 `json:"cpu"`
	RTTMS float64 `json:"rtt_ms"`
	DownKbps float64 `json:"down_kbps"`
}

type Vitals struct {
	LCPMS float64 `json:"lcp_ms"`
	INPMS float64 `json:"inp_ms"`
	Throttle Throttle `json:"throttle"`
}

type Budgets struct {
	Schema int
	MeasuredAt *string
	Source string
	Classes map[string]Limit
	Vendors map[string]Limit
	GlobalCSS Limit
	Routes map[string]RouteBudget
	Vitals Vitals
}

func strictJSON(data []byte, value any) error {
	d := json.NewDecoder(bytes.NewReader(data))
	d.DisallowUnknownFields()
	if err := d.Decode(value); err != nil { return err }
	if err := d.Decode(new(any)); err != io.EOF { return fmt.Errorf("trailing JSON data") }
	return nil
}

// Load validates the shipped schema, including its source/measured_at metadata.
// Every byte and vital limit is read from JSON; none is a package constant.
func Load(data []byte) (*Budgets, error) {
	var metadata map[string]json.RawMessage
	if err := json.Unmarshal(data, &metadata); err != nil { return nil, err }
	measured, present := metadata["measured_at"]
	if !present { return nil, fmt.Errorf("measured_at is required") }
	if !bytes.Equal(bytes.TrimSpace(measured), []byte("null")) {
		var sha string
		if err := json.Unmarshal(measured, &sha); err != nil || !regexp.MustCompile(`^(?:[a-f0-9]{40}|[a-f0-9]{64})$`).MatchString(sha) { return nil, fmt.Errorf("measured_at must be null or an actual Git SHA") }
	}
	if source, present := metadata["source"]; present {
		var text string
		if bytes.Equal(bytes.TrimSpace(source), []byte("null")) { return nil, fmt.Errorf("source must be a string when present") }
		if err := json.Unmarshal(source, &text); err != nil { return nil, fmt.Errorf("source must be a string when present") }
	}
	var vitalsFields, throttleFields map[string]json.RawMessage
	if err := json.Unmarshal(metadata["vitals"], &vitalsFields); err != nil || vitalsFields == nil { return nil, fmt.Errorf("vitals are required") }
	if err := json.Unmarshal(vitalsFields["throttle"], &throttleFields); err != nil || throttleFields == nil { return nil, fmt.Errorf("vital throttle limits are required") }
	for _, name := range []string{"cpu", "rtt_ms", "down_kbps"} {
		value, present := throttleFields[name]
		if !present || bytes.Equal(bytes.TrimSpace(value), []byte("null")) { return nil, fmt.Errorf("throttle.%s must be present and numeric", name) }
	}
	var raw struct {
		Schema int `json:"schema"`
		MeasuredAt *string `json:"measured_at"`
		Source string `json:"source"`
		JS map[string]json.RawMessage `json:"js"`
		CSS map[string]Limit `json:"css"`
		Routes map[string]RouteBudget `json:"routes"`
		Vitals Vitals `json:"vitals"`
	}
	if err := strictJSON(data, &raw); err != nil { return nil, err }
	if raw.Schema != 1 || raw.JS == nil || raw.CSS == nil || raw.Routes == nil {
		return nil, fmt.Errorf("schema, js, css and routes are required")
	}
	b := &Budgets{Schema: raw.Schema, MeasuredAt: raw.MeasuredAt, Source: raw.Source, Classes: map[string]Limit{}, Vendors: map[string]Limit{}, Routes: raw.Routes, Vitals: raw.Vitals}
	for _, name := range []string{"server-page", "island-route", "cat-initial"} {
		value, present := raw.JS[name]
		if !present { return nil, fmt.Errorf("missing js.%s budget", name) }
		var limit Limit
		if err := json.Unmarshal(value, &limit); err != nil { return nil, fmt.Errorf("js.%s: %w", name, err) }
		if limit.LimitGZ == nil { return nil, fmt.Errorf("js.%s.limit_gz must be numeric", name) }
		if name != "cat-initial" && limit.TargetGZ != nil { return nil, fmt.Errorf("target_gz is allowed only for js.cat-initial") }
		b.Classes[name] = limit
	}
	if b.Classes["cat-initial"].TargetGZ == nil { return nil, fmt.Errorf("missing js.cat-initial.target_gz") }
	vendor, present := raw.JS["vendor-gated"]
	if !present { return nil, fmt.Errorf("missing js.vendor-gated") }
	if err := json.Unmarshal(vendor, &b.Vendors); err != nil || b.Vendors == nil { return nil, fmt.Errorf("invalid js.vendor-gated") }
	for name, limit := range b.Vendors {
		if limit.LimitGZ == nil { return nil, fmt.Errorf("js.vendor-gated.%s.limit_gz must be numeric", name) }
		if limit.TargetGZ != nil { return nil, fmt.Errorf("target_gz is allowed only for js.cat-initial") }
	}
	for name := range raw.JS {
		if name != "server-page" && name != "island-route" && name != "cat-initial" && name != "vendor-gated" { return nil, fmt.Errorf("unknown JS budget class %s", name) }
	}
	global, present := raw.CSS["global"]
	if !present || len(raw.CSS) != 1 { return nil, fmt.Errorf("css.global is the required CSS budget") }
	if global.TargetGZ != nil { return nil, fmt.Errorf("target_gz is allowed only for js.cat-initial") }
	b.GlobalCSS = global
	for _, value := range []float64{b.Vitals.LCPMS, b.Vitals.INPMS, b.Vitals.Throttle.RTTMS, b.Vitals.Throttle.DownKbps} {
		if math.Trunc(value) != value { return nil, fmt.Errorf("LCP, INP, RTT and down_kbps must be integers") }
	}
	if b.Vitals.LCPMS <= 0 || b.Vitals.INPMS <= 0 || b.Vitals.Throttle.CPU < 1 || b.Vitals.Throttle.RTTMS < 0 || b.Vitals.Throttle.DownKbps <= 0 {
		return nil, fmt.Errorf("vital/throttle limits require positive values, with nonnegative RTT")
	}
	for name, route := range b.Routes {
		if name == "" { return nil, fmt.Errorf("empty budget route name") }
		if _, present := b.Classes[route.Class]; !present { return nil, fmt.Errorf("unknown budget route class %s", route.Class) }
	}
	return b, nil
}

// Vendor bindings are measured independently. Eager includes the vendor in the
// route's initial bytes; false means the app's explicit loading gate excludes it.
type Vendor struct {
	Name string `json:"name"`
	Entry string `json:"entry"`
	Eager bool `json:"eager"`
}

func (v *Vendor) UnmarshalJSON(data []byte) error {
	var raw map[string]json.RawMessage
	if err := json.Unmarshal(data, &raw); err != nil { return err }
	for _, key := range []string{"name", "entry", "eager"} {
		if _, present := raw[key]; !present { return fmt.Errorf("vendor binding needs explicit %s", key) }
	}
	for key := range raw {
		if key != "name" && key != "entry" && key != "eager" { return fmt.Errorf("unknown vendor binding field %s", key) }
	}
	if err := json.Unmarshal(raw["name"], &v.Name); err != nil { return err }
	if err := json.Unmarshal(raw["entry"], &v.Entry); err != nil { return err }
	if string(raw["eager"]) != "true" && string(raw["eager"]) != "false" { return fmt.Errorf("vendor eager must be boolean") }
	if err := json.Unmarshal(raw["eager"], &v.Eager); err != nil { return err }
	if v.Name == "" || v.Entry == "" { return fmt.Errorf("vendor name and entry required") }
	return nil
}

type Binding struct {
	Class string `json:"class"`
	Entries []string `json:"entries"`
	Islands []string `json:"islands"`
	Widgets []string `json:"widgets"`
	Vendors []Vendor `json:"vendors"`
}

type Config struct {
	Schema int `json:"schema"`
	Routes map[string]Binding `json:"routes"`
	GlobalCSS []string `json:"global_css"`
	Vendors map[string]string `json:"vendors"`
}

// LoadConfig accepts asset and class bindings only. It rejects threshold
// overrides and requires explicit entries/global_css lists (empty is allowed).
func LoadConfig(data []byte) (*Config, error) {
	var c Config
	if err := strictJSON(data, &c); err != nil { return nil, err }
	if err := validateConfig(&c); err != nil { return nil, err }
	return &c, nil
}

func validateConfig(c *Config) error {
	if c == nil || c.Schema != 1 || c.Routes == nil || c.GlobalCSS == nil || c.Vendors == nil {
		return fmt.Errorf("config schema, routes, global_css and vendors are required")
	}
	for name, binding := range c.Routes {
		if name == "" || binding.Class == "" || binding.Entries == nil { return fmt.Errorf("route %s needs class and explicit entries", name) }
	}
	return nil
}

type Manifest struct {
	Entries map[string]assets.Entry
	Files fs.FS
}

// LoadManifest reads the actual Vite manifest relative to the asset directory.
// gzip sizes come from real .gz sidecars or deterministic gzip of actual files.
func LoadManifest(files fs.FS, filename string) (*Manifest, error) {
	data, err := fs.ReadFile(files, filename)
	if err != nil { return nil, err }
	entries := map[string]assets.Entry{}
	if err := json.Unmarshal(data, &entries); err != nil { return nil, err }
	if len(entries) == 0 { return nil, fmt.Errorf("empty Vite manifest") }
	for key, entry := range entries {
		if key == "" || entry.File == "" || !fs.ValidPath(entry.File) { return nil, fmt.Errorf("invalid manifest entry") }
		for _, name := range append(append([]string{entry.File}, entry.CSS...), entry.Assets...) {
			if !fs.ValidPath(name) { return nil, fmt.Errorf("invalid manifest path %s", name) }
			info, err := fs.Stat(files, name)
			if err != nil || info.IsDir() { return nil, fmt.Errorf("missing manifest file %s", name) }
		}
		for _, dep := range append(append([]string{}, entry.Imports...), entry.DynamicImports...) {
			if _, present := entries[dep]; !present { return nil, fmt.Errorf("unknown manifest import %s", dep) }
		}
	}
	return &Manifest{Entries: entries, Files: files}, nil
}

type Measurement struct {
	Scope string `json:"scope"`
	Name string `json:"name"`
	ActualGZ int64 `json:"actual_gz"`
	LimitGZ *int64 `json:"limit_gz"`
	TargetGZ *int64 `json:"target_gz,omitempty"`
	TargetStatus string `json:"target_status,omitempty"`
	Status string `json:"status"`
	Files []string `json:"files"`
}

type RouteMeasurement struct {
	Name string `json:"name"`
	Class string `json:"class"`
	JS Measurement `json:"js"`
	CSS Measurement `json:"css"`
}

type UnusedLimit struct {
	Name string `json:"name"`
	LimitGZ *int64 `json:"limit_gz"`
	TargetGZ *int64 `json:"target_gz,omitempty"`
	Reason string `json:"reason"`
}

type Report struct {
	Schema int `json:"schema"`
	Status string `json:"status"`
	GlobalCSS Measurement `json:"global_css"`
	Routes []RouteMeasurement `json:"routes"`
	Vendors []Measurement `json:"vendors"`
	UnusedLimits []UnusedLimit `json:"unused_limits"`
	NonPageRoutes []string `json:"non_page_routes"`
	Vitals Vitals `json:"vitals_limits"`
	UnmeasuredMetrics []string `json:"unmeasured_metrics"`
}

func measurement(scope, name string, actual int64, limit Limit, files []string) Measurement {
	status := "pass"
	if limit.LimitGZ == nil { status = "recorded" } else if actual > *limit.LimitGZ { status = "fail" }
	m := Measurement{Scope: scope, Name: name, ActualGZ: actual, LimitGZ: limit.LimitGZ, TargetGZ: limit.TargetGZ, Status: status, Files: files}
	if limit.TargetGZ != nil {
		m.TargetStatus = "met"
		if actual > *limit.TargetGZ { m.TargetStatus = "unmet" }
	}
	return m
}

func sorted(set map[string]bool) []string {
	out := make([]string, 0, len(set))
	for value := range set { out = append(out, value) }
	sort.Strings(out)
	return out
}

// gzipSize verifies a sidecar decompresses to the actual original before using
// its shipped byte count. Without a sidecar it compresses actual source bytes.
func gzipSize(files fs.FS, filename string) (int64, error) {
	if !fs.ValidPath(filename) { return 0, fmt.Errorf("invalid asset path") }
	original, err := fs.ReadFile(files, filename)
	if err != nil { return 0, err }
	compressed, err := fs.ReadFile(files, filename+".gz")
	if err == nil {
		r, err := gzip.NewReader(bytes.NewReader(compressed))
		if err != nil { return 0, fmt.Errorf("invalid gzip asset %s", filename) }
		decoded, readErr := io.ReadAll(io.LimitReader(r, int64(len(original))+1))
		closeErr := r.Close()
		if readErr != nil || closeErr != nil || !bytes.Equal(decoded, original) { return 0, fmt.Errorf("stale gzip asset %s", filename) }
		return int64(len(compressed)), nil
	}
	if !errors.Is(err, fs.ErrNotExist) { return 0, err }
	var compressedBuffer bytes.Buffer
	w := gzip.NewWriter(&compressedBuffer)
	if _, err := w.Write(original); err != nil { return 0, err }
	if err := w.Close(); err != nil { return 0, err }
	return int64(compressedBuffer.Len()), nil
}

func sum(files fs.FS, names map[string]bool) (int64, error) {
	var total int64
	for _, name := range sorted(names) {
		size, err := gzipSize(files, name)
		if err != nil { return 0, err }
		total += size
	}
	return total, nil
}

func collect(m *Manifest, entry string, js, css, visited map[string]bool) error {
	if visited[entry] { return nil }
	value, present := m.Entries[entry]
	if !present { return fmt.Errorf("unknown asset entry %s", entry) }
	visited[entry] = true
	if path.Ext(value.File) == ".js" || path.Ext(value.File) == ".mjs" { js[value.File] = true } else if path.Ext(value.File) == ".css" { css[value.File] = true } else { return fmt.Errorf("budget entry is not JS or CSS: %s", entry) }
	for _, name := range value.CSS { css[name] = true }
	for _, dependency := range value.Imports {
		if err := collect(m, dependency, js, css, visited); err != nil { return err }
	}
	// DynamicImports do not load eagerly. An island/widget/vendor binding must
	// name a dynamic entry explicitly for its bytes to count in that journey.
	return nil
}

func sameNames(left, right []string) bool {
	a, b := map[string]bool{}, map[string]bool{}
	for _, name := range left { a[name] = true }
	for _, name := range right { b[name] = true }
	if len(a) != len(b) { return false }
	for name := range a { if !b[name] { return false } }
	return true
}

// Evaluate binds every exported HTML page route to explicit asset entries.
// Non-page routes are recorded by name; absent bindings for HTML pages fail.
// Committed per-route classes/islands/widgets always win through exact agreement.
func Evaluate(b *Budgets, manifest *Manifest, table []routes.Route, c *Config) (Report, error) {
	report := Report{Schema: 1, Status: "pass", UnmeasuredMetrics: []string{"lcp_ms", "inp_ms"}}
	if b == nil || manifest == nil || manifest.Files == nil || len(table) == 0 { return report, fmt.Errorf("budgets, manifest and exported routes are required") }
	if err := validateConfig(c); err != nil { return report, err }
	report.Vitals = b.Vitals
	known := map[string]bool{}
	pages := map[string]bool{}
	for _, route := range table {
		if route.Name == "" || known[route.Name] { return report, fmt.Errorf("duplicate or unnamed exported route") }
		known[route.Name] = true
		if route.Template != "" { pages[route.Name] = true } else { report.NonPageRoutes = append(report.NonPageRoutes, route.Name) }
	}
	if len(pages) == 0 { return report, fmt.Errorf("exported route table has no HTML pages") }
	for name := range c.Routes { if !pages[name] { return report, fmt.Errorf("binding for unknown or non-page route %s", name) } }
	for name := range b.Routes { if !pages[name] { return report, fmt.Errorf("budget declares unknown or non-page route %s", name) } }
	globalCSS := map[string]bool{}
	for _, name := range c.GlobalCSS {
		if path.Ext(name) != ".css" { return report, fmt.Errorf("global CSS binding is not CSS") }
		globalCSS[name] = true
	}
	globalSize, err := sum(manifest.Files, globalCSS)
	if err != nil { return report, err }
	report.GlobalCSS = measurement("global-css", "global", globalSize, b.GlobalCSS, sorted(globalCSS))
	if report.GlobalCSS.Status == "fail" { report.Status = "fail" }
	usedClasses, usedVendors := map[string]bool{}, map[string]bool{}
	for _, name := range sorted(pages) {
		binding, present := c.Routes[name]
		if !present { return report, fmt.Errorf("missing route binding %s", name) }
		limit, present := b.Classes[binding.Class]
		if !present { return report, fmt.Errorf("unknown route class %s", binding.Class) }
		if len(b.Routes) > 0 {
			committed, present := b.Routes[name]
			if !present { return report, fmt.Errorf("route missing from committed budgets: %s", name) }
			if binding.Class != committed.Class || !sameNames(binding.Islands, committed.Islands) || !sameNames(binding.Widgets, committed.Widgets) { return report, fmt.Errorf("binding disagrees with committed route budget: %s", name) }
		}
		usedClasses[binding.Class] = true
		js, css, visited := map[string]bool{}, map[string]bool{}, map[string]bool{}
		for file := range globalCSS { css[file] = true }
		entries := append(append(append([]string{}, binding.Entries...), binding.Islands...), binding.Widgets...)
		for _, entry := range entries { if err := collect(manifest, entry, js, css, visited); err != nil { return report, err } }
		for _, vendor := range binding.Vendors {
			if _, present := b.Vendors[vendor.Name]; !present { return report, fmt.Errorf("vendor lacks committed limit: %s", vendor.Name) }
			if c.Vendors[vendor.Name] != vendor.Entry { return report, fmt.Errorf("vendor binding disagrees with global declaration: %s", vendor.Name) }
			usedVendors[vendor.Name] = true
			if vendor.Eager { if err := collect(manifest, vendor.Entry, js, css, visited); err != nil { return report, err } }
		}
		jsSize, err := sum(manifest.Files, js)
		if err != nil { return report, err }
		cssSize, err := sum(manifest.Files, css)
		if err != nil { return report, err }
		row := RouteMeasurement{Name: name, Class: binding.Class, JS: measurement("route-js", name, jsSize, limit, sorted(js)), CSS: measurement("route-css", name, cssSize, b.GlobalCSS, sorted(css))}
		if row.JS.Status == "fail" || row.CSS.Status == "fail" { report.Status = "fail" }
		report.Routes = append(report.Routes, row)
	}
	vendorNames := make([]string, 0, len(c.Vendors))
	for name := range c.Vendors { vendorNames = append(vendorNames, name) }
	sort.Strings(vendorNames)
	for _, name := range vendorNames {
		limit, present := b.Vendors[name]
		if !present { return report, fmt.Errorf("vendor lacks committed limit: %s", name) }
		js, css, visited := map[string]bool{}, map[string]bool{}, map[string]bool{}
		if err := collect(manifest, c.Vendors[name], js, css, visited); err != nil { return report, err }
		size, err := sum(manifest.Files, js)
		if err != nil { return report, err }
		row := measurement("vendor-gated", name, size, limit, sorted(js))
		if row.Status == "fail" { report.Status = "fail" }
		report.Vendors = append(report.Vendors, row)
		usedVendors[name] = true
	}
	for name, limit := range b.Classes { if !usedClasses[name] { report.UnusedLimits = append(report.UnusedLimits, UnusedLimit{Name: "js."+name, LimitGZ: limit.LimitGZ, TargetGZ: limit.TargetGZ, Reason: "no route declares this class"}) } }
	for name, limit := range b.Vendors { if !usedVendors[name] { report.UnusedLimits = append(report.UnusedLimits, UnusedLimit{Name: "js.vendor-gated."+name, LimitGZ: limit.LimitGZ, TargetGZ: limit.TargetGZ, Reason: "no vendor binding declares this asset"}) } }
	sort.Strings(report.NonPageRoutes)
	sort.Slice(report.UnusedLimits, func(i,j int) bool { return report.UnusedLimits[i].Name < report.UnusedLimits[j].Name })
	return report, nil
}

// TestRouteBudgets logs every measurement (including null-limit recorded rows)
// and fails the calling suite on bad bindings or exceeded committed limits.
func TestRouteBudgets(t testing.TB, b *Budgets, manifest *Manifest, table []routes.Route, c *Config) Report {
	t.Helper()
	report, err := Evaluate(b, manifest, table, c)
	if err != nil { t.Fatalf("route budgets: %v", err); return report }
	data, err := json.Marshal(report)
	if err != nil { t.Fatalf("route budget report: %v", err); return report }
	t.Logf("route-budget measurements: %s", data)
	if report.Status != "pass" { t.Errorf("route budgets exceeded committed limits") }
	return report
}
