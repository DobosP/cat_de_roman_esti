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

func source30ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "ac509b62ebac174ae3352d26bf08ffd4f8b68bb1f8cb61df694951b3e0018b8c",
		"alchimie_recipe_extensions_v92.json": "e29c463d9eee9ab56d15929edfca5ae78905b59f21fc936a75daf61d1e4a858d",
		"board_rankings_v37.json":             "0437e07b4b31668d790481084b363df5c8c84890ea5b4d27355040063443502f",
		"derived_catalog_v38.json":            "e29c2fea2ac1f934c5eda60c071f4090f9e662a2e0acb3e6fa7f03d79adcb96d",
		"games_pack.json":                     "f3cb301fc3ce16e9fcd9825d5ea39054ba68c9b37f063b7e9d41e20e5136bce2",
		"kg_sample.json":                      "9ab0f376a4048c198b9497cf9ea675766e7300f6c55d8d54747f41fe032fbcc2",
		"quick_games_v92.json":                "f9499c795e5c08ab09f7067ce9945c35b21fedd8ef744c97d92fc065a23e5204",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func source30ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v5-forms-1-source30.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "6013a42a2df2f13e3367cf64cccfedaa099d8343c50138304c2c683da334aba9"
	if len(raw) != 33336 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V5Forms1Source30SHA256 != digest {
		t.Fatal("literal independent Source30 corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "Independent V5 Source30 Usturoi-only Python/Django oracle; fixed 1206 anonymous journeys" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, source30ExpectedSources()) {
		t.Fatal("exact independent Source30 eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestSource30SelectsExactCurrentIndependentCorpus(t *testing.T) {
	want := source30ReadExpectedCorpus(t)
	loaded, err := reviewedV5Forms1Source30()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("Source30 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || !reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle does not have the actual Source30 source tuple", err)
	}
	sources := source30ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete Source30 tuple selected different responses or changed its input", err)
	}
	if len(reviewedSources) != 30 {
		t.Fatal("expected Source30 plus 29 historical selectors", len(reviewedSources))
	}
	for _, row := range reviewedSources {
		if reflect.DeepEqual(row.sources, want.Sources) {
			continue
		}
		historical, err := row.load()
		if err != nil || !reflect.DeepEqual(row.sources, historical.Sources) {
			t.Fatal("historical loader no longer binds its exact sources", err)
		}
		selected, err := ForSources(row.sources)
		if err != nil || !reflect.DeepEqual(selected, historical) {
			t.Fatal("historical whole tuple selected different responses", err)
		}
	}
}

func TestSource30RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := source30ReadExpectedCorpus(t)
	older := source29ReadExpectedCorpus(t)
	names := make([]string, 0, len(current.Sources))
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	var changed []string
	for _, name := range names {
		if current.Sources[name] != older.Sources[name] {
			changed = append(changed, name)
		}
		t.Run("changed/"+name, func(t *testing.T) {
			sources := source30ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("empty-digest/"+name, func(t *testing.T) {
			sources := source30ExpectedSources()
			sources[name] = ""
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := source30ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	if !reflect.DeepEqual(changed, []string{
		"alchimie_discovery_world_v92.json",
		"alchimie_recipe_extensions_v92.json",
		"board_rankings_v37.json",
		"derived_catalog_v38.json",
		"kg_sample.json",
		"quick_games_v92.json",
	}) {
		t.Fatal("actual Source30/Source29 source delta differs", changed)
	}
	t.Run("extra", func(t *testing.T) {
		sources := source30ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	t.Run("KG-only", func(t *testing.T) {
		source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{"kg_sample.json": current.Sources["kg_sample.json"]})
	})
	for mask := 1; mask < (1<<len(changed))-1; mask++ {
		sources := source30ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-source30-source29-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
