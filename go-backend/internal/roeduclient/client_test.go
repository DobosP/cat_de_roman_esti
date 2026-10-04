package roeduclient

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
)

func TestFetchRefusalsAndNoPartialResults(t *testing.T) {
	identity := "live-" + strings.Repeat("a", 64)
	cases := map[string][]string{
		"refused":          {`{"available":false,"records":[{"id":"unsafe"}]}`},
		"torn":             {`{"available":false,"note":"snapshot changed during read"}`},
		"repeat":           {`{"available":true,"records":[{"id":"a"}],"next_cursor":"same"}`, `{"available":true,"records":[{"id":"b"}],"next_cursor":"same"}`},
		"duplicate":        {`{"available":true,"records":[{"id":"a"},{"id":"a"}]}`},
		"null_records":     {`{"available":true,"records":null}`},
		"bad_snapshot":     {`{"available":true,"records":[],"snapshot_id":"live-bad"}`},
		"newline_snapshot": {`{"available":true,"records":[],"snapshot_id":"` + identity + `\n"}`},
		"changed_snapshot": {`{"available":true,"records":[],"snapshot_id":"` + identity + `","next_cursor":"n"}`, `{"available":true,"records":[],"snapshot_id":"live-` + strings.Repeat("b", 64) + `"}`},
		"invalid_release":  {`{"available":true,"records":[],"snapshot_id":"` + identity + `","release_id":"` + identity + `"}`},
		"trailing":         {`{"available":true,"records":[]} {}`},
		"over_cap":         {`{"available":true,"records":[{"id":"a"},{"id":"b"},{"id":"c"}]}`},
		"page_cap":         {`{"available":true,"records":[],"next_cursor":"one"}`, `{"available":true,"records":[],"next_cursor":"two"}`},
	}
	for name, responses := range cases {
		t.Run(name, func(t *testing.T) {
			n := 0
			s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.Header.Get("X-API-Key") != "fixture-key" {
					t.Error("key missing")
				}
				at := min(n, len(responses)-1)
				n++
				_, _ = w.Write([]byte(responses[at]))
			}))
			defer s.Close()
			limits := Limits{PageSize: 2, Pages: 2, Records: 3, PageBytes: 1024}
			c, err := New(s.URL, "fixture-key", limits)
			if err != nil {
				t.Fatal(err)
			}
			p, err := c.Fetch(context.Background(), "kg_nodes", nil, 2)
			if err == nil || len(p.Records) != 0 {
				t.Fatalf("partial accepted %#v %v", p, err)
			}
		})
	}
}
func TestBoundedBytesAndRedirectKeyRefusal(t *testing.T) {
	received := false
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { received = true }))
	defer target.Close()
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v1/health" {
			http.Redirect(w, r, target.URL, 302)
			return
		}
		w.Write([]byte(strings.Repeat("x", 100)))
	}))
	defer s.Close()
	c, _ := New(s.URL, "private-fixture-key", Limits{2, 2, 2, 10})
	if _, err := c.Health(context.Background()); err == nil || received {
		t.Fatal("redirect forwarded key")
	}
	if _, err := c.Fetch(context.Background(), "kg_nodes", nil, 2); err == nil {
		t.Fatal("byte cap bypass")
	}
	for _, base := range []string{"file:///etc/passwd", "http://user:pass@localhost", "http://localhost?q=x"} {
		if _, err := New(base, "", DefaultLimits()); err == nil {
			t.Fatal("unsafe URL accepted")
		}
	}
}
func TestLegalFixtureImportPreservesProvenanceAndMixedUnion(t *testing.T) {
	snapshot := "sha256-" + strings.Repeat("c", 64)
	legal := func(id string) Record {
		return Record{"id": id, "redistributable": true, "gdpr_relevant": false, "legal_basis": "fixture-only-license", "access_type": "open_license", "provenance": Record{"source_url": "https://example.invalid/fixture", "sha256": "fixture-hash"}}
	}
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		records := []Record{}
		switch r.URL.Path {
		case "/v1/products/kg_nodes":
			for _, id := range []string{"s", "t"} {
				if r.URL.Query().Get("category") != "" && id == "t" {
					continue
				}
				n := legal(id)
				n["label_ro"] = id
				records = append(records, n)
			}
		case "/v1/products/kg_edges":
			e := legal("e")
			e["src_id"] = "s"
			e["dst_id"] = "t"
			records = append(records, e)
		case "/v1/products/kg_puzzles":
			if r.URL.Query().Get("category") == "mixed" {
				p := legal("p")
				p["start_id"] = "s"
				p["target_id"] = "t"
				p["solution_path"] = []string{"s", "t"}
				records = append(records, p)
			}
		}
		json.NewEncoder(w).Encode(Page{Available: true, Records: records, SnapshotID: snapshot, ReleaseID: &snapshot})
	}))
	defer s.Close()
	c, _ := New(s.URL, "", DefaultLimits())
	b, err := c.Load(context.Background(), "istorie", "easy")
	if err != nil {
		t.Fatal(err)
	}
	if len(b.Nodes) != 2 || len(b.Puzzles) != 1 || b.Nodes[0]["provenance"] == nil || b.Meta["snapshot_id"] != snapshot {
		t.Fatal(b)
	}
	if !PublicLegal(legal("l")) {
		t.Fatal("legal refused")
	}
	for _, key := range []string{"gdpr_relevant", "redistributable", "legal_basis", "access_type"} {
		r := legal("n")
		delete(r, key)
		if PublicLegal(r) {
			t.Fatal("unknown legal field accepted", key)
		}
	}
}
func TestUnknownProductsAndReservedFilters(t *testing.T) {
	c, _ := New("http://127.0.0.1", "", DefaultLimits())
	if _, err := c.Page(context.Background(), "accounts", "", nil); err == nil {
		t.Fatal("unknown product")
	}
	if _, err := c.Page(context.Background(), "kg_nodes", "", url.Values{"cursor": {"override"}}); err == nil {
		t.Fatal("cursor override")
	}
}

func TestWireCannotEraseRefusalOrReplaceUnicode(t *testing.T) {
	for _, raw := range [][]byte{
		[]byte(`{"available":false,"available":true,"records":[]}`),
		[]byte(`{"available":true,"records":[{"id":"n","label_ro":"\ud800"}]}`),
		[]byte(`{"available":false,"avail\u0061ble":true,"records":[]}`),
		[]byte(`{"available":true,"records":[{"id":"n","redistributable":false,"redistributable":true}]}`),
		append([]byte(`{"available":true,"records":[{"id":"n","label_ro":"`), append([]byte{0xff}, []byte(`"}]}`)...)...),
		[]byte(strings.Repeat("[", 66) + "0" + strings.Repeat("]", 66)),
	} {
		if validateWire(raw) == nil {
			t.Fatal("ambiguous or invalid wire input accepted")
		}
	}
	if err := validateWire([]byte(`{"available":true,"records":[],"provenance":{"source_url":"https://example.invalid"}}`)); err != nil {
		t.Fatal(err)
	}
}
