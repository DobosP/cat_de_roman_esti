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
	seeds                                             []string
	target, difficulty, daily, category               string
	owned                                             map[string]*Pair
	order                                             []string
	moves, fruitlessStreak, fruitlessTotal, hintsUsed int
	earnedHint                                        map[string]any
	projection                                        *Projection
	attempted                                         map[Pair]bool
}

func newGame(seeds []string, target string, p *Projection, difficulty, daily, category string) *gameSession {
	g := &gameSession{seeds: append([]string{}, seeds...), target: target, difficulty: difficulty, daily: daily, category: category, owned: map[string]*Pair{}, order: []string{}, projection: p, attempted: map[Pair]bool{}}
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
	if difficulty != "usor" && difficulty != "greu" && difficulty != "normal" {
		difficulty = "normal"
	}
	if category != "" && s.data.CategoryLabels[category] == "" {
		return nil, &Error{Status: 400, Detail: "Categorie necunoscută."}
	}
	rng := pyrandom.New(seed)
	opts := pack.PickOptions{Category: category, Difficulty: difficulty}
	var item *content.PackItem
	if daily != "" {
		rng = pyrandom.NewUint64(catalog.DailySeed(daily, "alchimie"))
		item = s.pack.PickDaily("alchimie", daily, opts)
	} else {
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
	} else {
		g, err = s.mine(rng, difficulty, daily, category)
		if err != nil {
			return nil, err
		}
	}
	id, e := s.store.Create(g)
	if e != nil {
		return nil, &Error{Status: 503, Detail: "Prea multe jocuri active. Încearcă din nou."}
	}
	return s.state(id, g), nil
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
	hintStage := "output"
	if g.hintsUsed > 0 {
		hintStage = "pair"
	}
	p := map[string]any{"game_id": id, "target": map[string]any{"id": targetID, "label": s.graph.Label(g.target), "description": s.graph.Description(g.target), "revealed": g.won()}, "inventory": inv, "inventory_summary": map[string]any{"active": active, "depleted": len(inv) - active, "total": len(inv)}, "discovered_count": max(0, len(g.order)-len(g.seeds)), "seed_count": len(g.seeds), "moves": g.moves, "attempted_count": len(g.attempted), "difficulty": g.difficulty, "target_depth": g.projection.Par, "won": g.won(), "hints_used": g.hintsUsed, "hint_stage": hintStage, "hint_available": !g.won() && g.fruitlessStreak >= 2, "recipe_summary": map[string]any{"pairs": len(g.projection.Recipes), "routes": len(g.projection.Routes), "max_results": maxResults}}
	if g.earnedHint != nil {
		p["earned_hint"] = g.earnedHint
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
		if g.moves-g.fruitlessTotal <= g.projection.Par && g.hintsUsed == 0 {
			medal = "✨"
		}
		share := fmt.Sprintf("%s\n⚗️ %d %s · %d pct %s", header, g.moves, noun, g.score(), medal)
		if g.hintsUsed > 0 {
			share += fmt.Sprintf("\n💡 x%d", g.hintsUsed)
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
	return s.transact(id, func(g *gameSession) (map[string]any, *Error) { return s.state(id, g), nil })
}
func (s *Service) Combine(id, a, b string) (map[string]any, *Error) {
	return s.CombineInput(id, func() (string, string, *Error) { return a, b, nil })
}

// Validation runs after lookup and under the same atomic action as Django.
func (s *Service) CombineInput(id string, validate func() (string, string, *Error)) (map[string]any, *Error) {
	return s.transact(id, func(g *gameSession) (map[string]any, *Error) {
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
		if len(g.attempted) >= MaxAttemptedPairs {
			return nil, &Error{Status: 409, Detail: "Limita de experimente a jocului a fost atinsă."}
		}
		g.earnedHint = nil
		g.attempted[key] = true
		g.moves++
		discovered := diff(g.projection.Recipes[key], sortedUnique(g.order))
		parents := Pair{a, b}
		for _, x := range discovered {
			g.add(x, &parents)
		}
		if len(discovered) > 0 {
			g.fruitlessStreak = 0
		} else {
			g.fruitlessStreak++
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
				message = "Ai deja rezultatul: " + strings.Join(names, ", ") + ". Fără penalizare."
			} else {
				message = "Perechea nu are o rețetă în această rundă. Fără penalizare."
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
	})
}
func (s *Service) Hint(id string) (map[string]any, *Error) {
	return s.transact(id, func(g *gameSession) (map[string]any, *Error) {
		if g.won() {
			return nil, &Error{Status: 400, Detail: "Jocul s-a terminat deja."}
		}
		if g.fruitlessStreak < 2 {
			need := 2 - g.fruitlessStreak
			noun := "combinații"
			if need == 1 {
				noun = "combinație"
			}
			return nil, &Error{Status: 400, Detail: fmt.Sprintf("Mai încearcă %d %s înainte de un indiciu.", need, noun)}
		}
		plan := MinimumPlan(g.order, g.target, g.projection.Recipes, MaxActions)
		g.fruitlessStreak = 0
		if len(plan) == 0 {
			g.earnedHint = nil
			p := s.state(id, g)
			p["hint"] = nil
			p["hint_kind"] = "none"
			p["hint_output"] = nil
			p["message"] = "Niciun indiciu disponibil acum."
			return p, nil
		}
		g.hintsUsed++
		key := plan[0]
		p := s.state(id, g)
		p["hint"] = nil
		p["hint_output"] = nil
		if g.hintsUsed == 1 {
			outputs := []string{}
			for _, x := range g.projection.Recipes[key] {
				if x != g.target {
					if _, ok := g.owned[x]; !ok {
						outputs = append(outputs, x)
					}
				}
			}
			if len(outputs) > 0 {
				label := s.graph.Label(outputs[0])
				p["hint_kind"] = "output"
				p["hint_output"] = map[string]any{"label": label}
				p["message"] = "Indiciu: caută mai întâi «" + label + "»."
			} else {
				p["hint_kind"] = "category"
				if g.category != "" {
					p["message"] = "Indiciu: ținta e aproape. Rămâi în tema " + s.data.CategoryLabels[g.category] + "."
				} else {
					p["message"] = "Indiciu: ținta e la un pas; caută o pereche utilă."
				}
			}
		} else {
			p["hint"] = []any{s.concept(key[0]), s.concept(key[1])}
			p["hint_kind"] = "pair"
			p["message"] = "Indiciu: combină " + s.graph.Label(key[0]) + " + " + s.graph.Label(key[1]) + "."
		}
		g.earnedHint = map[string]any{}
		for _, key := range []string{"hint", "hint_kind", "hint_output", "message"} {
			g.earnedHint[key] = p[key]
		}
		p["earned_hint"] = g.earnedHint
		return p, nil
	})
}
func (s *Service) Reset(id string) (map[string]any, *Error) {
	return s.transact(id, func(g *gameSession) (map[string]any, *Error) {
		g.owned = map[string]*Pair{}
		g.order = []string{}
		g.moves = 0
		g.fruitlessStreak = 0
		g.fruitlessTotal = 0
		g.hintsUsed = 0
		g.earnedHint = nil
		g.attempted = map[Pair]bool{}
		for _, x := range g.seeds {
			g.add(x, nil)
		}
		return s.state(id, g), nil
	})
}

func pyStrip(text string) string {
	return strings.TrimFunc(text, func(r rune) bool {
		return r >= 9 && r <= 13 || r >= 28 && r <= 32 || r == 0x85 || r == 0xa0 || r == 0x1680 || r >= 0x2000 && r <= 0x200a || r == 0x2028 || r == 0x2029 || r == 0x202f || r == 0x205f || r == 0x3000
	})
}
