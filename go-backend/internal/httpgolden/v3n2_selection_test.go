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
// inferred from registering the captured distinct V3 n2 corpus (1206 cases).
func v3n2ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "207aa0acaefcf76f82fa3107fce8bfd6eee3b958e0a65e7dcf223afc4beff231",
		"alchimie_recipe_extensions_v92.json": "f8bbcccfec38c0ccd64b14aaedd27ea3a997c6970017769fdb8727aa7f02edf9",
		"board_rankings_v37.json":             "8724518f73b4712a05bca1bf5ecbefc29061c66e6a773d592c6dbffecd268670",
		"derived_catalog_v38.json":            "1debab737c6c8fa3ad6f2acbbf6086751310d24d0600d83274d6ee51703017ae",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "7f185988ddc1437ce3923f4dfe0f4d1eda9ad98743e5d178b73f40eb113fec15",
		"quick_games_v92.json":                "ad73a0617e8bf7dee77776256860ac3f9abba2b2797ec826439b370127e74ef9",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v3n2ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v3-n2.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "765da7b46bbaa46ee8bf30bb73aa81c2f983b41b9e0abaab21f1b9705dd6467f"
	if len(raw) != 33617 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V3N2SHA256 != digest {
		t.Fatal("literal independent corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "existing Django offline oracle versus native Go V3 n2 candidate f2fade3e27d2923ca83f5bc44121220233e7e476; archived capture_reference.py unchanged except three configuration lines" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, v3n2ExpectedSources()) {
		t.Fatal("exact independent eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestV3N2SelectsItsExactEightSourceCorpus(t *testing.T) {
	want := v3n2ReadExpectedCorpus(t)
	loaded, err := reviewedV3N2()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V3 n2 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || !reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle does not have the actual V3 n2 source tuple", err)
	}
	sources := v3n2ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V3 n2 tuple selected different responses or changed its input", err)
	}
	// V3 n2 and V3 n1 each retain their own 1206-case capture;
	// distinctness is the exact source tuple.
	if reflect.DeepEqual(want.Sources, v3n1ReadExpectedCorpus(t).Sources) {
		t.Fatal("V3 n2 replaced its distinct V3 n1 predecessor tuple")
	}
}

func TestV3N2PreservesAllFourteenHistoricalSelections(t *testing.T) {
	current := v3n2ReadExpectedCorpus(t)
	readers := append(source6GUIHistoricalReaders(),
		source6GUIHistoricalReader{"source6-gui", source6GUIRequalificationCorpus},
		source6GUIHistoricalReader{"v1-8", reviewedV18},
		source6GUIHistoricalReader{"v1-9", reviewedV19},
		source6GUIHistoricalReader{"v1-10", reviewedV110},
		source6GUIHistoricalReader{"v1-11", reviewedV111},
		source6GUIHistoricalReader{"v1-12", reviewedV112},
		source6GUIHistoricalReader{"v1-13", reviewedV113},
		source6GUIHistoricalReader{"v3-n1", reviewedV3N1})
	if len(readers) != 14 {
		t.Fatal("historical selector set differs")
	}
	for _, row := range readers {
		t.Run(row.name, func(t *testing.T) {
			wantCases := 1207
			if row.name == "v1-13" || row.name == "v3-n1" {
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

func TestV3N2RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := v3n2ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := v3n2ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := v3n2ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := v3n2ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	// Both endpoints select positively above; all 62 proper mixtures of
	// V3 n2/V3 n1 refuse at the source boundary before HTTP.
	older := v3n1ReadExpectedCorpus(t)
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
		sources := v3n2ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-v3-n2-v3-n1-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
