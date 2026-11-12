package contentrails

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func replaceSourceOperationFile(t *testing.T, path string, changed []byte) []byte {
	t.Helper()
	original, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	info, err := os.Stat(path)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := os.WriteFile(path, original, info.Mode().Perm()); err != nil {
			t.Error(err)
		}
	})
	if err = os.WriteFile(path, changed, info.Mode().Perm()); err != nil {
		t.Fatal(err)
	}
	return original
}

// These are synthetic contract/refusal controls. The unfiltered current-source
// CheckAll, focused and whole native suites remain separate required evidence.
func TestInstalledSourceOperationBoundariesAndIsolation(t *testing.T) {
	f := installedFixtureForTest(t)
	a := authorityForTest(t, f.manifest)
	operation, err := a.captureSourceOperation(f.root)
	if err != nil {
		t.Fatal(err)
	}
	if err = operation.verify(f.root, a); err != nil {
		t.Fatal(err)
	}
	sourcePath := filepath.Join(f.root, text(object(rows(f.manifest["source_chain"])[0])["path"]))
	archivePath := filepath.Join(f.root, text(object(object(f.source.Raw["archives"])["quick_candidate"])["path"]))
	original := operation.source(f.source.SHA256)
	if original == nil || !same(original.Raw, f.source.Raw) {
		t.Fatal("authentic decoded source missing")
	}

	t.Run("private-deep-source-copies", func(t *testing.T) {
		first, second := operation.source(f.source.SHA256), operation.source(f.source.SHA256)
		object(rows(object(first.Raw["quick"])["boards"])[0])["id"] = "mutated-private-board"
		rows(rows(object(first.Raw["world"])["recipes"])[0])[0] = "mutated-private-recipe"
		object(object(first.Raw["archives"])["quick_candidate"])["path"] = "docs/reviews/private-only.json"
		rows(object(first.Raw["quick"])["boards"])[0] = nil
		if !same(second.Raw, original.Raw) || !same(operation.source(f.source.SHA256).Raw, original.Raw) {
			t.Fatal("mutable nested JSON escaped between source copies")
		}
		if _, ok := second.Raw["version"].(json.Number); !ok {
			t.Fatal("source copy changed decoded scalar types")
		}
		if operation.source("not-registered") != nil {
			t.Fatal("unknown source obtained cached authority")
		}
	})

	t.Run("all-registered-document-occurrences-preserved", func(t *testing.T) {
		expected := map[installedSourceDocument]int{}
		for _, value := range rows(a.raw["source_chain"]) {
			entry := object(value)
			expected[installedSourceDocument{text(entry["path"]), text(entry["sha256"])}]++
			for _, value := range object(operation.sources[text(entry["sha256"])].Raw["archives"]) {
				descriptor := object(value)
				expected[installedSourceDocument{text(descriptor["path"]), text(descriptor["sha256"])}]++
			}
		}
		actual := map[installedSourceDocument]int{}
		for _, document := range operation.documents {
			actual[document]++
		}
		if len(actual) != len(expected) {
			t.Fatal("document membership changed")
		}
		for document, count := range expected {
			if actual[document] != count {
				t.Fatal("source/archive occurrence omitted or duplicated", document.path)
			}
		}
	})

	for _, stage := range []string{"before", "after"} {
		for _, member := range []struct{ name, path string }{{"source", sourcePath}, {"archive", archivePath}} {
			t.Run(stage+"-"+member.name+"-permanent-byte-drift", func(t *testing.T) {
				body, err := os.ReadFile(member.path)
				if err != nil {
					t.Fatal(err)
				}
				if stage == "before" {
					replaceSourceOperationFile(t, member.path, append(append([]byte(nil), body...), '\n'))
				}
				called := false
				_, err = operation.withSource(f.root, a, f.source.SHA256, func(source *Source) (map[string]any, error) {
					called = true
					if stage == "after" {
						replaceSourceOperationFile(t, member.path, append(append([]byte(nil), body...), '\n'))
					}
					return source.Raw, nil
				})
				if err == nil || called != (stage == "after") {
					t.Fatal("source/archive pre/post guard did not stop changed input", stage, called, err)
				}
				if _, _, err := a.rebuildFromSourceOperation(f.root, f.selected, "quick", operation); err == nil {
					t.Fatal("adopted reconstruction ignored changed operation input")
				}
				if !same(operation.source(f.source.SHA256).Raw, original.Raw) {
					t.Fatal("live drift changed captured decoded source")
				}
			})
		}
	}

	for _, member := range []struct{ name, path string }{{"source", sourcePath}, {"archive", archivePath}} {
		t.Run(member.name+"-transient-edit-restore", func(t *testing.T) {
			body, err := os.ReadFile(member.path)
			if err != nil {
				t.Fatal(err)
			}
			result, err := operation.withSource(f.root, a, f.source.SHA256, func(source *Source) (map[string]any, error) {
				replaceSourceOperationFile(t, member.path, []byte(`{"transient":"unreviewed"}`))
				if err := operation.verify(f.root, a); err == nil {
					t.Fatal("visible transient drift passed boundary")
				}
				if _, err := a.captureSourceOperation(f.root); err == nil {
					t.Fatal("new operation inherited old decoding across transient drift")
				}
				// The private source passed into the real operation guard can
				// only contain original reviewed JSON, even across edit/undo.
				if !same(source.Raw, original.Raw) || !same(operation.source(f.source.SHA256).Raw, original.Raw) {
					t.Fatal("transient live body contaminated captured source")
				}
				if err := os.WriteFile(member.path, body, 0600); err != nil {
					t.Fatal(err)
				}
				return source.Raw, nil
			})
			if err != nil || !same(result, original.Raw) {
				t.Fatal("edit/restore produced anything but original captured source or refusal", err)
			}
		})
	}

	t.Run("exact-root-and-registered-membership", func(t *testing.T) {
		if err := operation.verify(t.TempDir(), a); err == nil {
			t.Fatal("operation reused for another root")
		}
		mutations := []func(map[string]any){
			func(raw map[string]any) { raw["source_chain"] = []any{} },
			func(raw map[string]any) {
				raw["source_chain"] = append(rows(raw["source_chain"]), copyJSONForTest(rows(raw["source_chain"])[0]))
			},
			func(raw map[string]any) {
				object(rows(raw["source_chain"])[0])["path"] = "docs/reviews/other-source.json"
			},
			func(raw map[string]any) { delete(object(raw["rails"]), "quick") },
			func(raw map[string]any) { delete(object(object(raw["rails"])["quick"]), "quality_review") },
			func(raw map[string]any) { raw["unregistered"] = true },
		}
		for index, mutate := range mutations {
			for _, stage := range []string{"before", "after"} {
				changed := copyJSONForTest(a.raw).(map[string]any)
				if stage == "before" {
					mutate(changed)
				}
				called := false
				_, err := operation.withSource(f.root, &installedAuthorities{raw: changed}, f.source.SHA256, func(source *Source) (map[string]any, error) {
					called = true
					if stage == "after" {
						mutate(changed)
					}
					return source.Raw, nil
				})
				if err == nil || called != (stage == "after") {
					t.Fatal("authority membership changed across operation boundary", index, stage, called, err)
				}
			}
		}
		if err := operation.verify(f.root, a); err != nil {
			t.Fatal("membership test changed original authority", err)
		}
	})

	for _, relative := range []string{installedManifestPath, installedPinPath} {
		t.Run("compiled-metadata-still-bound-"+filepath.Base(relative), func(t *testing.T) {
			path := filepath.Join(f.root, relative)
			body, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			replaceSourceOperationFile(t, path, append(body, '\n'))
			if err := operation.verify(f.root, a); err == nil {
				t.Fatal("operation bypassed compiled metadata source guard")
			}
		})
	}

	for _, member := range []struct{ name, path string }{{"source", sourcePath}, {"archive", archivePath}} {
		t.Run(member.name+"-missing-or-same-byte-symlink", func(t *testing.T) {
			backup := member.path + ".operation-test-original"
			if err := os.Rename(member.path, backup); err != nil {
				t.Fatal(err)
			}
			t.Cleanup(func() {
				_ = os.Remove(member.path)
				if err := os.Rename(backup, member.path); err != nil {
					t.Error(err)
				}
			})
			if err := operation.verify(f.root, a); err == nil {
				t.Fatal("missing registered document passed")
			}
			if err := os.Symlink(backup, member.path); err != nil {
				t.Fatal(err)
			}
			if err := operation.verify(f.root, a); err == nil {
				t.Fatal("same-byte symlink passed strong reader")
			}
		})
	}
}

func TestInstalledSourceOperationsDoNotRememberStandaloneApproval(t *testing.T) {
	f := installedFixtureForTest(t)
	a := authorityForTest(t, f.manifest)
	first, adopted, err := a.rebuild(f.root, f.selected, "quick")
	if err != nil || !adopted {
		t.Fatal("genuine reviewed synthetic authority refused", err)
	}
	firstBytes, err := Render(first)
	if err != nil || digestBytes(firstBytes) != f.entry["artifact_sha256"] {
		t.Fatal("original exact reviewed artifact lost", err)
	}
	for _, descriptor := range []map[string]any{
		object(rows(f.manifest["source_chain"])[0]),
		object(object(f.source.Raw["archives"])["quick_candidate"]),
	} {
		path := filepath.Join(f.root, text(descriptor["path"]))
		body, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		if err = os.WriteFile(path, append(append([]byte(nil), body...), '\n'), 0600); err != nil {
			t.Fatal(err)
		}
		_, _, refused := a.rebuild(f.root, f.selected, "quick")
		if err = os.WriteFile(path, body, 0600); err != nil {
			t.Fatal(err)
		}
		if refused == nil {
			t.Fatal("new top-level rebuild remembered approval from earlier call")
		}
	}
	second, adopted, err := a.rebuild(f.root, f.selected, "quick")
	if err != nil || !adopted {
		t.Fatal("restored authentic standalone rebuild refused", err)
	}
	secondBytes, err := Render(second)
	if err != nil || !bytes.Equal(firstBytes, secondBytes) {
		t.Fatal("new operation changed authentic reviewed result", err)
	}
}
