package session

import (
	"errors"
	"fmt"
	"runtime"
	"sync"
	"testing"
	"time"
)

type testClock struct {
	mu    sync.Mutex
	value time.Time
}

func (c *testClock) now() time.Time { c.mu.Lock(); defer c.mu.Unlock(); return c.value }
func (c *testClock) advance(duration time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.value = c.value.Add(duration)
}

func newTestStore[T any](t *testing.T, ttl time.Duration, max int) (*Store[T], *testClock) {
	t.Helper()
	clock := &testClock{value: time.Unix(0, 0)}
	store, err := NewWithOptions[T](ttl, max, clock.now)
	if err != nil {
		t.Fatal(err)
	}
	return store, clock
}

func create[T any](t *testing.T, store *Store[T], value T) string {
	t.Helper()
	id, err := store.Create(value)
	if err != nil {
		t.Fatal(err)
	}
	return id
}

func exists[T any](t *testing.T, store *Store[T], id string) bool {
	t.Helper()
	found, err := store.Transaction(id, func(T) error { return nil })
	if err != nil {
		t.Fatal(err)
	}
	return found
}

func TestSlidingTTLBoundaryAndRenewal(t *testing.T) {
	store, clock := newTestStore[int](t, 10*time.Second, 5)
	id := create(t, store, 1)
	clock.advance(10 * time.Second)
	if !exists(t, store, id) {
		t.Fatal("exact TTL must remain live")
	}
	clock.advance(9 * time.Second)
	if !exists(t, store, id) {
		t.Fatal("transaction must refresh TTL")
	}
	clock.advance(10*time.Second + time.Nanosecond)
	if exists(t, store, id) || store.Len() != 0 {
		t.Fatal("idle session must expire")
	}
}

func TestLRUEvictionTouchAndCryptographicIDs(t *testing.T) {
	store, _ := newTestStore[int](t, 0, 2)
	first, second := create(t, store, 1), create(t, store, 2)
	if len(first) != 36 || first[14] != '4' || first == second {
		t.Fatalf("invalid uuid4: %q %q", first, second)
	}
	if !exists(t, store, first) {
		t.Fatal("first missing")
	}
	third := create(t, store, 3)
	if exists(t, store, second) || !exists(t, store, first) || !exists(t, store, third) || store.Len() != 2 {
		t.Fatal("LRU capacity violated")
	}
}

func TestPinnedCapacityExpiryAndDeletion(t *testing.T) {
	store, clock := newTestStore[int](t, time.Second, 1)
	id := create(t, store, 1)
	started, release, done := make(chan struct{}), make(chan struct{}), make(chan error, 1)
	go func() {
		_, err := store.Transaction(id, func(int) error { close(started); <-release; return nil })
		done <- err
	}()
	<-started
	clock.advance(2 * time.Second)
	if store.PurgeExpired() != 0 || store.Len() != 1 || store.Delete(id) {
		t.Fatal("pinned session detached")
	}
	if _, err := store.Create(2); !errors.Is(err, ErrCapacity) {
		t.Fatalf("wanted capacity error, got %v", err)
	}
	close(release)
	if err := <-done; err != nil {
		t.Fatal(err)
	}
	if store.PurgeExpired() != 1 || store.Len() != 0 {
		t.Fatal("released expired session not reclaimed")
	}
}

func TestExpiredPinnedEntryDoesNotBlockIdleExpiry(t *testing.T) {
	store, clock := newTestStore[int](t, time.Second, 3)
	id := create(t, store, 1)
	started, release, done := make(chan struct{}), make(chan struct{}), make(chan struct{})
	go func() { store.Transaction(id, func(int) error { close(started); <-release; return nil }); close(done) }()
	<-started
	create(t, store, 2)
	clock.advance(2 * time.Second)
	if removed := store.PurgeExpired(); removed != 1 {
		t.Fatalf("removed %d; pinned entry blocked younger expiry", removed)
	}
	close(release)
	<-done
}

func TestQueuedTransactionsRemainPinned(t *testing.T) {
	store, clock := newTestStore[int](t, time.Second, 1)
	id := create(t, store, 1)
	started, release, done := make(chan struct{}), make(chan struct{}), make(chan struct{}, 2)
	go func() {
		store.Transaction(id, func(int) error { close(started); <-release; return nil })
		done <- struct{}{}
	}()
	<-started
	waiterEntered := make(chan struct{})
	go func() {
		store.Transaction(id, func(int) error { close(waiterEntered); return nil })
		done <- struct{}{}
	}()
	deadline := time.Now().Add(3 * time.Second)
	for {
		store.mu.Lock()
		borrowers := store.entries[id].borrowers
		store.mu.Unlock()
		if borrowers == 2 {
			break
		}
		if time.Now().After(deadline) {
			t.Fatal("waiter did not pin")
		}
		runtime.Gosched()
	}
	clock.advance(2 * time.Second)
	if _, err := store.Create(2); !errors.Is(err, ErrCapacity) {
		t.Fatal("queued waiter must prevent eviction")
	}
	close(release)
	<-waiterEntered
	<-done
	<-done
	if !exists(t, store, id) {
		t.Fatal("waiter must renew TTL at acquisition")
	}
}

func TestAtomicRequestsAndIndependentSessions(t *testing.T) {
	store, _ := newTestStore[*int](t, 0, 2)
	value, otherValue := 0, 0
	id, other := create(t, store, &value), create(t, store, &otherValue)
	const workers = 100
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			found, err := store.Transaction(id, func(value *int) error { *value++; return nil })
			if !found || err != nil {
				t.Errorf("transaction: %t %v", found, err)
			}
		}()
	}
	wg.Wait()
	if value != workers {
		t.Fatalf("lost updates: %d", value)
	}
	started, release, done := make(chan struct{}), make(chan struct{}), make(chan struct{})
	go func() { store.Transaction(id, func(*int) error { close(started); <-release; return nil }); close(done) }()
	<-started
	otherDone := make(chan struct{})
	go func() { store.Transaction(other, func(value *int) error { *value = 99; return nil }); close(otherDone) }()
	select {
	case <-otherDone:
	case <-time.After(3 * time.Second):
		t.Fatal("global lock held during transaction")
	}
	close(release)
	<-done
	if otherValue != 99 {
		t.Fatal("independent transaction lost")
	}
}

func TestCallbackErrorPanicAndMissingDoNotLeakPins(t *testing.T) {
	store, _ := newTestStore[int](t, 0, 1)
	id := create(t, store, 1)
	want := fmt.Errorf("callback")
	found, err := store.Transaction(id, func(int) error { return want })
	if !found || !errors.Is(err, want) {
		t.Fatalf("callback error lost: %v", err)
	}
	func() {
		defer func() {
			if recover() == nil {
				t.Error("missing panic")
			}
		}()
		store.Transaction(id, func(int) error { panic("test") })
	}()
	if !store.Delete(id) {
		t.Fatal("callback leaked pin")
	}
	for i := 0; i < 1000; i++ {
		if exists(t, store, fmt.Sprint(i)) {
			t.Fatal("unexpected session")
		}
	}
	if store.Len() != 0 {
		t.Fatal("missing ids created locks or entries")
	}
}

func TestConfigurationAndDefaults(t *testing.T) {
	if DefaultTTL != 7200*time.Second || DefaultMaxSessions != 1000 {
		t.Fatal("production bounds changed")
	}
	if _, err := NewWithOptions[int](-time.Second, 1, time.Now); err == nil {
		t.Fatal("negative ttl accepted")
	}
	if _, err := NewWithOptions[int](time.Second, -1, time.Now); err == nil {
		t.Fatal("negative cap accepted")
	}
	if _, err := NewWithOptions[int](time.Second, 1, nil); err == nil {
		t.Fatal("nil clock accepted")
	}
}
