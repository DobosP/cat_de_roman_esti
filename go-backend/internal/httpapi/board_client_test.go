package httpapi

import (
	"net/http"
	"net/http/httptest"
	"net/netip"
	"testing"
	"time"
)

func TestBoardClientAddress(t *testing.T) {
	for _, tc := range []struct {
		name, peer, want string
		values           []string
	}{
		{"Caddy selects IPv4", "172.20.0.4:8443", "198.51.100.8", []string{"198.51.100.8"}},
		{"Caddy selects IPv6", "[fd01::4]:8443", "2001:db8::2", []string{"2001:db8::2"}},
		{"mapped IPv6", "127.0.0.1:8443", "198.51.100.8", []string{"::ffff:198.51.100.8"}},
		{"public peer cannot forward", "203.0.113.10:8443", "203.0.113.10", []string{"198.51.100.8"}},
		{"direct local peer", "127.0.0.1:8443", "127.0.0.1", nil},
		{"list rejected", "172.20.0.4:8443", "", []string{"198.51.100.7, 198.51.100.8"}},
		{"duplicate rejected", "172.20.0.4:8443", "", []string{"198.51.100.7", "198.51.100.8"}},
		{"zone rejected", "172.20.0.4:8443", "", []string{"fe80::1%eth0"}},
		{"unspecified rejected", "172.20.0.4:8443", "", []string{"::ffff:0.0.0.0"}},
		{"empty rejected", "172.20.0.4:8443", "", []string{""}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, "http://localhost/", nil)
			req.RemoteAddr = tc.peer
			req.Header.Set("X-Forwarded-For", "192.0.2.1")
			req.Header.Set("CF-Connecting-IP", "192.0.2.2")
			for _, value := range tc.values {
				req.Header.Add(boardClientIPHeader, value)
			}
			want, _ := netip.ParseAddr(tc.want)
			if got := boardClientAddress(req); got != want {
				t.Fatalf("client address = %s; want %s", got, want)
			}
		})
	}
}

func TestBoardRoundLimiterClearsExpiredWindowWithoutTraffic(t *testing.T) {
	var limiter boardRoundLimiter
	now := time.Now()
	first := netip.MustParseAddr("192.0.2.1")
	second := netip.MustParseAddr("192.0.2.2")
	for i := 0; i < roundLimit; i++ {
		if !limiter.allow(first, now) {
			t.Fatal("window ended before its bound")
		}
	}
	if limiter.allow(first, now) || !limiter.allow(second, now) {
		t.Fatal("rate limit failed or affected a separate client")
	}
	limiter.mu.Lock()
	old := limiter.peers[first]
	other := limiter.peers[second]
	limiter.mu.Unlock()
	if !limiter.allow(first, now.Add(roundLimitWindow)) {
		t.Fatal("expired window blocked an active client")
	}
	limiter.expire(first, old) // An old timer may finish after a window was replaced.
	limiter.mu.Lock()
	active := limiter.peers[first]
	limiter.mu.Unlock()
	if active == nil || active == old {
		t.Fatal("stale timer removed the replacement window")
	}
	// Let the actual timer callbacks expire the remaining addresses immediately.
	active.timer.Reset(0)
	other.timer.Reset(0)
	deadline := time.After(2 * time.Second)
	tick := time.NewTicker(time.Millisecond)
	defer tick.Stop()
	for {
		limiter.mu.Lock()
		empty := len(limiter.peers) == 0
		limiter.mu.Unlock()
		if empty {
			return
		}
		select {
		case <-tick.C:
		case <-deadline:
			t.Fatal("timer expiry kept client addresses")
		}
	}
}

func TestBoardRoundLimiterCapsDistinctClients(t *testing.T) {
	now := time.Now()
	limiter := boardRoundLimiter{peers: make(map[netip.Addr]*roundAllowance)}
	for i := 0; i < roundLimitPeers; i++ {
		address := netip.AddrFrom4([4]byte{10, 0, byte(i >> 8), byte(i)})
		limiter.peers[address] = &roundAllowance{until: now.Add(roundLimitWindow)}
	}
	known := netip.MustParseAddr("10.0.0.0")
	newClient := netip.MustParseAddr("192.0.2.1")
	if limiter.allow(newClient, now) || !limiter.allow(known, now) {
		t.Fatal("client cap admitted a new address or affected a tracked address")
	}
}
