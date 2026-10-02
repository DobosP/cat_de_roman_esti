package alchimie

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
	"math/big"
	"os"
	"reflect"
	"testing"
)

func golden(t *testing.T) map[string]any {
	t.Helper()
	raw, e := os.ReadFile("testdata/python_parity.json")
	if e != nil {
		t.Fatal(e)
	}
	var result map[string]any
	if e = json.Unmarshal(raw, &result); e != nil {
		t.Fatal(e)
	}
	return result
}
func load(t *testing.T) *Service {
	t.Helper()
	c, e := content.Load()
	if e != nil {
		t.Fatal(e)
	}
	return New(c)
}
func ids(raw any) []string {
	out := []string{}
	for _, id := range raw.([]any) {
		out = append(out, id.(string))
	}
	return out
}
func projectionValue(p *Projection) any {
	if p == nil {
		return nil
	}
	rows := []Step{}
	for _, key := range recipePairs(p.Recipes) {
		rows = append(rows, Step{key, p.Recipes[key]})
	}
	v := map[string]any{"recipes": rows, "routes": p.Routes, "par": p.Par, "candidate_quality": p.CandidateQuality}
	raw, _ := json.Marshal(v)
	var normalized any
	_ = json.Unmarshal(raw, &normalized)
	return normalized
}
func stateDigest(p map[string]any) string {
	p["game_id"] = "<session>"
	var b bytes.Buffer
	encoder := json.NewEncoder(&b)
	encoder.SetEscapeHTML(false)
	_ = encoder.Encode(p)
	return fmt.Sprintf("%x", sha256.Sum256(bytes.TrimSuffix(b.Bytes(), []byte("\n"))))
}
func TestAllApprovedCuratedProjectionParity(t *testing.T) {
	s := load(t)
	g := golden(t)
	for _, raw := range g["curated"].([]any) {
		row := raw.(map[string]any)
		t.Run(row["id"].(string), func(t *testing.T) {
			actual := projectionValue(s.projection(ids(row["seeds"]), row["target"].(string), row["category"].(string)))
			if !reflect.DeepEqual(actual, row["projection"]) {
				a, _ := json.Marshal(actual)
				e, _ := json.Marshal(row["projection"])
				t.Fatalf("complete private projection differs (actual bytes%d expected%d)", len(a), len(e))
			}
		})
	}
}
func TestMinedSeedDifficultyParity(t *testing.T) {
	s := load(t)
	for _, raw := range golden(t)["mined"].([]any) {
		r := raw.(map[string]any)
		t.Run(fmt.Sprint(r["seed"]), func(t *testing.T) {
			g, e := s.mine(pyrandom.New(big.NewInt(int64(r["seed"].(float64)))), r["difficulty"].(string), "", "")
			if e != nil {
				t.Fatal(e)
			}
			if !reflect.DeepEqual(g.seeds, ids(r["seeds"])) || g.target != r["target"] || g.category != r["category"] {
				t.Fatalf("mined identity differs: %v %s %s", g.seeds, g.target, g.category)
			}
			v := projectionValue(g.projection).(map[string]any)
			for _, key := range []string{"recipes", "routes", "par"} {
				if !reflect.DeepEqual(v[key], r[key]) {
					t.Fatalf("mined %s differs", key)
				}
			}
			actual := s.state("<session>", g)
			raw, _ := json.Marshal(actual)
			var value any
			_ = json.Unmarshal(raw, &value)
			if !reflect.DeepEqual(value, r["state"]) {
				t.Fatalf("public mined state differs: %s", raw)
			}
		})
	}
}
func TestScoredJourneysAndTerminalResetParity(t *testing.T) {
	s := load(t)
	for _, raw := range golden(t)["challenge_journeys"].([]any) {
		id := ""
		for index, step := range raw.([]any) {
			row := step.(map[string]any)
			var p map[string]any
			var err *Error
			switch row["action"] {
			case "create":
				p, err = s.Create(big.NewInt(int64(row["seed"].(float64))), "", "", "normal")
				if err == nil {
					id = p["game_id"].(string)
				}
			case "combine":
				p, err = s.Combine(id, row["a"].(string), row["b"].(string))
			case "hint":
				p, err = s.Hint(id)
			case "reset":
				p, err = s.Reset(id)
			}
			if err != nil {
				t.Fatal(err)
			}
			if stateDigest(p) != row["hash"] {
				raw, _ := json.Marshal(p)
				t.Fatalf("journey step%d %s differs: %s", index, row["action"], raw)
			}
		}
		s.store.Delete(id)
	}
}
func TestMissingSessionValidationOrderAndExactWhitespace(t *testing.T) {
	s := load(t)
	called := false
	_, e := s.CombineInput("missing", func() (string, string, *Error) { called = true; return "", "", nil })
	if called || e == nil || e.Status != 404 {
		t.Fatal("lookup must precede body validation")
	}
	if pyStrip("\x1c \u2007 id \x1f") != "id" {
		t.Fatal("Python whitespace parity")
	}
}

func TestReviewedExtensionDeclinesMetadataDrift(t *testing.T) {
	c, e := content.Load()
	if e != nil {
		t.Fatal(e)
	}
	board := c.RecipeExtensions["boards"].([]any)[0].(map[string]any)
	core := board["core"].(map[string]any)
	seeds := ids(core["seeds"])
	target, category := core["target"].(string), core["category"].(string)
	s := New(c)
	original := BuildProjection(s.graph, seeds, target, category)
	extended := s.extend(original, seeds, target, category)
	if len(extended.Recipes) <= len(original.Recipes) {
		t.Fatal("fixture did not apply reviewed additions")
	}
	for i := range c.Nodes {
		if c.Nodes[i].ID == seeds[0] {
			c.Nodes[i].Source += "-metadata-drift"
		}
	}
	declined := s.extend(original, seeds, target, category)
	if len(declined.Recipes) != len(original.Recipes) {
		t.Fatal("altered provenance retained reviewed extension")
	}
}

func TestCompactScratchKeysAndIndexedTupleOrdering(t *testing.T) {
	if nodeKey([]uint32{1, 2}) == nodeKey([]uint32{256, 2}) || nodeKey([]uint32{1}) == nodeKey([]uint32{1, 0}) {
		t.Fatal("scratch-state key collision")
	}
	if compareNodes([]uint32{1, 2}, []uint32{1, 3}) >= 0 || compareNodes([]uint32{1}, []uint32{1, 0}) >= 0 {
		t.Fatal("indexed tuple order differs")
	}
	if !reflect.DeepEqual(unionNodes([]uint32{1, 3, 5}, []uint32{2, 3, 8}), []uint32{1, 2, 3, 5, 8}) {
		t.Fatal("indexed inventory union differs")
	}
}
