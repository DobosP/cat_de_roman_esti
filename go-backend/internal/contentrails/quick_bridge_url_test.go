package contentrails

import "testing"

// Expected identities use the existing Python independence sidecar contract;
// aliases are never fresh nonauthor sources. These are synthetic URLs only.
func TestQuickBridgeURLNormalizationContract(t *testing.T) {
	cases := []struct{ input, want string }{
		{"https://EXAMPLE.test:0443/author#section", "https://example.test/author"},
		{"http://example.test:00080/author", "http://example.test/author"},
		{"https://example.test:08081/author", "https://example.test:8081/author"},
		{"https://example.test:/author", "https://example.test/author"},
		{"https://example.test/author?a=2&a=1", "https://example.test/author?a=1&a=2"},
		{"https://example.test/author?z=&a=two+words&a=one", "https://example.test/author?a=one&a=two+words&z="},
		{"https://[2001:db8::1]:0443/author", "https://[2001:db8::1]/author"},
		{"https://example.test", "https://example.test/"},
	}
	for _, c := range cases {
		t.Run(c.input, func(t *testing.T) {
			got, err := bridgeURL(c.input)
			if err != nil || got != c.want {
				t.Fatalf("normalized %q = %q (%v), want %q", c.input, got, err, c.want)
			}
			if _, err = bridgeSources([]any{c.input, c.want}); err == nil {
				t.Fatal("equivalent source locators were not recognized as duplicates")
			}
		})
	}
}

func TestQuickBridgeURLDoesNotMergeDistinctResources(t *testing.T) {
	cases := [][2]string{
		{"https://example.test/a%2Fb", "https://example.test/a/b"},
		{"https://example.test/author?a=1", "https://example.test/author?a=2"},
		{"https://example.test:8081/author", "https://example.test:8082/author"},
	}
	for _, c := range cases {
		t.Run(c[0], func(t *testing.T) {
			a, errA := bridgeURL(c[0])
			b, errB := bridgeURL(c[1])
			if errA != nil || errB != nil || a == b {
				t.Fatalf("distinct resources merged or refused: %q (%v), %q (%v)", a, errA, b, errB)
			}
		})
	}
}

func TestQuickBridgeURLRefusesInvalidPorts(t *testing.T) {
	for _, value := range []string{"https://example.test:65536/a", "https://example.test:999999999999999999999999/a", "https://example.test:-1/a", "https://example.test:word/a"} {
		t.Run(value, func(t *testing.T) {
			if _, err := bridgeURL(value); err == nil {
				t.Fatal("invalid port was accepted")
			}
		})
	}
}
