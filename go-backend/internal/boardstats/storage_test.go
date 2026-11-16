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

func TestRestartPrunesExpiredSnapshotsAndReportsCorruption(t *testing.T) {
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
	for _, absent := range []string{snapshotName(expired), temp} {
		if _, err := os.Stat(filepath.Join(dir, absent)); !errors.Is(err, os.ErrNotExist) {
			t.Fatalf("expired or abandoned file %s remains: %v", absent, err)
		}
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
