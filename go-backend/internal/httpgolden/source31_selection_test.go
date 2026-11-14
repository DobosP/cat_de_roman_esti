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

func source31ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "d26369715fb85badee083b190ddc1024e860c330a1553610fb5e2a8561c9c198",
		"alchimie_recipe_extensions_v92.json": "7c9de6c2cddf7c285444f66284d32d9825035e23538b13082ccc5a3cf91bed30",
		"board_rankings_v37.json":             "ae1aa0c11e758158b063d1a457d0bf7db6240463232a5b32a1b8db504a4cbe92",
		"derived_catalog_v38.json":            "dfb365cd02bcc67fbaea3141be34009d889c190a2bba6c550664ab1ca80e43b2",
		"games_pack.json":                     "f3cb301fc3ce16e9fcd9825d5ea39054ba68c9b37f063b7e9d41e20e5136bce2",
		"kg_sample.json":                      "f40ae9bfba72971c2d8ed719d599bb58c2ce4f0da04c0bb89ea3fd5dec02d3ed",
		"quick_games_v92.json":                "2b5db548c6dc346c3cb20c7337245df98e5e0fe9ca3db17518defb97e41cd2ac",
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
	const digest = "ca94badbb21734c9fc843a5f49eb37b6c547692ef353d444ef614dba7df83ec3"
	if len(raw) != 33321 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V5Pilot2Forms1Source31SHA256 != digest {
		t.Fatal("literal independent Source31 corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "Independent V5 Pilot 2 first forms train Python/Django oracle; fixed 1206 anonymous journeys" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, source31ExpectedSources()) {
		t.Fatal("exact independent Source31 eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestSource31SelectsExactCurrentIndependentCorpus(t *testing.T) {
	want := source31ReadExpectedCorpus(t)
	loaded, err := reviewedV5Pilot2Forms1Source31()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("Source31 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || !reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle does not have the actual Source31 source tuple", err)
	}
	sources := source31ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete Source31 tuple selected different responses or changed its input", err)
	}
	if len(reviewedSources) != 31 {
		t.Fatal("expected Source31 plus 30 historical selectors", len(reviewedSources))
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
