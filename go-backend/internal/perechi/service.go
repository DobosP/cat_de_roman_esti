// Package perechi implements four private reviewed pairs and anonymous sessions.
package perechi

import (
	"fmt"
	"math/big"
	"slices"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/session"
)

type Error = gameapi.Error
type pair struct {
	members []string
	label   string
}
type gameSession struct {
	pairs               []pair
	order               []string
	solved              []int
	wrongHistory        [][]string
	mistakes, hintsUsed int
	hinted              int
	won, lost           bool
	daily, category     string
	sourceRing          []string
}
type Service struct {
	data    *content.Content
	catalog *catalog.Catalog
	store   *session.Store[*gameSession]
}

func New(data *content.Content) *Service {
	return &Service{data, catalog.New(data), session.New[*gameSession]()}
}
func fail(status int, detail string) *Error { return &Error{Status: status, Detail: detail} }
func list(value any) ([]string, bool) {
	switch values := value.(type) {
	case []string:
		return slices.Clone(values), true
	case []any:
		out := make([]string, len(values))
		for i, v := range values {
			var ok bool
			out[i], ok = v.(string)
			if !ok {
				return nil, false
			}
		}
		return out, true
	}
	return nil, false
}

func build(board *content.Board, rng *pyrandom.Random, daily, category string, previous []string) (*gameSession, *Error) {
	raw, ok := board.Payload["pairs"].([]any)
	if !ok || len(raw) != 4 {
		return nil, fail(503, "Catalogul Perechi este invalid.")
	}
	game := &gameSession{daily: daily, category: category, hinted: -1, solved: []int{}, wrongHistory: [][]string{}}
	unique := map[string]bool{}
	for _, value := range raw {
		row, ok := value.(map[string]any)
		if !ok || len(row) != 2 {
			return nil, fail(503, "Catalogul Perechi este invalid.")
		}
		members, ok := list(row["members"])
		label, hasLabel := row["group_label"].(string)
		if !ok || len(members) != 2 || !hasLabel {
			return nil, fail(503, "Catalogul Perechi este invalid.")
		}
		for _, id := range members {
			if unique[id] {
				return nil, fail(503, "Catalogul Perechi este invalid.")
			}
			unique[id] = true
			game.order = append(game.order, id)
		}
		game.pairs = append(game.pairs, pair{members, label})
	}
	rng.Shuffle(len(game.order), func(i, j int) { game.order[i], game.order[j] = game.order[j], game.order[i] })
	for _, source := range previous {
		if source != board.SourceID {
			game.sourceRing = append(game.sourceRing, source)
		}
	}
	game.sourceRing = append(game.sourceRing, board.SourceID)
	if len(game.sourceRing) > 4 {
		game.sourceRing = game.sourceRing[len(game.sourceRing)-4:]
	}
	return game, nil
}

func (s *Service) Create(seed *big.Int, daily, category, previous string, starter bool) (map[string]any, *Error) {
	if category != "" {
		if _, ok := s.data.CategoryLabels[category]; !ok {
			return nil, fail(400, "Categorie necunoscută.")
		}
	}
	var rng *pyrandom.Random
	var board *content.Board
	var ring []string
	if daily != "" {
		rng = pyrandom.NewUint64(catalog.DailySeed(daily, "perechi"))
		board = s.catalog.PickDaily("perechi", daily, category)
	} else {
		rng = pyrandom.New(seed)
		if previous != "" {
			s.store.Transaction(previous, func(game *gameSession) error { ring = slices.Clone(game.sourceRing); return nil })
		}
		excluded := map[string]bool{}
		for _, source := range ring {
			excluded[source] = true
		}
		passes := []map[string]bool{excluded}
		if len(excluded) > 0 {
			passes = append(passes, nil)
		}
		profiles := []bool{false}
		if starter {
			profiles = []bool{true, false}
		}
		for _, exclusions := range passes {
			for _, profile := range profiles {
				board = s.catalog.PickSeeded("perechi", rng, catalog.PickOptions{Category: category, ExcludeSources: exclusions, Starter: profile, BalanceCategories: starter})
				if board != nil {
					break
				}
			}
			if board != nil {
				break
			}
		}
	}
	if board == nil {
		return nil, fail(503, "Nu există jocuri Perechi pentru filtrul ales.")
	}
	game, err := build(board, rng, daily, category, ring)
	if err != nil {
		return nil, err
	}
	state := s.state("", game)
	id, createErr := s.store.Create(game)
	if createErr != nil {
		return nil, fail(503, "Prea multe jocuri active. Încearcă din nou.")
	}
	state["game_id"] = id
	return state, nil
}

func (s *Service) concept(id string) map[string]string {
	label, ok := s.data.Labels[id]
	if !ok {
		label = id
	}
	return map[string]string{"id": id, "label": label}
}
func (s *Service) pairPayload(p pair) map[string]any {
	tiles := make([]map[string]string, len(p.members))
	for i, id := range p.members {
		tiles[i] = s.concept(id)
	}
	return map[string]any{"tiles": tiles, "label": p.label}
}
func score(g *gameSession) int {
	if g.lost {
		return 0
	}
	return max(100, 1000-100*g.mistakes-150*g.hintsUsed)
}
func share(g *gameSession) string {
	word := "greșeli"
	if g.mistakes == 1 {
		word = "greșeală"
	}
	header := fmt.Sprintf("cat_de_roman_esti · Perechi · %d %s", g.mistakes, word)
	if g.hintsUsed > 0 {
		header += " · indiciu"
	}
	if g.daily != "" {
		header += " · " + g.daily
	}
	return header + "\n" + strings.Repeat("🟩", len(g.solved)) + strings.Repeat("⬜", 4-len(g.solved))
}
func hintAvailable(g *gameSession) bool {
	return !g.won && !g.lost && g.hintsUsed < 1 && g.mistakes >= 2 && len(g.solved) < 4
}
func (s *Service) state(id string, g *gameSession) map[string]any {
	tiles := make([]map[string]any, len(g.order))
	for i, node := range g.order {
		solved := false
		for _, p := range g.solved {
			if slices.Contains(g.pairs[p].members, node) {
				solved = true
				break
			}
		}
		c := s.concept(node)
		tiles[i] = map[string]any{"id": node, "label": c["label"], "solved": solved}
	}
	solved := make([]map[string]any, len(g.solved))
	for i, p := range g.solved {
		solved[i] = s.pairPayload(g.pairs[p])
	}
	body := map[string]any{"game_id": id, "tiles": tiles, "solved_pairs": solved, "solved_count": len(g.solved), "remaining_pairs": 4 - len(g.solved), "mistakes": g.mistakes, "remaining_mistakes": 6 - g.mistakes, "actions": len(g.solved) + len(g.wrongHistory), "hint_available": hintAvailable(g), "hints_used": g.hintsUsed, "won": g.won, "lost": g.lost}
	if g.hinted >= 0 {
		body["hint"] = s.pairPayload(g.pairs[g.hinted])
	}
	if g.daily != "" {
		body["daily"] = g.daily
	}
	if g.category != "" {
		body["board_category"] = g.category
	}
	if g.won || g.lost {
		body["score"] = score(g)
		body["share"] = share(g)
		solution := make([]map[string]any, len(g.pairs))
		for i, p := range g.pairs {
			solution[i] = s.pairPayload(p)
		}
		body["solution"] = solution
	}
	return body
}
func (s *Service) action(id string, fn func(*gameSession) (map[string]any, *Error)) (map[string]any, *Error) {
	var body map[string]any
	var err *Error
	found, _ := s.store.Transaction(id, func(g *gameSession) error { body, err = fn(g); return nil })
	if !found {
		return nil, fail(404, "Joc inexistent")
	}
	return body, err
}
func (s *Service) Get(id string) (map[string]any, *Error) {
	return s.action(id, func(g *gameSession) (map[string]any, *Error) { return s.state(id, g), nil })
}
func (s *Service) Match(id string, ids []string) (map[string]any, *Error) {
	return s.MatchInput(id, func() ([]string, *Error) { return ids, nil })
}
func (s *Service) MatchInput(id string, validate func() ([]string, *Error)) (map[string]any, *Error) {
	return s.action(id, func(g *gameSession) (map[string]any, *Error) {
		if g.won || g.lost {
			return nil, fail(400, "Jocul s-a terminat")
		}
		ids, err := validate()
		if err != nil {
			return nil, err
		}
		if len(ids) != 2 || ids[0] == ids[1] {
			return nil, fail(400, "Alege exact două concepte distincte")
		}
		for _, node := range ids {
			if !slices.Contains(g.order, node) {
				return nil, fail(400, "Concept care nu e pe tablă")
			}
		}
		for _, node := range ids {
			for _, p := range g.solved {
				if slices.Contains(g.pairs[p].members, node) {
					return nil, fail(400, "Concept deja rezolvat")
				}
			}
		}
		for i, p := range g.pairs {
			if slices.Contains(p.members, ids[0]) && slices.Contains(p.members, ids[1]) {
				g.solved = append(g.solved, i)
				g.won = len(g.solved) == 4
				body := s.state(id, g)
				body["ok"], body["correct"], body["pair"] = true, true, s.pairPayload(p)
				return body, nil
			}
		}
		key := slices.Clone(ids)
		slices.Sort(key)
		for _, previous := range g.wrongHistory {
			if slices.Equal(previous, key) {
				body := s.state(id, g)
				body["ok"], body["correct"], body["repeated"] = true, false, true
				return body, nil
			}
		}
		g.wrongHistory = append(g.wrongHistory, key)
		g.mistakes++
		g.lost = g.mistakes >= 6
		body := s.state(id, g)
		body["ok"], body["correct"], body["repeated"] = true, false, false
		return body, nil
	})
}
func (s *Service) Hint(id string) (map[string]any, *Error) {
	return s.action(id, func(g *gameSession) (map[string]any, *Error) {
		if g.won || g.lost {
			return nil, fail(400, "Jocul s-a terminat")
		}
		if g.hintsUsed >= 1 {
			return nil, fail(400, "Indiciul a fost deja folosit")
		}
		if g.mistakes < 2 {
			return nil, fail(400, "Indiciul se deschide după două greșeli.")
		}
		for i := range g.pairs {
			if !slices.Contains(g.solved, i) {
				g.hinted = i
				break
			}
		}
		g.hintsUsed++
		body := s.state(id, g)
		body["ok"] = true
		return body, nil
	})
}
