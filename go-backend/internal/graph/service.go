// Package graph provides the shared, directed Romanian word-game substrate.
package graph

import (
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"math"
	"sort"
	"strings"
	"unicode/utf8"
)

type Neighbor struct {
	ID   string
	Edge *content.Edge
}
type Service struct {
	Content            *content.Content
	nodes              map[string]*content.Node
	all                []string
	real, full         map[string][]Neighbor
	adj, rev           map[string][]string
	index              map[string]string
	keys               []string
	indices            map[string]int
	denseAdj, denseRev [][]int
	denseCosts         [][]float64
}

func New(c *content.Content) *Service {
	return c.Shared("graph", func() any { return build(c) }).(*Service)
}
func build(c *content.Content) *Service {
	g := &Service{Content: c, nodes: map[string]*content.Node{}, real: map[string][]Neighbor{}, full: map[string][]Neighbor{}, adj: map[string][]string{}, rev: map[string][]string{}, index: c.NormalizedIndex}
	for i := range c.Nodes {
		n := &c.Nodes[i]
		g.nodes[n.ID] = n
		g.all = append(g.all, n.ID)
	}
	sort.Strings(g.all)
	raw := map[string][]Neighbor{}
	for i := range c.Edges {
		e := &c.Edges[i]
		raw[e.Src] = append(raw[e.Src], Neighbor{e.Dst, e})
		if e.Bidirectional {
			raw[e.Dst] = append(raw[e.Dst], Neighbor{e.Src, e})
		}
	}
	for _, id := range g.all {
		for _, distractors := range []bool{false, true} {
			best := map[string]Neighbor{}
			for _, nb := range raw[id] {
				if g.nodes[nb.ID] == nil || (!distractors && nb.Edge.IsDistractor) {
					continue
				}
				old, ok := best[nb.ID]
				if !ok || nb.Edge.Strength > old.Edge.Strength {
					best[nb.ID] = nb
				}
			}
			nbs := make([]Neighbor, 0, len(best))
			for _, nb := range best {
				nbs = append(nbs, nb)
			}
			sort.Slice(nbs, func(i, j int) bool {
				a, b := nbs[i], nbs[j]
				if a.Edge.Strength != b.Edge.Strength {
					return a.Edge.Strength > b.Edge.Strength
				}
				if g.Label(a.ID) != g.Label(b.ID) {
					return g.Label(a.ID) < g.Label(b.ID)
				}
				return a.ID < b.ID
			})
			if distractors {
				g.full[id] = nbs
			} else {
				g.real[id] = nbs
				ids := make([]string, 0, len(nbs))
				for _, nb := range nbs {
					ids = append(ids, nb.ID)
					g.rev[nb.ID] = append(g.rev[nb.ID], id)
				}
				sort.Strings(ids)
				g.adj[id] = ids
			}
		}
	}
	for id := range g.rev {
		sort.Strings(g.rev[id])
	}
	for key := range g.index {
		g.keys = append(g.keys, key)
	}
	sort.Strings(g.keys)
	g.indices = make(map[string]int, len(g.all))
	g.denseAdj = make([][]int, len(g.all))
	g.denseRev = make([][]int, len(g.all))
	g.denseCosts = make([][]float64, len(g.all))
	for i, id := range g.all {
		g.indices[id] = i
	}
	for i, id := range g.all {
		for _, next := range g.adj[id] {
			g.denseAdj[i] = append(g.denseAdj[i], g.indices[next])
		}
		for _, previous := range g.rev[id] {
			g.denseRev[i] = append(g.denseRev[i], g.indices[previous])
			g.denseCosts[i] = append(g.denseCosts[i], edgeCost(g.Link(previous, id).Strength))
		}
	}
	return g
}
func (g *Service) Node(id string) *content.Node { return g.nodes[id] }
func (g *Service) Exists(id string) bool        { return g.nodes[id] != nil }
func (g *Service) Label(id string) string {
	if n := g.Node(id); n != nil {
		return n.LabelRO
	}
	return id
}
func (g *Service) DisplayLabel(id string) string {
	if label, ok := g.Content.Labels[id]; ok {
		return label
	}
	return id
}
func (g *Service) Description(id string) string {
	if n := g.Node(id); n != nil {
		return n.Description
	}
	return ""
}
func (g *Service) Salience(id string) float64 {
	if n := g.Node(id); n != nil {
		return n.Salience
	}
	return 0
}
func (g *Service) AllIDs() []string { return append([]string{}, g.all...) }
func (g *Service) ByCategory(cat string) []string {
	out := []string{}
	for _, id := range g.all {
		if g.nodes[id].Category == cat {
			out = append(out, id)
		}
	}
	return out
}
func (g *Service) BySalience(minimum float64, descending bool) []string {
	out := []string{}
	for _, id := range g.all {
		if g.Salience(id) >= minimum {
			out = append(out, id)
		}
	}
	sort.Slice(out, func(i, j int) bool {
		a, b := out[i], out[j]
		if g.Salience(a) == g.Salience(b) {
			if descending {
				return a > b
			}
			return a < b
		}
		if descending {
			return g.Salience(a) > g.Salience(b)
		}
		return g.Salience(a) < g.Salience(b)
	})
	return out
}
func (g *Service) Neighbors(id string, includeDistractors bool) []Neighbor {
	if includeDistractors {
		return append([]Neighbor{}, g.full[id]...)
	}
	return append([]Neighbor{}, g.real[id]...)
}
func (g *Service) NeighborIDs(id string) []string    { return append([]string{}, g.adj[id]...) }
func (g *Service) PredecessorIDs(id string) []string { return append([]string{}, g.rev[id]...) }
func (g *Service) Degree(id string) int              { return len(g.adj[id]) }
func (g *Service) Link(a, b string) *content.Edge {
	for _, nb := range g.real[a] {
		if nb.ID == b {
			return nb.Edge
		}
	}
	return nil
}
func (g *Service) LinkLabel(a, b string) string {
	if e := g.Link(a, b); e != nil {
		return e.LabelRO
	}
	return ""
}
func (g *Service) CommonNeighbors(a, b, category string) []string {
	aa, bb := g.adj[a], g.adj[b]
	out := []string{}
	for i, j := 0, 0; i < len(aa) && j < len(bb); {
		if aa[i] < bb[j] {
			i++
		} else if aa[i] > bb[j] {
			j++
		} else {
			if category == "" || g.nodes[aa[i]].Category == category {
				out = append(out, aa[i])
			}
			i++
			j++
		}
	}
	return out
}
func bfs(adj map[string][]string, source string) (map[string]int, []string) {
	dist := map[string]int{source: 0}
	order := []string{source}
	for i := 0; i < len(order); i++ {
		cur := order[i]
		for _, next := range adj[cur] {
			if _, ok := dist[next]; !ok {
				dist[next] = dist[cur] + 1
				order = append(order, next)
			}
		}
	}
	return dist, order
}
func (g *Service) DistancesFromOrdered(id string) (map[string]int, []string) { return bfs(g.adj, id) }
func (g *Service) DistancesToOrdered(id string) (map[string]int, []string)   { return bfs(g.rev, id) }
func (g *Service) DistancesFrom(id string) map[string]int {
	v, _ := g.DistancesFromOrdered(id)
	return v
}
func (g *Service) DistancesTo(id string) map[string]int { v, _ := g.DistancesToOrdered(id); return v }
func (g *Service) Distance(a, b string) (int, bool) {
	if a == b {
		return 0, true
	}
	if !g.Exists(a) || !g.Exists(b) {
		return 0, false
	}
	start, _ := g.Index(a)
	target, _ := g.Index(b)
	dist := make([]int32, len(g.all))
	for i := range dist {
		dist[i] = -1
	}
	dist[start] = 0
	queue := []int{start}
	for at := 0; at < len(queue); at++ {
		cur := queue[at]
		for _, next := range g.denseAdj[cur] {
			if dist[next] >= 0 {
				continue
			}
			dist[next] = dist[cur] + 1
			if next == target {
				return int(dist[next]), true
			}
			queue = append(queue, next)
		}
	}
	return 0, false
}

type costNode struct {
	cost  float64
	index int
}
type costHeap []costNode

func (h costHeap) Len() int { return len(h) }
func (h costHeap) Less(i, j int) bool {
	if h[i].cost == h[j].cost {
		return h[i].index < h[j].index
	}
	return h[i].cost < h[j].cost
}
func (h costHeap) Swap(i, j int) { h[i], h[j] = h[j], h[i] }
func (h *costHeap) Push(v any)   { *h = append(*h, v.(costNode)) }
func (h *costHeap) Pop() any     { old := *h; v := old[len(old)-1]; *h = old[:len(old)-1]; return v }
func edgeCost(strength float64) float64 {
	if math.IsNaN(strength) || math.IsInf(strength, 0) || strength <= 0 {
		return 1.5
	}
	return 2 - math.Min(1, math.Max(0, strength))
}
func (g *Service) WeightedDistancesTo(target string) map[string]float64 {
	dense := g.WeightedDistancesToDense(target)
	out := map[string]float64{}
	for i, cost := range dense {
		if !math.IsInf(cost, 1) {
			out[g.all[i]] = cost
		}
	}
	if _, ok := g.Index(target); !ok {
		out[target] = 0
	}
	return out
}
func pySpace(c rune) bool {
	return c >= 9 && c <= 13 || c >= 0x1c && c <= 0x20 || c == 0x85 || c == 0xa0 || c == 0x1680 || c >= 0x2000 && c <= 0x200a || c == 0x2028 || c == 0x2029 || c == 0x202f || c == 0x205f || c == 0x3000
}
func transform(text string, mapping map[string]string) string {
	var b strings.Builder
	for _, c := range text {
		key := string(c)
		if replacement, ok := mapping[key]; ok {
			b.WriteString(replacement)
		} else {
			b.WriteRune(c)
		}
	}
	return strings.Join(strings.FieldsFunc(b.String(), pySpace), " ")
}
func (g *Service) Normalize(text string) string { return transform(text, g.Content.NormalizationMap) }
func (g *Service) Casefold(text string) string {
	var b strings.Builder
	for _, c := range text {
		if v, ok := g.Content.CasefoldMap[string(c)]; ok {
			b.WriteString(v)
		} else {
			b.WriteRune(c)
		}
	}
	return b.String()
}
func (g *Service) ReviewedUnresolved(text string) bool {
	key := transform(text, g.Content.AccentNormalizationMap)
	key = strings.ReplaceAll(key, "\u0327", "\u0326")
	return key == "pas\u0326te" || key == "pas\u0326tele"
}
func (g *Service) Resolve(text string) string {
	if text == "" || g.ReviewedUnresolved(text) {
		return ""
	}
	return g.index[g.Normalize(text)]
}

type scoredKey struct {
	score   float64
	key, id string
}

func (g *Service) Suggest(text string, limit int) []string {
	out := []string{}
	if g.ReviewedUnresolved(text) {
		return out
	}
	key := g.Normalize(text)
	if key == "" || limit <= 0 {
		return out
	}
	scores := []scoredKey{}
	keyLength := utf8.RuneCountInString(key)
	for _, cand := range g.keys {
		if ratioUpperLen(utf8.RuneCountInString(cand), keyLength) < .78 {
			continue
		}
		score := SequenceRatio(cand, key)
		if score >= .78 {
			scores = append(scores, scoredKey{score, cand, g.index[cand]})
		}
	}
	sort.Slice(scores, func(i, j int) bool {
		if scores[i].score == scores[j].score {
			return scores[i].key > scores[j].key
		}
		return scores[i].score > scores[j].score
	})
	if len(scores) > limit*4 {
		scores = scores[:limit*4]
	}
	seen := map[string]bool{}
	for _, s := range scores {
		if !seen[s.id] {
			seen[s.id] = true
			out = append(out, g.Label(s.id))
			if len(out) == limit {
				break
			}
		}
	}
	return out
}
func (g *Service) ResolveFuzzy(text string) string {
	if g.ReviewedUnresolved(text) {
		return ""
	}
	key := g.Normalize(text)
	if key == "" {
		return ""
	}
	if exact := g.index[key]; exact != "" {
		return exact
	}
	if key == "intrigii" || key == "intrigilor" {
		return ""
	}
	best := map[string]float64{}
	keyLength := utf8.RuneCountInString(key)
	for _, cand := range g.keys {
		if ratioUpperLen(utf8.RuneCountInString(cand), keyLength) < .84 {
			continue
		}
		score := SequenceRatio(cand, key)
		if score < .84 {
			continue
		}
		id := g.index[cand]
		if score > best[id] {
			best[id] = score
		}
	}
	ranked := []scoredKey{}
	for id, score := range best {
		ranked = append(ranked, scoredKey{score, "", id})
	}
	sort.Slice(ranked, func(i, j int) bool {
		if ranked[i].score == ranked[j].score {
			return ranked[i].id < ranked[j].id
		}
		return ranked[i].score > ranked[j].score
	})
	if len(ranked) == 0 || ranked[0].score < .90 || len(ranked) > 1 && ranked[0].score-ranked[1].score <= .06 {
		return ""
	}
	return ranked[0].id
}
func ratioUpperLen(a, b int) float64 {
	if a+b == 0 {
		return 1
	}
	return 2 * float64(min(a, b)) / float64(a+b)
}

// SequenceRatio reproduces difflib.SequenceMatcher(None,a,b), including autojunk
// and deterministic longest-block tie breaks; it is not a Levenshtein distance.
func SequenceRatio(aText, bText string) float64 {
	a, b := []rune(aText), []rune(bText)
	if len(a)+len(b) == 0 {
		return 1
	}
	positions := map[rune][]int{}
	for j, c := range b {
		positions[c] = append(positions[c], j)
	}
	if len(b) >= 200 {
		for c, js := range positions {
			if len(js) > len(b)/100+1 {
				delete(positions, c)
			}
		}
	}
	type area struct{ alo, ahi, blo, bhi int }
	queue := []area{{0, len(a), 0, len(b)}}
	matches := 0
	for len(queue) > 0 {
		r := queue[len(queue)-1]
		queue = queue[:len(queue)-1]
		bi, bj, size := r.alo, r.blo, 0
		previous := map[int]int{}
		for i := r.alo; i < r.ahi; i++ {
			current := map[int]int{}
			for _, j := range positions[a[i]] {
				if j < r.blo {
					continue
				}
				if j >= r.bhi {
					break
				}
				k := previous[j-1] + 1
				current[j] = k
				if k > size {
					bi, bj, size = i-k+1, j-k+1, k
				}
			}
			previous = current
		}
		for bi > r.alo && bj > r.blo && a[bi-1] == b[bj-1] {
			bi--
			bj--
			size++
		}
		for bi+size < r.ahi && bj+size < r.bhi && a[bi+size] == b[bj+size] {
			size++
		}
		if size > 0 {
			matches += size
			if r.alo < bi && r.blo < bj {
				queue = append(queue, area{r.alo, bi, r.blo, bj})
			}
			if bi+size < r.ahi && bj+size < r.bhi {
				queue = append(queue, area{bi + size, r.ahi, bj + size, r.bhi})
			}
		}
	}
	return 2 * float64(matches) / float64(len(a)+len(b))
}
