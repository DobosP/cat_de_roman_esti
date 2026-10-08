package httpgolden

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func source6CorpusSources() map[string]string {
	return map[string]string{
		"alchimie_discovery_world_v92.json":   "8f013a8f6b54a97a768a34c42e669addc4f5ab9823302befbe15ad811cae77ad",
		"alchimie_recipe_extensions_v92.json": "d94647e78f8c2bd375b961f0aab52f3f7207024e60bed745b78c4a3d052d0bfc",
		"board_rankings_v37.json":             "036c8a00de347939d132ba25512da7cba53b12e9d11a9f86cecc07cc98293c31",
		"derived_catalog_v38.json":            "fdc94e5ded3477b44aaffe90858ca1070cd1c1d344be22724c0e02f0110bb96a",
		"games_pack.json":                     "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8",
		"kg_sample.json":                      "63f0dcd7992f0d1434eab49b9c1b7e97f0db30a22cd708b7b25c0199f39031bf",
		"quick_games_v92.json":                "0c79b9c5cb0f9602c2506ef384ac64d519731dd9add53acf602d2c4f51a3f345",
		"release_reserve_v1.json":             "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func TestV16IndependentCorpusRetainsExactSourceScope(t *testing.T) {
	c, err := reviewedV16()
	if err != nil {
		t.Fatal(err)
	}
	if V16SHA256 != "15c7d1bc33c2775a387a9bfe3229625145c94a0ed300622e6737b557c77ebdfe" || c.SchemaVersion != 1 || len(c.Cases) != 1207 || len(c.Sources) != 8 || !reflect.DeepEqual(c.Sources, source6CorpusSources()) {
		t.Fatal("V1.6 independent corpus source/count identity drift")
	}
	if !strings.Contains(c.Reference, "Independent Django application; V1.6 two reviewed singular inputs") || !strings.Contains(c.Reference, "Source6 a086dc2accd6eb97ab7040f6a0e609cc40209fa6a441ee9d9e3f3f727d76e611") {
		t.Fatal("V1.6 independent capture provenance drift")
	}
	selected, err := ForSources(source6CorpusSources())
	if err != nil || !reflect.DeepEqual(selected, c) {
		t.Fatal("exact Source6 tuple selected different independent responses", err)
	}
}

type historicalCorpusReaderV16 struct {
	name string
	read func() (*Corpus, error)
}

func historicalCorpusReadersV16() []historicalCorpusReaderV16 {
	return []historicalCorpusReaderV16{
		{"initial", Frozen},
		{"v1-2", reviewedV12},
		{"v1-3", reviewedV13},
		{"v1-4", reviewedV14},
		{"v1-5", reviewedV15},
	}
}

func TestV16SelectorPreservesAllFiveHistoricalCorpora(t *testing.T) {
	for _, row := range historicalCorpusReadersV16() {
		t.Run(row.name, func(t *testing.T) {
			old, err := row.read()
			if err != nil {
				t.Fatal(err)
			}
			if len(old.Cases) != 1207 || len(old.Sources) != 8 || reflect.DeepEqual(old.Sources, source6CorpusSources()) {
				t.Fatal("historical corpus identity was replaced")
			}
			selected, err := ForSources(old.Sources)
			if err != nil || !reflect.DeepEqual(selected, old) {
				t.Fatal("historical tuple lost its exact independent responses", err)
			}
		})
	}
	v14, err := reviewedV14()
	if err != nil {
		t.Fatal(err)
	}
	v15, err := reviewedV15()
	if err != nil {
		t.Fatal(err)
	}
	if v14.Sources["kg_sample.json"] != v15.Sources["kg_sample.json"] || reflect.DeepEqual(v14.Sources, v15.Sources) {
		t.Fatal("Source4/Source5 same-KG, different-world control changed")
	}
	for _, want := range []*Corpus{v14, v15} {
		selected, err := ForSources(want.Sources)
		if err != nil || !reflect.DeepEqual(selected, want) {
			t.Fatal("same KG collapsed distinct complete source tuples", err)
		}
	}
}

func cloneV16SourceSet(sources map[string]string) map[string]string {
	if sources == nil {
		return nil
	}
	out := map[string]string{}
	for name, digest := range sources {
		out[name] = digest
	}
	return out
}

func requireV16SourceRefusal(t *testing.T, sources map[string]string) {
	t.Helper()
	before := cloneV16SourceSet(sources)
	if c, err := ForSources(sources); err == nil || c != nil {
		t.Fatal("unreviewed source tuple acquired expected responses", err)
	}
	if !reflect.DeepEqual(sources, before) {
		t.Fatal("selector rewrote the unreviewed source tuple")
	}
}

func TestV16SelectorRefusesEveryChangedOrMissingSource(t *testing.T) {
	want := source6CorpusSources()
	names := make([]string, 0, len(want))
	for name := range want {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		t.Run("changed/"+name, func(t *testing.T) {
			sources := cloneV16SourceSet(want)
			sources[name] = strings.Repeat("0", 64)
			requireV16SourceRefusal(t, sources)
		})
		t.Run("missing/"+name, func(t *testing.T) {
			sources := cloneV16SourceSet(want)
			delete(sources, name)
			requireV16SourceRefusal(t, sources)
		})
	}
	t.Run("extraneous", func(t *testing.T) {
		sources := cloneV16SourceSet(want)
		sources["unreviewed-extra.json"] = strings.Repeat("0", 64)
		requireV16SourceRefusal(t, sources)
	})
	t.Run("nil", func(t *testing.T) { requireV16SourceRefusal(t, nil) })
	t.Run("empty", func(t *testing.T) { requireV16SourceRefusal(t, map[string]string{}) })
	t.Run("KG-only", func(t *testing.T) {
		requireV16SourceRefusal(t, map[string]string{"kg_sample.json": want["kg_sample.json"]})
	})
}

func TestV16SelectorRefusesMixedHistoricalSources(t *testing.T) {
	want := source6CorpusSources()
	for _, row := range historicalCorpusReadersV16() {
		old, err := row.read()
		if err != nil {
			t.Fatal(err)
		}
		for name, digest := range old.Sources {
			if digest == want[name] {
				continue
			}
			t.Run(row.name+"/"+name, func(t *testing.T) {
				sources := cloneV16SourceSet(want)
				sources[name] = digest
				requireV16SourceRefusal(t, sources)
			})
		}
	}
}

// Read the genuine Source5 bundle, not expected source names from an HTTP corpus.
// The complete immutable tar is bounded and pinned before its C1 member is decoded.
func historicalV15Data(t *testing.T) *content.Content {
	t.Helper()
	path := filepath.Join("..", "..", "..", "docs", "reviews", "v1-6-everyday-inputs", "reference", "historical-source5-context.tar.gz")
	f, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	compressed, err := io.ReadAll(io.LimitReader(f, (4<<20)+1))
	closeErr := f.Close()
	if err != nil || closeErr != nil || len(compressed) > 4<<20 || fmt.Sprintf("%x", sha256.Sum256(compressed)) != "ffffa21ccf11f79d817c529123f2583824c62fefaabd17a5887e7ce809507e48" {
		t.Fatal("historical Source5 compressed archive refused", err, closeErr)
	}
	z, err := gzip.NewReader(bytes.NewReader(compressed))
	if err != nil {
		t.Fatal(err)
	}
	raw, err := io.ReadAll(io.LimitReader(z, (32<<20)+1))
	closeErr = z.Close()
	if err != nil || closeErr != nil || len(raw) != 14376960 || len(raw) > 32<<20 {
		t.Fatal("historical Source5 tar size or compression refused", err, closeErr)
	}
	reader := tar.NewReader(bytes.NewReader(raw))
	seen := map[string]bool{}
	var bundle []byte
	for {
		header, err := reader.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			t.Fatal(err)
		}
		if header.Typeflag != tar.TypeReg || seen[header.Name] || header.Size < 0 || header.Size > 8<<20 {
			t.Fatal("historical Source5 member shape refused")
		}
		seen[header.Name] = true
		if header.Name == "go-backend/internal/content/bundled.json" {
			bundle, err = io.ReadAll(reader)
			if err != nil {
				t.Fatal(err)
			}
		}
	}
	if len(seen) != 12 || len(bundle) != 7272295 || fmt.Sprintf("%x", sha256.Sum256(bundle)) != "c1fff429992c69926aafb07f5b015f890a82c7c01cc5230107bdaf481bca5993" {
		t.Fatal("historical Source5 bundle identity refused")
	}
	c, err := content.Decode(bundle)
	if err != nil || len(c.Sources) != 8 {
		t.Fatal("historical Source5 content refused", err)
	}
	return c
}
