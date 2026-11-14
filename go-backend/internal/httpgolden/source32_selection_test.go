package httpgolden

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"os"
	"reflect"
	"sort"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func source32ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "d78fb05bf0afa3f4eae34032c98618ebadc2cef10d73578c8323dc9088c57f71",
		"alchimie_recipe_extensions_v92.json": "c050a195e63f7a3a624f40fe1499c7bada0ceb832daa9e37effdbdb939a2b64f",
		"board_rankings_v37.json":             "12dd78d9ee38f460be13ebdcfc189962a13787acaded458ada2a1e02cddbe794",
		"derived_catalog_v38.json":            "f947a56e4cc6d73dae957aa0a3fbb29e71d23c2463e7ad72e16b09e1bef1b31a",
		"games_pack.json":                     "f3cb301fc3ce16e9fcd9825d5ea39054ba68c9b37f063b7e9d41e20e5136bce2",
		"kg_sample.json":                      "ca85e359cb67ed8fa572903ad528e480cc9dbdd65f97155464cb1c135da6e617",
		"quick_games_v92.json":                "d3fb57210e0e47d6ef00a1c0d09720ccdfd304b65bd2d2c4a00cb31b94b15a8b",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func source32ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v5-p2-mixed-1-source32.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "8d563be747927fb042abe1ffd2077a248e2ae767ce1a4af540c922355814b02c"
	if len(raw) != 33322 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V5Pilot2Mixed1Source32SHA256 != digest {
		t.Fatal("literal independent Source32 corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "Independent V5 Pilot 2 five-word train Python/Django oracle; fixed 1206 anonymous journeys" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, source32ExpectedSources()) {
		t.Fatal("exact independent Source32 eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestSource32SelectsExactCurrentIndependentCorpus(t *testing.T) {
	want := source32ReadExpectedCorpus(t)
	loaded, err := reviewedV5Pilot2Mixed1Source32()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("Source32 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || !reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle does not have the actual Source32 source tuple", err)
	}
	sources := source32ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete Source32 tuple selected different responses or changed its input", err)
	}
	if len(reviewedSources) != 32 {
		t.Fatal("expected Source32 plus 31 historical selectors", len(reviewedSources))
	}
	for _, row := range reviewedSources {
		if reflect.DeepEqual(row.sources, want.Sources) {
			continue
		}
		historical, err := row.load()
		if err != nil || !reflect.DeepEqual(row.sources, historical.Sources) {
			t.Fatal("historical loader no longer binds its exact sources", err)
		}
		selected, err := ForSources(row.sources)
		if err != nil || !reflect.DeepEqual(selected, historical) {
			t.Fatal("historical whole tuple selected different responses", err)
		}
	}
}

func TestSource32RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := source32ReadExpectedCorpus(t)
	older := source31ReadExpectedCorpus(t)
	names := make([]string, 0, len(current.Sources))
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	var changed []string
	for _, name := range names {
		if current.Sources[name] != older.Sources[name] {
			changed = append(changed, name)
		}
		t.Run("changed/"+name, func(t *testing.T) {
			sources := source32ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("empty-digest/"+name, func(t *testing.T) {
			sources := source32ExpectedSources()
			sources[name] = ""
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := source32ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	if !reflect.DeepEqual(changed, []string{
		"alchimie_discovery_world_v92.json",
		"alchimie_recipe_extensions_v92.json",
		"board_rankings_v37.json",
		"derived_catalog_v38.json",
		"kg_sample.json",
		"quick_games_v92.json",
	}) {
		t.Fatal("actual Source32/Source31 source delta differs", changed)
	}
	t.Run("extra", func(t *testing.T) {
		sources := source32ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	t.Run("KG-only", func(t *testing.T) {
		source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{"kg_sample.json": current.Sources["kg_sample.json"]})
	})
	for mask := 1; mask < (1<<len(changed))-1; mask++ {
		sources := source32ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-source32-source31-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
