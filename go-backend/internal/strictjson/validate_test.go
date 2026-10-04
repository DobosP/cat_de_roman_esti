package strictjson

import (
	"strings"
	"testing"
)

func TestStrictPrivateUnicodeAndBindings(t *testing.T) {
	for _, raw := range []string{`{"s":"\ud800"}`, `{"s":"\udfff"}`, `{"s":"\ud800\u0041"}`, `{"s":"\ud800\\udfff"}`, `{"s":"\uDC00\uD800"}`, `{"binding":"reject","binding":"approve"}`, `{"binding":false,"b\u0069nding":true}`, strings.Repeat("[", 66) + "0" + strings.Repeat("]", 66), "{\"s\":\"\xff\"}"} {
		if Validate([]byte(raw)) == nil {
			t.Fatal("private input silently repaired/ambiguous")
		}
	}
	for _, raw := range []string{`{"s":"\ud83d\ude00"}`, `{"s":"\uD83D\uDE00"}`, `{"s":"literal \\ud800"}`, `{"s":"Șară 😀"}`, `{"Body":"{\"text\":\"\\ud800\"}"}`, `{"s":"\ufffd"}`} {
		if err := Validate([]byte(raw)); err != nil {
			t.Fatal("valid scalar/domain-negative envelope rejected", raw, err)
		}
	}
}
