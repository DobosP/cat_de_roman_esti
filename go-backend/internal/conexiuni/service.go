// Package conexiuni serves reviewed boards and the exact bounded KG fallback.
package conexiuni

import (
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pack"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/session"
	"math"
	"math/big"
	"slices"
	"sort"
	"strings"
	"sync"
	"unicode"
)

type Error = gameapi.Error
type gameSession struct {
	groups                      map[string][]string
	order, solved               []string
	lives, mistakes             int
	won, lost                   bool
	difficulty, daily, category string
	labels                      map[string]string
	clues                       []map[string]string
	clued                       []string
	cluesUsed                   int
	history                     [][]string
}
type rankedSet struct {
	categories   []string
	entanglement float64
}
type Service struct {
	data     *content.Content
	graph    *graph.Service
	pack     *pack.Pack
	store    *session.Store[*gameSession]
	ranked   []rankedSet
	rankOnce sync.Once
}

func New(data *content.Content) *Service { return NewWithGraph(data, graph.New(data)) }
func NewWithGraph(data *content.Content, g *graph.Service) *Service {
	s := &Service{data: data, graph: g, pack: pack.New(data), store: session.New[*gameSession]()}
	return s
}
func fail(status int, detail string) *Error { return &Error{Status: status, Detail: detail} }
func stringsList(value any) ([]string, bool) {
	switch a := value.(type) {
	case []string:
		return slices.Clone(a), true
	case []any:
		out := make([]string, len(a))
		for i, v := range a {
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
func newSession(groups map[string][]string, order []string, difficulty, daily, category string, labels map[string]string) *gameSession {
	return &gameSession{groups: groups, order: order, difficulty: difficulty, daily: daily, category: category, labels: labels, lives: 4, solved: []string{}, clues: []map[string]string{}, clued: []string{}, history: [][]string{}}
}
func keys(groups map[string][]string) []string {
	out := make([]string, 0, len(groups))
	for key := range groups {
		out = append(out, key)
	}
	slices.Sort(out)
	return out
}
func set(ids []string) map[string]bool {
	out := make(map[string]bool, len(ids))
	for _, id := range ids {
		out[id] = true
	}
	return out
}
func pythonSum(values []float64) float64 {
	hi, lo := 0., 0.
	for _, x := range values {
		t := hi + x
		if math.Abs(hi) >= math.Abs(x) {
			lo += (hi - t) + x
		} else {
			lo += (x - t) + hi
		}
		hi = t
	}
	return hi + lo
}
func (s *Service) rankCategories() {
	usable := []string{}
	for _, cat := range s.data.CategoryOrder {
		if len(s.graph.ByCategory(cat)) >= 4 {
			usable = append(usable, cat)
		}
	}
	ent := map[string]float64{}
	for i, a := range usable {
		am := s.graph.ByCategory(a)
		for _, b := range usable[i+1:] {
			bm := s.graph.ByCategory(b)
			bs := set(bm)
			cross := 0
			for _, id := range am {
				for _, n := range s.graph.NeighborIDs(id) {
					if bs[n] {
						cross++
					}
				}
			}
			ent[a+"\000"+b] = float64(cross) / math.Pow(float64(len(am)*len(bm)), .5)
		}
	}
	for a := 0; a < len(usable); a++ {
		for b := a + 1; b < len(usable); b++ {
			for c := b + 1; c < len(usable); c++ {
				for d := c + 1; d < len(usable); d++ {
					cats := []string{usable[a], usable[b], usable[c], usable[d]}
					slices.Sort(cats)
					values := []float64{}
					for i, x := range cats {
						for _, y := range cats[i+1:] {
							values = append(values, ent[x+"\000"+y])
						}
					}
					s.ranked = append(s.ranked, rankedSet{cats, pythonSum(values)})
				}
			}
		}
	}
	sort.Slice(s.ranked, func(i, j int) bool {
		a, b := s.ranked[i], s.ranked[j]
		if a.entanglement != b.entanglement {
			return a.entanglement < b.entanglement
		}
		return slices.Compare(a.categories, b.categories) < 0
	})
}
func (s *Service) buildBoard(rng *pyrandom.Random, difficulty string) (*gameSession, *Error) {
	// Curated games never need the fallback's complete category ranking.
	s.rankOnce.Do(s.rankCategories)
	n := len(s.ranked)
	if n == 0 {
		return nil, fail(503, "Nu există suficiente categorii pentru un joc.")
	}
	pool := s.ranked
	third := max(1, n/3)
	if difficulty == "usor" {
		pool = pool[:third]
	} else if difficulty == "greu" {
		pool = pool[n-third:]
	}
	cats := pool[rng.RandBelow(len(pool))].categories
	all := map[string]bool{}
	members := map[string]map[string]bool{}
	for _, cat := range cats {
		members[cat] = set(s.graph.ByCategory(cat))
		for id := range members[cat] {
			all[id] = true
		}
	}
	groups := map[string][]string{}
	order := []string{}
	for _, cat := range cats {
		ids := s.graph.ByCategory(cat)
		own := members[cat]
		fair := []string{}
		for _, id := range ids {
			ownCount, foreignCount := 0, 0
			for _, neighbor := range s.graph.NeighborIDs(id) {
				if own[neighbor] && neighbor != id {
					ownCount++
				}
				if all[neighbor] && !own[neighbor] {
					foreignCount++
				}
			}
			if foreignCount-ownCount <= 0 {
				fair = append(fair, id)
			}
		}
		choices := slices.Clone(ids)
		if len(fair) >= 4 {
			choices = fair
		}
		if difficulty == "usor" || difficulty == "greu" {
			sort.Slice(choices, func(i, j int) bool {
				a, b := s.graph.Salience(choices[i]), s.graph.Salience(choices[j])
				if a == b {
					return choices[i] < choices[j]
				}
				if difficulty == "usor" {
					return a > b
				}
				return a < b
			})
		} else {
			rng.Shuffle(len(choices), func(i, j int) { choices[i], choices[j] = choices[j], choices[i] })
		}
		picked := slices.Clone(choices[:4])
		slices.Sort(picked)
		groups[cat] = picked
		order = append(order, picked...)
	}
	rng.Shuffle(len(order), func(i, j int) { order[i], order[j] = order[j], order[i] })
	return newSession(groups, order, difficulty, "", "", nil), nil
}
func (s *Service) quality(g *gameSession) (bool, int) {
	owner := map[string]string{}
	count := 0
	for cat, ids := range g.groups {
		for _, id := range ids {
			count++
			owner[id] = cat
		}
	}
	if count != 16 || len(owner) != 16 {
		return false, 1000000
	}
	residual := 0
	for id, own := range owner {
		ownCount := 0
		foreign := map[string]int{}
		for _, n := range s.graph.NeighborIDs(id) {
			if cat, ok := owner[n]; ok {
				if cat == own && n != id {
					ownCount++
				} else if cat != own {
					foreign[cat]++
				}
			}
		}
		worst := 0
		for _, n := range foreign {
			worst = max(worst, n)
		}
		if worst > ownCount {
			return false, 1000000
		}
		if worst == ownCount && ownCount > 0 {
			residual++
		}
	}
	return true, residual
}
func (s *Service) pickBoard(rng *pyrandom.Random, difficulty string) (*gameSession, *Error) {
	var best *gameSession
	bestResidual := 1000000
	for range 16 {
		candidate, err := s.buildBoard(rng, difficulty)
		if err != nil {
			return nil, err
		}
		ok, residual := s.quality(candidate)
		if ok && residual == 0 {
			return candidate, nil
		}
		if ok && residual < bestResidual {
			best, bestResidual = candidate, residual
		}
	}
	if best != nil {
		return best, nil
	}
	return nil, fail(503, "Nu am putut genera o tablă validă; reîncearcă.")
}
func curated(item *content.PackItem, daily, category string) (*gameSession, *Error) {
	groups := map[string][]string{}
	raw, ok := item.Payload["groups"].(map[string]any)
	if !ok {
		return nil, fail(503, "Tabla Conexiuni este invalidă.")
	}
	for cat, value := range raw {
		ids, ok := stringsList(value)
		if !ok || len(ids) != 4 {
			return nil, fail(503, "Tabla Conexiuni este invalidă.")
		}
		groups[cat] = ids
	}
	order, ok := stringsList(item.Payload["order"])
	if !ok || len(groups) != 4 || len(order) != 16 {
		return nil, fail(503, "Tabla Conexiuni este invalidă.")
	}
	labels := map[string]string{}
	rawLabels, ok := item.Payload["group_labels"].(map[string]any)
	if !ok {
		return nil, fail(503, "Tabla Conexiuni este invalidă.")
	}
	for cat, value := range rawLabels {
		label, ok := value.(string)
		if !ok {
			return nil, fail(503, "Tabla Conexiuni este invalidă.")
		}
		labels[cat] = label
	}
	return newSession(groups, order, item.Difficulty, daily, category, labels), nil
}
func (s *Service) Create(seed *big.Int, daily, category, difficulty string) (map[string]any, *Error) {
	if !slices.Contains([]string{"usor", "normal", "greu"}, difficulty) {
		difficulty = "normal"
	}
	if category != "" {
		if _, ok := s.data.CategoryLabels[category]; !ok {
			return nil, fail(400, "Categorie necunoscută.")
		}
	}
	var rng *pyrandom.Random
	var item *content.PackItem
	opts := pack.PickOptions{Category: category, Difficulty: difficulty}
	if daily != "" {
		rng = pyrandom.NewUint64(catalog.DailySeed(daily, "conexiuni"))
		item = s.pack.PickDaily("conexiuni", daily, opts)
	} else {
		rng = pyrandom.New(seed)
		item = s.pack.PickSeeded("conexiuni", rng, opts)
	}
	var game *gameSession
	var err *Error
	if item != nil {
		game, err = curated(item, daily, category)
	} else if category != "" {
		return nil, fail(503, "Nu există încă jocuri pentru această categorie.")
	} else {
		game, err = s.pickBoard(rng, difficulty)
		if err == nil {
			game.daily = daily
		}
	}
	if err != nil {
		return nil, err
	}
	body := s.state("", game)
	id, createErr := s.store.Create(game)
	if createErr != nil {
		return nil, fail(503, "Prea multe jocuri active. Încearcă din nou.")
	}
	body["game_id"] = id
	return body, nil
}
func (s *Service) concept(id string) map[string]string {
	label, ok := s.data.Labels[id]
	if !ok {
		label = id
	}
	return map[string]string{"id": id, "label": label}
}
func (s *Service) label(g *gameSession, cat string) string {
	if label, ok := g.labels[cat]; ok {
		return label
	}
	if label, ok := s.data.CategoryLabels[cat]; ok {
		return label
	}
	return cat
}
func (s *Service) group(g *gameSession, cat string) map[string]any {
	tiles := make([]map[string]string, len(g.groups[cat]))
	for i, id := range g.groups[cat] {
		tiles[i] = s.concept(id)
	}
	return map[string]any{"key": cat, "label": s.label(g, cat), "tiles": tiles}
}
func owner(g *gameSession, id string) string {
	for cat, ids := range g.groups {
		if slices.Contains(ids, id) {
			return cat
		}
	}
	return ""
}
func clueAvailable(g *gameSession) bool {
	return !g.won && !g.lost && g.cluesUsed < 2 && g.mistakes >= 2+g.cluesUsed && len(g.solved) < len(g.groups)
}
func pattern(label string) string {
	var out strings.Builder
	start := true
	for _, c := range label {
		if unicode.IsLetter(c) {
			if start {
				out.WriteRune(unicode.ToUpper(c))
				start = false
			} else {
				out.WriteRune('_')
			}
		} else {
			out.WriteRune(c)
			start = unicode.IsSpace(c) || (c >= 0x1c && c <= 0x1f)
		}
	}
	return out.String()
}

func (s *Service) redaction(label string) string {
	if reviewed, ok := s.data.LabelPatterns[label]; ok {
		return reviewed
	}
	return pattern(label)
}
func (s *Service) share(g *gameSession) string {
	cats := keys(g.groups)
	emoji := []string{"🟩", "🟦", "🟪", "🟧"}
	rows := []string{}
	for _, guess := range g.history {
		row := ""
		for _, id := range guess {
			index := slices.Index(cats, owner(g, id))
			if index < 0 {
				index = 0
			}
			row += emoji[index%4]
		}
		rows = append(rows, row)
	}
	header := "cat_de_roman_esti · Conexiuni · "
	if g.category != "" {
		header += s.data.CategoryLabels[g.category] + " · "
	}
	word := "greșeli"
	if g.mistakes == 1 {
		word = "greșeală"
	}
	header += fmt.Sprintf("%d %s", g.mistakes, word)
	if g.cluesUsed > 0 {
		header += fmt.Sprintf(" · indiciu x%d", g.cluesUsed)
	}
	if g.daily != "" {
		header += " · " + g.daily
	}
	body := "—"
	if len(rows) > 0 {
		body = strings.Join(rows, "\n")
	}
	return header + "\n" + body
}
func (s *Service) state(id string, g *gameSession) map[string]any {
	terminal := g.won || g.lost
	solvedIDs := map[string]bool{}
	for _, category := range g.solved {
		for _, node := range g.groups[category] {
			solvedIDs[node] = true
		}
	}
	tiles := []map[string]string{}
	for _, node := range g.order {
		if terminal || !solvedIDs[node] {
			tiles = append(tiles, s.concept(node))
		}
	}
	solved := make([]map[string]any, len(g.solved))
	for i, cat := range g.solved {
		solved[i] = s.group(g, cat)
	}
	clues := make([]map[string]string, len(g.clues))
	for i, clue := range g.clues {
		clues[i] = map[string]string{"pattern": clue["pattern"], "message": clue["message"]}
	}
	body := map[string]any{"game_id": id, "tiles": tiles, "solved": solved, "solved_count": len(g.solved), "remaining_groups": len(g.groups) - len(g.solved), "lives": g.lives, "mistakes": g.mistakes, "won": g.won, "lost": g.lost, "difficulty": g.difficulty, "clues_used": g.cluesUsed, "clue_available": clueAvailable(g), "clues": clues}
	if g.daily != "" {
		body["daily"] = g.daily
	}
	if g.category != "" {
		body["board_category"] = g.category
	}
	if terminal {
		body["score"] = max(0, 1000-250*g.mistakes-100*g.cluesUsed)
		body["share"] = s.share(g)
		order := slices.Clone(g.solved)
		for _, cat := range keys(g.groups) {
			if !slices.Contains(g.solved, cat) {
				order = append(order, cat)
			}
		}
		solution := make([]map[string]any, len(order))
		for i, cat := range order {
			solution[i] = s.group(g, cat)
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
func (s *Service) Guess(id string, ids []string) (map[string]any, *Error) {
	return s.GuessInput(id, func() ([]string, *Error) { return ids, nil })
}
func (s *Service) GuessInput(id string, validate func() ([]string, *Error)) (map[string]any, *Error) {
	return s.action(id, func(g *gameSession) (map[string]any, *Error) {
		ids, err := validate()
		if err != nil {
			return nil, err
		}
		if g.won || g.lost {
			return nil, fail(400, "Jocul s-a terminat")
		}
		if len(ids) != 4 || len(set(ids)) != 4 {
			return nil, fail(400, "Alege exact 4 concepte distincte")
		}
		for _, node := range ids {
			if !slices.Contains(g.order, node) {
				return nil, fail(400, "Concept care nu e pe tablă")
			}
			if slices.Contains(g.solved, owner(g, node)) {
				return nil, fail(400, "Concept deja rezolvat")
			}
		}
		key := slices.Clone(ids)
		slices.Sort(key)
		for _, previous := range g.history {
			p := slices.Clone(previous)
			slices.Sort(p)
			if slices.Equal(key, p) {
				return nil, fail(409, "Ai încercat deja această combinație.")
			}
		}
		g.history = append(g.history, slices.Clone(ids))
		shared := owner(g, ids[0])
		correct := true
		counts := map[string]int{}
		for _, node := range ids {
			cat := owner(g, node)
			counts[cat]++
			if cat != shared {
				correct = false
			}
		}
		if correct {
			g.solved = append(g.solved, shared)
			g.won = len(g.solved) == 4
			body := s.state(id, g)
			body["ok"], body["correct"], body["category"] = true, true, map[string]string{"key": shared, "label": s.label(g, shared)}
			return body, nil
		}
		g.mistakes++
		g.lives--
		g.lost = g.lives <= 0
		oneAway := false
		for _, n := range counts {
			if n == 3 {
				oneAway = true
			}
		}
		body := s.state(id, g)
		body["ok"], body["correct"], body["one_away"] = true, false, oneAway
		return body, nil
	})
}
func (s *Service) Clue(id string) (map[string]any, *Error) {
	return s.action(id, func(g *gameSession) (map[string]any, *Error) {
		if g.won || g.lost {
			return nil, fail(400, "Jocul s-a terminat")
		}
		if g.cluesUsed >= 2 {
			return nil, fail(400, "Indiciile au fost deja folosite")
		}
		if g.mistakes < 2+g.cluesUsed {
			need := 2 + g.cluesUsed - g.mistakes
			word := "greșeli"
			if need == 1 {
				word = "greșeală"
			}
			return nil, fail(400, fmt.Sprintf("Indiciul apare după încă %d %s.", need, word))
		}
		unsolved := []string{}
		for _, cat := range keys(g.groups) {
			if !slices.Contains(g.solved, cat) {
				unsolved = append(unsolved, cat)
			}
		}
		cat := unsolved[0]
		if len(g.clued) > 0 && len(unsolved) > 1 {
			previous := g.clued[len(g.clued)-1]
			for _, next := range unsolved {
				if next > previous {
					cat = next
					break
				}
			}
		}
		g.clued = append(g.clued, cat)
		redacted := s.redaction(s.label(g, cat))
		clue := map[string]string{"pattern": redacted, "message": "Numele unui grup rămas: " + redacted + " (fiecare _ este o literă lipsă)."}
		g.clues = append(g.clues, clue)
		g.cluesUsed++
		body := s.state(id, g)
		body["ok"] = true
		body["clue"] = map[string]string{"pattern": clue["pattern"], "message": clue["message"]}
		return body, nil
	})
}
