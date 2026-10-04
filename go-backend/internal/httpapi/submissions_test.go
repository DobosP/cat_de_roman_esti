package httpapi

import (
	"encoding/json"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

type proposalVector struct {
	Name, Game string
	Item       map[string]any
	Valid      bool
}

func proposalVectors(t *testing.T) []proposalVector {
	t.Helper()
	raw, err := os.ReadFile("testdata/submissions_python.json")
	if err != nil {
		t.Fatal(err)
	}
	var vectors []proposalVector
	if json.Unmarshal(raw, &vectors) != nil {
		t.Fatal("invalid oracle")
	}
	return vectors
}
func TestNativeProposalValidatorsAgainstPython(t *testing.T) {
	s := testServer(t)
	for _, v := range proposalVectors(t) {
		t.Run(v.Name, func(t *testing.T) {
			category, _ := v.Item["category"].(string)
			difficulty, _ := v.Item["difficulty"].(string)
			errors := s.validateSubmission(v.Game, category, difficulty, v.Item)
			if (len(errors) == 0) != v.Valid {
				t.Fatalf("gate differs reference: %v", errors)
			}
		})
	}
}
func TestProposalQueueIsPendingPrivateAndBounded(t *testing.T) {
	s := testServer(t)
	directory := t.TempDir()
	t.Setenv("CAT_SUBMISSIONS_DIR", directory)
	v := proposalVectors(t)[0]
	payload := map[string]any{"game": v.Game, "category": v.Item["category"], "difficulty": v.Item["difficulty"], "payload": v.Item, "author": "synthetic fixture"}
	raw, _ := json.Marshal(payload)
	send := func(body string, peer string) *httptest.ResponseRecorder {
		request := httptest.NewRequest("POST", "/api/submissions", strings.NewReader(body))
		request.RemoteAddr = peer
		response := httptest.NewRecorder()
		s.ServeHTTP(response, request)
		return response
	}
	response := send(string(raw), "127.0.0.1:3210")
	if response.Code != 202 {
		t.Fatalf("proposal %d %s", response.Code, response.Body.String())
	}
	file := filepath.Join(directory, "submissions.jsonl")
	contents, err := os.ReadFile(file)
	if err != nil {
		t.Fatal(err)
	}
	var record map[string]any
	if json.Unmarshal(contents, &record) != nil {
		t.Fatal("invalid queued JSON")
	}
	item := record["item"].(map[string]any)
	if item["status"] != "pending" || item["source"] != "user" {
		t.Fatal("unreviewed submission cannot publish")
	}
	info, _ := os.Stat(file)
	if info.Mode().Perm() != 0600 {
		t.Fatal("queue is not private")
	}
	if got := send(string(raw)+"{}", "127.0.0.2:3210").Code; got != 422 {
		t.Fatal("trailing JSON accepted", got)
	}
	for i := 1; i < 10; i++ {
		if send(string(raw), "127.0.0.1:3210").Code != 202 {
			t.Fatal("rate window unexpectedly exhausted")
		}
	}
	if got := send(string(raw), "127.0.0.1:3210").Code; got != 429 {
		t.Fatal("rate budget bypass", got)
	}
	size, _ := os.Stat(file)
	if size.Size() != int64(len(contents)*10) {
		t.Fatal("rejected input changed queue")
	}
}
func TestProposalQueueRejectsSymlinkAndFullFile(t *testing.T) {
	for _, kind := range []string{"symlink", "full"} {
		t.Run(kind, func(t *testing.T) {
			s := testServer(t)
			dir := t.TempDir()
			t.Setenv("CAT_SUBMISSIONS_DIR", dir)
			path := filepath.Join(dir, "submissions.jsonl")
			if kind == "symlink" {
				target := filepath.Join(t.TempDir(), "outside")
				if err := os.WriteFile(target, []byte("keep"), 0600); err != nil {
					t.Fatal(err)
				}
				if err := os.Symlink(target, path); err != nil {
					t.Fatal(err)
				}
			} else {
				f, err := os.Create(path)
				if err != nil {
					t.Fatal(err)
				}
				_ = f.Truncate(32 << 20)
				_ = f.Close()
			}
			v := proposalVectors(t)[0]
			raw, _ := json.Marshal(map[string]any{"game": v.Game, "category": v.Item["category"], "difficulty": v.Item["difficulty"], "payload": v.Item})
			request := httptest.NewRequest("POST", "/api/submissions", strings.NewReader(string(raw)))
			response := httptest.NewRecorder()
			s.ServeHTTP(response, request)
			if response.Code != 503 {
				t.Fatal("unsafe queue accepted", response.Code)
			}
		})
	}
}
