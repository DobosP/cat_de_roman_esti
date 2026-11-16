package main

import (
	"encoding/json"
	"fmt"
	"maps"
	"slices"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/alchimie"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contexto"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/lant"
)

var games = []string{"alchimie", "conexiuni", "contexto", "intrusul", "lant", "perechi"}

// Schema 2 counts the same board parts in every mode. Schema 1 S7 reports also
// counted Cald feedback and Lanț caption and menu fields as disturbances.
const viewDiffSchema = "cat-board-view-diff-2"

type boardKey struct {
	Game string `json:"game"`
	ID   string `json:"id"`
}

type boardView struct {
	parts      map[string]string
	selection  map[string]any
	diagnostic map[string]string
}

type inventory struct {
	boards           map[boardKey]boardView
	approved         map[string]int
	excluded         map[string]int
	storedQuick      map[string]int
	unreachableQuick map[string]int
	storedKeys       map[boardKey]bool
}

type gameCount struct {
	Baseline                  int `json:"baseline"`
	Candidate                 int `json:"candidate"`
	BaselineApproved          int `json:"baseline_approved_pack"`
	CandidateApproved         int `json:"candidate_approved_pack"`
	BaselineExcluded          int `json:"baseline_ineligible_pack"`
	CandidateExcluded         int `json:"candidate_ineligible_pack"`
	BaselineQuickStored       int `json:"baseline_stored_quick"`
	CandidateQuickStored      int `json:"candidate_stored_quick"`
	BaselineQuickUnreachable  int `json:"baseline_unreachable_quick"`
	CandidateQuickUnreachable int `json:"candidate_unreachable_quick"`
	Added                     int `json:"added"`
	Changed                   int `json:"changed"`
	Removed                   int `json:"removed"`
	Disturbed                 int `json:"disturbed"`
}

type change struct {
	boardKey
	Kind         string   `json:"kind"`
	BeforeSHA256 string   `json:"before_sha256,omitempty"`
	AfterSHA256  string   `json:"after_sha256,omitempty"`
	Fields       []string `json:"fields,omitempty"`
	BeforeStored bool     `json:"before_stored,omitempty"`
	AfterStored  bool     `json:"after_stored,omitempty"`
}

type selectionChange struct {
	boardKey
	Before map[string]any `json:"before"`
	After  map[string]any `json:"after"`
}

type dryRunResult struct {
	WordID     string `json:"word_id"`
	Limit      int    `json:"limit"`
	Hold       bool   `json:"hold"`
	KGSHA256   string `json:"prospective_kg_sha256"`
	PackSHA256 string `json:"prospective_pack_sha256"`
}

type report struct {
	Schema           string                `json:"schema"`
	BaselineSHA256   string                `json:"baseline_bundle_sha256"`
	CandidateSHA256  string                `json:"candidate_bundle_sha256,omitempty"`
	Games            map[string]*gameCount `json:"games"`
	DisturbedTotal   int                   `json:"disturbed_total"`
	Added            []change              `json:"added"`
	Disturbed        []change              `json:"disturbed"`
	SelectionChanges []selectionChange     `json:"selection_changes"`
	Diagnostics      []change              `json:"diagnostic_changes"`
	DryRun           *dryRunResult         `json:"one_word_dry_run,omitempty"`
}

func compare(baseline, candidate *content.Content) (*report, error) {
	before, err := buildInventory(baseline)
	if err != nil {
		return nil, fmt.Errorf("baseline view: %w", err)
	}
	after := before
	if baseline != candidate {
		after, err = buildInventory(candidate)
		if err != nil {
			return nil, fmt.Errorf("candidate view: %w", err)
		}
	}
	return compareInventories(before, after), nil
}

func compareInventories(before, after inventory) *report {
	out := &report{
		Schema: viewDiffSchema, Games: map[string]*gameCount{},
		Added: []change{}, Disturbed: []change{}, SelectionChanges: []selectionChange{}, Diagnostics: []change{},
	}
	for _, game := range games {
		out.Games[game] = &gameCount{
			BaselineApproved: before.approved[game], CandidateApproved: after.approved[game],
			BaselineExcluded: before.excluded[game], CandidateExcluded: after.excluded[game],
			BaselineQuickStored: before.storedQuick[game], CandidateQuickStored: after.storedQuick[game],
			BaselineQuickUnreachable: before.unreachableQuick[game], CandidateQuickUnreachable: after.unreachableQuick[game],
		}
	}
	union := make(map[boardKey]bool, len(before.boards)+len(after.boards))
	for key := range before.boards {
		union[key] = true
		out.Games[key.Game].Baseline++
	}
	for key := range after.boards {
		union[key] = true
		out.Games[key.Game].Candidate++
	}
	for _, key := range slices.SortedFunc(maps.Keys(union), compareKeys) {
		old, wasServed := before.boards[key]
		next, isServed := after.boards[key]
		count := out.Games[key.Game]
		switch {
		case !wasServed:
			count.Added++
			out.Added = append(out.Added, change{boardKey: key, Kind: "added", AfterSHA256: hashFields(next.parts), BeforeStored: before.storedKeys[key], AfterStored: true})
		case !isServed:
			count.Removed++
			out.Disturbed = append(out.Disturbed, change{boardKey: key, Kind: "removed", BeforeSHA256: hashFields(old.parts), BeforeStored: true, AfterStored: after.storedKeys[key]})
		default:
			if fields := changedFields(old.parts, next.parts); len(fields) > 0 {
				count.Changed++
				out.Disturbed = append(out.Disturbed, change{boardKey: key, Kind: "changed", BeforeSHA256: hashFields(old.parts), AfterSHA256: hashFields(next.parts), Fields: fields})
			}
			if hashFields(old.selection) != hashFields(next.selection) {
				out.SelectionChanges = append(out.SelectionChanges, selectionChange{key, old.selection, next.selection})
			}
			if fields := changedFields(old.diagnostic, next.diagnostic); len(fields) > 0 {
				out.Diagnostics = append(out.Diagnostics, change{boardKey: key, Kind: "changed", BeforeSHA256: hashFields(old.diagnostic), AfterSHA256: hashFields(next.diagnostic), Fields: fields})
			}
		}
		count.Disturbed = count.Changed + count.Removed
	}
	out.DisturbedTotal = len(out.Disturbed)
	return out
}

func compareKeys(a, b boardKey) int {
	if a.Game != b.Game {
		return strings.Compare(a.Game, b.Game)
	}
	return strings.Compare(a.ID, b.ID)
}

func changedFields(before, after map[string]string) []string {
	fields := map[string]bool{}
	for key, sha := range before {
		if sha != after[key] {
			fields[key] = true
		}
	}
	for key, sha := range after {
		if sha != before[key] {
			fields[key] = true
		}
	}
	return slices.Sorted(maps.Keys(fields))
}

func hashFields(value any) string {
	// These maps contain only encoded SHA-256 strings and typed selection metadata.
	raw, err := json.Marshal(value)
	if err != nil {
		panic(err)
	}
	return contentbuild.SHA256(raw)
}

type services struct {
	data *content.Content
	g    *graph.Service
	al   *alchimie.Service
	cald *contexto.Service
	lant *lant.Service
}

func buildInventory(c *content.Content) (inventory, error) {
	result := inventory{boards: map[boardKey]boardView{}, approved: map[string]int{}, excluded: map[string]int{},
		storedQuick: map[string]int{}, unreachableQuick: map[string]int{},
		storedKeys: make(map[boardKey]bool, len(c.PackItems)+len(c.Boards))}
	services := services{c, graph.New(c), alchimie.New(c), contexto.New(c), lant.New(c)}
	seen := result.storedKeys
	for _, item := range c.PackItems {
		key := boardKey{item.Game, item.ID}
		if item.ID == "" || seen[key] || !slices.Contains(contentbuild.Games, item.Game) || item.Status != "approved" ||
			(item.Category != "None" && c.CategoryLabels[item.Category] == "") || !slices.Contains([]string{"usor", "normal", "greu"}, item.Difficulty) ||
			item.PilotScore < 0 || item.PilotScore > 100 || item.SelectionWeight < 1 || item.SelectionWeight > 5 {
			return result, fmt.Errorf("invalid approved pack record %s/%s", key.Game, key.ID)
		}
		seen[key] = true
		result.approved[item.Game]++
		if !item.PilotEligible {
			result.excluded[item.Game]++
			continue
		}
		view, err := services.packView(item)
		if err != nil {
			return result, fmt.Errorf("%s/%s: %w", key.Game, key.ID, err)
		}
		view.selection = map[string]any{"pilot_score": item.PilotScore, "selection_weight": item.SelectionWeight}
		result.boards[key] = view
	}
	selectable := quickSelectable(c.Boards)
	for _, board := range c.Boards {
		key := boardKey{board.Game, board.CatalogID}
		if seen[key] {
			return result, fmt.Errorf("duplicate served key %s/%s", key.Game, key.ID)
		}
		seen[key] = true
		result.storedQuick[board.Game]++
		if !selectable[key] {
			result.unreachableQuick[board.Game]++
			continue
		}
		view, err := services.quickView(board)
		if err != nil {
			return result, fmt.Errorf("%s/%s: %w", key.Game, key.ID, err)
		}
		view.selection = map[string]any{
			"source_id": board.SourceID, "overall_score": board.OverallScore, "overall_rank": board.OverallRank,
			"starter_score": board.StarterScore, "starter_rank": board.StarterRank, "starter_safe": board.StarterSafe,
			"preferred": catalog.PreferredForReview(board.OverallScore), "overall_weight": catalog.ScoreBandWeight(board.OverallScore),
			"starter_weight": catalog.ScoreBandWeight(board.StarterScore),
		}
		result.boards[key] = view
	}
	return result, nil
}
