package main

import (
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/intrusul"
)

// Both Quick games carry the previous four source IDs. A category filter
// minimizes the preferred competitors. Each remaining preferred source can
// be picked once to exclude it before a below-shelf board becomes reachable.
func quickSelectable(boards []content.Board) map[boardKey]bool {
	type shelf struct {
		game, category string
		starter        bool
	}
	preferred := map[shelf]map[string]bool{}
	for _, board := range boards {
		if !catalog.PreferredForReview(board.OverallScore) {
			continue
		}
		for _, starter := range []bool{false, true} {
			if starter && !board.StarterSafe {
				continue
			}
			key := shelf{board.Game, board.Category, starter}
			if preferred[key] == nil {
				preferred[key] = map[string]bool{}
			}
			preferred[key][board.SourceID] = true
		}
	}
	available := map[boardKey]bool{}
	for _, board := range boards {
		key := boardKey{board.Game, board.CatalogID}
		if catalog.PreferredForReview(board.OverallScore) {
			available[key] = true
			continue
		}
		for _, starter := range []bool{false, true} {
			if starter && !board.StarterSafe {
				continue
			}
			sources := preferred[shelf{board.Game, board.Category, starter}]
			if len(sources) <= intrusul.SourceRingLimit && !sources[board.SourceID] {
				available[key] = true
				break
			}
		}
	}
	return available
}
