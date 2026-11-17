package boardstats

import (
	"bytes"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func writeTestFile(t *testing.T, dir, name string, raw []byte) {
	t.Helper()
	if err := os.WriteFile(filepath.Join(dir, name), raw, 0600); err != nil {
		t.Fatal(err)
	}
}

func snapshotName(key Key) string { return snapshotPrefix + key.Day + ".json" }

func TestRestartReportsCorruptionWithoutAdvancingRetention(t *testing.T) {
	dir := t.TempDir()
	seed := openTest(t, dir, Options{Now: func() time.Time { return testDay(15) }})
	expired, retained, broken := testKey(2), testKey(3), testKey(15)
	recordN(t, seed, expired, Loss, 0, 100)
	recordN(t, seed, retained, Win, 3, 80)
	recordN(t, seed, retained, GiveUp, 0, 20)
	recordN(t, seed, broken, Loss, 0, 100)
	if err := seed.Close(); err != nil {
		t.Fatal(err)
	}
	before, err := os.ReadFile(filepath.Join(dir, snapshotName(broken)))
	if err != nil {
		t.Fatal(err)
	}
	after := bytes.Replace(before, []byte(`"losses":100`), []byte(`"losses":101`), 1)
	if bytes.Equal(before, after) {
		t.Fatal("no count to corrupt in the generated snapshot")
	}
	writeTestFile(t, dir, snapshotName(broken), after)
	temp := tempPrefix + strings.Repeat("d", 32) + ".tmp"
	writeTestFile(t, dir, temp, []byte("interrupted snapshot"))
	writeTestFile(t, dir, "owner-notes.txt", []byte("retained"))

	var reports []error
	options := Options{
		Now:    func() time.Time { return testDay(16) },
		Report: func(err error) { reports = append(reports, err) },
	}
	s := openTest(t, dir, options)
	if len(reports) != 1 || !strings.Contains(reports[0].Error(), snapshotName(broken)) ||
		!strings.Contains(reports[0].Error(), "checksum mismatch") {
		t.Fatalf("corruption reports: %v", reports)
	}
	if _, err := os.Stat(filepath.Join(dir, temp)); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("abandoned file %s remains: %v", temp, err)
	}
	if _, err := os.Stat(filepath.Join(dir, snapshotName(expired))); err != nil {
		t.Fatalf("a corrupt newer snapshot advanced retention: %v", err)
	}
	if _, err := os.Stat(filepath.Join(dir, "owner-notes.txt")); err != nil {
		t.Fatalf("unrelated file disappeared: %v", err)
	}
	want := Place{BetterThanPct: 20, Tier: Completed, Rounds: 100}
	if got, ok := s.Place(retained, 3); !ok || got != want {
		t.Fatalf("retained board: %+v, %t; want %+v", got, ok, want)
	}
	if _, ok := s.Place(broken, 0); ok {
		t.Fatal("corrupt file contributed counts")
	}
	if err := s.Record(broken, Win, 0); err != nil {
		t.Fatalf("corrupt bytes blocked new rounds: %v", err)
	}
	if fresh, err := Open(dir, options); !errors.Is(err, ErrLocked) {
		if fresh != nil {
			_ = fresh.Close()
		}
		t.Fatalf("second writer was not refused: %v", err)
	}
}

func TestFailedSnapshotWriteCanBeRetried(t *testing.T) {
	dir := t.TempDir()
	options := Options{Now: func() time.Time { return testDay(16) }}
	s := openTest(t, dir, options)
	key := testKey(16)
	recordN(t, s, key, Win, 2, 100)

	// An occupied destination should never turn a partial write into a
	// snapshot or clear the pending aggregate.
	target := filepath.Join(dir, snapshotName(key))
	if err := os.Mkdir(target, 0700); err != nil {
		t.Fatal(err)
	}
	if err := s.Flush(); err == nil {
		t.Fatal("expected a failure to replace the directory")
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		if isTemporarySnapshot(entry.Name()) {
			t.Fatalf("failed flush leaked %s", entry.Name())
		}
	}
	if err := os.Remove(target); err != nil {
		t.Fatal(err)
	}
	if err := s.Flush(); err != nil {
		t.Fatal(err)
	}
	if err := s.Close(); err != nil {
		t.Fatal(err)
	}
	s = openTest(t, dir, options)
	if got, ok := s.Place(key, 1); !ok || got != (Place{BetterThanPct: 100, Tier: Top10, Rounds: 100}) {
		t.Fatalf("retried write after reopening: %+v, %t", got, ok)
	}
}

func TestRetentionFollowsLocalCalendarAndDoesNotReopenPrunedDate(t *testing.T) {
	dir := t.TempDir()
	zone := testDay(16).Location()
	var clock atomic.Int64
	clock.Store(time.Date(2026, time.November, 16, 0, 1, 0, 0, zone).Unix())
	s := openTest(t, dir, Options{Now: func() time.Time { return time.Unix(clock.Load(), 0).In(zone) }})
	oldest, today := testKey(3), testKey(16)
	recordN(t, s, oldest, Win, 1, 100)
	recordN(t, s, today, Win, 1, 100)
	if err := s.Record(testKey(2), Win, 1); !errors.Is(err, ErrDate) {
		t.Fatalf("fourteenth previous day: %v", err)
	}
	if err := s.Record(testKey(17), Win, 1); !errors.Is(err, ErrDate) {
		t.Fatalf("future day: %v", err)
	}
	if err := s.Flush(); err != nil {
		t.Fatal(err)
	}
	clock.Add(int64((24 * time.Hour) / time.Second))
	if err := s.Record(testKey(17), Loss, 0); err != nil {
		t.Fatal(err)
	}
	if err := s.Flush(); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dir, snapshotName(oldest))); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("expired day remains on disk: %v", err)
	}
	if _, ok := s.Place(oldest, 0); ok {
		t.Fatal("expired day remained available")
	}
	clock.Add(-int64((24 * time.Hour) / time.Second))
	if err := s.Record(oldest, Win, 1); !errors.Is(err, ErrDate) {
		t.Fatalf("clock rollback re-admitted a pruned date: %v", err)
	}
	if got, ok := s.Place(today, 1); !ok || got.Rounds != 100 {
		t.Fatalf("retained current day changed: %+v, %t", got, ok)
	}
}

// Ported from TestCriticClockJump in the independent redesign review.
func TestForwardClockJumpCannotPruneOrAdmitSamples(t *testing.T) {
	dir := t.TempDir()
	var clock atomic.Int64
	clock.Store(testDay(16).Unix())
	var reports atomic.Int64
	options := Options{
		Now:    func() time.Time { return time.Unix(clock.Load(), 0).In(testDay(16).Location()) },
		Report: func(error) { reports.Add(1) },
	}
	store := openTest(t, dir, options)
	key := testKey(16)
	recordN(t, store, key, Loss, 0, 120)
	if err := store.Flush(); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, snapshotName(key))
	before, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	clock.Store(testDay(36).Unix())
	for range 2 {
		if err := store.Flush(); err != nil {
			t.Fatal(err)
		}
		if err := store.Record(testKey(36), Win, 0); !errors.Is(err, ErrDate) {
			t.Errorf("sample during +20-day jump returned %v", err)
		}
		if _, show := store.Place(key, 0); show {
			t.Error("place was shown during an untrusted clock reading")
		}
	}
	if reports.Load() != 1 {
		t.Errorf("one clock anomaly produced %d reports", reports.Load())
	}
	after, err := os.ReadFile(path)
	if err != nil || !bytes.Equal(before, after) {
		t.Errorf("clock jump removed or changed the existing snapshot: %v", err)
	}
	clock.Store(testDay(16).Unix())
	if err := store.Record(key, Win, 0); err != nil {
		t.Fatalf("corrected clock failed to recover: %v", err)
	}
	if place, show := store.Place(key, 0); !show || place.Rounds != 121 {
		t.Fatalf("recovered aggregate: %+v, shown=%t", place, show)
	}
}

func TestIdleClockTicksAndRestartKeepRetentionOnRecordedData(t *testing.T) {
	for _, restart := range []bool{false, true} {
		name := "idle periodic checks"
		if restart {
			name = "restart after twenty days"
		}
		t.Run(name, func(t *testing.T) {
			dir := t.TempDir()
			var clock atomic.Int64
			clock.Store(testDay(16).Unix())
			options := Options{Now: func() time.Time { return time.Unix(clock.Load(), 0).In(testDay(16).Location()) }}
			store := openTest(t, dir, options)
			key := testKey(16)
			recordN(t, store, key, Loss, 0, 100)
			if err := store.Flush(); err != nil {
				t.Fatal(err)
			}
			if restart {
				if err := store.Close(); err != nil {
					t.Fatal(err)
				}
				clock.Store(testDay(36).Unix())
				store = openTest(t, dir, options)
			} else {
				for day := 17; day <= 36; day++ {
					clock.Store(testDay(day).Unix())
					if err := store.Flush(); err != nil {
						t.Fatal(err)
					}
				}
			}
			path := filepath.Join(dir, snapshotName(key))
			if _, err := os.Stat(path); err != nil {
				t.Fatalf("clock reads alone pruned recorded data: %v", err)
			}
			if err := store.Record(testKey(36), Win, 0); err != nil {
				t.Fatalf("current sample after idle time: %v", err)
			}
			if err := store.Flush(); err != nil {
				t.Fatal(err)
			}
			if _, err := os.Stat(path); !errors.Is(err, os.ErrNotExist) {
				t.Fatalf("new recorded day failed to expire old data: %v", err)
			}
		})
	}
}

func TestFutureSnapshotIsRestoredAfterClockRollback(t *testing.T) {
	for _, checkPlaceFirst := range []bool{false, true} {
		name := "record first"
		if checkPlaceFirst {
			name = "place first"
		}
		t.Run(name, func(t *testing.T) {
			dir := t.TempDir()
			var clock atomic.Int64
			now := func() time.Time { return time.Unix(clock.Load(), 0).In(testDay(17).Location()) }
			options := Options{Now: now, Report: func(error) {}}
			key := testKey(17)
			clock.Store(testDay(17).Unix())
			seed := openTest(t, dir, options)
			recordN(t, seed, key, Win, 3, 100)
			if err := seed.Close(); err != nil {
				t.Fatal(err)
			}

			clock.Store(testDay(16).Unix())
			store := openTest(t, dir, options)
			if _, ok := store.Place(key, 2); ok {
				t.Fatal("future snapshot contributed before its date became eligible")
			}
			if err := store.Record(key, Loss, 0); !errors.Is(err, ErrDate) {
				t.Fatalf("future round: %v", err)
			}
			clock.Store(testDay(17).Unix())
			if checkPlaceFirst {
				if place, ok := store.Place(key, 2); !ok || place.Rounds != 100 {
					t.Fatalf("place from restored snapshot: %+v, %t", place, ok)
				}
			}
			if err := store.Record(key, Loss, 0); err != nil {
				t.Fatal(err)
			}
			if err := store.Close(); err != nil {
				t.Fatal(err)
			}
			store = openTest(t, dir, options)
			want := Place{BetterThanPct: 100, Tier: Top10, Rounds: 101}
			if place, ok := store.Place(key, 2); !ok || place != want {
				t.Fatalf("persisted place after rollback: %+v, %t; want %+v", place, ok, want)
			}
		})
	}
}

func TestUnreadableSnapshotWithholdsRoundAndPlaceUntilRecovery(t *testing.T) {
	dir := t.TempDir()
	key := testKey(17)
	var clock atomic.Int64
	now := func() time.Time { return time.Unix(clock.Load(), 0).In(testDay(17).Location()) }
	options := Options{Now: now, Report: func(error) {}}
	clock.Store(testDay(17).Unix())
	seed := openTest(t, dir, options)
	recordN(t, seed, key, Win, 3, 100)
	if err := seed.Close(); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, snapshotName(key))
	before, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}

	clock.Store(testDay(16).Unix())
	store := openTest(t, dir, options)
	clock.Store(testDay(17).Unix())
	// A closed Root makes the lazy filesystem read fail even as root, while
	// leaving the real snapshot and the store's original Root intact.
	blocked, err := os.OpenRoot(dir)
	if err != nil {
		t.Fatal(err)
	}
	if err := blocked.Close(); err != nil {
		t.Fatal(err)
	}
	store.mu.Lock()
	usable := store.dir
	store.dir = blocked
	store.mu.Unlock()
	recoverRead := func() {
		store.mu.Lock()
		store.dir = usable
		store.mu.Unlock()
	}
	t.Cleanup(recoverRead)

	if _, ok := store.Place(key, 0); ok {
		t.Fatal("place appeared before the snapshot could be read")
	}
	if err := store.Record(key, Loss, 0); !errors.Is(err, os.ErrClosed) {
		t.Fatalf("record with unreadable snapshot returned %v", err)
	}
	recoverRead()
	if err := store.Flush(); err != nil {
		t.Fatal(err)
	}
	after, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(before, after) {
		t.Fatal("failed admission modified the saved snapshot")
	}
	if place, ok := store.Place(key, 0); !ok || place.Rounds != 100 {
		t.Fatalf("recovered place: %+v, %t", place, ok)
	}
	if err := store.Record(key, Loss, 0); err != nil {
		t.Fatal(err)
	}
	if place, ok := store.Place(key, 0); !ok || place.Rounds != 101 {
		t.Fatalf("first admitted round after recovery: %+v, %t", place, ok)
	}
}

func TestSaturatedRoundCountPersistsWithoutArithmeticOverflow(t *testing.T) {
	dir := t.TempDir()
	key := testKey(16)
	data := snapshotData{
		Schema: snapshotSchema, Day: key.Day,
		Boards: []storedBoard{{
			Key: key, Wins: []storedBucket{{Steps: 1, Count: 1}},
			Losses: maxRounds - 2, GiveUps: 1,
		}},
	}
	checksum, err := snapshotDigest(data)
	if err != nil {
		t.Fatal(err)
	}
	raw, err := json.Marshal(snapshot{Data: data, Checksum: checksum})
	if err != nil {
		t.Fatal(err)
	}
	writeTestFile(t, dir, snapshotName(key), raw)
	s := openTest(t, dir, Options{Now: func() time.Time { return testDay(16) }})
	want := Place{BetterThanPct: 99, Tier: Top10, Rounds: maxRounds}
	if got, ok := s.Place(key, 1); !ok || got != want {
		t.Fatalf("saturated board: %+v, %t; want %+v", got, ok, want)
	}
	if err := s.Record(key, Win, 1); !errors.Is(err, ErrCapacity) {
		t.Fatalf("saturated board accepted another round: %v", err)
	}
	if got, ok := s.Place(key, 1); !ok || got != want {
		t.Fatalf("refused round changed the board: %+v, %t", got, ok)
	}
}
