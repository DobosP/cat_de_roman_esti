package contentops

import "github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"

// ConexiuniFairnessForReview applies the native content screen to the groups
// in a served board payload. It uses directed, non-distractor neighbors.
func ConexiuniFairnessForReview(g *graph.Service, payload Object) Object {
	unfair, contested, raw := fairness(g, payload)
	return Object{"unfair": unfair, "contested": contested, "raw_unfair_count": raw}
}
