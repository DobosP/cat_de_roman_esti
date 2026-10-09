package graph

import (
	"sort"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

// Rebuild the reference graph from authenticated raw content rather than from
// Service adjacency, neighbor methods or another distance wrapper.
func TestDenseDistancesAgainstIndependentRawEdgeBFS(t *testing.T) {
	data, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	known := make(map[string]bool, len(data.Nodes))
	ids := make([]string, 0, len(data.Nodes))
	for _, node := range data.Nodes {
		if node.ID == "" || known[node.ID] {
			t.Fatalf("empty or duplicate raw node ID: %q", node.ID)
		}
		known[node.ID] = true
		ids = append(ids, node.ID)
	}
	if len(ids) == 0 {
		t.Fatal("current graph has no nodes")
	}
	sort.Strings(ids)

	// DistancesToDense follows non-distractor directed edges. A bidirectional
	// edge supplies both orientations. Parallel edges need not be collapsed:
	// they have identical unweighted connectivity, regardless of strength.
	reverse := make(map[string][]string, len(ids))
	arcs := 0
	for _, edge := range data.Edges {
		if edge.IsDistractor || !known[edge.Src] || !known[edge.Dst] {
			continue
		}
		reverse[edge.Dst] = append(reverse[edge.Dst], edge.Src)
		arcs++
		if edge.Bidirectional {
			reverse[edge.Src] = append(reverse[edge.Src], edge.Dst)
			arcs++
		}
	}

	service := New(data)
	if service.NodeCount() != len(ids) {
		t.Fatalf("dense node count: got %d, raw content has %d", service.NodeCount(), len(ids))
	}
	for expected, id := range ids {
		index, ok := service.Index(id)
		if !ok || index != expected || service.IDAt(expected) != id {
			t.Fatalf("dense ID mapping differs for %q: got %d/%t, want %d", id, index, ok, expected)
		}
	}

	// Reuse only the reference workspace. Each target starts with an empty
	// map and queue, keeping peak auxiliary storage linear in nodes and edges.
	distance := make(map[string]int32, len(ids))
	queue := make([]string, 0, len(ids))
	reachable, unreachable := 0, 0
	for _, target := range ids {
		clear(distance)
		queue = queue[:0]
		distance[target] = 0
		queue = append(queue, target)
		for head := 0; head < len(queue); head++ {
			current := queue[head]
			for _, predecessor := range reverse[current] {
				if _, visited := distance[predecessor]; !visited {
					distance[predecessor] = distance[current] + 1
					queue = append(queue, predecessor)
				}
			}
		}
		got := service.DistancesToDense(target)
		if len(got) != len(ids) {
			t.Fatalf("dense result length for %q: got %d, want %d", target, len(got), len(ids))
		}
		for index, source := range ids {
			want, exists := distance[source]
			if exists {
				reachable++
			} else {
				want = -1
				unreachable++
			}
			if got[index] != want {
				t.Fatalf("distance %q -> %q: dense %d, independent BFS %d", source, target, got[index], want)
			}
			if source == target && got[index] != 0 {
				t.Fatalf("identity distance for %q is %d", target, got[index])
			}
		}
	}

	unknown := "__independent_bfs_unknown_target__"
	for known[unknown] {
		unknown += "_"
	}
	got := service.DistancesToDense(unknown)
	if len(got) != len(ids) {
		t.Fatalf("unknown-target result length: got %d, want %d", len(got), len(ids))
	}
	for index, value := range got {
		if value != -1 {
			t.Fatalf("unknown target is reachable from %q: %d", ids[index], value)
		}
	}
	if reachable+unreachable != len(ids)*len(ids) {
		t.Fatal("not every raw source/target pair was compared")
	}
	t.Logf("checked %d targets, %d raw directed arcs and %d source/target pairs (%d unreachable)", len(ids), arcs, reachable+unreachable, unreachable)
}
