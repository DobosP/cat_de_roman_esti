package health

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestIdentityHashesActualBytesAndServesWitness(t *testing.T) {
	manifest := []byte(`{"main":{"file":"app-12345678.js"}}`)
	versions := []byte(`{"schema":1,"core_tag":"core-v1.0"}`)
	i, err := NewIdentity(strings.Repeat("a",40),strings.Repeat("b",64),manifest,versions)
	if err != nil { t.Fatal(err) }
	if i.ManifestSHA256 != "48dcec4ab44ce932d050cd398c2644e158f557d375669aaddb0e52ac05ec894a" || i.VersionsLockSHA256 != "830cf774a8eb6bc0fa9dedee581de45cebeccd5aa9e289dd5b78140150647606" {
		t.Fatalf("identity byte hashes wrong: %s %s",i.ManifestSHA256,i.VersionsLockSHA256)
	}
	w := httptest.NewRecorder()
	i.Handler().ServeHTTP(w,httptest.NewRequest("GET","/__gate/identity",nil))
	var decoded Identity
	if err := json.Unmarshal(w.Body.Bytes(),&decoded); err != nil { t.Fatal(err) }
	if decoded != *i || w.Code != 200 || w.Header().Get("Cache-Control") != "no-store" || w.Header().Get("Content-Type") != "application/json" { t.Fatal("HTTP identity contract diverged") }
	manifest[0]='['
	versions[0]='['
	if err := i.Validate(); err != nil { t.Fatal("caller byte mutation changed immutable hashes") }
	w = httptest.NewRecorder()
	i.ServeHTTP(w,httptest.NewRequest("HEAD","/__gate/identity",nil))
	if w.Code != 200 || w.Body.Len() != 0 { t.Fatal("HEAD identity response wrong") }
	w = httptest.NewRecorder()
	i.ServeHTTP(w,httptest.NewRequest("POST","/__gate/identity",nil))
	if w.Code != http.StatusMethodNotAllowed { t.Fatal("identity accepted mutation method") }
}

func TestIdentityRejectsInvalidAndEmptyEvidence(t *testing.T) {
	sha,tree := strings.Repeat("a",40),strings.Repeat("b",64)
	for _, bad := range []struct {sha,tree string;manifest,versions []byte}{
		{"",tree,[]byte(`{}`),[]byte(`{}`)},
		{sha,"",[]byte(`{}`),[]byte(`{}`)},
		{strings.Repeat("0",40),tree,[]byte(`{}`),[]byte(`{}`)},
		{sha,strings.Repeat("0",64),[]byte(`{}`),[]byte(`{}`)},
		{strings.Repeat("A",40),tree,[]byte(`{}`),[]byte(`{}`)},
		{sha,strings.Repeat("z",64),[]byte(`{}`),[]byte(`{}`)},
		{sha,tree,nil,[]byte(`{}`)},
		{sha,tree,[]byte(`{}`),nil},
		{sha,tree,[]byte(`not JSON`),[]byte(`{}`)},
		{sha,tree,[]byte(`null`),[]byte(`{}`)},
		{sha,tree,[]byte(`{}`),[]byte(`[]`)},
		{sha,tree,[]byte(`{}`),[]byte(` `)},
	} {
		if i,err := NewIdentity(bad.sha,bad.tree,bad.manifest,bad.versions); err==nil || i!=nil { t.Fatal("invalid identity was constructed") }
	}
	for _,i := range []*Identity{nil,{}, {SHA:sha,TreeSHA256:tree}} {
		w := httptest.NewRecorder()
		i.Handler().ServeHTTP(w,httptest.NewRequest("GET","/__gate/identity",nil))
		if w.Code != 500 || strings.Contains(w.Body.String(),`"sha"`) { t.Fatal("invalid HTTP witness was served") }
	}
}
