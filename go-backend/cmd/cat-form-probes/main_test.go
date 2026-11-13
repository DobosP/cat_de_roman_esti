package main

import (
	"slices"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

func TestNearUsesRuntimeDirection(t *testing.T) {
	proposed, typed := normalizedWord("atide"), normalizedWord("adiet")
	if near(proposed, typed, .5) || !near(typed, proposed, .5) {
		t.Fatal("SequenceRatio direction changed")
	}
	proposed, typed = normalizedWord("abcdefghi"), normalizedWord("abcdefgxy")
	if !near(proposed, typed, .77) || near(proposed, typed, suggestionFloor) {
		t.Fatal("did not use the exact threshold after upper bounds")
	}
	if !near(normalizedWord("abcdefghij"), normalizedWord("abcdefghxy"), suggestionFloor) ||
		near(normalizedWord("abcdefghij"), normalizedWord("abcdefghxy"), fuzzyFloor) {
		t.Fatal("suggestion-only neighbors are required")
	}
}

func TestPruningMatchesNativeRatio(t *testing.T) {
	words := []string{"a", "abc", "abac", "papa", "afinele", "afínele", "țest", "ab ba", strings.Repeat("a", 230)}
	for _, a := range words {
		for _, b := range words {
			for _, floor := range []float64{suggestionFloor, fuzzyFloor} {
				got := near(normalizedWord(a), normalizedWord(b), floor)
				if want := graph.SequenceRatio(a, b) >= floor; got != want {
					t.Errorf("%q, %q at %v: got %v want %v", a, b, floor, got, want)
				}
			}
		}
	}
}

func TestRawAccentsAndProfanity(t *testing.T) {
	data := &content.Content{
		Labels:                 map[string]string{"family": "familie"},
		NormalizationMap:       map[string]string{"ș": "s", "ş": "s", "\u0326": "", "ă": "a"},
		AccentNormalizationMap: map[string]string{"ș": "s\u0326", "ş": "s\u0327"},
		NormalizedIndex:        map[string]string{},
	}
	corpus := []string{"pasta", "paste", "pas\u0326te", "paşte", "paște"}
	slices.Sort(corpus)
	input := batch{
		UncoveredTitles:    []string{"pasta"},
		Proposals:          []proposal{{"one", "family", "paste"}, {"two", "family", "inventarului"}, {"three", "family", "întrebări"}},
		Profanity:          []string{"inventarului", "intrebari", "inventarul"},
		FrequencyWitnesses: []frequencyWitness{{"inventarului", "inventarului"}},
	}
	got, err := scan(data, input, corpus)
	if err != nil {
		t.Fatal(err)
	}
	if len(got.NearbyCoverageGaps) != 1 || got.NearbyCoverageGaps[0].Surface != "pasta" {
		t.Fatalf("nearby incomplete page coverage missing: %+v", got.NearbyCoverageGaps)
	}
	if got.Proposals[0].NearbyCount != len(corpus) || !got.Proposals[1].ProfanityExact || got.Proposals[2].ProfanityExact {
		t.Fatalf("proposal review differs: %+v", got.Proposals)
	}
	var unresolved []string
	for _, row := range got.Neighbors {
		if row.ReviewedUnresolved {
			unresolved = append(unresolved, row.Surface)
		}
	}
	if want := []string{"pas\u0326te", "paşte", "paște"}; !slices.Equal(unresolved, want) {
		t.Fatalf("different exact surfaces or unresolved status: %v", unresolved)
	}
	if !slices.ContainsFunc(got.UnsafeResolutions, func(row unsafeResolution) bool {
		return row.Probe == "inventarul" && row.AfterOwner == "family" &&
			slices.Equal(row.SingleFormChanges, []int{1})
	}) {
		t.Fatalf("missing newly resolved folded probe: %+v", got.UnsafeResolutions)
	}
}

func TestLongRelevantSurfaceIsReported(t *testing.T) {
	surface := strings.Repeat("ab", 128)
	data := &content.Content{Labels: map[string]string{"one": "one"}}
	input := batch{Proposals: []proposal{{"id", "one", surface}}, Profanity: []string{"witness"},
		FrequencyWitnesses: []frequencyWitness{{"witness", "witness"}}}
	got, err := scan(data, input, []string{surface + "a"})
	if err != nil {
		t.Fatal(err)
	}
	if len(got.Neighbors) != 0 || len(got.Unavailable) != 1 || got.Proposals[0].UnavailableCount != 1 {
		t.Fatalf("unavailable probe must be reported: %+v", got)
	}
	input.FrequencyWitnesses[0].Token = "different"
	if _, err = scan(data, input, []string{surface + "a"}); err == nil {
		t.Fatal("accepted mismatched exact frequency witness")
	}
}

func TestBaselineOwnerContenderAndSimultaneousChanges(t *testing.T) {
	data := &content.Content{
		Labels:          map[string]string{"old": "old", "one": "one", "two": "two"},
		NormalizedIndex: map[string]string{"abcdefghi": "old"},
	}
	probe := "abcdefghij"
	input := batch{
		Proposals: []proposal{{"one", "one", "abcdefghijk"}, {"two", "two", "abcdefghijl"}},
		Profanity: []string{probe}, FrequencyWitnesses: []frequencyWitness{{probe, probe}},
	}
	got, err := scan(data, input, []string{probe})
	if err != nil {
		t.Fatal(err)
	}
	// Both aliases would compete closely with the existing correctable typo.
	// A lost baseline resolution does not count as newly resolved.
	if len(got.UnsafeResolutions) != 0 {
		t.Fatalf("an owner loss is not a newly resolved probe: %+v", got.UnsafeResolutions)
	}
}
