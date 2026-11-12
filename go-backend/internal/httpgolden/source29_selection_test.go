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

func source29ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "82c9aec2c4e3720de05e1a418f977f8766dad73a0d4176f72f74e21c528ef14a",
		"alchimie_recipe_extensions_v92.json": "3a6aa6b83119079e9d27e96b5e604c4f7d072dad90cb1db05293f64ca36df263",
		"board_rankings_v37.json":             "a972d688d078d8a16583063aba47610f1811509b99ac7cc3982b611384049957",
		"derived_catalog_v38.json":            "3bd4df8c1315bed18ae5f239cca2d0097430632d490d4fe34f71ac6367ef19a5",
		"games_pack.json":                     "f3cb301fc3ce16e9fcd9825d5ea39054ba68c9b37f063b7e9d41e20e5136bce2",
		"kg_sample.json":                      "8b8addd26cdc3aa5972a97368196e9593d5ef38477625f2fba988845e10879d4",
		"quick_games_v92.json":                "da6d82bbe29ace091ae72cbd3c5d3f5acf97c124a97fd73553752903105b99a8",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func source29ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v4-c44-source29.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "c6e835321b337e0df256d7897cfa8c25563f977342f4e74de6625e17fe3461f2"
	if len(raw) != 33364 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V4C44Source29SHA256 != digest {
		t.Fatal("literal independent Source29 corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "Independent current Loop Python/Django Source29 C44 oracle; original retained 1206 C10 HTTP journeys reexecuted; no native or prior expected responses used" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, source29ExpectedSources()) {
		t.Fatal("exact independent Source29 eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestSource29SelectsExactCurrentIndependentCorpus(t *testing.T) {
	want := source29ReadExpectedCorpus(t)
	loaded, err := reviewedV4C44Source29()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("Source29 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || !reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle does not have the actual Source29 source tuple", err)
	}
	sources := source29ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete Source29 tuple selected different responses or changed its input", err)
	}
	if len(reviewedSources) != 29 {
		t.Fatal("expected Source29 plus 28 historical selectors", len(reviewedSources))
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

func TestSource29RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := source29ReadExpectedCorpus(t)
	older := source28ReadExpectedCorpus(t)
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
			sources := source29ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("empty-digest/"+name, func(t *testing.T) {
			sources := source29ExpectedSources()
			sources[name] = ""
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := source29ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	if !reflect.DeepEqual(changed, []string{
		"alchimie_discovery_world_v92.json",
		"alchimie_recipe_extensions_v92.json",
		"board_rankings_v37.json",
		"derived_catalog_v38.json",
		"games_pack.json",
		"quick_games_v92.json",
	}) {
		t.Fatal("actual Source29/Source28 source delta differs", changed)
	}
	t.Run("extra", func(t *testing.T) {
		sources := source29ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	t.Run("KG-only", func(t *testing.T) {
		source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{"kg_sample.json": current.Sources["kg_sample.json"]})
	})
	for mask := 1; mask < (1<<len(changed))-1; mask++ {
		sources := source29ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-source29-source28-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
