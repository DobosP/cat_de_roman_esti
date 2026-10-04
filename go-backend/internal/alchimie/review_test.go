package alchimie

import (
	"reflect"
	"testing"
)

func TestReviewProjectionMatchesLiveAndCannotMutateCache(t *testing.T) {
	s := load(t)
	row := golden(t)["curated"].([]any)[0].(map[string]any)
	seeds, target, category := ids(row["seeds"]), row["target"].(string), row["category"].(string)
	p := s.ProjectionForReview(seeds, target, category)
	if p == nil {
		t.Fatal("review lost live projection")
	}
	expected := projectionValue(s.projection(seeds, target, category))
	if !reflect.DeepEqual(projectionValue(p), expected) {
		t.Fatal("review differs from live rules")
	}
	for pair, outputs := range p.Recipes {
		if len(outputs) > 0 {
			outputs[0] = "mutated"
		}
		delete(p.Recipes, pair)
	}
	if len(p.Routes) > 0 && len(p.Routes[0]) > 0 {
		p.Routes[0][0].Results = []string{"mutated"}
	}
	p.Par = -1
	if !reflect.DeepEqual(projectionValue(s.projection(seeds, target, category)), expected) {
		t.Fatal("review mutated cached gameplay projection")
	}
}
