package main

import (
	"errors"
	"fmt"
	"math"
	"slices"
	"sort"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/lant"
)

const (
	maxRoutes  = 4096 // shortest routes enumerated per board; more is refused, never truncated
	maxMatches = 20   // matches listed per prospect; the rest is counted
	sep        = "\x1f"
)

type prospect struct {
	Start  string `json:"start"`
	Target string `json:"target"`
	Par    *int   `json:"par,omitempty"`
}

// view is everything the comparison needs from one board or prospect.
type view struct {
	length  int
	routes  [][]string
	nodes   map[string]bool
	steps   map[string]bool // directed shortest-route edges
	choices map[string]bool // visible menu choices: from, choice id, short caption
	keys    []string        // routes as delimited strings for contiguous matching
}

type menuOverlap struct {
	Shared int     `json:"shared"`
	Total  int     `json:"total"`
	Share  float64 `json:"share"`
}

type match struct {
	BoardID        string      `json:"board_id"`
	Subpath        bool        `json:"subpath"`
	RoutesCovered  int         `json:"routes_covered"`
	ProspectRoutes int         `json:"prospect_routes"`
	BoardRoutes    int         `json:"board_routes"`
	SharedNodes    []string    `json:"shared_nodes"`
	SharedSteps    int         `json:"shared_steps"`
	MenuOverlap    menuOverlap `json:"menu_overlap"`
}

type result struct {
	Start         string  `json:"start"`
	Target        string  `json:"target"`
	Par           int     `json:"par"`
	NearDuplicate bool    `json:"near_duplicate"`
	MatchesTotal  int     `json:"matches_total"`
	Matches       []match `json:"matches"`
}

type served struct {
	id            string
	start, target string
	par           int
}

type analyzer struct {
	g      *graph.Service
	l      *lant.Service
	boards []served
	cache  map[string]*view
}

func newAnalyzer(c *content.Content) (*analyzer, error) {
	a := &analyzer{g: graph.New(c), l: lant.New(c), cache: map[string]*view{}}
	seen := map[string]bool{}
	for _, item := range c.PackItems {
		if item.Game != "lant" || item.Status != "approved" || !item.PilotEligible {
			continue
		}
		start, _ := item.Payload["start"].(string)
		target, _ := item.Payload["target"].(string)
		par, ok := integer(item.Payload["optimal"])
		if item.ID == "" || seen[item.ID] || !ok || !a.g.Exists(start) || !a.g.Exists(target) || start == target {
			return nil, fmt.Errorf("invalid served Lanț board %q", item.ID)
		}
		seen[item.ID] = true
		a.boards = append(a.boards, served{item.ID, start, target, par})
	}
	if len(a.boards) == 0 {
		return nil, errors.New("bundle has no served Lanț boards")
	}
	sort.Slice(a.boards, func(i, j int) bool { return a.boards[i].id < a.boards[j].id })
	return a, nil
}

func integer(value any) (int, bool) {
	number, ok := value.(float64)
	if !ok || number != math.Trunc(number) || number < 0 || number > 1000 {
		return 0, false
	}
	return int(number), true
}

func (a *analyzer) view(start, target string, par int) (*view, error) {
	length, steps := a.l.BoardShortestRoutesForReview(start, target)
	if length < 1 {
		return nil, fmt.Errorf("%s does not reach %s", start, target)
	}
	if par < length {
		return nil, fmt.Errorf("par %d is below the shortest distance %d", par, length)
	}
	v := &view{length: length, nodes: map[string]bool{}, steps: map[string]bool{}, choices: map[string]bool{}}
	next := map[string][]string{}
	for _, step := range steps {
		if strings.Contains(step.From+step.To, sep) {
			return nil, errors.New("node id contains a reserved separator")
		}
		next[step.From] = append(next[step.From], step.To)
		v.steps[step.From+sep+step.To] = true
	}
	routes, err := enumerate(next, start, target)
	if err != nil {
		return nil, err
	}
	v.routes = routes
	for _, route := range routes {
		for _, id := range route {
			v.nodes[id] = true
		}
		v.keys = append(v.keys, sep+strings.Join(route, sep)+sep)
	}
	menus, err := a.l.BoardRouteMenusForReview(start, target, par)
	if err != nil {
		return nil, err
	}
	for _, menu := range menus {
		from := menu.Prefix[len(menu.Prefix)-1]
		for _, choice := range menu.Choices {
			id, _ := choice["id"].(string)
			relation, _ := choice["relation"].(string)
			v.choices[from+sep+id+sep+relation] = true
		}
	}
	return v, nil
}

// enumerate lists every start-to-target path of the shortest-route DAG, refusing
// graphs with more than maxRoutes routes instead of truncating them.
func enumerate(next map[string][]string, start, target string) ([][]string, error) {
	counts := map[string]int{}
	var count func(string) int
	count = func(id string) int {
		if id == target {
			return 1
		}
		if n, ok := counts[id]; ok {
			return n
		}
		total := 0
		for _, to := range next[id] {
			total += count(to)
			if total > maxRoutes {
				total = maxRoutes + 1
				break
			}
		}
		counts[id] = total
		return total
	}
	if count(start) > maxRoutes {
		return nil, fmt.Errorf("more than %d shortest routes", maxRoutes)
	}
	routes := [][]string{}
	var walk func(string, []string)
	walk = func(id string, prefix []string) {
		prefix = append(prefix, id)
		if id == target {
			routes = append(routes, slices.Clone(prefix))
			return
		}
		for _, to := range next[id] {
			walk(to, prefix)
		}
	}
	walk(start, nil)
	return routes, nil
}

func (a *analyzer) served(b served) (*view, error) {
	if v, ok := a.cache[b.id]; ok {
		return v, nil
	}
	v, err := a.view(b.start, b.target, b.par)
	if err != nil {
		return nil, fmt.Errorf("served board %s: %w", b.id, err)
	}
	a.cache[b.id] = v
	return v, nil
}

// compare checks one prospect against every served board except exclude.
func (a *analyzer) compare(p prospect, exclude string) (result, error) {
	if !a.g.Exists(p.Start) || !a.g.Exists(p.Target) || p.Start == p.Target {
		return result{}, fmt.Errorf("invalid prospect endpoints %q -> %q", p.Start, p.Target)
	}
	par := 0
	if p.Par != nil {
		par = *p.Par
	} else {
		par, _ = a.l.BoardShortestRoutesForReview(p.Start, p.Target)
	}
	v, err := a.view(p.Start, p.Target, par)
	if err != nil {
		return result{}, fmt.Errorf("prospect %s -> %s: %w", p.Start, p.Target, err)
	}
	out := result{Start: p.Start, Target: p.Target, Par: par, Matches: []match{}}
	var matches []match
	for _, b := range a.boards {
		if b.id == exclude {
			continue
		}
		bv, err := a.served(b)
		if err != nil {
			return result{}, err
		}
		m := match{BoardID: b.id, ProspectRoutes: len(v.routes), BoardRoutes: len(bv.routes), SharedNodes: []string{}}
		for _, key := range v.keys {
			for _, other := range bv.keys {
				if strings.Contains(other, key) {
					m.RoutesCovered++
					break
				}
			}
		}
		m.Subpath = m.RoutesCovered == len(v.routes)
		for id := range v.nodes {
			if bv.nodes[id] {
				m.SharedNodes = append(m.SharedNodes, id)
			}
		}
		sort.Strings(m.SharedNodes)
		for step := range v.steps {
			if bv.steps[step] {
				m.SharedSteps++
			}
		}
		m.MenuOverlap.Total = len(v.choices)
		for choice := range v.choices {
			if bv.choices[choice] {
				m.MenuOverlap.Shared++
			}
		}
		if m.MenuOverlap.Total > 0 {
			m.MenuOverlap.Share = math.Round(float64(m.MenuOverlap.Shared)/float64(m.MenuOverlap.Total)*1e4) / 1e4
		}
		if m.Subpath || m.SharedSteps > 0 || m.MenuOverlap.Shared > 0 {
			matches = append(matches, m)
		}
	}
	sort.Slice(matches, func(i, j int) bool {
		x, y := matches[i], matches[j]
		if x.Subpath != y.Subpath {
			return x.Subpath
		}
		if x.RoutesCovered != y.RoutesCovered {
			return x.RoutesCovered > y.RoutesCovered
		}
		if x.MenuOverlap.Share != y.MenuOverlap.Share {
			return x.MenuOverlap.Share > y.MenuOverlap.Share
		}
		return x.BoardID < y.BoardID
	})
	out.MatchesTotal = len(matches)
	out.NearDuplicate = len(matches) > 0 && matches[0].Subpath
	out.Matches = matches[:min(len(matches), maxMatches)]
	if out.Matches == nil {
		out.Matches = []match{}
	}
	return out, nil
}
