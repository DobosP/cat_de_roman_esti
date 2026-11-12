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

func source28ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "7943a014920065598ae9a3b6d23217d9d72613d7227ef73fd17603a317dfec19",
		"alchimie_recipe_extensions_v92.json": "14672cc7701cd43ae33f9b7d7de26ae5a13011fa45912653624d97240a3d03e0",
		"board_rankings_v37.json":             "9ed2e15d496006325dcf70d3d1808ec519cda58a3e5d03b21d269226048e7889",
		"derived_catalog_v38.json":            "60510f1943c8459307ce99d09be4360c84b0b5b7fac852e049b25be3ef1201d9",
		"games_pack.json":                     "1ba0f099b47e3c0c8fd7319938a9649ec3e508a08fd7467990d1cfbb147335f5",
		"kg_sample.json":                      "8b8addd26cdc3aa5972a97368196e9593d5ef38477625f2fba988845e10879d4",
		"quick_games_v92.json":                "8ac60f6ec592def74f0fe298a0e29546b2fa925151274bb97df020e062a20406",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func source28ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	const path = "testdata/python-http-parity-v4-c42-source28.json.gz"
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	const digest = "438abf5396eb07cfe21acfab6185ce726f0af1dbef32407773e470fd1cdef71c"
	if len(raw) != 33453 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || V4C42Source28SHA256 != digest {
		t.Fatal("literal independent Source28 corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != "Independent current Loop Python/Django Source28 C42 oracle; original retained 1206 C10 HTTP journeys reexecuted; no native or prior expected responses used" ||
		len(corpus.Cases) != 1206 || !reflect.DeepEqual(corpus.Sources, source28ExpectedSources()) {
		t.Fatal("exact independent Source28 eight-source/1206-case provenance differs", path)
	}
	return corpus
}

func TestSource28SelectsExactCurrentIndependentCorpus(t *testing.T) {
	want := source28ReadExpectedCorpus(t)
	loaded, err := reviewedV4C42Source28()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("Source28 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || !reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle does not have the actual Source28 source tuple", err)
	}
	sources := source28ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete Source28 tuple selected different responses or changed its input", err)
	}
	if len(reviewedSources) != 28 {
		t.Fatal("expected Source28 plus 27 historical selectors", len(reviewedSources))
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

func TestSource28RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := source28ReadExpectedCorpus(t)
	older := source27ReadExpectedCorpus(t)
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
			sources := source28ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("empty-digest/"+name, func(t *testing.T) {
			sources := source28ExpectedSources()
			sources[name] = ""
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := source28ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	if !reflect.DeepEqual(changed, []string{
		"alchimie_discovery_world_v92.json",
		"alchimie_recipe_extensions_v92.json",
		"board_rankings_v37.json",
		"derived_catalog_v38.json",
		"games_pack.json",
		"quick_games_v92.json",
	}) {
		t.Fatal("actual Source28/Source27 source delta differs", changed)
	}
	t.Run("extra", func(t *testing.T) {
		sources := source28ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	t.Run("KG-only", func(t *testing.T) {
		source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{"kg_sample.json": current.Sources["kg_sample.json"]})
	})
	for mask := 1; mask < (1<<len(changed))-1; mask++ {
		sources := source28ExpectedSources()
		for i, name := range changed {
			if mask&(1<<i) != 0 {
				sources[name] = older.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("mixed-source28-source27-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
