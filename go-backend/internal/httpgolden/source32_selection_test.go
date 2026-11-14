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
		"alchimie_discovery_world_v92.json":   "15ea311bc2689737ae3b76c3e27358eb350d4d00fe3145bcd1ab6ab8740dfe5b",
		"alchimie_recipe_extensions_v92.json": "dc2c611077cb442c28fd86466253097c1bafe17a3b8e3dfe5880fa5ae58032ab",
		"board_rankings_v37.json":             "a139daa4bf5496902f60cfcbd27a0053d0950ebef818a8ae1d4a04083acf8b1d",
		"derived_catalog_v38.json":            "120ecb95aee7bf7ac3e1ad8f30f0033d377dd92f8085826942426cde2be0a1d1",
		"games_pack.json":                     "f3cb301fc3ce16e9fcd9825d5ea39054ba68c9b37f063b7e9d41e20e5136bce2",
		"kg_sample.json":                      "1c6e504326e91bf92d3c2c5d8bf1d5cfe74d43aa81939305ca65d7d2f0c9bed1",
		"quick_games_v92.json":                "826317b2c1e6f6c0eacc8c0c5773842e555a8ebb6db97a8d60c72573ce4cf935",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func source32ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v5-p2-word-sparanghel-source32.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "a102fa53ead69dcc47b65e5e9167997ae1ed22e6656651cd654c04b70634f93d"
	if len(raw) != 33319 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V5Pilot2SparanghelSource32SHA256 != digest {
		t.Fatal("literal independent Source32 corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "Independent V5 Pilot 2 Sparanghel Python/Django oracle; fixed 1206 anonymous journeys" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, source32ExpectedSources()) {
		t.Fatal("exact independent Source32 eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestSource32SelectsExactCurrentIndependentCorpus(t *testing.T) {
	want := source32ReadExpectedCorpus(t)
	loaded, err := reviewedV5Pilot2SparanghelSource32()
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
