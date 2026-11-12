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

// Selector/data contracts only; no HTTP requests or combined qualification are
// inferred from registering the captured distinct V4 c10 corpus (1206 cases).
func v4c10ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "04d8d7121761bcd3986c3de382c5d40af37389e91d46b89b6ecf71b30142f6ff",
		"alchimie_recipe_extensions_v92.json": "b0a2e34ae4988a5eb3479db529e23e238dd54f8a999b66de270aca0a1a577020",
		"board_rankings_v37.json":             "f3e6e8978a2d6655f8b489dd24721d677c6601ee25c976b8484c1f441910e22c",
		"derived_catalog_v38.json":            "c7e090826fac787171a9a2c535f0b9acdb71bc0fc1a6cb04e518c0780659ab8b",
		"games_pack.json":                     "a28ea49639c4a23aeaf90116a7603ba0dba1a11d51e99acc029fe25fe2719645",
		"kg_sample.json":                      "8b8addd26cdc3aa5972a97368196e9593d5ef38477625f2fba988845e10879d4",
		"quick_games_v92.json":                "f243937f8c3bfff83a8deaa4ccc89a8153db4b4c30ff53b8c3cd66532166b7b6",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v4c10ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v4-c10.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "38476202a7bdbba33289028c2da03adfe255ee45e9494a2916547da5079872dd"
	if len(raw) != 33345 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V4C10SHA256 != digest {
		t.Fatal("literal independent corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "existing Django offline oracle versus native Go V4 c10 candidate 6cdacb83b8902f37d77d8656bc6981704a104a1a; archived capture_reference.py unchanged except three configuration lines" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, v4c10ExpectedSources()) {
		t.Fatal("exact independent eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestV4C10SelectsItsExactEightSourceCorpus(t *testing.T) {
	want := v4c10ReadExpectedCorpus(t)
	loaded, err := reviewedV4C10()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V4 c10 loader changed its independent captured responses", err)
	}
	sources := v4c10ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V4 c10 tuple selected different responses or changed its input", err)
	}
	// V4 c10 and V4 c9 each retain their own 1206-case capture;
	// distinctness is the exact source tuple.
	if reflect.DeepEqual(want.Sources, v4c9ReadExpectedCorpus(t).Sources) {
		t.Fatal("V4 c10 replaced its distinct V4 c9 predecessor tuple")
	}
}

func TestV4C10PreservesAllTwentyFiveHistoricalSelections(t *testing.T) {
	current := v4c10ReadExpectedCorpus(t)
	readers := append(source6GUIHistoricalReaders(),
		source6GUIHistoricalReader{"source6-gui", source6GUIRequalificationCorpus},
		source6GUIHistoricalReader{"v1-8", reviewedV18},
		source6GUIHistoricalReader{"v1-9", reviewedV19},
		source6GUIHistoricalReader{"v1-10", reviewedV110},
		source6GUIHistoricalReader{"v1-11", reviewedV111},
		source6GUIHistoricalReader{"v1-12", reviewedV112},
		source6GUIHistoricalReader{"v1-13", reviewedV113},
		source6GUIHistoricalReader{"v3-n1", reviewedV3N1},
		source6GUIHistoricalReader{"v3-n2", reviewedV3N2},
		source6GUIHistoricalReader{"v3-n4", reviewedV3N4},
		source6GUIHistoricalReader{"v4-c1", reviewedV4C1},
		source6GUIHistoricalReader{"v4-c2", reviewedV4C2},
		source6GUIHistoricalReader{"v4-c3", reviewedV4C3},
		source6GUIHistoricalReader{"v4-c4", reviewedV4C4},
		source6GUIHistoricalReader{"v4-c5", reviewedV4C5},
		source6GUIHistoricalReader{"v4-c6", reviewedV4C6},
		source6GUIHistoricalReader{"v4-c7", reviewedV4C7},
		source6GUIHistoricalReader{"v4-c8", reviewedV4C8},
		source6GUIHistoricalReader{"v4-c9", reviewedV4C9})
	if len(readers) != 25 {
		t.Fatal("historical selector set differs")
	}
	for _, row := range readers {
		t.Run(row.name, func(t *testing.T) {
			wantCases := 1207
			if row.name == "v1-13" || row.name == "v3-n1" || row.name == "v3-n2" || row.name == "v3-n4" || row.name == "v4-c1" || row.name == "v4-c2" || row.name == "v4-c3" || row.name == "v4-c4" || row.name == "v4-c5" || row.name == "v4-c6" || row.name == "v4-c7" || row.name == "v4-c8" || row.name == "v4-c9" {
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

func TestV4C10RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := v4c10ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := v4c10ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := v4c10ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := v4c10ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	// Both endpoints select positively above; all 62 proper mixtures of
	// V4 c10/V4 c9 refuse at the source boundary before HTTP.
	older := v4c9ReadExpectedCorpus(t)
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
		sources := v4c10ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-v4-c10-v4-c9-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
