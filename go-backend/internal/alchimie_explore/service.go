// Package alchimie_explore implements the unscored, portable discovery world.
package alchimie_explore

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"sort"
	"unicode/utf8"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/session"
)

type Error = gameapi.Error

const MaxConcepts = 256
const MaxEmptyPairs = 128

type Pair [2]string

func pair(a, b string) Pair {
	if a > b {
		return Pair{b, a}
	}
	return Pair{a, b}
}

type Concept struct {
	ID          string `json:"id"`
	Label       string `json:"label"`
	Description string `json:"description"`
}
type Recipe struct {
	ID          string   `json:"id"`
	Pair        Pair     `json:"pair"`
	Result      string   `json:"result"`
	Explanation string   `json:"explanation"`
	Sources     []string `json:"sources"`
}
type Goal struct {
	ID     string `json:"id"`
	Target string `json:"target"`
	Title  string `json:"title"`
}
type Unlock struct {
	ID       string   `json:"id"`
	After    int      `json:"after_discoveries"`
	Concepts []string `json:"concept_ids"`
	Title    string   `json:"title"`
}
type Mechanics struct {
	Starters []string `json:"starters"`
	Recipes  []struct {
		Pair   Pair   `json:"pair"`
		Result string `json:"result"`
	} `json:"recipes"`
	Unlocks []struct {
		After    int      `json:"after"`
		Concepts []string `json:"concepts"`
	} `json:"unlocks"`
}
type Version struct {
	WorldID   string    `json:"world_id"`
	Hash      string    `json:"recipe_hash"`
	Mechanics Mechanics `json:"mechanics"`
}
type World struct {
	Info struct {
		ID          string   `json:"id"`
		Title       string   `json:"title"`
		Description string   `json:"description"`
		Starters    []string `json:"starter_ids"`
	} `json:"world"`
	Concepts  []Concept `json:"concepts"`
	Recipes   []Recipe  `json:"recipes"`
	Goals     []Goal    `json:"goals"`
	Unlocks   []Unlock  `json:"unlocks"`
	Versions  []Version `json:"compatible_versions"`
	Hash      string    `json:"recipe_hash"`
	Mechanics Mechanics `json:"mechanics"`
	concepts  map[string]Concept
	recipes   map[Pair]Recipe
	goals     map[string]Goal
	versions  map[string]Version
}

func decodeWorld(raw map[string]any) (*World, error) {
	encoded, err := json.Marshal(raw)
	if err != nil {
		return nil, err
	}
	var w World
	if err = json.Unmarshal(encoded, &w); err != nil {
		return nil, err
	}
	if w.Info.ID == "" || len(w.Concepts) < 3 || len(w.Concepts) > 256 || len(w.Recipes) < 2 || len(w.Recipes) > 512 || len(w.Unlocks) > 12 || len(w.Versions) > 16 {
		return nil, fmt.Errorf("invalid bounded discovery world")
	}
	w.concepts = map[string]Concept{}
	w.recipes = map[Pair]Recipe{}
	w.goals = map[string]Goal{}
	w.versions = map[string]Version{}
	for _, c := range w.Concepts {
		if c.ID == "" || c.Label == "" {
			return nil, fmt.Errorf("invalid concept")
		}
		w.concepts[c.ID] = c
	}
	if len(w.concepts) != len(w.Concepts) {
		return nil, fmt.Errorf("duplicate concepts")
	}
	for index, r := range w.Recipes {
		r.Pair = pair(r.Pair[0], r.Pair[1])
		w.Recipes[index] = r
		if r.Pair[0] >= r.Pair[1] || w.concepts[r.Pair[0]].ID == "" || w.concepts[r.Pair[1]].ID == "" || w.concepts[r.Result].ID == "" {
			return nil, fmt.Errorf("invalid recipe")
		}
		w.recipes[r.Pair] = r
	}
	if len(w.recipes) != len(w.Recipes) {
		return nil, fmt.Errorf("duplicate recipes")
	}
	for _, g := range w.Goals {
		w.goals[g.ID] = g
	}
	for _, v := range w.Versions {
		if v.WorldID != w.Info.ID || v.Hash == w.Hash {
			return nil, fmt.Errorf("invalid compatible world identity")
		}
		w.versions[v.Hash] = v
	}
	if len(w.Mechanics.Starters) == 0 {
		w.Mechanics.Starters = append([]string{}, w.Info.Starters...)
		sort.Strings(w.Mechanics.Starters)
		ordered := append([]Recipe{}, w.Recipes...)
		sort.Slice(ordered, func(i, j int) bool { return lessPair(ordered[i].Pair, ordered[j].Pair) })
		for _, r := range ordered {
			w.Mechanics.Recipes = append(w.Mechanics.Recipes, struct {
				Pair   Pair   `json:"pair"`
				Result string `json:"result"`
			}{r.Pair, r.Result})
		}
		for _, u := range w.Unlocks {
			ids := append([]string{}, u.Concepts...)
			sort.Strings(ids)
			w.Mechanics.Unlocks = append(w.Mechanics.Unlocks, struct {
				After    int      `json:"after"`
				Concepts []string `json:"concepts"`
			}{u.After, ids})
		}
		sort.Slice(w.Mechanics.Unlocks, func(i, j int) bool {
			a, b := w.Mechanics.Unlocks[i], w.Mechanics.Unlocks[j]
			if a.After != b.After {
				return a.After < b.After
			}
			return fmt.Sprint(a.Concepts) < fmt.Sprint(b.Concepts)
		})
	}
	// json.Marshal of a struct does not sort fields; a map round-trip supplies Python's canonical key order.
	mechBytes, _ := json.Marshal(w.Mechanics)
	var canonical map[string]any
	_ = json.Unmarshal(mechBytes, &canonical)
	mechBytes, _ = json.Marshal(canonical)
	hash := fmt.Sprintf("%x", sha256.Sum256(mechBytes))
	if w.Hash == "" {
		w.Hash = hash
	} else if w.Hash != hash {
		return nil, fmt.Errorf("mechanics hash mismatch")
	}
	return &w, nil
}
func lessPair(a, b Pair) bool {
	if a[0] != b[0] {
		return a[0] < b[0]
	}
	return a[1] < b[1]
}

type exploreSession struct {
	world               *World
	owned               map[string]*Pair
	order               []string
	discoveries         []Pair
	goal                *string
	unlocked            map[string]bool
	revision, hintStage int
	hintPair            *Pair
	empty               []Pair
}

func fresh(w *World, goal *string) *exploreSession {
	s := &exploreSession{world: w, owned: map[string]*Pair{}, order: []string{}, discoveries: []Pair{}, goal: goal, unlocked: map[string]bool{}, empty: []Pair{}}
	for _, id := range w.Info.Starters {
		s.add(id, nil)
	}
	return s
}
func (s *exploreSession) add(id string, parents *Pair) {
	if _, ok := s.owned[id]; !ok {
		s.order = append(s.order, id)
	}
	s.owned[id] = parents
}
func (s *exploreSession) award() []string {
	out := []string{}
	for _, u := range s.world.Unlocks {
		if !s.unlocked[u.ID] && len(s.discoveries) >= u.After {
			s.unlocked[u.ID] = true
			for _, id := range u.Concepts {
				s.add(id, nil)
				out = append(out, id)
			}
		}
	}
	return out
}
func (s *exploreSession) craft(p Pair) (string, bool, []string, *Error) {
	if _, ok := s.owned[p[0]]; !ok {
		return "", false, nil, &Error{Status: 400, Detail: "Alege două ingrediente diferite din colecția ta."}
	}
	if _, ok := s.owned[p[1]]; !ok || p[0] == p[1] {
		return "", false, nil, &Error{Status: 400, Detail: "Alege două ingrediente diferite din colecția ta."}
	}
	r, ok := s.world.recipes[p]
	if !ok {
		return "", false, []string{}, nil
	}
	if _, ok = s.owned[r.Result]; ok {
		return r.Result, false, []string{}, nil
	}
	if len(s.discoveries) >= MaxConcepts {
		return "", false, nil, &Error{Status: 409, Detail: "Colecția a atins limita acestei lumi."}
	}
	s.add(r.Result, &p)
	s.discoveries = append(s.discoveries, p)
	s.hintPair = nil
	s.hintStage = 0
	return r.Result, true, s.award(), nil
}
func (s *exploreSession) concept(id string) map[string]any {
	return map[string]any{"id": id, "label": s.world.concepts[id].Label}
}
func (s *exploreSession) hint() any {
	if s.hintStage == 0 {
		return nil
	}
	if s.hintPair == nil {
		return map[string]any{"stage": "complete", "message": "Ai descoperit tot în această lume!", "output": nil, "pair": nil}
	}
	r := s.world.recipes[*s.hintPair]
	label := s.world.concepts[r.Result].Label
	var p any
	stage, msg := "output", fmt.Sprintf("Poți descoperi «%s» cu ingredientele pe care le ai.", label)
	if s.hintStage >= 2 {
		a, b := s.concept(s.hintPair[0]), s.concept(s.hintPair[1])
		p = []any{a, b}
		stage = "pair"
		msg = fmt.Sprintf("Încearcă %s + %s.", a["label"], b["label"])
	}
	return map[string]any{"stage": stage, "message": msg, "output": map[string]any{"label": label}, "pair": p}
}
func (s *exploreSession) state(id string) map[string]any {
	inv := []any{}
	for _, cid := range s.order {
		c := s.world.concepts[cid]
		p := s.owned[cid]
		uses, remaining, ready := 0, 0, false
		for _, r := range s.world.Recipes {
			if r.Pair[0] != cid && r.Pair[1] != cid {
				continue
			}
			uses++
			if _, owned := s.owned[r.Result]; !owned {
				remaining++
				_, a := s.owned[r.Pair[0]]
				_, b := s.owned[r.Pair[1]]
				ready = ready || (a && b)
			}
		}
		status := "depleted"
		if uses == 0 {
			status = "final"
		} else if remaining > 0 {
			status = "active"
		}
		var parents, explanation any
		sources := []string{}
		if p != nil {
			parents = []any{s.concept(p[0]), s.concept(p[1])}
			if r, ok := s.world.recipes[*p]; ok {
				explanation = r.Explanation
				sources = r.Sources
			}
		} else {
			for _, u := range s.world.Unlocks {
				for _, x := range u.Concepts {
					if x == cid {
						explanation = u.Title
						break
					}
				}
				if explanation != nil {
					break
				}
			}
		}
		inv = append(inv, map[string]any{"id": cid, "label": c.Label, "description": c.Description, "parents": parents, "explanation": explanation, "sources": sources, "status": status, "ready": ready})
	}
	goals, unlocked, hashes := []any{}, []any{}, []string{}
	for _, v := range s.world.Versions {
		hashes = append(hashes, v.Hash)
	}
	for _, g := range s.world.Goals {
		_, done := s.owned[g.Target]
		var target any
		if done {
			target = g.Target
		}
		goals = append(goals, map[string]any{"id": g.ID, "title": g.Title, "label": s.world.concepts[g.Target].Label, "completed": done, "target_id": target})
	}
	var next *Unlock
	for i := range s.world.Unlocks {
		u := &s.world.Unlocks[i]
		if s.unlocked[u.ID] {
			unlocked = append(unlocked, map[string]any{"id": u.ID, "title": u.Title, "after_discoveries": u.After})
		} else if next == nil || u.After < next.After {
			next = u
		}
	}
	var nextValue any
	if next != nil {
		nextValue = map[string]any{"title": next.Title, "after_discoveries": next.After, "remaining": next.After - len(s.discoveries)}
	}
	return map[string]any{"game_id": id, "revision": s.revision, "mode": "explore", "compatible_recipe_hashes": hashes, "empty_pairs": s.empty, "world": map[string]any{"id": s.world.Info.ID, "title": s.world.Info.Title, "description": s.world.Info.Description, "total_concepts": len(s.world.Concepts), "total_recipes": len(s.world.Recipes)}, "inventory": inv, "discovered_count": len(s.discoveries), "seed_count": len(s.world.Info.Starters), "complete": len(s.owned) == len(s.world.Concepts), "goal_id": s.goal, "goals": goals, "hint": s.hint(), "unlocked": unlocked, "next_unlock": nextValue, "progress": map[string]any{"world_id": s.world.Info.ID, "recipe_hash": s.world.Hash, "discoveries": s.discoveries}}
}
func (s *exploreSession) useful() *Pair {
	ancestors := map[string]bool{}
	if s.goal != nil {
		target := s.world.goals[*s.goal].Target
		if _, ok := s.owned[target]; !ok {
			ancestors[target] = true
			for {
				n := len(ancestors)
				for _, r := range s.world.Recipes {
					if ancestors[r.Result] {
						ancestors[r.Pair[0]] = true
						ancestors[r.Pair[1]] = true
					}
				}
				if n == len(ancestors) {
					break
				}
			}
		}
	}
	var chosen *Recipe
	for i := range s.world.Recipes {
		r := &s.world.Recipes[i]
		_, a := s.owned[r.Pair[0]]
		_, b := s.owned[r.Pair[1]]
		_, known := s.owned[r.Result]
		if !a || !b || known {
			continue
		}
		if chosen == nil || (ancestors[r.Result] && !ancestors[chosen.Result]) || (ancestors[r.Result] == ancestors[chosen.Result] && r.ID < chosen.ID) {
			chosen = r
		}
	}
	if chosen == nil {
		return nil
	}
	p := chosen.Pair
	return &p
}
func restore(w *World, progress map[string]any, goal *string) (*exploreSession, *Error) {
	s := fresh(w, goal)
	if progress == nil {
		return s, nil
	}
	wid, _ := progress["world_id"].(string)
	hash, _ := progress["recipe_hash"].(string)
	v, old := w.versions[hash]
	if wid != w.Info.ID || (hash != w.Hash && !old) {
		return nil, &Error{Status: 409, Detail: "Colecția aparține altei versiuni. Salvarea rămâne păstrată."}
	}
	mech := w.Mechanics
	if old {
		mech = v.Mechanics
	}
	recipes := map[Pair]string{}
	for _, r := range mech.Recipes {
		recipes[r.Pair] = r.Result
	}
	owned := map[string]bool{}
	for _, x := range mech.Starters {
		owned[x] = true
	}
	crafted := map[string]bool{}
	validated := []Pair{}
	raw, ok := progress["discoveries"].([]any)
	if !ok {
		return nil, &Error{Status: 400, Detail: "Colecția salvată conține o combinație invalidă."}
	}
	for _, x := range raw {
		xs, ok := x.([]any)
		if !ok || len(xs) != 2 {
			return nil, &Error{Status: 400, Detail: "Colecția salvată conține o combinație invalidă."}
		}
		a, oka := xs[0].(string)
		b, okb := xs[1].(string)
		if !oka || !okb {
			return nil, &Error{Status: 400, Detail: "Colecția salvată conține o combinație invalidă."}
		}
		p := pair(a, b)
		if a == b || !owned[a] || !owned[b] {
			return nil, &Error{Status: 400, Detail: "Colecția salvată folosește ingrediente încă nedescoperite."}
		}
		result, ok := recipes[p]
		if !ok {
			return nil, &Error{Status: 400, Detail: "Colecția salvată conține o rețetă necunoscută."}
		}
		if !owned[result] {
			owned[result] = true
			crafted[result] = true
			validated = append(validated, p)
			for _, u := range mech.Unlocks {
				if len(crafted) >= u.After {
					for _, x := range u.Concepts {
						owned[x] = true
					}
				}
			}
		}
	}
	for _, p := range validated {
		if _, _, _, err := s.craft(p); err != nil {
			return nil, err
		}
	}
	for x := range owned {
		if _, ok := s.owned[x]; !ok {
			return nil, &Error{Status: 409, Detail: "Colecția nu poate fi actualizată. Salvarea rămâne păstrată."}
		}
	}
	return s, nil
}

type Service struct {
	world     *World
	loadError error
	store     *session.Store[*exploreSession]
}

func New(data *content.Content) *Service {
	w, err := decodeWorld(data.DiscoveryWorld)
	return &Service{world: w, loadError: err, store: session.New[*exploreSession]()}
}
func (s *Service) Create(progress map[string]any, goal *string) (map[string]any, *Error) {
	if s.loadError != nil {
		return nil, &Error{Status: 503, Detail: "Lumea de explorat nu este disponibilă momentan."}
	}
	if goal != nil {
		if _, ok := s.world.goals[*goal]; !ok {
			return nil, &Error{Status: 400, Detail: "Obiectiv necunoscut."}
		}
	}
	game, err := restore(s.world, progress, goal)
	if err != nil {
		return nil, err
	}
	id, e := s.store.Create(game)
	if e != nil {
		return nil, &Error{Status: 503, Detail: "Prea multe explorări active. Încearcă din nou."}
	}
	return game.state(id), nil
}
func (s *Service) transact(id string, fn func(*exploreSession) (map[string]any, *Error)) (map[string]any, *Error) {
	var value map[string]any
	var result *Error
	found, _ := s.store.Transaction(id, func(game *exploreSession) error { value, result = fn(game); return nil })
	if !found {
		return nil, &Error{Status: 404, Detail: "Explorarea a expirat. Reia colecția salvată."}
	}
	return value, result
}
func (s *Service) Get(id string) (map[string]any, *Error) {
	return s.transact(id, func(g *exploreSession) (map[string]any, *Error) { return g.state(id), nil })
}
func (s *Service) Combine(id, a, b string) (map[string]any, *Error) {
	return s.CombineInput(id, func() (string, string, *Error) { return a, b, nil })
}
func (s *Service) CombineInput(id string, validate func() (string, string, *Error)) (map[string]any, *Error) {
	return s.transact(id, func(g *exploreSession) (map[string]any, *Error) {
		a, b, err := validate()
		if err != nil {
			return nil, err
		}
		result, new, supplies, err := g.craft(pair(a, b))
		if err != nil {
			return nil, err
		}
		g.revision++
		msg := "Perechea nu are încă o rețetă. Încearcă alt ingredient; nu pierzi nimic."
		if result == "" {
			p := pair(a, b)
			seen := false
			for _, x := range g.empty {
				seen = seen || x == p
			}
			if !seen {
				if len(g.empty) >= MaxEmptyPairs {
					g.empty = g.empty[1:]
				}
				g.empty = append(g.empty, p)
			}
		} else if new {
			msg = "Ai descoperit " + g.world.concepts[result].Label + "!"
		} else {
			msg = "Ai deja " + g.world.concepts[result].Label + " în colecție."
		}
		if len(supplies) > 0 {
			msg += " Ai primit provizii noi în cămară!"
		}
		p := g.state(id)
		discovered, supplied := []any{}, []any{}
		var resultValue any
		if result != "" {
			resultValue = g.concept(result)
			if new {
				discovered = append(discovered, resultValue)
			}
		}
		for _, x := range supplies {
			supplied = append(supplied, g.concept(x))
		}
		p["message"] = msg
		p["discovered"] = discovered
		p["result"] = resultValue
		p["supplied"] = supplied
		p["already_known"] = result != "" && !new
		return p, nil
	})
}
func (s *Service) Hint(id string) (map[string]any, *Error) {
	return s.transact(id, func(g *exploreSession) (map[string]any, *Error) {
		if g.hintPair == nil {
			g.hintPair = g.useful()
		}
		if g.hintStage < 2 {
			g.hintStage++
		}
		g.revision++
		return g.state(id), nil
	})
}
func (s *Service) Goal(id string, goal *string) (map[string]any, *Error) {
	return s.GoalInput(id, func() (*string, *Error) { return goal, nil })
}
func (s *Service) GoalInput(id string, validate func() (*string, *Error)) (map[string]any, *Error) {
	return s.transact(id, func(g *exploreSession) (map[string]any, *Error) {
		goal, err := validate()
		if err != nil {
			return nil, err
		}
		if goal != nil {
			if _, ok := g.world.goals[*goal]; !ok {
				return nil, &Error{Status: 400, Detail: "Obiectiv necunoscut."}
			}
		}
		g.goal = goal
		g.hintPair = nil
		g.hintStage = 0
		g.revision++
		return g.state(id), nil
	})
}
func ValidIdentifier(x any) bool {
	s, ok := x.(string)
	return ok && utf8.RuneCountInString(s) >= 1 && utf8.RuneCountInString(s) <= 160
}
