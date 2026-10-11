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

// Selector/data contracts only; no HTTP requests or combined qualification are
// inferred from registering the genuine distinct V1.8 corpus.
func v18ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "dc0fd8737d3ed187c18f2ba246af524cb20ef2c9e0be35ed282b844decd7528a",
		"alchimie_recipe_extensions_v92.json": "ff14ada7e6a048012fc774fcbe8e4fbd57ed4ed2981d236eabc0ddd82964f063",
		"board_rankings_v37.json":             "538cf0db0e9141c3bbb4676404f136ab1faab0f06023dee86d207a0ee775c99c",
		"derived_catalog_v38.json":            "e4535a059c253fbf07911ec04e476a4e9725b52aa025faa4967ffbaa936adb7e",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "da14c34310eac3a03c2b5438c18043a2a7da682af9e0d991eb105c0639696c8f",
		"quick_games_v92.json":                "d3a50586c0983cb6f2f291f1b042041840b7403fabc330554977575f7866791b",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v18ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	raw, err := os.ReadFile("testdata/python-http-parity-v1-8.json.gz")
	if err != nil {
		t.Fatal(err)
	}
	if len(raw) != 33553 || fmt.Sprintf("%x", sha256.Sum256(raw)) != "2c02ee69ebdffd295f5ebe2f90a53276e4166cb39faecd3b14b51bb9e3d295ed" || V18SHA256 != "2c02ee69ebdffd295f5ebe2f90a53276e4166cb39faecd3b14b51bb9e3d295ed" {
		t.Fatal("literal independent V1.8 corpus bytes changed")
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "Django reference, V1.8 everyday-core content at 7d93fd6" || len(corpus.Cases) != 1207 || !reflect.DeepEqual(corpus.Sources, v18ExpectedSources()) {
		t.Fatal("exact independent V1.8 eight-source/1207-case provenance differs")
	}
	return corpus
}

func TestV18SelectsItsExactEightSourceCorpus(t *testing.T) {
	want := v18ReadExpectedCorpus(t)
	loaded, err := reviewedV18()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V1.8 loader changed its independent captured responses", err)
	}
	// Main's reviewed V1.10 succeeded V1.8 (ADR-0196); like main's own superseded
	// tuples, V1.8 keeps its literal identity and selection while the live-tuple
	// clause moves to TestV110SelectsItsExactEightSourceCorpus.
	data, err := content.Load()
	if err != nil || len(data.Sources) != 8 || reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle did not move past the historical V1.8 source tuple", err)
	}
	sources := v18ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V1.8 tuple selected different responses or changed its input", err)
	}
	old := source6GUIReadExpectedCorpus(t)
	if len(old.Cases) != len(want.Cases) || reflect.DeepEqual(old.Sources, want.Sources) {
		t.Fatal("V1.8 replaced the distinct GUI Source6 tuple")
	}
	changed := 0
	for i, record := range want.Cases {
		if !reflect.DeepEqual(record.Request, old.Cases[i].Request) || record.Status != old.Cases[i].Status {
			t.Fatal("captured ordered V1.8 requests/statuses differ from their retained history")
		}
		if !reflect.DeepEqual(record.Body, old.Cases[i].Body) {
			changed++
		}
	}
	if changed != 23 {
		t.Fatal("distinct captured V1.8 response-body delta differs")
	}
}

func TestV18PreservesAllSevenHistoricalSelections(t *testing.T) {
	current := v18ReadExpectedCorpus(t)
	readers := append(source6GUIHistoricalReaders(), source6GUIHistoricalReader{"source6-gui", source6GUIRequalificationCorpus})
	for _, row := range readers {
		t.Run(row.name, func(t *testing.T) {
			old, err := row.read()
			if err != nil || len(old.Cases) != 1207 || len(old.Sources) != 8 || reflect.DeepEqual(old.Sources, current.Sources) {
				t.Fatal("historical source/count identity changed", err)
			}
			sources := source6GUICloneSources(old.Sources)
			before := source6GUICloneSources(sources)
			selected, err := ForSources(sources)
			if err != nil || !reflect.DeepEqual(selected, old) || !reflect.DeepEqual(sources, before) {
				t.Fatal("old whole tuple lost its own independent responses or input identity", err)
			}
		})
	}
}

func TestV18RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := v18ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := v18ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := v18ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := v18ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	old := source6GUIReadExpectedCorpus(t)
	changed := make([]string, 0, 6)
	for _, name := range names {
		if current.Sources[name] != old.Sources[name] {
			changed = append(changed, name)
		}
	}
	if len(changed) != 6 {
		t.Fatal("actual V1.8 versus GUI Source6 source delta differs")
	}
	// The two complete endpoints have positive selection tests. All62 proper
	// mixtures must refuse at the unchanged source boundary before any request.
	for mask := 1; mask < (1<<len(changed))-1; mask++ {
		sources := v18ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = old.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-source6-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
