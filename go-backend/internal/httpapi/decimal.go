package httpapi

import "sort"

// decimalZeros freezes the decimal digits accepted by the production Python
// 3.12 runtime's Unicode 15.0.0 database. Go 1.26 uses Unicode 17, whose new
// digits would change the HTTP validation contract. Each entry begins a group
// of ten consecutive digits; the five mathematical alphabets are separate.
// Source: Python unicodedata.decimal(chr(r)), for all Unicode code points.
// Updating the compatibility runtime requires regenerating and reviewing this
// table together with the independent exhaustive checksum in decimal_test.go.
var decimalZeros = [...]rune{
	0x0030, 0x0660, 0x06f0, 0x07c0, 0x0966, 0x09e6, 0x0a66, 0x0ae6,
	0x0b66, 0x0be6, 0x0c66, 0x0ce6, 0x0d66, 0x0de6, 0x0e50, 0x0ed0,
	0x0f20, 0x1040, 0x1090, 0x17e0, 0x1810, 0x1946, 0x19d0, 0x1a80,
	0x1a90, 0x1b50, 0x1bb0, 0x1c40, 0x1c50, 0xa620, 0xa8d0, 0xa900,
	0xa9d0, 0xa9f0, 0xaa50, 0xabf0, 0xff10, 0x104a0, 0x10d30, 0x11066,
	0x110f0, 0x11136, 0x111d0, 0x112f0, 0x11450, 0x114d0, 0x11650, 0x116c0,
	0x11730, 0x118e0, 0x11950, 0x11c50, 0x11d50, 0x11da0, 0x11f50, 0x16a60,
	0x16ac0, 0x16b50, 0x1d7ce, 0x1d7d8, 0x1d7e2, 0x1d7ec, 0x1d7f6, 0x1e140,
	0x1e2f0, 0x1e4f0, 0x1e950, 0x1fbf0,
}

func decimalValue(r rune) (int, bool) {
	index := sort.Search(len(decimalZeros), func(i int) bool { return decimalZeros[i] > r }) - 1
	if index >= 0 {
		value := r - decimalZeros[index]
		if value < 10 {
			return int(value), true
		}
	}
	return 0, false
}
