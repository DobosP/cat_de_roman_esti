// Package hopcli retains the original terminal semantic-hop game in Go.
package hopcli

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/roeduclient"
)

type Puzzle struct {
	ID, StartID, TargetID, Category, Difficulty string
	OptimalHops, Par                            int
	SolutionPath, HintNeighbors                 []string
}
type Bundle struct {
	Graph   *graph.Service
	Puzzles []Puzzle
	Raw     roeduclient.Bundle
}
type Game struct {
	Graph  *graph.Service
	Puzzle Puzzle
	Mode   string
	Path   []string
}
type Result struct {
	OK     bool   `json:"ok"`
	Reason string `json:"reason"`
	Won    bool   `json:"won"`
}

func number(v any) float64 {
	switch n := v.(type) {
	case json.Number:
		f, _ := n.Float64()
		return f
	case float64:
		return n
	case int:
		return float64(n)
	case string:
		f, _ := strconv.ParseFloat(n, 64)
		return f
	}
	return 0
}
func text(v any) string {
	if v == nil {
		return ""
	}
	if s, ok := v.(string); ok {
		return s
	}
	return fmt.Sprint(v)
}
func truth(v any) bool {
	switch b := v.(type) {
	case bool:
		return b
	case string:
		s := strings.ToLower(strings.TrimSpace(b))
		return s == "1" || s == "true" || s == "yes" || s == "t"
	case nil:
		return false
	default:
		return number(v) != 0
	}
}
func Parse(raw roeduclient.Bundle) (*Bundle, error) {
	if len(raw.Nodes) > 10000 || len(raw.Edges) > 50000 || len(raw.Puzzles) > 5000 {
		return nil, errors.New("terminal bundle record cap exceeded")
	}
	c := &content.Content{}
	ids := map[string]bool{}
	for _, r := range raw.Nodes {
		id := text(r["id"])
		if id == "" || ids[id] {
			return nil, errors.New("missing or duplicate node identity")
		}
		ids[id] = true
		label := text(r["label_ro"])
		if label == "" {
			label = id
		}
		kind := text(r["node_type"])
		if kind == "" {
			kind = "concept"
		}
		c.Nodes = append(c.Nodes, content.Node{ID: id, LabelRO: label, NodeType: kind, Category: text(r["category"]), Description: text(r["description"]), Salience: number(r["salience"])})
	}
	for _, r := range raw.Edges {
		src, dst := text(r["src_id"]), text(r["dst_id"])
		if src == "" || dst == "" {
			return nil, errors.New("missing edge endpoint")
		}
		bidirectional := true
		if v, ok := r["bidirectional"]; ok {
			bidirectional = truth(v)
		}
		c.Edges = append(c.Edges, content.Edge{ID: text(r["id"]), Src: src, Dst: dst, LabelRO: text(r["label_ro"]), Strength: number(r["strength"]), IsDistractor: truth(r["is_distractor"]), Bidirectional: bidirectional})
	}
	b := &Bundle{Graph: graph.New(c), Puzzles: []Puzzle{}, Raw: raw}
	pids := map[string]bool{}
	for _, r := range raw.Puzzles {
		p := Puzzle{ID: text(r["id"]), StartID: text(r["start_id"]), TargetID: text(r["target_id"]), Category: text(r["category"]), Difficulty: strings.ToLower(strings.TrimSpace(text(r["difficulty"]))), OptimalHops: int(number(r["optimal_hops"])), Par: int(number(r["par"])), SolutionPath: roeduclient.IDList(r["solution_path"]), HintNeighbors: roeduclient.IDList(r["hint_neighbors"])}
		if _, ok := r["par"]; !ok {
			p.Par = p.OptimalHops
		}
		if p.Difficulty == "" {
			p.Difficulty = "easy"
		}
		if p.ID == "" || pids[p.ID] || !ids[p.StartID] || !ids[p.TargetID] || p.Par < 0 || p.OptimalHops < 0 {
			return nil, errors.New("unplayable terminal puzzle identity/endpoints")
		}
		pids[p.ID] = true
		b.Puzzles = append(b.Puzzles, p)
	}
	return b, nil
}
func ReadFixture(path string) (*Bundle, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	data, err := io.ReadAll(io.LimitReader(f, (32<<20)+1))
	if err != nil {
		return nil, err
	}
	if len(data) > 32<<20 {
		return nil, errors.New("fixture byte cap exceeded")
	}
	var raw roeduclient.Bundle
	d := json.NewDecoder(strings.NewReader(string(data)))
	d.UseNumber()
	if err = d.Decode(&raw); err != nil {
		return nil, err
	}
	if d.Decode(new(any)) != io.EOF {
		return nil, errors.New("trailing fixture JSON")
	}
	return Parse(raw)
}
func New(g *graph.Service, p Puzzle, mode string) (*Game, error) {
	mode = strings.ToLower(strings.TrimSpace(mode))
	if mode != "easy" && mode != "hard" {
		return nil, errors.New("unknown mode (expected easy|hard)")
	}
	if !g.Exists(p.StartID) || !g.Exists(p.TargetID) {
		return nil, errors.New("puzzle start/target missing from graph")
	}
	return &Game{g, p, mode, []string{p.StartID}}, nil
}
func (g *Game) Current() string           { return g.Path[len(g.Path)-1] }
func (g *Game) Won() bool                 { return g.Current() == g.Puzzle.TargetID }
func (g *Game) Hops() int                 { return len(g.Path) - 1 }
func (g *Game) Options() []graph.Neighbor { return g.Graph.Neighbors(g.Current(), g.Mode == "hard") }
func (g *Game) Hints() []string {
	out := []string{}
	if g.Mode != "easy" {
		return out
	}
	reachable := map[string]bool{}
	for _, n := range g.Options() {
		reachable[n.ID] = true
	}
	for i, id := range g.Puzzle.SolutionPath {
		if id == g.Current() {
			if i+1 < len(g.Puzzle.SolutionPath) && reachable[g.Puzzle.SolutionPath[i+1]] {
				return []string{g.Puzzle.SolutionPath[i+1]}
			}
			return out
		}
	}
	for _, id := range g.Puzzle.HintNeighbors {
		if reachable[id] {
			out = append(out, id)
		}
	}
	return out
}
func (g *Game) Hop(dst string) Result {
	if g.Won() {
		return Result{false, "game already won", true}
	}
	if dst == g.Current() {
		return Result{false, "already at this node", false}
	}
	for _, n := range g.Options() {
		if n.ID == dst {
			g.Path = append(g.Path, dst)
			return Result{true, "", g.Won()}
		}
	}
	return Result{false, "no edge from current node to that node", false}
}
func (g *Game) Undo() Result {
	if len(g.Path) <= 1 {
		return Result{false, "already at the start — nothing to undo", false}
	}
	g.Path = g.Path[:len(g.Path)-1]
	return Result{true, "", g.Won()}
}
func (g *Game) Score() int {
	if !g.Won() {
		return 0
	}
	return max(100, 1000-100*max(0, g.Hops()-g.Puzzle.Par))
}
func (g *Game) Summary() map[string]any {
	return map[string]any{"puzzle_id": g.Puzzle.ID, "mode": g.Mode, "won": g.Won(), "hops": g.Hops(), "par": g.Puzzle.Par, "optimal_hops": g.Puzzle.OptimalHops, "score": g.Score(), "path": append([]string{}, g.Path...)}
}

// Smoke replays an independently served solution, rejecting missing or illegal
// steps and checking exact optimal hops/par. It cannot silently skip a gate.
func Smoke(b *Bundle, difficulty string) (map[string]any, error) {
	for _, p := range b.Puzzles {
		if p.Difficulty != difficulty {
			continue
		}
		if len(p.SolutionPath) < 2 || p.SolutionPath[0] != p.StartID || p.SolutionPath[len(p.SolutionPath)-1] != p.TargetID {
			return nil, errors.New("missing or inconsistent solution path")
		}
		g, err := New(b.Graph, p, difficulty)
		if err != nil {
			return nil, err
		}
		for _, id := range p.SolutionPath[1:] {
			if !g.Hop(id).OK {
				return nil, errors.New("illegal served solution hop")
			}
		}
		if !g.Won() || g.Hops() != p.OptimalHops || g.Hops() != p.Par || g.Score() != 1000 {
			return nil, errors.New("served solution fails optimal/par gate")
		}
		return g.Summary(), nil
	}
	return nil, errors.New("no matching puzzle")
}
