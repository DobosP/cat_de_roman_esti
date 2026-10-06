package alchimie_explore_test

import (
	"bytes"
	"compress/gzip"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
)

// These empty constants are replaced only by a recorded scratch Go test overlay
// for the pre-installation prospective audit. Normal gates use the sealed bundle.
const v15ProspectiveWorld = ""
const v15ProspectiveTranscript = ""
const hotChocolateID = "alw_food_ciocolata_calda"
const milkID = "n_v4gas_lapte"
const chocolateID = "n_v85_food_ciocolata"

type v15Journey struct {
	t    *testing.T
	rows []map[string]any
}

func (j *v15Journey) request(h http.Handler, label, method, path string, body any, status int) map[string]any {
	j.t.Helper()
	encoded, _ := json.Marshal(body)
	if body == nil {
		encoded = []byte("{}")
	}
	r := httptest.NewRequest(method, "http://localhost"+path, bytes.NewReader(encoded))
	r.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	var out map[string]any
	if e := json.Unmarshal(w.Body.Bytes(), &out); e != nil {
		j.t.Fatalf("%s invalid JSON: %v", label, e)
	}
	j.rows = append(j.rows, map[string]any{"label": label, "method": method, "path": path, "request": body, "status": w.Code, "response": out})
	if w.Code != status {
		j.t.Fatalf("%s HTTP%d expected%d: %s", label, w.Code, status, w.Body.String())
	}
	return out
}
func (j *v15Journey) create(h http.Handler, label string, progress any) map[string]any {
	body := map[string]any{}
	if progress != nil {
		body["progress"] = progress
	}
	return j.request(h, label, "POST", "/api/alchimie/explore", body, 200)
}
func (j *v15Journey) combine(h http.Handler, state map[string]any, label, a, b string, status int) map[string]any {
	return j.request(h, label, "POST", "/api/alchimie/explore/"+state["game_id"].(string)+"/combine", map[string]any{"a": a, "b": b}, status)
}
func (j *v15Journey) get(h http.Handler, state map[string]any, label string) map[string]any {
	return j.request(h, label, "GET", "/api/alchimie/explore/"+state["game_id"].(string), nil, 200)
}
func (j *v15Journey) save() {
	if v15ProspectiveTranscript == "" {
		return
	}
	b, e := json.MarshalIndent(j.rows, "", "  ")
	if e != nil {
		j.t.Error(e)
		return
	}
	if e = os.WriteFile(v15ProspectiveTranscript, append(b, '\n'), 0600); e != nil {
		j.t.Error(e)
	}
}
func v15Before(t *testing.T) *content.Content {
	t.Helper()
	raw, e := os.ReadFile("testdata/bundled-v1-4.json.gz")
	if e != nil {
		t.Fatal(e)
	}
	z, e := gzip.NewReader(bytes.NewReader(raw))
	if e != nil {
		t.Fatal(e)
	}
	b, e := io.ReadAll(io.LimitReader(z, 8<<20))
	if e != nil {
		t.Fatal(e)
	}
	z.Close()
	if fmt.Sprintf("%x", sha256.Sum256(b)) != "d1d3f721525e06f247727d6998bd91a9e38bf26610bde9eba55406dabcfd54c2" {
		t.Fatal("whole Source4 bundle archive drift")
	}
	c, e := content.Decode(b)
	if e != nil {
		t.Fatal(e)
	}
	return c
}
func v15After(t *testing.T) *content.Content {
	t.Helper()
	c, e := content.Load()
	if e != nil {
		t.Fatal(e)
	}
	if v15ProspectiveWorld != "" {
		if !filepath.IsAbs(v15ProspectiveWorld) {
			t.Fatal("prospective path must be explicit")
		}
		raw, e := contentbuild.ReadObject(v15ProspectiveWorld, 2<<20)
		if e != nil {
			t.Fatal(e)
		}
		normalized, e := contentbuild.ValidateDiscoveryWorld(raw, graph.New(c))
		if e != nil {
			t.Fatal(e)
		}
		c.DiscoveryWorld = normalized
	}
	return c
}
func v15Inventory(s map[string]any) map[string]map[string]any {
	out := map[string]map[string]any{}
	for _, v := range s["inventory"].([]any) {
		r := v.(map[string]any)
		out[r["id"].(string)] = r
	}
	return out
}
func v15Private(t *testing.T, s map[string]any) {
	t.Helper()
	b, _ := json.Marshal(s)
	if bytes.Contains(b, []byte(hotChocolateID)) || bytes.Contains(b, []byte("Ciocolată caldă")) {
		t.Fatal("undiscovered hot chocolate leaked")
	}
	if s["recipes"] != nil {
		t.Fatal("private recipe map leaked")
	}
	for _, v := range s["goals"].([]any) {
		g := v.(map[string]any)
		if g["completed"] == false && g["target_id"] != nil {
			t.Fatal("undiscovered goal ID leaked")
		}
	}
}
func v15StateOnly(s map[string]any) map[string]any {
	out := map[string]any{}
	for k, v := range s {
		switch k {
		case "message", "discovered", "supplied", "result", "already_known":
			continue
		}
		out[k] = v
	}
	return out
}
func (j *v15Journey) earnChocolate(h http.Handler, label string) map[string]any {
	s := j.create(h, label+"-create", nil)
	v15Private(j.t, s)
	if s["discovered_count"] != float64(0) || len(v15Inventory(s)) != 8 || v15Inventory(s)[milkID] == nil || v15Inventory(s)[chocolateID] != nil {
		j.t.Fatal("starter inventory changed")
	}
	before := j.get(h, s, label+"-initial-get")
	if !reflect.DeepEqual(s, before) {
		j.t.Fatal("initial Get drift")
	}
	j.combine(h, s, label+"-unearned-refusal", milkID, chocolateID, 400)
	if !reflect.DeepEqual(before, j.get(h, s, label+"-refused-get")) {
		j.t.Fatal("unearned refusal mutated state")
	}
	b, e := os.ReadFile("../alchimie/testdata/python_parity.json")
	if e != nil {
		j.t.Fatal(e)
	}
	var trace map[string]any
	if e = json.Unmarshal(b, &trace); e != nil {
		j.t.Fatal(e)
	}
	for i, v := range trace["explore"].([]any) {
		if i < 3 || i > 18 {
			continue
		}
		r := v.(map[string]any)
		if r["action"] != "combine" {
			j.t.Fatal("frozen earning trace drift")
		}
		s = j.combine(h, s, fmt.Sprintf("%s-earn-%d", label, i-2), r["a"].(string), r["b"].(string), 200)
		if s["discovered_count"] != float64(i-2) || len(s["discovered"].([]any)) != 1 {
			j.t.Fatal("legitimate earning prefix changed")
		}
		v15Private(j.t, s)
	}
	if v15Inventory(s)["n_v85_food_cacao"] == nil || v15Inventory(s)["n_v86_food_lapte_praf"] == nil {
		j.t.Fatal("cofetarie supplies not earned at16")
	}
	s = j.combine(h, s, label+"-earn-chocolate", "n_v85_food_cacao", "n_v86_food_lapte_praf", 200)
	if s["discovered_count"] != float64(17) || s["result"].(map[string]any)["id"] != chocolateID {
		j.t.Fatal("existing chocolate recipe changed")
	}
	v15Private(j.t, s)
	if !reflect.DeepEqual(v15StateOnly(s), j.get(h, s, label+"-chocolate-get")) {
		j.t.Fatal("earned Get mismatch")
	}
	return s
}
func (j *v15Journey) discover(h http.Handler, s map[string]any, label string) map[string]any {
	before := s["progress"].(map[string]any)["discoveries"]
	s = j.combine(h, s, label+"-new-drink", milkID, chocolateID, 200)
	if s["discovered_count"] != float64(18) || len(s["discovered"].([]any)) != 1 || s["result"].(map[string]any)["id"] != hotChocolateID || s["already_known"] != false {
		j.t.Fatal("new beverage not one earned discovery")
	}
	row := v15Inventory(s)[hotChocolateID]
	if row["label"] != "Ciocolată caldă" || len(row["parents"].([]any)) != 2 || len(row["sources"].([]any)) == 0 || !bytes.Contains([]byte(row["explanation"].(string)), []byte("încălzit")) {
		j.t.Fatal("reviewed meaning/parents/source absent")
	}
	parents := map[string]bool{}
	for _, raw := range row["parents"].([]any) {
		parents[raw.(map[string]any)["id"].(string)] = true
	}
	if len(parents) != 2 || !parents[milkID] || !parents[chocolateID] {
		j.t.Fatal("new recipe parents differ")
	}
	after := s["progress"].(map[string]any)["discoveries"].([]any)
	if !reflect.DeepEqual(before, after[:17]) {
		j.t.Fatal("prior discoveries changed")
	}
	got := j.get(h, s, label+"-new-get")
	if !reflect.DeepEqual(v15StateOnly(s), got) {
		j.t.Fatal("new Get drift")
	}
	repeated := j.combine(h, s, label+"-repeat", chocolateID, milkID, 200)
	if repeated["already_known"] != true || len(repeated["discovered"].([]any)) != 0 || !reflect.DeepEqual(repeated["progress"], s["progress"]) {
		j.t.Fatal("repeat spent discovery capacity")
	}
	if repeated["discovered_count"] != float64(18) || !reflect.DeepEqual(repeated["inventory"], s["inventory"]) || !reflect.DeepEqual(repeated["unlocked"], s["unlocked"]) || v15Inventory(repeated)[milkID] == nil || v15Inventory(repeated)[chocolateID] == nil {
		j.t.Fatal("repeat changed earned inventory/supplies")
	}
	if !reflect.DeepEqual(v15StateOnly(repeated), j.get(h, repeated, label+"-repeat-get")) {
		j.t.Fatal("repeat Get mismatch")
	}
	return repeated
}
func TestV15HotChocolateEarnedDiscoveryAndNewServiceRestore(t *testing.T) {
	j := &v15Journey{t: t}
	defer j.save()
	old := httpapi.New(v15Before(t))
	oldState := j.earnChocolate(old, "old")
	oldProgress := oldState["progress"]
	oldProgressBytes, _ := json.Marshal(oldProgress)
	oldInventory := v15Inventory(oldState)
	empty := j.combine(old, oldState, "old-empty", milkID, chocolateID, 200)
	if empty["result"] != nil || len(empty["discovered"].([]any)) != 0 || len(empty["empty_pairs"].([]any)) != 1 || !reflect.DeepEqual(empty["progress"], oldProgress) {
		t.Fatal("old pair/save baseline differs")
	}
	after := httpapi.New(v15After(t))
	fresh := j.earnChocolate(after, "candidate")
	j.discover(after, fresh, "candidate")
	// A distinct service has its own sessions. Restore earned progress, not old
	// ephemeral observations or a fabricated inventory.
	resumedService := httpapi.New(v15After(t))
	j.request(resumedService, "old-session-is-not-shared", "GET", "/api/alchimie/explore/"+oldState["game_id"].(string), nil, 404)
	restored := j.create(resumedService, "restore-old17", oldProgress)
	v15Private(t, restored)
	if restored["discovered_count"] != float64(17) || len(restored["empty_pairs"].([]any)) != 0 || !reflect.DeepEqual(restored["progress"].(map[string]any)["discoveries"], oldProgress.(map[string]any)["discoveries"]) || restored["progress"].(map[string]any)["recipe_hash"] == oldProgress.(map[string]any)["recipe_hash"] {
		t.Fatal("old save migration changed earned discoveries")
	}
	for id, entry := range oldInventory {
		got := v15Inventory(restored)[id]
		if got == nil || got["label"] != entry["label"] || !reflect.DeepEqual(got["parents"], entry["parents"]) {
			t.Fatalf("old earned concept lost %s", id)
		}
	}
	afterRestore := j.discover(resumedService, restored, "restored")
	currentService := httpapi.New(v15After(t))
	current := j.create(currentService, "restore-current18", afterRestore["progress"])
	if current["discovered_count"] != float64(18) || v15Inventory(current)[hotChocolateID] == nil || !reflect.DeepEqual(current["progress"], afterRestore["progress"]) {
		t.Fatal("new discovery save lost")
	}
	hinted := j.request(currentService, "current-hint", "POST", "/api/alchimie/explore/"+current["game_id"].(string)+"/hint", nil, 200)
	hint := hinted["hint"].(map[string]any)
	if hint["stage"] != "output" || hint["pair"] != nil || hint["output"].(map[string]any)["id"] != nil {
		t.Fatal("first earned hint exposed private IDs/pair")
	}
	paired := j.request(currentService, "current-pair-hint", "POST", "/api/alchimie/explore/"+current["game_id"].(string)+"/hint", nil, 200)
	pairHint := paired["hint"].(map[string]any)
	if pairHint["stage"] != "pair" || len(pairHint["pair"].([]any)) != 2 || paired["recipes"] != nil {
		t.Fatal("second hint protocol/private recipes changed")
	}
	for _, raw := range pairHint["pair"].([]any) {
		if v15Inventory(current)[raw.(map[string]any)["id"].(string)] == nil {
			t.Fatal("hint used unearned ingredient")
		}
	}
	for _, state := range []map[string]any{hinted, paired} {
		if !reflect.DeepEqual(state["progress"], current["progress"]) || !reflect.DeepEqual(state["inventory"], current["inventory"]) || state["discovered_count"] != float64(18) {
			t.Fatal("hint changed earned progress")
		}
	}
	if !reflect.DeepEqual(paired, j.get(currentService, paired, "hint-get")) {
		t.Fatal("earned hint Get mismatch")
	}
	stillEmpty := j.combine(old, oldState, "old-service-remains-old", milkID, chocolateID, 200)
	if stillEmpty["result"] != nil || !reflect.DeepEqual(stillEmpty["progress"], oldProgress) {
		t.Fatal("old service unexpectedly hot-reloaded")
	}
	unchanged, _ := json.Marshal(oldProgress)
	if !bytes.Equal(unchanged, oldProgressBytes) {
		t.Fatal("caller save was mutated")
	}
	t.Logf("old17 preserved; new18th discovery; restore/repeat/private states checked through %d HTTP requests", len(j.rows))
}
