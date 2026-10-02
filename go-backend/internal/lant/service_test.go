package lant

import (
	"encoding/json"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
	"math/big"
	"os"
	"reflect"
	"sync"
	"testing"
)

func normalize(value any) any {
	switch v := value.(type) {
	case map[string]any:
		for k, x := range v {
			if k == "game_id" {
				v[k] = "<session>"
			} else {
				v[k] = normalize(x)
			}
		}
	case []any:
		for i, x := range v {
			v[i] = normalize(x)
		}
	}
	return value
}

func TestPinnedValidationAndConcurrentHintStages(t *testing.T) {
	c, e := content.Load()
	if e != nil {
		t.Fatal(e)
	}
	s := New(c)
	out, err := s.Create(big.NewInt(17), "normal", nil, "")
	if err != nil {
		t.Fatal(err)
	}
	id := out["game_id"].(string)
	called := false
	_, err = s.MoveInput("missing", func() (string, *gameapi.Error) { called = true; return "", nil })
	if called || err == nil || err.Status != 404 {
		t.Fatal("missing lookup must precede validation")
	}
	_, err = s.MoveInput(id, func() (string, *gameapi.Error) {
		if s.store.Delete(id) {
			t.Fatal("validation not pinned")
		}
		return "", &gameapi.Error{Status: 422, Detail: "validation"}
	})
	if err == nil || err.Status != 422 {
		t.Fatal("validation failure missing")
	}
	var wg sync.WaitGroup
	for i := 0; i < 24; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, err := s.Hint(id)
			if err != nil {
				t.Errorf("unexpected hint error %v", err)
			}
		}()
	}
	wg.Wait()
	s.store.Transaction(id, func(v *game) error {
		if v.HintRequests != 3 || v.moves() != 0 {
			t.Errorf("hint stage/cost bounds wrong: %+v", v)
		}
		return nil
	})
	if len(s.profiles.values) > 512 {
		t.Fatal("route cache exceeded bound")
	}
}
func TestPythonHTTPSequences(t *testing.T) {
	c, e := content.Load()
	if e != nil {
		t.Fatal(e)
	}
	s := New(c)
	data, e := os.ReadFile("testdata/python_games.json")
	if e != nil {
		t.Fatal(e)
	}
	var rows []struct {
		Seed, Difficulty, Category string
		Daily                      *string
		CreateStatus               int `json:"create_status"`
		Create                     any
		Actions                    []struct {
			Kind   string
			Text   *string
			Status int
			Body   any
		}
	}
	if e = json.Unmarshal(data, &rows); e != nil {
		t.Fatal(e)
	}
	check := func(where string, body map[string]any, status int, detail any, wantStatus int, want any) {
		t.Helper()
		if body == nil {
			body = map[string]any{"detail": detail}
		}
		raw, e := json.Marshal(body)
		if e != nil {
			t.Fatal(e)
		}
		var actual any
		json.Unmarshal(raw, &actual)
		actual = normalize(actual)
		if status != wantStatus || !reflect.DeepEqual(actual, want) {
			t.Fatalf("%s status %d/%d\ngot %s\nwant %#v", where, status, wantStatus, raw, want)
		}
	}
	for _, row := range rows {
		seed, _ := new(big.Int).SetString(row.Seed, 10)
		body, err := s.Create(seed, row.Difficulty, row.Daily, row.Category)
		status := 200
		var detail any
		if err != nil {
			status, detail = err.Status, err.Detail
		}
		check("create "+row.Seed+" "+row.Difficulty, body, status, detail, row.CreateStatus, row.Create)
		if err != nil {
			continue
		}
		id := body["game_id"].(string)
		for _, a := range row.Actions {
			switch a.Kind {
			case "get":
				body, err = s.Get(id)
			case "move":
				body, err = s.Move(id, *a.Text)
			case "hint":
				body, err = s.Hint(id)
			case "undo":
				body, err = s.Undo(id)
			}
			status = 200
			detail = nil
			if err != nil {
				status, detail = err.Status, err.Detail
			}
			check(row.Difficulty+" "+row.Seed+" "+a.Kind, body, status, detail, a.Status, a.Body)
		}
	}
}
