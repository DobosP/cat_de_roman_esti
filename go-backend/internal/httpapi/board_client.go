package httpapi

import (
	"net/http"
	"net/netip"
	"sync"
	"time"
)

const (
	boardClientIPHeader = "X-Cat-Client-IP"
	roundLimit          = 20
	roundLimitWindow    = 10 * time.Minute
	roundLimitPeers     = 4096
	roundLimitIPv6Group = 64
)

func boardClientAddress(r *http.Request) netip.Addr {
	peerPort, err := netip.ParseAddrPort(r.RemoteAddr)
	if err != nil {
		return netip.Addr{}
	}
	peer := peerPort.Addr().WithZone("").Unmap()
	if peer.IsUnspecified() {
		return netip.Addr{}
	}
	// The Compose app's private ingress belongs to Caddy, which overwrites
	// this header. Local direct requests can fall back to the socket peer.
	if !peer.IsPrivate() && !peer.IsLoopback() {
		return peer
	}
	values := r.Header.Values(boardClientIPHeader)
	if len(values) == 0 {
		return peer
	}
	if len(values) != 1 {
		return netip.Addr{}
	}
	address, err := netip.ParseAddr(values[0])
	if err != nil || address.Zone() != "" || address.Unmap().IsUnspecified() {
		return netip.Addr{}
	}
	return address.Unmap()
}

type roundAllowance struct {
	until    time.Time
	lastUsed time.Time
	finished int
	timer    *time.Timer
}

// boardRoundLimiter keeps IPv4 addresses and IPv6 /64 prefixes in memory.
// Each IPv6 /48 can occupy at most 64 entries. Expiry removes idle keys,
// including when no more requests arrive.
type boardRoundLimiter struct {
	mu     sync.Mutex
	peers  map[netip.Addr]*roundAllowance
	groups map[netip.Prefix]int
}

func (l *boardRoundLimiter) allow(address netip.Addr, now time.Time) bool {
	if !address.IsValid() {
		return false
	}
	address = address.WithZone("").Unmap()
	if address.Is6() {
		address = netip.PrefixFrom(address, 64).Masked().Addr()
	}
	l.mu.Lock()
	defer l.mu.Unlock()

	window := l.peers[address]
	if window != nil && !now.Before(window.until) {
		l.remove(address)
		window = nil
	}
	if window == nil {
		group := netip.PrefixFrom(address, 48).Masked()
		if address.Is6() && l.groups[group] >= roundLimitIPv6Group {
			return false
		}
		if len(l.peers) >= roundLimitPeers {
			var oldest netip.Addr
			for candidate, allowance := range l.peers {
				if !oldest.IsValid() || allowance.lastUsed.Before(l.peers[oldest].lastUsed) {
					oldest = candidate
				}
			}
			l.remove(oldest)
		}
		if l.peers == nil {
			l.peers = make(map[netip.Addr]*roundAllowance)
		}
		window = &roundAllowance{until: now.Add(roundLimitWindow)}
		l.peers[address] = window
		if address.Is6() {
			if l.groups == nil {
				l.groups = make(map[netip.Prefix]int)
			}
			l.groups[group]++
		}
		window.timer = time.AfterFunc(roundLimitWindow, func() { l.expire(address, window) })
	}
	window.lastUsed = now
	if window.finished >= roundLimit {
		return false
	}
	window.finished++
	return true
}

func (l *boardRoundLimiter) expire(address netip.Addr, window *roundAllowance) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.peers[address] == window {
		l.remove(address)
	}
}

func (l *boardRoundLimiter) remove(address netip.Addr) {
	if window := l.peers[address]; window != nil && window.timer != nil {
		window.timer.Stop()
	}
	delete(l.peers, address)
	if address.Is6() {
		group := netip.PrefixFrom(address, 48).Masked()
		l.groups[group]--
		if l.groups[group] == 0 {
			delete(l.groups, group)
		}
	}
}
