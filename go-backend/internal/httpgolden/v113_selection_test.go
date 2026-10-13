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
// inferred from registering main's genuine distinct V1.13 corpus (1206 cases).
func v113ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "2b4e18f8e5f231c0e94f30567366fe18a4d3677093f4fd590d0ecfebefb0cfff",
		"alchimie_recipe_extensions_v92.json": "fe3265069003aaca36cd9d7d1a1a49f2768374f6872e19b0ea53516670192dcd",
		"board_rankings_v37.json":             "7380a013c0ee14cd40c78b5469352346e945f42b90ca3a305fb17bc379cbad60",
		"derived_catalog_v38.json":            "6ede0ddfb44346bcd5595b08f4de7739aea64e0724f090ba6dd8d54059f525eb",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "d8c7a8226e7b128ef613aeeebedbd6af8529e5dd1d56676c3a8b1a6b86c886fc",
		"quick_games_v92.json":                "36bed57411692dbb714fc4978b7d8193d3012cf1bb2a2bf4e48e14a01d29af31",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v113ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v1-13.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "7423ca8b66969fbd10ac236b729eeb9f75982ec93a3a53965d8a86a24975e406"
	if len(raw) != 33564 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V113SHA256 != digest {
		t.Fatal("literal independent corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "Django application, V1.13 weather-and-landscape independently reviewed content" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, v113ExpectedSources()) {
		t.Fatal("exact independent eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestV113SelectsItsExactEightSourceCorpus(t *testing.T) {
	want := v113ReadExpectedCorpus(t)
	loaded, err := reviewedV113()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V1.13 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || !reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle does not have the actual V1.13 source tuple", err)
	}
	sources := v113ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V1.13 tuple selected different responses or changed its input", err)
	}
	// V1.13 captures 1206 cases against V1.12's 1207, so the equal-length
	// successor body delta does not apply; distinctness is the source tuple.
	if reflect.DeepEqual(want.Sources, v112ReadExpectedCorpus(t).Sources) {
		t.Fatal("V1.13 replaced its distinct V1.12 predecessor tuple")
	}
}

func TestV113PreservesAllTwelveHistoricalSelections(t *testing.T) {
	current := v113ReadExpectedCorpus(t)
	readers := append(source6GUIHistoricalReaders(),
		source6GUIHistoricalReader{"source6-gui", source6GUIRequalificationCorpus},
		source6GUIHistoricalReader{"v1-8", reviewedV18},
		source6GUIHistoricalReader{"v1-9", reviewedV19},
		source6GUIHistoricalReader{"v1-10", reviewedV110},
		source6GUIHistoricalReader{"v1-11", reviewedV111},
		source6GUIHistoricalReader{"v1-12", reviewedV112})
	if len(readers) != 12 {
		t.Fatal("historical selector set differs")
	}
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

func TestV113RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := v113ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := v113ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := v113ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := v113ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	// Both endpoints select positively above; all 62 proper mixtures of
	// V1.13/V1.12 refuse at the source boundary before HTTP.
	older := v112ReadExpectedCorpus(t)
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
		sources := v113ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-v1-13-v1-12-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
