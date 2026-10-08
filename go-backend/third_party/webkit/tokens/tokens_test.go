package tokens

import (
	"encoding/json"
	"os"
	"strings"
	"testing"
)

func TestGeneratedDTCGContract(t *testing.T) {
	data, err := os.ReadFile("testdata/tokens.json")
	if err != nil { t.Fatal(err) }
	var source struct { Base map[string]map[string]struct { Type string `json:"$type"`; Value json.RawMessage `json:"$value"` } `json:"base"` }
	if err := json.Unmarshal(data, &source); err != nil { t.Fatal(err) }
	if len(source.Base) != 6 { t.Fatal("expected all six DTCG token groups") }
	for group, entries := range source.Base { for name, token := range entries {
		if token.Type == "" || strings.TrimSpace(string(token.Value)) == "" { t.Fatalf("invalid DTCG token %s/%s", group, name) }
	} }
	var color struct { Hex string `json:"hex"` }; var space struct { Value float64 `json:"value"`; Unit string `json:"unit"` }; var font []string
	if err := json.Unmarshal(source.Base["color"]["primary"].Value, &color); err != nil { t.Fatal(err) }
	if err := json.Unmarshal(source.Base["space"]["md"].Value, &space); err != nil { t.Fatal(err) }
	if err := json.Unmarshal(source.Base["font"]["body"].Value, &font); err != nil { t.Fatal(err) }
	if ColorPrimary != color.Hex || SpaceMd != "16px" || space.Value != 16 || space.Unit != "px" || FontBody != strings.Join(font, ", ") { t.Fatal("server token constants differ from typed DTCG fixture") }
}
