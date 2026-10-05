package contentrails

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
)

func TestProspectiveWorldAuditRefusesMalformedGraphBeforeReplay(t *testing.T) {
	root := t.TempDir()
	kg, err := fixture(rootPath(t), "kg_sample.json")
	if err != nil {
		t.Fatal(err)
	}
	object(object(kg["meta"])["counts"])["nodes"] = len(rows(kg["kg_nodes"])) + 1
	writeJSONTest(t, filepath.Join(root, "cat_de_roman_esti/fixtures/kg_sample.json"), kg)
	g, err := sourceGraph(root)
	if err != nil {
		t.Fatal("the parser alone should not certify complete fixture metadata", err)
	}
	world, err := fixture(rootPath(t), "alchimie_discovery_world_v92.json")
	if err != nil {
		t.Fatal(err)
	}
	for _, v := range rows(world["concepts"]) {
		c := object(v)
		if c["origin"] != "authored" {
			c["snapshot"] = contentbuild.NodeSnapshot(g.Node(text(c["id"])))
		}
	}
	if _, err = contentbuild.ValidateDiscoveryWorld(world, g); err != nil {
		t.Fatal("otherwise-valid prospective world should demonstrate separate graph gate", err)
	}
	if _, err = auditWorld(root, world); err == nil || !strings.Contains(err.Error(), "prospective world source fixture invalid: meta_counts:") {
		t.Fatal("malformed source graph reached prospective replay", err)
	}
}

func TestProspectiveWorldAuditWithChangedGraphKeepsInstalledWorldFailClosed(t *testing.T) {
	root, _ := cloneRoot(t)
	world, err := fixture(root, "alchimie_discovery_world_v92.json")
	if err != nil {
		t.Fatal(err)
	}
	g, err := sourceGraph(root)
	if err != nil {
		t.Fatal(err)
	}
	// Establish this synthetic installed world's exact current graph snapshots
	// before introducing the single alias transition being tested. This does
	// not modify the calling repository or grant any publication authority.
	tomato := ""
	for _, v := range rows(world["concepts"]) {
		c := object(v)
		if c["origin"] == "authored" {
			continue
		}
		n := g.Node(text(c["id"]))
		if n == nil {
			t.Fatal("installed world KG concept missing")
		}
		c["snapshot"] = contentbuild.NodeSnapshot(n)
		if c["label"] == "Roșie" {
			tomato = text(c["id"])
		}
	}
	if tomato == "" {
		t.Fatal("missing actual Roșie world concept")
	}
	if _, err = contentbuild.ValidateDiscoveryWorld(world, g); err != nil {
		t.Fatal("synthetic starting world must match its graph", err)
	}
	worldPath, _ := ArtifactPath(root, "world")
	writeJSONTest(t, worldPath, world)
	installedBytes, _ := os.ReadFile(worldPath)
	kg, err := fixture(root, "kg_sample.json")
	if err != nil {
		t.Fatal(err)
	}
	for _, v := range rows(kg["kg_nodes"]) {
		n := object(v)
		if n["id"] == tomato {
			n["aliases"] = append(rows(n["aliases"]), "synthetic prospective tomato")
		}
	}
	for _, relative := range []string{"cat_de_roman_esti/fixtures/kg_sample.json", "tests/fixtures/kg_sample.json"} {
		writeJSONTest(t, filepath.Join(root, relative), kg)
	}
	if errors := contentbuild.ValidateFixture(filepath.Join(root, "cat_de_roman_esti/fixtures/kg_sample.json")); len(errors) != 0 {
		t.Fatal("the changed source graph itself must remain valid", errors)
	}
	g, err = sourceGraph(root)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = contentbuild.ValidateDiscoveryWorld(world, g); err == nil {
		t.Fatal("stale installed world snapshot accepted against changed graph")
	}
	if _, err = contentbuild.Load(root); err == nil {
		t.Fatal("incoherent installed sources silently activated serving content")
	}
	prospective := clone(world).(map[string]any)
	for _, v := range rows(prospective["concepts"]) {
		c := object(v)
		if c["id"] == tomato {
			c["snapshot"] = contentbuild.NodeSnapshot(g.Node(tomato))
		}
	}
	audit, err := auditWorld(root, prospective)
	if err != nil {
		t.Fatal("validated prospective world could not be audited before installation", err)
	}
	if audit["verdict"] != "accept" || len(rows(audit["goal_replays"])) != 33 || len(rows(audit["compatible_save_replays"])) != 9 || integer(audit["historical_prefixes"]) != 1009 || integer(object(audit["metrics"])["recipes"]) != 351 {
		t.Fatal("prospective audit dropped goal/recipe/historical-save coverage", audit["metrics"])
	}
	if _, err = auditWorld(root, world); err == nil {
		t.Fatal("stale prospective world snapshot bypassed source validation")
	}
	unchanged, err := os.ReadFile(worldPath)
	if err != nil || !bytes.Equal(installedBytes, unchanged) {
		t.Fatal("private prospective audit changed the installed world")
	}
	if _, err = contentbuild.Load(root); err == nil {
		t.Fatal("successful private audit weakened sealed export refusal")
	}
}
