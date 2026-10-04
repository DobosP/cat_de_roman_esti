package browserplan

import (
	"encoding/json"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"os"
	"reflect"
	"testing"
)

func testContent(t *testing.T) *content.Content {
	t.Helper()
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	return c
}
func TestIndependentFrozenBrowserStartsAndWinningPlans(t *testing.T) {
	c := testContent(t)
	raw, err := os.ReadFile("../../../frontend/e2e/seeded-starts.json")
	if err != nil {
		t.Fatal(err)
	}
	var frozen map[string]any
	if err = json.Unmarshal(raw, &frozen); err != nil {
		t.Fatal(err)
	}
	for _, game := range Games {
		t.Run(game, func(t *testing.T) {
			p, err := Solution(c, game, "", "")
			if err != nil {
				t.Fatal(err)
			}
			if !reflect.DeepEqual(p.Initial, frozen[game]) {
				t.Fatalf("independent frozen %s start changed", game)
			}
			if len(p.Steps) == 0 || p.Practice.Action == "" {
				t.Fatal("incomplete journey")
			}
			if p.Initial["game_id"] != nil {
				t.Fatal("volatile session leaked into fixture")
			}
			if game == "alchimie" && len(p.HintSetup) < 6 {
				t.Fatal("missing bounded hint setup")
			}
		})
	}
}
func TestNamedPublicSeedsAndEveryReviewedCaptionRoute(t *testing.T) {
	c := testContent(t)
	p, err := Solution(c, "alchimie", "al_sport_083", "")
	if err != nil {
		t.Fatal(err)
	}
	if p.PackID != "al_sport_083" || p.Query["seed"] == "" {
		t.Fatal("named seed missing")
	}
	for _, id := range []string{"lt_geografie_239", "lt_literatura_240", "lt_gastronomie_241", "lt_gastronomie_243", "lt_gastronomie_244", "lt_gastronomie_245"} {
		t.Run(id, func(t *testing.T) {
			j, err := CaptionJourney(c, id)
			if err != nil {
				t.Fatal(err)
			}
			if len(j.Routes) < 2 || len(j.Routes) > MaxRoutes {
				t.Fatal("reviewed route count missing or unbounded")
			}
			for _, route := range j.Routes {
				for _, n := range route {
					if n.ID == "" || n.Label == "" {
						t.Fatal("incomplete caption route")
					}
				}
			}
		})
	}
}
func TestPlannerRefusesUnknownOrReservedNamedRounds(t *testing.T) {
	c := testContent(t)
	for _, args := range [][2]string{{"unknown", ""}, {"alchimie", "missing"}, {"lant", "missing"}, {"intrusul", "missing"}} {
		if _, err := Solution(c, args[0], args[1], ""); err == nil {
			t.Fatal("invalid fixture accepted")
		}
	}
}
