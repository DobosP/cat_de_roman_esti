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
// inferred from registering the captured distinct V3 n4 corpus (1206 cases).
func v3n4ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "66f0feb170696c82b4b804d814059fd7a0c90f90579cd8b3990dd86853532b74",
		"alchimie_recipe_extensions_v92.json": "8e0325328d3f1297192a2f6f841820333c0d26cbac9493b5da2bb68a42e84850",
		"board_rankings_v37.json":             "c25e80d9e5a86a6b7c0480f5be5ba9af89b92d1f6b00109f409b6f9d66a9cffe",
		"derived_catalog_v38.json":            "b207b6e9d12442583e66d06a62912d935691cf3cd7fefcd4ee0415e99eacb003",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "8b8addd26cdc3aa5972a97368196e9593d5ef38477625f2fba988845e10879d4",
		"quick_games_v92.json":                "fad794767aeaae12ba7f1b7bccdde69f27ea25a319ae309d2835986a5134ae4c",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v3n4ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v3-n4.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "4c51141f73260267e56f4a91230306155b700bc0c304ddb7083af773a3d6ed38"
	if len(raw) != 33617 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V3N4SHA256 != digest {
		t.Fatal("literal independent corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "existing Django offline oracle versus native Go V3 n4 candidate 97a4b24d4c6f71c711b480d160bed9ae048a24c0; archived capture_reference.py unchanged except three configuration lines" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, v3n4ExpectedSources()) {
		t.Fatal("exact independent eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestV3N4SelectsItsExactEightSourceCorpus(t *testing.T) {
	want := v3n4ReadExpectedCorpus(t)
	loaded, err := reviewedV3N4()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V3 n4 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || !reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle does not have the actual V3 n4 source tuple", err)
	}
	sources := v3n4ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V3 n4 tuple selected different responses or changed its input", err)
	}
	// V3 n4 and V3 n2 each retain their own 1206-case capture;
	// distinctness is the exact source tuple.
	if reflect.DeepEqual(want.Sources, v3n2ReadExpectedCorpus(t).Sources) {
		t.Fatal("V3 n4 replaced its distinct V3 n2 predecessor tuple")
	}
}

func TestV3N4PreservesAllFifteenHistoricalSelections(t *testing.T) {
	current := v3n4ReadExpectedCorpus(t)
	readers := append(source6GUIHistoricalReaders(),
		source6GUIHistoricalReader{"source6-gui", source6GUIRequalificationCorpus},
		source6GUIHistoricalReader{"v1-8", reviewedV18},
		source6GUIHistoricalReader{"v1-9", reviewedV19},
		source6GUIHistoricalReader{"v1-10", reviewedV110},
		source6GUIHistoricalReader{"v1-11", reviewedV111},
		source6GUIHistoricalReader{"v1-12", reviewedV112},
		source6GUIHistoricalReader{"v1-13", reviewedV113},
		source6GUIHistoricalReader{"v3-n1", reviewedV3N1},
		source6GUIHistoricalReader{"v3-n2", reviewedV3N2})
	if len(readers) != 15 {
		t.Fatal("historical selector set differs")
	}
	for _, row := range readers {
		t.Run(row.name, func(t *testing.T) {
			wantCases := 1207
			if row.name == "v1-13" || row.name == "v3-n1" || row.name == "v3-n2" {
				wantCases = 1206
			}
			old, err := row.read()
			if err != nil || len(old.Cases) != wantCases || len(old.Sources) != 8 || reflect.DeepEqual(old.Sources, current.Sources) {
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

func TestV3N4RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := v3n4ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := v3n4ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := v3n4ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := v3n4ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	// Both endpoints select positively above; all 62 proper mixtures of
	// V3 n4/V3 n2 refuse at the source boundary before HTTP.
	older := v3n2ReadExpectedCorpus(t)
	changed := make([]string, 0, 6)
	for _, name := range names {
		if current.Sources[name] != older.Sources[name] {
			changed = append(changed, name)
		}
	}
	if len(changed) != 6 {
		t.Fatal("actual adjacent source delta differs", len(changed))
	}
	for mask := 1; mask < (1<<len(changed))-1; mask++ {
		sources := v3n4ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-v3-n4-v3-n2-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
