package contexto

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

func normalized(value any) any {
	switch v := value.(type) {
	case map[string]any:
		for k, x := range v {
			if k == "game_id" {
				v[k] = "<session>"
			} else if k == "resolved_token" {
				v[k] = "<confirmation>"
			} else {
				v[k] = normalized(x)
			}
		}
	case []any:
		for i, x := range v {
			v[i] = normalized(x)
		}
	}
	return value
}

func TestPinnedValidationAndConcurrentRepeats(t *testing.T) {
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
	_, err = s.GuessInput("missing", func() (GuessBody, *gameapi.Error) { called = true; return GuessBody{}, nil })
	if called || err == nil || err.Status != 404 {
		t.Fatal("missing lookup must precede validation")
	}
	validation := func() (GuessBody, *gameapi.Error) {
		if s.store.Delete(id) {
			t.Fatal("validation not pinned")
		}
		return GuessBody{}, &gameapi.Error{Status: 422, Detail: "validation"}
	}
	_, err = s.GuessInput(id, validation)
	if err == nil || err.Status != 422 {
		t.Fatal("validation failure missing")
	}
	var wg sync.WaitGroup
	for i := 0; i < 24; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, err := s.Guess(id, "n_mihai_eminescu", "")
			if err != nil && err.Status != 400 {
				t.Errorf("unexpected error %v", err)
			}
		}()
	}
	wg.Wait()
	out, err = s.Get(id)
	if err != nil || out["attempts"] != 1 {
		t.Fatalf("duplicate guesses charged multiple times: %v", out)
	}
	s.GiveUp(id)
	_, err = s.GuessInput(id, validation)
	if err == nil || err.Status != 422 {
		t.Fatal("terminal guard preceded validation")
	}
	if len(s.profiles.values) > 256 {
		t.Fatal("profile cache exceeded bound")
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
			Kind          string
			Text, Confirm *string
			Status        int
			Body          any
		}
	}
	if e = json.Unmarshal(data, &rows); e != nil {
		t.Fatal(e)
	}
	check := func(where string, body map[string]any, errStatus int, detail any, expectedStatus int, expected any) {
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
		actual = normalized(actual)
		if errStatus != expectedStatus || !reflect.DeepEqual(actual, expected) {
			t.Fatalf("%s status %d/%d\ngot %s\nwant %#v", where, errStatus, expectedStatus, raw, expected)
		}
	}
	for i, row := range rows {
		seed, _ := new(big.Int).SetString(row.Seed, 10)
		body, err := s.Create(seed, row.Difficulty, row.Daily, row.Category)
		status := 200
		var detail any
		if err != nil {
			status, detail = err.Status, err.Detail
		}
		check("create", body, status, detail, row.CreateStatus, row.Create)
		if err != nil {
			continue
		}
		id := body["game_id"].(string)
		token := ""
		for j, a := range row.Actions {
			switch a.Kind {
			case "get":
				body, err = s.Get(id)
			case "guess":
				text := ""
				if a.Text != nil {
					text = *a.Text
				}
				confirm := ""
				if a.Confirm != nil {
					confirm = token
				}
				body, err = s.Guess(id, text, confirm)
			case "clue":
				body, err = s.Clue(id)
			case "giveup":
				body, err = s.GiveUp(id)
			}
			if body != nil {
				if value, ok := body["resolved_token"].(string); ok {
					token = value
				}
			}
			status = 200
			detail = nil
			if err != nil {
				status, detail = err.Status, err.Detail
			}
			check(row.Difficulty+" "+row.Seed+" "+a.Kind, body, status, detail, a.Status, a.Body)
			_ = i
			_ = j
		}
	}
}
