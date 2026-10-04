// Package contentops implements bounded, offline reviewed-content operators.
// No operator accesses a provider, serves a solution, or changes a live service.
package contentops

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
	"io"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"unicode/utf8"
)

const MaxDocumentBytes = 32 << 20
const MaxRecords = 20000

var Games = []string{"conexiuni", "contexto", "lant", "alchimie"}

const fixtures = "cat_de_roman_esti/fixtures/"

var packCopies = []string{fixtures + "games_pack.json", "tests/fixtures/games_pack.json"}
var prefixes = map[string]string{"conexiuni": "cx", "contexto": "ct", "lant": "lt", "alchimie": "al"}

type Object = map[string]any

func digest(blob []byte) string { return fmt.Sprintf("%x", sha256.Sum256(blob)) }
func textDigest(blob []byte) string {
	return digest(bytes.ReplaceAll(bytes.ReplaceAll(blob, []byte("\r\n"), []byte("\n")), []byte("\r"), []byte("\n")))
}
func str(v any) string { s, _ := v.(string); return s }
func obj(v any) Object { m, _ := v.(map[string]any); return m }
func array(v any) []any {
	switch a := v.(type) {
	case []any:
		return a
	case []string:
		out := make([]any, len(a))
		for i, v := range a {
			out[i] = v
		}
		return out
	case []Object:
		out := make([]any, len(a))
		for i, v := range a {
			out[i] = v
		}
		return out
	}
	return nil
}
func integer(v any) int {
	switch n := v.(type) {
	case json.Number:
		i, e := strconv.Atoi(string(n))
		if e == nil {
			return i
		}
	case int:
		return n
	case float64:
		if n == float64(int(n)) {
			return int(n)
		}
	}
	return -1
}
func number(v any) float64 {
	switch n := v.(type) {
	case json.Number:
		f, _ := n.Float64()
		return f
	case float64:
		return n
	case int:
		return float64(n)
	}
	return 0
}
func nonblank(v any) bool { return str(v) != "" && strings.TrimSpace(str(v)) != "" }
func gameKnown(g string) bool {
	for _, s := range Games {
		if s == g {
			return true
		}
	}
	return false
}
func stringsOf(v any) ([]string, error) {
	a := array(v)
	if a == nil {
		return nil, errors.New("expected string array")
	}
	s := []string{}
	for _, v := range a {
		if str(v) == "" {
			return nil, errors.New("expected nonempty string")
		}
		s = append(s, str(v))
	}
	return s, nil
}
func uniqueStrings(v any) ([]string, error) {
	s, e := stringsOf(v)
	if e != nil {
		return nil, e
	}
	m := map[string]bool{}
	for _, x := range s {
		if m[x] {
			return nil, fmt.Errorf("duplicate %s", x)
		}
		m[x] = true
	}
	return s, nil
}
func exactStrings(a, b []string) bool { return strings.Join(a, "\x00") == strings.Join(b, "\x00") }
func keys(m Object) []string {
	s := []string{}
	for k := range m {
		s = append(s, k)
	}
	sort.Strings(s)
	return s
}
func copyObject(m Object) Object {
	n := Object{}
	for k, v := range m {
		n[k] = v
	}
	return n
}
func validHex(s string) bool {
	if len(s) != 64 {
		return false
	}
	for _, c := range s {
		if !strings.ContainsRune("0123456789abcdef", c) {
			return false
		}
	}
	return true
}
func validBinding(s string) bool {
	return strings.HasPrefix(s, "sha256:") && validHex(strings.TrimPrefix(s, "sha256:"))
}

// Decode rejects duplicate keys, trailing values and invalid UTF-8. The explicit
// record/byte limits apply before any source mutation or queue processing.
func Decode(blob []byte) (Object, error) {
	if len(blob) > MaxDocumentBytes || !utf8.Valid(blob) {
		return nil, errors.New("document exceeds bound or is not UTF-8")
	}
	if err := strictjson.Validate(blob); err != nil {
		return nil, err
	}
	d := json.NewDecoder(bytes.NewReader(blob))
	d.UseNumber()
	v, e := decodeValue(d, 0)
	if e != nil {
		return nil, e
	}
	if _, e = d.Token(); e != io.EOF {
		return nil, errors.New("trailing JSON")
	}
	m, ok := v.(map[string]any)
	if !ok {
		return nil, errors.New("expected JSON object")
	}
	return m, nil
}
func decodeValue(d *json.Decoder, depth int) (any, error) {
	if depth > 64 {
		return nil, errors.New("JSON nesting exceeds bound")
	}
	t, e := d.Token()
	if e != nil {
		return nil, e
	}
	delim, ok := t.(json.Delim)
	if !ok {
		if n, ok := t.(json.Number); ok {
			f, err := n.Float64()
			if err != nil || math.IsNaN(f) || math.IsInf(f, 0) {
				return nil, errors.New("non-finite JSON number refused")
			}
		}
		return t, nil
	}
	switch delim {
	case '{':
		m := Object{}
		for d.More() {
			k, e := d.Token()
			if e != nil {
				return nil, e
			}
			s, ok := k.(string)
			if !ok {
				return nil, errors.New("invalid key")
			}
			if _, ok = m[s]; ok {
				return nil, fmt.Errorf("duplicate JSON key %q", s)
			}
			v, e := decodeValue(d, depth+1)
			if e != nil {
				return nil, e
			}
			m[s] = v
			if len(m) > MaxRecords {
				return nil, errors.New("object exceeds record bound")
			}
		}
		_, e = d.Token()
		return m, e
	case '[':
		a := []any{}
		for d.More() {
			v, e := decodeValue(d, depth+1)
			if e != nil {
				return nil, e
			}
			a = append(a, v)
			if len(a) > MaxRecords {
				return nil, errors.New("array exceeds record bound")
			}
		}
		_, e = d.Token()
		return a, e
	}
	return nil, errors.New("unexpected JSON delimiter")
}
func read(path string) (Object, []byte, error) {
	f, e := os.Open(path)
	if e != nil {
		return nil, nil, e
	}
	defer f.Close()
	b, e := io.ReadAll(io.LimitReader(f, MaxDocumentBytes+1))
	if e != nil {
		return nil, nil, e
	}
	m, e := Decode(b)
	return m, b, e
}
func render(v any) ([]byte, error) {
	var b bytes.Buffer
	e := json.NewEncoder(&b)
	e.SetEscapeHTML(false)
	e.SetIndent("", " ")
	if err := e.Encode(v); err != nil {
		return nil, err
	}
	return b.Bytes(), nil
}

// Canonical preserves Python's JSON numeric distinction for existing portable
// dossier and ledger bindings, while sorting keys and emitting literal UTF-8.
func canonical(v any) []byte {
	b, e := contentbuild.Canonical(v)
	if e != nil {
		panic(e)
	}
	return b
}

func safePath(root, name string) (string, error) {
	p := name
	if !filepath.IsAbs(p) {
		p = filepath.Join(root, p)
	}
	p = filepath.Clean(p)
	resolved, e := filepath.EvalSymlinks(filepath.Dir(p))
	if e != nil {
		return "", e
	}
	if resolved != filepath.Dir(p) {
		return "", errors.New("symlinked output parent refused")
	}
	if info, e := os.Lstat(p); e == nil && info.Mode()&os.ModeSymlink != 0 {
		return "", errors.New("symlinked content file refused")
	}
	return p, nil
}
func atomicWrite(path string, blob []byte, mode os.FileMode) error {
	f, e := os.CreateTemp(filepath.Dir(path), ".cat-content-ops-")
	if e != nil {
		return e
	}
	name := f.Name()
	defer os.Remove(name)
	if e = f.Chmod(mode); e == nil {
		_, e = f.Write(blob)
	}
	if e == nil {
		e = f.Sync()
	}
	ce := f.Close()
	if e == nil {
		e = ce
	}
	if e != nil {
		return e
	}
	if e = os.Rename(name, path); e != nil {
		return e
	}
	d, e := os.Open(filepath.Dir(path))
	if e != nil {
		return e
	}
	defer d.Close()
	return d.Sync()
}

type snapshot struct {
	blob   []byte
	exists bool
	mode   os.FileMode
}

// Transaction locks the operator root, snapshots ALL targets before replacement,
// runs the post-write gate, and restores and byte-verifies every original on error.
func Transaction(root string, changes map[string][]byte, verify func() error) error {
	return transaction(root, changes, verify, nil)
}
func transaction(root string, changes map[string][]byte, verify func() error, afterWrite func(int) error) error {
	return guardedTransaction(root, changes, verify, afterWrite, nil)
}
func guardedTransaction(root string, changes map[string][]byte, verify func() error, afterWrite func(int) error, expected map[string]snapshot) error {
	return guardedTransactionWithInventory(root, changes, verify, afterWrite, expected, nil)
}
func guardedTransactionWithInventory(root string, changes map[string][]byte, verify func() error, afterWrite func(int) error, expected map[string]snapshot, inventory func() error) (result error) {
	lock, e := os.OpenFile(filepath.Join(root, ".cat-content-ops.lock"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return fmt.Errorf("content operator is locked: %w", e)
	}
	defer os.Remove(lock.Name())
	if e = lock.Close(); e != nil {
		return e
	}
	if e := checkSnapshots(expected); e != nil {
		return e
	}
	targets := make([]string, 0, len(changes))
	for p := range changes {
		targets = append(targets, p)
	}
	sort.Strings(targets)
	originals := map[string]snapshot{}
	for _, p := range targets {
		safe, e := safePath(root, p)
		if e != nil {
			return e
		}
		if safe != p {
			return errors.New("transaction requires absolute targets")
		}
		if len(changes[p]) > MaxDocumentBytes {
			return errors.New("transaction document exceeds byte bound")
		}
		s, e := takeSnapshot(p)
		if e != nil {
			return e
		}
		originals[p] = s
	}
	defer func() {
		if result == nil {
			return
		}
		failures := []string{}
		for _, p := range targets {
			s := originals[p]
			if s.exists {
				if e := atomicWrite(p, s.blob, s.mode); e != nil {
					failures = append(failures, e.Error())
				}
			} else if e := os.Remove(p); e != nil && !os.IsNotExist(e) {
				failures = append(failures, e.Error())
			}
		}
		for _, p := range targets {
			s := originals[p]
			b, e := os.ReadFile(p)
			if (s.exists && (e != nil || !bytes.Equal(b, s.blob))) || (!s.exists && !os.IsNotExist(e)) {
				failures = append(failures, "rollback mismatch: "+p)
			}
		}
		if len(failures) > 0 {
			result = fmt.Errorf("%w; rollback incomplete: %s", result, strings.Join(failures, "; "))
		}
	}()
	for i, p := range targets {
		if e = atomicWrite(p, changes[p], originals[p].mode); e != nil {
			return e
		}
		if afterWrite != nil {
			if e = afterWrite(i); e != nil {
				return e
			}
		}
	}
	unchanged := map[string]snapshot{}
	for p, snap := range expected {
		if _, written := changes[p]; !written {
			unchanged[p] = snap
		}
	}
	if e = checkSnapshots(unchanged); e != nil {
		return e
	}
	if inventory != nil {
		if e = inventory(); e != nil {
			return e
		}
	}
	if verify != nil {
		if e = verify(); e != nil {
			return e
		}
	}
	if inventory != nil {
		if e = inventory(); e != nil {
			return e
		}
	}
	return checkSnapshots(unchanged)
}
func mirrors(root string) (Object, []byte, error) {
	var first []byte
	var pack Object
	for _, name := range packCopies {
		m, b, e := read(filepath.Join(root, name))
		if e != nil {
			return nil, nil, e
		}
		if first == nil {
			first = b
			pack = m
		} else if !bytes.Equal(first, b) {
			return nil, nil, errors.New("pack mirror drift")
		}
	}
	return pack, first, nil
}
func packChanges(root string, pack Object) (map[string][]byte, error) {
	b, e := render(pack)
	if e != nil {
		return nil, e
	}
	m := map[string][]byte{}
	for _, p := range packCopies {
		m[filepath.Join(root, p)] = b
	}
	return m, nil
}
func refreshCounts(pack Object) {
	counts := Object{}
	for _, g := range Games {
		counts[g] = len(array(pack[g]))
	}
	meta := obj(pack["meta"])
	if meta == nil {
		meta = Object{}
		pack["meta"] = meta
	}
	meta["counts"] = counts
}
func indexPack(pack Object) (map[string]Object, map[string]string, error) {
	rows := map[string]Object{}
	games := map[string]string{}
	for _, g := range Games {
		a, ok := pack[g].([]any)
		if !ok {
			return nil, nil, fmt.Errorf("missing array %s", g)
		}
		for _, v := range a {
			r := obj(v)
			id := str(r["id"])
			if !safeID(id) || rows[id] != nil {
				return nil, nil, errors.New("empty or duplicate pack ID")
			}
			rows[id] = r
			games[id] = g
		}
	}
	return rows, games, nil
}

func takeSnapshot(path string) (snapshot, error) {
	safe, e := safePath(filepath.Dir(path), path)
	if e != nil {
		return snapshot{}, e
	}
	f, e := os.Open(safe)
	if os.IsNotExist(e) {
		return snapshot{exists: false, mode: 0600}, nil
	}
	if e != nil {
		return snapshot{}, e
	}
	defer f.Close()
	info, e := f.Stat()
	if e != nil {
		return snapshot{}, e
	}
	if !info.Mode().IsRegular() || info.Size() > MaxDocumentBytes {
		return snapshot{}, errors.New("read-set member exceeds bound or is not regular")
	}
	b, e := io.ReadAll(io.LimitReader(f, MaxDocumentBytes+1))
	if e != nil {
		return snapshot{}, e
	}
	if len(b) > MaxDocumentBytes {
		return snapshot{}, errors.New("read-set member exceeds bound")
	}
	return snapshot{b, true, info.Mode().Perm()}, nil
}

func checkSnapshots(expected map[string]snapshot) error {
	for p, old := range expected {
		actual, e := takeSnapshot(p)
		if e != nil {
			return e
		}
		if old.exists != actual.exists || !bytes.Equal(old.blob, actual.blob) || (old.exists && old.mode != actual.mode) {
			return fmt.Errorf("source changed during operator preflight: %s", p)
		}
	}
	return nil
}

func snapshotSources(root string) (map[string]snapshot, error) {
	expected := map[string]snapshot{}
	names := append(append([]string{}, packCopies...), fixtures+"kg_sample.json", "tests/fixtures/kg_sample.json", "docs/CRITIQUE_RUBRIC.md", fixtures+"conexiuni_rejection_tombstones.json", fixtures+"lant_rejection_tombstones.json", fixtures+"alchimie_recipe_extensions_v92.json")
	for _, name := range contentbuild.SourceNames {
		names = append(names, fixtures+name, "tests/fixtures/"+name)
	}
	inventory, e := runtimeInventory(root)
	if e != nil {
		return nil, e
	}
	for _, path := range inventory {
		relative, e := filepath.Rel(root, path)
		if e != nil {
			return nil, e
		}
		names = append(names, relative)
	}
	for _, name := range names {
		path := filepath.Join(root, name)
		snap, e := takeSnapshot(path)
		if e != nil {
			return nil, e
		}
		expected[path] = snap
	}
	return expected, nil
}
func (s *Sources) bindInput(path string) error {
	absolute, e := filepath.Abs(path)
	if e != nil {
		return e
	}
	snap, e := takeSnapshot(absolute)
	if e != nil {
		return e
	}
	if old, exists := s.Inputs[absolute]; exists {
		if old.exists != snap.exists || !bytes.Equal(old.blob, snap.blob) {
			return errors.New("input changed between dependent reads")
		}
	}
	s.Inputs[absolute] = snap
	return nil
}
func (s *Sources) commit(changes map[string][]byte, verify func() error) error {
	return guardedTransactionWithInventory(s.Root, changes, verify, nil, s.Inputs, s.checkInventory)
}
func (s *Sources) reconcileHighWater() {
	water := highWater(s.Pack)
	for _, game := range []string{"conexiuni", "lant"} {
		debt := s.Rejections
		if game == "lant" {
			debt = s.LantRejections
		}
		for _, row := range debt {
			id := str(row["id"])
			parts := strings.Split(id, "_")
			if len(parts) >= 3 && parts[0] == prefixes[game] {
				n, e := strconv.Atoi(parts[len(parts)-1])
				if e == nil {
					water[game] = max(integer(water[game]), n)
				}
			}
		}
	}
	obj(s.Pack["meta"])["id_high_water"] = water
}

func safeID(id string) bool {
	return id != "" && id != "." && id != ".." && len(id) <= 200 && strings.TrimSpace(id) == id && !strings.ContainsAny(id, "/\\\x00\r\n")
}

func validGitSHA(s string) bool {
	if len(s) != 40 {
		return false
	}
	for _, c := range s {
		if !strings.ContainsRune("0123456789abcdef", c) {
			return false
		}
	}
	return true
}

// ReadSet is an immutable snapshot for source-hash-bound offline installers.
// Its entries are opaque so callers cannot silently replace reviewed baselines.
type ReadSet struct{ entries map[string]snapshot }

// CaptureReadSet records bytes, presence and mode without taking a write lock.
// Capture every source and target baseline BEFORE building a prospective result.
func CaptureReadSet(paths []string) (ReadSet, error) {
	expected := map[string]snapshot{}
	for _, path := range paths {
		absolute, e := filepath.Abs(path)
		if e != nil {
			return ReadSet{}, e
		}
		if _, ok := expected[absolute]; ok {
			continue
		}
		snap, e := takeSnapshot(absolute)
		if e != nil {
			return ReadSet{}, e
		}
		expected[absolute] = snap
	}
	return ReadSet{expected}, nil
}

// GuardedTransaction checks the captured read set under the shared operator lock,
// snapshots targets, installs atomically per file, rechecks unchanged inputs and
// runs the caller's final gate. Any failure restores and byte-verifies originals.
// The verify callback must not recursively acquire this shared lock.
func GuardedTransaction(root string, changes map[string][]byte, expected ReadSet, verify func() error) error {
	if len(expected.entries) == 0 {
		return errors.New("missing immutable read set")
	}
	absolute, e := filepath.Abs(root)
	if e != nil {
		return e
	}
	return guardedTransaction(absolute, changes, verify, nil, expected.entries)
}

func validateSourcePackEnvelope(pack Object) error {
	required := append([]string{"meta"}, Games...)
	if !exactKeys(pack, required...) {
		return errors.New("source pack requires meta and four game arrays")
	}
	meta := obj(pack["meta"])
	if meta == nil {
		return errors.New("source pack meta must be an object")
	}
	counts, water := obj(meta["counts"]), obj(meta["id_high_water"])
	if !exactKeys(counts, Games...) || !exactKeys(water, Games...) {
		return errors.New("source pack counts and persistent id_high_water must exactly cover four games")
	}
	for _, game := range Games {
		rows, ok := pack[game].([]any)
		if !ok {
			return fmt.Errorf("source pack %s must be an array", game)
		}
		if integer(counts[game]) != len(rows) || integer(water[game]) < 0 {
			return fmt.Errorf("source pack %s invalid counts or persistent id_high_water", game)
		}
		observed := 0
		for _, v := range rows {
			r := obj(v)
			if r == nil || !safeID(str(r["id"])) {
				return errors.New("source pack record identity invalid")
			}
			parts := strings.Split(str(r["id"]), "_")
			if len(parts) >= 3 && parts[0] == prefixes[game] {
				suffix, e := strconv.Atoi(parts[len(parts)-1])
				if e == nil {
					observed = max(observed, suffix)
				}
			}
		}
		if integer(water[game]) < observed {
			return fmt.Errorf("source pack %s persistent id_high_water below current stock", game)
		}
	}
	return nil
}
