package lant

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
	"sort"
	"strings"
	"sync"
)

type game struct {
	Start, Target, Difficulty, Category string
	Daily                               *string
	Optimal                             int
	Chain                               []string
	Won                                 bool
	HintRequests, NonImproving          int
	Earned                              map[string]any
}

func (v *game) current() string { return v.Chain[len(v.Chain)-1] }
func (v *game) moves() int      { return len(v.Chain) - 1 }

type profileKey struct {
	Start, Target string
	Optimal       int
}
type profiles [2][3]int
type cache struct {
	mu     sync.Mutex
	values map[profileKey]profiles
	fifo   []profileKey
}
type Service struct {
	c        *content.Content
	g        *graph.Service
	pack     *pack.Pack
	store    *session.Store[*game]
	profiles *cache
}

func New(c *content.Content) *Service {
	return &Service{c: c, g: graph.New(c), pack: pack.New(c), store: session.New[*game](), profiles: c.Shared("lant-profiles", func() any { return &cache{values: map[profileKey]profiles{}} }).(*cache)}
}
func fail(status int, message string) *gameapi.Error {
	return &gameapi.Error{Status: status, Detail: message}
}
func contains(ids []string, id string) bool {
	for _, v := range ids {
		if v == id {
			return true
		}
	}
	return false
}
func clone(value any) any {
	switch v := value.(type) {
	case map[string]any:
		out := map[string]any{}
		for k, x := range v {
			out[k] = clone(x)
		}
		return out
	case []map[string]any:
		out := []map[string]any{}
		for _, x := range v {
			out = append(out, clone(x).(map[string]any))
		}
		return out
	case []string:
		return append([]string{}, v...)
	default:
		return value
	}
}
func (s *Service) action(id string, fn func(*game) (map[string]any, *gameapi.Error)) (map[string]any, *gameapi.Error) {
	var out map[string]any
	var err *gameapi.Error
	found, _ := s.store.Transaction(id, func(v *game) error { out, err = fn(v); return nil })
	if !found {
		return nil, fail(404, "Joc inexistent")
	}
	return out, err
}
func (s *Service) concept(id string) map[string]any {
	return map[string]any{"id": id, "label": s.g.Label(id)}
}
func (s *Service) caption(a, b string) string { return s.c.LantCaptions[a+"\x00"+b] }
func (s *Service) short(a, b string) string {
	label := s.caption(a, b)
	if label == "" {
		label = "legătură directă"
	}
	chars := []rune(label)
	if len(chars) <= 34 {
		return label
	}
	head := string(chars[:33])
	if at := strings.LastIndex(head, " "); at >= 0 {
		head = head[:at]
	}
	if head == "" {
		head = string(chars[:33])
	}
	return head + "…"
}
func (s *Service) hub(id string) float64 {
	return math.Min(1.25, float64(max(0, s.g.Degree(id)-20))*.08)
}
func (s *Service) quality(current, id string) float64 {
	strength := 0.
	if e := s.g.Link(current, id); e != nil {
		strength = e.Strength
	}
	return -(strength*4 + s.g.Salience(id)*1.5 - s.hub(id))
}
func (s *Service) qualityLess(current, a, b string) bool {
	aa, bb := s.quality(current, a), s.quality(current, b)
	if aa != bb {
		return aa < bb
	}
	al, bl := s.g.Normalize(s.g.Label(a)), s.g.Normalize(s.g.Label(b))
	if al != bl {
		return al < bl
	}
	return a < b
}
func (s *Service) routeProfiles(start, target string, optimal int) profiles {
	key := profileKey{start, target, optimal}
	s.profiles.mu.Lock()
	cached, ok := s.profiles.values[key]
	s.profiles.mu.Unlock()
	if ok {
		return cached
	}
	from, to := s.g.DistancesFrom(start), s.g.DistancesTo(target)
	layers := [2]map[int]int{{}, {}}
	budget := optimal + 2
	for id, a := range from {
		b, ok := to[id]
		if !ok {
			continue
		}
		if a+b == optimal {
			layers[0][a]++
		}
		if a+b <= budget {
			layers[1][a]++
		}
	}
	var result profiles
	for i := 0; i < 2; i++ {
		first := 0
		for _, id := range s.g.NeighborIDs(start) {
			d, ok := to[id]
			if ok && ((i == 0 && d == optimal-1) || (i == 1 && d+1 <= budget)) {
				first++
			}
		}
		width, total := 1, 0
		if optimal > 1 {
			width = math.MaxInt
			for layer := 1; layer < optimal; layer++ {
				count := layers[i][layer]
				width = min(width, count)
				total += count
			}
		}
		result[i] = [3]int{first, width, total}
	}
	s.profiles.mu.Lock()
	defer s.profiles.mu.Unlock()
	if old, ok := s.profiles.values[key]; ok {
		return old
	}
	if len(s.profiles.fifo) >= 512 {
		delete(s.profiles.values, s.profiles.fifo[0])
		s.profiles.fifo = s.profiles.fifo[1:]
	}
	s.profiles.fifo = append(s.profiles.fifo, key)
	s.profiles.values[key] = result
	return result
}
func (s *Service) distinct(current string, ids []string, to map[string]int) []string {
	unique := map[string]bool{}
	rows := []string{}
	for _, id := range ids {
		if !unique[id] {
			unique[id] = true
			rows = append(rows, id)
		}
	}
	sort.Slice(rows, func(i, j int) bool {
		a, b := rows[i], rows[j]
		ad, ok := to[a]
		if !ok {
			ad = 1000000
		}
		bd, ok := to[b]
		if !ok {
			bd = 1000000
		}
		if ad != bd {
			return ad < bd
		}
		return s.qualityLess(current, a, b)
	})
	out := []string{}
	seen := map[string]bool{}
	for _, id := range rows {
		key := s.g.Normalize(s.g.Label(id))
		if key != "" && !seen[key] {
			seen[key] = true
			out = append(out, id)
		}
	}
	return out
}
func (s *Service) shortest(v *game, to map[string]int) []string {
	d, ok := to[v.current()]
	if !ok {
		return []string{}
	}
	ids := []string{}
	for _, id := range s.g.NeighborIDs(v.current()) {
		n, ok := to[id]
		if !contains(v.Chain, id) && ok && n == d-1 {
			ids = append(ids, id)
		}
	}
	return s.distinct(v.current(), ids, to)
}
func (s *Service) near(v *game, to map[string]int) []string {
	budget := v.Optimal + 2 - v.moves()
	out := []string{}
	for _, id := range s.g.NeighborIDs(v.current()) {
		d, ok := to[id]
		if !contains(v.Chain, id) && ok && d+1 <= budget {
			out = append(out, id)
		}
	}
	return out
}
func (s *Service) choice(current, id string) map[string]any {
	return map[string]any{"label": s.g.Label(id), "relation": s.short(current, id)}
}
func (s *Service) choiceIDs(v *game) []string {
	if v.Won || v.moves() >= 64 {
		return []string{}
	}
	cur := v.current()
	to := s.g.DistancesTo(v.Target)
	legal := []string{}
	for _, id := range s.g.NeighborIDs(cur) {
		if _, ok := to[id]; ok && !contains(v.Chain, id) {
			legal = append(legal, id)
		}
	}
	safe := s.distinct(cur, legal, to)
	corridor := s.near(v, to)
	on, detour := []string{}, []string{}
	for _, id := range safe {
		if contains(corridor, id) {
			on = append(on, id)
		} else {
			detour = append(detour, id)
		}
	}
	for _, ids := range [][]string{on, detour} {
		sort.Slice(ids, func(i, j int) bool { return s.qualityLess(cur, ids[i], ids[j]) })
	}
	shortest := []string{}
	remaining, ok := to[cur]
	for _, id := range on {
		if ok && to[id] == remaining-1 {
			shortest = append(shortest, id)
		}
	}
	chosen := append([]string{}, shortest[:min(2, len(shortest))]...)
	for _, id := range on {
		if len(chosen) >= 3 {
			break
		}
		if !contains(chosen, id) {
			chosen = append(chosen, id)
		}
	}
	chosen = append(chosen, detour[:min(6-len(chosen), len(detour))]...)
	sort.Slice(chosen, func(i, j int) bool {
		a, b := chosen[i], chosen[j]
		aa, bb := s.g.Normalize(s.g.Label(a)), s.g.Normalize(s.g.Label(b))
		if aa != bb {
			return aa < bb
		}
		return a < b
	})
	return chosen
}
func (s *Service) choices(v *game) []map[string]any {
	out := []map[string]any{}
	for _, id := range s.choiceIDs(v) {
		out = append(out, s.choice(v.current(), id))
	}
	return out
}
func (s *Service) path(v *game) []map[string]any {
	out := []map[string]any{}
	for i, id := range v.Chain {
		step := s.concept(id)
		if i > 0 {
			step["relation"] = s.caption(v.Chain[i-1], id)
		}
		out = append(out, step)
	}
	return out
}
func score(v *game) int {
	return max(100, int(math.RoundToEven(1000*float64(v.Optimal)/float64(max(max(v.moves(), 1), v.Optimal)))))
}
func (s *Service) share(v *game) string {
	header := "cat_de_roman_esti · Lanțul Cuvintelor"
	if v.Category != "" {
		header += " · " + s.c.CategoryLabels[v.Category]
	}
	daily := ""
	if v.Daily != nil {
		daily = *v.Daily
	}
	return fmt.Sprintf("%s\n🔗 %d/%d salturi\n%s", header, v.moves(), v.Optimal, daily)
}
func (s *Service) state(id string, v *game) map[string]any {
	out := map[string]any{"game_id": id, "start": s.concept(v.Start), "target": map[string]any{"id": v.Target, "label": s.g.Label(v.Target), "description": s.g.Description(v.Target)}, "current": s.concept(v.current()), "path": s.path(v), "moves": v.moves(), "optimal": v.Optimal, "won": v.Won, "difficulty": v.Difficulty, "choices": s.choices(v), "backtrack_recommended": v.Difficulty == "usor" && v.NonImproving >= 2}
	if v.Earned != nil {
		out["earned_hint"] = clone(v.Earned)
	}
	if v.Daily != nil {
		out["daily"] = *v.Daily
	}
	if v.Category != "" {
		out["board_category"] = v.Category
	}
	if v.Won {
		out["score"] = score(v)
		out["share"] = s.share(v)
	}
	return out
}
func (s *Service) wide(item *content.PackItem) bool {
	p := s.routeProfiles(item.Payload["start"].(string), item.Payload["target"].(string), int(item.Payload["optimal"].(float64)))[1]
	return p[0] >= 3 && p[1] >= 3
}
func (s *Service) curated(rng *pyrandom.Random, daily *string, category, difficulty string) *content.PackItem {
	o := pack.PickOptions{Category: category, Difficulty: difficulty}
	var picked *content.PackItem
	if daily != nil {
		picked = s.pack.PickDaily("lant", *daily, o)
	} else {
		picked = s.pack.PickSeeded("lant", rng, o)
	}
	if picked == nil || difficulty != "usor" || s.wide(picked) {
		return picked
	}
	if daily == nil && rng.RandBelow(4) == 0 {
		return picked
	}
	pool := s.pack.Pool("lant", o)
	if s.c.PackRanked {
		eligible := []*content.PackItem{}
		for _, p := range pool {
			if p.PilotEligible {
				eligible = append(eligible, p)
			}
		}
		pool = eligible
	}
	minimum := min(3, len(pool))
	if daily != nil && category == "" {
		minimum = 8
	}
	wide := []*content.PackItem{}
	for _, p := range pool {
		if s.wide(p) {
			wide = append(wide, p)
		}
	}
	if len(wide) >= max(1, minimum) {
		pool = wide
	}
	narrowed := pack.FromItems(pool, s.c.PackRanked)
	if daily != nil {
		return narrowed.PickDaily("lant", *daily, o)
	}
	return narrowed.PickSeeded("lant", rng, o)
}

type pair struct {
	start, target string
	optimal       int
	score         float64
}

func (s *Service) mine(rng *pyrandom.Random, category, difficulty string) (pair, *gameapi.Error) {
	lo, hi := 3, 4
	if difficulty == "usor" {
		lo, hi = 2, 3
	} else if difficulty == "greu" {
		lo, hi = 4, 6
	}
	pool := s.g.AllIDs()
	if category != "" {
		pool = s.g.ByCategory(category)
	}
	candidates := []string{}
	for _, id := range pool {
		if s.g.Degree(id) >= 2 {
			candidates = append(candidates, id)
		}
	}
	if len(candidates) == 0 && category == "" {
		for _, id := range pool {
			if s.g.Degree(id) >= 1 {
				candidates = append(candidates, id)
			}
		}
	}
	if len(candidates) == 0 {
		if category != "" {
			return pair{}, fail(503, "Nu există încă jocuri pentru această categorie.")
		}
		return pair{}, fail(503, "Graful nu are noduri jucabile.")
	}
	if difficulty == "usor" {
		salient := []string{}
		for _, id := range candidates {
			if s.g.Salience(id) >= .6 {
				salient = append(salient, id)
			}
		}
		if len(salient) >= 8 {
			candidates = salient
		}
	}
	weight := 9.
	if difficulty == "usor" {
		weight = 16
	} else if difficulty == "greu" {
		weight = 2
	}
	var bestGood, bestAny, fallback *pair
	goodCount := 0
	for attempt := 0; attempt < 140; attempt++ {
		start := candidates[rng.RandBelow(len(candidates))]
		dist, order := s.g.DistancesFromOrdered(start)
		reachable := []string{}
		for _, id := range order {
			d := dist[id]
			if d >= lo && d <= hi && s.g.Degree(id) >= 2 && contains(candidates, id) {
				reachable = append(reachable, id)
			}
		}
		if len(reachable) == 0 {
			continue
		}
		rng.ShuffleStrings(reachable)
		for _, target := range reachable[:min(24, len(reachable))] {
			optimal := dist[target]
			p := s.routeProfiles(start, target, optimal)
			salience := (s.g.Salience(start) + s.g.Salience(target)) / 2
			value := pair{start, target, optimal, float64(p[0][1]*10+p[0][0]*3+p[0][2]) + salience*weight - (s.hub(start) + s.hub(target))}
			if fallback == nil {
				copy := value
				fallback = &copy
			}
			if bestAny == nil || value.score > bestAny.score {
				copy := value
				bestAny = &copy
			}
			wide := difficulty != "usor" || p[1][0] >= 3 && p[1][1] >= 3
			if p[0][0] >= 2 && p[0][1] >= 2 && wide {
				if bestGood == nil || value.score > bestGood.score {
					copy := value
					bestGood = &copy
				}
				goodCount++
			}
		}
		if goodCount >= 6 {
			break
		}
	}
	for _, p := range []*pair{bestGood, bestAny, fallback} {
		if p != nil {
			return *p, nil
		}
	}
	if category != "" {
		return pair{}, fail(503, "Nu există încă jocuri pentru această categorie.")
	}
	return pair{}, fail(503, "Nu am putut genera un lanț valid; reîncearcă.")
}
func (s *Service) Create(seed *big.Int, difficulty string, daily *string, category string) (map[string]any, *gameapi.Error) {
	if difficulty != "usor" && difficulty != "greu" {
		difficulty = "normal"
	}
	if category != "" && s.c.CategoryLabels[category] == "" {
		return nil, fail(400, "Categorie necunoscută.")
	}
	if daily != nil {
		seed = new(big.Int).SetUint64(catalog.DailySeed(*daily, "lant"))
	}
	rng := pyrandom.New(seed)
	picked := s.curated(rng, daily, category, difficulty)
	var p pair
	if picked != nil {
		p = pair{start: picked.Payload["start"].(string), target: picked.Payload["target"].(string), optimal: int(picked.Payload["optimal"].(float64))}
	} else {
		var err *gameapi.Error
		p, err = s.mine(rng, category, difficulty)
		if err != nil {
			return nil, err
		}
	}
	v := &game{Start: p.start, Target: p.target, Optimal: p.optimal, Difficulty: difficulty, Daily: daily, Category: category, Chain: []string{p.start}}
	out := s.state("", v)
	id, err := s.store.Create(v)
	if err != nil {
		return nil, fail(503, "Prea multe jocuri active. Încearcă din nou.")
	}
	out["game_id"] = id
	return out, nil
}
func (s *Service) Get(id string) (map[string]any, *gameapi.Error) {
	return s.action(id, func(v *game) (map[string]any, *gameapi.Error) { return s.state(id, v), nil })
}
func (s *Service) resolveNeighbor(text, current, target string) string {
	primary := s.g.Resolve(text)
	key := s.g.Normalize(text)
	if key == "" {
		return primary
	}
	legal := []string{}
	for _, id := range s.g.AllIDs() {
		if id != current && s.g.Normalize(s.g.Label(id)) == key && s.g.Link(current, id) != nil {
			legal = append(legal, id)
		}
	}
	if len(legal) == 0 {
		return primary
	}
	if len(legal) == 1 {
		return legal[0]
	}
	to := s.g.DistancesTo(target)
	return s.distinct(current, legal, to)[0]
}
func (s *Service) MoveInput(id string, validate func() (string, *gameapi.Error)) (map[string]any, *gameapi.Error) {
	return s.action(id, func(v *game) (map[string]any, *gameapi.Error) {
		text, err := validate()
		if err != nil {
			return nil, err
		}
		if v.Won {
			out := s.state(id, v)
			out["ok"] = true
			return out, nil
		}
		if v.moves() >= 64 {
			return map[string]any{"ok": false, "last_error": "Limită atinsă — folosește Înapoi."}, nil
		}
		if strings.TrimFunc(text, pySpace) == "" {
			return map[string]any{"ok": false, "last_error": "Scrie un concept"}, nil
		}
		if s.g.ReviewedUnresolved(text) {
			return map[string]any{"ok": false, "last_error": "Nu cunosc acest concept", "suggestions": []string{}}, nil
		}
		prev := v.current()
		key := s.g.Normalize(text)
		visible := []string{}
		for _, node := range s.choiceIDs(v) {
			if s.g.Normalize(s.g.Label(node)) == key {
				visible = append(visible, node)
			}
		}
		guess := ""
		if len(visible) == 1 {
			guess = visible[0]
		} else {
			guess = s.resolveNeighbor(text, prev, v.Target)
		}
		corrected := false
		if guess == "" {
			guess = s.g.ResolveFuzzy(text)
			corrected = guess != ""
		}
		if guess == "" {
			suggestions := s.g.Suggest(text, 3)
			message := "Nu cunosc acest concept"
			if len(suggestions) > 0 {
				message += ". Poate căutai: " + suggestions[0] + "?"
			}
			return map[string]any{"ok": false, "last_error": message, "suggestions": suggestions}, nil
		}
		understood := ""
		if corrected {
			understood = "Am înțeles: " + s.g.Label(guess) + ". "
		}
		if guess == prev {
			return map[string]any{"ok": false, "last_error": understood + "Ești deja aici."}, nil
		}
		if s.g.Link(prev, guess) == nil {
			return map[string]any{"ok": false, "last_error": understood + s.g.DisplayLabel(guess) + " nu are o legătură directă cu " + s.g.Label(prev) + ". Alege un cuvânt din listă sau cere un indiciu."}, nil
		}
		v.Chain = append(v.Chain, guess)
		v.Earned = nil
		v.Won = guess == v.Target
		notes := []string{}
		if corrected {
			notes = append(notes, "Am înțeles: "+s.g.Label(guess)+".")
		}
		to := s.g.DistancesTo(v.Target)
		before, beforeOK := to[prev]
		after, afterOK := to[guess]
		dead := !v.Won && !afterOK
		if dead && v.Difficulty != "usor" {
			notes = append(notes, "Atenție: fundătură — de aici ținta nu mai e accesibilă.")
		}
		var progress map[string]any
		if v.Difficulty == "usor" || v.Difficulty == "normal" {
			kind := "farther"
			if v.Won {
				kind = "won"
			} else if dead {
				kind = "dead_end"
			} else if !beforeOK || after < before {
				kind = "closer"
			} else if after == before {
				kind = "lateral"
			}
			messages := map[string]string{"closer": "Mai aproape de țintă.", "lateral": "Tot cam la aceeași distanță.", "farther": "Te-ai îndepărtat puțin.", "dead_end": "Fundătură — folosește Înapoi.", "won": "Ai ajuns la țintă!"}
			if kind == "closer" || kind == "won" {
				v.NonImproving = 0
			} else {
				v.NonImproving = min(2, v.NonImproving+1)
			}
			progress = map[string]any{"kind": kind, "message": messages[kind]}
		} else {
			v.NonImproving = 0
		}
		out := map[string]any{"ok": true, "current": s.concept(guess), "relation": s.caption(prev, guess), "path": s.path(v), "moves": v.moves(), "won": v.Won, "choices": s.choices(v), "backtrack_recommended": v.Difficulty == "usor" && v.NonImproving >= 2}
		if progress != nil {
			out["progress"] = progress
		}
		if dead {
			out["dead_end"] = true
		}
		if len(notes) > 0 {
			out["message"] = strings.Join(notes, " ")
		}
		if v.Won {
			out["score"] = score(v)
			out["share"] = s.share(v)
		}
		return out, nil
	})
}
func (s *Service) Move(id, text string) (map[string]any, *gameapi.Error) {
	return s.MoveInput(id, func() (string, *gameapi.Error) { return text, nil })
}
func (s *Service) Undo(id string) (map[string]any, *gameapi.Error) {
	return s.action(id, func(v *game) (map[string]any, *gameapi.Error) {
		if !v.Won {
			if len(v.Chain) > 1 {
				v.Chain = v.Chain[:len(v.Chain)-1]
				v.Earned = nil
				v.Won = v.current() == v.Target
			}
			v.NonImproving = 0
		}
		return s.state(id, v), nil
	})
}
func (s *Service) Hint(id string) (map[string]any, *gameapi.Error) {
	return s.action(id, func(v *game) (map[string]any, *gameapi.Error) {
		earn := func(payload map[string]any) (map[string]any, *gameapi.Error) {
			if !v.Won {
				v.Earned = clone(payload).(map[string]any)
			}
			return payload, nil
		}
		if v.Won {
			return earn(map[string]any{"hint": nil, "message": "Ai ajuns deja la țintă."})
		}
		if v.moves() >= 64 {
			return earn(map[string]any{"hint": nil, "stage": "backtrack", "message": "Limită atinsă — folosește Înapoi."})
		}
		v.HintRequests = min(3, v.HintRequests+1)
		cur := v.current()
		to := s.g.DistancesTo(v.Target)
		remaining, ok := to[cur]
		if !ok {
			for i := len(v.Chain) - 1; i >= 0; i-- {
				node := v.Chain[i]
				if _, ok := to[node]; node != cur && ok {
					return earn(map[string]any{"hint": nil, "stage": "backtrack", "message": "Fundătură — folosește Înapoi până la " + s.g.Label(node) + "."})
				}
			}
			return earn(map[string]any{"hint": nil, "message": "Nicio scurtătură de aici — încearcă să revii cu Înapoi."})
		}
		shortest := s.shortest(v, to)
		forward := shortest
		if len(forward) == 0 {
			legal := []string{}
			for _, node := range s.g.NeighborIDs(cur) {
				if _, ok := to[node]; !contains(v.Chain, node) && ok {
					legal = append(legal, node)
				}
			}
			forward = s.distinct(cur, legal, to)
		}
		if len(forward) == 0 {
			prior := map[string]bool{}
			for _, node := range s.g.NeighborIDs(cur) {
				if n, ok := to[node]; contains(v.Chain[:len(v.Chain)-1], node) && ok && n == remaining-1 {
					prior[node] = true
				}
			}
			for i := len(v.Chain) - 2; i >= 0; i-- {
				node := v.Chain[i]
				if prior[node] {
					return earn(map[string]any{"hint": nil, "stage": "backtrack", "remaining": remaining, "message": "Drumul continuă printr-un pas deja vizitat. Folosește Înapoi până la " + s.g.Label(node) + "."})
				}
			}
		}
		if len(forward) > 0 {
			best := forward[0]
			common := map[string]any{"hint": nil, "remaining": 1 + to[best], "alternatives": len(forward)}
			if v.HintRequests == 1 {
				relation := s.short(cur, best)
				if relation != "legătură directă" {
					common["stage"] = "direction"
					common["relation"] = relation
					common["message"] = "Direcție: caută o legătură „" + relation + "”."
					return earn(common)
				}
				v.HintRequests = 2
			}
			if v.HintRequests == 2 {
				near := forward
				if len(shortest) > 0 {
					near = s.distinct(cur, append(append([]string{}, shortest...), s.near(v, to)...), to)
				}
				choices := []map[string]any{}
				labels := []string{}
				for _, node := range near[:min(2, len(near))] {
					choice := s.choice(cur, node)
					choices = append(choices, choice)
					labels = append(labels, s.g.Label(node))
				}
				lead := "Variante utile: "
				if len(choices) == 1 {
					lead = "O variantă utilă: "
				}
				common["stage"] = "alternatives"
				common["alternatives_choices"] = choices
				common["alternatives_labels"] = labels
				common["message"] = lead + strings.Join(labels, ", ") + "."
				return earn(common)
			}
			common["stage"] = "hop"
			common["hint"] = s.concept(best)
			common["relation"] = s.short(cur, best)
			common["message"] = "Un salt bun: " + s.g.Label(best) + "."
			return earn(common)
		}
		return earn(map[string]any{"hint": nil, "message": "Niciun indiciu disponibil."})
	})
}
func pySpace(c rune) bool {
	return c >= 9 && c <= 13 || c >= 0x1c && c <= 0x20 || c == 0x85 || c == 0xa0 || c == 0x1680 || c >= 0x2000 && c <= 0x200a || c == 0x2028 || c == 0x2029 || c == 0x202f || c == 0x205f || c == 0x3000
}
