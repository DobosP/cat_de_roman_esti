package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"slices"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

func testAuthority() *authority {
	c := &content.Content{
		Nodes: []content.Node{
			{ID: "owner_a", LabelRO: "Alfa"},
			{ID: "owner_b", LabelRO: "Beta"},
			{ID: "n_v1_33_ie", LabelRO: "Ie"},
			{ID: "n_v84_food_sucitor", LabelRO: "Sucitor"},
			{ID: "n_v2art_manastire", LabelRO: "Mănăstire"},
		},
		NormalizedIndex:        map[string]string{"alfa": "owner_a", "beta": "owner_b"},
		NormalizationMap:       map[string]string{"ă": "a", "î": "i", "ș": "s", "Ş": "s", "\u0306": "", "B": "b", "S": "s", "Î": "i"},
		AccentNormalizationMap: map[string]string{"ș": "s\u0326", "ş": "s\u0327"},
	}
	return &authority{graph: graph.New(c), registry: map[string]registryRow{}, denials: map[string][]restriction{},
		inventory: map[string][]restriction{}, stock: map[string][]string{}, families: map[string][]restriction{}}
}

func item(id, owner string, forms ...string) proposal {
	return proposal{ID: id, Kind: "form", OwnerID: owner, Forms: forms}
}

func TestExactAndPolicyBoundaries(t *testing.T) {
	a := testAuthority()
	a.inventory["lume"] = []restriction{{"alchimie_world_collision", "world_lume", "world"}}
	a.inventory["hamburger"] = []restriction{{"cald_projection_collision", "", "cald"}}
	a.denials["vulpoii"] = []restriction{{"owner_hold_adr0210", "owner_b", "adr"}}
	a.families["owner_b"] = []restriction{{"registry_recorded_hold", "owner_b", "legacy"}}
	a.registry["held-board"] = registryRow{State: "held_owner", Type: "board.conexiuni"}
	cases := []struct {
		item   proposal
		reason string
	}{
		{item("collision", "owner_a", "Beta"), "resolver_exact_collision"},
		{item("already", "owner_a", "alfa"), "already_served"},
		{item("projection", "owner_a", "hamburger"), "cald_projection_collision"},
		{item("world", "owner_a", "lume"), "alchimie_world_collision"},
		{item("new-id", "owner_a", "vulpoii"), "owner_hold_adr0210"},
		{item("held-board", "owner_a", "buzunare"), "owner_hold_registry"},
		{item("sucitoare", "owner_a", "Sucitoare"), "owner_hold_bare_sucitoare"},
		{item("ie", "n_v1_33_ie", "Îi"), "owner_hold_ie"},
		{item("sucitor", "n_v84_food_sucitor", "sucitoarele"), "owner_hold_named_family"},
		{item("manastire", "n_v2art_manastire", "mănăstirilor"), "owner_hold_named_family"},
		{item("other-form", "owner_b", "buzunare"), "registry_recorded_hold"},
		{item("runtime-fuzzy-deny", "owner_a", "intrigilor"), "native_fuzzy_deny"},
		{item("runtime-reviewed", "owner_a", "paștele"), "native_reviewed_unresolved"},
		{item("spoof", "owner_a", "suci\u200btoare"), "invalid_surface"},
		{item("mixed-script", "owner_a", "pаste"), "invalid_surface"},
		{item("unknown", "missing", "tamplarului"), "unknown_owner"},
		{proposal{ID: "dim", Kind: "diminutive", OwnerID: "owner_a", Forms: []string{"broscuței"}}, "pilot_diminutive"},
	}
	for _, tc := range cases {
		t.Run(tc.item.ID, func(t *testing.T) {
			results, _ := a.screen([]proposal{tc.item})
			if got := results[0]; got.Reason != tc.reason || len(got.AcceptedForms) != 0 {
				t.Fatalf("result = %+v, wanted reason %s and no forms", got, tc.reason)
			}
		})
	}
}

func TestAtomicBatchAndCoLanding(t *testing.T) {
	a := testAuthority()
	t.Run("a single hold blocks the whole family and dependencies", func(t *testing.T) {
		a1 := item("a", "owner_a", "buzunare", "sucitoare")
		b1 := item("b", "owner_a", "tramvaielor")
		b1.Requires = []string{"a"}
		results, _ := a.screen([]proposal{b1, a1})
		if results[0].Reason != "owner_hold_bare_sucitoare" || results[0].Forms[0].Reason != "family_blocked" ||
			results[1].Reason != "dependency_unavailable" {
			t.Fatalf("unexpected dispositions: %+v", results)
		}
	})
	t.Run("normalized key reuse blocks each claimant", func(t *testing.T) {
		a1 := item("a", "owner_a", "păduri")
		b1 := item("b", "owner_b", "pa\u0306duri")
		results, _ := a.screen([]proposal{a1, b1})
		for _, result := range results {
			if result.Reason != "batch_key_collision" || len(result.AcceptedForms) != 0 {
				t.Fatalf("normalized duplicate survived: %+v", results)
			}
		}
	})
	t.Run("co-landing cannot be partial or asymmetric", func(t *testing.T) {
		a1 := item("a", "owner_a", "tramvaielor", "buzunare")
		b1 := item("b", "owner_b", "firimiturilor")
		a1.CoLanding = []string{"b"}
		results, _ := a.screen([]proposal{a1})
		if results[0].Reason != "co_landing_incomplete" {
			t.Fatalf("missing partner allowed: %+v", results)
		}
		results, _ = a.screen([]proposal{a1, b1})
		if results[0].Reason != "co_landing_incomplete" {
			t.Fatalf("asymmetric group allowed: %+v", results)
		}
		b1.CoLanding = []string{"a"}
		results, _ = a.screen([]proposal{b1, a1})
		if results[0].State != eligible || results[1].State != eligible ||
			!slices.Equal(results[0].AcceptedForms, []string{"buzunare", "tramvaielor"}) {
			t.Fatalf("complete atomic group did not produce sorted forms: %+v", results)
		}
	})
}

func TestRegistryConstraintsCannotBeOmitted(t *testing.T) {
	a := testAuthority()
	group := "joint"
	a1 := item("a", "owner_a", "tramvaielor")
	b1 := item("b", "owner_b", "firimiturilor")
	row := func(item proposal, state string, group *string, dependencies ...string) registryRow {
		r := registryRow{ID: item.ID, State: state, Type: item.Kind, CoLandingGroup: group, Dependencies: dependencies}
		r.Identity.OwnerID = item.OwnerID
		r.Payload.Forms = item.Forms
		return r
	}
	a.registry["a"] = row(a1, "idea", &group, "prerequisite")
	a.registry["b"] = row(b1, "idea", &group)
	a.addRegistryRestrictions()

	results, _ := a.screen([]proposal{a1})
	if results[0].Reason != "co_landing_incomplete" || len(results[0].AcceptedForms) != 0 {
		t.Fatalf("omitted registry group passed: %+v", results)
	}
	renamed := a1
	renamed.ID = "new-id"
	results, _ = a.screen([]proposal{renamed})
	if results[0].Reason != "registry_duplicate" {
		t.Fatalf("new ID bypassed registered group: %+v", results)
	}

	results, _ = a.screen([]proposal{b1, a1})
	if results[0].Reason != "dependency_unavailable" || results[1].Reason != "co_landing_incomplete" {
		t.Fatalf("omitted registry dependency passed or did not propagate to its partner: %+v", results)
	}
	a.registry["prerequisite"] = registryRow{State: "landed"}
	results, _ = a.screen([]proposal{b1, a1})
	if results[0].Reason != eligible || results[1].Reason != eligible {
		t.Fatalf("complete registry group with a landed prerequisite failed: %+v", results)
	}

	a.registry["a"] = row(a1, "idea", nil, b1.ID)
	a.registry["b"] = row(b1, "idea", nil)
	results, _ = a.screen([]proposal{a1})
	if results[0].Reason != "dependency_unavailable" {
		t.Fatalf("omitted same-train dependency passed: %+v", results)
	}
	results, _ = a.screen([]proposal{b1, a1})
	if results[0].Reason != eligible || results[1].Reason != eligible {
		t.Fatalf("same-train registry dependency failed: %+v", results)
	}
}

func TestFuzzyOwnerChangeUsesNativeResolver(t *testing.T) {
	a := testAuthority()
	// The prospective key competes on scriitoarele but has no existing
	// fuzzy resolution of its own.
	a.graph = graph.New(&content.Content{
		Nodes:           []content.Node{{ID: "owner_a", LabelRO: "Scriitor"}, {ID: "owner_b", LabelRO: "Sucitor test"}},
		NormalizedIndex: map[string]string{"xcriitoarele": "owner_a"},
	})
	if got := a.graph.ResolveFuzzy("scriitoarele"); got != "owner_a" {
		t.Fatalf("bad test baseline fuzzy owner %q", got)
	}
	results, changes := a.screen([]proposal{item("test", "owner_b", "scriitoarelz")})
	if results[0].Reason != "fuzzy_neighbor_owner_change" || len(results[0].AcceptedForms) != 0 {
		t.Fatalf("fuzzy owner change not held: %+v", results)
	}
	found := false
	for _, change := range changes {
		if change.Probe == "scriitoarele" && change.BeforeOwner == "owner_a" && change.AfterOwner == "" &&
			slices.Equal(change.ItemIDs, []string{"test"}) {
			found = true
		}
	}
	if !found {
		t.Fatalf("missing native fuzzy change: %+v", changes)
	}
}

func TestStrictInput(t *testing.T) {
	row := `{"id":"clean","kind":"form","owner_id":"owner_a","forms":["arcuri"]}`
	wrap := func(body string) []byte {
		return []byte(`{"schema":"cat-form-screen-input-1","items":[` + body + `]}`)
	}
	if _, err := decodeBatch(wrap(row)); err != nil {
		t.Fatalf("valid envelope refused: %v", err)
	}
	invalid := []string{
		strings.Replace(row, `"id":`, `"ID":`, 1),
		strings.Replace(row, `"clean"`, `"../outside"`, 1),
		strings.Replace(row, `"arcuri"`, `"\ud800"`, 1),
		strings.Replace(row, `"arcuri"`, `null`, 1),
		row + "," + row,
		row[:len(row)-1] + `,"id":"changed"}`,
		row[:len(row)-1] + `,"release_owner_hold":true}`,
		row[:len(row)-1] + `,"requires":["clean"]}`,
		row[:len(row)-1] + `,"co_landing":null}`,
	}
	for _, candidate := range invalid {
		if _, err := decodeBatch(wrap(candidate)); err == nil {
			t.Errorf("untrusted input passed: %s", candidate)
		}
	}
	if _, err := decodeBatch(append(wrap(row), []byte("{}")...)); err == nil {
		t.Fatal("trailing document accepted")
	}
}

func TestRegistryTransitionPreservesConstraints(t *testing.T) {
	group := "joint"
	prior := registryRow{ID: "a", Type: "form", State: "idea", CoLandingGroup: &group, Dependencies: []string{"b"}}
	changed := prior
	changed.State = "screened"
	changed.Dependencies = nil
	if err := checkTransition(nil, prior, changed, nil); err == nil {
		t.Fatal("transition removed a trusted dependency")
	}
	changed = prior
	changed.State = "screened"
	changed.CoLandingGroup = nil
	if err := checkTransition(nil, prior, changed, nil); err == nil {
		t.Fatal("transition removed a trusted co-landing group")
	}
	changed.CoLandingGroup = &group
	if err := checkTransition(nil, prior, changed, nil); err != nil {
		t.Fatalf("unchanged trusted constraints blocked an ordinary transition: %v", err)
	}
}

func TestRegistryRetryNeedsBoundEvidence(t *testing.T) {
	root, err := os.OpenRoot(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer root.Close()
	prior := []byte(`{"schema":"cat-content-candidate-1","event":"create","id":"x","type":"form","state":"held_recorded","label_ro":"Alfa","identity":{"owner_id":"owner_a"},"payload":{"forms":["alfelor"]},"retry_when":{"predicate":"recorded_hold_resolved","ref":"review:1"},"holds":[{"kind":"recorded","ref":"review:1"}]}`)
	canonical, err := canonicalRow(prior)
	if err != nil {
		t.Fatal(err)
	}
	hash := contentbuild.SHA256(canonical)
	evidence := []byte(`{"candidate_id":"x","previous_sha256":"` + hash + `","verdict":"resolved","prerequisite":{"predicate":"recorded_hold_resolved","ref":"review:1"}}`)
	if err := root.WriteFile("evidence.json", evidence, 0600); err != nil {
		t.Fatal(err)
	}
	next := []byte(`{"schema":"cat-content-candidate-1","event":"transition","id":"x","type":"form","state":"idea","identity":{"owner_id":"owner_a"},"payload":{"forms":["alfelor"]},"retry_when":{"predicate":"current_screen_available","ref":"review:1"},"previous_sha256":"` + hash + `","retry_evidence":{"ref":"evidence.json:1","sha256":"` + contentbuild.SHA256(evidence) + `","prerequisite":{"predicate":"recorded_hold_resolved","ref":"review:1"}}}`)
	journal := bytes.Join([][]byte{prior, next, nil}, []byte("\n"))
	rows, err := loadRegistry(root, journal)
	if err != nil || rows["x"].State != "idea" {
		t.Fatalf("bound retry rejected: %v", err)
	}
	changed := bytes.Replace(journal, []byte("evidence.json:1"), []byte("../evidence.json:1"), 1)
	if _, err := loadRegistry(root, changed); err == nil {
		t.Fatal("retry accepted a path escape")
	}
	if err := root.WriteFile("evidence.json", []byte(`{}`), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := loadRegistry(root, journal); err == nil {
		t.Fatal("retry accepted modified bytes")
	}
}

func TestTrustedCheckoutSmoke(t *testing.T) {
	root, err := filepath.Abs("../../..")
	if err != nil {
		t.Fatal(err)
	}
	dir := t.TempDir()
	input := filepath.Join(dir, "input.json")
	proposals := []proposal{
		item("owner-hold", "n_v33_forest_animal_lup", "vulpoii"),
		item("old-exclusion", "n_v30_kitchen_table_castron", "sucitoare"),
		item("already", "n_v2sti_avion", "avioanelor"),
		item("new-form", "n_v2sti_avion", "zzformtestului"),
		item("known-diminutive", "n_v1_8_broasca", "broscuțelor"),
		item("test-exclusion", "n_v20gas_smantana", "smântână dulce"),
	}
	// The CLI treats omitted lists differently from explicitly null lists.
	var items []map[string]any
	for _, p := range proposals {
		items = append(items, map[string]any{"id": p.ID, "owner_id": p.OwnerID, "kind": p.Kind, "forms": p.Forms})
	}
	raw, err := json.Marshal(map[string]any{"schema": inputSchema, "items": items})
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(input, raw, 0600); err != nil {
		t.Fatal(err)
	}
	var out, stderr bytes.Buffer
	args := []string{"--root", root, "--input", input}
	if err := run(args, &out, &stderr); err != nil {
		t.Fatalf("form screen: %v", err)
	}
	var result receipt
	if err := json.Unmarshal(out.Bytes(), &result); err != nil {
		t.Fatal(err)
	}
	wanted := []string{"already_served", "pilot_diminutive", "screened", "owner_hold_bare_sucitoare", "owner_hold_adr0210", "recorded_test_exclusion"}
	var got []string
	for _, item := range result.Items {
		got = append(got, item.Reason)
	}
	if !reflect.DeepEqual(got, wanted) {
		t.Fatalf("dispositions %v, expected %v", got, wanted)
	}
	denial := result.Items[len(result.Items)-1].Forms[0]
	if !slices.Contains(denial.Refs, "tests/test_v88_everyday_graph.py:308") {
		t.Fatalf("missing exact legacy assertion citation: %+v", denial)
	}
	if result.Schema != resultSchema || result.Bindings["input_sha256"] != contentbuild.SHA256(raw) ||
		len(result.Bindings["executable_sha256"]) != 64 || len(result.Bindings["test_exclusions_sha256"]) != 64 {
		t.Fatalf("missing receipt binding: %+v", result.Bindings)
	}
	var repeat bytes.Buffer
	if err := run(args, &repeat, &stderr); err != nil || !bytes.Equal(out.Bytes(), repeat.Bytes()) {
		t.Fatalf("nondeterministic result: %v", err)
	}
}
