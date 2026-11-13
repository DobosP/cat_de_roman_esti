package main

import (
	"path/filepath"
	"reflect"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

func installed(t *testing.T) *bundle {
	t.Helper()
	path := filepath.Join("..", "..", "internal", "content", "bundled.json")
	b, err := load(path)
	if err != nil {
		t.Fatal(err)
	}
	return b
}

func TestSameInstalledBundleCoversAllTargets(t *testing.T) {
	before, after := installed(t), installed(t)
	targets, probes, changes, err := compare(before, after, []string{"România"})
	if err != nil {
		t.Fatal(err)
	}
	if len(targets) != len(before.targets) || len(targets) < 2 || len(probes) != 1 || len(changes) != 0 {
		t.Fatalf("unexpected identical bundle diff: %d targets, %v probes, %d changes", len(targets), probes, len(changes))
	}
	nonselectable := 0
	for _, target := range targets {
		if !target.Selectable {
			nonselectable++
		}
	}
	if nonselectable == 0 {
		t.Fatal("fixture has no approved but ineligible target")
	}
}

func TestNewAliasWinsOnlyAtItsOwner(t *testing.T) {
	before, after := installed(t), installed(t)
	var selected target
	for _, target := range before.targets {
		if target.Selectable {
			selected = target
			break
		}
	}
	if selected.ID == "" {
		t.Fatal("no selectable target")
	}
	probe := "martorrezolvator" // Synthetic test input, never written into a source fixture.
	key := graph.New(before.content).Normalize(probe)
	for i := range after.content.Nodes {
		if after.content.Nodes[i].ID == selected.Owner {
			after.content.Nodes[i].Aliases = append(after.content.Nodes[i].Aliases, probe)
		}
	}
	after.content.NormalizedIndex[key] = selected.Owner
	got, err := probesFor(before, after, nil)
	if err != nil || !reflect.DeepEqual(got, []string{probe}) {
		t.Fatalf("probes=%v error=%v", got, err)
	}
	before.prepare()
	after.prepare()
	exclude := map[string]bool{}
	for id := range before.targets {
		if id != selected.ID {
			exclude[id] = true
		}
	}
	old, err := readAnswer(before, selected, exclude, probe)
	if err != nil {
		t.Fatal(err)
	}
	new, err := readAnswer(after, selected, exclude, probe)
	if err != nil {
		t.Fatal(err)
	}
	if old.Mode != "unknown" || old.Won || new.Mode != "direct" || !new.Won ||
		new.Attempts != 1 || new.Guess["id"] != selected.Owner {
		t.Fatalf("unexpected before %+v or after %+v", old, new)
	}
}

func TestRejectsNonAliasChangesAndUnboundedProbes(t *testing.T) {
	before, after := installed(t), installed(t)
	after.content.Edges[0].Strength += 0.1
	if _, err := probesFor(before, after, nil); err == nil {
		t.Fatal("accepted changed topology")
	}
	if _, err := probesFor(before, before, []string{""}); err == nil {
		t.Fatal("accepted blank probe")
	}
	if _, err := probesFor(before, before, make([]string, 1001)); err == nil {
		t.Fatal("accepted oversize probe set")
	}
}

func TestRejectsGeneratedResolverChangesWithoutAlias(t *testing.T) {
	before, after := installed(t), installed(t)
	after.content.NormalizedIndex["adversarial"] = before.content.Nodes[0].ID
	if _, err := probesFor(before, after, nil); err == nil {
		t.Fatal("accepted unexplained normalized index change")
	}
	delete(after.content.NormalizedIndex, "adversarial")
	after.content.NormalizationMap["s"] = "z"
	if _, err := probesFor(before, after, nil); err == nil {
		t.Fatal("accepted unexplained normalization rule change")
	}
}
