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
// inferred from registering the captured distinct V4 c6 corpus (1206 cases).
func v4c6ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "6c9a3fe9e013ba6f78728fb4afa04c001ea11e5b4a39e5c95a7e62da8de85104",
		"alchimie_recipe_extensions_v92.json": "aaf11d4f396295cace4dd89d5cf507956fa790ca6337c1918a862148ee5a3ef1",
		"board_rankings_v37.json":             "cf425b13bf3c0ee2dbb67657946679873db87f35ca3d6e0920b5777e32e97ac7",
		"derived_catalog_v38.json":            "0ef89b887bfd1f690a5fefb8a36c4b1d5bf78d455395aa42dfa702eebefab811",
		"games_pack.json":                     "c7ce2da27b80f683392696bdb212fc7e80d24a5cc834f343454fb7a51a29f64c",
		"kg_sample.json":                      "8b8addd26cdc3aa5972a97368196e9593d5ef38477625f2fba988845e10879d4",
		"quick_games_v92.json":                "a86c143b7261113810bfdc136fd92792f50cab8647d8f2a176479af3803274e9",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v4c6ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v4-c6.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "d1153cb5de65c5d987fc127675baad0a2ca4d17b989e7f1a7bc1c7acf9ef38d9"
	if len(raw) != 33373 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V4C6SHA256 != digest {
		t.Fatal("literal independent corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "existing Django offline oracle versus native Go V4 c6 candidate 05112dbe275971ccbeb635128c9d0d19571b8cdb; archived capture_reference.py unchanged except three configuration lines" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, v4c6ExpectedSources()) {
		t.Fatal("exact independent eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestV4C6SelectsItsExactEightSourceCorpus(t *testing.T) {
	want := v4c6ReadExpectedCorpus(t)
	loaded, err := reviewedV4C6()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V4 c6 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || !reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle does not have the actual V4 c6 source tuple", err)
	}
	sources := v4c6ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V4 c6 tuple selected different responses or changed its input", err)
	}
	// V4 c6 and V4 c5 each retain their own 1206-case capture;
	// distinctness is the exact source tuple.
	if reflect.DeepEqual(want.Sources, v4c5ReadExpectedCorpus(t).Sources) {
		t.Fatal("V4 c6 replaced its distinct V4 c5 predecessor tuple")
	}
}

func TestV4C6PreservesAllTwentyOneHistoricalSelections(t *testing.T) {
	current := v4c6ReadExpectedCorpus(t)
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
		source6GUIHistoricalReader{"v4-c5", reviewedV4C5})
	if len(readers) != 21 {
		t.Fatal("historical selector set differs")
	}
	for _, row := range readers {
		t.Run(row.name, func(t *testing.T) {
			wantCases := 1207
			if row.name == "v1-13" || row.name == "v3-n1" || row.name == "v3-n2" || row.name == "v3-n4" || row.name == "v4-c1" || row.name == "v4-c2" || row.name == "v4-c3" || row.name == "v4-c4" || row.name == "v4-c5" {
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

func TestV4C6RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := v4c6ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := v4c6ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := v4c6ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := v4c6ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	// Both endpoints select positively above; all 62 proper mixtures of
	// V4 c6/V4 c5 refuse at the source boundary before HTTP.
	older := v4c5ReadExpectedCorpus(t)
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
		sources := v4c6ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-v4-c6-v4-c5-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
