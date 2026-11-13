package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/fs"
	"maps"
	"os"
	"path"
	"reflect"
	"regexp"
	"slices"
	"strconv"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
)

const (
	bundlePath     = "go-backend/internal/content/bundled.json"
	fixturePath    = "cat_de_roman_esti/fixtures/kg_sample.json"
	registryPath   = "docs/content-registry/registry.jsonl"
	exclusionsPath = "docs/content-registry/exclusions.json"
	graphSource    = "go-backend/internal/graph/service.go"
)

type authority struct {
	graph     *graph.Service
	registry  map[string]registryRow
	denials   map[string][]restriction
	inventory map[string][]restriction
	stock     map[string][]string
	families  map[string][]restriction
}

type restriction struct {
	code  string
	owner string
	ref   string
}

type registryRow struct {
	Schema         string   `json:"schema"`
	ID             string   `json:"id"`
	Type           string   `json:"type"`
	Event          string   `json:"event"`
	State          string   `json:"state"`
	Previous       string   `json:"previous_sha256"`
	Label          string   `json:"label_ro"`
	Dependencies   []string `json:"dependencies"`
	CoLandingGroup *string  `json:"co_landing_group"`
	Identity       struct {
		OwnerID string `json:"owner_id"`
		Sense   string `json:"sense"`
	} `json:"identity"`
	Payload struct {
		NodeID    string   `json:"node_id"`
		Forms     []string `json:"forms"`
		HeldForms []string `json:"held_forms"`
	} `json:"payload"`
	Retry struct {
		Predicate string `json:"predicate"`
		Ref       string `json:"ref"`
	} `json:"retry_when"`
	Holds []struct {
		Kind string `json:"kind"`
		Ref  string `json:"ref"`
	} `json:"holds"`
	Line int `json:"-"`
}

func loadAuthority(root *os.Root) (*authority, map[string]string, error) {
	bundle, err := readRegular(root, bundlePath, maxAuthority)
	if err != nil {
		return nil, nil, err
	}
	// The same digest check as the server establishes which stock the binary uses.
	sealed, err := content.Load()
	if err != nil {
		return nil, nil, err
	}
	bundleHash := contentbuild.SHA256(bundle)
	build, err := content.Decode(bundle)
	if err != nil {
		return nil, nil, err
	}
	if len(build.NormalizedIndex) == 0 || len(build.NormalizationMap) == 0 || !reflect.DeepEqual(build, sealed) {
		return nil, nil, fmt.Errorf("resolver bundle differs from the compiled worktree")
	}
	bindings := map[string]string{"bundle_sha256": bundleHash}
	for _, name := range slices.Sorted(maps.Keys(sealed.Sources)) {
		expected := sealed.Sources[name]
		if path.Base(name) != name || !fs.ValidPath(name) {
			return nil, nil, fmt.Errorf("unexpected sealed source name")
		}
		fixture, err := readRegular(root, path.Join(path.Dir(fixturePath), name), maxAuthority)
		if err != nil {
			return nil, nil, err
		}
		// Export source digests use the native portable text hashing contract.
		if contentbuild.TextSHA256(fixture) != expected {
			return nil, nil, fmt.Errorf("%s differs from the compiled content export", name)
		}
		if name == path.Base(fixturePath) {
			bindings["kg_sha256"] = contentbuild.SHA256(fixture)
		}
	}
	state := &authority{
		graph: graph.New(sealed), denials: map[string][]restriction{},
		inventory: map[string][]restriction{}, stock: map[string][]string{}, families: map[string][]restriction{},
	}
	if err := state.addInventory(); err != nil {
		return nil, nil, err
	}

	journal, err := readRegular(root, registryPath, maxAuthority)
	if err != nil {
		return nil, nil, err
	}
	state.registry, err = loadRegistry(root, journal)
	if err != nil {
		return nil, nil, err
	}
	state.addRegistryRestrictions()
	bindings["registry_sha256"] = contentbuild.SHA256(journal)

	exclusions, err := readRegular(root, exclusionsPath, maxAuthority)
	if err != nil {
		return nil, nil, err
	}
	if err := state.addExclusions(exclusions); err != nil {
		return nil, nil, err
	}
	bindings["exclusions_sha256"] = contentbuild.SHA256(exclusions)
	bindings["history_sha256"], err = state.addHistory(root)
	if err != nil {
		return nil, nil, err
	}
	bindings["test_exclusions_sha256"], err = state.addTestExclusions(root)
	if err != nil {
		return nil, nil, err
	}
	return state, bindings, nil
}

func loadRegistry(root *os.Root, raw []byte) (map[string]registryRow, error) {
	if len(raw) == 0 || raw[len(raw)-1] != '\n' {
		return nil, fmt.Errorf("empty or unterminated registry")
	}
	rows := map[string]registryRow{}
	previous := map[string][]byte{}
	for index, line := range bytes.Split(raw[:len(raw)-1], []byte("\n")) {
		if len(line) > 256<<10 {
			return nil, fmt.Errorf("oversized registry line %d", index+1)
		}
		var row registryRow
		if strictjson.Validate(line) != nil || json.Unmarshal(line, &row) != nil ||
			row.Schema != "cat-content-candidate-1" || row.ID == "" || row.Type == "" ||
			!validRegistryState(row.State) || row.Retry.Predicate == "" {
			return nil, fmt.Errorf("invalid registry line %d", index+1)
		}
		row.Line = index + 1
		if row.CoLandingGroup != nil && !identifier.MatchString(*row.CoLandingGroup) {
			return nil, fmt.Errorf("invalid registry co-landing group on line %d", row.Line)
		}
		seen := map[string]bool{row.ID: true}
		for _, dependency := range row.Dependencies {
			if !identifier.MatchString(dependency) || seen[dependency] {
				return nil, fmt.Errorf("invalid registry dependency on line %d", row.Line)
			}
			seen[dependency] = true
		}
		prior, exists := rows[row.ID]
		switch row.Event {
		case "create":
			if exists || row.Previous != "" || slices.Index(registryPipeline, row.State) > 0 ||
				strings.HasPrefix(row.State, "retracted(") {
				return nil, fmt.Errorf("invalid registry creation on line %d", row.Line)
			}
		case "transition":
			if !exists || prior.Identity != row.Identity || prior.Type != row.Type ||
				prior.State == "held_owner" {
				return nil, fmt.Errorf("invalid registry transition on line %d", row.Line)
			}
			canonical, err := canonicalRow(previous[row.ID])
			if err != nil || contentbuild.SHA256(canonical) != row.Previous {
				return nil, fmt.Errorf("invalid registry predecessor on line %d", row.Line)
			}
			if err := checkTransition(root, prior, row, line); err != nil {
				return nil, fmt.Errorf("registry line %d: %w", row.Line, err)
			}
		default:
			return nil, fmt.Errorf("invalid registry event on line %d", row.Line)
		}
		if row.State == "held_owner" && row.Retry.Predicate != "never" ||
			(row.State == "held_owner" || row.State == "held_recorded") && len(row.Holds) == 0 {
			return nil, fmt.Errorf("invalid hold on registry line %d", row.Line)
		}
		rows[row.ID] = row
		previous[row.ID] = line
	}
	return rows, nil
}

var registryPipeline = []string{"idea", "screened", "sourced", "authored", "reviewed", "qualified", "landed"}
var parameterizedState = regexp.MustCompile(`^(?:parked|retracted)\([^()\n]+\)$`)
var retryReference = regexp.MustCompile(`^([^:\\\x00\r\n]+):([1-9][0-9]*)$`)

func validRegistryState(state string) bool {
	return slices.Contains(registryPipeline, state) ||
		slices.Contains([]string{"rejected", "duplicate", "already_served", "held_owner", "held_recorded"}, state) ||
		parameterizedState.MatchString(state)
}

func checkTransition(root *os.Root, prior, current registryRow, raw []byte) error {
	if prior.Type == "form" || prior.Type == "synonym" {
		for _, dependency := range prior.Dependencies {
			if !slices.Contains(current.Dependencies, dependency) {
				return fmt.Errorf("transition removed its registry dependency")
			}
		}
		if prior.CoLandingGroup != nil &&
			(current.CoLandingGroup == nil || *current.CoLandingGroup != *prior.CoLandingGroup) {
			return fmt.Errorf("transition changed its registry co-landing group")
		}
	}
	stage := slices.Index(registryPipeline, current.State)
	if stage > 0 && prior.State != registryPipeline[stage-1] {
		return fmt.Errorf("transition skipped a gate")
	}
	if prior.State == "landed" && !strings.HasPrefix(current.State, "retracted(") {
		return fmt.Errorf("landed state requires retraction")
	}
	if (prior.State == "rejected" || prior.State == "duplicate" || strings.HasPrefix(prior.State, "retracted(")) &&
		current.State != prior.State {
		return fmt.Errorf("terminal registry state changed")
	}
	if prior.State != "held_recorded" && prior.State != "already_served" && !strings.HasPrefix(prior.State, "parked(") {
		return nil
	}
	if current.State == prior.State {
		if prior.Retry != current.Retry || !slices.Equal(prior.Holds, current.Holds) ||
			!slices.Equal(prior.Payload.Forms, current.Payload.Forms) ||
			!slices.Equal(prior.Payload.HeldForms, current.Payload.HeldForms) {
			return fmt.Errorf("transition changed its prerequisite")
		}
		return nil
	}
	if current.State != "idea" || prior.Retry.Predicate == "owner_answer" || prior.Retry.Predicate == "never" {
		return fmt.Errorf("registry prerequisite remains in force")
	}
	var event struct {
		Evidence struct {
			Ref          string `json:"ref"`
			SHA          string `json:"sha256"`
			Prerequisite struct {
				Predicate string `json:"predicate"`
				Ref       string `json:"ref"`
			} `json:"prerequisite"`
		} `json:"retry_evidence"`
	}
	if err := json.Unmarshal(raw, &event); err != nil || event.Evidence.Prerequisite != prior.Retry {
		return fmt.Errorf("missing exact retry evidence")
	}
	parts := retryReference.FindStringSubmatch(event.Evidence.Ref)
	if root == nil || parts == nil {
		return fmt.Errorf("invalid retry evidence reference")
	}
	line, err := strconv.Atoi(parts[2])
	if err != nil {
		return fmt.Errorf("invalid retry evidence line")
	}
	bytesAtRef, err := readRegular(root, parts[1], 16<<20)
	if err != nil || contentbuild.SHA256(bytesAtRef) != event.Evidence.SHA {
		return fmt.Errorf("invalid retry evidence digest")
	}
	lines := bytes.Split(bytesAtRef, []byte("\n"))
	if line > len(lines) {
		return fmt.Errorf("missing retry evidence line")
	}
	record := lines[line-1]
	var evidence struct {
		CandidateID  string `json:"candidate_id"`
		Previous     string `json:"previous_sha256"`
		Verdict      string `json:"verdict"`
		Prerequisite struct {
			Predicate string `json:"predicate"`
			Ref       string `json:"ref"`
		} `json:"prerequisite"`
	}
	if strictjson.Validate(record) != nil || json.Unmarshal(record, &evidence) != nil ||
		evidence.CandidateID != prior.ID || evidence.Previous != current.Previous ||
		evidence.Verdict != "resolved" || evidence.Prerequisite != prior.Retry {
		return fmt.Errorf("retry evidence does not resolve the predecessor")
	}
	return nil
}

func canonicalRow(raw []byte) ([]byte, error) {
	var row map[string]any
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	if err := decoder.Decode(&row); err != nil {
		return nil, err
	}
	return contentbuild.Canonical(row)
}

func (a *authority) addRegistryRestrictions() {
	for id, row := range a.registry {
		ref := fmt.Sprintf("%s:%d", registryPath, row.Line)
		owner := row.Identity.OwnerID
		if owner == "" {
			owner = row.Payload.NodeID
		}
		// Legacy held lexical rows may omit an owner ID. Bind them through the
		// exact label owner, keeping the restriction scoped to that family.
		if owner == "" {
			owner = a.graph.Resolve(row.Label)
		}
		if row.State == "held_owner" && a.graph.Normalize(row.Label) == "ie" && owner == "" {
			owner = "n_v1_33_ie"
		}
		surfaces := row.Payload.Forms
		if len(surfaces) == 0 {
			surfaces = []string{row.Label}
		}
		code := ""
		switch {
		case row.Retry.Predicate == "owner_answer":
			code = "owner_hold_adr0210"
			if len(row.Holds) > 0 {
				ref = row.Holds[0].Ref
			}
		case row.State == "held_owner" && row.Type == "form":
			code = "owner_hold_registry"
		case strings.Contains(a.graph.Normalize(row.Identity.Sense), "diminutiv"):
			code = "pilot_diminutive"
		case row.State == "rejected" || strings.HasPrefix(row.State, "retracted("):
			code = "registry_rejected"
		case row.State == "held_recorded":
			code = "registry_recorded_hold"
		case strings.HasPrefix(row.State, "parked("):
			code = "registry_prerequisite"
		}
		if code != "" && (row.Type == "form" || row.Type == "synonym") {
			if len(row.Payload.Forms) == 0 && owner != "" && code == "registry_recorded_hold" {
				a.families[owner] = append(a.families[owner], restriction{code, owner, ref})
			}
			for _, surface := range surfaces {
				a.add(a.denials, surface, restriction{code, owner, ref})
			}
		}
		if row.Type == "form" || row.Type == "synonym" || row.Type == "concept" || row.Type == "name" {
			for _, surface := range row.Payload.HeldForms {
				a.add(a.denials, surface, restriction{"registry_recorded_hold", owner, ref})
			}
			if row.State != "held_owner" && row.State != "held_recorded" &&
				row.State != "rejected" && !strings.HasPrefix(row.State, "parked(") &&
				!strings.HasPrefix(row.State, "retracted(") {
				for _, surface := range surfaces {
					key := a.graph.Normalize(surface)
					a.stock[key] = append(a.stock[key], id)
				}
			}
		}
	}
}

func (a *authority) add(index map[string][]restriction, surface string, entry restriction) {
	key := a.graph.Normalize(surface)
	if key != "" && !slices.Contains(index[key], entry) {
		index[key] = append(index[key], entry)
	}
}

func (a *authority) addInventory() error {
	c := a.graph.Content
	for _, node := range c.Nodes {
		entry := restriction{"inventory_collision", node.ID, fixturePath}
		a.add(a.inventory, node.LabelRO, entry)
		for _, alias := range node.Aliases {
			a.add(a.inventory, alias, entry)
		}
	}
	for _, raw := range c.PackItems {
		if raw.Game != "contexto" {
			continue
		}
		target, ok := raw.Payload["target"].(string)
		if !ok || !a.graph.Exists(target) {
			return fmt.Errorf("invalid Cald target in sealed bundle")
		}
		if !raw.PilotEligible {
			continue
		}
		incoming := 0
		for _, predecessor := range a.graph.PredecessorIDs(target) {
			if predecessor != target {
				incoming++
			}
		}
		if incoming < 5 {
			return fmt.Errorf("Cald inbound floor below 5 for eligible board %s", raw.ID)
		}
	}
	var projection []struct {
		Key     string `json:"key"`
		Label   string `json:"label"`
		Surface string `json:"surface"`
	}
	raw, err := json.Marshal(c.ContextoData["projection_terms"])
	if err != nil || json.Unmarshal(raw, &projection) != nil || projection == nil {
		return fmt.Errorf("invalid Cald projection inventory")
	}
	for _, term := range projection {
		if term.Key == "" {
			return fmt.Errorf("invalid Cald projection key")
		}
		for _, surface := range []string{term.Key, term.Label, term.Surface} {
			a.add(a.inventory, surface, restriction{"cald_projection_collision", "", bundlePath + "#contexto_data.projection_terms"})
		}
	}
	var concepts []struct {
		ID       string `json:"id"`
		Label    string `json:"label"`
		Snapshot struct {
			ID      string   `json:"id"`
			Label   string   `json:"label"`
			LabelRO string   `json:"label_ro"`
			Aliases []string `json:"aliases"`
		} `json:"snapshot"`
	}
	raw, err = json.Marshal(c.DiscoveryWorld["concepts"])
	if err != nil || json.Unmarshal(raw, &concepts) != nil || concepts == nil {
		return fmt.Errorf("invalid Alchimie discovery inventory")
	}
	for _, concept := range concepts {
		entry := restriction{"alchimie_world_collision", concept.ID, bundlePath + "#discovery_world.concepts"}
		if a.graph.Exists(concept.Snapshot.ID) {
			entry.owner = concept.Snapshot.ID
		}
		for _, surface := range append([]string{concept.Label, concept.Snapshot.Label, concept.Snapshot.LabelRO}, concept.Snapshot.Aliases...) {
			a.add(a.inventory, surface, entry)
		}
	}
	return nil
}

func (a *authority) addExclusions(raw []byte) error {
	var index struct {
		Schema       string `json:"schema"`
		Declarations []struct {
			Literal string `json:"literal"`
			Source  struct {
				Path string `json:"path"`
				Line int    `json:"line"`
			} `json:"source"`
		} `json:"lexical_declarations"`
	}
	if err := strictjson.Validate(raw); err != nil {
		return err
	}
	if json.Unmarshal(raw, &index) != nil || index.Schema != "cat-content-exclusions-1" ||
		len(index.Declarations) == 0 {
		return fmt.Errorf("incomplete lexical exclusions")
	}
	for _, entry := range index.Declarations {
		if entry.Literal == "" || !fs.ValidPath(entry.Source.Path) || entry.Source.Line < 1 {
			return fmt.Errorf("invalid lexical exclusion")
		}
		a.add(a.denials, entry.Literal, restriction{"recorded_exclusion", "", fmt.Sprintf("%s:%d", entry.Source.Path, entry.Source.Line)})
	}
	return nil
}

func (a *authority) addHistory(root *os.Root) (string, error) {
	var bindings []string
	err := fs.WalkDir(root.FS(), "docs/reviews", func(name string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.IsDir() || !strings.HasSuffix(name, "graph-candidates.json") {
			return nil
		}
		data, err := readRegular(root, name, maxAuthority)
		if err != nil {
			return err
		}
		if err := strictjson.Validate(data); err != nil {
			return fmt.Errorf("%s: %w", name, err)
		}
		var history struct {
			Exclusions []string `json:"exclusions"`
			Deferred   []string `json:"deferred"`
			Separate   []string `json:"preserve_separate_surfaces"`
		}
		if err := json.Unmarshal(data, &history); err != nil || bytes.TrimSpace(data)[0] != '{' {
			return fmt.Errorf("invalid lexical history %s", name)
		}
		for field, surfaces := range map[string][]string{
			"exclusions": history.Exclusions, "deferred": history.Deferred,
			"preserve_separate_surfaces": history.Separate,
		} {
			for _, surface := range surfaces {
				a.add(a.denials, surface, restriction{"historical_exclusion", "", name + "#" + field})
			}
		}
		bindings = append(bindings, name+" "+contentbuild.SHA256(data))
		return nil
	})
	if err != nil {
		return "", err
	}
	if len(bindings) == 0 {
		return "", fmt.Errorf("missing graph-candidate history")
	}
	return contentbuild.SHA256([]byte(strings.Join(bindings, "\n"))), nil
}

// The structured history omits some intentional negatives asserted by tests.
// Select confirmed product-policy assertions here. Historical fixture states,
// temporary mocks and examples that may resolve exactly today are unsuitable.
var testExclusions = []struct {
	Path      string
	Assertion string
	Surface   string
}{
	{"tests/test_v28_basic_words.py", `assert svc.resolve("luni") is None`, "luni"},
	{"tests/test_v28_basic_words.py", `assert svc.resolve("vapori") is None`, "vapori"},
	{"tests/test_v72_romanian_dishes_and_pastries_morphology.py", `assert svc.resolve("strugur") is None`, "strugur"},
	// The V88 author graph candidates also preserve this distinction in sense_limits.
	{"tests/test_v88_everyday_graph.py", `assert svc.resolve("smântână dulce") is None`, "smântână dulce"},
	{"tests/test_v90_praf_migration.py", `assert get_service().resolve("prafuri") is None`, "prafuri"},
	{"tests/test_v90_praf_migration.py", `assert svc.resolve("prafzz") is None and svc.resolve_fuzzy("prafzz") is None`, "prafzz"},
	{"tests/test_wordgames_contexto.py", `assert svc.resolve_fuzzy("portocal") is None`, "portocal"},
	{"tests/test_wordgames_contexto.py", `assert svc.resolve_fuzzy("strug") is None`, "strug"},
}

func (a *authority) addTestExclusions(root *os.Root) (string, error) {
	files := map[string][]byte{}
	var bindings []string
	for _, denial := range testExclusions {
		raw, found := files[denial.Path]
		if !found {
			var err error
			raw, err = readRegular(root, denial.Path, 1<<20)
			if err != nil {
				return "", err
			}
			files[denial.Path] = raw
		}
		line := 0
		for index, content := range bytes.Split(raw, []byte("\n")) {
			if string(bytes.TrimSpace(content)) == denial.Assertion {
				if line != 0 {
					return "", fmt.Errorf("ambiguous test exclusion in %s", denial.Path)
				}
				line = index + 1
			}
		}
		if line == 0 {
			return "", fmt.Errorf("missing bound test exclusion in %s", denial.Path)
		}
		ref := fmt.Sprintf("%s:%d", denial.Path, line)
		a.add(a.denials, denial.Surface, restriction{"recorded_test_exclusion", "", ref})
		bindings = append(bindings, ref+" "+contentbuild.SHA256(raw))
	}
	return contentbuild.SHA256([]byte(strings.Join(bindings, "\n"))), nil
}
