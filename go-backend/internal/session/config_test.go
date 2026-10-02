package session

import (
	"math"
	"strings"
	"testing"
	"time"
)

func ptr(s string) *string { return &s }
func TestPythonSessionConfiguration(t *testing.T) {
	cfg, e := ParseConfig(nil, nil)
	if e != nil || cfg.TTLSeconds != 7200 || cfg.MaxSessions != 1000 {
		t.Fatal(cfg, e)
	}
	for _, raw := range []string{"1.25", "  +١.٢٥  ", "1_2.5e-1", "１.２５"} {
		cfg, e := ParseConfig(ptr(raw), nil)
		if e != nil || cfg.TTLSeconds != 1.25 {
			t.Fatal(raw, cfg, e)
		}
	}
	for _, raw := range []string{"+٣", " ３ ", "0_3"} {
		cfg, e := ParseConfig(nil, ptr(raw))
		if e != nil || cfg.MaxSessions != 3 {
			t.Fatal(raw, cfg, e)
		}
	}
	for _, raw := range []string{"", "0", "-1", "NaN", "inf", "1e309", "1__2", "\x1c1.25\x1f", "١_.٢"} {
		if _, e := ParseConfig(ptr(raw), nil); e == nil || !strings.Contains(e.Error(), ttlEnv) {
			t.Fatal("invalid TTL accepted", raw)
		}
	}
	for _, raw := range []string{"", "0", "-1", "1.0", "1e3", "3__0", "0x10", "\x1c3\x1f", "𑯱"} {
		if _, e := ParseConfig(nil, ptr(raw)); e == nil || !strings.Contains(e.Error(), capEnv) {
			t.Fatal("invalid capacity accepted", raw)
		}
	}
	cfg, e = ParseConfig(ptr("1e-100"), ptr(strings.Repeat("9", 100)))
	if e != nil || cfg.TTLSeconds <= 0 || cfg.MaxSessions != math.MaxInt {
		t.Fatal("positive settings lost", cfg, e)
	}
	cfg, e = ParseConfig(ptr("1e100"), nil)
	if e != nil || cfg.TTLSeconds != 1e100 {
		t.Fatal("huge finite TTL rejected", cfg, e)
	}
}
func TestEveryDefaultStoreReadsEnvironment(t *testing.T) {
	t.Setenv(ttlEnv, "0.25")
	t.Setenv(capEnv, "2")
	s := New[int]()
	if s.ttl != .25 || s.max != 2 {
		t.Fatal("constructor ignored configuration")
	}
	a, _ := s.Create(1)
	_, _ = s.Create(2)
	_, _ = s.Create(3)
	if s.Len() != 2 {
		t.Fatal("cap not enforced")
	}
	if found, _ := s.Transaction(a, func(int) error { return nil }); found {
		t.Fatal("idle LRU not evicted")
	}
	clock := time.Unix(0, 0)
	s.now = func() time.Time { return clock }
	s.entries = map[string]*entry[int]{}
	s.lru.Init()
	id, _ := s.Create(1)
	clock = clock.Add(250 * time.Millisecond)
	if found, _ := s.Transaction(id, func(int) error { return nil }); !found {
		t.Fatal("TTL boundary should survive")
	}
	clock = clock.Add(251 * time.Millisecond)
	if found, _ := s.Transaction(id, func(int) error { return nil }); found {
		t.Fatal("fractional TTL ignored")
	}
}
