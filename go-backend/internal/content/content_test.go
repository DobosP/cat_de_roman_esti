package content

import (
	"bytes"
	"encoding/json"
	"testing"
)

func TestEmbeddedContentFailsClosed(t *testing.T) {
	c, err := Load()
	if err != nil {
		t.Fatal(err)
	}
	intrusul:=0;for _,b:=range c.Boards{if b.Game=="intrusul"{intrusul++}}
	if intrusul != 226 {
		t.Fatalf("reviewed Intrusul pool drift: %d", len(c.Boards))
	}
	if _, err = Decode(append(bytes.Clone(bundled), []byte(" {}")...)); err == nil {
		t.Fatal("trailing JSON accepted")
	}
	original := bundled
	defer func() { bundled = original }()
	bundled = bytes.Replace(original, []byte(`"schema_version":2`), []byte(`"schema_version":9`), 1)
	if _, err = Load(); err == nil {
		t.Fatal("modified embedded export accepted")
	}
}

func TestManifestIdentityRequired(t *testing.T) {
	var value map[string]any
	if err := json.Unmarshal(bundled, &value); err != nil {
		t.Fatal(err)
	}
	value["manifest"] = map[string]any{}
	data, _ := json.Marshal(value)
	if _, err := Decode(data); err == nil {
		t.Fatal("empty manifest accepted")
	}
}
