package contentops

import (
	"errors"
	"fmt"
	"path/filepath"
	"sort"
)

func (s *Sources) regionFlags() map[string]string {
	regions := map[string]bool{}
	for _, n := range s.Graph.Content.Nodes {
		for _, label := range []string{"Moldova", "Transilvania", "Oltenia", "Muntenia", "Dobrogea", "Banat", "Bucovina", "Maramureș", "Crișana", "Ardeal"} {
			if n.NodeType == "place" && n.LabelRO == label {
				regions[n.ID] = true
			}
		}
	}
	links := map[string]map[string]bool{}
	generic := map[string]bool{}
	for _, edge := range s.Graph.Content.Edges {
		if edge.IsDistractor {
			continue
		}
		for _, p := range [][2]string{{edge.Src, edge.Dst}, {edge.Dst, edge.Src}} {
			if !regions[p[1]] || regions[p[0]] || s.Graph.Node(p[0]) == nil || s.Graph.Node(p[0]).NodeType == "place" {
				continue
			}
			if links[p[0]] == nil {
				links[p[0]] = map[string]bool{}
			}
			links[p[0]][p[1]] = true
			if edge.Relation == "related_to" {
				generic[p[0]] = true
			}
		}
	}
	out := map[string]string{}
	for id, rs := range links {
		node := s.Graph.Node(id)
		if len(rs) >= 2 {
			out[id] = fmt.Sprintf("linked to %d regions", len(rs))
		} else if node != nil && node.NodeType == "concept" && node.Salience >= .7 && generic[id] {
			out[id] = "national-salience concept with generic related_to region edge"
		}
	}
	return out
}
func (s *Sources) regionFinding(r Object, game string) bool {
	flags := s.regionFlags()
	if game == "contexto" {
		target := str(r["target"])
		if flags[target] != "" {
			return true
		}
		regions := map[string]bool{}
		for _, label := range []string{"Moldova", "Transilvania", "Oltenia", "Muntenia", "Dobrogea", "Banat", "Bucovina", "Maramureș", "Crișana", "Ardeal"} {
			regions[label] = true
		}
		if regions[s.Graph.Label(target)] {
			n := 0
			for _, id := range s.Graph.PredecessorIDs(target) {
				e := s.Graph.Link(id, target)
				if flags[id] != "" && e != nil && e.Strength >= .6 {
					n++
				}
			}
			return n >= 2
		}
	}
	if game == "conexiuni" {
		flag, region := false, false
		for _, id := range boardIDs(r) {
			flag = flag || flags[id] != ""
			switch s.Graph.Label(id) {
			case "Moldova", "Transilvania", "Oltenia", "Muntenia", "Dobrogea", "Banat", "Bucovina", "Maramureș", "Crișana", "Ardeal":
				region = true
			}
		}
		return flag && region
	}
	return false
}
func (s *Sources) ownerHolds() (map[string]bool, error) {
	out := map[string]bool{}
	for _, name := range []string{"board_demotions_v43.json", "contexto_demotions_v44.json", "contexto_impact_reserve_v69.json", "release_reserve_v1.json"} {
		path := filepath.Join(s.Root, fixtures+name)
		if e := s.bindInput(path); e != nil {
			return nil, e
		}
		m, _, e := read(path)
		if e != nil {
			return nil, e
		}
		ids, e := uniqueStrings(m["ids"])
		if e != nil {
			return nil, e
		}
		if integer(obj(m["meta"])["count"]) != len(ids) {
			return nil, errors.New("owner demotion metadata count mismatch")
		}
		for _, id := range ids {
			if out[id] {
				return nil, errors.New("duplicate owner demotion id")
			}
			out[id] = true
		}
	}
	return out, nil
}
func choice(v float64) float64 {
	if v <= 1 {
		return 0
	}
	if v == 2 {
		return 70
	}
	if v <= 5 {
		return 100
	}
	return max(50.0, 100-10*(v-5))
}
func width(v float64) float64 {
	if v < 2 {
		return 0
	}
	if v < 3 {
		return 70
	}
	if v <= 6 {
		return 100
	}
	return max(50.0, 100-10*(v-6))
}
func strengthScore(v []float64) float64 {
	if len(v) == 0 {
		return 0
	}
	return 100 * (.6*mean(v) + .4*minFloat(v))
}
func openingRatio(v float64) float64 {
	v = max(0.0, min(1.0, v))
	if v < .15 {
		return 100 * v / .15
	}
	if v <= .45 {
		return 100
	}
	return max(50.0, 100-50*(v-.45)/.55)
}
func (s *Sources) rankScores(r Object, game string) (int, int, error) {
	g := s.Graph
	sal := func(id string) float64 { return max(0.0, min(100.0, 100*g.Salience(id))) }
	f, q := 0, 0
	findings := s.Findings(r, game, nil)
	count := func(check string) int {
		n := 0
		for _, f := range findings {
			if str(f["check"]) == check {
				n++
			}
		}
		return n
	}
	generic := 0
	if s.regionFinding(r, game) {
		generic = 1
	}
	switch game {
	case "conexiuni":
		all := []float64{}
		best := 0.0
		for _, key := range keys(obj(r["groups"])) {
			ss := []float64{}
			for _, id := range members(r, key) {
				ss = append(ss, sal(id))
				all = append(all, sal(id))
			}
			best = max(best, mean(ss))
		}
		f = score(.6*mean(all) + .25*lowerQuartile(all) + .15*best)
		unfair, contested, raw := fairness(g, r)
		cross := 0
		strength := s.undirectedStrength()
		group := map[string]string{}
		for _, key := range keys(obj(r["groups"])) {
			for _, id := range members(r, key) {
				group[id] = key
			}
		}
		for a, ga := range group {
			for b, gb := range group {
				if a < b && ga != gb && strength[a][b] >= .6 {
					cross++
				}
			}
		}
		q = score(100 - float64(35*len(unfair)+8*max(0, len(contested)-1)+4*max(0, raw-2)+2*max(0, cross-4)+8*count("type_coherence")+12*count("mirrored_groups")+5*count("duplicate_groups")+15*generic))
	case "contexto":
		target := str(r["target"])
		strong := []string{}
		for _, id := range g.PredecessorIDs(target) {
			if edge := g.Link(id, target); edge != nil && edge.Strength >= .6 {
				strong = append(strong, id)
			}
		}
		sort.Slice(strong, func(i, j int) bool {
			a, b := g.Link(strong[i], target).Strength, g.Link(strong[j], target).Strength
			if a != b {
				return a > b
			}
			return strong[i] < strong[j]
		})
		if len(strong) > 10 {
			strong = strong[:10]
		}
		ss := []float64{}
		for _, id := range strong {
			ss = append(ss, sal(id))
		}
		f = score(.75*sal(target) + .25*mean(ss))
		q = score(.35*min(100.0, 20*float64(len(strong))) + .35*mean(ss) + .2*min(100.0, 12.5*float64(len(g.PredecessorIDs(target)))) + .1*min(100.0, 100*float64(len(g.DistancesTo(target)))/120) - 15*float64(generic))
	case "lant":
		start, target := str(r["start"]), str(r["target"])
		paths := s.rankPaths(start, target, integer(r["optimal"]))
		intermediate := map[string]bool{}
		strengths := []float64{}
		for _, path := range paths {
			for _, id := range path[1 : len(path)-1] {
				intermediate[id] = true
			}
			for i, a := range path[:len(path)-1] {
				edge := g.Link(a, path[i+1])
				if edge != nil {
					strengths = append(strengths, edge.Strength)
				}
			}
		}
		ss := []float64{}
		for id := range intermediate {
			ss = append(ss, sal(id))
		}
		f = score(.55*mean([]float64{sal(start), sal(target)}) + .25*min(sal(start), sal(target)) + .20*mean(ss))
		first, narrow, total := branch(g, start, target, integer(r["optimal"]))
		average := float64(total) / float64(max(1, integer(r["optimal"])-1))
		q = score(.30*choice(float64(first)) + .25*choice(float64(narrow)) + .20*width(average) + .25*strengthScore(strengths))
	case "alchimie":
		seeds, e := uniqueStrings(r["seeds"])
		if e != nil {
			return 0, 0, e
		}
		profile, e := s.RawCraft(seeds, str(r["target"]), str(r["category"]))
		if e != nil {
			return 0, 0, e
		}
		steps := array(obj(profile["recipe"])["steps"])
		ss := []float64{}
		excluded := map[string]bool{str(r["target"]): true}
		for _, id := range seeds {
			ss = append(ss, sal(id))
			excluded[id] = true
		}
		intermediate := map[string]bool{}
		strengths := []float64{}
		for index, v := range steps {
			step := obj(v)
			ids, _ := stringsOf(step["results"])
			required := map[string]bool{}
			for _, later := range steps[index+1:] {
				pair, _ := stringsOf(obj(later)["pair"])
				for _, id := range pair {
					required[id] = true
				}
			}
			required[str(r["target"])] = true
			sort.Slice(ids, func(i, j int) bool {
				a, b := required[ids[i]], required[ids[j]]
				if a != b {
					return a
				}
				if a {
					return ids[i] < ids[j]
				}
				if g.Salience(ids[i]) != g.Salience(ids[j]) {
					return g.Salience(ids[i]) > g.Salience(ids[j])
				}
				return ids[i] < ids[j]
			})
			requiredCount := 0
			for _, id := range ids {
				if required[id] {
					requiredCount++
				}
			}
			limit := max(6, requiredCount)
			if len(ids) > limit {
				ids = ids[:limit]
			}
			pair, _ := stringsOf(step["pair"])
			for _, id := range ids {
				if !excluded[id] {
					intermediate[id] = true
				}
				for _, parent := range pair {
					edge := g.Link(parent, id)
					st := 0.0
					if edge != nil {
						st = edge.Strength
					}
					strengths = append(strengths, st)
				}
			}
		}
		ints := []float64{}
		for id := range intermediate {
			ints = append(ints, sal(id))
		}
		f = score(.45*mean(ss) + .20*minFloat(ss) + .25*sal(str(r["target"])) + .10*mean(ints))
		openings := array(profile["openings"])
		counts := []float64{}
		for _, v := range openings {
			counts = append(counts, float64(len(array(obj(v)["results"]))))
		}
		sort.Slice(counts, func(i, j int) bool { return counts[i] > counts[j] })
		if len(counts) > 6 {
			counts = counts[:6]
		}
		noise := 0.0
		if len(counts) > 0 {
			noise = max(40.0, 100-10*max(0.0, mean(counts)-3))
		}
		ratio := float64(integer(obj(profile["profile"])["opening_pairs"])) / float64(len(seeds)*(len(seeds)-1)/2)
		band := map[string][2]int{"usor": {2, 2}, "normal": {2, 3}, "greu": {3, 5}}[str(r["difficulty"])]
		depth := integer(r["target_depth"])
		par := max(0.0, 100-30*float64(max(0, max(band[0]-depth, depth-band[1]))))
		q = score(.30*openingRatio(ratio) + .30*strengthScore(strengths) + .25*par + .15*noise)
	}
	return f, q, nil
}
func (s *Sources) rankPaths(start, target string, optimal int) [][]string {
	g := s.Graph
	to := g.DistancesTo(target)
	ordered := func(id string, remaining int) []string {
		out := []string{}
		for _, next := range g.NeighborIDs(id) {
			if d, ok := to[next]; ok && d == remaining-1 {
				out = append(out, next)
			}
		}
		sort.Slice(out, func(i, j int) bool {
			a, b := g.Link(id, out[i]).Strength, g.Link(id, out[j]).Strength
			if a != b {
				return a > b
			}
			return out[i] < out[j]
		})
		return out
	}
	var complete func(string, []string) []string
	complete = func(id string, path []string) []string {
		if id == target {
			return path
		}
		for _, next := range ordered(id, optimal-len(path)+1) {
			if route := complete(next, append(append([]string{}, path...), next)); route != nil {
				return route
			}
		}
		return nil
	}
	paths := [][]string{}
	first := ordered(start, optimal)
	if len(first) > 3 {
		first = first[:3]
	}
	for _, id := range first {
		if path := complete(id, []string{start, id}); path != nil {
			paths = append(paths, path)
		}
	}
	return paths
}
func (s *Sources) generateRankings() (Object, error) {
	holds, e := s.ownerHolds()
	if e != nil {
		return nil, e
	}
	rows := []Object{}
	byGame, eligibleBy := Object{}, Object{}
	approved, eligible := 0, 0
	for _, game := range Games {
		group := []Object{}
		for _, v := range array(s.Pack[game]) {
			r := obj(v)
			f, q, e := s.rankScores(r, game)
			if e != nil {
				return nil, fmt.Errorf("ranking %s: %w", r["id"], e)
			}
			allowed := str(r["status"]) == "approved" && !holds[str(r["id"])]
			if allowed {
				for _, f := range s.Findings(r, game, nil) {
					if str(f["level"]) == "FAIL" {
						allowed = false
					}
				}
			}
			row := Object{"id": r["id"], "game": game, "status": r["status"], "romanian_familiarity": f, "play_quality": q, "pilot_score": score(.6*float64(f) + .4*float64(q)), "rank": 0, "pilot_eligible": allowed, "selection_weight": 1}
			group = append(group, row)
			if str(r["status"]) == "approved" {
				approved++
			}
		}
		sort.Slice(group, func(i, j int) bool {
			if integer(group[i]["pilot_score"]) != integer(group[j]["pilot_score"]) {
				return integer(group[i]["pilot_score"]) > integer(group[j]["pilot_score"])
			}
			return str(group[i]["id"]) < str(group[j]["id"])
		})
		selected := []Object{}
		for i, r := range group {
			r["rank"] = i + 1
			if r["pilot_eligible"] == true {
				selected = append(selected, r)
			}
		}
		for i, r := range selected {
			r["selection_weight"] = 5 - min(4, 5*i/len(selected))
		}
		rows = append(rows, group...)
		byGame[game] = len(group)
		eligibleBy[game] = len(selected)
		eligible += len(selected)
	}
	return Object{"meta": Object{"schema_version": 1, "pack_sha256": textDigest(s.PackBytes), "kg_sha256": s.KGHash, "rubric_sha256": s.RubricHash, "counts": Object{"total": len(rows), "approved": approved, "pilot_eligible": eligible, "by_game": byGame, "eligible_by_game": eligibleBy}}, "boards": rows}, nil
}
func (s *Sources) Rank(write bool) (Object, error) {
	document, e := s.generateRankings()
	if e != nil {
		return nil, e
	}
	return s.sidecar(document, "board_rankings_v37.json", write)
}
