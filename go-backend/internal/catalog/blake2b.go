package catalog


import (
	"encoding/binary"
	"math/bits"
)

// This fixed-output BLAKE2b implementation follows RFC 7693. Puzzle selection
// requires digest_size=8: truncating a BLAKE2b-512 digest gives a different hash.
// It is intentionally private and supports only unkeyed, sequential BLAKE2b-64.
var blakeIV = [8]uint64{
	0x6a09e667f3bcc908, 0xbb67ae8584caa73b, 0x3c6ef372fe94f82b, 0xa54ff53a5f1d36f1,
	0x510e527fade682d1, 0x9b05688c2b3e6c1f, 0x1f83d9abfb41bd6b, 0x5be0cd19137e2179,
}

var blakeSigma = [12][16]uint8{
	{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15},
	{14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3},
	{11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4},
	{7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8},
	{9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13},
	{2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9},
	{12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11},
	{13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10},
	{6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5},
	{10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0},
	{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15},
	{14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3},
}

func blakeMix(v *[16]uint64, a, b, c, d int, x, y uint64) {
	v[a] += v[b] + x
	v[d] = bits.RotateLeft64(v[d]^v[a], -32)
	v[c] += v[d]
	v[b] = bits.RotateLeft64(v[b]^v[c], -24)
	v[a] += v[b] + y
	v[d] = bits.RotateLeft64(v[d]^v[a], -16)
	v[c] += v[d]
	v[b] = bits.RotateLeft64(v[b]^v[c], -63)
}

func blakeCompress(h *[8]uint64, block *[128]byte, total uint64, final bool) {
	var words [16]uint64
	var v [16]uint64
	for i := range words {
		words[i] = binary.LittleEndian.Uint64(block[i*8 : (i+1)*8])
	}
	copy(v[:8], h[:])
	copy(v[8:], blakeIV[:])
	v[12] ^= total
	if final {
		v[14] = ^v[14]
	}
	for _, s := range blakeSigma {
		blakeMix(&v, 0, 4, 8, 12, words[s[0]], words[s[1]])
		blakeMix(&v, 1, 5, 9, 13, words[s[2]], words[s[3]])
		blakeMix(&v, 2, 6, 10, 14, words[s[4]], words[s[5]])
		blakeMix(&v, 3, 7, 11, 15, words[s[6]], words[s[7]])
		blakeMix(&v, 0, 5, 10, 15, words[s[8]], words[s[9]])
		blakeMix(&v, 1, 6, 11, 12, words[s[10]], words[s[11]])
		blakeMix(&v, 2, 7, 8, 13, words[s[12]], words[s[13]])
		blakeMix(&v, 3, 4, 9, 14, words[s[14]], words[s[15]])
	}
	for i := range h {
		h[i] ^= v[i] ^ v[i+8]
	}
}

func blake2b8(input []byte) [8]byte {
	h := blakeIV
	h[0] ^= 0x01010008 // fanout=1, depth=1, key length=0, digest length=8
	var total uint64
	for len(input) > 128 {
		var block [128]byte
		copy(block[:], input[:128])
		total += 128
		blakeCompress(&h, &block, total, false)
		input = input[128:]
	}
	var block [128]byte
	copy(block[:], input)
	total += uint64(len(input))
	blakeCompress(&h, &block, total, true)
	var result [8]byte
	binary.LittleEndian.PutUint64(result[:], h[0])
	return result
}

// DailySeed is Python service.daily_seed, interpreted as an unsigned big-endian
// integer. The client's supplied date, rather than the server clock, is used.
func DailySeed(date, salt string) uint64 {
	digest := blake2b8([]byte(date + ":" + salt))
	return binary.BigEndian.Uint64(digest[:])
}
