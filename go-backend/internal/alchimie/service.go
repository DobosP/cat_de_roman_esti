// Package alchimie owns authoritative challenge sessions and private recipe books.
package alchimie

import (
	"fmt"
	"math/big"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pack"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/session"
)

type Error = gameapi.Error
type gameSession struct {
	boardObservation                    gameapi.TerminalObservation
	curatedID                           string
	seeds                               []string
	target, difficulty, daily, category string
	owned                               map[string]*Pair
	order                               []string
	moves, fruitlessTotal, hintsUsed    int
	hintLevel, paidHints                int
	hintPair                            *Pair
	hintPairKnown                       bool
	earnedHint                          *hint
	projection                          *Projection
	attempted, lifetimePairs            map[Pair]bool
}

type hint struct {
	level int
	pair  Pair
	label string
}

func newGame(seeds []string, target string, p *Projection, difficulty, daily, category string) *gameSession {
	g := &gameSession{seeds: append([]string{}, seeds...), target: target, difficulty: difficulty, daily: daily, category: category, owned: map[string]*Pair{}, order: []string{}, projection: p, attempted: map[Pair]bool{}, lifetimePairs: map[Pair]bool{}}
	for _, id := range seeds {
		g.add(id, nil)
	}
	return g
}
func (g *gameSession) add(id string, p *Pair) {
	if _, ok := g.owned[id]; !ok {
		g.owned[id] = p
		g.order = append(g.order, id)
	}
}
func (g *gameSession) won() bool { _, ok := g.owned[g.target]; return ok }
func (g *gameSession) steps() int {
	return max(0, len(g.lifetimePairs)-g.projection.Par) + g.paidHints
}
func (g *gameSession) score() int {
	return max(100, 1000-120*max(0, g.moves-g.fruitlessTotal-g.projection.Par)-150*g.hintsUsed)
}

type Service struct {
	data  *content.Content
	graph *graph.Service
	pack  *pack.Pack
	store *session.Store[*gameSession]
	cache *projectionCache
}

func New(data *content.Content) *Service {
	return &Service{data: data, graph: graph.New(data), pack: pack.New(data), store: session.New[*gameSession](), cache: newCache()}
}
func (s *Service) Create(seed *big.Int, daily, category, difficulty string) (map[string]any, *Error) {
	return s.CreateWithExclusions(seed, daily, category, difficulty, nil)
}

func (s *Service) CreateWithExclusions(seed *big.Int, daily, category, difficulty string, extraExcludeIDs map[string]bool) (map[string]any, *Error) {
	if difficulty != "usor" && difficulty != "greu" && difficulty != "normal" {
		difficulty = "normal"
	}
	if category != "" && s.data.CategoryLabels[category] == "" {
		return nil, &Error{Status: 400, Detail: "Categorie necunoscută."}
	}
	if daily != "" {
		difficulty, category = "usor", ""
	}
	rng := pyrandom.New(seed)
	opts := pack.PickOptions{Category: category, Difficulty: difficulty}
	var item *content.PackItem
	if daily != "" {
		rng = pyrandom.NewUint64(catalog.DailySeed(daily, "alchimie"))
		item = s.pack.PickDaily("alchimie", daily, opts)
	} else {
		opts.ExcludeIDs = extraExcludeIDs
		item = s.pack.PickSeeded("alchimie", rng, opts)
	}
	var g *gameSession
	var err *Error
	if item != nil {
		seeds := []string{}
		for _, id := range item.Payload["seeds"].([]any) {
			seeds = append(seeds, id.(string))
		}
		target := item.Payload["target"].(string)
		p := s.projection(seeds, target, item.Category)
		par := int(item.Payload["target_depth"].(float64))
		if p == nil || p.Par != par {
			return nil, &Error{Status: 503, Detail: "Jocul ales nu are o proiecție de rețete validă."}
		}
		g = newGame(seeds, target, p, difficulty, daily, item.Category)
		g.curatedID = item.ID
	} else {
		g, err = s.mine(rng, difficulty, daily, category)
		if err != nil {
			return nil, err
		}
	}
	p := s.state("", g)
	id, e := s.store.Create(g)
	if e != nil {
		return nil, &Error{Status: 503, Detail: "Prea multe jocuri active. Încearcă din nou."}
	}
	p["game_id"] = id
	return p, nil
}

// BoardTerminal observes a server-terminal reviewed daily once and returns its
// anonymous outcome for subsequent comparisons.
func (s *Service) BoardTerminal(id string, onFirst func(gameapi.TerminalRound)) (gameapi.TerminalRound, bool) {
	return gameapi.ObserveBoardTerminal(s.store, id, onFirst, (*gameSession).boardTerminal)
}

func (g *gameSession) boardTerminal() (gameapi.TerminalRound, *gameapi.TerminalObservation) {
	if !g.won() {
		return gameapi.TerminalRound{}, nil
	}
	return gameapi.TerminalRound{BoardID: g.curatedID, Day: g.daily, Steps: g.steps(), Outcome: gameapi.TerminalWin}, &g.boardObservation
}

func (s *Service) Progress(id string) (curatedID string, finished, won bool, score int, found bool) {
	score = -1
	found, _ = s.store.Transaction(id, func(v *gameSession) error {
		curatedID = v.curatedID
		finished = v.won()
		won = finished
		if won {
			score = v.score()
		}
		return nil
	})
	return
}
func (s *Service) concept(id string) map[string]any {
	return map[string]any{"id": id, "label": s.graph.Label(id)}
}
func (s *Service) state(id string, g *gameSession) map[string]any {
	inv := []any{}
	owned := sortedUnique(g.order)
	recent := map[string]bool{}
	for _, x := range g.order[max(0, len(g.order)-8):] {
		recent[x] = true
	}
	useful, ready := map[string]bool{}, map[string]bool{}
	for p, outputs := range g.projection.Recipes {
		if len(diff(outputs, owned)) == 0 {
			continue
		}
		for _, x := range p {
			if has(owned, x) {
				useful[x] = true
			}
		}
		if has(owned, p[0]) && has(owned, p[1]) {
			ready[p[0]] = true
			ready[p[1]] = true
		}
	}
	active := 0
	for _, x := range g.order {
		p := g.owned[x]
		var parents any
		links := []any{}
		if p != nil {
			parents = []any{s.concept(p[0]), s.concept(p[1])}
			for _, parent := range sortedUnique([]string{p[0], p[1]}) {
				if parent == x || !has(owned, parent) {
					continue
				}
				e := s.graph.Link(parent, x)
				if e == nil || e.IsDistractor || strings.TrimSpace(e.LabelRO) == "" || !((e.Src == parent && e.Dst == x) || (e.Src == x && e.Dst == parent)) {
					continue
				}
				links = append(links, map[string]any{"source": s.concept(e.Src), "target": s.concept(e.Dst), "label": e.LabelRO})
			}
		}
		if useful[x] {
			active++
		}
		inv = append(inv, map[string]any{"id": x, "label": s.graph.Label(x), "parents": parents, "links": links, "recent": recent[x], "useful": useful[x], "ready": ready[x], "depleted": !useful[x]})
	}
	var targetID any
	if g.won() {
		targetID = g.target
	}
	maxResults := 0
	for _, outputs := range g.projection.Recipes {
		maxResults = max(maxResults, len(outputs))
	}
	hints := s.hintLevels(g)
	hintStage := "pair"
	if len(hints) > 0 && hints[0] == 1 {
		hintStage = "output"
	}
	p := map[string]any{"game_id": id, "target": map[string]any{"id": targetID, "label": s.graph.Label(g.target), "description": s.graph.Description(g.target), "revealed": g.won()}, "inventory": inv, "inventory_summary": map[string]any{"active": active, "depleted": len(inv) - active, "total": len(inv)}, "discovered_count": max(0, len(g.order)-len(g.seeds)), "seed_count": len(g.seeds), "moves": g.moves, "attempted_count": len(g.attempted), "difficulty": g.difficulty, "target_depth": g.projection.Par, "won": g.won(), "hints_used": g.hintsUsed, "hint_stage": hintStage, "hint_available": len(hints) > 0, "steps": g.steps(), "perfect": g.won() && g.steps() == 0, "hints_left": len(hints), "hint_level": g.hintLevel, "recipe_summary": map[string]any{"pairs": len(g.projection.Recipes), "routes": len(g.projection.Routes), "max_results": maxResults}}
	if g.earnedHint != nil {
		p["earned_hint"] = s.hintPayload(*g.earnedHint)
	}
	if g.daily != "" {
		p["daily"] = g.daily
	}
	if g.category != "" {
		p["board_category"] = g.category
	}
	if g.won() {
		p["score"] = g.score()
		header := "cat_de_roman_esti · Alchimie"
		if g.category != "" {
			header += " · " + s.data.CategoryLabels[g.category]
		}
		noun, medal := "combinații", "⚗️"
		if g.moves == 1 {
			noun = "combinație"
		}
		if g.steps() == 0 {
			medal = "✨"
		}
		stepNoun := "pași"
		if g.steps() == 1 {
			stepNoun = "pas"
		}
		share := fmt.Sprintf("%s\n⚗️ %d %s · %d %s %s", header, g.moves, noun, g.steps(), stepNoun, medal)
		if g.paidHints > 0 {
			share += fmt.Sprintf("\n💡 x%d", g.paidHints)
		}
		if g.daily != "" {
			share += "\n" + g.daily
		}
		p["share"] = share
	}
	return p
}
func (s *Service) transact(id string, fn func(*gameSession) (map[string]any, *Error)) (map[string]any, *Error) {
	var value map[string]any
	var result *Error
	found, _ := s.store.Transaction(id, func(g *gameSession) error { value, result = fn(g); return nil })
	if !found {
		return nil, &Error{Status: 404, Detail: "Joc inexistent."}
	}
	return value, result
}
func (s *Service) Get(id string) (map[string]any, *Error) {
	return s.GetWithTerminal(id, nil)
}

func (s *Service) GetWithTerminal(id string, onTerminal gameapi.TerminalResponse) (map[string]any, *Error) {
	return s.transact(id, gameapi.WithTerminalResponse(onTerminal, (*gameSession).boardTerminal, func(g *gameSession) (map[string]any, *Error) { return s.state(id, g), nil }))
}
func (s *Service) Combine(id, a, b string) (map[string]any, *Error) {
	return s.CombineInput(id, func() (string, string, *Error) { return a, b, nil })
}

// Validation runs after lookup and under the same atomic action as Django.
func (s *Service) CombineInput(id string, validate func() (string, string, *Error)) (map[string]any, *Error) {
	return s.CombineInputWithTerminal(id, validate, nil)
}

func (s *Service) CombineInputWithTerminal(id string, validate func() (string, string, *Error), onTerminal gameapi.TerminalResponse) (map[string]any, *Error) {
	return s.transact(id, gameapi.WithTerminalResponse(onTerminal, (*gameSession).boardTerminal, func(g *gameSession) (map[string]any, *Error) {
		a, b, err := validate()
		if err != nil {
			return nil, err
		}
		a, b = pyStrip(a), pyStrip(b)
		key := pair(a, b)
		if g.won() {
			p := s.state(id, g)
			p["discovered"] = []any{}
			p["already_tried"] = a != "" && b != "" && a != b && g.attempted[key]
			p["message"] = "Jocul s-a terminat — ai obținut deja ținta."
			return p, nil
		}
		if _, ok := g.owned[a]; !ok {
			return nil, &Error{Status: 400, Detail: "Ambele concepte trebuie să fie în inventar."}
		}
		if _, ok := g.owned[b]; !ok {
			return nil, &Error{Status: 400, Detail: "Ambele concepte trebuie să fie în inventar."}
		}
		if a == b {
			return nil, &Error{Status: 400, Detail: "Alege două concepte diferite."}
		}
		if g.attempted[key] {
			p := s.state(id, g)
			p["discovered"] = []any{}
			p["already_tried"] = true
			p["message"] = "Deja încercată · fără cost. Schimbă un ingredient."
			return p, nil
		}
		if !g.lifetimePairs[key] && len(g.lifetimePairs) >= MaxAttemptedPairs {
			return nil, &Error{Status: 409, Detail: "Limita de experimente a jocului a fost atinsă."}
		}
		g.earnedHint = nil
		g.attempted[key] = true
		g.lifetimePairs[key] = true
		g.moves++
		discovered := diff(g.projection.Recipes[key], sortedUnique(g.order))
		parents := Pair{a, b}
		for _, x := range discovered {
			g.add(x, &parents)
		}
		if len(discovered) > 0 {
			g.hintPairKnown = false
		} else {
			g.fruitlessTotal++
		}
		message := ""
		if len(discovered) == 0 {
			known := g.projection.Recipes[key]
			if len(known) > 0 {
				names := []string{}
				for _, x := range known {
					names = append(names, s.graph.Label(x))
				}
				message = "Ai deja rezultatul: " + strings.Join(names, ", ") + "."
			} else {
				message = "Perechea nu are o rețetă în această rundă."
			}
			if g.fruitlessTotal >= 4 {
				whispers := []string{"Încearcă perechi din aceeași temă.", "Combină un element descoperit cu unul de start.", "Indiciul te poate debloca."}
				message += " " + whispers[(g.fruitlessTotal-4)%3]
			}
		} else if has(discovered, g.target) {
			message = "Ai descoperit ținta: " + s.graph.Label(g.target) + "!"
		} else if len(discovered) == 1 {
			message = "Ai descoperit: " + s.graph.Label(discovered[0]) + "."
		} else {
			names := []string{}
			for _, x := range discovered {
				names = append(names, s.graph.Label(x))
			}
			message = fmt.Sprintf("Ai descoperit %d concepte: %s.", len(discovered), strings.Join(names, ", "))
		}
		p := s.state(id, g)
		out := []any{}
		for _, x := range discovered {
			out = append(out, s.concept(x))
		}
		p["discovered"] = out
		p["already_tried"] = false
		p["message"] = message
		return p, nil
	}))
}
func (s *Service) hintPayload(cue hint) map[string]any {
	out := map[string]any{"hint": nil, "hint_output": nil}
	switch cue.level {
	case 1:
		out["hint_kind"] = "output"
		out["hint_output"] = map[string]any{"label": cue.label}
		out["message"] = "Indiciu: caută mai întâi «" + cue.label + "»."
	case 2:
		out["hint_kind"] = "category"
		out["hint_ingredient"] = s.concept(cue.pair[0])
		out["message"] = "Indiciu: încearcă cu " + s.graph.Label(cue.pair[0]) + "."
	case 3:
		out["hint"] = []any{s.concept(cue.pair[0]), s.concept(cue.pair[1])}
		out["hint_kind"] = "pair"
		out["message"] = "Indiciu: combină " + s.graph.Label(cue.pair[0]) + " + " + s.graph.Label(cue.pair[1]) + "."
	}
	return out
}

func (s *Service) hintOutput(g *gameSession, key Pair) string {
	for _, x := range g.projection.Recipes[key] {
		if _, owned := g.owned[x]; x != g.target && !owned {
			return s.graph.Label(x)
		}
	}
	return ""
}

func (s *Service) hintLevels(g *gameSession) []int {
	if g.won() || g.hintLevel >= 3 {
		return nil
	}
	if !g.hintPairKnown {
		g.hintPair = nil
		if plan := MinimumPlan(g.order, g.target, g.projection.Recipes, MaxActions); len(plan) > 0 {
			g.hintPair = &plan[0]
		}
		g.hintPairKnown = true
	}
	if g.hintPair == nil {
		return nil
	}
	levels := []int{}
	for level := g.hintLevel + 1; level <= 3; level++ {
		if level > 1 || s.hintOutput(g, *g.hintPair) != "" {
			levels = append(levels, level)
		}
	}
	return levels
}

func (s *Service) Hint(id string) (map[string]any, *Error) {
	return s.transact(id, func(g *gameSession) (map[string]any, *Error) {
		if g.won() {
			return nil, &Error{Status: 400, Detail: "Jocul s-a terminat deja."}
		}
		levels := s.hintLevels(g)
		if len(levels) == 0 {
			return nil, &Error{Status: 400, Detail: "Nu mai sunt indicii disponibile."}
		}
		cue := hint{level: levels[0], pair: *g.hintPair}
		if cue.level == 1 {
			cue.label = s.hintOutput(g, cue.pair)
		}
		g.hintLevel = cue.level
		g.hintsUsed++
		g.paidHints++
		g.earnedHint = &cue
		p := s.state(id, g)
		for key, value := range s.hintPayload(cue) {
			p[key] = value
		}
		return p, nil
	})
}
func (s *Service) Reset(id string) (map[string]any, *Error) {
	return s.ResetWithTerminal(id, nil)
}

func (s *Service) ResetWithTerminal(id string, onTerminal gameapi.TerminalResponse) (map[string]any, *Error) {
	return s.transact(id, gameapi.WithTerminalResponse(onTerminal, (*gameSession).boardTerminal, func(g *gameSession) (map[string]any, *Error) {
		g.owned = map[string]*Pair{}
		g.order = []string{}
		g.moves = 0
		g.fruitlessTotal = 0
		g.hintsUsed = 0
		g.earnedHint = nil
		g.hintPairKnown = false
		g.attempted = map[Pair]bool{}
		for _, x := range g.seeds {
			g.add(x, nil)
		}
		return s.state(id, g), nil
	}))
}

func pyStrip(text string) string {
	return strings.TrimFunc(text, func(r rune) bool {
		return r >= 9 && r <= 13 || r >= 28 && r <= 32 || r == 0x85 || r == 0xa0 || r == 0x1680 || r >= 0x2000 && r <= 0x200a || r == 0x2028 || r == 0x2029 || r == 0x202f || r == 0x205f || r == 0x3000
	})
}
