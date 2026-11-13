package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"slices"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/alchimie"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
)

func (s services) packView(item content.PackItem, dryRun bool) (boardView, error) {
	payload := item.Payload
	parts := map[string]any{"category": item.Category, "category_label": s.data.CategoryLabels[item.Category], "difficulty": item.Difficulty}
	diagnostic := map[string]any{}
	target, _ := payload["target"].(string)
	if item.Game != "conexiuni" && !s.g.Exists(target) {
		return boardView{}, errors.New("unknown target")
	}
	switch item.Game {
	case "contexto":
		top, reachable := s.cald.BoardTopForReview(target)
		ids := make([]string, len(top))
		for i, guess := range top {
			ids[i] = guess.ID
		}
		parts["target"] = target
		parts["top_100_ids"] = ids
		extra := parts
		if dryRun {
			extra = diagnostic
		}
		extra["top_100_native_scores"] = top
		extra["target_display"] = s.targetDisplay(target)
		extra["reachable_count"] = reachable
	case "lant":
		start, _ := payload["start"].(string)
		par, ok := integer(payload["optimal"])
		if !ok || !s.g.Exists(start) || start == target {
			return boardView{}, errors.New("invalid Lanț endpoints or declared optimal")
		}
		length, steps := s.lant.BoardShortestRoutesForReview(start, target)
		labels := map[string]string{start: s.g.Label(start), target: s.g.Label(target)}
		for _, step := range steps {
			labels[step.From], labels[step.To] = s.g.Label(step.From), s.g.Label(step.To)
		}
		parts["start"], parts["target"] = start, target
		parts["declared_optimal"], parts["shortest_distance"] = par, length
		topology := make([][2]string, 0, len(steps))
		for _, step := range steps {
			topology = append(topology, [2]string{step.From, step.To})
		}
		parts["shortest_steps"] = topology
		extra := parts
		if dryRun {
			extra = diagnostic
		}
		extra["route_captions"], extra["route_labels"], extra["target_display"] = steps, labels, s.targetDisplay(target)
		menus, err := s.lant.BoardRouteMenusForReview(start, target, par)
		if err != nil {
			return boardView{}, err
		}
		extra["route_menus"] = menus
	case "alchimie":
		seeds, ok := stringsIn(payload["seeds"])
		par, parOK := integer(payload["target_depth"])
		if !ok || !parOK || len(seeds) < 5 || len(seeds) > 7 {
			return boardView{}, errors.New("invalid Alchimie seeds or declared depth")
		}
		if _, err := s.labels(seeds, false); err != nil {
			return boardView{}, err
		}
		parts["seeds"], parts["target"] = seeds, s.targetDisplay(target)
		parts["declared_depth"] = par
		if err := s.addRecipeView(parts, seeds, target, item.Category, par); err != nil {
			return boardView{}, err
		}
	case "conexiuni":
		order, ok := stringsIn(payload["order"])
		groups, hasGroups := payload["groups"].(map[string]any)
		groupLabels, hasLabels := payload["group_labels"].(map[string]any)
		if !ok || len(order) != 16 || !hasGroups || len(groups) != 4 || !hasLabels || len(groupLabels) != 4 {
			return boardView{}, errors.New("invalid Conexiuni board")
		}
		labels, err := s.labels(order, true)
		if err != nil || len(labels) != len(order) {
			return boardView{}, errors.New("invalid Conexiuni tile order")
		}
		grouped := map[string]bool{}
		patterns := map[string]string{}
		for name, group := range groups {
			ids, ok := stringsIn(group)
			label, hasLabel := groupLabels[name].(string)
			if !ok || len(ids) != 4 || !hasLabel || label == "" || s.data.LabelPatterns[label] == "" {
				return boardView{}, errors.New("invalid Conexiuni group or label pattern")
			}
			patterns[label] = s.data.LabelPatterns[label]
			for _, id := range ids {
				if labels[id] == "" || grouped[id] {
					return boardView{}, errors.New("Conexiuni groups are not a partition of the tiles")
				}
				grouped[id] = true
			}
		}
		parts["tiles"], parts["groups"], parts["group_labels"] = order, groups, groupLabels
		parts["tile_labels"], parts["group_patterns"] = labels, patterns
		parts["fairness"] = contentops.ConexiuniFairnessForReview(s.g, payload)
	}
	return encodeView(parts, diagnostic)
}

func (s services) quickView(board content.Board) (boardView, error) {
	// Decode has already validated exact payload members and the tile labels.
	var ids []string
	if board.Game == "intrusul" {
		ids, _ = stringsIn(board.Payload["members"])
		ids = append(ids, board.Payload["intruder"].(string))
	} else {
		for _, raw := range board.Payload["pairs"].([]any) {
			row := raw.(map[string]any)
			if _, ok := row["group_label"].(string); len(row) != 2 || !ok {
				return boardView{}, errors.New("invalid Perechi pair label")
			}
			members, _ := stringsIn(row["members"])
			ids = append(ids, members...)
		}
	}
	labels, err := s.labels(ids, true)
	if err != nil {
		return boardView{}, err
	}
	return encodeView(map[string]any{
		"category": board.Category, "category_label": s.data.CategoryLabels[board.Category],
		"difficulty": board.Difficulty, "payload": board.Payload, "tile_labels": labels,
	}, nil)
}

type recipeLink struct {
	Source string `json:"source"`
	Target string `json:"target"`
	Label  string `json:"label"`
}

func (s services) addRecipeView(parts map[string]any, seeds []string, target, category string, par int) error {
	projection := s.al.ProjectionForReview(seeds, target, category)
	parts["playable"] = projection != nil && projection.Par == par
	if projection == nil {
		return nil
	}
	steps := make([]alchimie.Step, 0, len(projection.Recipes))
	all := append(slices.Clone(seeds), target)
	links := map[string]recipeLink{}
	for pair, outputs := range projection.Recipes {
		steps = append(steps, alchimie.Step{Pair: pair, Results: outputs})
		all = append(all, pair[:]...)
		all = append(all, outputs...)
		for _, from := range pair {
			for _, to := range outputs {
				edge := s.g.Link(from, to)
				if edge != nil && edge.LabelRO != "" {
					links[from+"\x00"+to] = recipeLink{edge.Src, edge.Dst, edge.LabelRO}
				}
			}
		}
	}
	slices.SortFunc(steps, func(a, b alchimie.Step) int { return slices.Compare(a.Pair[:], b.Pair[:]) })
	labels, err := s.labels(all, false)
	if err != nil {
		return err
	}
	parts["projection_par"], parts["recipes"], parts["routes"] = projection.Par, steps, projection.Routes
	parts["recipe_labels"], parts["recipe_links"] = labels, links
	return nil
}

func (s services) targetDisplay(id string) map[string]string {
	return map[string]string{"id": id, "label": s.g.Label(id), "description": s.g.Description(id)}
}

func (s services) labels(ids []string, display bool) (map[string]string, error) {
	labels := make(map[string]string, len(ids))
	for _, id := range ids {
		if !s.g.Exists(id) {
			return nil, errors.New("board references an unknown concept")
		}
		label := s.g.Label(id)
		if display {
			label = s.g.DisplayLabel(id)
		}
		labels[id] = label
	}
	return labels, nil
}

func stringsIn(value any) ([]string, bool) {
	values, ok := value.([]any)
	if !ok {
		return nil, false
	}
	items := make([]string, 0, len(values))
	for _, raw := range values {
		item, ok := raw.(string)
		if !ok || item == "" {
			return nil, false
		}
		items = append(items, item)
	}
	return items, true
}

func integer(value any) (int, bool) {
	n, ok := value.(float64)
	if !ok || n < 1 || n > 6 || n != float64(int(n)) {
		return 0, false
	}
	return int(n), true
}

func encodeView(parts, diagnostic map[string]any) (boardView, error) {
	result := boardView{parts: map[string]string{}, diagnostic: map[string]string{}}
	for _, set := range []struct {
		input  map[string]any
		output map[string]string
	}{{parts, result.parts}, {diagnostic, result.diagnostic}} {
		for field, value := range set.input {
			raw, err := json.Marshal(value)
			if err != nil {
				return boardView{}, fmt.Errorf("encode %s: %w", field, err)
			}
			set.output[field] = contentbuild.SHA256(raw)
		}
	}
	return result, nil
}
