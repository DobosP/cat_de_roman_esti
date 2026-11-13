package contentops

import (
	"bytes"
	"errors"
	"fmt"
	"maps"
	"path/filepath"
	"reflect"
	"slices"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

// BoardViewPreview rebuilds the baseline and prospective board catalogs without
// writing sidecars. The original reviewed stock and reserve come from root.
func BoardViewPreview(root string, baseline *content.Content, prospective *graph.Service, kgHash string, packBytes []byte) (_ *content.Content, err error) {
	s, err := LoadSources(root)
	if err != nil {
		return nil, err
	}
	defer func() { err = errors.Join(err, checkSnapshots(s.Inputs), s.checkInventory()) }()
	if s.RubricHash != contentbuild.RubricSHA256 || s.KGHash != baseline.Sources["kg_sample.json"] ||
		textDigest(s.PackBytes) != baseline.Sources["games_pack.json"] {
		return nil, errors.New("baseline source pack, graph or rubric binding differs")
	}
	oldPack, err := Decode(s.PackBytes)
	if err != nil {
		return nil, err
	}
	newPack, err := Decode(packBytes)
	if err != nil {
		return nil, err
	}
	if err := validateSourcePackEnvelope(newPack); err != nil {
		return nil, err
	}
	for _, name := range []string{"board_demotions_v43.json", "contexto_demotions_v44.json", "contexto_impact_reserve_v69.json"} {
		if err := s.bindInput(filepath.Join(s.Root, fixtures+name)); err != nil {
			return nil, err
		}
	}
	authority := map[string]Object{}
	for _, name := range []string{"board_rankings_v37.json", "derived_catalog_v38.json", "quick_games_v92.json", "release_reserve_v1.json", "alchimie_recipe_extensions_v92.json"} {
		snapshot := s.Inputs[filepath.Join(s.Root, fixtures+name)]
		if !snapshot.exists || textDigest(snapshot.blob) != baseline.Sources[name] {
			return nil, fmt.Errorf("baseline %s binding differs", name)
		}
		authority[name], err = Decode(snapshot.blob)
		if err != nil {
			return nil, err
		}
	}
	oldGraph := s.Graph
	s.Pack = oldPack
	originalRanks, err := s.generateRankings()
	if err != nil {
		return nil, err
	}
	if !bytes.Equal(canonical(originalRanks), canonical(authority["board_rankings_v37.json"])) {
		return nil, errors.New("native baseline ranking differs from sealed source")
	}
	originalDerived, err := s.generateDerived()
	if err != nil {
		return nil, err
	}
	if !bytes.Equal(canonical(originalDerived), canonical(authority["derived_catalog_v38.json"])) {
		return nil, errors.New("native baseline V38 derivation differs from sealed source")
	}
	quick, reserve := authority["quick_games_v92.json"], authority["release_reserve_v1.json"]
	extensions := authority["alchimie_recipe_extensions_v92.json"]
	if err := contentbuild.ValidateRecipeExtensions(extensions); err != nil {
		return nil, err
	}
	if err := contentbuild.BoardViewCatalogs(oldGraph, oldPack, Object{"boards": array(originalRanks["boards"])}, authority["derived_catalog_v38.json"], quick, reserve, extensions); err != nil {
		return nil, err
	}
	if err := baselineParity(baseline, oldGraph.Content); err != nil {
		return nil, err
	}
	if invalid := contentbuild.ValidatePackObjectsFromGraph(prospective, newPack); len(invalid) != 0 {
		return nil, fmt.Errorf("prospective pack: %s", invalid[0])
	}
	if err := checkReDerivedPack(oldPack, newPack, prospective); err != nil {
		return nil, err
	}
	s.Pack, s.PackBytes, s.Graph, s.KGHash = newPack, packBytes, prospective, kgHash
	ranks, err := s.generateRankings()
	if err != nil {
		return nil, err
	}
	derived, err := s.generateDerived()
	if err != nil {
		return nil, err
	}
	if err := contentbuild.BoardViewCatalogs(prospective, newPack, Object{"boards": array(ranks["boards"])}, Object{"boards": array(derived["boards"])}, quick, reserve, extensions); err != nil {
		return nil, err
	}
	return prospective.Content, nil
}

func baselineParity(want, got *content.Content) error {
	for _, field := range []struct {
		name string
		want any
		got  any
	}{
		{"nodes", want.Nodes, got.Nodes},
		{"edges", want.Edges, got.Edges},
		{"labels", want.Labels, got.Labels},
		{"normalized index", want.NormalizedIndex, got.NormalizedIndex},
		{"category labels", want.CategoryLabels, got.CategoryLabels},
		{"label patterns", want.LabelPatterns, got.LabelPatterns},
		{"Lanț captions", want.LantCaptions, got.LantCaptions},
		{"Cald rules", want.ContextoData, got.ContextoData},
		{"Alchimie recipe extensions", want.RecipeExtensions, got.RecipeExtensions},
		{"normalization", want.NormalizationMap, got.NormalizationMap},
		{"accent normalization", want.AccentNormalizationMap, got.AccentNormalizationMap},
		{"casefold", want.CasefoldMap, got.CasefoldMap},
		{"approved pack", want.PackItems, got.PackItems},
		{"serving Quick", want.Boards, got.Boards},
	} {
		if !reflect.DeepEqual(field.want, field.got) {
			return fmt.Errorf("native baseline %s differs from exact bundle", field.name)
		}
	}
	return nil
}

func checkReDerivedPack(before, after Object, g *graph.Service) error {
	old, oldGames, err := indexPack(before)
	if err != nil {
		return err
	}
	current, games, err := indexPack(after)
	if err != nil {
		return err
	}
	if !reflect.DeepEqual(obj(before["meta"])["id_high_water"], obj(after["meta"])["id_high_water"]) {
		return errors.New("one-word candidate changed the pack ID high-water")
	}
	for _, id := range boardIDsSorted(current) {
		if old[id] == nil || oldGames[id] != games[id] {
			return fmt.Errorf("one-word candidate introduced or moved board %s", id)
		}
	}
	s := &Sources{Graph: g}
	for _, id := range boardIDsSorted(old) {
		game, row := oldGames[id], old[id]
		expected := copyObject(row)
		switch game {
		case "lant":
			length, reachable := g.Distance(str(row["start"]), str(row["target"]))
			band := oneWordBand(length, str(row["difficulty"]), [3][2]int{{2, 3}, {3, 4}, {4, 6}})
			if !reachable || band == "" {
				expected = nil
			} else {
				expected["difficulty"], expected["optimal"] = band, length
			}
		case "alchimie":
			seeds, _ := stringsOf(row["seeds"])
			profile, err := s.RawCraft(seeds, str(row["target"]), str(row["category"]))
			if err != nil {
				if current[id] != nil {
					return fmt.Errorf("candidate retained %s without a native craft result: %w", id, err)
				}
				expected = nil
			} else {
				mechanics := obj(profile["profile"])
				band := oneWordBand(integer(mechanics["target_generation"]), str(row["difficulty"]), [3][2]int{{2, 2}, {2, 3}, {3, 5}})
				if band == "" || integer(mechanics["opening_pairs"]) < 2 {
					expected = nil
				} else {
					expected["difficulty"], expected["target_depth"] = band, obj(profile["recipe"])["exact_actions"]
				}
			}
		}
		if expected != nil && (len(contentbuild.ValidateEnvelope(game, expected)) > 0 ||
			expected["status"] == "approved" && len(contentbuild.ValidatePayload(g, game, expected)) > 0) {
			expected = nil
		}
		if !bytes.Equal(canonical(expected), canonical(current[id])) {
			return fmt.Errorf("candidate pack rederivation differs from native graph mechanics for %s/%s", game, id)
		}
	}
	return nil
}

func oneWordBand(actual int, declared string, bounds [3][2]int) string {
	options := []string{"usor", "normal", "greu"}
	fallback := ""
	for i, band := range options {
		if actual < bounds[i][0] || actual > bounds[i][1] {
			continue
		}
		if band == declared {
			return declared
		}
		if fallback == "" {
			fallback = band
		}
	}
	return fallback
}

func boardIDsSorted(rows map[string]Object) []string {
	return slices.Sorted(maps.Keys(rows))
}
