// Package browserplan supplies private, offline test-process journeys. It is
// never imported by cat-server and installs no solution or debug HTTP route.
package browserplan

import (
	"encoding/json"
	"fmt"
	"math/big"
	"net/http"
	"net/http/httptest"
	"net/url"
	"sort"
	"strconv"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/alchimie"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/lant"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pack"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
)

const MaxSeedSearch = 10000
const MaxRoutes = 512

var Games = []string{"alchimie", "intrusul", "perechi", "conexiuni", "contexto", "lant"}

type Step struct {
	Action  string         `json:"action"`
	Labels  []string       `json:"labels,omitempty"`
	Payload map[string]any `json:"payload"`
}
type Plan struct {
	Initial   map[string]any      `json:"initial"`
	Steps     []Step              `json:"steps"`
	Practice  Step                `json:"practice"`
	HintSetup []map[string]string `json:"hint_setup,omitempty"`
	PackID    string              `json:"pack_id,omitempty"`
	Query     map[string]string   `json:"query,omitempty"`
}

func call(h http.Handler, method, path string, body any) (map[string]any, error) {
	raw := []byte{}
	if body != nil {
		var err error
		raw, err = json.Marshal(body)
		if err != nil {
			return nil, err
		}
	}
	r := httptest.NewRequest(method, path, strings.NewReader(string(raw)))
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	if w.Code != 200 {
		return nil, fmt.Errorf("offline %s %s: HTTP %d", method, strings.Split(path, "?")[0], w.Code)
	}
	var value map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &value); err != nil {
		return nil, err
	}
	return value, nil
}
func values(v any) []string {
	out := []string{}
	for _, x := range v.([]any) {
		out = append(out, x.(string))
	}
	return out
}
func tiles(v any) []string {
	out := []string{}
	for _, x := range v.([]any) {
		out = append(out, x.(map[string]any)["id"].(string))
	}
	return out
}
func equalIDs(a, b []string) bool {
	a = append([]string{}, a...)
	b = append([]string{}, b...)
	sort.Strings(a)
	sort.Strings(b)
	return strings.Join(a, "\x00") == strings.Join(b, "\x00")
}
func targetItem(c *content.Content, game, id string) (*content.PackItem, error) {
	for i := range c.PackItems {
		x := &c.PackItems[i]
		if x.Game == game && x.ID == id && x.PilotEligible {
			return x, nil
		}
	}
	return nil, fmt.Errorf("named fixture requires a selectable approved %s round %s", game, id)
}
func namedSeed(c *content.Content, game, id string) (map[string]string, error) {
	item, err := targetItem(c, game, id)
	if err != nil {
		return nil, err
	}
	query := map[string]string{"category": item.Category, "difficulty": item.Difficulty}
	p := pack.New(c)
	for seed := 0; seed < MaxSeedSearch; seed++ {
		if game == "alchimie" {
			x := p.PickSeeded(game, pyrandom.New(big.NewInt(int64(seed))), pack.PickOptions{Category: item.Category, Difficulty: item.Difficulty})
			if x != nil && x.ID == id {
				query["seed"] = strconv.Itoa(seed)
				return query, nil
			}
		} else if game == "lant" {
			// The ordinary engine has additional route-width selection rails. Fresh
			// stores avoid filling the production-size 1000-session bound during search.
			s := lant.New(c)
			state, e := s.Create(big.NewInt(int64(seed)), item.Difficulty, nil, item.Category)
			if e != nil {
				return nil, e
			}
			selected, _, _, _, ok := s.Progress(state["game_id"].(string))
			if ok && selected == id {
				query["seed"] = strconv.Itoa(seed)
				return query, nil
			}
		} else {
			return nil, fmt.Errorf("named fixtures support Alchimie and Lanț only")
		}
	}
	return nil, fmt.Errorf("round %s not selectable within %d public seeds", id, MaxSeedSearch)
}

// Solution creates one ordinary, in-process HTTP session. Only the test process
// receives the action plan; browsers still execute every action on the real server.
func Solution(c *content.Content, game, packID, daily string) (*Plan, error) {
	return SolutionQuery(c, game, packID, daily, nil)
}
func SolutionQuery(c *content.Content, game, packID, daily string, override map[string]string) (*Plan, error) {
	query := map[string]string{"seed": "38", "difficulty": "usor"}
	var err error
	if packID != "" {
		query, err = namedSeed(c, game, packID)
		if err != nil {
			return nil, err
		}
	}
	for k, v := range override {
		query[k] = v
	}
	if daily != "" {
		query["daily"] = daily
	}
	if game == "intrusul" || game == "perechi" {
		query["starter"] = "1"
	}
	q := url.Values{}
	for k, v := range query {
		q.Set(k, v)
	}
	h := httpapi.New(c)
	base := "/api/wordgames/" + game + "/games"
	initial, err := call(h, "POST", base+"?"+q.Encode(), nil)
	if err != nil {
		return nil, err
	}
	sid := initial["game_id"].(string)
	g := graph.New(c)
	p := &Plan{Initial: initial, Steps: []Step{}}
	label := g.DisplayLabel
	if game == "alchimie" {
		label = g.Label
	}
	add := func(action string, ids []string) {
		labels := []string{}
		for _, id := range ids {
			labels = append(labels, label(id))
		}
		payload := map[string]any{"ids": ids}
		if game == "intrusul" {
			payload = map[string]any{"id": ids[0]}
		}
		if game == "alchimie" {
			payload = map[string]any{"a": ids[0], "b": ids[1]}
		}
		p.Steps = append(p.Steps, Step{action, labels, payload})
	}
	switch game {
	case "intrusul", "perechi":
		boardIDs := tiles(initial["tiles"])
		var found *content.Board
		for i := range c.Boards {
			x := &c.Boards[i]
			if x.Game != game {
				continue
			}
			ids := []string{}
			if game == "intrusul" {
				ids = append(values(x.Payload["members"]), x.Payload["intruder"].(string))
			} else {
				for _, r := range x.Payload["pairs"].([]any) {
					ids = append(ids, values(r.(map[string]any)["members"])...)
				}
			}
			if equalIDs(boardIDs, ids) {
				found = x
				break
			}
		}
		if found == nil {
			return nil, fmt.Errorf("reviewed %s board unavailable", game)
		}
		if game == "intrusul" {
			add("guess", []string{found.Payload["intruder"].(string)})
			id := values(found.Payload["members"])[0]
			p.Practice = Step{"guess", []string{label(id)}, map[string]any{"id": id}}
		} else {
			rows := found.Payload["pairs"].([]any)
			for _, r := range rows {
				add("match", values(r.(map[string]any)["members"]))
			}
			ids := []string{values(rows[0].(map[string]any)["members"])[0], values(rows[1].(map[string]any)["members"])[0]}
			p.Practice = Step{"match", []string{label(ids[0]), label(ids[1])}, map[string]any{"ids": ids}}
		}
	case "conexiuni":
		boardIDs := tiles(initial["tiles"])
		var groups map[string]any
		for _, x := range c.PackItems {
			if x.Game == game && equalIDs(boardIDs, values(x.Payload["order"])) {
				groups = x.Payload["groups"].(map[string]any)
				break
			}
		}
		if groups == nil {
			return nil, fmt.Errorf("reviewed Conexiuni board unavailable")
		}
		keys := []string{}
		for k := range groups {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		for _, k := range keys {
			add("guess", values(groups[k]))
		}
		ids := append(values(groups[keys[0]])[:3:3], values(groups[keys[1]])[0])
		labels := []string{}
		for _, id := range ids {
			labels = append(labels, label(id))
		}
		p.Practice = Step{"guess", labels, map[string]any{"ids": ids}}
	case "contexto":
		revealed, err := call(h, "POST", base+"/"+sid+"/giveup", nil)
		if err != nil {
			return nil, err
		}
		target := revealed["target"].(map[string]any)["id"].(string)
		p.Steps = append(p.Steps, Step{Action: "guess", Payload: map[string]any{"text": g.Label(target)}})
		for _, id := range g.PredecessorIDs(target) {
			if id != target && g.Resolve(g.Label(id)) == id {
				p.Practice = Step{Action: "guess", Payload: map[string]any{"text": g.Label(id)}}
				break
			}
		}
		if p.Practice.Action == "" {
			return nil, fmt.Errorf("Contexto has no resolvable practice predecessor")
		}
	case "lant":
		current := initial["start"].(map[string]any)["id"].(string)
		target := initial["target"].(map[string]any)["id"].(string)
		to := g.DistancesTo(target)
		for current != target {
			neighbors := g.NeighborIDs(current)
			sort.Strings(neighbors)
			next := ""
			for _, id := range neighbors {
				if d, ok := to[id]; ok && d == to[current]-1 {
					next = id
					break
				}
			}
			if next == "" {
				return nil, fmt.Errorf("Lanț has no route")
			}
			current = next
			p.Steps = append(p.Steps, Step{Action: "move", Payload: map[string]any{"text": g.Label(current)}})
		}
	case "alchimie":
		seed, ok := new(big.Int).SetString(query["seed"], 10)
		if !ok {
			return nil, fmt.Errorf("invalid planner seed")
		}
		opts := pack.PickOptions{Category: query["category"], Difficulty: query["difficulty"]}
		var item *content.PackItem
		if daily != "" {
			item = pack.New(c).PickDaily(game, daily, opts)
		} else {
			item = pack.New(c).PickSeeded(game, pyrandom.New(seed), opts)
		}
		if item == nil {
			return nil, fmt.Errorf("browser Alchimie fixture needs a curated projection")
		}
		if packID != "" && item.ID != packID {
			return nil, fmt.Errorf("named selection drift")
		}
		seeds := values(item.Payload["seeds"])
		target := item.Payload["target"].(string)
		projection := alchimie.BuildProjection(g, seeds, target, item.Category)
		if projection == nil {
			return nil, fmt.Errorf("projection unavailable")
		}
		// Use the independent core plan. Every action is subsequently verified against
		// ordinary HTTP gameplay, which also enforces the reviewed extension rails.
		plan := alchimie.MinimumPlan(seeds, target, projection.Recipes, alchimie.MaxActions)
		if len(plan) == 0 {
			return nil, fmt.Errorf("fixture needs a nonempty crafting plan")
		}
		for _, pair := range plan {
			add("combine", pair[:])
		}
		sort.Strings(seeds)
		for i, a := range seeds {
			for _, b := range seeds[i+1:] {
				if len(projection.Recipes[alchimie.Pair{a, b}]) == 0 {
					p.HintSetup = append(p.HintSetup, map[string]string{"a": a, "b": b})
				}
			}
		}
		if len(p.HintSetup) < 6 {
			return nil, fmt.Errorf("fixture needs six barren owned pairs")
		}
	default:
		return nil, fmt.Errorf("unknown game %s", game)
	}
	if len(p.Steps) == 0 {
		return nil, fmt.Errorf("empty winning journey")
	}
	if p.Practice.Action == "" {
		p.Practice = p.Steps[0]
	}
	// Validate the planner against a fresh ordinary session before emitting secrets.
	verify := httpapi.New(c)
	state, err := call(verify, "POST", base+"?"+q.Encode(), nil)
	if err != nil {
		return nil, err
	}
	id := state["game_id"].(string)
	for _, step := range p.Steps {
		state, err = call(verify, "POST", base+"/"+id+"/"+step.Action, step.Payload)
		if err != nil {
			return nil, err
		}
	}
	if state["won"] != true {
		return nil, fmt.Errorf("offline winning journey failed")
	}
	delete(initial, "game_id")
	if packID != "" {
		p.PackID = packID
		p.Query = query
	}
	return p, nil
}

type Node struct {
	ID    string `json:"id"`
	Label string `json:"label"`
}
type Journey struct {
	PackID string            `json:"pack_id"`
	Query  map[string]string `json:"query"`
	Start  any               `json:"start"`
	Target any               `json:"target"`
	Routes [][]Node          `json:"routes"`
}

func CaptionJourney(c *content.Content, id string) (*Journey, error) {
	query, err := namedSeed(c, "lant", id)
	if err != nil {
		return nil, err
	}
	q := url.Values{}
	for k, v := range query {
		q.Set(k, v)
	}
	state, err := call(httpapi.New(c), "POST", "/api/wordgames/lant/games?"+q.Encode(), nil)
	if err != nil {
		return nil, err
	}
	g := graph.New(c)
	start := state["start"].(map[string]any)["id"].(string)
	target := state["target"].(map[string]any)["id"].(string)
	to := g.DistancesTo(target)
	result := &Journey{id, query, state["start"], state["target"], [][]Node{}}
	var walk func([]Node) error
	walk = func(path []Node) error {
		current := path[len(path)-1].ID
		if current == target {
			if len(result.Routes) >= MaxRoutes {
				return fmt.Errorf("caption route bound exceeded")
			}
			result.Routes = append(result.Routes, append([]Node{}, path...))
			return nil
		}
		if len(path) > len(c.Nodes) {
			return fmt.Errorf("caption route depth exceeded")
		}
		neighbors := g.NeighborIDs(current)
		sort.Strings(neighbors)
		for _, node := range neighbors {
			if d, ok := to[node]; ok && d == to[current]-1 {
				if err := walk(append(path, Node{node, g.Label(node)})); err != nil {
					return err
				}
			}
		}
		return nil
	}
	if err = walk([]Node{{start, g.Label(start)}}); err != nil {
		return nil, err
	}
	if len(result.Routes) == 0 {
		return nil, fmt.Errorf("caption has no shortest route")
	}
	return result, nil
}
