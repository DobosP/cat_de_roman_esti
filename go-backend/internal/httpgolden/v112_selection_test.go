package httpgolden

import (
	"fmt"
	"reflect"
	"sort"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

// Selector/data contracts only; no HTTP requests or combined qualification are
// inferred from registering main's genuine distinct V1.11 and V1.12 corpora.
func v111ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "2bd3a1287a369c052a92e76dcf26f40711a82e3498242578e4fa7a11034e3f7c",
		"alchimie_recipe_extensions_v92.json": "b2f26c8205495a8be4d507784026f0973064d0f4caae074166d5c8e417c14183",
		"board_rankings_v37.json":             "b2d3e5395d174bace8767e8d1258067a286e4a3b917e892df1a0022bca416973",
		"derived_catalog_v38.json":            "0c2e458ff3f55c51d1a0fd84f4f8628dc6fcf32a71732f786e06257229db0482",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "fb3841b6b1d37078fa482541f6a148213af30a63157ef0e58bf67eeed78b61cd",
		"quick_games_v92.json":                "7235db2857785a01c829af90e9345702b1cc40c2f6fbf00ba703687fc3750813",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v112ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "c77c62cb28c6b4aae3b3e8c81aea50624cfd561b42d87b606b34f0b052922ad6",
		"alchimie_recipe_extensions_v92.json": "034cf54261de0eb0046c1b6751637c03a610a95da34aeb2681195a13d73d60a5",
		"board_rankings_v37.json":             "d2e9d8c4193947c0dd821b2bd4cdbf5938732f4257a3ddb1841e4d3c11b85e97",
		"derived_catalog_v38.json":            "ae801b16fe240b218ab035296b5d895b37c915ce701efaa68e754ed30ca65d56",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "9b4c056e16e9a18100f4e376e7b6ae5dd0d82bb0408367e4d940fea0798bd9c6",
		"quick_games_v92.json":                "26bda43974c528aa9f04074541f4b248777550a7d6174bd75a17cc57665fd88a",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v111ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	return v110ReadLiteralCorpus(t, "testdata/python-http-parity-v1-11.json.gz", 33593,
		"51655503ba618016e2ae3d3cc341639f1825864a8619761bc89635fa94bba600", V111SHA256,
		"Django application, reviewed V1.11 home-and-nature content at 61fe9a4795732d6c63774f40332ae55cee2b53a7", v111ExpectedSources())
}

func v112ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	return v110ReadLiteralCorpus(t, "testdata/python-http-parity-v1-12.json.gz", 33614,
		"b05affc8f80ab96513973444a6d7345123ffe5678c9dfd2c7b2839725eee01dc", V112SHA256,
		"Django application, V1.12 post-and-garden; archived scripts/check_go_parity.py at ae70c16935d402719b95405685bccbbbea13a3bd", v112ExpectedSources())
}

func TestV111SelectsItsExactEightSourceHistoricalCorpus(t *testing.T) {
	want := v111ReadExpectedCorpus(t)
	loaded, err := reviewedV111()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V1.11 loader changed its independent captured responses", err)
	}
	sources := v111ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V1.11 tuple selected different responses or changed its input", err)
	}
	v110RequireDistinctSuccessor(t, want, v110ReadExpectedCorpus(t), 23)
}

func TestV112SelectsItsExactEightSourceCorpus(t *testing.T) {
	want := v112ReadExpectedCorpus(t)
	loaded, err := reviewedV112()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V1.12 loader changed its independent captured responses", err)
	}
	// Main's reviewed V1.13 succeeded V1.12 (ed9932fa); like main's own
	// superseded tuples, V1.12 keeps its literal identity and selection while the
	// live-tuple clause moves to TestV113SelectsItsExactEightSourceCorpus.
	data, err := content.Load()
	if err != nil || len(data.Sources) != 8 || reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle did not move past the historical V1.12 source tuple", err)
	}
	sources := v112ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V1.12 tuple selected different responses or changed its input", err)
	}
	v110RequireDistinctSuccessor(t, want, v111ReadExpectedCorpus(t), 24)
}

func TestV112PreservesAllElevenHistoricalSelections(t *testing.T) {
	current := v112ReadExpectedCorpus(t)
	readers := append(source6GUIHistoricalReaders(),
		source6GUIHistoricalReader{"source6-gui", source6GUIRequalificationCorpus},
		source6GUIHistoricalReader{"v1-8", reviewedV18},
		source6GUIHistoricalReader{"v1-9", reviewedV19},
		source6GUIHistoricalReader{"v1-10", reviewedV110},
		source6GUIHistoricalReader{"v1-11", reviewedV111})
	if len(readers) != 11 {
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

func TestV112RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := v112ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := v112ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := v112ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := v112ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	// Each adjacent pair has two positive endpoint tests. All62 proper mixtures
	// of V1.12/V1.11 and of V1.11/V1.10 refuse at the source boundary before HTTP.
	for _, pair := range []struct {
		name      string
		newer     *Corpus
		newerSrcs func() map[string]string
		older     *Corpus
	}{
		{"v1-12-v1-11", current, v112ExpectedSources, v111ReadExpectedCorpus(t)},
		{"v1-11-v1-10", v111ReadExpectedCorpus(t), v111ExpectedSources, v110ReadExpectedCorpus(t)},
	} {
		changed := make([]string, 0, 6)
		for _, name := range names {
			if pair.newer.Sources[name] != pair.older.Sources[name] {
				changed = append(changed, name)
			}
		}
		if len(changed) != 6 {
			t.Fatal("actual adjacent source delta differs", pair.name)
		}
		for mask := 1; mask < (1<<len(changed))-1; mask++ {
			sources := pair.newerSrcs()
			for i, name := range changed {
				if mask&(1<<i) != 0 {
					sources[name] = pair.older.Sources[name]
				}
			}
			t.Run(fmt.Sprintf("mixed-%s-%d", pair.name, mask), func(t *testing.T) {
				source6GUIRequireRefusalWithoutRequests(t, pair.newer, sources)
			})
		}
	}
}
