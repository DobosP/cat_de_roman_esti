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
	finished int
	timer    *time.Timer
}

// boardRoundLimiter keeps addresses only in the process and removes each
// window at expiry, including when no more requests arrive.
type boardRoundLimiter struct {
	mu    sync.Mutex
	peers map[netip.Addr]*roundAllowance
}

func (l *boardRoundLimiter) allow(address netip.Addr, now time.Time) bool {
	if !address.IsValid() {
		return false
	}
	l.mu.Lock()
	defer l.mu.Unlock()

	window := l.peers[address]
	if window != nil && !now.Before(window.until) {
		window.timer.Stop()
		delete(l.peers, address)
		window = nil
	}
	if window == nil {
		if len(l.peers) >= roundLimitPeers {
			return false
		}
		if l.peers == nil {
			l.peers = make(map[netip.Addr]*roundAllowance)
		}
		window = &roundAllowance{until: now.Add(roundLimitWindow)}
		l.peers[address] = window
		window.timer = time.AfterFunc(roundLimitWindow, func() { l.expire(address, window) })
	}
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
		delete(l.peers, address)
	}
}
