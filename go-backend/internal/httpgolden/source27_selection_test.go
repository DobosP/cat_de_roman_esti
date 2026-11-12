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

// Selector/data contracts only. These tests do not replay HTTP journeys or
// qualify Source27 for native HTTP parity, GoFull, PG, GUI, or release.
func source27ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "7c9f9ff091d21e15e198c8a93917ab350962ac6a98fd66f9e1347287e068cf70",
		"alchimie_recipe_extensions_v92.json": "a93682f876ea22a614cdb6e31810867d00d557bbdcf3c8fa7a36bb5d9cdd25eb",
		"board_rankings_v37.json":             "28f16fdcb66a33830419e128f0522c04901b142166f1e8d7724292c19002ec0f",
		"derived_catalog_v38.json":            "6f2687c35f4927ded018bb321fbf84e567e7d652474c681fd7bea2d5afd25cf1",
		"games_pack.json":                     "a28ea49639c4a23aeaf90116a7603ba0dba1a11d51e99acc029fe25fe2719645",
		"kg_sample.json":                      "8b8addd26cdc3aa5972a97368196e9593d5ef38477625f2fba988845e10879d4",
		"quick_games_v92.json":                "2140b0a380f65ac05f9a8e3719118b6d9befe281d16ed87ddb4a77ead1e10840",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func source27ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v4-m3-stage5-recovery27.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "d5b42e701b0d0170addfbbbc66b56b9d2c26fa3aa4081843c786e4315f63236b"
	if len(raw) != 33314 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V4M3Stage5Recovery27SHA256 != digest {
		t.Fatal("literal independent Source27 corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "Independent current Loop Python/Django Source27 M3 stage5 recovery oracle; original retained 1206 C10 HTTP journeys reexecuted; no native or prior expected responses used" ||
		len(corpus.Cases) != 1206 || len(corpus.Sources) != 8 || !reflect.DeepEqual(corpus.Sources, source27ExpectedSources()) {
		t.Fatal("exact independent Source27 eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestSource27SelectsExactHistoricalIndependentCorpus(t *testing.T) {
	want := source27ReadExpectedCorpus(t)
	loaded, err := reviewedV4M3Stage5Recovery27()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("Source27 loader changed its independent captured responses", err)
	}
	sources := source27ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete Source27 tuple selected different responses or changed its input", err)
	}
}

func TestSource27PreservesAllTwentySixHistoricalSelectionsAndDistinctHeaders(t *testing.T) {
	current := source27ReadExpectedCorpus(t)
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
		source6GUIHistoricalReader{"v4-c9", reviewedV4C9},
		source6GUIHistoricalReader{"v4-c10", reviewedV4C10})
	if len(readers) != 26 {
		t.Fatal("historical selector set differs")
	}
	seen := map[string]map[string]string{"source27": current.Sources}
	for _, row := range readers {
		t.Run(row.name, func(t *testing.T) {
			wantCases := 1206
			switch row.name {
			case "initial", "v1-2", "v1-3", "v1-4", "v1-5", "v1-6", "source6-gui", "v1-8", "v1-9", "v1-10", "v1-11", "v1-12":
				wantCases = 1207
			}
			old, err := row.read()
			if err != nil {
				t.Fatal(err)
			}
			if len(old.Cases) != wantCases || len(old.Sources) != 8 {
				t.Fatal("historical source/count identity changed")
			}
			for name, sources := range seen {
				if reflect.DeepEqual(old.Sources, sources) {
					t.Fatal("distinct corpus source headers collapsed", row.name, name)
				}
			}
			seen[row.name] = source6GUICloneSources(old.Sources)
			sources := source6GUICloneSources(old.Sources)
			before := source6GUICloneSources(sources)
			selected, err := ForSources(sources)
			if err != nil || !reflect.DeepEqual(selected, old) || !reflect.DeepEqual(sources, before) {
				t.Fatal("old whole tuple lost its own independent responses or input identity", err)
			}
		})
	}
	if len(seen) != 27 {
		t.Fatal("expected 27 distinct complete source headers", len(seen))
	}
}

func TestSource27RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := source27ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := source27ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("empty-digest/"+name, func(t *testing.T) {
			sources := source27ExpectedSources()
			sources[name] = ""
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := source27ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := source27ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	t.Run("KG-only", func(t *testing.T) {
		source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{"kg_sample.json": current.Sources["kg_sample.json"]})
	})
	older := v4c10ReadExpectedCorpus(t)
	changed := make([]string, 0, 5)
	for _, name := range names {
		if current.Sources[name] != older.Sources[name] {
			changed = append(changed, name)
		}
	}
	if !reflect.DeepEqual(changed, []string{
		"alchimie_discovery_world_v92.json",
		"alchimie_recipe_extensions_v92.json",
		"board_rankings_v37.json",
		"derived_catalog_v38.json",
		"quick_games_v92.json",
	}) {
		t.Fatal("actual Source27/C10 source delta differs", changed)
	}
	// Both whole tuples select positively above. All 30 proper mixtures
	// refuse at the source boundary before HTTP.
	for mask := 1; mask < (1<<len(changed))-1; mask++ {
		sources := source27ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-source27-v4-c10-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
