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
// inferred from registering main's genuine distinct V1.9 and V1.10 corpora.
func v19ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "0c5fb28ecb3a682eecb28d4d192f688d39a61893ce66e69facac56c09b6603d5",
		"alchimie_recipe_extensions_v92.json": "64e046b1f069105184dd5f61ba5a3af02efcb3b11e7f2f77a3afbfd6de8b639e",
		"board_rankings_v37.json":             "2f7c7d15a95f52f80be5ae219d605edce3a2e9494d6bff2e3b3f03494e4a5110",
		"derived_catalog_v38.json":            "49cbcc3fc8473966ebf61ae1f69c2ba6a999d0d2e3376ffc837f8e92717ed6cf",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "846c2a4d48f85524b21043ecf52320edfa937946d030f91022ff6a879caae3e8",
		"quick_games_v92.json":                "793cc9cf54abf4f655fcf2441405db687c8fe45f0a79fd48819a39249892f8c8",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v110ExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "e50eb606c35f5c6695e29732bc5e1a85471771e5dc59c1f5da9da4852b1b498e",
		"alchimie_recipe_extensions_v92.json": "a25735aaae4c4c79622ea4e9385b0dc780fca0da6b6355170941f3ac78477e08",
		"board_rankings_v37.json":             "f28bd8d074bbc1595542944f419952fe6ad6f4c8e25f0639d6be257ce2c9db20",
		"derived_catalog_v38.json":            "6d381e18fd6aa4c538c2565b636436b136b935961ad18014ba52c37e45d6e1a6",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "5690162f60d8252a2d3e76a391f0109e27869cff2dbabf82f3333d3176ab0db5",
		"quick_games_v92.json":                "0ef98d29f6baf6ef1266f39e4231852866bb2397fd5407bbae3762c3eafedd3b",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func v110ReadLiteralCorpus(t *testing.T, path string, size int, digest, constant, reference string, sources map[string]string) *Corpus {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if len(raw) != size || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || constant != digest {
		t.Fatal("literal independent corpus bytes changed", path)
	}
	corpus, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if corpus.SchemaVersion != 1 || corpus.Reference != reference || len(corpus.Cases) != 1207 || !reflect.DeepEqual(corpus.Sources, sources) {
		t.Fatal("exact independent eight-source/1207-case provenance differs", path)
	}
	return corpus
}

func v19ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	return v110ReadLiteralCorpus(t, "testdata/python-http-parity-v1-9.json.gz", 33560,
		"3cce62aa1c34edeff2db245f4d4977a59808545fd24058fce9858f6516a52141", V19SHA256,
		"Django application, V1.9 seasons-and-school content", v19ExpectedSources())
}

func v110ReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	return v110ReadLiteralCorpus(t, "testdata/python-http-parity-v1-10.json.gz", 33603,
		"bd72460000d5b4cd8e642f11d9d03335105ebb55f31faa1661b720a45517f404", V110SHA256,
		"Django application, V1.10 everyday-discovery; archived capture_reference.py at ae70c16935d402719b95405685bccbbbea13a3bd", v110ExpectedSources())
}

// v110RequireDistinctSuccessor checks that a successor keeps every ordered
// request/status of its predecessor and changes exactly the captured bodies.
func v110RequireDistinctSuccessor(t *testing.T, want, old *Corpus, bodies int) {
	t.Helper()
	if len(old.Cases) != len(want.Cases) || reflect.DeepEqual(old.Sources, want.Sources) {
		t.Fatal("successor replaced its distinct predecessor tuple")
	}
	changed := 0
	for i, record := range want.Cases {
		if !reflect.DeepEqual(record.Request, old.Cases[i].Request) || record.Status != old.Cases[i].Status {
			t.Fatal("captured ordered requests/statuses differ from their retained history")
		}
		if !reflect.DeepEqual(record.Body, old.Cases[i].Body) {
			changed++
		}
	}
	if changed != bodies {
		t.Fatal("distinct captured response-body delta differs", changed)
	}
}

func TestV19SelectsItsExactEightSourceHistoricalCorpus(t *testing.T) {
	want := v19ReadExpectedCorpus(t)
	loaded, err := reviewedV19()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V1.9 loader changed its independent captured responses", err)
	}
	sources := v19ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V1.9 tuple selected different responses or changed its input", err)
	}
	v110RequireDistinctSuccessor(t, want, v18ReadExpectedCorpus(t), 23)
}

func TestV110SelectsItsExactEightSourceCorpus(t *testing.T) {
	want := v110ReadExpectedCorpus(t)
	loaded, err := reviewedV110()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("V1.10 loader changed its independent captured responses", err)
	}
	data, err := content.Load()
	if err != nil || !reflect.DeepEqual(data.Sources, want.Sources) {
		t.Fatal("live compiled bundle does not have the actual V1.10 source tuple", err)
	}
	sources := v110ExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) || !reflect.DeepEqual(sources, before) {
		t.Fatal("complete V1.10 tuple selected different responses or changed its input", err)
	}
	v110RequireDistinctSuccessor(t, want, v19ReadExpectedCorpus(t), 23)
}

func TestV110PreservesAllNineHistoricalSelections(t *testing.T) {
	current := v110ReadExpectedCorpus(t)
	readers := append(source6GUIHistoricalReaders(),
		source6GUIHistoricalReader{"source6-gui", source6GUIRequalificationCorpus},
		source6GUIHistoricalReader{"v1-8", reviewedV18},
		source6GUIHistoricalReader{"v1-9", reviewedV19})
	if len(readers) != 9 {
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

func TestV110RefusesChangedMissingExtraNilAndMixedSourcesBeforeHTTP(t *testing.T) {
	current := v110ReadExpectedCorpus(t)
	names := make([]string, 0, 8)
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := v110ExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := v110ExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := v110ExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
	// Each adjacent pair has two positive endpoint tests. All62 proper mixtures
	// of V1.10/V1.9 and of V1.9/V1.8 refuse at the source boundary before HTTP.
	for _, pair := range []struct {
		name      string
		newer     *Corpus
		newerSrcs func() map[string]string
		older     *Corpus
	}{
		{"v1-10-v1-9", current, v110ExpectedSources, v19ReadExpectedCorpus(t)},
		{"v1-9-v1-8", v19ReadExpectedCorpus(t), v19ExpectedSources, v18ReadExpectedCorpus(t)},
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
