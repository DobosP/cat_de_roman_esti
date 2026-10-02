package httpapi

import (
	"bytes"
	"encoding/json"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
	"io"
	"net/http"
	"regexp"
	"sort"
	"strconv"
	"unicode/utf8"
)

type fieldRule struct {
	Name, Kind         string
	Optional, Nullable bool
	Min, Max           int
	Pattern            string
}

func validation(kind, msg string, loc []any, input any, ctx map[string]any) map[string]any {
	e := map[string]any{"type": kind, "loc": loc, "msg": msg, "input": input}
	if len(ctx) > 0 {
		e["ctx"] = ctx
	}
	return e
}

// jsonObjectOrder retains JSON insertion order for extra_forbidden errors. Like
// Python dictionaries, duplicate keys replace the value without moving the key.
type jsonObjectOrder struct {
	Keys     []string
	Children map[string]*jsonObjectOrder
}

func readObjectOrder(d *json.Decoder) (*jsonObjectOrder, error) {
	token, err := d.Token()
	if err != nil {
		return nil, err
	}
	delimiter, container := token.(json.Delim)
	if !container {
		return nil, nil
	}
	if delimiter == '{' {
		order := &jsonObjectOrder{Keys: []string{}, Children: map[string]*jsonObjectOrder{}}
		seen := map[string]bool{}
		for d.More() {
			keyToken, err := d.Token()
			if err != nil {
				return nil, err
			}
			key := keyToken.(string)
			child, err := readObjectOrder(d)
			if err != nil {
				return nil, err
			}
			if !seen[key] {
				order.Keys = append(order.Keys, key)
				seen[key] = true
			}
			order.Children[key] = child
		}
		_, err = d.Token()
		return order, err
	}
	for d.More() {
		if _, err := readObjectOrder(d); err != nil {
			return nil, err
		}
	}
	_, err = d.Token()
	return nil, err
}
func parseObjectOrdered(r *http.Request, model string) (map[string]any, *jsonObjectOrder, *gameapi.Error) {
	raw, err := io.ReadAll(io.LimitReader(r.Body, MaxRequestBytes+1))
	if err != nil {
		return nil, nil, &gameapi.Error{Status: 400, Detail: "Request body unreadable"}
	}
	if len(raw) > MaxRequestBytes {
		return nil, nil, &gameapi.Error{Status: 413, Detail: "Request body too large"}
	}
	var value any
	if len(bytes.TrimSpace(raw)) > 0 {
		d := json.NewDecoder(bytes.NewReader(raw))
		d.UseNumber()
		err = d.Decode(&value)
		if err == nil {
			var trailing any
			if d.Decode(&trailing) != io.EOF {
				err = extraData{}
			}
		}
		if err != nil {
			return nil, nil, &gameapi.Error{Status: 422, Detail: []map[string]any{validation("json_invalid", "JSON decode error", []any{"body"}, map[string]any{}, map[string]any{"error": jsonMessage(raw, err)})}}
		}
	}
	obj, ok := value.(map[string]any)
	if !ok {
		return nil, nil, &gameapi.Error{Status: 422, Detail: []map[string]any{validation("model_type", "Input should be a valid dictionary or instance of "+model, []any{"body"}, value, map[string]any{"class_name": model})}}
	}
	orderDecoder := json.NewDecoder(bytes.NewReader(raw))
	orderDecoder.UseNumber()
	order, _ := readObjectOrder(orderDecoder)
	return obj, order, nil
}
func parseObject(r *http.Request, model string) (map[string]any, *gameapi.Error) {
	obj, _, err := parseObjectOrdered(r, model)
	return obj, err
}
func appendStringErrors(value any, rule fieldRule, loc []any, errors *[]map[string]any) {
	text, ok := value.(string)
	if !ok {
		*errors = append(*errors, validation("string_type", "Input should be a valid string", loc, value, nil))
		return
	}
	length := utf8.RuneCountInString(text)
	if rule.Min > 0 && length < rule.Min {
		noun := "characters"
		if rule.Min == 1 {
			noun = "character"
		}
		*errors = append(*errors, validation("string_too_short", "String should have at least "+number(rule.Min)+" "+noun, loc, value, map[string]any{"min_length": rule.Min}))
		return
	}
	if rule.Max > 0 && length > rule.Max {
		noun := "characters"
		if rule.Max == 1 {
			noun = "character"
		}
		*errors = append(*errors, validation("string_too_long", "String should have at most "+number(rule.Max)+" "+noun, loc, value, map[string]any{"max_length": rule.Max}))
		return
	}
	if rule.Pattern != "" && !regexp.MustCompile(rule.Pattern).MatchString(text) {
		*errors = append(*errors, validation("string_pattern_mismatch", "String should match pattern '"+rule.Pattern+"'", loc, value, map[string]any{"pattern": rule.Pattern}))
	}
}
func childLocation(parent []any, field any) []any { return append(append([]any{}, parent...), field) }
func appendExtraErrors(obj map[string]any, order *jsonObjectOrder, allowed map[string]bool, parent []any, errors *[]map[string]any) {
	var keys []string
	if order != nil {
		keys = order.Keys
	} else {
		keys = make([]string, 0, len(obj))
		for key := range obj {
			keys = append(keys, key)
		}
		sort.Strings(keys)
	}
	for _, key := range keys {
		if !allowed[key] {
			*errors = append(*errors, validation("extra_forbidden", "Extra inputs are not permitted", childLocation(parent, key), obj[key], nil))
		}
	}
}
func fields(r *http.Request, model string, rules []fieldRule, forbid bool) (map[string]any, *gameapi.Error) {
	obj, order, err := parseObjectOrdered(r, model)
	if err != nil {
		return nil, err
	}
	errors := []map[string]any{}
	allowed := map[string]bool{}
	for _, rule := range rules {
		allowed[rule.Name] = true
		value, present := obj[rule.Name]
		loc := []any{"body", rule.Name}
		if !present {
			if !rule.Optional {
				errors = append(errors, validation("missing", "Field required", loc, obj, nil))
			}
			continue
		}
		if value == nil && rule.Nullable {
			continue
		}
		switch rule.Kind {
		case "string":
			appendStringErrors(value, rule, loc, &errors)
		case "strings":
			entries, ok := value.([]any)
			if !ok {
				errors = append(errors, validation("list_type", "Input should be a valid list", loc, value, nil))
				continue
			}
			for index, entry := range entries {
				appendStringErrors(entry, fieldRule{}, childLocation(loc, index), &errors)
			}
		case "object":
			if _, ok := value.(map[string]any); !ok {
				errors = append(errors, validation("dict_type", "Input should be a valid dictionary", loc, value, nil))
			}
		}
	}
	if forbid {
		appendExtraErrors(obj, order, allowed, []any{"body"}, &errors)
	}
	if len(errors) > 0 {
		return nil, &gameapi.Error{Status: 422, Detail: errors}
	}
	return obj, nil
}

// exploreCreateBody validates the strict CreateBody/Progress model before the
// discovery service replays any saved craft. Pair cardinality remains the game's
// 400-level replay check; the model validates only nested list and identifier types.
func exploreCreateBody(r *http.Request) (map[string]any, *string, *gameapi.Error) {
	obj, order, err := parseObjectOrdered(r, "CreateBody")
	if err != nil {
		return nil, nil, err
	}
	errors := []map[string]any{}
	var progress map[string]any
	var goal *string
	if input, present := obj["progress"]; present && input != nil {
		loc := []any{"body", "progress"}
		record, ok := input.(map[string]any)
		if !ok {
			errors = append(errors, validation("model_type", "Input should be a valid dictionary or instance of Progress", loc, input, map[string]any{"class_name": "Progress"}))
		} else {
			progress = record
			for _, rule := range []fieldRule{{Name: "world_id", Min: 1, Max: 160}, {Name: "recipe_hash", Pattern: "^[a-f0-9]{64}$"}} {
				fieldLoc := childLocation(loc, rule.Name)
				value, present := record[rule.Name]
				if !present {
					errors = append(errors, validation("missing", "Field required", fieldLoc, record, nil))
				} else {
					appendStringErrors(value, rule, fieldLoc, &errors)
				}
			}
			discoverLoc := childLocation(loc, "discoveries")
			value, present := record["discoveries"]
			if !present {
				errors = append(errors, validation("missing", "Field required", discoverLoc, record, nil))
			} else if rows, ok := value.([]any); !ok {
				errors = append(errors, validation("list_type", "Input should be a valid list", discoverLoc, value, nil))
			} else if len(rows) > 256 {
				errors = append(errors, validation("too_long", "List should have at most 256 items after validation, not "+number(len(rows)), discoverLoc, value, map[string]any{"field_type": "List", "max_length": 256, "actual_length": len(rows)}))
			} else {
				for index, row := range rows {
					rowLoc := childLocation(discoverLoc, index)
					ids, ok := row.([]any)
					if !ok {
						errors = append(errors, validation("list_type", "Input should be a valid list", rowLoc, row, nil))
						continue
					}
					for column, id := range ids {
						appendStringErrors(id, fieldRule{Min: 1, Max: 160}, childLocation(rowLoc, column), &errors)
					}
				}
			}
			var progressOrder *jsonObjectOrder
			if order != nil {
				progressOrder = order.Children["progress"]
			}
			appendExtraErrors(record, progressOrder, map[string]bool{"world_id": true, "recipe_hash": true, "discoveries": true}, loc, &errors)
		}
	}
	if value, present := obj["goal_id"]; present && value != nil {
		appendStringErrors(value, fieldRule{Min: 1, Max: 160}, []any{"body", "goal_id"}, &errors)
		if text, ok := value.(string); ok {
			goal = &text
		}
	}
	appendExtraErrors(obj, order, map[string]bool{"progress": true, "goal_id": true}, []any{"body"}, &errors)
	if len(errors) > 0 {
		return nil, nil, &gameapi.Error{Status: 422, Detail: errors}
	}
	return progress, goal, nil
}
func number(n int) string                                { return strconv.Itoa(n) }
func stringField(obj map[string]any, name string) string { s, _ := obj[name].(string); return s }
func optionalString(obj map[string]any, name string) *string {
	if v, ok := obj[name].(string); ok {
		return &v
	}
	return nil
}
func stringIDs(obj map[string]any, name string) []string {
	out := []string{}
	for _, v := range obj[name].([]any) {
		out = append(out, v.(string))
	}
	return out
}
func idsBody(r *http.Request, model string) ([]string, *gameapi.Error) {
	v, e := fields(r, model, []fieldRule{{Name: "ids", Kind: "strings"}}, false)
	if e != nil {
		return nil, e
	}
	return stringIDs(v, "ids"), nil
}
func textBody(r *http.Request) (string, *gameapi.Error) {
	v, e := fields(r, "MoveBody", []fieldRule{{Name: "text", Kind: "string"}}, false)
	if e != nil {
		return "", e
	}
	return stringField(v, "text"), nil
}
func pairBody(r *http.Request, strict bool) (string, string, *gameapi.Error) {
	rules := []fieldRule{{Name: "a", Kind: "string"}, {Name: "b", Kind: "string"}}
	name := "CombineBody"
	if strict {
		name = "PairBody"
		for i := range rules {
			rules[i].Min = 1
			rules[i].Max = 160
		}
	}
	v, e := fields(r, name, rules, strict)
	if e != nil {
		return "", "", e
	}
	return stringField(v, "a"), stringField(v, "b"), nil
}
func goalBody(r *http.Request) (*string, *gameapi.Error) {
	v, e := fields(r, "GoalBody", []fieldRule{{Name: "goal_id", Kind: "string", Nullable: true, Min: 1, Max: 160}}, true)
	if e != nil {
		return nil, e
	}
	return optionalString(v, "goal_id"), nil
}
