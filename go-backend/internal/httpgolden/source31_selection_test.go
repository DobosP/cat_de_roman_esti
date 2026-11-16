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
)

func source31ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "cf316348c35b7c1105e4dc6f832f975f96d6cfdc2517930bc3ffcf2e20c83281",
		"alchimie_recipe_extensions_v92.json": "51e3096a89014f384c75457d2b74c1ac60ca99a0e3952a1605d3b499f1244ff7",
		"board_rankings_v37.json":             "c1e6ad7b231f05c319d8d1b5a502105581d953ce310d9da43deaa8ccd5086ac5",
		"derived_catalog_v38.json":            "d4455166cb22d5df652d4134ef61a231d5d90c66513af065a23c176142e65ff2",
		"games_pack.json":                     "f3cb301fc3ce16e9fcd9825d5ea39054ba68c9b37f063b7e9d41e20e5136bce2",
		"kg_sample.json":                      "bb0993b5bff80a355dc7a5d966d11e7cd5c08346ae72d1afb0fcf0927304bc07",
		"quick_games_v92.json":                "33d3408f841dc7172f5aad8cee109b99692c79aab03f33d464917521431296cb",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func source31ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v5-p2-forms-1-source31.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "c70953212a7544bab7bc269209d2fb36f307f8c71aee880a5d32f2b155086708"
	if len(raw) != 33327 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V5Pilot2Forms1Source31SHA256 != digest {
		t.Fatal("literal independent Source31 corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "Independent V5 Pilot 2 seven-form rebuild Python/Django oracle; fixed 1206 anonymous journeys" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, source31ExpectedSources()) {
		t.Fatal("exact independent Source31 eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestSource31SelectsExactHistoricalIndependentCorpus(t *testing.T) {
	want := source31ReadExpectedCorpus(t)
	loaded, err := reviewedV5Pilot2Forms1Source31()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("Source31 loader changed its independent captured responses", err)
	}
	sources := source31ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete Source31 tuple selected different responses or changed its input", err)
	}
	legacyCount := 0
	for _, row := range reviewedSources {
		if row.version == 1 {
			legacyCount++
		}
	}
	if legacyCount != 31 {
		t.Fatal("expected Source31 plus 30 historical rules-1 selectors", legacyCount)
	}
	for _, row := range reviewedSources {
		if row.version == want.Version() && reflect.DeepEqual(row.sources, want.Sources) {
			continue
		}
		historical, err := row.load()
		if err != nil || !reflect.DeepEqual(row.sources, historical.Sources) {
			t.Fatal("historical loader no longer binds its exact sources", err)
		}
		selected, err := ForSourcesAndRules(row.sources, row.version)
		if err != nil || !reflect.DeepEqual(selected, historical) {
			t.Fatal("historical whole tuple selected different responses", err)
		}
	}
}

func TestSource31RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := source31ReadExpectedCorpus(t)
	older := source30ReadExpectedCorpus(t)
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
			sources := source31ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("empty-digest/"+name, func(t *testing.T) {
			sources := source31ExpectedSources()
			sources[name] = ""
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := source31ExpectedSources()
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
		t.Fatal("actual Source31/Source30 source delta differs", changed)
	}
	t.Run("extra", func(t *testing.T) {
		sources := source31ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	t.Run("KG-only", func(t *testing.T) {
		source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{"kg_sample.json": current.Sources["kg_sample.json"]})
	})
	for mask := 1; mask < (1<<len(changed))-1; mask++ {
		sources := source31ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-source31-source30-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
