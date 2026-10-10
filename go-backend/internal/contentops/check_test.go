package contentops

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestNativeSidecarFormatAndMeaning(t *testing.T) {
	want := Object{"meta": Object{"kg_sha256": "bound", "counts": Object{"boards": 2}}, "boards": []any{
		Object{"id": "a", "pilot_score": 90, "rank": 1, "selection_weight": 5},
		Object{"id": "b", "pilot_score": 80, "rank": 2, "selection_weight": 4},
	}}
	blob, err := render(want)
	if err != nil {
		t.Fatal(err)
	}
	decoded, err := Decode(blob)
	if err != nil {
		t.Fatal(err)
	}
	again, err := render(decoded)
	if err != nil || !bytes.Equal(blob, again) {
		t.Fatal("native formatter is not stable")
	}
	s := &Sources{Root: t.TempDir()}
	writeCopies := func(value any) {
		for _, rel := range []string{fixtures + "board_rankings_v37.json", "tests/fixtures/board_rankings_v37.json"} {
			put(t, filepath.Join(s.Root, rel), value)
		}
	}
	writeCopies(blob)
	report, err := s.sidecar(want, "board_rankings_v37.json", false)
	if err != nil || requireNativeFormat(report, "rank") != nil {
		t.Fatalf("native bytes refused: %v", err)
	}
	// JSON map order and whitespace do not change meaning, but the native
	// physical format is a separate, explicit regeneration requirement.
	meta, err := json.Marshal(want["meta"])
	if err != nil {
		t.Fatal(err)
	}
	boards, err := json.Marshal(want["boards"])
	if err != nil {
		t.Fatal(err)
	}
	other := []byte(fmt.Sprintf(`{"meta":%s,"boards":%s}`, meta, boards))
	writeCopies(other)
	report, err = s.sidecar(want, "board_rankings_v37.json", false)
	if err != nil || report["semantic_match"] != true {
		t.Fatalf("equivalent JSON meaning refused: %v", err)
	}
	if err = requireNativeFormat(report, "rank"); err == nil || !strings.Contains(err.Error(), "format_drift") || !strings.Contains(err.Error(), "rank --root ROOT --write") {
		t.Fatalf("missing actionable format refusal: %v", err)
	}
	for _, field := range []string{"pilot_score", "rank", "selection_weight", "binding", "array_order", "type", "duplicate"} {
		t.Run(field, func(t *testing.T) {
			changed, err := Decode(blob)
			if err != nil {
				t.Fatal(err)
			}
			rows := array(changed["boards"])
			switch field {
			case "binding":
				obj(changed["meta"])["kg_sha256"] = "other"
			case "array_order":
				rows[0], rows[1] = rows[1], rows[0]
			case "type":
				obj(rows[0])["rank"] = "1"
			case "duplicate":
				writeCopies([]byte(`{"meta":{},"meta":{},"boards":[]}`))
			default:
				obj(rows[0])[field] = 0
			}
			if field != "duplicate" {
				writeCopies(changed)
			}
			if _, err = s.sidecar(want, "board_rankings_v37.json", false); err == nil {
				t.Fatal("sidecar drift accepted")
			}
		})
	}
}

// Copy only the existing source read set to an owned test root. Source fixtures
// are never edited in place, and native sidecars are produced by their builders.
func nativeCheckRoot(t *testing.T) string {
	t.Helper()
	s, err := LoadSources(repoRoot(t))
	if err != nil {
		t.Fatal(err)
	}
	rank, err := s.generateRankings()
	if err != nil {
		t.Fatal(err)
	}
	root := t.TempDir()
	for name, snap := range s.Inputs {
		if snap.exists {
			rel, err := filepath.Rel(s.Root, name)
			if err != nil || strings.HasPrefix(rel, "..") {
				t.Fatal("source read set escaped root")
			}
			put(t, filepath.Join(root, rel), snap.blob)
		}
	}
	put(t, filepath.Join(root, fixtures+"board_rankings_v37.json"), rank)
	put(t, filepath.Join(root, "tests/fixtures/board_rankings_v37.json"), rank)
	staged, err := LoadSources(root)
	if err != nil {
		t.Fatal(err)
	}
	derived, err := staged.generateDerived()
	if err != nil {
		t.Fatal(err)
	}
	put(t, filepath.Join(root, fixtures+"derived_catalog_v38.json"), derived)
	put(t, filepath.Join(root, "tests/fixtures/derived_catalog_v38.json"), derived)
	return root
}

func TestCheckReadonlyAndRefusals(t *testing.T) {
	root := nativeCheckRoot(t)
	s, err := LoadSources(root)
	if err != nil {
		t.Fatal(err)
	}
	report, err := s.Check()
	if err != nil || integer(report["boards"]) != 716 || report["write"] != false {
		t.Fatalf("native check: %v, %v", report, err)
	}
	if err = checkSnapshots(s.Inputs); err != nil {
		t.Fatal("check modified source: ", err)
	}
	// Invalid graph shapes and references fail even with identical mirrors.
	_, original, err := read(filepath.Join(root, fixtures+"kg_sample.json"))
	if err != nil {
		t.Fatal(err)
	}
	for _, kind := range []string{"reference", "type", "duplicate_id", "duplicate_key"} {
		t.Run(kind, func(t *testing.T) {
			kg, err := Decode(original)
			if err != nil {
				t.Fatal(err)
			}
			switch kind {
			case "reference":
				obj(array(kg["kg_edges"])[0])["src_id"] = "n_missing_check_control"
			case "type":
				obj(array(kg["kg_nodes"])[0])["salience"] = "high"
			case "duplicate_id":
				nodes := array(kg["kg_nodes"])
				obj(nodes[1])["id"] = obj(nodes[0])["id"]
			}
			for _, rel := range []string{fixtures + "kg_sample.json", "tests/fixtures/kg_sample.json"} {
				if kind == "duplicate_key" {
					put(t, filepath.Join(root, rel), []byte(`{"kg_nodes":[],"kg_nodes":[]}`))
				} else {
					put(t, filepath.Join(root, rel), kg)
				}
			}
			if err = Run([]string{"check", "--root", root}, &bytes.Buffer{}); err == nil {
				t.Fatalf("invalid graph %s accepted", kind)
			}
		})
	}
	put(t, filepath.Join(root, fixtures+"kg_sample.json"), original)
	put(t, filepath.Join(root, "tests/fixtures/kg_sample.json"), original)
	put(t, filepath.Join(root, "tests/fixtures/games_pack.json"), []byte("{}"))
	if _, err = LoadSources(root); err == nil || !strings.Contains(err.Error(), "pack mirror drift") {
		t.Fatalf("mirror drift accepted: %v", err)
	}
}

func TestCheckSourceAndInventoryChangesRefused(t *testing.T) {
	for _, kind := range []string{"bytes", "mode", "inventory"} {
		t.Run(kind, func(t *testing.T) {
			s := syntheticSource(t)
			path := filepath.Join(s.Root, "docs/CRITIQUE_RUBRIC.md")
			switch kind {
			case "bytes":
				put(t, path, []byte("changed rubric"))
			case "mode":
				if err := os.Chmod(path, 0400); err != nil {
					t.Fatal(err)
				}
			case "inventory":
				put(t, filepath.Join(s.Root, "go-backend/new_policy.go"), []byte("package policy\n"))
			}
			if _, err := s.Check(); err == nil || (!strings.Contains(err.Error(), "source changed") && !strings.Contains(err.Error(), "inventory changed")) {
				t.Fatalf("changed %s was not refused before validation: %v", kind, err)
			}
		})
	}
}

func TestCheckWriteRefusedBeforeSourceLoad(t *testing.T) {
	root := filepath.Join(t.TempDir(), "absent")
	if err := Run([]string{"check", "--root", root, "--write"}, &bytes.Buffer{}); err == nil || !strings.Contains(err.Error(), "check is read only") {
		t.Fatalf("write was not refused before source access: %v", err)
	}
	if _, err := os.Stat(root); !os.IsNotExist(err) {
		t.Fatal("write refusal created a source root")
	}
}

func BenchmarkReviewedRankings(b *testing.B) {
	root, err := filepath.Abs("../../..")
	if err != nil {
		b.Fatal(err)
	}
	s, err := LoadSources(root)
	if err != nil {
		b.Fatal(err)
	}
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		result, err := s.generateRankings()
		if err != nil || len(array(result["boards"])) != 716 {
			b.Fatalf("full reviewed ranking: %v", err)
		}
	}
}
