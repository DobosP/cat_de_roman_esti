package budget_test

import (
	"encoding/json"
	"os"
	"testing"

	"github.com/DobosP/roedu-ui/web-kit/budget"
)

// The Node schema tests consume this same owned matrix. Its base is the exact
// committed budget seed copied into this module, so standalone Go archives
// never depend on a source-external fixture or the repository root.
func TestBudgetSchemaSharedMatrix(t *testing.T) {
	base, err := os.ReadFile("testdata/budgets.seed.json")
	if err != nil { t.Fatal(err) }
	if _, err := budget.Load(base); err != nil { t.Fatalf("actual seed fixture rejected: %v",err) }
	data, err := os.ReadFile("testdata/schema-cases.json")
	if err != nil { t.Fatal(err) }
	var cases []struct {
		Name string `json:"name"`
		Valid bool `json:"valid"`
		Pointer []string `json:"pointer"`
		Value json.RawMessage `json:"value"`
		Drop bool `json:"drop"`
	}
	if err := json.Unmarshal(data,&cases); err != nil { t.Fatal(err) }
	if len(cases)==0 { t.Fatal("shared schema matrix is empty") }
	for _, tc := range cases {
		t.Run(tc.Name,func(t *testing.T) {
			if tc.Name=="" || len(tc.Pointer)==0 || (tc.Drop&&len(tc.Value)>0) || (!tc.Drop&&len(tc.Value)==0) { t.Fatal("invalid schema matrix case") }
			var document map[string]any
			if err := json.Unmarshal(base,&document); err != nil { t.Fatal(err) }
			current := document
			for _, key := range tc.Pointer[:len(tc.Pointer)-1] {
				next, ok := current[key].(map[string]any)
				if !ok { t.Fatalf("matrix path traverses a non-object: %s",key) }
				current = next
			}
			key := tc.Pointer[len(tc.Pointer)-1]
			if tc.Drop {
				if _,present:=current[key];!present { t.Fatal("matrix drops an absent property") }
				delete(current,key)
			} else {
				var value any
				if err := json.Unmarshal(tc.Value,&value); err != nil { t.Fatal(err) }
				current[key] = value
			}
			mutated, err := json.Marshal(document)
			if err != nil { t.Fatal(err) }
			_, err = budget.Load(mutated)
			if (err==nil)!=tc.Valid { t.Fatalf("valid=%v, Load error=%v",tc.Valid,err) }
		})
	}
}
