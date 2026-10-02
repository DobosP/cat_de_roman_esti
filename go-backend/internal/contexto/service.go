package contexto

import (
	"crypto/sha256"
	"encoding/json"
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
	"unicode/utf8"
)

type GuessBody struct {
	Text    string
	Confirm *string
}
type projection struct {
	Key         string `json:"key"`
	Label       string `json:"label"`
	PublicID    string `json:"public_id"`
	AnchorID    string `json:"anchor_id"`
	RankPenalty int    `json:"rank_penalty"`
}
type neighborhood struct {
	AnchorID      string   `json:"anchor_id"`
	MinStrength   float64  `json:"min_strength"`
	IncludeDirect bool     `json:"include_direct_neighbors"`
	ExactTargets  []string `json:"exact_target_ids"`
}
type ingredient struct {
	Fallback    string  `json:"fallback_anchor_id"`
	MinStrength float64 `json:"min_strength"`
}
type privateData struct {
	Terms         []projection            `json:"projection_terms"`
	Neighborhoods map[string]neighborhood `json:"neighborhoods"`
	Proxies       map[string]string       `json:"feedback_proxies"`
	Ingredients   map[string]ingredient   `json:"ingredient_policies"`
	Pairs         [][]string              `json:"exact_pairs"`
}
type profile struct {
	Dist      []int32
	Weighted  []float64
	Buckets   map[int][]float64
	Closer    map[int]int
	Reachable int
}
type profileCache struct {
	mu     sync.Mutex
	values map[string]*profile
	fifo   []string
}
type record struct {
	ID, Label, Temperature, Anchor     string
	Distance, Closeness, Rank, Attempt int
}
type warmClue struct {
	Label string
	Rank  int
}
type game struct {
	Target, Difficulty, Category             string
	Daily                                    *string
	Profile                                  *profile
	Guesses                                  map[string]*record
	Order                                    []string
	Attempts                                 int
	Won, GaveUp, CategoryClue, WarmExhausted bool
	Warm                                     *warmClue
	Clues                                    int
}
type Service struct {
	c              *content.Content
	g              *graph.Service
	pack           *pack.Pack
	data           privateData
	projections    map[string]*projection
	projectionKeys []string
	exact          map[string]bool
	profiles       *profileCache
	store          *session.Store[*game]
}

func New(c *content.Content) *Service {
	s := &Service{c: c, g: graph.New(c), pack: pack.New(c), projections: map[string]*projection{}, exact: map[string]bool{}, store: session.New[*game]()}
	raw, _ := json.Marshal(c.ContextoData)
	if err := json.Unmarshal(raw, &s.data); err != nil {
		panic("validated Contexto data malformed")
	}
	for i := range s.data.Terms {
		v := &s.data.Terms[i]
		s.projections[v.Key] = v
		s.projectionKeys = append(s.projectionKeys, v.Key)
	}
	sort.Strings(s.projectionKeys)
	for _, pair := range s.data.Pairs {
		s.exact[pair[0]+"\x00"+pair[1]] = true
	}
	s.profiles = c.Shared("contexto-profiles", func() any { return &profileCache{values: map[string]*profile{}} }).(*profileCache)
	return s
}
func fail(status int, message string) *gameapi.Error {
	return &gameapi.Error{Status: status, Detail: message}
}
func (s *Service) profile(target string) *profile {
	s.profiles.mu.Lock()
	cached := s.profiles.values[target]
	s.profiles.mu.Unlock()
	if cached != nil {
		return cached
	}
	dist := s.g.DistancesToDense(target)
	p := &profile{Dist: dist, Weighted: s.g.WeightedDistancesToDense(target), Buckets: map[int][]float64{}, Closer: map[int]int{}}
	for index, d := range dist {
		if d < 0 {
			continue
		}
		p.Reachable++
		p.Buckets[int(d)] = append(p.Buckets[int(d)], p.Weighted[index])
	}
	keys := []int{}
	for d, bucket := range p.Buckets {
		sort.Float64s(bucket)
		keys = append(keys, d)
	}
	sort.Ints(keys)
	count := 0
	for _, d := range keys {
		p.Closer[d] = count
		count += len(p.Buckets[d])
	}
	s.profiles.mu.Lock()
	defer s.profiles.mu.Unlock()
	if cached = s.profiles.values[target]; cached != nil {
		return cached
	}
	if len(s.profiles.fifo) >= 256 {
		old := s.profiles.fifo[0]
		s.profiles.fifo = s.profiles.fifo[1:]
		delete(s.profiles.values, old)
	}
	s.profiles.fifo = append(s.profiles.fifo, target)
	s.profiles.values[target] = p
	return p
}
func (s *Service) build(target, difficulty string, daily *string, category string) *game {
	return &game{Target: target, Difficulty: difficulty, Daily: daily, Category: category, Profile: s.profile(target), Guesses: map[string]*record{}, Order: []string{}}
}
func (s *Service) Create(seed *big.Int, difficulty string, daily *string, category string) (map[string]any, *gameapi.Error) {
	if difficulty != "usor" && difficulty != "greu" {
		difficulty = "normal"
	}
	if category != "" && s.c.CategoryLabels[category] == "" {
		return nil, fail(400, "Categorie necunoscută.")
	}
	o := pack.PickOptions{Category: category, Difficulty: difficulty, FilteredShelfWeights: true}
	var chosen *content.PackItem
	if daily != nil {
		seed = new(big.Int).SetUint64(catalog.DailySeed(*daily, "contexto"))
		chosen = s.pack.PickDaily("contexto", *daily, o)
	} else {
		chosen = s.pack.PickSeeded("contexto", pyrandom.New(seed), o)
	}
	target := ""
	if chosen != nil {
		target = chosen.Payload["target"].(string)
	} else {
		pool := s.g.AllIDs()
		if difficulty == "usor" {
			high := s.g.BySalience(.6, true)
			if len(high) > 0 {
				pool = high
			}
		} else if difficulty == "greu" {
			pool = s.g.BySalience(0, false)
			if len(pool) > 1 {
				pool = pool[:max(1, len(pool)/2)]
			}
		}
		if category != "" {
			filtered := []string{}
			for _, id := range pool {
				if s.g.Node(id).Category == category {
					filtered = append(filtered, id)
				}
			}
			pool = filtered
			if len(pool) == 0 {
				return nil, fail(503, "Nu există încă jocuri pentru această categorie.")
			}
		}
		rng := pyrandom.New(seed)
		rng.ShuffleStrings(pool)
		fallback := ""
		for _, id := range pool {
			d := s.g.DistancesTo(id)
			responsive := 0
			for _, n := range d {
				if n >= 1 && n <= 5 {
					responsive++
				}
			}
			if len(d) >= 120 && responsive >= 40 {
				target = id
				break
			}
			if fallback == "" && len(d) >= 120 {
				fallback = id
			}
		}
		if target == "" {
			target = fallback
		}
		if target == "" {
			bestSize := -1
			if category == "" {
				pool = s.g.AllIDs()
			}
			for _, id := range pool {
				size := len(s.g.DistancesTo(id))
				if size > bestSize {
					target = id
					bestSize = size
				}
			}
			if category != "" && bestSize < 120 {
				return nil, fail(503, "Nu există încă jocuri pentru această categorie.")
			}
		}
	}
	state := s.build(target, difficulty, daily, category)
	body := s.state("", state)
	id, err := s.store.Create(state)
	if err != nil {
		return nil, fail(503, "Prea multe jocuri active. Încearcă din nou.")
	}
	body["game_id"] = id
	return body, nil
}
func (s *Service) action(id string, fn func(*game) (map[string]any, *gameapi.Error)) (map[string]any, *gameapi.Error) {
	var body map[string]any
	var e *gameapi.Error
	found, _ := s.store.Transaction(id, func(v *game) error { body, e = fn(v); return nil })
	if !found {
		return nil, fail(404, "Joc inexistent")
	}
	return body, e
}
func (s *Service) Get(id string) (map[string]any, *gameapi.Error) {
	return s.action(id, func(v *game) (map[string]any, *gameapi.Error) { return s.state(id, v), nil })
}
func (s *Service) feedbackAnchor(id, target string, allowExact bool) string {
	if id == target {
		return id
	}
	if allowExact && s.exact[id+"\x00"+target] && s.g.Exists(id) && s.g.Exists(target) {
		return target
	}
	if policy, ok := s.data.Ingredients[id]; ok && s.g.Exists(id) {
		e := s.g.Link(id, target)
		if e != nil && e.Relation == "part_of" && e.LabelRO == "ingredient pentru" && e.Strength >= policy.MinStrength {
			return id
		}
		if s.g.Exists(policy.Fallback) {
			return policy.Fallback
		}
	}
	if proxy := s.data.Proxies[id]; proxy != "" && proxy != id && s.g.Exists(proxy) {
		return proxy
	}
	return id
}
func (s *Service) projectionAnchor(term *projection, target string) string {
	if n, ok := s.data.Neighborhoods[term.Key]; ok && s.g.Exists(n.AnchorID) {
		for _, exact := range n.ExactTargets {
			if target == exact && s.g.Exists(target) {
				return target
			}
		}
		if target == n.AnchorID {
			return target
		}
		if n.IncludeDirect {
			e := s.g.Link(n.AnchorID, target)
			if e != nil && e.Strength >= n.MinStrength {
				return n.AnchorID
			}
		}
	}
	return term.AnchorID
}

type feedbackScore struct {
	Anchor    string
	Distance  int
	Reachable bool
	Rank      int
}

func (s *Service) score(v *game, id string, nonwinning bool, penalty int) feedbackScore {
	anchor := s.feedbackAnchor(id, v.Target, !nonwinning)
	index, exists := s.g.Index(anchor)
	d := 0
	ok := exists && v.Profile.Dist[index] >= 0
	if ok {
		d = int(v.Profile.Dist[index])
	}
	rank := v.Profile.Reachable + 1
	if ok {
		rank = v.Profile.Closer[d] + sort.SearchFloat64s(v.Profile.Buckets[d], v.Profile.Weighted[index]) + 1
	}
	if nonwinning || anchor != id {
		if anchor != id {
			penalty = max(penalty, 1)
		}
		rank = max(2, min(v.Profile.Reachable+1, rank+penalty))
		if ok && d == 0 {
			d = 1
		}
	}
	return feedbackScore{anchor, d, ok, rank}
}
func closeness(v *game, r feedbackScore) int {
	if !r.Reachable {
		return 0
	}
	if r.Distance == 0 {
		return 100
	}
	if v.Profile.Reachable <= 1 {
		return 0
	}
	return max(1, min(99, int(math.RoundToEven(100*float64(v.Profile.Reachable-r.Rank)/float64(v.Profile.Reachable-1)))))
}
func temperature(v *game, r feedbackScore) string {
	if !r.Reachable {
		return "Inghetat"
	}
	if r.Distance == 0 {
		return "Gasit"
	}
	pct := float64(r.Rank) / float64(v.Profile.Reachable)
	if r.Distance == 1 || pct <= .005 {
		return "Fierbinte"
	}
	if pct <= .03 {
		return "Cald"
	}
	if pct <= .1 {
		return "Caldut"
	}
	if pct <= .4 {
		return "Rece"
	}
	if pct <= .7 {
		return "Foarte rece"
	}
	return "Inghetat"
}
func recordJSON(r *record) map[string]any {
	return map[string]any{"id": r.ID, "label": r.Label, "distance": r.Distance, "rank": r.Rank, "temperature": r.Temperature, "closeness": r.Closeness, "attempt_number": r.Attempt}
}
func (s *Service) guesses(v *game) []map[string]any {
	records := []*record{}
	for _, r := range v.Guesses {
		records = append(records, r)
	}
	sort.Slice(records, func(i, j int) bool {
		a, b := records[i], records[j]
		if a.Rank != b.Rank {
			return a.Rank < b.Rank
		}
		if a.Distance != b.Distance {
			return a.Distance < b.Distance
		}
		if a.Closeness != b.Closeness {
			return a.Closeness > b.Closeness
		}
		if a.Label != b.Label {
			return a.Label < b.Label
		}
		if a.Attempt != b.Attempt {
			return a.Attempt < b.Attempt
		}
		return a.ID < b.ID
	})
	out := []map[string]any{}
	for _, r := range records {
		if !v.Won && !v.GaveUp && r.ID == v.Target {
			panic("unrevealed target serialization")
		}
		out = append(out, recordJSON(r))
	}
	return out
}
func (s *Service) categoryClue(v *game) map[string]any {
	cat := s.g.Node(v.Target).Category
	label := s.c.CategoryLabels[cat]
	if label == "" {
		label = cat
	}
	return map[string]any{"category": map[string]any{"key": cat, "label": label}, "message": "Categoria secretului: " + label + "."}
}
func (s *Service) warmer(v *game) *warmClue {
	if v.Warm != nil || v.WarmExhausted {
		return nil
	}
	best := v.Profile.Reachable + 1
	anchors := map[string]bool{}
	for _, r := range v.Guesses {
		best = min(best, r.Rank)
		anchors[r.Anchor] = true
	}
	if best <= 2 {
		return nil
	}
	type candidate struct {
		rank      int
		sal       float64
		label, id string
	}
	rows := []candidate{}
	for index, distance := range v.Profile.Dist {
		if distance < 0 {
			continue
		}
		id := s.g.IDAt(index)
		if id == v.Target {
			continue
		}
		sc := s.score(v, id, false, 0)
		if anchors[sc.Anchor] || sc.Rank <= 1 || sc.Rank >= best {
			continue
		}
		rows = append(rows, candidate{sc.Rank, s.g.Salience(id), s.g.Label(id), id})
	}
	sort.Slice(rows, func(i, j int) bool {
		a, b := rows[i], rows[j]
		if a.rank != b.rank {
			return a.rank < b.rank
		}
		if a.sal != b.sal {
			return a.sal > b.sal
		}
		aa, bb := s.g.Casefold(a.label), s.g.Casefold(b.label)
		if aa != bb {
			return aa < bb
		}
		return a.id < b.id
	})
	for _, familiar := range []bool{true, false} {
		for _, r := range rows {
			if familiar && r.sal < .55 {
				continue
			}
			return &warmClue{r.label, r.rank}
		}
	}
	return nil
}

func (s *Service) clueView(v *game) map[string]any {
	kind := ""
	if !v.Won && !v.GaveUp && v.Attempts >= 3 {
		if !v.CategoryClue && v.Category == "" {
			kind = "category"
		} else if s.warmer(v) != nil {
			kind = "warmer"
		}
	}
	out := map[string]any{"clues_used": v.Clues, "clue_available": kind != ""}
	if kind != "" {
		out["next_clue_kind"] = kind
	}
	if v.CategoryClue {
		out["clue"] = s.categoryClue(v)
	}
	if v.Warm != nil {
		out["warm_clue"] = warmJSON(v.Warm)
	}
	return out
}
func warmJSON(v *warmClue) map[string]any {
	return map[string]any{"label": v.Label, "rank": v.Rank, "message": fmt.Sprintf("Mai cald: %s (#%d).", v.Label, v.Rank)}
}
func (s *Service) target(v *game) map[string]any {
	return map[string]any{"id": v.Target, "label": s.g.Label(v.Target), "description": s.g.Description(v.Target)}
}
func (s *Service) state(id string, v *game) map[string]any {
	out := map[string]any{"game_id": id, "attempts": v.Attempts, "won": v.Won, "gave_up": v.GaveUp, "reachable_count": v.Profile.Reachable, "difficulty": v.Difficulty, "guesses": s.guesses(v)}
	for k, x := range s.clueView(v) {
		out[k] = x
	}
	if v.Daily != nil {
		out["daily"] = *v.Daily
	}
	if v.Category != "" {
		out["board_category"] = v.Category
	}
	if v.Won || v.GaveUp {
		out["target"] = s.target(v)
	}
	if v.Won {
		out["score"] = max(50, 1000-60*(max(1, v.Attempts)-1)-120*v.Clues)
		out["share"] = s.share(v)
	}
	return out
}
func (s *Service) share(v *game) string {
	var trail strings.Builder
	for _, id := range v.Order {
		r := v.Guesses[id]
		emoji := "🟥"
		if r.Distance == 0 {
			emoji = "🎯"
		} else if r.Closeness >= 75 {
			emoji = "🟩"
		} else if r.Closeness >= 50 {
			emoji = "🟨"
		} else if r.Closeness >= 25 {
			emoji = "🟧"
		}
		trail.WriteString(emoji)
	}
	header := "cat_de_roman_esti · Cald sau Rece"
	if v.Category != "" {
		header += " · " + s.c.CategoryLabels[v.Category]
	}
	word := "încercări"
	if v.Attempts == 1 {
		word = "încercare"
	}
	lines := []string{header, trail.String(), fmt.Sprintf("%d %s", v.Attempts, word)}
	if v.Clues > 0 {
		lines = append(lines, fmt.Sprintf("indiciu x%d", v.Clues))
	}
	if v.Daily != nil {
		lines = append(lines, *v.Daily)
	}
	return strings.Join(lines, "\n")
}
func feedback(v *game, r *record, isNew, found bool) map[string]any {
	if found {
		return map[string]any{"kind": "found", "message": "Exact — ai găsit răspunsul!"}
	}
	if !isNew {
		return map[string]any{"kind": "repeat", "message": fmt.Sprintf("Deja încercat — rămâne #%d.", r.Rank)}
	}
	if len(v.Order) == 0 {
		return map[string]any{"kind": "first", "message": fmt.Sprintf("Primul reper: #%d.", r.Rank)}
	}
	previous := v.Guesses[v.Order[len(v.Order)-1]]
	best := v.Profile.Reachable + 1
	for _, guess := range v.Guesses {
		best = min(best, guess.Rank)
	}
	places := func(n int) string {
		if n == 1 {
			return "un loc"
		}
		return fmt.Sprintf("%d locuri", n)
	}
	if r.Rank < best {
		delta := best - r.Rank
		return map[string]any{"kind": "new-best", "message": "Cel mai bun: cu " + places(delta) + " mai aproape.", "rank_delta": delta}
	}
	delta := previous.Rank - r.Rank
	kind, message := "same", "La fel de aproape ca încercarea trecută."
	if delta > 0 {
		kind, message = "warmer", "Mai cald cu "+places(delta)+"."
	} else if delta < 0 {
		kind, message = "colder", "Mai rece cu "+places(-delta)+"."
	}
	return map[string]any{"kind": kind, "message": message, "rank_delta": delta}
}
func (s *Service) unknown(v *game, suggestions []string) map[string]any {
	out := map[string]any{"ok": false, "message": "Cuvântul nu este încă în vocabularul jocului. Nu ai pierdut nicio încercare.", "suggestions": suggestions, "guesses": s.guesses(v), "attempts": v.Attempts, "won": v.Won, "reachable_count": v.Profile.Reachable}
	for k, x := range s.clueView(v) {
		out[k] = x
	}
	return out
}
func advisory(typed, shown string) bool {
	a, b := []rune(typed), []rune(shown)
	if len(a) == len(b) {
		different := []int{}
		for i := range a {
			if a[i] != b[i] {
				different = append(different, i)
			}
		}
		if len(different) <= 1 {
			return true
		}
		if len(different) == 2 {
			p, q := different[0], different[1]
			if q == p+1 && a[p] == b[q] && a[q] == b[p] {
				return true
			}
		}
	}
	if len(b) >= 3 && strings.HasPrefix(typed, shown) && len(a)-len(b) >= 1 && len(a)-len(b) <= 2 {
		return true
	}
	return graph.SequenceRatio(typed, shown) >= .82
}
func (s *Service) suggestProjection(text string) []*projection {
	key := s.g.Normalize(text)
	length := utf8.RuneCountInString(key)
	type candidate struct {
		score float64
		key   string
	}
	rows := []candidate{}
	for _, k := range s.projectionKeys {
		n := utf8.RuneCountInString(k)
		if n+length == 0 || 2*float64(min(n, length))/float64(n+length) < .78 {
			continue
		}
		score := graph.SequenceRatio(k, key)
		if score >= .78 {
			rows = append(rows, candidate{score, k})
		}
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].score == rows[j].score {
			return rows[i].key > rows[j].key
		}
		return rows[i].score > rows[j].score
	})
	if len(rows) > 6 {
		rows = rows[:6]
	}
	out := []*projection{}
	for _, r := range rows {
		out = append(out, s.projections[r.key])
	}
	return out
}
func (s *Service) GuessInput(id string, validate func() (GuessBody, *gameapi.Error)) (map[string]any, *gameapi.Error) {
	return s.action(id, func(v *game) (map[string]any, *gameapi.Error) {
		body, e := validate()
		if e != nil {
			return nil, e
		}
		if v.Won || v.GaveUp {
			return nil, fail(400, "Jocul s-a terminat")
		}
		text := strings.TrimFunc(body.Text, pySpace)
		if text == "" {
			return nil, fail(400, "Scrie un concept")
		}
		node := s.g.Resolve(text)
		unresolved := s.g.ReviewedUnresolved(text)
		var term *projection
		if node == "" && !unresolved {
			term = s.projections[s.g.Normalize(text)]
		}
		corrected := false
		if node == "" && term == nil {
			fuzzy := s.g.ResolveFuzzy(text)
			if fuzzy != "" && fuzzy != v.Target && s.feedbackAnchor(fuzzy, v.Target, true) == v.Target {
				fuzzy = ""
			}
			if fuzzy != "" && fuzzy != v.Target {
				digest := sha256.Sum256([]byte(id + "\x00" + fuzzy))
				token := fmt.Sprintf("ctxc_%x", digest[:8])
				if body.Confirm == nil || *body.Confirm != token {
					out := s.unknown(v, []string{})
					delete(out, "message")
					out["needs_confirmation"] = true
					out["resolved_label"] = s.g.Label(fuzzy)
					out["resolved_token"] = token
					out["message"] = "Am înțeles: " + s.g.Label(fuzzy) + ". Confirmă sau corectează."
					return out, nil
				}
			}
			node = fuzzy
			corrected = node != ""
		}
		if node == "" && term == nil {
			labels := []string{}
			if !unresolved {
				for _, p := range s.suggestProjection(text) {
					if s.feedbackAnchor(s.projectionAnchor(p, v.Target), v.Target, false) != v.Target {
						labels = append(labels, p.Label)
					}
				}
			}
			for _, label := range s.g.Suggest(text, 3) {
				nid := s.g.Resolve(label)
				if nid != "" && s.feedbackAnchor(nid, v.Target, true) != v.Target {
					labels = append(labels, label)
				}
			}
			suggestions := []string{}
			seen := map[string]bool{}
			for _, label := range labels {
				key := s.g.Casefold(label)
				if seen[key] || !advisory(s.g.Normalize(text), s.g.Normalize(label)) {
					continue
				}
				seen[key] = true
				suggestions = append(suggestions, label)
				if len(suggestions) == 3 {
					break
				}
			}
			return s.unknown(v, suggestions), nil
		}
		submitted := node
		guessID, label := node, s.g.Label(node)
		penalty := 0
		if term != nil {
			submitted = s.projectionAnchor(term, v.Target)
			guessID, label, penalty = term.PublicID, term.Label, term.RankPenalty
		}
		sc := s.score(v, submitted, term != nil, penalty)
		distance := 999
		if sc.Reachable {
			distance = sc.Distance
		}
		existing := v.Guesses[guessID]
		isNew := existing == nil
		attempt := v.Attempts + 1
		if !isNew {
			attempt = existing.Attempt
		}
		r := &record{ID: guessID, Label: label, Distance: distance, Temperature: temperature(v, sc), Closeness: closeness(v, sc), Rank: sc.Rank, Anchor: sc.Anchor, Attempt: attempt}
		found := term == nil && submitted == v.Target
		fb := feedback(v, r, isNew, found)
		v.Guesses[guessID] = r
		if isNew {
			v.Attempts++
			v.Order = append(v.Order, guessID)
		}
		if found {
			v.Won = true
		}
		out := map[string]any{"ok": true, "guess": recordJSON(r), "guesses": s.guesses(v), "attempts": v.Attempts, "won": v.Won, "reachable_count": v.Profile.Reachable, "feedback": fb}
		for k, x := range s.clueView(v) {
			out[k] = x
		}
		if corrected {
			out["message"] = "Am înțeles: " + r.Label + "."
		}
		if v.Won {
			out["target"] = s.target(v)
			out["score"] = max(50, 1000-60*(v.Attempts-1)-120*v.Clues)
			out["share"] = s.share(v)
		}
		return out, nil
	})
}
func (s *Service) Guess(id, text, confirm string) (map[string]any, *gameapi.Error) {
	return s.GuessInput(id, func() (GuessBody, *gameapi.Error) { return GuessBody{text, &confirm}, nil })
}
func (s *Service) Clue(id string) (map[string]any, *gameapi.Error) {
	return s.action(id, func(v *game) (map[string]any, *gameapi.Error) {
		if v.Won || v.GaveUp {
			return nil, fail(400, "Jocul s-a terminat")
		}
		if v.Attempts < 3 {
			n := 3 - v.Attempts
			word := "concepte"
			if n == 1 {
				word = "concept"
			}
			return nil, fail(400, fmt.Sprintf("Mai încearcă %d %s înainte de indiciu.", n, word))
		}
		out := map[string]any{"ok": true}
		if !v.CategoryClue && v.Category == "" {
			v.CategoryClue = true
			v.Clues++
			out["clue_kind"] = "category"
			for k, x := range s.categoryClue(v) {
				out[k] = x
			}
		} else {
			clue := s.warmer(v)
			if clue == nil {
				v.WarmExhausted = true
				return nil, fail(400, "Nu mai există un indiciu sigur mai cald.")
			}
			v.Warm = clue
			v.Clues++
			out["clue_kind"] = "warmer"
			out["word"] = warmJSON(clue)
			out["message"] = "Mai cald: " + clue.Label + "."
		}
		for k, x := range s.state(id, v) {
			out[k] = x
		}
		return out, nil
	})
}
func (s *Service) GiveUp(id string) (map[string]any, *gameapi.Error) {
	return s.action(id, func(v *game) (map[string]any, *gameapi.Error) {
		if v.Won || v.GaveUp {
			return nil, fail(400, "Jocul s-a terminat")
		}
		v.GaveUp = true
		return s.state(id, v), nil
	})
}
func pySpace(c rune) bool {
	return c >= 9 && c <= 13 || c >= 0x1c && c <= 0x20 || c == 0x85 || c == 0xa0 || c == 0x1680 || c >= 0x2000 && c <= 0x200a || c == 0x2028 || c == 0x2029 || c == 0x202f || c == 0x205f || c == 0x3000
}
