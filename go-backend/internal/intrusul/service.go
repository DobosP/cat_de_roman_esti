// Package intrusul implements the anonymous server-authoritative 3+1 game.
package intrusul

import (
	"errors"
	"fmt"
	"math/big"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/session"
)

const (
	GameKey         = "intrusul"
	MaxMistakes     = 3
	SourceRingLimit = 4
)

// Error describes a stable public API error. Private content is never included.
type Error struct {
	Status int
	Detail any
}

func (e *Error) Error() string { return fmt.Sprint(e.Detail) }

type gameSession struct {
	members                         []string
	intruder, groupLabel            string
	order                           []string
	difficulty, sourceID, catalogID string
	sourceRing                      []string
	daily, category                 string
	wrongIDs                        []string
	attempts                        int
	hintUsed, won, lost             bool
}

func (s *gameSession) finished() bool { return s.won || s.lost }

func (s *gameSession) score() int {
	if !s.won {
		return 0
	}
	result := 1000 - 200*len(s.wrongIDs)
	if s.hintUsed {
		result -= 150
	}
	if result < 100 {
		return 100
	}
	return result
}

// Service owns an immutable catalog and a bounded process-local session store.
type Service struct {
	content *content.Content
	catalog *catalog.Catalog
	store   *session.Store[*gameSession]
}

func New(data *content.Content) *Service {
	return &Service{content: data, catalog: catalog.New(data), store: session.New[*gameSession]()}
}

func contains(values []string, value string) bool {
	for _, candidate := range values {
		if candidate == value {
			return true
		}
	}
	return false
}

func stringList(value any) ([]string, bool) {
	switch items := value.(type) {
	case []string:
		return append([]string(nil), items...), true
	case []any:
		result := make([]string, len(items))
		for i, item := range items {
			var ok bool
			result[i], ok = item.(string)
			if !ok {
				return nil, false
			}
		}
		return result, true
	default:
		return nil, false
	}
}

func build(board *content.Board, rng *pyrandom.Random, daily, category string, previous []string) (*gameSession, *Error) {
	members, ok := stringList(board.Payload["members"])
	intruder, hasIntruder := board.Payload["intruder"].(string)
	group, hasGroup := board.Payload["group_label"].(string)
	if !ok || len(members) != 3 || !hasIntruder || !hasGroup || intruder == "" || group == "" {
		return nil, &Error{503, "Tabla aleasă nu mai este validă."}
	}
	order := append(append([]string(nil), members...), intruder)
	unique := make(map[string]bool, len(order))
	for _, id := range order {
		if id == "" || unique[id] {
			return nil, &Error{503, "Tabla aleasă nu mai este validă."}
		}
		unique[id] = true
	}
	rng.Shuffle(len(order), func(i, j int) { order[i], order[j] = order[j], order[i] })
	ring := make([]string, 0, SourceRingLimit+1)
	for _, source := range previous {
		if source != board.SourceID {
			ring = append(ring, source)
		}
	}
	ring = append(ring, board.SourceID)
	if len(ring) > SourceRingLimit {
		ring = ring[len(ring)-SourceRingLimit:]
	}
	return &gameSession{members: members, intruder: intruder, groupLabel: group, order: order, difficulty: board.Difficulty, sourceID: board.SourceID, catalogID: board.CatalogID, sourceRing: ring, daily: daily, category: category, wrongIDs: []string{}}, nil
}

func (s *Service) Create(seed *big.Int, daily, category, previous string, starter bool) (map[string]any, *Error) {
	if category != "" {
		if _, known := s.content.CategoryLabels[category]; !known {
			return nil, &Error{400, "Categorie necunoscută."}
		}
	}
	var board *content.Board
	var rng *pyrandom.Random
	ring := []string{}
	if daily != "" {
		board = s.catalog.PickDaily(GameKey, daily, category)
		rng = pyrandom.NewUint64(catalog.DailySeed(daily, GameKey))
	} else {
		rng = pyrandom.New(seed)
		if previous != "" {
			_, _ = s.store.Transaction(previous, func(game *gameSession) error { ring = append(ring, game.sourceRing...); return nil })
		}
		excluded := make(map[string]bool, len(ring))
		for _, source := range ring {
			excluded[source] = true
		}
		passes := []map[string]bool{excluded}
		if len(excluded) > 0 {
			passes = append(passes, nil)
		}
		for _, exclusions := range passes {
			opts := catalog.PickOptions{Category: category, ExcludeSources: exclusions, BalanceCategories: starter}
			if starter {
				opts.Starter = true
				board = s.catalog.PickSeeded(GameKey, rng, opts)
				if board != nil {
					break
				}
			}
			opts.Starter = false
			board = s.catalog.PickSeeded(GameKey, rng, opts)
			if board != nil {
				break
			}
		}
	}
	if board == nil {
		return nil, &Error{503, "Nu există încă jocuri sigure pentru această categorie."}
	}
	game, err := build(board, rng, daily, category, ring)
	if err != nil {
		return nil, err
	}
	// Snapshot before publishing mutable state to the store. Every returned list and
	// map is owned by the response, including a concurrent create/eviction workload.
	body := s.state("", game)
	id, createErr := s.store.Create(game)
	if createErr != nil {
		if errors.Is(createErr, session.ErrCapacity) {
			return nil, &Error{503, "Prea multe jocuri active. Încearcă din nou."}
		}
		return nil, &Error{503, "Jocul nu a putut fi creat. Încearcă din nou."}
	}
	body["game_id"] = id
	return body, nil
}

func (s *Service) concept(id string) map[string]string {
	label, ok := s.content.Labels[id]
	if !ok {
		label = id
	}
	return map[string]string{"id": id, "label": label}
}

func (s *Service) concepts(ids []string) []map[string]string {
	result := make([]map[string]string, len(ids))
	for i, id := range ids {
		result[i] = s.concept(id)
	}
	return result
}

func (s *Service) share(game *gameSession) string {
	header := "cat_de_roman_esti · Intrusul"
	if game.category != "" {
		header += " · " + s.content.CategoryLabels[game.category]
	}
	result := "🟥"
	if game.won {
		result = "🟩"
	}
	attemptWord := "încercări"
	if game.attempts == 1 {
		attemptWord = "încercare"
	}
	detail := fmt.Sprintf("%s %d %s", result, game.attempts, attemptWord)
	if game.hintUsed {
		detail += " · indiciu"
	}
	share := header + "\n" + detail
	if game.daily != "" {
		share += "\n" + game.daily
	}
	return share
}

func (s *Service) state(id string, game *gameSession) map[string]any {
	remaining := MaxMistakes - len(game.wrongIDs)
	if remaining < 0 {
		remaining = 0
	}
	hints := 0
	if game.hintUsed {
		hints = 1
	}
	wrong := append([]string{}, game.wrongIDs...)
	body := map[string]any{"game_id": id, "tiles": s.concepts(game.order), "wrong_ids": wrong, "attempts": game.attempts, "mistakes": len(wrong), "remaining_mistakes": remaining, "won": game.won, "lost": game.lost, "difficulty": game.difficulty, "hints_used": hints, "hint_available": !game.finished() && len(wrong) > 0 && !game.hintUsed}
	if game.daily != "" {
		body["daily"] = game.daily
	}
	if game.category != "" {
		body["board_category"] = game.category
	}
	if game.hintUsed {
		body["clue"] = map[string]string{"label": game.groupLabel, "message": "Trei cuvinte țin de: " + game.groupLabel + "."}
	}
	if game.finished() {
		body["score"] = game.score()
		body["share"] = s.share(game)
		body["solution"] = map[string]any{"intruder": s.concept(game.intruder), "group": map[string]any{"label": game.groupLabel, "tiles": s.concepts(game.members)}}
	}
	return body
}

func (s *Service) action(id string, fn func(*gameSession) (map[string]any, *Error)) (map[string]any, *Error) {
	var result map[string]any
	var err *Error
	found, _ := s.store.Transaction(id, func(game *gameSession) error { result, err = fn(game); return nil })
	if !found {
		return nil, &Error{404, "Joc inexistent"}
	}
	return result, err
}

func (s *Service) Get(id string) (map[string]any, *Error) {
	return s.action(id, func(game *gameSession) (map[string]any, *Error) { return s.state(id, game), nil })
}

func (s *Service) Guess(id, selected string) (map[string]any, *Error) {
	return s.GuessInput(id, func() (string, *Error) { return selected, nil })
}

// GuessInput validates an HTTP body inside the same pinned transaction as the
// mutation. Missing-session lookup precedes validation; validation precedes the
// terminal guard, matching the existing anonymous API's error precedence.
func (s *Service) GuessInput(id string, validate func() (string, *Error)) (map[string]any, *Error) {
	return s.action(id, func(game *gameSession) (map[string]any, *Error) {
		selected, validationErr := validate()
		if validationErr != nil {
			return nil, validationErr
		}
		if game.finished() {
			return nil, &Error{400, "Jocul s-a terminat"}
		}
		selected = strings.TrimSpace(selected)
		if !contains(game.order, selected) {
			return nil, &Error{400, "Concept care nu este pe tablă"}
		}
		if contains(game.wrongIDs, selected) {
			body := s.state(id, game)
			body["ok"], body["correct"], body["already_tried"], body["message"] = true, false, true, "Deja încercat · fără cost."
			return body, nil
		}
		game.attempts++
		correct := selected == game.intruder
		message := "Exact — acesta este intrusul!"
		if correct {
			game.won = true
		} else {
			game.wrongIDs = append(game.wrongIDs, selected)
			game.lost = len(game.wrongIDs) >= MaxMistakes
			message = "Face parte din grup. Mai încearcă."
			if game.lost {
				message = "Gata — îți arăt intrusul și legătura dintre celelalte trei."
			}
		}
		body := s.state(id, game)
		body["ok"], body["correct"], body["already_tried"], body["message"] = true, correct, false, message
		return body, nil
	})
}

func (s *Service) Hint(id string) (map[string]any, *Error) {
	return s.action(id, func(game *gameSession) (map[string]any, *Error) {
		if game.finished() {
			return nil, &Error{400, "Jocul s-a terminat"}
		}
		if game.hintUsed {
			return nil, &Error{400, "Indiciul a fost deja folosit"}
		}
		if len(game.wrongIDs) == 0 {
			return nil, &Error{400, "Indiciul apare după prima încercare."}
		}
		game.hintUsed = true
		body := s.state(id, game)
		body["ok"] = true
		return body, nil
	})
}

// Progress exposes only server-authored terminal bookkeeping, never solutions.
func (s *Service) Progress(id string) (string, bool, bool, int, bool) {
	finished, won, result, found := false, false, -1, false
	s.action(id, func(game *gameSession) (map[string]any, *Error) {
		found = true
		finished = game.won || game.lost
		won = game.won
		if finished {
			result = game.score()
		}
		return nil, nil
	})
	return "", finished, won, result, found
}
