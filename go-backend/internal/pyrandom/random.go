// Package pyrandom implements the integer-seeded CPython random.Random operations
// used by the game contract. It is for reproducible puzzles, never credentials.
package pyrandom

import (
	"crypto/rand"
	"math/big"
	"math/bits"
)

const stateSize = 624

// Random preserves CPython's MT19937 seed expansion, getrandbits, randrange,
// and shuffle behavior. Each game session owns its instance.
type Random struct {
	state [stateSize]uint32
	index int
}

// New seeds with the absolute value of an integer, matching Python. A nil seed
// uses OS entropy, like Python Random(None); there is no deterministic parity
// requirement for those new rounds.
func New(seed *big.Int) *Random {
	value := new(big.Int)
	if seed != nil {
		value.Abs(seed)
	} else {
		var entropy [32]byte
		if _, err := rand.Read(entropy[:]); err != nil {
			panic("pyrandom: operating-system entropy unavailable")
		}
		value.SetBytes(entropy[:])
	}
	count := (value.BitLen() + 31) / 32
	if count == 0 {
		count = 1
	}
	key := make([]uint32, count)
	mask := new(big.Int).SetUint64(0xffffffff)
	for i := range key {
		key[i] = uint32(new(big.Int).And(value, mask).Uint64())
		value.Rsh(value, 32)
	}
	r := &Random{}
	r.seedArray(key)
	return r
}

func NewUint64(seed uint64) *Random {
	return New(new(big.Int).SetUint64(seed))
}

func (r *Random) seedArray(key []uint32) {
	r.state[0] = 19650218
	for i := 1; i < stateSize; i++ {
		previous := r.state[i-1]
		r.state[i] = 1812433253*(previous^(previous>>30)) + uint32(i)
	}
	i, j := 1, 0
	count := stateSize
	if len(key) > count {
		count = len(key)
	}
	for ; count > 0; count-- {
		previous := r.state[i-1]
		r.state[i] = (r.state[i] ^ ((previous ^ (previous >> 30)) * 1664525)) + key[j] + uint32(j)
		i++
		j++
		if i >= stateSize {
			r.state[0] = r.state[stateSize-1]
			i = 1
		}
		if j >= len(key) {
			j = 0
		}
	}
	for count = stateSize - 1; count > 0; count-- {
		previous := r.state[i-1]
		r.state[i] = (r.state[i] ^ ((previous ^ (previous >> 30)) * 1566083941)) - uint32(i)
		i++
		if i >= stateSize {
			r.state[0] = r.state[stateSize-1]
			i = 1
		}
	}
	r.state[0] = 0x80000000
	r.index = stateSize
}

// Uint32 is the next full-width MT19937 output (Python getrandbits(32)).
func (r *Random) Uint32() uint32 {
	if r.index >= stateSize {
		for i := 0; i < stateSize; i++ {
			y := (r.state[i] & 0x80000000) | (r.state[(i+1)%stateSize] & 0x7fffffff)
			r.state[i] = r.state[(i+397)%stateSize] ^ (y >> 1)
			if y&1 != 0 {
				r.state[i] ^= 0x9908b0df
			}
		}
		r.index = 0
	}
	y := r.state[r.index]
	r.index++
	y ^= y >> 11
	y ^= (y << 7) & 0x9d2c5680
	y ^= (y << 15) & 0xefc60000
	y ^= y >> 18
	return y
}

// GetRandBits matches Python's getrandbits, including little-endian word
// assembly and use of the high bits for a partial final word.
func (r *Random) GetRandBits(k int) *big.Int {
	if k < 0 {
		panic("pyrandom: number of bits must be non-negative")
	}
	result := new(big.Int)
	for offset := 0; offset < k; offset += 32 {
		word := r.Uint32()
		if remaining := k - offset; remaining < 32 {
			word >>= 32 - remaining
		}
		part := new(big.Int).SetUint64(uint64(word))
		part.Lsh(part, uint(offset))
		result.Or(result, part)
	}
	return result
}

// RandBelow follows CPython's rejection sampling, including the extra bit
// sampled when n is a power of two.
func (r *Random) RandBelow(n int) int {
	if n <= 0 {
		panic("pyrandom: empty range")
	}
	k := bits.Len(uint(n))
	for {
		var value uint64
		if k <= 32 {
			value = uint64(r.Uint32() >> (32 - k))
		} else {
			value = r.GetRandBits(k).Uint64()
		}
		if value < uint64(n) {
			return int(value)
		}
	}
}

func (r *Random) Shuffle(n int, swap func(i, j int)) {
	for i := n - 1; i > 0; i-- {
		swap(i, r.RandBelow(i+1))
	}
}

func (r *Random) ShuffleStrings(items []string) {
	r.Shuffle(len(items), func(i, j int) { items[i], items[j] = items[j], items[i] })
}
