package conexiuni

import (
	"bytes"
	"encoding/json"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
	"math/big"
	"os"
	"slices"
	"sort"
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
	Name, Seed, Daily, Category, Difficulty string
	PackLimit                               *int `json:"pack_limit"`
	Create                                  goldenResponse
	Steps                                   []goldenStep
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
func TestPythonAPIGoldensCuratedMinedAndDailyFloors(t *testing.T) {
	raw, err := os.ReadFile("testdata/python-goldens.json")
	if err != nil {
		t.Fatal(err)
	}
	var vectors struct{ Cases []goldenCase }
	if err = json.Unmarshal(raw, &vectors); err != nil {
		t.Fatal(err)
	}
	base := data(t)
	defaultService := New(base)
	for _, c := range vectors.Cases {
		t.Run(c.Name, func(t *testing.T) {
			service := defaultService
			if c.PackLimit != nil {
				modified := data(t)
				items := []content.PackItem{}
				for _, item := range modified.PackItems {
					if item.Game == "conexiuni" && item.PilotEligible && item.Difficulty == c.Difficulty && (c.Category == "" || item.Category == c.Category) {
						items = append(items, item)
					}
				}
				sort.Slice(items, func(i, j int) bool { return items[i].ID < items[j].ID })
				modified.PackItems = items[:*c.PackLimit]
				service = NewWithGraph(modified, defaultService.graph)
			}
			seed, _ := new(big.Int).SetString(c.Seed, 10)
			body, e := service.Create(seed, c.Daily, c.Category, c.Difficulty)
			id := ""
			if e == nil {
				id = body["game_id"].(string)
			}
			compare(t, body, e, c.Create)
			for index, step := range c.Steps {
				var result map[string]any
				var failure *Error
				switch step.Action {
				case "get":
					result, failure = service.Get(id)
				case "guess":
					result, failure = service.Guess(id, step.IDs)
				case "clue":
					result, failure = service.Clue(id)
				default:
					t.Fatal(step.Action)
				}
				t.Run(step.Action+big.NewInt(int64(index)).String(), func(t *testing.T) { compare(t, result, failure, step.goldenResponse) })
			}
		})
	}
}
func TestAtomicWrongGuessAndValidationPrecedence(t *testing.T) {
	service := New(data(t))
	body, e := service.Create(big.NewInt(17), "", "", "normal")
	if e != nil {
		t.Fatal(e)
	}
	id := body["game_id"].(string)
	var groups [][]string
	service.store.Transaction(id, func(g *gameSession) error {
		for _, cat := range keys(g.groups) {
			groups = append(groups, slices.Clone(g.groups[cat]))
		}
		return nil
	})
	wrong := append(slices.Clone(groups[0][:3]), groups[1][0])
	var wg sync.WaitGroup
	var mu sync.Mutex
	accepted := 0
	for range 32 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			result, e := service.Guess(id, wrong)
			if e == nil {
				mu.Lock()
				accepted++
				mu.Unlock()
				if result["mistakes"] != 1 || result["one_away"] != true {
					t.Error("wrong guess")
				}
			} else if e.Status != 409 {
				t.Error(e)
			}
		}()
	}
	wg.Wait()
	if accepted != 1 {
		t.Fatalf("accepted %d", accepted)
	}
	for _, group := range groups {
		if _, e := service.Guess(id, group); e != nil {
			t.Fatal(e)
		}
	}
	called := false
	_, e = service.GuessInput(id, func() ([]string, *Error) { called = true; return nil, fail(422, "invalid") })
	if !called || e == nil || e.Status != 422 {
		t.Fatal("body validation must precede terminal guard")
	}
}
func TestMineFailsClosedWithInsufficientCategoriesAndBadBoards(t *testing.T) {
	d := data(t)
	d.CategoryOrder = []string{"muzica"}
	service := New(d)
	if _, e := service.pickBoard(nil, "normal"); e == nil || e.Detail != "Nu există suficiente categorii pentru un joc." {
		t.Fatal(e)
	}
	bad := newSession(map[string][]string{"a": {"x", "x", "x", "x"}}, []string{"x"}, "normal", "", "", nil)
	if ok, _ := service.quality(bad); ok {
		t.Fatal("degenerate board accepted")
	}
}

func TestCuratedCreationLeavesFallbackRankingCold(t *testing.T) {
	service := New(data(t))
	if len(service.ranked) != 0 {
		t.Fatal("fallback ranking eagerly allocated")
	}
	if _, err := service.Create(big.NewInt(17), "", "", "normal"); err != nil {
		t.Fatal(err)
	}
	if len(service.ranked) != 0 {
		t.Fatal("curated creation initialized fallback ranking")
	}
	if _, err := service.pickBoard(pyrandom.New(big.NewInt(13)), "normal"); err != nil {
		t.Fatal(err)
	}
	if len(service.ranked) == 0 {
		t.Fatal("mining failed to initialize ranking")
	}
}
