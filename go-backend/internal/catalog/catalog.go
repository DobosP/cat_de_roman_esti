// Package catalog preserves the ranked derived-board selection contract.
// Catalog IDs, source IDs, rankings and answers are private server inputs.
package catalog

import (
	"bytes"
	"sort"
	"strconv"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
)

type PickOptions struct {
	Category          string
	Difficulty        string
	ExcludeSources    map[string]bool
	Starter           bool
	BalanceCategories bool
}

// Catalog owns a catalog-ID-sorted copy of the selectable board inventory.
// Input must already have passed the Python content/export safety gates.
// Returned boards and their payloads must be treated as immutable.
type Catalog struct {
	boards []content.Board
}

func New(source *content.Content) *Catalog {
	c := &Catalog{boards: append([]content.Board(nil), source.Boards...)}
	sort.Slice(c.boards, func(i, j int) bool { return c.boards[i].CatalogID < c.boards[j].CatalogID })
	return c
}

func (c *Catalog) Pool(game string, options PickOptions) []*content.Board {
	pool := make([]*content.Board, 0)
	for i := range c.boards {
		board := &c.boards[i]
		if board.Game != game || options.Category != "" && board.Category != options.Category ||
			options.Difficulty != "" && board.Difficulty != options.Difficulty ||
			options.ExcludeSources[board.SourceID] || options.Starter && !board.StarterSafe {
			continue
		}
		pool = append(pool, board)
	}
	return pool
}

// ScoreBandWeight returns the same one-to-five integer tickets as Python.
func ScoreBandWeight(score int) int {
	switch {
	case score >= 85:
		return 5
	case score >= 75:
		return 4
	case score >= 65:
		return 3
	case score >= 55:
		return 2
	default:
		return 1
	}
}

func preferredShelf(pool []*content.Board) []*content.Board {
	preferred := make([]*content.Board, 0, len(pool))
	for _, board := range pool {
		if board.OverallScore >= 55 {
			preferred = append(preferred, board)
		}
	}
	if len(preferred) > 0 {
		return preferred
	}
	return pool
}

type boardGroup struct {
	key    string
	boards []*content.Board
}

func groups(pool []*content.Board, category bool) []boardGroup {
	grouped := make(map[string][]*content.Board)
	for _, board := range pool {
		key := board.SourceID
		if category {
			key = board.Category
		}
		grouped[key] = append(grouped[key], board)
	}
	keys := make([]string, 0, len(grouped))
	for key := range grouped {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	result := make([]boardGroup, 0, len(keys))
	for _, key := range keys {
		result = append(result, boardGroup{key: key, boards: grouped[key]})
	}
	return result
}

func boardScore(board *content.Board, starter bool) int {
	if starter {
		return board.StarterScore
	}
	return board.OverallScore
}

func sourceAverage(boards []*content.Board, starter bool) int {
	total := 0
	for _, board := range boards {
		total += boardScore(board, starter)
	}
	return (total + len(boards)/2) / len(boards)
}

func categoryAverage(boards []*content.Board, starter bool) int {
	sources := groups(boards, false)
	total := 0
	for _, source := range sources {
		total += sourceAverage(source.boards, starter)
	}
	return (total + len(sources)/2) / len(sources)
}

func weightedIndex(weights []int, rng *pyrandom.Random) int {
	total := 0
	for _, weight := range weights {
		total += weight
	}
	ticket := rng.RandBelow(total)
	for i, weight := range weights {
		ticket -= weight
		if ticket < 0 {
			return i
		}
	}
	panic("catalog: weighted selection exhausted its ticket range")
}

func groupWeights(grouped []boardGroup, starter, category bool) []int {
	weights := make([]int, len(grouped))
	for i, group := range grouped {
		score := sourceAverage(group.boards, starter)
		if category {
			score = categoryAverage(group.boards, starter)
		}
		weights[i] = ScoreBandWeight(score)
	}
	return weights
}

func candidateWeights(boards []*content.Board, starter bool) []int {
	weights := make([]int, len(boards))
	for i, board := range boards {
		weights[i] = ScoreBandWeight(boardScore(board, starter))
	}
	return weights
}

// PickSeeded balances source weights before selecting a variant, and optionally
// balances category weights by source averages. It never widens supplied filters.
func (c *Catalog) PickSeeded(game string, rng *pyrandom.Random, options PickOptions) *content.Board {
	pool := preferredShelf(c.Pool(game, options))
	if len(pool) == 0 {
		return nil
	}
	if options.BalanceCategories && options.Category == "" {
		categories := groups(pool, true)
		chosen := weightedIndex(groupWeights(categories, options.Starter, true), rng)
		pool = categories[chosen].boards
	}
	sources := groups(pool, false)
	chosen := weightedIndex(groupWeights(sources, options.Starter, false), rng)
	candidates := sources[chosen].boards
	return candidates[weightedIndex(candidateWeights(candidates, options.Starter), rng)]
}

// rendezvousIndex uses weighted BLAKE2b-64 tickets and a lexical key tiebreak.
// The unversioned first ticket preserves the original derived daily namespace.
func rendezvousIndex(keys []string, weights []int, namespace string) int {
	chosen := -1
	var chosenRank [8]byte
	for i, base := range keys {
		rank := blake2b8([]byte(base))
		for ticket := 1; ticket < weights[i]; ticket++ {
			versioned := base + ":v38:" + namespace + ":" + strconv.Itoa(ticket)
			digest := blake2b8([]byte(versioned))
			if bytes.Compare(digest[:], rank[:]) < 0 {
				rank = digest
			}
		}
		comparison := bytes.Compare(rank[:], chosenRank[:])
		if chosen < 0 || comparison < 0 || comparison == 0 && base < keys[chosen] {
			chosen = i
			chosenRank = rank
		}
	}
	return chosen
}

func (c *Catalog) PickDaily(game, daily, category string) *content.Board {
	return c.PickDailyWithOptions(game, daily, PickOptions{Category: category})
}

// PickDailyWithOptions takes only Category and Difficulty into account, matching
// Python's daily contract: starter and history cannot fork a shared daily.
func (c *Catalog) PickDailyWithOptions(game, daily string, options PickOptions) *content.Board {
	pool := preferredShelf(c.Pool(game, PickOptions{Category: options.Category, Difficulty: options.Difficulty}))
	sources := groups(pool, false)
	if len(sources) == 0 {
		return nil
	}
	base := daily + ":" + game + ":" + options.Category + ":" + options.Difficulty + ":"
	keys := make([]string, len(sources))
	for i, source := range sources {
		keys[i] = base + source.key
	}
	source := sources[rendezvousIndex(keys, groupWeights(sources, false, false), "source")]
	keys = make([]string, len(source.boards))
	for i, board := range source.boards {
		keys[i] = base + source.key + ":" + board.CatalogID
	}
	return source.boards[rendezvousIndex(keys, candidateWeights(source.boards, false), "candidate")]
}
