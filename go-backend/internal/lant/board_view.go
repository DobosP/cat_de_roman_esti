package lant

import (
	"errors"
	"slices"
)

// BoardRouteEdge is one directed step on a shortest route, with both forms
// of its caption as displayed by the native service.
type BoardRouteEdge struct {
	From         string `json:"from"`
	To           string `json:"to"`
	Caption      string `json:"caption"`
	ShortCaption string `json:"short_caption"`
}

// BoardShortestRoutesForReview returns the complete shortest-path DAG in
// lexical edge order. Distances to the target follow reverse legal adjacency.
func (s *Service) BoardShortestRoutesForReview(start, target string) (int, []BoardRouteEdge) {
	to := s.g.DistancesTo(target)
	length, ok := to[start]
	steps := []BoardRouteEdge{}
	if !ok {
		return -1, steps
	}
	from := s.g.DistancesFrom(start)
	for _, id := range s.g.AllIDs() {
		depth, fromStart := from[id]
		remaining, toTarget := to[id]
		if !fromStart || !toTarget || depth+remaining != length {
			continue
		}
		for _, next := range s.g.NeighborIDs(id) {
			if distance, ok := to[next]; ok && distance == remaining-1 {
				steps = append(steps, BoardRouteEdge{id, next, s.caption(id, next), s.short(id, next)})
			}
		}
	}
	return length, steps
}

// BoardRouteMenu is the native menu shown at one exact shortest-route prefix.
type BoardRouteMenu struct {
	Prefix  []string         `json:"prefix"`
	Choices []map[string]any `json:"choices"`
}

// BoardRouteMenusForReview follows every shortest prefix, including its
// exact chain history for the runtime's visited-node and detour rules. The
// cap bounds work for adversarially broad routes and refuses a partial view.
func (s *Service) BoardRouteMenusForReview(start, target string, optimal int) ([]BoardRouteMenu, error) {
	const maxMenus = 2048
	to := s.g.DistancesTo(target)
	menus := []BoardRouteMenu{}
	var visit func([]string) bool
	visit = func(prefix []string) bool {
		current := prefix[len(prefix)-1]
		if current == target {
			return true
		}
		if len(menus) == maxMenus {
			return false
		}
		v := &game{Start: start, Target: target, Optimal: optimal, Chain: prefix}
		choices := []map[string]any{}
		for _, id := range s.choiceIDs(v) {
			choice := s.choice(current, id)
			choice["id"] = id
			choices = append(choices, choice)
		}
		menus = append(menus, BoardRouteMenu{Prefix: slices.Clone(prefix), Choices: choices})
		remaining, reachable := to[current]
		if !reachable {
			return true
		}
		for _, next := range s.g.NeighborIDs(current) {
			if distance, ok := to[next]; ok && distance == remaining-1 {
				if !visit(append(prefix, next)) {
					return false
				}
			}
		}
		return true
	}
	if !visit([]string{start}) {
		return nil, errors.New("shortest-prefix menu count exceeds 2048")
	}
	return menus, nil
}
