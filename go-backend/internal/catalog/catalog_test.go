package catalog

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math/big"
	"os"
	"reflect"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
)

func readGolden(t *testing.T, name string, target any) {
	t.Helper()
	data, err := os.ReadFile("testdata/" + name)
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(data, target); err != nil {
		t.Fatal(err)
	}
}

func TestBLAKE2b8AgainstCPython(t *testing.T) {
	var golden []struct {
		Input  string `json:"input"`
		Digest string `json:"digest"`
	}
	readGolden(t, "blake2b8.json", &golden)
	for i, vector := range golden {
		t.Run(fmt.Sprint(i), func(t *testing.T) {
			digest := blake2b8([]byte(vector.Input))
			if got := hex.EncodeToString(digest[:]); got != vector.Digest {
				t.Fatalf("digest got %s, want %s", got, vector.Digest)
			}
		})
	}
}

type goldenOptions struct {
	Category          string   `json:"category"`
	Difficulty        string   `json:"difficulty"`
	ExcludeSources    []string `json:"exclude_source_ids"`
	Starter           bool     `json:"starter"`
	BalanceCategories bool     `json:"balance_categories"`
}

func (o goldenOptions) pickOptions() PickOptions {
	excluded := make(map[string]bool)
	for _, source := range o.ExcludeSources {
		excluded[source] = true
	}
	return PickOptions{Category: o.Category, Difficulty: o.Difficulty,
		ExcludeSources: excluded, Starter: o.Starter, BalanceCategories: o.BalanceCategories}
}

func catalogID(board *content.Board) string {
	if board == nil {
		return ""
	}
	return board.CatalogID
}

func TestSelectionAgainstCanonicalPython(t *testing.T) {
	var synthetic []content.Board
	readGolden(t, "synthetic_boards.json", &synthetic)
	bundled, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	catalogs := map[string]*Catalog{"synthetic": New(&content.Content{Boards: synthetic}), "bundled": New(bundled)}
	var golden struct {
		Seeded []struct {
			Inventory string        `json:"inventory"`
			Seed      string        `json:"seed"`
			Options   goldenOptions `json:"options"`
			ID        string        `json:"id"`
			NextBits  string        `json:"next_bits"`
		} `json:"seeded"`
		Daily []struct {
			Inventory string        `json:"inventory"`
			Day       string        `json:"day"`
			Options   goldenOptions `json:"options"`
			ID        string        `json:"id"`
		} `json:"daily"`
	}
	readGolden(t, "python_selector.json", &golden)
	for i, vector := range golden.Seeded {
		seed, ok := new(big.Int).SetString(vector.Seed, 10)
		if !ok {
			t.Fatal("invalid seed")
		}
		rng := pyrandom.New(seed)
		selected := catalogs[vector.Inventory].PickSeeded("intrusul", rng, vector.Options.pickOptions())
		if got := catalogID(selected); got != vector.ID {
			t.Fatalf("seeded vector %d (%s seed %s, %+v): got %s, want %s", i, vector.Inventory, vector.Seed, vector.Options, got, vector.ID)
		}
		if got := rng.GetRandBits(64).String(); got != vector.NextBits {
			t.Fatalf("seeded vector %d consumed different RNG state: got %s, want %s", i, got, vector.NextBits)
		}
	}
	for i, vector := range golden.Daily {
		selected := catalogs[vector.Inventory].PickDailyWithOptions("intrusul", vector.Day, vector.Options.pickOptions())
		if got := catalogID(selected); got != vector.ID {
			t.Fatalf("daily vector %d (%s %s, %+v): got %s, want %s", i, vector.Inventory, vector.Day, vector.Options, got, vector.ID)
		}
	}
	t.Logf("%d seeded cases and %d daily cases match canonical Python", len(golden.Seeded), len(golden.Daily))
}

func TestCatalogInputOrderDoesNotAffectSelection(t *testing.T) {
	var boards []content.Board
	readGolden(t, "synthetic_boards.json", &boards)
	originalIDs := make([]string, len(boards))
	for i, board := range boards {
		originalIDs[i] = board.CatalogID
	}
	left := New(&content.Content{Boards: boards})
	for i, board := range boards {
		if board.CatalogID != originalIDs[i] {
			t.Fatal("New mutated the input board order")
		}
	}
	for i, j := 0, len(boards)-1; i < j; i, j = i+1, j-1 {
		boards[i], boards[j] = boards[j], boards[i]
	}
	right := New(&content.Content{Boards: boards})
	for seed := uint64(0); seed < 100; seed++ {
		options := PickOptions{BalanceCategories: true}
		if catalogID(left.PickSeeded("intrusul", pyrandom.NewUint64(seed), options)) !=
			catalogID(right.PickSeeded("intrusul", pyrandom.NewUint64(seed), options)) {
			t.Fatalf("input order affected seed %d", seed)
		}
		day := fmt.Sprintf("order-test-%d", seed)
		if catalogID(left.PickDaily("intrusul", day, "")) != catalogID(right.PickDaily("intrusul", day, "")) {
			t.Fatalf("input order affected daily %s", day)
		}
	}
}

func TestPreferredShelfWithinStrictFilters(t *testing.T) {
	var boards []content.Board
	readGolden(t, "synthetic_boards.json", &boards)
	c := New(&content.Content{Boards: boards})
	pool := c.Pool("intrusul", PickOptions{Category: "stiinta"})
	if got := []string{pool[0].CatalogID, pool[1].CatalogID}; !reflect.DeepEqual(got, []string{"d1", "e1"}) {
		t.Fatalf("low-score strict shelf was widened: %v", got)
	}
	if len(c.Pool("intrusul", PickOptions{Category: "does-not-exist"})) != 0 ||
		c.PickDaily("intrusul", "2026-10-01", "does-not-exist") != nil {
		t.Fatal("an empty strict filter must stay empty")
	}
	for seed := uint64(0); seed < 100; seed++ {
		picked := c.PickSeeded("intrusul", pyrandom.NewUint64(seed), PickOptions{})
		if picked.OverallScore < 55 {
			t.Fatal("unfiltered selection bypassed preferred shelf")
		}
	}
}

func TestDailySeedBigEndian(t *testing.T) {
	// hashlib.blake2b(b"2026-10-01:intrusul", digest_size=8), int.from_bytes(..., "big").
	if got := DailySeed("2026-10-01", "intrusul"); got != 7572043643114448372 {
		t.Fatalf("daily seed: got %d", got)
	}
}
