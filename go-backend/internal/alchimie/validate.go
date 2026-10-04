package alchimie

// ValidateProposal certifies the same bounded native recipe projection used to
// serve a game. It never installs or publishes the submitted content.
func (s *Service) ValidateProposal(seeds []string, target, category string, depth int) []string {
	if len(seeds) < 5 || len(seeds) > 7 {
		return []string{"seeds must be 5-7 distinct node ids"}
	}
	seen := map[string]bool{}
	for _, id := range seeds {
		if seen[id] || !s.graph.Exists(id) {
			return []string{"seeds must be distinct known node ids"}
		}
		seen[id] = true
	}
	if !s.graph.Exists(target) || seen[target] {
		return []string{"target must be a known node outside seeds"}
	}
	p := s.projection(seeds, target, category)
	if p == nil {
		return []string{"target is not certified within the bounded recipe search"}
	}
	if depth != p.Par {
		return []string{"target_depth must equal the exact action par"}
	}
	openings := 0
	for i, a := range seeds {
		for _, b := range seeds[i+1:] {
			if len(p.Recipes[pair(a, b)]) > 0 {
				openings++
			}
		}
	}
	if openings < 2 {
		return []string{"seed set needs two opening pairs"}
	}
	return nil
}
