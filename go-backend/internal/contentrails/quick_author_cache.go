package contentrails

// This is a versioned provenance extension. First fetch, current author use,
// inspection and authorship remain different facts. Root's independently
// supplied pin is the trust premise; none of these JSON fields authenticates it.
import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"math"
	"net/url"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode"
	"unicode/utf8"
)

const quickApprovedManualClient = "29f6979a54bba0bb5858c9449e226f759d863ef11667db8ceee30de0ee9f33c3"

// QuickCachePin must come from the orchestrator outside the author packet.
// Supplying it establishes a v2 exposure context: v1 cannot erase that context.
type QuickCachePin struct{ Path, SHA256 string }

func cachePin(pins []QuickCachePin) (QuickCachePin, error) {
	if len(pins) == 0 {
		return QuickCachePin{}, nil
	}
	if len(pins) != 1 || pins[0].Path == "" || !authorityDigest(pins[0].SHA256) {
		return QuickCachePin{}, fmt.Errorf("quick cache requires one independent Root path and SHA")
	}
	return pins[0], nil
}
func cacheRef(v any) (map[string]any, error) {
	r := object(v)
	if !pendingExact(r, "path", "bytes", "sha256") || !authorityDigest(r["sha256"]) || integer(r["bytes"]) < 1 || integer(r["bytes"]) > MaxBytes {
		return nil, fmt.Errorf("quick cache descriptor shape/cap")
	}
	return r, nil
}
func cacheExternal(root, path string) error {
	rel, err := filepath.Rel(root, path)
	if err != nil || rel == "." || rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		return fmt.Errorf("quick cache external input inside Root")
	}
	return nil
}

// Fixed two-level closure only: no discovery by arbitrary descriptor recursion.
// Caller freezes every returned byte and enforces the existing 64MiB/4100 caps.
func cacheLoad(root string, pin QuickCachePin, read func(map[string]any) ([]byte, error)) (map[string]any, []string, error) {
	if pin.Path == "" || !authorityDigest(pin.SHA256) {
		return nil, nil, fmt.Errorf("quick cache independent Root pin required")
	}
	if err := cacheExternal(root, pin.Path); err != nil {
		return nil, nil, err
	}
	b, err := pendingRegular(pin.Path, MaxBytes)
	if err != nil || digestBytes(b) != pin.SHA256 {
		return nil, nil, fmt.Errorf("quick cache Root pin differs")
	}
	binding, err := pendingDecode(b, MaxBytes)
	if err != nil {
		return nil, nil, err
	}
	if !pendingExact(binding, "schema", "operator", "root", "baseline_source_sha256", "inventory_sha256", "packet_sha256", "run_id", "cache_root", "client", "author", "author_context", "created_at", "source_controls", "first_receipt_journal", "owner_refusals", "attempts", "deliveries", "inspection_ack", "exposure_urls") || binding["schema"] != "quick-author-cache-binding-v1" || binding["operator"] != "agent:codex" || binding["root"] != root || strings.TrimSpace(text(binding["run_id"])) == "" || strings.TrimSpace(text(binding["author"])) == "" || strings.TrimSpace(text(binding["author_context"])) == "" || !authorityDigest(binding["baseline_source_sha256"]) || !authorityDigest(binding["inventory_sha256"]) || !authorityDigest(binding["packet_sha256"]) || !arrayShape(binding["attempts"], 1, 64) || !arrayShape(binding["deliveries"], 1, 4096) {
		return nil, nil, fmt.Errorf("quick cache Root binding exact identity/shape")
	}
	cacheRoot := text(binding["cache_root"])
	if !filepath.IsAbs(cacheRoot) || filepath.Clean(cacheRoot) != cacheRoot || cacheExternal(root, cacheRoot) != nil {
		return nil, nil, fmt.Errorf("quick cache canonical external cache root required")
	}
	paths, roles := []string{}, map[string]string{}
	get := func(role string, v any) ([]byte, error) {
		ref, e := cacheRef(v)
		if e != nil {
			return nil, e
		}
		path := text(ref["path"])
		if e = cacheExternal(root, path); e != nil {
			return nil, e
		}
		if prior := roles[path]; prior != "" {
			return nil, fmt.Errorf("quick cache duplicate artifact roles %s/%s", prior, role)
		}
		roles[path] = role
		data, e := read(ref)
		if e == nil {
			paths = append(paths, path)
		}
		return data, e
	}
	if _, err = get("binding", map[string]any{"path": pin.Path, "bytes": len(b), "sha256": pin.SHA256}); err != nil {
		return nil, nil, err
	}
	for _, key := range []string{"client", "first_receipt_journal", "owner_refusals", "inspection_ack"} {
		if _, err = get(key, binding[key]); err != nil {
			return nil, nil, err
		}
	}
	controlsBytes, err := get("source_controls", binding["source_controls"])
	if err != nil {
		return nil, nil, err
	}
	controls, err := pendingDecode(controlsBytes, MaxBytes)
	if err != nil {
		return nil, nil, err
	}
	if !pendingExact(controls, "schema", "run_id", "client_sha256", "checked_at", "terms_checked_by", "terms_evidence", "hosts") || controls["schema"] != "quick-cache-current-controls-v1" || !arrayShape(controls["hosts"], 1, 3) || !arrayShape(controls["terms_evidence"], 1, 32) {
		return nil, nil, fmt.Errorf("quick cache current controls shape")
	}
	for i, v := range rows(controls["terms_evidence"]) {
		if _, err = get(fmt.Sprintf("terms/%d", i), v); err != nil {
			return nil, nil, err
		}
	}
	for i, v := range rows(controls["hosts"]) {
		h := object(v)
		if !pendingExact(h, "host", "state", "robots_receipt", "robots_body") {
			return nil, nil, fmt.Errorf("quick cache host controls shape")
		}
		for _, key := range []string{"state", "robots_receipt", "robots_body"} {
			if _, err = get(fmt.Sprintf("host/%d/%s", i, key), h[key]); err != nil {
				return nil, nil, err
			}
		}
	}
	for i, v := range rows(binding["attempts"]) {
		if _, err = get(fmt.Sprintf("attempt/%d", i), v); err != nil {
			return nil, nil, err
		}
	}
	for i, v := range rows(binding["deliveries"]) {
		d := object(v)
		if _, err = get(fmt.Sprintf("first_receipt/%d", i), d["first_receipt"]); err != nil {
			return nil, nil, err
		}
	}
	return binding, paths, nil
}
func cacheObject(inputs map[string][]byte, v any) (map[string]any, error) {
	ref, err := cacheRef(v)
	if err != nil {
		return nil, err
	}
	b, ok := inputs[text(ref["path"])]
	if !ok || len(b) != integer(ref["bytes"]) || digestBytes(b) != ref["sha256"] {
		return nil, fmt.Errorf("quick cache frozen descriptor differs")
	}
	return pendingDecode(b, MaxBytes)
}
func cacheCanonicalURLs(v any) (map[string]bool, error) {
	if !stringArray(v, 1, 4096) {
		return nil, fmt.Errorf("quick cache complete exposure required")
	}
	list := ids(v)
	out := map[string]bool{}
	for _, raw := range list {
		u, e := bridgeURL(raw)
		if e != nil || raw != u || out[u] {
			return nil, fmt.Errorf("quick cache canonical unique URLs required")
		}
		out[u] = true
	}
	if !sort.StringsAreSorted(list) {
		return nil, fmt.Errorf("quick cache exposure URLs must be sorted")
	}
	return out, nil
}
func cacheEpoch(v any) (time.Time, error) {
	n, ok := v.(json.Number)
	if !ok {
		return time.Time{}, fmt.Errorf("quick cache original epoch must be numeric")
	}
	f, e := strconv.ParseFloat(string(n), 64)
	if e != nil || math.IsNaN(f) || math.IsInf(f, 0) || f < 0 || f > 253402300799 {
		return time.Time{}, fmt.Errorf("quick cache epoch bound")
	}
	// Explicit Python-compatible microsecond display, round ties to even. Original
	// raw receipt bytes remain pinned and are compared without normalization.
	sec, frac := math.Modf(f)
	micro := int64(math.RoundToEven(frac * 1e6))
	return time.Unix(int64(sec), micro*1000).UTC(), nil
}

// Policy-only compatibility helpers follow the approved Python client's Unicode
// splitlines/strip/lower and Content-Signal refusal semantics. ASCII regexp word
// boundaries conservatively over-refuse some Unicode-adjacent signal spellings.
// No unsupported-policy fallback grants permission.
func cachePolicySpace(r rune) bool {
	return unicode.IsSpace(r) || r >= '\x1c' && r <= '\x1f'
}
func cachePolicyTrim(s string) string { return strings.TrimFunc(s, cachePolicySpace) }
func cachePolicyLower(s string) string {
	// Python lower expands LATIN CAPITAL LETTER I WITH DOT ABOVE; Go's simple
	// lowercase would select a different own-agent group ahead of wildcard rules.
	return strings.ToLower(strings.ReplaceAll(s, "\u0130", "i\u0307"))
}
func cachePolicyLines(s string) []string {
	// Empty lines carry no directives in the approved parser; collapsing them
	// also treats CRLF as one boundary without changing group construction.
	return strings.FieldsFunc(s, func(r rune) bool {
		switch r {
		case '\n', '\r', '\v', '\f', '\x1c', '\x1d', '\x1e', '\u0085', '\u2028', '\u2029':
			return true
		}
		return false
	})
}

var quickCacheSignalRefusal = regexp.MustCompile("(?i)\\ba[i\u0130\u0131]-(?:[i\u0130\u0131]nput|tra[i\u0130\u0131]n)[\t-\r\x1c-\x1f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*=[\t-\r\x1c-\x1f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*no\\b")

func cachePolicySignalDenied(s string) bool { return quickCacheSignalRefusal.MatchString(s) }

func cacheRawReceipt(r map[string]any) error {
	if !pendingExact(r, "url", "sha256", "status", "bytes", "fetched_by_role", "fetched_at", "headers") || r["status"] == nil || integer(r["status"]) != 200 || !authorityDigest(r["sha256"]) || integer(r["bytes"]) < 1 || integer(r["bytes"]) > MaxBytes || !pendingExact(object(r["headers"]), "content-type", "content-signal", "retry-after") {
		return fmt.Errorf("quick cache immutable original receipt shape/status")
	}
	for _, v := range object(r["headers"]) {
		if _, ok := v.(string); !ok {
			return fmt.Errorf("quick cache receipt header type")
		}
	}
	if cachePolicySignalDenied(text(object(r["headers"])["content-signal"])) {
		return fmt.Errorf("quick cache original source policy refusal")
	}
	switch r["fetched_by_role"] {
	case "author", "factual", "quality", "critic":
	default:
		return fmt.Errorf("quick cache legacy/policy/unknown first role refused")
	}
	_, e := cacheEpoch(r["fetched_at"])
	return e
}
func cacheJournal(inputs map[string][]byte, ref any) (map[string]map[string]any, error) {
	d, e := cacheRef(ref)
	if e != nil {
		return nil, e
	}
	b := inputs[text(d["path"])]
	if len(b) != integer(d["bytes"]) || digestBytes(b) != d["sha256"] {
		return nil, fmt.Errorf("quick cache journal descriptor differs")
	}
	out := map[string]map[string]any{}
	scanner := bufio.NewScanner(bytes.NewReader(b))
	scanner.Buffer(make([]byte, 4096), MaxBytes)
	count := 0
	for scanner.Scan() {
		count++
		if count > 32768 {
			return nil, fmt.Errorf("quick cache journal row cap")
		}
		r, e := pendingDecode(scanner.Bytes(), MaxBytes)
		if e != nil {
			return nil, e
		}
		u := text(r["url"])
		if integer(r["status"]) != 200 {
			continue
		}
		canonical, e := bridgeURL(u)
		if e != nil {
			return nil, e
		}
		u = canonical
		when, e := cacheEpoch(r["fetched_at"])
		if e != nil {
			return nil, e
		}
		if old := out[u]; old != nil {
			first, _ := cacheEpoch(old["fetched_at"])
			if when.Equal(first) && !same(old, r) {
				return nil, fmt.Errorf("quick cache conflicting earliest first receipt")
			}
			if !when.Before(first) {
				continue
			}
		}
		out[u] = r
	}
	return out, scanner.Err()
}

// cacheRobots mirrors only the existing approved manual client's offline policy
// rules. It never executes/imports a client or opens transport.
func cacheRobots(body []byte, path string) error {
	check, e := cacheRobotsPolicy(body)
	if e != nil {
		return e
	}
	return check(path)
}
func cacheRobotsPolicy(body []byte) (func(string) error, error) {
	if !utf8.Valid(body) {
		return nil, fmt.Errorf("quick cache robots requires valid UTF-8")
	}
	type group struct {
		agents []string
		rules  [][2]string
	}
	groups := []group{}
	g := group{}
	directives := 0
	for _, line := range cachePolicyLines(strings.TrimPrefix(string(body), "\ufeff")) {
		line = strings.SplitN(line, "#", 2)[0]
		pair := strings.SplitN(cachePolicyTrim(line), ":", 2)
		if len(pair) != 2 {
			continue
		}
		key, value := cachePolicyLower(cachePolicyTrim(pair[0])), cachePolicyTrim(pair[1])
		directives++
		if directives > 8192 || len(value) > 8192 {
			return nil, fmt.Errorf("quick cache robots directive/work cap")
		}
		if key == "content-signal" && cachePolicySignalDenied(value) {
			return nil, fmt.Errorf("quick cache robots content-signal refusal")
		}
		if key == "user-agent" {
			if len(g.rules) > 0 {
				groups = append(groups, g)
				g = group{}
			}
			g.agents = append(g.agents, cachePolicyLower(value))
		} else if len(g.agents) > 0 && (key == "allow" || key == "disallow" || key == "crawl-delay") {
			g.rules = append(g.rules, [2]string{key, value})
		}
	}
	if len(g.agents) > 0 {
		groups = append(groups, g)
	}
	has := func(a []string, s string) bool {
		for _, v := range a {
			if v == s {
				return true
			}
		}
		return false
	}
	own := false
	for _, g := range groups {
		own = own || has(g.agents, "cat-de-roman-esti-content-research")
	}
	sets := [][][2]string{nil}
	for _, crawler := range []string{"gptbot", "chatgpt-user", "oai-searchbot", "claudebot", "anthropic-ai", "google-extended"} {
		rules := [][2]string{}
		for _, g := range groups {
			if has(g.agents, crawler) {
				rules = append(rules, g.rules...)
			}
		}
		sets = append(sets, rules)
	}
	for _, g := range groups {
		if own && has(g.agents, "cat-de-roman-esti-content-research") || !own && has(g.agents, "*") {
			sets[0] = append(sets[0], g.rules...)
		}
	}
	octets := regexp.MustCompile(`%[0-9a-fA-F]{2}`)
	normalize := func(s string) string {
		return octets.ReplaceAllStringFunc(s, func(v string) string {
			n, _ := strconv.ParseUint(v[1:], 16, 8)
			c := byte(n)
			if c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || strings.ContainsRune("._~-", rune(c)) {
				return string(c)
			}
			return strings.ToUpper(v)
		})
	}
	type rule struct {
		pattern  *regexp.Regexp
		specific int
		allow    bool
	}
	compiled := [][]rule{}
	for _, set := range sets {
		rules := []rule{}
		for _, r := range set {
			if r[1] == "" || r[0] == "crawl-delay" {
				continue
			}
			body := normalize(r[1])
			anchor := strings.HasSuffix(body, "$")
			body = strings.TrimSuffix(body, "$")
			parts := strings.Split(body, "*")
			for i := range parts {
				parts[i] = regexp.QuoteMeta(parts[i])
			}
			pattern := "^" + strings.Join(parts, ".*")
			if anchor {
				pattern += "$"
			}
			p, e := regexp.Compile(pattern)
			if e != nil {
				return nil, e
			}
			rules = append(rules, rule{p, len(strings.ReplaceAll(body, "*", "")), r[0] == "allow"})
		}
		compiled = append(compiled, rules)
	}
	return func(path string) error {
		path = normalize(path)
		for _, rules := range compiled {
			best, allowed := -1, true
			for _, r := range rules {
				if r.pattern.MatchString(path) && (r.specific > best || r.specific == best && r.allow) {
					best, allowed = r.specific, r.allow
				}
			}
			if !allowed {
				return fmt.Errorf("quick cache robots path/AI crawler refusal")
			}
		}
		return nil
	}, nil
}
func cacheControls(binding map[string]any, inputs map[string][]byte, U map[string]bool, ack time.Time) error {
	cacheRoot := text(binding["cache_root"])
	if text(object(binding["first_receipt_journal"])["path"]) != filepath.Join(cacheRoot, "receipts.jsonl") || text(object(binding["owner_refusals"])["path"]) != filepath.Join(cacheRoot, "owner-refusals.jsonl") {
		return fmt.Errorf("quick cache current journal/refusal path differs")
	}
	c, e := cacheObject(inputs, binding["source_controls"])
	if e != nil {
		return e
	}
	checked, e := bridgeTime(c["checked_at"])
	if e != nil || checked.After(ack) || c["run_id"] != binding["run_id"] || c["client_sha256"] != quickApprovedManualClient || c["terms_checked_by"] != binding["operator"] {
		return fmt.Errorf("quick cache stale current source control context")
	}
	// DEX/Foundation remain whole-run dropped; this feature adds no hosts.
	hosts := map[string]map[string]any{}
	for _, v := range rows(c["hosts"]) {
		h := object(v)
		host := text(h["host"])
		if host != "ro.wikipedia.org" && host != "ro.wiktionary.org" && host != "raw.githubusercontent.com" || hosts[host] != nil {
			return fmt.Errorf("quick cache unapproved/duplicate/dropped host")
		}
		hosts[host] = h
	}
	refusalsRef, _ := cacheRef(binding["owner_refusals"])
	scan := bufio.NewScanner(bytes.NewReader(inputs[text(refusalsRef["path"])]))
	scan.Buffer(make([]byte, 4096), MaxBytes)
	denied := map[string]bool{}
	count := 0
	for scan.Scan() {
		count++
		if count > 32768 {
			return fmt.Errorf("quick cache refusal row cap")
		}
		r, e := pendingDecode(scan.Bytes(), MaxBytes)
		if e != nil {
			return e
		}
		if !pendingExact(r, "host", "reason", "at") || strings.TrimSpace(text(r["host"])) == "" || strings.TrimSpace(text(r["reason"])) == "" {
			return fmt.Errorf("quick cache original refusal ledger shape")
		}
		if _, e = cacheEpoch(r["at"]); e != nil {
			return e
		}
		denied[text(r["host"])] = true
	}
	if e = scan.Err(); e != nil {
		return e
	}
	used := map[string]bool{}
	robotPolicies := map[string]func(string) error{}
	for raw := range U {
		target, e := url.Parse(raw)
		if e != nil || target.Scheme != "https" || target.Fragment != "" || target.User != nil || target.Host != target.Hostname() {
			return fmt.Errorf("quick cache approved HTTPS source path required")
		}
		for _, ch := range raw {
			if ch < 33 || ch > 126 {
				return fmt.Errorf("quick cache source printable ASCII required")
			}
		}
		host := target.Host
		h := hosts[host]
		if h == nil || denied[host] {
			return fmt.Errorf("quick cache current dropped host")
		}
		used[host] = true
		if host == "raw.githubusercontent.com" {
			rawPath := target.EscapedPath()
			p := strings.Split(rawPath, "/")
			if len(p) < 5 || strings.Join(p[:3], "/") != "/hermitdave/FrequencyWords" || strings.ContainsAny(rawPath, "%\\") || target.RawQuery != "" {
				return fmt.Errorf("quick cache raw path allowlist")
			}
			for _, part := range p[3:] {
				if part == "" || part == "." || part == ".." {
					return fmt.Errorf("quick cache raw path allowlist")
				}
			}
		}
		if text(object(h["state"])["path"]) != filepath.Join(cacheRoot, host+".json") || text(object(h["robots_receipt"])["path"]) != filepath.Join(cacheRoot, digestBytes([]byte("https://"+host+"/robots.txt"))+".receipt.json") {
			return fmt.Errorf("quick cache current host state/robots path differs")
		}
		state, e := cacheObject(inputs, h["state"])
		if e != nil {
			return e
		}
		if !allowedKeys(state, "last_start", "breaker_until", "denied") || state["denied"] != nil && state["denied"] != "" {
			return fmt.Errorf("quick cache current policy denial")
		}
		if state["breaker_until"] != nil {
			until, e := cacheEpoch(state["breaker_until"])
			if e != nil || until.After(checked) {
				return fmt.Errorf("quick cache current breaker refusal")
			}
		}
		rr, e := cacheObject(inputs, h["robots_receipt"])
		if e != nil {
			return e
		}
		bodyRef, e := cacheRef(h["robots_body"])
		if e != nil {
			return e
		}
		if text(bodyRef["path"]) != filepath.Join(cacheRoot, text(bodyRef["sha256"])+".body") {
			return fmt.Errorf("quick cache robots body path differs")
		}
		if !pendingExact(rr, "url", "sha256", "status", "bytes", "fetched_by_role", "fetched_at", "headers") || rr["url"] != "https://"+host+"/robots.txt" || rr["fetched_by_role"] != "policy" || rr["sha256"] != bodyRef["sha256"] || !same(rr["bytes"], bodyRef["bytes"]) {
			return fmt.Errorf("quick cache robots original receipt differs")
		}
		if !pendingExact(object(rr["headers"]), "content-type", "content-signal", "retry-after") || cachePolicySignalDenied(text(object(rr["headers"])["content-signal"])) {
			return fmt.Errorf("quick cache robots header policy refusal")
		}
		first, e := cacheEpoch(rr["fetched_at"])
		if e != nil || first.After(checked) {
			return fmt.Errorf("quick cache robots time")
		}
		if integer(rr["status"]) == 200 {
			path := target.EscapedPath()
			if path == "" {
				path = "/"
			}
			if target.RawQuery != "" {
				path += "?" + target.RawQuery
			}
			check := robotPolicies[host]
			if check == nil {
				check, e = cacheRobotsPolicy(inputs[text(bodyRef["path"])])
				if e != nil {
					return e
				}
				robotPolicies[host] = check
			}
			if e = check(path); e != nil {
				return e
			}
		} else if integer(rr["status"]) != 404 && integer(rr["status"]) != 410 {
			return fmt.Errorf("quick cache robots unavailable")
		}
	}
	if len(used) != len(hosts) {
		return fmt.Errorf("quick cache unexplained control host")
	}
	return nil
}

func pendingEvidenceV2(root, baseline, inventorySHA string, packet, evidenceBytes []byte, boards []any, seal, evidence, binding map[string]any, inputs map[string][]byte, pin QuickCachePin) error {
	if !pendingExact(evidence, "schema", "packet_sha256", "items", "receipts", "cache_binding") || evidence["schema"] != "quick-author-evidence-v2" || !pendingExact(seal, "schema", "author", "packet_sha256", "evidence_sha256", "cache_binding_sha256", "sealed_at", "urls") || seal["schema"] != "quick-author-seal-v2" || evidence["packet_sha256"] != digestBytes(packet) || seal["packet_sha256"] != digestBytes(packet) || seal["evidence_sha256"] != digestBytes(evidenceBytes) || seal["cache_binding_sha256"] != pin.SHA256 || binding["packet_sha256"] != digestBytes(packet) || binding["baseline_source_sha256"] != baseline || binding["inventory_sha256"] != inventorySHA || binding["root"] != root || seal["author"] != binding["author"] {
		return fmt.Errorf("quick cache v2 evidence/seal/current Root binding differs")
	}
	ref, e := cacheRef(evidence["cache_binding"])
	if e != nil || ref["path"] != pin.Path || ref["sha256"] != pin.SHA256 || integer(ref["bytes"]) != len(inputs[pin.Path]) || digestBytes(inputs[pin.Path]) != pin.SHA256 {
		return fmt.Errorf("quick cache independent pin/evidence reference differs")
	}
	clientRef, _ := cacheRef(binding["client"])
	if clientRef == nil || clientRef["sha256"] != quickApprovedManualClient {
		return fmt.Errorf("quick cache unapproved research client")
	}
	U, e := cacheCanonicalURLs(binding["exposure_urls"])
	if e != nil {
		return e
	}
	if !same(binding["exposure_urls"], seal["urls"]) {
		return fmt.Errorf("quick cache seal exposure truncation")
	}
	items := map[string]any{}
	for _, v := range boards {
		r := object(v)
		items[text(r["id"])] = "source_backed"
		for _, u := range ids(r["sources"]) {
			canon, e := bridgeURL(u)
			if e != nil || u != canon || !U[u] {
				return fmt.Errorf("quick cache citation outside full exposure")
			}
		}
	}
	if !same(items, evidence["items"]) || !arrayShape(evidence["receipts"], len(U), len(U)) {
		return fmt.Errorf("quick cache item/receipt complete exposure coverage")
	}
	sealed, e := bridgeTime(seal["sealed_at"])
	if e != nil {
		return e
	}
	created, e := bridgeTime(binding["created_at"])
	if e != nil || !sealed.After(created) {
		return fmt.Errorf("quick cache new seal must follow Root binding")
	}
	ack, e := cacheObject(inputs, binding["inspection_ack"])
	if e != nil {
		return e
	}
	if !pendingExact(ack, "schema", "author", "root", "baseline_source_sha256", "inventory_sha256", "packet_sha256", "run_id", "client_sha256", "acknowledged_at", "items", "attempt_sha256s", "exposure_urls") || ack["schema"] != "quick-author-inspection-ack-v1" || ack["author"] != binding["author"] || ack["root"] != root || ack["baseline_source_sha256"] != baseline || ack["inventory_sha256"] != inventorySHA || ack["packet_sha256"] != digestBytes(packet) || ack["run_id"] != binding["run_id"] || ack["client_sha256"] != quickApprovedManualClient || !same(ack["exposure_urls"], binding["exposure_urls"]) || !arrayShape(ack["items"], len(U), len(U)) {
		return fmt.Errorf("quick cache genuine fresh author acknowledgement context/coverage")
	}
	inspected, e := bridgeTime(ack["acknowledged_at"])
	if e != nil || inspected.After(created) || !sealed.After(inspected) {
		return fmt.Errorf("quick cache inspection/Root binding/new seal chronology")
	}
	if e = cacheControls(binding, inputs, U, inspected); e != nil {
		return e
	}
	controls, _ := cacheObject(inputs, binding["source_controls"])
	controlsChecked, _ := bridgeTime(controls["checked_at"])
	journal, e := cacheJournal(inputs, binding["first_receipt_journal"])
	if e != nil {
		return e
	}
	attempts, attemptSHAs, observed := map[string]map[string]any{}, []string{}, map[string]bool{}
	originalStarts := map[string]time.Time{}
	for _, v := range rows(binding["attempts"]) {
		ar, _ := cacheRef(v)
		sha := text(ar["sha256"])
		a, e := cacheObject(inputs, v)
		if e != nil {
			return e
		}
		if cacheAttempt(a, binding) != nil || attempts[sha] != nil {
			return fmt.Errorf("quick cache exact actual client-result format")
		}
		attempts[sha] = a
		attemptSHAs = append(attemptSHAs, sha)
		for _, v := range rows(a["captures"]) {
			row := object(v)
			if cacheAttemptRow(row, text(a["schema"])) != nil {
				return fmt.Errorf("quick cache result not successful original author request")
			}
			if row["started_at"] != nil {
				started, err := bridgeTime(row["started_at"])
				if err != nil || started.After(inspected) {
					return fmt.Errorf("quick cache linked original request follows author acknowledgement")
				}
				u := text(row["url"])
				if started.After(originalStarts[u]) {
					originalStarts[u] = started
				}
			}
			r := object(row["receipt"])
			if cacheRawReceipt(r) != nil || row["url"] != r["url"] || !U[text(row["url"])] || !same(r, journal[text(row["url"])]) {
				return fmt.Errorf("quick cache result/exposure truncation")
			}
			observed[text(row["url"])] = true
		}
	}
	sort.Strings(attemptSHAs)
	if !same(attemptSHAs, ack["attempt_sha256s"]) || len(observed) != len(U) {
		return fmt.Errorf("quick cache linked attempt/exposure closure")
	}
	receipts, inspections := map[string]map[string]any{}, map[string]map[string]any{}
	bodyPaths := map[string]bool{}
	for _, v := range rows(evidence["receipts"]) {
		r := object(v)
		u, p := text(r["url"]), text(r["capture_path"])
		if !pendingExact(r, "url", "capture_path", "capture_sha256", "bytes", "fetched_by_role", "fetched_at") || !U[u] || receipts[u] != nil || bodyPaths[p] || len(inputs[p]) < 1 || len(inputs[p]) > MaxBytes || len(inputs[p]) != integer(r["bytes"]) || digestBytes(inputs[p]) != r["capture_sha256"] {
			return fmt.Errorf("quick cache immutable capture/duplicate role/receipt coverage")
		}
		receipts[u] = r
		bodyPaths[p] = true
	}
	for _, v := range rows(ack["items"]) {
		r := object(v)
		u := text(r["url"])
		receipt := receipts[u]
		if !pendingExact(r, "url", "capture_path", "capture_sha256", "bytes", "first_receipt_sha256") || receipt == nil || inspections[u] != nil || r["capture_path"] != receipt["capture_path"] || r["capture_sha256"] != receipt["capture_sha256"] || !same(r["bytes"], receipt["bytes"]) || !authorityDigest(r["first_receipt_sha256"]) {
			return fmt.Errorf("quick cache acknowledgement exact bound body")
		}
		inspections[u] = r
	}
	if !arrayShape(binding["deliveries"], len(U), len(U)) {
		return fmt.Errorf("quick cache exact delivery coverage")
	}
	seen := map[string]bool{}
	for _, v := range rows(binding["deliveries"]) {
		d := object(v)
		u := text(d["url"])
		r := receipts[u]
		a := attempts[text(d["attempt_sha256"])]
		if !pendingExact(d, "url", "first_receipt", "attempt_sha256", "result_row", "requested_role", "delivery_kind", "requested_at", "client_requested_at", "observed_by", "observation_kind") || r == nil || seen[u] || a == nil || d["requested_role"] != "author" || d["observation_kind"] != "observed_by" || integer(d["result_row"]) < 0 || integer(d["result_row"]) >= len(rows(a["captures"])) {
			return fmt.Errorf("quick cache Root delivery identity/result binding")
		}
		seen[u] = true
		if text(object(d["first_receipt"])["path"]) != filepath.Join(text(binding["cache_root"]), digestBytes([]byte(u))+".receipt.json") || text(r["capture_path"]) != filepath.Join(text(binding["cache_root"]), text(r["capture_sha256"])+".body") {
			return fmt.Errorf("quick cache original receipt/capture cache path differs")
		}
		raw, e := cacheObject(inputs, d["first_receipt"])
		if e != nil {
			return e
		}
		firstRef, _ := cacheRef(d["first_receipt"])
		if inspections[u]["first_receipt_sha256"] != firstRef["sha256"] || cacheRawReceipt(raw) != nil || raw["url"] != u || raw["sha256"] != r["capture_sha256"] || !same(raw["bytes"], r["bytes"]) || raw["fetched_by_role"] != r["fetched_by_role"] || !same(raw, journal[u]) {
			return fmt.Errorf("quick cache original earliest receipt/first role differs")
		}
		row := object(rows(a["captures"])[integer(d["result_row"])])
		if row["url"] != u || !same(row["receipt"], raw) || !same(row["started_at"], d["client_requested_at"]) {
			return fmt.Errorf("quick cache actual original result row/time differs")
		}
		first, e := cacheEpoch(raw["fetched_at"])
		if e != nil {
			return e
		}
		display, e := bridgeTime(r["fetched_at"])
		if e != nil || !display.Equal(first) {
			return fmt.Errorf("quick cache original epoch display differs")
		}
		requested, e := bridgeTime(d["requested_at"])
		if e != nil {
			return e
		}
		observed, e := bridgeTime(d["observed_by"])
		if e != nil || observed.Before(first) || observed.Before(requested) || observed.After(inspected) || observed.After(controlsChecked) {
			return fmt.Errorf("quick cache actual observation/inspection chronology")
		}
		if originalStarts[u].After(observed) {
			return fmt.Errorf("quick cache linked original request follows current observation")
		}
		// Available original request precision must precede this actual handoff.
		// Legacy formats omit started_at; retain that absence without guessing.
		if row["started_at"] != nil {
			original, err := bridgeTime(row["started_at"])
			if err != nil || original.After(requested) || original.After(observed) {
				return fmt.Errorf("quick cache original client request follows current handoff")
			}
		}
		switch d["delivery_kind"] {
		case "cache_hit":
			if first.After(requested) {
				return fmt.Errorf("quick cache hit predates original fetch")
			}
		case "new_response":
			if d["client_requested_at"] == nil || d["client_requested_at"] != d["requested_at"] || first.Before(requested) {
				return fmt.Errorf("quick cache new response reuses earlier fetch")
			}
		default:
			return fmt.Errorf("quick cache unknown delivery kind")
		}
	}
	return nil
}

func bridgeCacheContext(pending map[string]any, files *quickBridgeFiles) (map[string]any, error) {
	pin := files.cachePin
	b, ok := files.blobs[pin.Path]
	if !ok || pin.Path == "" || digestBytes(b) != pin.SHA256 || object(pending["bindings"])["author_cache_binding_sha256"] != pin.SHA256 {
		return nil, fmt.Errorf("quick bridge cache independent context missing")
	}
	binding, e := pendingDecode(b, MaxBytes)
	if e != nil {
		return nil, e
	}
	return map[string]any{"binding": map[string]any{"path": pin.Path, "sha256": pin.SHA256}, "exposure_urls": binding["exposure_urls"]}, nil
}

// Additive history envelope only. The unchanged history verifier still receives
// and checks every original same-role judgment, retained source and occurrence.
func bridgeHistoryWithCache(snap *quickPendingSnapshot, pending, closure map[string]any, names map[string]string, material map[string]map[string]any, files *quickBridgeFiles) error {
	if object(pending["bindings"])["author_cache_binding_sha256"] == nil {
		return bridgeHistory(snap, pending, closure, names, material, files)
	}
	context, e := bridgeCacheContext(pending, files)
	if e != nil {
		return e
	}
	if !pendingExact(closure, "schema", "pending_sha256", "registry_sha256", "items", "author_cache_context") || closure["schema"] != "quick-history-closure-v2" || !same(closure["author_cache_context"], context) {
		return fmt.Errorf("quick history v2 complete exposure context required")
	}
	original := object(clone(closure))
	delete(original, "author_cache_context")
	original["schema"] = "quick-history-closure-v1"
	return bridgeHistory(snap, pending, original, names, material, files)
}

// These are the three immutable actual M3 result formats, not a new producer or
// a policy adoption. Missing historical start/end precision stays missing.
func cacheAttempt(a, binding map[string]any) error {
	valid := false
	switch a["schema"] {
	case "cat-m3-actual-author-source-capture-attempt-1":
		valid = pendingExact(a, "all_cache_first_fetch_roles_retained", "author_capture_seal_yet", "author_context", "cache", "captures", "client_sha256", "schema", "source_judgment_or_admission") && a["author_context"] == binding["author_context"] && a["cache"] == binding["cache_root"] && a["all_cache_first_fetch_roles_retained"] == true && a["author_capture_seal_yet"] == false && a["client_sha256"] == quickApprovedManualClient && a["source_judgment_or_admission"] == nil
	case "cat-m3-additional-actual-author-captures-1":
		valid = pendingExact(a, "schema", "captures", "no_source_approval_or_seal", "whole_original_URLset_and_first_roles_retained") && a["no_source_approval_or_seal"] == true && a["whole_original_URLset_and_first_roles_retained"] == true
	case "cat-m3-final-bounded-author-captures-1":
		valid = pendingExact(a, "schema", "captures", "original_URLsets_first_roles_and_all_prior_attempts_preserved", "source_approval") && a["original_URLsets_first_roles_and_all_prior_attempts_preserved"] == true && a["source_approval"] == nil
	}
	if !valid || !arrayShape(a["captures"], 1, 4096) {
		return fmt.Errorf("quick cache actual result schema/retention/source boundary")
	}
	return nil
}
func cacheAttemptRow(row map[string]any, schema string) error {
	valid := false
	if schema == "cat-m3-actual-author-source-capture-attempt-1" {
		valid = pendingExact(row, "exit", "receipt", "requested_role", "started_at", "stderr", "url") && row["stderr"] == ""
		if _, e := bridgeTime(row["started_at"]); e != nil {
			return e
		}
	} else {
		valid = pendingExact(row, "exit", "receipt", "requested_role", "error", "url") && row["error"] == ""
	}
	if !valid || integer(row["exit"]) != 0 || row["requested_role"] != "author" {
		return fmt.Errorf("quick cache original result row status/role/shape")
	}
	return nil
}
