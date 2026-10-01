package pyrandom

import (
	"encoding/json"
	"fmt"
	"math/big"
	"os"
	"reflect"
	"testing"
)

func TestCPythonIntegerSeedVectors(t *testing.T) {
	var golden struct {
		Vectors []struct {
			Seed    string `json:"seed"`
			Outputs []struct {
				Index int    `json:"index"`
				Value uint32 `json:"value"`
			} `json:"outputs"`
			Bits      []int    `json:"bits"`
			BitValues []string `json:"bit_values"`
			Ranges    []int    `json:"ranges"`
			Below     []int    `json:"below"`
			Shuffle   []int    `json:"shuffle"`
		} `json:"vectors"`
	}
	data, err := os.ReadFile("testdata/python_random.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(data, &golden); err != nil {
		t.Fatal(err)
	}
	for i, vector := range golden.Vectors {
		t.Run(fmt.Sprintf("vector%d", i), func(t *testing.T) {
			seed, ok := new(big.Int).SetString(vector.Seed, 10)
			if !ok {
				t.Fatal("invalid reference seed")
			}
			rng := New(seed)
			checkpoint := 0
			for i := 0; i <= vector.Outputs[len(vector.Outputs)-1].Index; i++ {
				value := rng.Uint32()
				if i == vector.Outputs[checkpoint].Index {
					if value != vector.Outputs[checkpoint].Value {
						t.Fatalf("getrandbits(32) #%d: got %d, want %d", i, value, vector.Outputs[checkpoint].Value)
					}
					checkpoint++
				}
			}
			rng = New(seed)
			for i, width := range vector.Bits {
				if value := rng.GetRandBits(width).String(); value != vector.BitValues[i] {
					t.Fatalf("getrandbits(%d): got %s, want %s", width, value, vector.BitValues[i])
				}
			}
			rng = New(seed)
			for i, upper := range vector.Ranges {
				if value := rng.RandBelow(upper); value != vector.Below[i] {
					t.Fatalf("randrange(%d): got %d, want %d", upper, value, vector.Below[i])
				}
			}
			rng = New(seed)
			items := make([]int, len(vector.Shuffle))
			for i := range items {
				items[i] = i
			}
			rng.Shuffle(len(items), func(i, j int) { items[i], items[j] = items[j], items[i] })
			if !reflect.DeepEqual(items, vector.Shuffle) {
				t.Fatalf("shuffle: got %v, want %v", items, vector.Shuffle)
			}
		})
	}
}

func TestSeedInputIsNotMutated(t *testing.T) {
	seed := big.NewInt(-123456789)
	New(seed)
	if seed.Int64() != -123456789 {
		t.Fatalf("seed mutated to %s", seed)
	}
}

func TestZeroWidthDoesNotConsumeRandomState(t *testing.T) {
	left, right := NewUint64(42), NewUint64(42)
	if left.GetRandBits(0).Sign() != 0 || left.Uint32() != right.Uint32() {
		t.Fatal("zero-width getrandbits must return zero without consuming state")
	}
}
