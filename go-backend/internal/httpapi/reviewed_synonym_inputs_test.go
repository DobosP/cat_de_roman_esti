package httpapi

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

// Use actual bundled content and ordinary public session creation. Seeds make
// the protocol deterministic; selected targets, release digests and feedback
// ranks are deliberately not part of this lexical/session regression contract.
func TestReviewedSynonymInputsUseOnePublicGuessSlot(t *testing.T) {
	t.Setenv("CAT_ALLOWED_HOSTS", "testserver,example.com")
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	for _, row := range []struct {
		alias, canonical, owner string
		seed                    int
	}{
		{"drapel", "Steag", "n_v4ist_steag", 36},
		{"untdelemn", "Ulei", "n_v24_food_pantry_ulei", 3},
	} {
		t.Run(row.alias, func(t *testing.T) {
			var firstOrderGuess map[string]any
			for _, aliasFirst := range []bool{true, false} {
				t.Run(fmt.Sprintf("alias_first_%t", aliasFirst), func(t *testing.T) {
					s := New(c)
					request := func(method, path string, body any) map[string]any {
						t.Helper()
						var raw []byte
						if body != nil {
							var err error
							raw, err = json.Marshal(body)
							if err != nil {
								t.Fatal(err)
							}
						}
						r := httptest.NewRequest(method, "http://testserver"+path, bytes.NewReader(raw))
						r.Header.Set("Content-Type", "application/json")
						w := httptest.NewRecorder()
						s.ServeHTTP(w, r)
						if w.Code != 200 {
							t.Fatalf("%s %s: %d %s", method, path, w.Code, w.Body.String())
						}
						var reply map[string]any
						if err := json.Unmarshal(w.Body.Bytes(), &reply); err != nil {
							t.Fatal(err)
						}
						assertReviewedInputPrivate(t, reply)
						return reply
					}
					created := request("POST", fmt.Sprintf("/api/wordgames/contexto/games?seed=%d&difficulty=usor", row.seed), nil)
					id, ok := created["game_id"].(string)
					if !ok || id == "" || created["won"] != false || created["attempts"] != float64(0) {
						t.Fatalf("ordinary session creation: %v", created)
					}
					base := "/api/wordgames/contexto/games/" + id
					if recovered := request("GET", base, nil); !reflect.DeepEqual(recovered, created) {
						t.Fatalf("initial recovery changed state: %v", recovered)
					}
					forms := []string{row.alias, row.canonical}
					if !aliasFirst {
						forms[0], forms[1] = forms[1], forms[0]
					}
					forms = append(forms, " \t"+strings.ToUpper(row.alias)+"\n", " "+strings.ToUpper(row.canonical)+" ")
					var expectedGuess map[string]any
					for _, form := range forms {
						reply := request("POST", base+"/guess", map[string]any{"text": form})
						if reply["ok"] != true || reply["won"] != false || reply["needs_confirmation"] == true || reply["attempts"] != float64(1) {
							t.Fatalf("%q did not directly reuse one nonwinning attempt: %v", form, reply)
						}
						guess, ok := reply["guess"].(map[string]any)
						if !ok || guess["id"] != row.owner || guess["label"] != row.canonical || guess["attempt_number"] != float64(1) {
							t.Fatalf("%q resolved to a different canonical identity: %v", form, guess)
						}
						if expectedGuess == nil {
							expectedGuess = guess
						} else if !reflect.DeepEqual(guess, expectedGuess) {
							t.Fatalf("%q changed canonical feedback: %v vs %v", form, guess, expectedGuess)
						}
						guesses, ok := reply["guesses"].([]any)
						if !ok || len(guesses) != 1 || !reflect.DeepEqual(guesses[0], expectedGuess) {
							t.Fatalf("%q created a separate guess slot: %v", form, guesses)
						}
						recovered := request("GET", base, nil)
						for _, key := range []string{"attempts", "guesses", "clues_used", "won"} {
							before, existed := reply[key]
							after, exists := recovered[key]
							if !existed || !exists || !reflect.DeepEqual(before, after) {
								t.Fatalf("%q recovery changed %s: %v vs %v", form, key, before, after)
							}
						}
					}
					if firstOrderGuess == nil {
						firstOrderGuess = expectedGuess
					} else if !reflect.DeepEqual(firstOrderGuess, expectedGuess) {
						t.Fatalf("alias-first and canonical-first feedback differ: %v vs %v", firstOrderGuess, expectedGuess)
					}
				})
			}
		})
	}
}

func assertReviewedInputPrivate(t *testing.T, value any) {
	t.Helper()
	switch v := value.(type) {
	case map[string]any:
		for key, child := range v {
			switch key {
			case "target", "solution", "score", "share", "curated_id", "curatedId":
				t.Fatalf("unrevealed input response exposed private field %q", key)
			}
			assertReviewedInputPrivate(t, child)
		}
	case []any:
		for _, child := range v {
			assertReviewedInputPrivate(t, child)
		}
	}
}
