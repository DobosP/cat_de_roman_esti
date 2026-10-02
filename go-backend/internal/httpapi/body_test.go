package httpapi

import (
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
	"net/http/httptest"
	"os"
	"reflect"
	"regexp"
	"strings"
	"testing"
)

// One independently captured Python corpus qualifies both native validators.
func TestFrozenPythonBodyModels(t *testing.T) {
	source, err := os.ReadFile("../../../rust-backend/src/validation.rs")
	if err != nil {
		t.Fatal(err)
	}
	literal := regexp.MustCompile(`(?s)serde_json::from_str\(\s*r###"(.*?)"###\s*\)`).FindSubmatch(source)
	if len(literal) != 2 {
		t.Fatal("Python model reference vectors unavailable")
	}
	var cases []struct {
		Kind, Model, Raw string
		Error            any
	}
	if err = json.Unmarshal(literal[1], &cases); err != nil {
		t.Fatal(err)
	}
	if len(cases) != 32 {
		t.Fatalf("expected32Pythonmodelvectors,got%d", len(cases))
	}
	for index, row := range cases {
		t.Run(fmt.Sprintf("%02d-%s", index, row.Kind), func(t *testing.T) {
			r := httptest.NewRequest("POST", "/", strings.NewReader(row.Raw))
			var failure *gameapi.Error
			switch row.Kind {
			case "ids":
				_, failure = idsBody(r, row.Model)
			case "contexto":
				_, failure = fields(r, "GuessBody", []fieldRule{{Name: "text", Kind: "string"}, {Name: "confirm", Kind: "string", Optional: true, Nullable: true}}, false)
			case "text":
				_, failure = textBody(r)
			case "pair":
				_, _, failure = pairBody(r, false)
			case "strict_pair":
				_, _, failure = pairBody(r, true)
			case "goal":
				_, failure = goalBody(r)
			case "create":
				_, _, failure = exploreCreateBody(r)
			default:
				t.Fatalf("unknownmodel %s", row.Kind)
			}
			if row.Error == nil {
				if failure != nil {
					t.Fatalf("unexpectedvalidation: %v", failure)
				}
				return
			}
			if failure == nil || failure.Status != 422 {
				t.Fatalf("wanted422,got%v", failure)
			}
			encoded, e := json.Marshal(failure.Detail)
			if e != nil {
				t.Fatal(e)
			}
			var detail any
			if e = json.Unmarshal(encoded, &detail); e != nil {
				t.Fatal(e)
			}
			if !reflect.DeepEqual(detail, row.Error) {
				t.Fatalf("model%s raw%s\nactual%s\nexpected%v", row.Model, row.Raw, encoded, row.Error)
			}
		})
	}
}
func errorDetail(t *testing.T, e *gameapi.Error) []map[string]any {
	t.Helper()
	if e == nil || e.Status != 422 {
		t.Fatalf("wanted422,got%v", e)
	}
	return e.Detail.([]map[string]any)
}
func TestNestedProgressErrorOrderAndDuplicateKeyPosition(t *testing.T) {
	raw := `{"z":1,"progress":{"z":1,"a":2,"world_id":"","recipe_hash":"bad","discoveries":[null,["",17,"` + strings.Repeat("ș", 161) + `"]]},"a":2,"goal_id":17,"z":3}`
	_, _, failure := exploreCreateBody(httptest.NewRequest("POST", "/", strings.NewReader(raw)))
	errors := errorDetail(t, failure)
	want := [][]any{{"body", "progress", "world_id"}, {"body", "progress", "recipe_hash"}, {"body", "progress", "discoveries", 0}, {"body", "progress", "discoveries", 1, 0}, {"body", "progress", "discoveries", 1, 1}, {"body", "progress", "discoveries", 1, 2}, {"body", "progress", "z"}, {"body", "progress", "a"}, {"body", "goal_id"}, {"body", "z"}, {"body", "a"}}
	if len(errors) != len(want) {
		t.Fatalf("wrongerrorcount%v", errors)
	}
	for i, loc := range want {
		if !reflect.DeepEqual(errors[i]["loc"], loc) {
			t.Fatalf("error%d location%v wanted%v", i, errors[i]["loc"], loc)
		}
	}
	if errors[9]["input"] != json.Number("3") {
		t.Fatal("duplicate key must keep first position and final value")
	}
}
func TestProgressMaximumOverridesRowErrorsAndRetainsVariablePairCardinality(t *testing.T) {
	rows := make([]any, 257)
	for i := range rows {
		rows[i] = 17
	}
	body := map[string]any{"progress": map[string]any{"world_id": "world", "recipe_hash": strings.Repeat("a", 64), "discoveries": rows}}
	encoded, _ := json.Marshal(body)
	_, _, failure := exploreCreateBody(httptest.NewRequest("POST", "/", strings.NewReader(string(encoded))))
	errors := errorDetail(t, failure)
	if len(errors) != 1 || errors[0]["type"] != "too_long" || errors[0]["msg"] != "List should have at most 256 items after validation, not 257" {
		t.Fatalf("maximum must override invalid rows: %v", errors)
	}
	if !reflect.DeepEqual(errors[0]["ctx"], map[string]any{"field_type": "List", "max_length": 256, "actual_length": 257}) {
		t.Fatal("maximum context differs")
	}
	// Pair cardinality belongs to the 400 replay check, rather than the body model.
	body["progress"].(map[string]any)["discoveries"] = []any{[]any{}, []any{"a"}, []any{"a", "b", "c"}}
	encoded, _ = json.Marshal(body)
	progress, goal, e := exploreCreateBody(httptest.NewRequest("POST", "/", strings.NewReader(string(encoded))))
	if e != nil || progress == nil || goal != nil {
		t.Fatalf("pair shape belongs to replay, got%v", e)
	}
}
func TestStrictRecordsCountUnicodeCodepointsAndPreserveExtraOrder(t *testing.T) {
	for _, n := range []int{160, 161} {
		raw := `{"progress":{"world_id":"` + strings.Repeat("ș", n) + `","recipe_hash":"` + strings.Repeat("a", 64) + `","discoveries":[["` + strings.Repeat("🙂", n) + `"]]},"goal_id":null}`
		_, _, e := exploreCreateBody(httptest.NewRequest("POST", "/", strings.NewReader(raw)))
		if n == 160 && e != nil {
			t.Fatal(e)
		}
		if n == 161 {
			errors := errorDetail(t, e)
			if len(errors) != 2 || errors[0]["type"] != "string_too_long" || errors[1]["type"] != "string_too_long" {
				t.Fatal("Unicode codepoint limits differ")
			}
		}
	}
	for _, kind := range []string{"pair", "goal"} {
		raw := `{"z":1,"a":"x","b":"y","goal_id":null,"m":2}`
		request := httptest.NewRequest("POST", "/", strings.NewReader(raw))
		var e *gameapi.Error
		if kind == "pair" {
			_, _, e = pairBody(request, true)
		} else {
			_, e = goalBody(request)
		}
		errors := errorDetail(t, e)
		if errors[0]["loc"].([]any)[1] != "z" || errors[len(errors)-1]["loc"].([]any)[1] != "m" {
			t.Fatal("extras lost input order")
		}
	}
}
