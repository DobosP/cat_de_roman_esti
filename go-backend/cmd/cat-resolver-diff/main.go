package main

import (
	"crypto/sha256"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"maps"
	"math/big"
	"os"
	"reflect"
	"slices"
	"strings"
	"unicode/utf8"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contexto"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
)

type target struct {
	ID         string `json:"board_id"`
	Owner      string `json:"owner_id"`
	Category   string `json:"category"`
	Difficulty string `json:"difficulty"`
	Selectable bool   `json:"selectable"`
}

type answer struct {
	Mode           string         `json:"mode"`
	Label          any            `json:"confirmation_label,omitempty"`
	Guess          map[string]any `json:"guess,omitempty"`
	Suggestions    any            `json:"suggestions,omitempty"`
	Attempts       int            `json:"attempts"`
	Won            bool           `json:"won"`
	ReachableCount int            `json:"reachable_count"`
}

type change struct {
	Target string `json:"board_id"`
	Probe  string `json:"probe"`
	Before answer `json:"before"`
	After  answer `json:"after"`
}

type bundle struct {
	game    *contexto.Service
	content *content.Content
	graph   *graph.Service
	targets map[string]target
	digest  string
}

const maxBundleBytes = 32 << 20

func load(path string) (*bundle, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Size() > maxBundleBytes {
		return nil, errors.New("bundle must be a bounded regular file")
	}
	raw, err := io.ReadAll(io.LimitReader(file, maxBundleBytes+1))
	if err != nil || len(raw) > maxBundleBytes {
		return nil, errors.New("cannot read bounded bundle")
	}
	data, err := content.Decode(raw)
	if err != nil {
		return nil, err
	}
	b := &bundle{content: data, targets: map[string]target{}, digest: fmt.Sprintf("%x", sha256.Sum256(raw))}
	for _, row := range data.PackItems {
		if row.Game != "contexto" {
			continue
		}
		owner, ok := row.Payload["target"].(string)
		if row.ID == "" || !ok || data.Labels[owner] == "" || row.Category == "" ||
			!slices.Contains([]string{"usor", "normal", "greu"}, row.Difficulty) ||
			b.targets[row.ID].ID != "" {
			return nil, fmt.Errorf("invalid Cald target %q", row.ID)
		}
		b.targets[row.ID] = target{row.ID, owner, row.Category, row.Difficulty, !data.PackRanked || row.PilotEligible}
	}
	if len(b.targets) == 0 || len(b.targets) > 1000 {
		return nil, errors.New("invalid Cald target inventory size")
	}
	return b, nil
}

func (b *bundle) prepare() {
	// The audit pins the target in the private, in-memory picker by marking
	// every pack board eligible and excluding every sibling. This reaches
	// approved stock outside the current ranked pool. Native graph, guesses
	// and scoring still run through the production service.
	b.content.PackRanked = true
	for i := range b.content.PackItems {
		if b.content.PackItems[i].Game == "contexto" {
			b.content.PackItems[i].PilotEligible = true
		}
	}
	b.graph = graph.New(b.content)
	b.game = contexto.New(b.content)
}

func inventoryChanges(before, after *content.Content) ([]string, error) {
	if !reflect.DeepEqual(before.Edges, after.Edges) ||
		!reflect.DeepEqual(before.PackItems, after.PackItems) ||
		!reflect.DeepEqual(before.ContextoData, after.ContextoData) ||
		!reflect.DeepEqual(before.Labels, after.Labels) ||
		!reflect.DeepEqual(before.CategoryLabels, after.CategoryLabels) ||
		!reflect.DeepEqual(before.NormalizationMap, after.NormalizationMap) ||
		!reflect.DeepEqual(before.AccentNormalizationMap, after.AccentNormalizationMap) ||
		!reflect.DeepEqual(before.CasefoldMap, after.CasefoldMap) ||
		len(before.Nodes) != len(after.Nodes) {
		return nil, errors.New("resolver audit requires a forms-only Cald change")
	}
	added := []string{}
	expectedIndex := maps.Clone(before.NormalizedIndex)
	resolver := graph.New(before)
	for i, old := range before.Nodes {
		next := after.Nodes[i]
		oldAliases, nextAliases := old.Aliases, next.Aliases
		old.Aliases, next.Aliases = nil, nil
		if !reflect.DeepEqual(old, next) {
			return nil, fmt.Errorf("node changed beyond aliases: %s", old.ID)
		}
		existing := map[string]bool{}
		for _, form := range oldAliases {
			existing[form] = true
		}
		for _, form := range nextAliases {
			if !existing[form] {
				key := resolver.Normalize(form)
				if key == "" || resolver.ReviewedUnresolved(form) || expectedIndex[key] != "" {
					return nil, fmt.Errorf("alias does not add a distinct resolver key for %s", old.ID)
				}
				expectedIndex[key] = old.ID
				added = append(added, form)
			}
		}
		for _, form := range oldAliases {
			if !slices.Contains(nextAliases, form) {
				return nil, fmt.Errorf("removed alias for %s", old.ID)
			}
		}
	}
	if !maps.Equal(expectedIndex, after.NormalizedIndex) {
		return nil, errors.New("candidate normalized index differs from exact alias additions")
	}
	return added, nil
}

func probesFor(before, after *bundle, extra []string) ([]string, error) {
	added, err := inventoryChanges(before.content, after.content)
	if err != nil {
		return nil, err
	}
	if !reflect.DeepEqual(before.targets, after.targets) {
		return nil, errors.New("Cald target inventory changed")
	}
	all := append(added, extra...)
	if len(all) > 1000 {
		return nil, errors.New("too many probe inputs")
	}
	for _, text := range all {
		if !utf8.ValidString(text) || strings.TrimSpace(text) == "" || len(text) > 256 {
			return nil, errors.New("invalid probe text")
		}
	}
	slices.Sort(all)
	return slices.Compact(all), nil
}

func newSession(b *bundle, t target, exclude map[string]bool) (string, error) {
	initial, failure := b.game.CreateWithExclusions(big.NewInt(0), t.Difficulty, nil, t.Category, exclude)
	if failure != nil {
		return "", fmt.Errorf("create game %s: %s", t.ID, failure.Detail)
	}
	id, ok := initial["game_id"].(string)
	if !ok || id == "" {
		return "", fmt.Errorf("no session for %s", t.ID)
	}
	selected, _, _, _, found := b.game.Progress(id)
	if !found || selected != t.ID {
		return "", fmt.Errorf("wanted %s, selected %s", t.ID, selected)
	}
	return id, nil
}

func readAnswer(b *bundle, t target, exclude map[string]bool, text string) (answer, error) {
	id, err := newSession(b, t, exclude)
	if err != nil {
		return answer{}, err
	}
	result, failure := b.game.Guess(id, text, "")
	if failure != nil {
		return answer{}, fmt.Errorf("first guess for %s: %s", t.ID, failure.Detail)
	}
	var a answer
	if result["needs_confirmation"] == true {
		a.Mode = "confirm"
		a.Label = result["resolved_label"]
		token, ok := result["resolved_token"].(string)
		if !ok || token == "" {
			return answer{}, errors.New("confirmation token missing")
		}
		result, failure = b.game.Guess(id, text, token)
		if failure != nil || result["ok"] != true {
			return answer{}, fmt.Errorf("confirmation failed for %s", t.ID)
		}
	} else if result["ok"] != true {
		a.Mode = "unknown"
		a.Suggestions = result["suggestions"]
	} else {
		a.Mode = "direct"
		if b.graph.Resolve(text) == "" {
			a.Mode = "projection-or-fuzzy"
			if result["won"] == true {
				a.Mode = "fuzzy-win"
			}
		}
	}
	a.Guess, _ = result["guess"].(map[string]any)
	a.Attempts, _ = result["attempts"].(int)
	a.Won, _ = result["won"].(bool)
	a.ReachableCount, _ = result["reachable_count"].(int)
	return a, nil
}

func compare(before, after *bundle, extra []string) ([]target, []string, []change, error) {
	probes, err := probesFor(before, after, extra)
	if err != nil {
		return nil, nil, nil, err
	}
	targets := make([]target, 0, len(before.targets))
	exclude := make(map[string]bool, len(before.targets))
	for id, t := range before.targets {
		targets = append(targets, t)
		exclude[id] = true
	}
	slices.SortFunc(targets, func(a, b target) int { return strings.Compare(a.ID, b.ID) })
	changes := []change{}
	if len(probes) == 0 {
		return targets, probes, changes, nil
	}
	before.prepare()
	after.prepare()
	for _, t := range targets {
		delete(exclude, t.ID)
		for _, probe := range probes {
			old, err := readAnswer(before, t, exclude, probe)
			if err != nil {
				return nil, nil, nil, err
			}
			next, err := readAnswer(after, t, exclude, probe)
			if err != nil {
				return nil, nil, nil, err
			}
			if !reflect.DeepEqual(old, next) {
				changes = append(changes, change{t.ID, probe, old, next})
			}
		}
		exclude[t.ID] = true
	}
	return targets, probes, changes, nil
}

func run(args []string, output io.Writer) error {
	fs := flag.NewFlagSet("cat-resolver-diff", flag.ContinueOnError)
	baseline := fs.String("before", "", "before content bundle")
	candidate := fs.String("after", "", "after content bundle")
	probesPath := fs.String("probes", "", "optional JSON array of reviewed fuzzy-neighbour probes")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *baseline == "" || *candidate == "" || fs.NArg() != 0 {
		return errors.New("--before and --after bundles are required")
	}
	probes := []string{}
	if *probesPath != "" {
		file, err := os.Open(*probesPath)
		if err != nil {
			return err
		}
		defer file.Close()
		info, err := file.Stat()
		if err != nil || !info.Mode().IsRegular() || info.Size() > 512*1024 {
			return errors.New("probes must be a bounded regular file")
		}
		raw, err := io.ReadAll(io.LimitReader(file, 512*1024+1))
		if err != nil || len(raw) > 512*1024 || !utf8.Valid(raw) || strictjson.Validate(raw) != nil ||
			json.Unmarshal(raw, &probes) != nil || probes == nil {
			return errors.New("probes must contain one valid UTF-8 JSON array of strings")
		}
	}
	before, err := load(*baseline)
	if err != nil {
		return fmt.Errorf("before bundle: %w", err)
	}
	after, err := load(*candidate)
	if err != nil {
		return fmt.Errorf("after bundle: %w", err)
	}
	targets, checked, changes, err := compare(before, after, probes)
	if err != nil {
		return err
	}
	return json.NewEncoder(output).Encode(map[string]any{
		"schema": "cat-resolver-diff-1", "before_bundle_sha256": before.digest,
		"after_bundle_sha256": after.digest, "targets": targets,
		"probes": checked, "checked_count": len(targets) * len(checked), "changes": changes,
	})
}

func main() {
	if err := run(os.Args[1:], os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
