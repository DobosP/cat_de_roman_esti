// Package boardstats keeps anonymous daily-board aggregates. The caller
// verifies the board and terminal result and admits each session at most once.
package boardstats

import (
	"errors"
	"fmt"
	"log"
	"os"
	"sync"
	"time"
)

const (
	RetentionDays = 14
	MinimumRounds = 100
	flushInterval = 30 * time.Second

	maxBoardsPerDay    = 256
	maxBucketsPerDay   = 16_384
	maxBucketsPerBoard = 4_096
	// Round totals remain exact in JSON consumers, and multiplying by 100
	// for the percentile fits in uint64.
	maxRounds uint64 = 1<<53 - 1
)

var (
	ErrLocked   = errors.New("board stats directory already has a writer")
	ErrClosed   = errors.New("board stats store is closed")
	ErrInvalid  = errors.New("invalid board stats key or result")
	ErrDate     = errors.New("board stats date is outside the retention window")
	ErrCapacity = errors.New("board stats capacity reached")
)

// Key identifies the shared board. The content digest is lowercase SHA-256 hex
// and Day is a server-local calendar date written as YYYY-MM-DD.
type Key struct {
	RulesVersion  int    `json:"rules_version"`
	ContentDigest string `json:"content_digest"`
	Day           string `json:"day"`
	Game          string `json:"game"`
	BoardID       string `json:"board_id"`
}

type Outcome uint8

const (
	Win Outcome = iota + 1
	Loss
	GiveUp
)

type Tier string

const (
	Perfect   Tier = "perfect"
	Top10     Tier = "top_10"
	TopHalf   Tier = "top_half"
	Completed Tier = "completed"
)

type Place struct {
	BetterThanPct int    `json:"better_than_pct"`
	Tier          Tier   `json:"tier"`
	Rounds        uint64 `json:"rounds"`
}

type Options struct {
	// Now returns time in the server's date zone. Defaults to time.Now.
	Now func() time.Time
	// Report receives snapshot corruption and background persistence errors.
	// It may run under the store lock. It must return promptly and must not
	// call store methods. Defaults to logging.
	Report func(error)
}

type board struct {
	wins    map[int]uint64
	losses  uint64
	giveUps uint64
	rounds  uint64
}

type day struct {
	boards  map[Key]*board
	buckets int
	dirty   bool
}

// Store owns one directory lock until Close and is safe for concurrent use.
type Store struct {
	mu           sync.Mutex
	dir          *os.Root
	lock         *os.File
	now          func() time.Time
	report       func(error)
	days         map[string]*day
	latest       time.Time
	prunedBefore string
	closed       bool

	stop      chan struct{}
	stopped   chan struct{}
	closeOnce sync.Once
	closeErr  error
}

// Open acquires sole writer ownership, reads retained snapshots, and starts
// periodic persistence. The caller enables the feature by choosing a directory.
func Open(dir string, options Options) (*Store, error) {
	if dir == "" {
		return nil, errors.New("board stats directory is empty")
	}
	if options.Now == nil {
		options.Now = time.Now
	}
	if options.Report == nil {
		options.Report = func(err error) { log.Printf("board stats: %v", err) }
	}
	if err := os.MkdirAll(dir, 0700); err != nil {
		return nil, fmt.Errorf("prepare board stats directory: %w", err)
	}
	root, err := os.OpenRoot(dir)
	if err != nil {
		return nil, fmt.Errorf("open board stats directory: %w", err)
	}
	lock, err := openLock(root)
	if err != nil {
		return nil, errors.Join(err, root.Close())
	}
	store := &Store{
		dir: root, lock: lock, now: options.Now, report: options.Report,
		days: make(map[string]*day), latest: options.Now(),
		stop: make(chan struct{}), stopped: make(chan struct{}),
	}
	if err := store.load(); err != nil {
		return nil, errors.Join(err, lock.Close(), root.Close())
	}
	go store.flushPeriodically()
	return store, nil
}

func (s *Store) flushPeriodically() {
	defer close(s.stopped)
	ticker := time.NewTicker(flushInterval)
	defer ticker.Stop()
	for {
		select {
		case <-s.stop:
			return
		case <-ticker.C:
			if err := s.Flush(); err != nil && !errors.Is(err, ErrClosed) {
				s.report(err)
			}
		}
	}
}

// Record adds one admitted finished round. A new key or bucket above the
// retention bounds leaves the aggregate intact. Only wins use the step count.
func (s *Store) Record(key Key, outcome Outcome, steps int) error {
	if !validKey(key) || outcome < Win || outcome > GiveUp || outcome == Win && !validSteps(steps) {
		return ErrInvalid
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.closed {
		return ErrClosed
	}
	oldest, today := s.dayBounds()
	if key.Day < oldest || key.Day > today {
		return ErrDate
	}
	s.discardExpired(oldest)

	d, err := s.restoreDay(key.Day)
	if err != nil {
		return err
	}
	b := d.boards[key]
	if b == nil {
		if len(d.boards) >= maxBoardsPerDay {
			return ErrCapacity
		}
		b = &board{}
	}
	if b.rounds == maxRounds {
		return ErrCapacity
	}
	if outcome == Win && b.wins[steps] == 0 {
		if len(b.wins) >= maxBucketsPerBoard || d.buckets >= maxBucketsPerDay {
			return ErrCapacity
		}
		if b.wins == nil {
			b.wins = make(map[int]uint64)
		}
		d.buckets++
	}
	switch outcome {
	case Win:
		b.wins[steps]++
	case Loss:
		b.losses++
	case GiveUp:
		b.giveUps++
	}
	b.rounds++
	if d.boards == nil {
		d.boards = make(map[Key]*board)
	}
	d.boards[key] = b
	d.dirty = true
	return nil
}

// Place compares the caller's verified win to the board's completed rounds.
// Losses and give-ups rank below every win; equal win steps do not count.
func (s *Store) Place(key Key, steps int) (Place, bool) {
	if !validKey(key) || !validSteps(steps) {
		return Place{}, false
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.closed {
		return Place{}, false
	}
	oldest, today := s.dayBounds()
	if key.Day < oldest || key.Day > today {
		return Place{}, false
	}
	s.discardExpired(oldest)
	d, err := s.restoreDay(key.Day)
	if err != nil {
		return Place{}, false
	}
	b := d.boards[key]
	if b == nil || b.rounds < MinimumRounds {
		return Place{}, false
	}
	below := b.losses + b.giveUps
	for saved, count := range b.wins {
		if saved > steps {
			below += count
		}
	}
	pct := int(100 * below / b.rounds)
	tier := Completed
	switch {
	case steps == 0:
		tier = Perfect
	case pct >= 90:
		tier = Top10
	case pct >= 50:
		tier = TopHalf
	}
	return Place{BetterThanPct: pct, Tier: tier, Rounds: b.rounds}, true
}

func (s *Store) dayBounds() (oldest, today string) {
	now := s.now()
	today = now.Format(time.DateOnly)
	// A clock correction cannot re-admit dates already pruned or widen the
	// number of retained in-memory days.
	if today > s.latest.Format(time.DateOnly) {
		s.latest = now
	}
	return s.latest.AddDate(0, 0, 1-RetentionDays).Format(time.DateOnly), today
}

func (s *Store) discardExpired(oldest string) {
	for saved := range s.days {
		if saved < oldest {
			delete(s.days, saved)
		}
	}
}

// Flush saves all changed days and removes expired snapshots. Failed writes
// remain pending for a later flush.
func (s *Store) Flush() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.closed {
		return ErrClosed
	}
	return s.flushLocked()
}

// Close stops background work, flushes pending writes, and releases the
// directory lock even on persistence failure. It is safe to call twice.
func (s *Store) Close() error {
	s.closeOnce.Do(func() {
		close(s.stop)
		<-s.stopped

		s.mu.Lock()
		defer s.mu.Unlock()
		s.closed = true
		s.closeErr = errors.Join(s.flushLocked(), s.lock.Close(), s.dir.Close())
	})
	return s.closeErr
}

func validDate(value string) bool {
	if len(value) != len(time.DateOnly) {
		return false
	}
	_, err := time.Parse(time.DateOnly, value)
	return err == nil
}

func validSteps(steps int) bool {
	return steps >= 0 && uint64(steps) <= maxRounds
}

func validDigest(digest string) bool {
	if len(digest) != 64 {
		return false
	}
	for _, c := range digest {
		if !(c >= '0' && c <= '9' || c >= 'a' && c <= 'f') {
			return false
		}
	}
	return true
}

func validKey(key Key) bool {
	if key.RulesVersion <= 0 || !validDigest(key.ContentDigest) || !validDate(key.Day) ||
		len(key.BoardID) == 0 || len(key.BoardID) > 128 {
		return false
	}
	for _, c := range key.BoardID {
		if !(c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' ||
			c == '_' || c == '-' || c == ':' || c == '.') {
			return false
		}
	}
	switch key.Game {
	case "intrusul", "perechi", "conexiuni", "contexto", "lant", "alchimie":
		return true
	default:
		return false
	}
}
