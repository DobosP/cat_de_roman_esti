package main

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
)

func TestNativePreviewReproducesExactServingBaseline(t *testing.T) {
	root := "../../.."
	fixture := filepath.Join(root, "cat_de_roman_esti", "fixtures")
	read := func(path string) []byte {
		t.Helper()
		data, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		return data
	}
	before, err := loadBundle(bundledPath, contentbuild.SHA256(read(bundledPath)))
	if err != nil {
		t.Fatal(err)
	}
	kgBytes := read(filepath.Join(fixture, "kg_sample.json"))
	kg, err := contentops.Decode(kgBytes)
	if err != nil {
		t.Fatal(err)
	}
	g, err := contentbuild.BoardViewGraph(kg)
	if err != nil {
		t.Fatal(err)
	}
	packBytes := read(filepath.Join(fixture, "games_pack.json"))
	after, err := contentops.BoardViewPreview(root, before, g, contentbuild.TextSHA256(kgBytes), packBytes)
	if err != nil {
		t.Fatal(err)
	}
	result, err := compare(before, after)
	if err != nil {
		t.Fatal(err)
	}
	if result.DisturbedTotal != 0 || len(result.Added)+len(result.SelectionChanges)+len(result.Diagnostics) != 0 {
		t.Fatal("native baseline preview does not reproduce all sealed board views")
	}
}
