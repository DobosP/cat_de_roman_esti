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
// inferred from registering the captured distinct V4 c4 corpus (1206 cases).
func v4c4ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "85443bee8683e88c93e7c368e5a97134071968f557555cee4bcd9ce19495bd99",
		"alchimie_recipe_extensions_v92.json": "d3bdedc63273affd9695b991cfcb558ab3aebd249fa604fd8516fc94665ba42c",
		"board_rankings_v37.json":             "0259b62592399ff0bcd56cbf37f569ff5229c3fbe872bd260add7d812bd117a3",
		"derived_catalog_v38.json":            "2e5d3d795d66ee9009880aa3039e6310760ab650f36fd27579a744e345b52fdb",
		"games_pack.json":                     "99782a238dfc1c8e8912202d4836cad0a92c7c5a24bbe16cea80d2d2a2d2b3eb",
		"kg_sample.json":                      "8b8addd26cdc3aa5972a97368196e9593d5ef38477625f2fba988845e10879d4",
		"quick_games_v92.json":                "c6b0e91bb014acc257589ad7ab5f0fd6f4ca60c5ac134255ecadc888a34b87a9",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v4c4ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v4-c4.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "bd9109338ead1ad3ad07a9074f53770838aacafefee3a3dc76b40bd5a2549c34"
	if len(raw) != 33397 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V4C4SHA256 != digest {
		t.Fatal("literal independent corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "existing Django offline oracle versus native Go V4 c4 candidate 1d12d605429581659d522cffe7bd85563d9bc2ee; archived capture_reference.py unchanged except three configuration lines" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, v4c4ExpectedSources()) {
		t.Fatal("exact independent eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestV4C4SelectsItsExactEightSourceCorpus(t *testing.T) {
	want := v4c4ReadExpectedCorpus(t)
	loaded, err := reviewedV4C4()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V4 c4 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || len(data.Sources) != 8 || reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle did not move past the historical V4 c4 source tuple", err)
	}
	sources := v4c4ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V4 c4 tuple selected different responses or changed its input", err)
	}
	// V4 c4 and V4 c3 each retain their own 1206-case capture;
	// distinctness is the exact source tuple.
	if reflect.DeepEqual(want.Sources, v4c3ReadExpectedCorpus(t).Sources) {
		t.Fatal("V4 c4 replaced its distinct V4 c3 predecessor tuple")
	}
}

func TestV4C4PreservesAllNineteenHistoricalSelections(t *testing.T) {
	current := v4c4ReadExpectedCorpus(t)
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
		source6GUIHistoricalReader{"v4-c3", reviewedV4C3})
	if len(readers) != 19 {
		t.Fatal("historical selector set differs")
	}
	for _, row := range readers {
		t.Run(row.name, func(t *testing.T) {
			wantCases := 1207
			if row.name == "v1-13" || row.name == "v3-n1" || row.name == "v3-n2" || row.name == "v3-n4" || row.name == "v4-c1" || row.name == "v4-c2" || row.name == "v4-c3" {
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

func TestV4C4RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := v4c4ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := v4c4ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := v4c4ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := v4c4ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	// Both endpoints select positively above; all 62 proper mixtures of
	// V4 c4/V4 c3 refuse at the source boundary before HTTP.
	older := v4c3ReadExpectedCorpus(t)
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
		sources := v4c4ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-v4-c4-v4-c3-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
