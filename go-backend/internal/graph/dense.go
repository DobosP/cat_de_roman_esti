package graph

import (
	"container/heap"
	"math"
)

// Stable indices follow lexically sorted IDs, preserving Python heap tie breaks.
func (g *Service) Index(id string) (int, bool) { i, ok := g.indices[id]; return i, ok }
func (g *Service) IDAt(index int) string       { return g.all[index] }
func (g *Service) NodeCount() int              { return len(g.all) }
func (g *Service) DistancesToDense(target string) []int32 {
	dist := make([]int32, len(g.all))
	for i := range dist {
		dist[i] = -1
	}
	start, ok := g.Index(target)
	if !ok {
		return dist
	}
	dist[start] = 0
	queue := make([]int, 1, len(g.all))
	queue[0] = start
	for at := 0; at < len(queue); at++ {
		cur := queue[at]
		for _, previous := range g.denseRev[cur] {
			if dist[previous] < 0 {
				dist[previous] = dist[cur] + 1
				queue = append(queue, previous)
			}
		}
	}
	return dist
}
func (g *Service) WeightedDistancesToDense(target string) []float64 {
	dist := make([]float64, len(g.all))
	for i := range dist {
		dist[i] = math.Inf(1)
	}
	start, ok := g.Index(target)
	if !ok {
		return dist
	}
	dist[start] = 0
	h := &costHeap{{0, start}}
	heap.Init(h)
	for h.Len() > 0 {
		cur := heap.Pop(h).(costNode)
		if cur.cost > dist[cur.index] {
			continue
		}
		for at, previous := range g.denseRev[cur.index] {
			nd := cur.cost + g.denseCosts[cur.index][at]
			if nd < dist[previous] {
				dist[previous] = nd
				heap.Push(h, costNode{nd, previous})
			}
		}
	}
	return dist
}
