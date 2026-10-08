package httpgolden

import (
	"bytes"
	"context"
	"crypto/sha256"
	"fmt"
	"os"
	"reflect"
	"sort"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

// Authored selector/refusal contracts only. These tests do not qualify a live
// server, execute the 1207 HTTP requests, or confer installed-source authority.
func source6GUIExpectedSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "572882a77dbdd8bac63ca69c64c6990a1601a49551693cf1b1b5fcb7a81861de",
		"alchimie_recipe_extensions_v92.json": "eeb7eede9009f09a7d9df012c7addb9f26b1b484040eb31c44ba2e6f7f35cee8",
		"board_rankings_v37.json":             "036c8a00de347939d132ba25512da7cba53b12e9d11a9f86cecc07cc98293c31",
		"derived_catalog_v38.json":            "fdc94e5ded3477b44aaffe90858ca1070cd1c1d344be22724c0e02f0110bb96a",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "63f0dcd7992f0d1434eab49b9c1b7e97f0db30a22cd708b7b25c0199f39031bf",
		"quick_games_v92.json":                "234305a844033cff0914a5213f6c0b8dcd1b21918d57cc851780259c9e87ee59",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func source6GUICloneSources(sources map[string]string) map[string]string {
	if sources == nil {
		return nil
	}
	out := make(map[string]string, len(sources))
	for name, digest := range sources {
		out[name] = digest
	}
	return out
}

func source6GUIReadExpectedCorpus(t *testing.T) *Corpus {
	t.Helper()
	raw, err := os.ReadFile("testdata/python-http-parity-source6-gui-requalification.json.gz")
	if err != nil {
		t.Fatal(err)
	}
	const digest = "0437c53b91b07d7c4323a7c66753d7250d9304b6a32f94f03901285e64c21951"
	if len(raw) != 33969 || fmt.Sprintf("%x", sha256.Sum256(raw)) != digest || source6GUIRequalificationSHA256 != digest {
		t.Fatal("accepted current independent corpus byte identity changed")
	}
	want, err := ReadCorpus(bytes.NewReader(raw), true)
	if err != nil {
		t.Fatal(err)
	}
	if want.SchemaVersion != 1 || len(want.Cases) != 1207 || len(want.Sources) != 8 || !reflect.DeepEqual(want.Sources, source6GUIExpectedSources()) {
		t.Fatal("current independent corpus lost its exact eight-source/1207-case scope")
	}
	if !strings.Contains(want.Reference, "Independent current Django TestClient responses; Source6 GUI runtime metadata successor") ||
		!strings.Contains(want.Reference, "authoredSource6 a086dc2accd6eb97ab7040f6a0e609cc40209fa6a441ee9d9e3f3f727d76e611 unchanged") {
		t.Fatal("current independent capture provenance changed")
	}
	return want
}

func TestSource6GUIRequalificationSelectsExactIndependentCorpus(t *testing.T) {
	want := source6GUIReadExpectedCorpus(t)
	loaded, err := source6GUIRequalificationCorpus()
	if err != nil || !reflect.DeepEqual(loaded, want) {
		t.Fatal("current loader changed the accepted independent corpus", err)
	}
	sources := source6GUIExpectedSources()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err != nil || !reflect.DeepEqual(selected, want) {
		t.Fatal("exact current tuple selected different independent responses", err)
	}
	if !reflect.DeepEqual(sources, before) {
		t.Fatal("selector rewrote the accepted current input map")
	}
	old, err := reviewedV16()
	if err != nil {
		t.Fatal(err)
	}
	if reflect.DeepEqual(old, want) || reflect.DeepEqual(old.Sources, want.Sources) || old.Reference == want.Reference {
		t.Fatal("current metadata successor replaced the historical V1.6 corpus identity")
	}
	if !reflect.DeepEqual(old.Cases, want.Cases) {
		t.Fatal("accepted metadata-only successor changed an ordered request, status or expected body")
	}
}

type source6GUIHistoricalReader struct {
	name string
	read func() (*Corpus, error)
}

func source6GUIHistoricalReaders() []source6GUIHistoricalReader {
	return []source6GUIHistoricalReader{
		{"initial", Frozen},
		{"v1-2", reviewedV12},
		{"v1-3", reviewedV13},
		{"v1-4", reviewedV14},
		{"v1-5", reviewedV15},
		{"v1-6", reviewedV16},
	}
}

func TestSource6GUIRequalificationPreservesAllSixHistoricalSelections(t *testing.T) {
	current := source6GUIReadExpectedCorpus(t)
	for _, row := range source6GUIHistoricalReaders() {
		t.Run(row.name, func(t *testing.T) {
			old, err := row.read()
			if err != nil {
				t.Fatal(err)
			}
			if len(old.Sources) != 8 || len(old.Cases) != 1207 || reflect.DeepEqual(old.Sources, current.Sources) {
				t.Fatal("historical corpus source/count identity changed")
			}
			sources := source6GUICloneSources(old.Sources)
			before := source6GUICloneSources(sources)
			selected, err := ForSources(sources)
			if err != nil || !reflect.DeepEqual(selected, old) || reflect.DeepEqual(selected, current) {
				t.Fatal("historical whole tuple lost its own independent corpus", err)
			}
			if !reflect.DeepEqual(sources, before) {
				t.Fatal("selector rewrote a historical input map")
			}
		})
	}
}

type source6GUIRefusalTransport struct{ calls int }

func (transport *source6GUIRefusalTransport) Do(context.Context, Request) (Response, error) {
	transport.calls++
	return Response{}, fmt.Errorf("unexpected request across source-refusal boundary")
}

func (*source6GUIRefusalTransport) Close() error { return nil }

func source6GUIRequireRefusalWithoutRequests(t *testing.T, current *Corpus, sources map[string]string) {
	t.Helper()
	before := source6GUICloneSources(sources)
	selected, err := ForSources(sources)
	if err == nil || selected != nil {
		t.Fatal("unreviewed tuple acquired an independent expected corpus", err)
	}
	if !reflect.DeepEqual(sources, before) {
		t.Fatal("selector rewrote a refused input map")
	}
	transport := &source6GUIRefusalTransport{}
	client, err := NewClient(transport, MaxCases)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := Replay(context.Background(), client, current, &content.Content{Sources: sources}); err == nil ||
		err.Error() != "reference source digest binding differs from current reviewed export" {
		t.Fatal("mismatched current corpus did not refuse at its source boundary", err)
	}
	if client.Count() != 0 || transport.calls != 0 || !reflect.DeepEqual(sources, before) {
		t.Fatal("source refusal issued a request or mutated its input map")
	}
}

func TestSource6GUIRequalificationRefusesChangedMissingExtraAndNilSources(t *testing.T) {
	current := source6GUIReadExpectedCorpus(t)
	names := make([]string, 0, len(current.Sources))
	for name := range current.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := source6GUIExpectedSources()
			sources[name] = strings.Repeat("0", 64)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := source6GUIExpectedSources()
			delete(sources, name)
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
	t.Run("extra", func(t *testing.T) {
		sources := source6GUIExpectedSources()
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		source6GUIRequireRefusalWithoutRequests(t, current, sources)
	})
	t.Run("nil", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, nil) })
	t.Run("empty", func(t *testing.T) { source6GUIRequireRefusalWithoutRequests(t, current, map[string]string{}) })
}

func TestSource6GUIRequalificationRefusesProperSource6Mixtures(t *testing.T) {
	current := source6GUIReadExpectedCorpus(t)
	old, err := reviewedV16()
	if err != nil {
		t.Fatal(err)
	}
	names := make([]string, 0, 3)
	for name, digest := range old.Sources {
		if digest != current.Sources[name] {
			names = append(names, name)
		}
	}
	sort.Strings(names)
	if !reflect.DeepEqual(names, []string{
		"alchimie_discovery_world_v92.json",
		"alchimie_recipe_extensions_v92.json",
		"quick_games_v92.json",
	}) {
		t.Fatal("metadata successor changed sources beyond the three accepted catalogs")
	}
	// Masks 1..6 are the six proper mixtures. Zero is the valid current tuple;
	// seven is the valid historical V1.6 tuple, verified in its positive route.
	for mask := 1; mask < 7; mask++ {
		sources := source6GUIExpectedSources()
		for index, name := range names {
			if mask&(1<<index) != 0 {
				sources[name] = old.Sources[name]
			}
		}
		t.Run(fmt.Sprintf("partial-old-catalogs-%d", mask), func(t *testing.T) {
			source6GUIRequireRefusalWithoutRequests(t, current, sources)
		})
	}
}
