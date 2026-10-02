// Exact bounded graph projection and mined-round creation. No runtime Python.
package alchimie

import (
	"container/list"
	"encoding/binary"
	"encoding/json"
	"math"
	"sort"
	"strings"
	"sync"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
)

const MaxActions = 6
const MaxSearchStates = 50000
const MaxPairResults = 4096
const MaxProjectedConcepts = 32
const MaxAttemptedPairs = 496

type Pair [2]string
type Step struct {
	Pair    Pair     `json:"pair"`
	Results []string `json:"results"`
}
type Route []Step
type Projection struct {
	Recipes          map[Pair][]string
	Routes           []Route
	Par              int
	CandidateQuality [][3]float64
}

func pair(a, b string) Pair {
	if a > b {
		return Pair{b, a}
	}
	return Pair{a, b}
}
func pairLess(a, b Pair) bool {
	if a[0] != b[0] {
		return a[0] < b[0]
	}
	return a[1] < b[1]
}
func has(xs []string, x string) bool {
	i := sort.SearchStrings(xs, x)
	return i < len(xs) && xs[i] == x
}
func sortedUnique(xs []string) []string {
	m := map[string]bool{}
	for _, x := range xs {
		m[x] = true
	}
	out := make([]string, 0, len(m))
	for x := range m {
		out = append(out, x)
	}
	sort.Strings(out)
	return out
}

// union merges sorted unique ID lists without constructing a hash table.
func union(a, b []string) []string {
	out := make([]string, 0, len(a)+len(b))
	i, j := 0, 0
	for i < len(a) && j < len(b) {
		if a[i] < b[j] {
			out = append(out, a[i])
			i++
		} else if b[j] < a[i] {
			out = append(out, b[j])
			j++
		} else {
			out = append(out, a[i])
			i++
			j++
		}
	}
	out = append(out, a[i:]...)
	out = append(out, b[j:]...)
	return out
}
func compareIDs(a, b []string) int {
	for i := 0; i < min(len(a), len(b)); i++ {
		if a[i] < b[i] {
			return -1
		}
		if a[i] > b[i] {
			return 1
		}
	}
	if len(a) < len(b) {
		return -1
	}
	if len(a) > len(b) {
		return 1
	}
	return 0
}

func diff(a, b []string) []string {
	out := []string{}
	for _, x := range a {
		if !has(b, x) {
			out = append(out, x)
		}
	}
	return out
}
func stateKey(xs []string) string { return strings.Join(xs, "\x00") }
func pairs(xs []string) []Pair {
	out := []Pair{}
	for i, a := range xs {
		for _, b := range xs[i+1:] {
			out = append(out, Pair{a, b})
		}
	}
	return out
}
func recipePairs(m map[Pair][]string) []Pair {
	out := make([]Pair, 0, len(m))
	for p := range m {
		out = append(out, p)
	}
	sort.Slice(out, func(i, j int) bool { return pairLess(out[i], out[j]) })
	return out
}
func MinimumPlan(owned []string, target string, recipes map[Pair][]string, maxActions int) []Pair {
	start := sortedUnique(owned)
	if has(start, target) {
		return []Pair{}
	}
	type planState struct {
		owned []string
		plan  []Pair
	}
	frontier := []planState{{start, []Pair{}}}
	seen := map[string]bool{stateKey(start): true}
	ordered := recipePairs(recipes)
	for action := 0; action < maxActions; action++ {
		sort.Slice(frontier, func(i, j int) bool { return compareIDs(frontier[i].owned, frontier[j].owned) < 0 })
		next := []planState{}
		layer := map[string]bool{}
		for _, row := range frontier {
			for _, p := range ordered {
				if !has(row.owned, p[0]) || !has(row.owned, p[1]) {
					continue
				}
				fresh := diff(recipes[p], row.owned)
				if len(fresh) == 0 {
					continue
				}
				plan := append(append([]Pair{}, row.plan...), p)
				if has(fresh, target) {
					return plan
				}
				owned := union(row.owned, fresh)
				key := stateKey(owned)
				if !seen[key] && !layer[key] {
					layer[key] = true
					next = append(next, planState{owned, plan})
				}
			}
		}
		if len(next) == 0 {
			return nil
		}
		frontier = next
		for key := range layer {
			seen[key] = true
		}
	}
	return nil
}
func prune(raw Route, seeds []string, target string) Route {
	required := map[string]bool{target: true}
	selected := Route{}
	for i := len(raw) - 1; i >= 0; i-- {
		r := raw[i]
		outputs := []string{}
		for _, x := range r.Results {
			if required[x] {
				outputs = append(outputs, x)
			}
		}
		if len(outputs) == 0 || len(outputs) > 2 {
			return nil
		}
		selected = append(selected, Step{r.Pair, outputs})
		for _, x := range outputs {
			delete(required, x)
		}
		for _, x := range r.Pair {
			if !has(seeds, x) {
				required[x] = true
			}
		}
	}
	if len(required) > 0 {
		return nil
	}
	for i, j := 0, len(selected)-1; i < j; i, j = i+1, j-1 {
		selected[i], selected[j] = selected[j], selected[i]
	}
	return selected
}
func quality(g *graph.Service, r Route) (float64, float64, int) {
	strengths := []float64{}
	degree := 0
	for _, step := range r {
		for _, output := range step.Results {
			degree = max(degree, g.Degree(output))
			for _, parent := range step.Pair {
				e := g.Link(parent, output)
				s := 0.0
				if e != nil {
					s = e.Strength
				}
				strengths = append(strengths, s)
			}
		}
	}
	if len(strengths) == 0 {
		return 0, 0, 0
	}
	low := math.Inf(1)
	for _, s := range strengths {
		low = math.Min(low, s)
	}
	return low, compensatedSum(strengths) / float64(len(strengths)), degree
}
func routeLess(a, b Route) bool {
	for i := 0; i < min(len(a), len(b)); i++ {
		if a[i].Pair != b[i].Pair {
			return pairLess(a[i].Pair, b[i].Pair)
		}
		if compareIDs(a[i].Results, b[i].Results) != 0 {
			return compareIDs(a[i].Results, b[i].Results) < 0
		}
	}
	return len(a) < len(b)
}
func routeKey(r Route) string { b, _ := json.Marshal(r); return string(b) }

type indexPair [2]uint32

// Temporary search state uses compact ordered node indices. Final books retain
// their original opaque string IDs, so this representation never crosses HTTP.
type indexInventory struct {
	ids []uint32
	key string
}
type indexParent struct {
	previous string
	pair     indexPair
	fresh    []uint32
}
type indexStep struct {
	pair  indexPair
	fresh []uint32
}

func nodeKey(ids []uint32) string {
	encoded := make([]byte, len(ids)*4)
	for i, id := range ids {
		binary.BigEndian.PutUint32(encoded[i*4:], id)
	}
	return string(encoded)
}
func hasNode(ids []uint32, id uint32) bool {
	i := sort.Search(len(ids), func(i int) bool { return ids[i] >= id })
	return i < len(ids) && ids[i] == id
}
func compareNodes(a, b []uint32) int {
	for i := 0; i < min(len(a), len(b)); i++ {
		if a[i] < b[i] {
			return -1
		}
		if a[i] > b[i] {
			return 1
		}
	}
	if len(a) < len(b) {
		return -1
	}
	if len(a) > len(b) {
		return 1
	}
	return 0
}
func unionNodes(a, b []uint32) []uint32 {
	out := make([]uint32, 0, len(a)+len(b))
	i, j := 0, 0
	for i < len(a) && j < len(b) {
		if a[i] < b[j] {
			out = append(out, a[i])
			i++
		} else if a[i] > b[j] {
			out = append(out, b[j])
			j++
		} else {
			out = append(out, a[i])
			i++
			j++
		}
	}
	out = append(out, a[i:]...)
	out = append(out, b[j:]...)
	return out
}
func pruneIndexed(raw []indexStep, seeds []uint32, target uint32, idAt func(int) string) Route {
	required := map[uint32]bool{target: true}
	selected := Route{}
	for i := len(raw) - 1; i >= 0; i-- {
		step := raw[i]
		outputs := []string{}
		for _, id := range step.fresh {
			if required[id] {
				outputs = append(outputs, idAt(int(id)))
			}
		}
		if len(outputs) == 0 || len(outputs) > 2 {
			return nil
		}
		selected = append(selected, Step{Pair{idAt(int(step.pair[0])), idAt(int(step.pair[1]))}, outputs})
		for _, id := range step.fresh {
			delete(required, id)
		}
		for _, id := range step.pair {
			if !hasNode(seeds, id) {
				required[id] = true
			}
		}
	}
	if len(required) > 0 {
		return nil
	}
	for i, j := 0, len(selected)-1; i < j; i, j = i+1, j-1 {
		selected[i], selected[j] = selected[j], selected[i]
	}
	return selected
}
func BuildProjection(g *graph.Service, seeds []string, target, category string) *Projection {
	targetIndex, ok := g.Index(target)
	if !ok {
		return nil
	}
	idAt, index := g.IDAt, g.Index
	// Synthetic helper callers may retain an inert unknown seed. Production packs
	// contain valid IDs; the slow path preserves their historical tuple ordering.
	for _, seed := range seeds {
		if _, exists := g.Index(seed); !exists {
			ids := sortedUnique(append(g.AllIDs(), seeds...))
			positions := make(map[string]int, len(ids))
			for i, id := range ids {
				positions[id] = i
			}
			idAt = func(i int) string { return ids[i] }
			index = func(id string) (int, bool) { i, ok := positions[id]; return i, ok }
			targetIndex, _ = index(target)
			break
		}
	}
	start := make([]uint32, 0, len(seeds))
	for _, id := range sortedUnique(seeds) {
		i, _ := index(id)
		start = append(start, uint32(i))
	}
	targetID := uint32(targetIndex)
	startKey := nodeKey(start)
	frontier := []indexInventory{{start, startKey}}
	seen := map[string]bool{startKey: true}
	parents := map[string]indexParent{}
	candidates := []Route{}
	candidateSet := map[string]bool{}
	minimum, stateCount, exhausted := 0, 1, false
	pairResults := map[indexPair][]uint32{}
	reconstruct := func(ownedKey string, pair indexPair, fresh []uint32) Route {
		raw := []indexStep{{pair, fresh}}
		for key := ownedKey; key != startKey; {
			previous := parents[key]
			raw = append(raw, indexStep{previous.pair, previous.fresh})
			key = previous.previous
		}
		for i, j := 0, len(raw)-1; i < j; i, j = i+1, j-1 {
			raw[i], raw[j] = raw[j], raw[i]
		}
		return pruneIndexed(raw, start, targetID, idAt)
	}
	for action := 1; action <= MaxActions; action++ {
		if minimum != 0 && action > minimum+2 {
			break
		}
		sort.Slice(frontier, func(i, j int) bool { return compareNodes(frontier[i].ids, frontier[j].ids) < 0 })
		next := []indexInventory{}
		layer := map[string]bool{}
		for _, entry := range frontier {
			owned := entry.ids
			for i, a := range owned {
				for _, b := range owned[i+1:] {
					pair := indexPair{a, b}
					results, cached := pairResults[pair]
					if !cached {
						neighborIDs := g.CommonNeighbors(idAt(int(a)), idAt(int(b)), category)
						results = make([]uint32, 0, len(neighborIDs))
						for _, id := range neighborIDs {
							j, _ := index(id)
							results = append(results, uint32(j))
						}
						if len(pairResults) < MaxPairResults {
							pairResults[pair] = results
						}
					}
					if len(results) == 0 {
						continue
					}
					fresh := []uint32{}
					for _, id := range results {
						if !hasNode(owned, id) {
							fresh = append(fresh, id)
						}
					}
					if len(fresh) == 0 {
						continue
					}
					if hasNode(fresh, targetID) {
						if minimum == 0 {
							minimum = action
						}
						route := reconstruct(entry.key, pair, fresh)
						if route != nil {
							routeID := routeKey(route)
							if !candidateSet[routeID] {
								candidates = append(candidates, route)
								candidateSet[routeID] = true
							}
						}
						if len(candidates) >= 128 {
							exhausted = true
							break
						}
						continue
					}
					state := unionNodes(owned, fresh)
					key := nodeKey(state)
					if seen[key] || layer[key] {
						continue
					}
					stateCount++
					if stateCount > MaxSearchStates {
						exhausted = true
						break
					}
					parents[key] = indexParent{entry.key, pair, fresh}
					layer[key] = true
					next = append(next, indexInventory{state, key})
				}
				if exhausted {
					break
				}
			}
			if exhausted {
				break
			}
		}
		if exhausted || len(next) == 0 {
			break
		}
		frontier = next
		for key := range layer {
			seen[key] = true
		}
	}
	if minimum == 0 || len(candidates) == 0 {
		return nil
	}
	// Python sort(key=...) decorates once. Computing graph quality inside
	// the comparator repeats every lookup/allocation O(log candidates) times.
	type decoratedRoute struct {
		route            Route
		minimum, average float64
		degree           int
	}
	decorated := make([]decoratedRoute, 0, len(candidates))
	for _, route := range candidates {
		minimum, average, degree := quality(g, route)
		decorated = append(decorated, decoratedRoute{route, minimum, average, degree})
	}
	sort.Slice(decorated, func(i, j int) bool {
		a, b := decorated[i], decorated[j]
		if len(a.route) != len(b.route) {
			return len(a.route) < len(b.route)
		}
		if a.minimum != b.minimum {
			return a.minimum > b.minimum
		}
		if a.average != b.average {
			return a.average > b.average
		}
		if a.degree != b.degree {
			return a.degree < b.degree
		}
		return routeLess(a.route, b.route)
	})
	projection := &Projection{Recipes: map[Pair][]string{}, Routes: []Route{}, Par: minimum, CandidateQuality: [][3]float64{}}
	for _, row := range decorated {
		projection.CandidateQuality = append(projection.CandidateQuality, [3]float64{float64(len(row.route)), row.minimum, row.average})
	}
	for _, row := range decorated {
		r, low := row.route, row.minimum
		if len(projection.Routes) > 0 && low < .55 {
			continue
		}
		merged := map[Pair][]string{}
		for p, outputs := range projection.Recipes {
			merged[p] = append([]string{}, outputs...)
		}
		compatible := true
		for _, step := range r {
			existing, ok := merged[step.Pair]
			if ok && len(existing) == 1 && len(step.Results) == 1 && existing[0] != step.Results[0] {
				compatible = false
				break
			}
			merged[step.Pair] = union(existing, step.Results)
			if len(merged[step.Pair]) > 2 {
				compatible = false
				break
			}
		}
		if !compatible {
			continue
		}
		redundant := len(projection.Routes) > 0
		for _, step := range r {
			for _, x := range step.Results {
				if !has(projection.Recipes[step.Pair], x) {
					redundant = false
				}
			}
		}
		if redundant {
			continue
		}
		projected := sortedUnique(seeds)
		for p, outputs := range merged {
			projected = append(projected, p[0], p[1])
			projected = append(projected, outputs...)
		}
		if len(merged) > 24 || len(sortedUnique(projected)) > 32 {
			continue
		}
		projection.Recipes = merged
		projection.Routes = append(projection.Routes, r)
		if len(projection.Routes) >= 4 {
			break
		}
	}
	if len(projection.Routes) == 0 {
		return nil
	}
	plan := MinimumPlan(seeds, target, projection.Recipes, MaxActions)
	if plan == nil || len(plan) != minimum {
		return nil
	}
	return projection
}

// LRU bounds immutable projections exactly as the original 512-entry cache.
type cachedProjection struct {
	key string
	p   *Projection
}
type projectionCache struct {
	mu      sync.Mutex
	entries map[string]*list.Element
	lru     *list.List
}

func newCache() *projectionCache {
	return &projectionCache{entries: map[string]*list.Element{}, lru: list.New()}
}
func (c *projectionCache) get(key string) (*Projection, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	e, ok := c.entries[key]
	if !ok {
		return nil, false
	}
	c.lru.MoveToBack(e)
	return e.Value.(cachedProjection).p, true
}
func (c *projectionCache) put(key string, p *Projection) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if e, ok := c.entries[key]; ok {
		e.Value = cachedProjection{key, p}
		c.lru.MoveToBack(e)
		return
	}
	if len(c.entries) >= 512 {
		old := c.lru.Front()
		delete(c.entries, old.Value.(cachedProjection).key)
		c.lru.Remove(old)
	}
	c.entries[key] = c.lru.PushBack(cachedProjection{key, p})
}
func (s *Service) projection(seeds []string, target, category string) *Projection {
	encoded, _ := json.Marshal([]any{seeds, target, category})
	key := string(encoded)
	if p, ok := s.cache.get(key); ok {
		return p
	}
	p := BuildProjection(s.graph, seeds, target, category)
	if p != nil {
		p = s.extend(p, seeds, target, category)
	}
	s.cache.put(key, p)
	return p
}
func (s *Service) extend(core *Projection, seeds []string, target, category string) *Projection {
	// Extensions are strictly matched to the unchanged complete core, never applied by target alone.
	rows := []Step{}
	for _, p := range recipePairs(core.Recipes) {
		rows = append(rows, Step{p, core.Recipes[p]})
	}
	record := map[string]any{"seeds": seeds, "target": target, "category": category, "par": core.Par, "recipes": rows, "routes": core.Routes}
	encoded, _ := json.Marshal(record)
	var normalized any
	_ = json.Unmarshal(encoded, &normalized)
	encoded, _ = json.Marshal(normalized)
	boards, _ := s.data.RecipeExtensions["boards"].([]any)
	for _, raw := range boards {
		board, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		expected, _ := json.Marshal(board["core"])
		if string(encoded) != string(expected) {
			continue
		}
		// Reviewed additions are pinned to every actual node/edge snapshot as well
		// as the core. A compatible-looking target is insufficient authorization.
		for id, expected := range board["nodes"].(map[string]any) {
			if !jsonEqual(s.graph.Node(id), expected) {
				return core
			}
		}
		for _, expected := range board["edges"].(map[string]any) {
			row := expected.(map[string]any)
			if !jsonEqual(s.graph.Link(row["src_id"].(string), row["dst_id"].(string)), expected) {
				return core
			}
		}
		merged := &Projection{Recipes: map[Pair][]string{}, Routes: core.Routes, Par: core.Par, CandidateQuality: core.CandidateQuality}
		for p, x := range core.Recipes {
			merged.Recipes[p] = x
		}
		adds, _ := board["additions"].([]any)
		for _, raw := range adds {
			a := raw.(map[string]any)
			xs := a["pair"].([]any)
			p := pair(xs[0].(string), xs[1].(string))
			result := a["result"].(string)
			if !has(s.graph.CommonNeighbors(p[0], p[1], category), result) {
				return core
			}
			merged.Recipes[p] = []string{result}
		}
		plan := MinimumPlan(seeds, target, merged.Recipes, core.Par)
		if plan == nil || len(plan) != core.Par {
			return nil
		}
		return merged
	}
	return core
}

func jsonEqual(a, b any) bool {
	encoded, err := json.Marshal(a)
	if err != nil {
		return false
	}
	var normalized any
	if json.Unmarshal(encoded, &normalized) != nil {
		return false
	}
	left, _ := json.Marshal(normalized)
	right, err := json.Marshal(b)
	return err == nil && string(left) == string(right)
}
func (s *Service) closure(seeds []string, category string) (map[string]int, []string) {
	generation := map[string]int{}
	order := []string{}
	for _, id := range seeds {
		if _, ok := generation[id]; !ok {
			order = append(order, id)
		}
		generation[id] = 0
	}
	owned := sortedUnique(seeds)
	for gen := 1; ; gen++ {
		fresh := []string{}
		found := map[string]bool{}
		for pairIndex, a := range owned {
			for _, b := range owned[pairIndex+1:] {
				p := Pair{a, b}
				for _, id := range s.graph.CommonNeighbors(p[0], p[1], category) {
					if !has(owned, id) && !found[id] {
						found[id] = true
						fresh = append(fresh, id)
						generation[id] = gen
						order = append(order, id)
					}
				}
			}
		}
		if len(fresh) == 0 {
			break
		}
		owned = union(owned, sortedUnique(fresh))
	}
	return generation, order
}
func (s *Service) grow(rng *pyrandom.Random, k int, pool []string, category string) []string {
	starts := []string{}
	for _, id := range pool {
		if len(s.graph.NeighborIDs(id)) >= 3 {
			starts = append(starts, id)
		}
	}
	if len(starts) == 0 || len(pool) < k {
		return nil
	}
	owned := []string{starts[rng.RandBelow(len(starts))]}
	for attempt := 0; len(owned) < k && attempt < 4000; attempt++ {
		candidate := pool[rng.RandBelow(len(pool))]
		duplicate := false
		for _, x := range owned {
			duplicate = duplicate || x == candidate
		}
		if duplicate {
			continue
		}
		creates := len(owned) < 2
		for _, x := range owned {
			if creates {
				break
			}
			for _, result := range s.graph.CommonNeighbors(candidate, x, category) {
				known := result == candidate
				for _, o := range owned {
					known = known || result == o
				}
				if !known {
					creates = true
					break
				}
			}
		}
		if creates {
			owned = append(owned, candidate)
		}
	}
	if len(owned) == k {
		return owned
	}
	return nil
}
func sample(rng *pyrandom.Random, population []string, k int) []string {
	out := []string{}
	setSize := 21
	if k > 5 {
		power := 4
		for power < k*3 {
			power *= 4
		}
		setSize += power
	}
	if len(population) <= setSize {
		pool := append([]string{}, population...)
		for i := 0; i < k; i++ {
			j := rng.RandBelow(len(population) - i)
			out = append(out, pool[j])
			pool[j] = pool[len(population)-i-1]
		}
	} else {
		selected := map[int]bool{}
		for i := 0; i < k; i++ {
			j := rng.RandBelow(len(population))
			for selected[j] {
				j = rng.RandBelow(len(population))
			}
			selected[j] = true
			out = append(out, population[j])
		}
	}
	return out
}
func (s *Service) mine(rng *pyrandom.Random, difficulty, daily, category string) (*gameSession, *Error) {
	minGen, maxGen, seedMin, seedMax := 2, 3, 5, 7
	if difficulty == "usor" {
		maxGen = 2
		seedMin = 6
	} else if difficulty == "greu" {
		minGen = 3
		maxGen = 5
		seedMax = 5
	}
	if category == "" {
		usable := []string{}
		for c := range s.data.CategoryLabels {
			if len(s.graph.ByCategory(c)) >= 11 {
				usable = append(usable, c)
			}
		}
		sort.Strings(usable)
		if len(usable) > 0 {
			category = usable[rng.RandBelow(len(usable))]
		}
	}
	inScope := func(id string) bool { return category == "" || s.graph.Node(id).Category == category }
	pool := []string{}
	for _, id := range s.graph.BySalience(.4, true) {
		if len(s.graph.NeighborIDs(id)) >= 2 && inScope(id) {
			pool = append(pool, id)
		}
	}
	if len(pool) < seedMax {
		pool = []string{}
		for _, id := range s.graph.AllIDs() {
			if len(s.graph.NeighborIDs(id)) >= 2 && inScope(id) {
				pool = append(pool, id)
			}
		}
	}
	if category != "" && len(pool) < seedMin {
		return nil, &Error{Status: 503, Detail: "Nu există încă jocuri pentru această categorie."}
	}
	finish := func(seeds []string, target string) *gameSession {
		p := s.projection(seeds, target, category)
		if p == nil {
			return nil
		}
		return newGame(seeds, target, p, difficulty, daily, category)
	}
	var relaxed *gameSession
	for attempt := 0; attempt < 400; attempt++ {
		if len(pool) < seedMin {
			break
		}
		k := seedMin + rng.RandBelow(min(seedMax, len(pool))-seedMin+1)
		seeds := s.grow(rng, k, pool, category)
		if seeds == nil {
			continue
		}
		gen, order := s.closure(seeds, category)
		candidates := []string{}
		deepest := 0
		for _, id := range order {
			depth := gen[id]
			if depth >= minGen && depth <= maxGen && s.graph.Salience(id) >= .4 {
				candidates = append(candidates, id)
				deepest = max(deepest, depth)
			}
		}
		if difficulty == "greu" {
			deep := []string{}
			for _, id := range candidates {
				if gen[id] == deepest {
					deep = append(deep, id)
				}
			}
			candidates = deep
		}
		if len(candidates) == 0 {
			continue
		}
		game := finish(seeds, candidates[rng.RandBelow(len(candidates))])
		if game == nil {
			continue
		}
		openings := 0
		for _, p := range pairs(sortedUnique(seeds)) {
			if len(diff(game.projection.Recipes[p], sortedUnique(seeds))) > 0 {
				openings++
			}
		}
		if openings >= 2 {
			return game, nil
		}
		if relaxed == nil {
			relaxed = game
		}
	}
	if relaxed != nil {
		return relaxed, nil
	}
	fallback := []string{}
	for _, id := range s.graph.AllIDs() {
		if len(s.graph.NeighborIDs(id)) >= 2 && inScope(id) {
			fallback = append(fallback, id)
		}
	}
	seeds := sample(rng, fallback, min(seedMax, len(fallback)))
	gen, order := s.closure(seeds, category)
	deep := []string{}
	for _, id := range order {
		if gen[id] >= 2 {
			deep = append(deep, id)
		}
	}
	if len(deep) == 0 {
		if category != "" {
			return nil, &Error{Status: 503, Detail: "Nu există încă jocuri pentru această categorie."}
		}
		return nil, &Error{Status: 500, Detail: "Nu am putut genera un joc solvabil."}
	}
	rng.ShuffleStrings(deep)
	for _, target := range deep {
		if game := finish(seeds, target); game != nil {
			return game, nil
		}
	}
	return nil, &Error{Status: 503, Detail: "Nu există încă o țintă rezolvabilă în cel mult 6 mutări."}
}

// CPython 3.12+ float sum uses Neumaier compensation. Its final rounding also
// determines ties between otherwise equal recipe routes, so a naive sum changes play.
func compensatedSum(values []float64) float64 {
	total, correction := 0.0, 0.0
	for _, x := range values {
		next := total + x
		if math.Abs(total) >= math.Abs(x) {
			correction += (total - next) + x
		} else {
			correction += (x - next) + total
		}
		total = next
	}
	if correction != 0 && !math.IsInf(correction, 0) && !math.IsNaN(correction) {
		total += correction
	}
	return total
}
