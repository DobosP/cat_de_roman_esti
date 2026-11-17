package boardstats

import (
	"bytes"
	"cmp"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"slices"
	"strings"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
)

const (
	snapshotSchema   = 1
	maxSnapshotBytes = 1 << 20
	snapshotPrefix   = "boardstats-"
	tempPrefix       = ".boardstats-"
	lockName         = ".boardstats.lock"
)

var errCorruptSnapshot = errors.New("corrupt board stats snapshot")

type storedBucket struct {
	Steps int    `json:"steps"`
	Count uint64 `json:"count"`
}

type storedBoard struct {
	Key
	Wins    []storedBucket `json:"wins"`
	Losses  uint64         `json:"losses"`
	GiveUps uint64         `json:"give_ups"`
}

type snapshotData struct {
	Schema int           `json:"schema_version"`
	Day    string        `json:"day"`
	Boards []storedBoard `json:"boards"`
}

type snapshot struct {
	Data     snapshotData `json:"data"`
	Checksum string       `json:"sha256"`
}

func openLock(dir *os.Root) (*os.File, error) {
	info, err := dir.Lstat(lockName)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return nil, err
	}
	if info != nil && !info.Mode().IsRegular() {
		return nil, errors.New("board stats lock is not a regular file")
	}
	f, err := dir.OpenFile(lockName, os.O_CREATE|os.O_RDWR, 0600)
	if err != nil {
		return nil, err
	}
	if err = sameRegularFile(dir, f, lockName); err == nil {
		err = takeLock(f)
	}
	if err != nil {
		_ = f.Close()
		return nil, fmt.Errorf("lock board stats directory: %w", err)
	}
	return f, nil
}

func sameRegularFile(dir *os.Root, file *os.File, name string) error {
	entry, err := dir.Lstat(name)
	if err != nil {
		return err
	}
	info, err := file.Stat()
	if err != nil {
		return err
	}
	if !entry.Mode().IsRegular() || !info.Mode().IsRegular() || !os.SameFile(entry, info) {
		return errors.New("board stats path is not the opened regular file")
	}
	return nil
}

func snapshotDay(name string) (string, bool) {
	day, ok := strings.CutPrefix(name, snapshotPrefix)
	if !ok {
		return "", false
	}
	day, ok = strings.CutSuffix(day, ".json")
	return day, ok && validDate(day)
}

func isTemporarySnapshot(name string) bool {
	id, ok := strings.CutPrefix(name, tempPrefix)
	if !ok {
		return false
	}
	id, ok = strings.CutSuffix(id, ".tmp")
	if !ok || len(id) != 32 {
		return false
	}
	_, err := hex.DecodeString(id)
	return err == nil
}

func walkDir(dir *os.Root, visit func(os.DirEntry)) error {
	f, err := dir.Open(".")
	if err != nil {
		return err
	}
	defer f.Close()
	for {
		entries, err := f.ReadDir(64)
		for _, entry := range entries {
			visit(entry)
		}
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}
	}
}

func (s *Store) load() error {
	today := s.trusted.Format(time.DateOnly)
	if err := walkDir(s.dir, func(entry os.DirEntry) {
		name := entry.Name()
		date, ok := snapshotDay(name)
		if !ok && !isTemporarySnapshot(name) {
			return
		}
		if !entry.Type().IsRegular() {
			s.report(fmt.Errorf("skip %s: expected a regular board stats file", name))
			return
		}
		if !ok {
			if err := s.dir.Remove(name); err != nil && !errors.Is(err, os.ErrNotExist) {
				s.report(fmt.Errorf("remove stale %s: %w", name, err))
			}
			return
		}
		if date > today {
			s.report(fmt.Errorf("defer %s: snapshot date is in the future", name))
			return
		}
		d, err := readSnapshot(s.dir, name, date)
		if err != nil {
			s.report(fmt.Errorf("skip %s: %w", name, err))
			return
		}
		if len(d.boards) > 0 {
			s.acceptRecordedDay(date)
			if date >= s.oldestDay() {
				s.days[date] = d
			}
		}
	}); err != nil {
		return fmt.Errorf("read board stats directory: %w", err)
	}
	if err := s.flushLocked(); err != nil {
		s.report(err)
	}
	return nil
}

// A snapshot can outlive a clock rollback. Restore it when its date is
// eligible again so the first new round cannot replace its previous counts.
// Leave filesystem failures uncached so future requests can retry the read.
// Callers check the date bounds before invoking this method.
func (s *Store) restoreDay(date string) (*day, error) {
	if d := s.days[date]; d != nil {
		return d, nil
	}
	name := snapshotPrefix + date + ".json"
	d, err := readSnapshot(s.dir, name, date)
	if errors.Is(err, errCorruptSnapshot) {
		s.report(fmt.Errorf("skip %s: %w", name, err))
		d = &day{}
	} else if err != nil {
		return nil, fmt.Errorf("read %s: %w", name, err)
	}
	if len(d.boards) > 0 {
		s.acceptRecordedDay(date)
		s.days[date] = d
	}
	return d, nil
}

func readSnapshot(dir *os.Root, name, date string) (*day, error) {
	info, err := dir.Lstat(name)
	if errors.Is(err, os.ErrNotExist) {
		return &day{}, nil
	}
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() {
		return nil, errors.New("expected a regular board stats file")
	}
	f, err := dir.Open(name)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	if err := sameRegularFile(dir, f, name); err != nil {
		return nil, err
	}
	raw, err := io.ReadAll(io.LimitReader(f, maxSnapshotBytes+1))
	if err != nil {
		return nil, err
	}
	if len(raw) > maxSnapshotBytes {
		return nil, fmt.Errorf("%w: file too large", errCorruptSnapshot)
	}
	if err := strictjson.Validate(raw); err != nil {
		return nil, fmt.Errorf("%w: %w", errCorruptSnapshot, err)
	}
	d, err := decodeSnapshot(raw, date)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", errCorruptSnapshot, err)
	}
	return d, nil
}

func decodeSnapshot(raw []byte, date string) (*day, error) {
	var input snapshot
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&input); err != nil {
		return nil, err
	}
	data := input.Data
	if data.Schema != snapshotSchema || data.Day != date || len(data.Boards) == 0 || len(data.Boards) > maxBoardsPerDay {
		return nil, errors.New("invalid board stats snapshot schema, date, or size")
	}
	checksum, err := snapshotDigest(data)
	if err != nil || input.Checksum != checksum {
		return nil, errors.New("board stats snapshot checksum mismatch")
	}
	d := &day{boards: make(map[Key]*board, len(data.Boards))}
	for _, row := range data.Boards {
		if !validKey(row.Key) || row.Day != date || d.boards[row.Key] != nil ||
			len(row.Wins) > maxBucketsPerBoard || d.buckets+len(row.Wins) > maxBucketsPerDay {
			return nil, errors.New("invalid board stats row or duplicate board")
		}
		if row.Losses > maxRounds || row.GiveUps > maxRounds-row.Losses {
			return nil, errors.New("invalid board stats totals")
		}
		b := &board{
			wins: make(map[int]uint64, len(row.Wins)), losses: row.Losses, giveUps: row.GiveUps,
			rounds: row.Losses + row.GiveUps,
		}
		for _, bucket := range row.Wins {
			if !validSteps(bucket.Steps) || bucket.Count == 0 || bucket.Count > maxRounds-b.rounds ||
				b.wins[bucket.Steps] != 0 {
				return nil, errors.New("invalid board stats step bucket or duplicate count")
			}
			b.wins[bucket.Steps] = bucket.Count
			b.rounds += bucket.Count
		}
		if b.rounds == 0 {
			return nil, errors.New("empty board stats row")
		}
		d.boards[row.Key] = b
		d.buckets += len(row.Wins)
	}
	return d, nil
}

func snapshotDigest(data snapshotData) (string, error) {
	encoded, err := json.Marshal(data)
	if err != nil {
		return "", err
	}
	digest := sha256.Sum256(encoded)
	return hex.EncodeToString(digest[:]), nil
}

func collectDay(date string, d *day) snapshotData {
	rows := make([]storedBoard, 0, len(d.boards))
	for key, b := range d.boards {
		row := storedBoard{
			Key: key, Wins: make([]storedBucket, 0, len(b.wins)), Losses: b.losses, GiveUps: b.giveUps,
		}
		for steps, count := range b.wins {
			row.Wins = append(row.Wins, storedBucket{Steps: steps, Count: count})
		}
		slices.SortFunc(row.Wins, func(a, b storedBucket) int { return cmp.Compare(a.Steps, b.Steps) })
		rows = append(rows, row)
	}
	slices.SortFunc(rows, func(a, b storedBoard) int {
		return cmp.Or(cmp.Compare(a.RulesVersion, b.RulesVersion),
			cmp.Compare(a.ContentDigest, b.ContentDigest), cmp.Compare(a.Game, b.Game), cmp.Compare(a.BoardID, b.BoardID))
	})
	return snapshotData{Schema: snapshotSchema, Day: date, Boards: rows}
}

func writeSnapshot(dir *os.Root, date string, d *day) error {
	data := collectDay(date, d)
	checksum, err := snapshotDigest(data)
	if err != nil {
		return err
	}
	raw, err := json.Marshal(snapshot{Data: data, Checksum: checksum})
	if err != nil {
		return err
	}
	if len(raw)+1 > maxSnapshotBytes {
		return errors.New("board stats snapshot too large")
	}

	var suffix [16]byte
	rand.Read(suffix[:])
	temp := tempPrefix + hex.EncodeToString(suffix[:]) + ".tmp"
	f, err := dir.OpenFile(temp, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	defer dir.Remove(temp)
	_, err = f.Write(append(raw, '\n'))
	if err == nil {
		err = f.Sync()
	}
	if err = errors.Join(err, f.Close()); err != nil {
		return err
	}
	if err := dir.Rename(temp, snapshotPrefix+date+".json"); err != nil {
		return err
	}
	return syncDirectory(dir)
}

func (s *Store) flushLocked() error {
	oldest, _ := s.dayBounds()
	s.discardExpired(oldest)

	var result error
	if !s.latest.IsZero() && s.prunedBefore != oldest {
		var removeErr error
		scanErr := walkDir(s.dir, func(entry os.DirEntry) {
			if !entry.Type().IsRegular() {
				return
			}
			date, isSnapshot := snapshotDay(entry.Name())
			if !isTemporarySnapshot(entry.Name()) && (!isSnapshot || date >= oldest) {
				return
			}
			if err := s.dir.Remove(entry.Name()); err != nil && !errors.Is(err, os.ErrNotExist) && removeErr == nil {
				removeErr = err
			}
		})
		if err := errors.Join(removeErr, scanErr); err != nil {
			result = fmt.Errorf("prune board stats snapshots: %w", err)
		} else {
			s.prunedBefore = oldest
		}
	}
	for date, d := range s.days {
		if !d.dirty {
			continue
		}
		if err := writeSnapshot(s.dir, date, d); err != nil {
			result = errors.Join(result, fmt.Errorf("write board stats for %s: %w", date, err))
			continue
		}
		d.dirty = false
	}
	return result
}
