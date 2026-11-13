package contexto

import (
	"encoding/json"
	"fmt"
	"sort"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

// BoardGuess is the native feedback for an exact KG concept.
type BoardGuess struct {
	ID          string `json:"id"`
	Label       string `json:"label"`
	Distance    int    `json:"distance"`
	Rank        int    `json:"rank"`
	Closeness   int    `json:"closeness"`
	Temperature string `json:"temperature"`
}

// BoardTopForReview uses the same score and rank tiebreaks as a live board.
// Projection terms and fuzzy aliases are alternate inputs, not KG concepts.
func (s *Service) BoardTopForReview(target string) ([]BoardGuess, int) {
	v := s.build(target, "", nil, "")
	top := make([]BoardGuess, 0, v.Profile.Reachable)
	for _, id := range s.g.AllIDs() {
		sc := s.score(v, id, false, 0)
		if sc.Reachable {
			top = append(top, BoardGuess{id, s.g.Label(id), sc.Distance, sc.Rank, closeness(v, sc), temperature(v, sc)})
		}
	}
	sort.Slice(top, func(i, j int) bool {
		a, b := top[i], top[j]
		if a.Rank != b.Rank {
			return a.Rank < b.Rank
		}
		if a.Distance != b.Distance {
			return a.Distance < b.Distance
		}
		if a.Closeness != b.Closeness {
			return a.Closeness > b.Closeness
		}
		if a.Label != b.Label {
			return a.Label < b.Label
		}
		return a.ID < b.ID
	})
	return top[:min(100, len(top))], v.Profile.Reachable
}

// ValidateBoardReviewRules checks the typed rules before an offline operator
// constructs a service from an externally supplied bundle.
func ValidateBoardReviewRules(c *content.Content) error {
	raw, err := json.Marshal(c.ContextoData)
	if err != nil {
		return err
	}
	var data privateData
	if err := json.Unmarshal(raw, &data); err != nil {
		return fmt.Errorf("invalid Cald rules: %w", err)
	}
	if data.Terms == nil || data.Neighborhoods == nil || data.Proxies == nil || data.Ingredients == nil || data.Pairs == nil {
		return fmt.Errorf("missing Cald rules")
	}
	for _, pair := range data.Pairs {
		if len(pair) != 2 {
			return fmt.Errorf("invalid Cald exact pair")
		}
	}
	return nil
}
