package httpapi

import (
	"crypto/sha256"
	"encoding/hex"
	"testing"
)

func TestDecimalPython15Examples(t *testing.T) {
	for _, example := range []struct {
		r     rune
		value int
	}{
		{'0', 0}, {'9', 9}, {'١', 1}, {'۹', 9}, {'７', 7},
		{'𝟎', 0}, {'𝟠', 8}, {'𝟩', 7}, {'𝟶', 0}, {'𝟵', 9},
		{0x11f55, 5}, // Kawi, introduced in Unicode 15.
		{0x1e4f8, 8}, // Nag Mundari, introduced in Unicode 15.
	} {
		if value, ok := decimalValue(example.r); !ok || value != example.value {
			t.Errorf("U+%04X: got (%d,%t), want (%d,true)", example.r, value, ok, example.value)
		}
	}
	for _, r := range []rune{
		-1, 0x110000, 'a', '²', 'Ⅸ', 0x1d7cd, 0x1d800,
		0x11bf1, // Sunuwar, introduced in Unicode 16.
		0x1e5f1, // Ol Onal, introduced in Unicode 16.
		0x10d41, // Garay, introduced in Unicode 16.
		0x116d1, // Myanmar Pao, introduced in Unicode 16.
		0x116db, // Myanmar Eastern Pwo Karen, introduced in Unicode 16.
		0x16131, // Gurung Khema, introduced in Unicode 16.
	} {
		if value, ok := decimalValue(r); ok {
			t.Errorf("U+%04X unexpectedly accepted as %d", r, value)
		}
	}
}

func TestDecimalMatchesEveryPython15CodePoint(t *testing.T) {
	// Independent reference generated with production Python 3.12:
	// buf = bytearray(0x110000)
	// for r in range(len(buf)):
	//     try: buf[r] = unicodedata.decimal(chr(r)) + 1
	//     except ValueError: pass
	// hashlib.sha256(buf).hexdigest()
	// Zero denotes rejection; 1..10 represent decimal values 0..9.
	buf := make([]byte, 0x110000)
	count := 0
	for r := range buf {
		if value, ok := decimalValue(rune(r)); ok {
			buf[r] = byte(value + 1)
			count++
		}
	}
	if count != 680 {
		t.Fatalf("accepted %d code points, want 680", count)
	}
	digest := sha256.Sum256(buf)
	const want = "63786f7ca550846ae22618aeff8eb7c9dcd25b8aae895b6bf8276ce90abec8b5"
	if got := hex.EncodeToString(digest[:]); got != want {
		t.Fatalf("decimal membership/value checksum: got %s, want %s", got, want)
	}
}
