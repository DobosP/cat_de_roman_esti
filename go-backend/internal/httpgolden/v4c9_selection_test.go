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
// inferred from registering the captured distinct V4 c9 corpus (1206 cases).
func v4c9ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "9e6549aea6fb8f0f392b40f57395334c7067117ce4ed0cf7d2150bb866c5aaea",
		"alchimie_recipe_extensions_v92.json": "120a1b3dddbbcc8c949b95d8ce6e0c2df338aff70d08f6c29b575a9f5883d200",
		"board_rankings_v37.json":             "023b1cac5003031a61a07ee1fa6b19e040af6bee57355cf73e3c2197b4b6b309",
		"derived_catalog_v38.json":            "b6916b2458b1a9e91d1ab9519f89ae545033d324adb30b7d2eb690884ca26338",
		"games_pack.json":                     "10d7eb4cc44ddb4728b48b907cf245c5f7f7a432c2719683e5f8d801a54defca",
		"kg_sample.json":                      "8b8addd26cdc3aa5972a97368196e9593d5ef38477625f2fba988845e10879d4",
		"quick_games_v92.json":                "a363ecbf4b719f027d773fc7fa1c0b77ed2e514d7ab922235128c75219e0e1cf",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v4c9ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v4-c9.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "59e18f54c6a4e13a20d88b9023188eb894a5d1611c84f054bfc2e13920a318bb"
	if len(raw) != 33343 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V4C9SHA256 != digest {
		t.Fatal("literal independent corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "existing Django offline oracle versus native Go V4 c9 candidate 70c30b2dc5e6be8cc1834aa1e8cac6a83cc0b000; archived capture_reference.py unchanged except three configuration lines" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, v4c9ExpectedSources()) {
		t.Fatal("exact independent eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestV4C9SelectsItsExactEightSourceCorpus(t *testing.T) {
	want := v4c9ReadExpectedCorpus(t)
	loaded, err := reviewedV4C9()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V4 c9 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || len(data.Sources) != 8 || reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle did not move past the historical V4 c9 source tuple", err)
	}
	sources := v4c9ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V4 c9 tuple selected different responses or changed its input", err)
	}
	// V4 c9 and V4 c8 each retain their own 1206-case capture;
	// distinctness is the exact source tuple.
	if reflect.DeepEqual(want.Sources, v4c8ReadExpectedCorpus(t).Sources) {
		t.Fatal("V4 c9 replaced its distinct V4 c8 predecessor tuple")
	}
}

func TestV4C9PreservesAllTwentyFourHistoricalSelections(t *testing.T) {
	current := v4c9ReadExpectedCorpus(t)
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
		source6GUIHistoricalReader{"v4-c8", reviewedV4C8})
	if len(readers) != 24 {
		t.Fatal("historical selector set differs")
	}
	for _, row := range readers {
		t.Run(row.name, func(t *testing.T) {
			wantCases := 1207
			if row.name == "v1-13" || row.name == "v3-n1" || row.name == "v3-n2" || row.name == "v3-n4" || row.name == "v4-c1" || row.name == "v4-c2" || row.name == "v4-c3" || row.name == "v4-c4" || row.name == "v4-c5" || row.name == "v4-c6" || row.name == "v4-c7" || row.name == "v4-c8" {
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

func TestV4C9RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := v4c9ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := v4c9ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := v4c9ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := v4c9ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	// Both endpoints select positively above; all 62 proper mixtures of
	// V4 c9/V4 c8 refuse at the source boundary before HTTP.
	older := v4c8ReadExpectedCorpus(t)
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
		sources := v4c9ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-v4-c9-v4-c8-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
