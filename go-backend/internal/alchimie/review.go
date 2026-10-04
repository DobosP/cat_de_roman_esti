package alchimie

// ProjectionForReview runs the same bounded projection and extension rules used
// by games. The detached result is only for local content operators; HTTP never
// exposes it and a reviewer cannot mutate a memoized game recipe book.
func (s *Service) ProjectionForReview(seeds []string, target, category string) *Projection {
	p := s.projection(seeds, target, category)
	if p == nil {
		return nil
	}
	out := &Projection{Recipes: map[Pair][]string{}, Par: p.Par, CandidateQuality: append([][3]float64{}, p.CandidateQuality...)}
	for pair, outputs := range p.Recipes {
		out.Recipes[pair] = append([]string{}, outputs...)
	}
	for _, route := range p.Routes {
		cloned := Route{}
		for _, step := range route {
			cloned = append(cloned, Step{step.Pair, append([]string{}, step.Results...)})
		}
		out.Routes = append(out.Routes, cloned)
	}
	return out
}
