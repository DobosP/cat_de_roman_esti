// Package session owns bounded, process-local state for anonymous games.
package session

import (
	"container/list"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"sync"
	"time"
)

const (
	DefaultTTL         = 2 * time.Hour
	DefaultMaxSessions = 1000
)

var ErrCapacity = errors.New("all session slots are currently busy")

type entry[T any] struct {
	id          string
	value       T
	lastAccess  time.Time
	position    *list.Element
	transaction sync.Mutex
	borrowers   int // Includes both the current transaction and callers waiting for it.
}

// Store serializes operations on each session independently. Locks belong to the
// bounded entries, so missing ids and evicted sessions cannot accumulate locks.
type Store[T any] struct {
	mu      sync.Mutex
	entries map[string]*entry[T]
	lru     *list.List
	ttl     time.Duration
	max     int
	now     func() time.Time
}

func New[T any]() *Store[T] {
	store, _ := NewWithOptions[T](DefaultTTL, DefaultMaxSessions, time.Now)
	return store
}

// NewWithOptions permits deterministic expiry tests. A zero TTL disables expiry,
// and a zero maximum disables capacity limiting. Production uses New's bounds.
// The supplied clock must be monotonic, as time.Now is when comparing its values.
func NewWithOptions[T any](ttl time.Duration, max int, now func() time.Time) (*Store[T], error) {
	if ttl < 0 || max < 0 || now == nil {
		return nil, errors.New("invalid session store configuration")
	}
	return &Store[T]{entries: make(map[string]*entry[T]), lru: list.New(), ttl: ttl, max: max, now: now}, nil
}

func uuid() (string, error) {
	var bytes [16]byte
	if _, err := rand.Read(bytes[:]); err != nil {
		return "", err
	}
	bytes[6] = (bytes[6] & 0x0f) | 0x40
	bytes[8] = (bytes[8] & 0x3f) | 0x80
	var encoded [36]byte
	hex.Encode(encoded[:8], bytes[:4])
	encoded[8] = '-'
	hex.Encode(encoded[9:13], bytes[4:6])
	encoded[13] = '-'
	hex.Encode(encoded[14:18], bytes[6:8])
	encoded[18] = '-'
	hex.Encode(encoded[19:23], bytes[8:10])
	encoded[23] = '-'
	hex.Encode(encoded[24:], bytes[10:])
	return string(encoded[:]), nil
}

func (s *Store[T]) remove(entry *entry[T]) {
	delete(s.entries, entry.id)
	s.lru.Remove(entry.position)
}

func (s *Store[T]) purge(now time.Time) int {
	if s.ttl == 0 {
		return 0
	}
	removed := 0
	for item := s.lru.Front(); item != nil; {
		next := item.Next()
		entry := item.Value.(*entry[T])
		// Access times are ordered by LRU. Skip old pinned entries, but stop as
		// soon as a live timestamp means every later entry is younger too.
		if now.Sub(entry.lastAccess) <= s.ttl {
			break
		}
		if entry.borrowers == 0 {
			s.remove(entry)
			removed++
		}
		item = next
	}
	return removed
}

func (s *Store[T]) touch(entry *entry[T], now time.Time) {
	entry.lastAccess = now
	s.lru.MoveToBack(entry.position)
}

// Create evicts the least recently used idle session at capacity. Active or
// queued transactions stay pinned; it fails immediately if all slots are busy.
func (s *Store[T]) Create(value T) (string, error) {
	for {
		id, err := uuid()
		if err != nil {
			return "", err
		}
		s.mu.Lock()
		if _, exists := s.entries[id]; exists {
			s.mu.Unlock()
			continue
		}
		now := s.now()
		s.purge(now)
		if s.max > 0 && len(s.entries) >= s.max {
			var idle *entry[T]
			for item := s.lru.Front(); item != nil; item = item.Next() {
				if candidate := item.Value.(*entry[T]); candidate.borrowers == 0 {
					idle = candidate
					break
				}
			}
			if idle == nil {
				s.mu.Unlock()
				return "", ErrCapacity
			}
			s.remove(idle)
		}
		entry := &entry[T]{id: id, value: value, lastAccess: now}
		entry.position = s.lru.PushBack(entry)
		s.entries[id] = entry
		s.mu.Unlock()
		return id, nil
	}
}

// Transaction pins and exclusively borrows a session for one request. The
// callback must not retain mutable session references or recursively transact on
// this same id. No global lock is held while waiting or while callback work runs.
func (s *Store[T]) Transaction(id string, fn func(T) error) (bool, error) {
	s.mu.Lock()
	s.purge(s.now())
	entry := s.entries[id]
	if entry != nil {
		entry.borrowers++
	}
	s.mu.Unlock()
	if entry == nil {
		return false, nil
	}
	entry.transaction.Lock()
	defer func() {
		entry.transaction.Unlock()
		s.mu.Lock()
		entry.borrowers--
		s.mu.Unlock()
	}()
	s.mu.Lock()
	s.touch(entry, s.now()) // Waiting alone cannot refresh the sliding deadline.
	s.mu.Unlock()
	return true, fn(entry.value)
}

func (s *Store[T]) Delete(id string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	entry := s.entries[id]
	if entry == nil || entry.borrowers != 0 {
		return false
	}
	s.remove(entry)
	return true
}

func (s *Store[T]) PurgeExpired() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.purge(s.now())
}

func (s *Store[T]) Len() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.purge(s.now())
	return len(s.entries)
}
