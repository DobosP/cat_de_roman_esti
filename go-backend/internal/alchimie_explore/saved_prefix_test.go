package alchimie_explore

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"os"
	"reflect"
	"testing"
)

func TestAll1009IndependentHistoricalSavedPrefixes(t *testing.T) {
	raw, err := os.ReadFile("testdata/legacy-saved-prefixes-v92.json")
	if err != nil {
		t.Fatal(err)
	}
	if fmt.Sprintf("%x", sha256.Sum256(raw)) != "51eadd294f043991fb9a518a0ea62b7bd1249f2f1d3878db91cd0d3253ab1718" {
		t.Fatal("independent saved-prefix corpus drift")
	}
	var corpus struct {
		Schema string `json:"schema"`
		Source string `json:"source_sha256"`
		Count  int    `json:"prefix_count"`
		Books  []struct {
			WorldID  string   `json:"world_id"`
			Hash     string   `json:"recipe_hash"`
			Starters []string `json:"starters"`
			Steps    []struct {
				Pair     Pair     `json:"pair"`
				Result   string   `json:"result"`
				Unlocked []string `json:"unlocked"`
			} `json:"steps"`
		} `json:"books"`
	}
	if err = json.Unmarshal(raw, &corpus); err != nil {
		t.Fatal(err)
	}
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	if corpus.Schema != "legacy-saved-prefixes-v1" || corpus.Source != "0b3fea2c30b4c729cbe8398bc467e5a4f7e6a443ff886023a07d9bf0e40e9f44" || corpus.Count != 1009 || len(corpus.Books) != 9 {
		t.Fatal("independent corpus/source identity mismatch")
	}
	s := New(c)
	if s.loadError != nil {
		t.Fatal(s.loadError)
	}
	if len(s.world.Versions) < len(corpus.Books) {
		t.Fatal("historical book count changed")
	}
	checked := 0
	for _, book := range corpus.Books {
		t.Run(book.Hash, func(t *testing.T) {
			if archived, ok := s.world.versions[book.Hash]; !ok || archived.WorldID != book.WorldID {
				t.Fatal("historical book missing")
			}
			owned := map[string]bool{}
			for _, id := range book.Starters {
				owned[id] = true
			}
			discoveries := []any{}
			expected := []Pair{}
			for i, step := range book.Steps {
				if !owned[step.Pair[0]] || !owned[step.Pair[1]] || owned[step.Result] {
					t.Fatal("frozen legacy step inconsistent", i)
				}
				owned[step.Result] = true
				for _, id := range step.Unlocked {
					owned[id] = true
				}
				discoveries = append(discoveries, []any{step.Pair[0], step.Pair[1]})
				expected = append(expected, step.Pair)
				state, e := s.Create(map[string]any{"world_id": book.WorldID, "recipe_hash": book.Hash, "discoveries": discoveries}, nil)
				if e != nil {
					t.Fatalf("prefix %d refused: %s", i+1, e)
				}
				actualOwned := map[string]bool{}
				for _, item := range state["inventory"].([]any) {
					actualOwned[item.(map[string]any)["id"].(string)] = true
				}
				for id := range owned {
					if !actualOwned[id] {
						t.Fatalf("prefix %d lost earned concept %s", i+1, id)
					}
				}
				progress := state["progress"].(map[string]any)
				if progress["recipe_hash"] != s.world.Hash || !reflect.DeepEqual(progress["discoveries"], expected) {
					t.Fatalf("prefix %d lost saved craft order", i+1)
				}
				checked++
			}
		})
	}
	if checked != 1009 || s.store.Len() > 1000 {
		t.Fatalf("coverage/session bound %d/%d", checked, s.store.Len())
	}
}
