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
// inferred from registering the captured distinct V4 c8 corpus (1206 cases).
func v4c8ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "6e4693e31c995f613c5f90a1388cdd5e5e712924d9f78a6e717be923f92aaef7",
		"alchimie_recipe_extensions_v92.json": "cbbf6d795e78e26fbc21c7ce715cb7323266ddaf2775ac498ac4e3a5cad1000b",
		"board_rankings_v37.json":             "4e907e6e7c1f6ca975ddb19b6833430836bd527ac6cef3188d802ed785bd9977",
		"derived_catalog_v38.json":            "19879c0a00fb91d9a44a5a6a067ced7e7f6d6a5025900eecacef41cb51d14a69",
		"games_pack.json":                     "70a9b92b0b93f865a28d25c55b997d26a2234db33f0f60210a356b6122bdfe88",
		"kg_sample.json":                      "8b8addd26cdc3aa5972a97368196e9593d5ef38477625f2fba988845e10879d4",
		"quick_games_v92.json":                "7989fd6a283e0ddfaa5d19cffcbcd948e3bd3915e33e19d20c5cce18a2cd19d6",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v4c8ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v4-c8.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "a144a21a42005efebe83428c1035efb9ef2d80076d3468d107112593c3e24190"
	if len(raw) != 33317 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V4C8SHA256 != digest {
		t.Fatal("literal independent corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "existing Django offline oracle versus native Go V4 c8 candidate cdb42b2aa779c3149a9c4fe5aaa60c33bdc611c8; archived capture_reference.py unchanged except three configuration lines" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, v4c8ExpectedSources()) {
		t.Fatal("exact independent eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestV4C8SelectsItsExactEightSourceCorpus(t *testing.T) {
	want := v4c8ReadExpectedCorpus(t)
	loaded, err := reviewedV4C8()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V4 c8 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || !reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle does not have the actual V4 c8 source tuple", err)
	}
	sources := v4c8ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V4 c8 tuple selected different responses or changed its input", err)
	}
	// V4 c8 and V4 c7 each retain their own 1206-case capture;
	// distinctness is the exact source tuple.
	if reflect.DeepEqual(want.Sources, v4c7ReadExpectedCorpus(t).Sources) {
		t.Fatal("V4 c8 replaced its distinct V4 c7 predecessor tuple")
	}
}

func TestV4C8PreservesAllTwentyThreeHistoricalSelections(t *testing.T) {
	current := v4c8ReadExpectedCorpus(t)
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
		source6GUIHistoricalReader{"v4-c7", reviewedV4C7})
	if len(readers) != 23 {
		t.Fatal("historical selector set differs")
	}
	for _, row := range readers {
		t.Run(row.name, func(t *testing.T) {
			wantCases := 1207
			if row.name == "v1-13" || row.name == "v3-n1" || row.name == "v3-n2" || row.name == "v3-n4" || row.name == "v4-c1" || row.name == "v4-c2" || row.name == "v4-c3" || row.name == "v4-c4" || row.name == "v4-c5" || row.name == "v4-c6" || row.name == "v4-c7" {
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

func TestV4C8RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := v4c8ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := v4c8ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := v4c8ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := v4c8ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	// Both endpoints select positively above; all 62 proper mixtures of
	// V4 c8/V4 c7 refuse at the source boundary before HTTP.
	older := v4c7ReadExpectedCorpus(t)
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
		sources := v4c8ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-v4-c8-v4-c7-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
