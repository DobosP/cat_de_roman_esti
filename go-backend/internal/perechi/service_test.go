package perechi

import (
	"bytes"
	"encoding/json"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"math/big"
	"os"
	"slices"
	"sync"
	"testing"
)

type goldenResponse struct {
	Status int            `json:"status"`
	Body   map[string]any `json:"body"`
}
type goldenStep struct {
	goldenResponse
	Action string   `json:"action"`
	IDs    []string `json:"ids"`
}
type goldenCase struct {
	Name, Seed, Daily, Category string
	Starter                     bool
	PreviousCase                int `json:"previous_case"`
	Create                      goldenResponse
	Steps                       []goldenStep
}

func data(t *testing.T) *content.Content {
	t.Helper()
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	return c
}
func compare(t *testing.T, body map[string]any, err *Error, want goldenResponse) {
	t.Helper()
	status := 200
	if err != nil {
		status = err.Status
		body = map[string]any{"detail": err.Detail}
	} else {
		body["game_id"] = "<session>"
	}
	a, _ := json.Marshal(body)
	b, _ := json.Marshal(want.Body)
	if status != want.Status || !bytes.Equal(a, b) {
		t.Fatalf("parity status %d != %d\nactual %s\nPython %s", status, want.Status, a, b)
	}
}
func TestPythonAPIGoldens(t *testing.T) {
	raw, err := os.ReadFile("testdata/python-goldens.json")
	if err != nil {
		t.Fatal(err)
	}
	var vectors struct{ Cases []goldenCase }
	if err = json.Unmarshal(raw, &vectors); err != nil {
		t.Fatal(err)
	}
	service := New(data(t))
	ids := map[int]string{}
	for i, c := range vectors.Cases {
		t.Run(c.Name, func(t *testing.T) {
			seed, _ := new(big.Int).SetString(c.Seed, 10)
			previous := ""
			if c.PreviousCase >= 0 {
				previous = ids[c.PreviousCase]
			}
			body, failure := service.Create(seed, c.Daily, c.Category, previous, c.Starter)
			identifier := ""
			if failure == nil {
				identifier = body["game_id"].(string)
				ids[i] = identifier
			}
			compare(t, body, failure, c.Create)
			for index, step := range c.Steps {
				var result map[string]any
				var e *Error
				switch step.Action {
				case "get":
					result, e = service.Get(identifier)
				case "match":
					result, e = service.Match(identifier, step.IDs)
				case "hint":
					result, e = service.Hint(identifier)
				default:
					t.Fatal(step.Action)
				}
				t.Run(step.Action+big.NewInt(int64(index)).String(), func(t *testing.T) { compare(t, result, e, step.goldenResponse) })
			}
		})
	}
}
func TestAtomicDuplicateAndTerminalValidationPrecedence(t *testing.T) {
	service := New(data(t))
	created, e := service.Create(big.NewInt(17), "", "", "", false)
	if e != nil {
		t.Fatal(e)
	}
	id := created["game_id"].(string)
	var pairs [][]string
	service.store.Transaction(id, func(g *gameSession) error {
		for _, p := range g.pairs {
			pairs = append(pairs, slices.Clone(p.members))
		}
		return nil
	})
	wrong := []string{pairs[0][0], pairs[1][0]}
	var wg sync.WaitGroup
	var mu sync.Mutex
	charged := 0
	for range 32 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			body, e := service.Match(id, wrong)
			if e != nil {
				t.Error(e)
				return
			}
			if body["repeated"] == false {
				mu.Lock()
				charged++
				mu.Unlock()
			}
		}()
	}
	wg.Wait()
	if charged != 1 {
		t.Fatalf("charged %d", charged)
	}
	for _, p := range pairs {
		if _, e := service.Match(id, p); e != nil {
			t.Fatal(e)
		}
	}
	called := false
	_, e = service.MatchInput(id, func() ([]string, *Error) { called = true; return nil, fail(422, "invalid") })
	if called || e == nil || e.Status != 400 {
		t.Fatal("terminal guard must precede body validation")
	}
	_, e = service.MatchInput("missing", func() ([]string, *Error) { t.Fatal("missing callback called"); return nil, nil })
	if e == nil || e.Status != 404 {
		t.Fatal("missing game")
	}
}
