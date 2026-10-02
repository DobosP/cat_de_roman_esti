package session

import (
	"fmt"
	"math"
	"math/big"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

const ttlEnv = "CAT_SESSION_TTL_SECONDS"
const capEnv = "CAT_MAX_SESSIONS_PER_GAME"

type Config struct {
	TTLSeconds  float64
	MaxSessions int
}

var floatSyntax = regexp.MustCompile(`^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$`)

// Decimal zeroes are the same frozen CPython 3.12 / Unicode 15 groups used by
// the HTTP parser. Environment parsing is independent of the transport package.
var envDecimalZeros = [...]rune{0x30, 0x660, 0x6f0, 0x7c0, 0x966, 0x9e6, 0xa66, 0xae6, 0xb66, 0xbe6, 0xc66, 0xce6, 0xd66, 0xde6, 0xe50, 0xed0, 0xf20, 0x1040, 0x1090, 0x17e0, 0x1810, 0x1946, 0x19d0, 0x1a80, 0x1a90, 0x1b50, 0x1bb0, 0x1c40, 0x1c50, 0xa620, 0xa8d0, 0xa900, 0xa9d0, 0xa9f0, 0xaa50, 0xabf0, 0xff10, 0x104a0, 0x10d30, 0x11066, 0x110f0, 0x11136, 0x111d0, 0x112f0, 0x11450, 0x114d0, 0x11650, 0x116c0, 0x11730, 0x118e0, 0x11950, 0x11c50, 0x11d50, 0x11da0, 0x11f50, 0x16a60, 0x16ac0, 0x16b50, 0x1d7ce, 0x1d7d8, 0x1d7e2, 0x1d7ec, 0x1d7f6, 0x1e140, 0x1e2f0, 0x1e4f0, 0x1e950, 0x1fbf0}

func envDecimal(r rune) (byte, bool) {
	i := sort.Search(len(envDecimalZeros), func(i int) bool { return envDecimalZeros[i] > r }) - 1
	if i >= 0 && r-envDecimalZeros[i] < 10 {
		return byte(r-envDecimalZeros[i]) + '0', true
	}
	return 0, false
}
func numericSpace(c rune) bool {
	return c >= 9 && c <= 13 || c == 32 || c == 0x85 || c == 0xa0 || c == 0x1680 || c >= 0x2000 && c <= 0x200a || c == 0x2028 || c == 0x2029 || c == 0x202f || c == 0x205f || c == 0x3000
}
func numericText(raw string) (string, int, bool) {
	runes := []rune(strings.TrimFunc(raw, numericSpace))
	var b strings.Builder
	digits := 0
	for i, r := range runes {
		if digit, ok := envDecimal(r); ok {
			b.WriteByte(digit)
			digits++
			continue
		}
		if r == '_' {
			if i == 0 || i+1 == len(runes) {
				return "", 0, false
			}
			if _, ok := envDecimal(runes[i-1]); !ok {
				return "", 0, false
			}
			if _, ok := envDecimal(runes[i+1]); !ok {
				return "", 0, false
			}
			continue
		}
		if r > 127 {
			return "", 0, false
		}
		b.WriteRune(r)
	}
	return b.String(), digits, true
}

// ParseConfig is pure for tests. Positive finite fractional TTLs are retained as
// seconds rather than rounded to Duration, so tiny values never disable expiry.
func ParseConfig(ttlRaw, capRaw *string) (Config, error) {
	cfg := Config{DefaultTTL.Seconds(), DefaultMaxSessions}
	if ttlRaw != nil {
		raw, _, ok := numericText(*ttlRaw)
		value, err := strconv.ParseFloat(raw, 64)
		if !ok || !floatSyntax.MatchString(raw) || err != nil || math.IsNaN(value) || math.IsInf(value, 0) || value <= 0 {
			return Config{}, fmt.Errorf("%s must be a positive number", ttlEnv)
		}
		cfg.TTLSeconds = value
	}
	if capRaw != nil {
		raw, digits, ok := numericText(*capRaw)
		value, parsed := new(big.Int).SetString(raw, 10)
		if !ok || digits > 4300 || !parsed || value.Sign() <= 0 {
			return Config{}, fmt.Errorf("%s must be a positive integer", capEnv)
		}
		if value.BitLen() > strconv.IntSize-1 {
			cfg.MaxSessions = int(^uint(0) >> 1)
		} else {
			cfg.MaxSessions = int(value.Int64())
		}
	}
	return cfg, nil
}
func configFromEnv() (Config, error) {
	var ttl, cap *string
	if v, ok := os.LookupEnv(ttlEnv); ok {
		ttl = &v
	}
	if v, ok := os.LookupEnv(capEnv); ok {
		cap = &v
	}
	return ParseConfig(ttl, cap)
}
