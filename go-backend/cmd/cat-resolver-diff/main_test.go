package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strconv"
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

func TestResolverReportMatchesAcrossWorkerCounts(t *testing.T) {
	// A worker must retain its session between create, guess and confirmation.
	t.Setenv("CAT_MAX_SESSIONS_PER_GAME", "1")
	t.Setenv("CAT_SESSION_TTL_SECONDS", "7200")

	candidate := installed(t)
	ids := make([]string, 0, len(candidate.targets))
	for id := range candidate.targets {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	selected := map[string]bool{}
	for _, id := range ids[:8] {
		selected[id] = true
	}
	items := candidate.content.PackItems[:0]
	for _, item := range candidate.content.PackItems {
		if item.Game != "contexto" || selected[item.ID] {
			items = append(items, item)
		}
	}
	candidate.content.PackItems = items
	dir := t.TempDir()
	writeBundle := func(name string) string {
		t.Helper()
		raw, err := json.Marshal(candidate.content)
		if err != nil {
			t.Fatal(err)
		}
		path := filepath.Join(dir, name)
		if err := os.WriteFile(path, raw, 0o600); err != nil {
			t.Fatal(err)
		}
		return path
	}
	beforePath := writeBundle("before.json")
	owner := candidate.targets[ids[0]].Owner
	resolver := graph.New(candidate.content)
	for _, spelling := range []string{"martorrezolvator", "semnprobator"} {
		for i := range candidate.content.Nodes {
			node := &candidate.content.Nodes[i]
			if node.ID == owner {
				node.Aliases = append(node.Aliases, spelling)
			}
		}
		candidate.content.NormalizedIndex[resolver.Normalize(spelling)] = owner
	}
	afterPath := writeBundle("candidate.json")
	probesPath := filepath.Join(dir, "probes.json")
	if err := os.WriteFile(probesPath, []byte(`["semnprobator","România","semnprobator"]`), 0o600); err != nil {
		t.Fatal(err)
	}
	args := []string{"--before", beforePath, "--after", afterPath, "--probes", probesPath}
	var serial bytes.Buffer
	if err := run(args, &serial); err != nil {
		t.Fatal(err)
	}
	var report struct {
		Targets []target
		Probes  []string
		Changes []change
	}
	if err := json.Unmarshal(serial.Bytes(), &report); err != nil {
		t.Fatal(err)
	}
	if len(report.Targets) != len(selected) || len(report.Changes) < 2 ||
		!reflect.DeepEqual(report.Probes, []string{"România", "martorrezolvator", "semnprobator"}) {
		t.Fatalf("unexpected coverage: %d targets, %v probes, %d changes",
			len(report.Targets), report.Probes, len(report.Changes))
	}
	for _, workers := range []int{2, 4} {
		var parallel bytes.Buffer
		if err := run(append(args, "--workers", strconv.Itoa(workers)), &parallel); err != nil {
			t.Fatal(err)
		}
		if !bytes.Equal(serial.Bytes(), parallel.Bytes()) {
			t.Fatalf("report bytes differ for %d workers", workers)
		}
	}
	for _, workers := range []int{0, maxWorkers + 1} {
		var refused bytes.Buffer
		if err := run(append(args, "--workers", strconv.Itoa(workers)), &refused); err == nil || refused.Len() != 0 {
			t.Fatalf("expected invalid worker count %d to fail without a report", workers)
		}
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
