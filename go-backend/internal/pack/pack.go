package pack

import (
	"bytes"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/catalog"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
	"sort"
	"strconv"
)

type PickOptions struct {
	Category, Difficulty string
	ExcludeIDs           map[string]bool
	MinPool              int
	MinPoolSet           bool
	FilteredShelfWeights bool
}
type Pack struct {
	items  []*content.PackItem
	ranked bool
}

func FromItems(items []*content.PackItem, ranked bool) *Pack {
	p := &Pack{items: append([]*content.PackItem(nil), items...), ranked: ranked}
	sort.Slice(p.items, func(i, j int) bool { return p.items[i].ID < p.items[j].ID })
	return p
}
func New(c *content.Content) *Pack {
	return c.Shared("pack", func() any {
		p := &Pack{ranked: c.PackRanked}
		for i := range c.PackItems {
			p.items = append(p.items, &c.PackItems[i])
		}
		sort.Slice(p.items, func(i, j int) bool { return p.items[i].ID < p.items[j].ID })
		return p
	}).(*Pack)
}
func (p *Pack) Pool(game string, o PickOptions) []*content.PackItem {
	result := []*content.PackItem{}
	for _, v := range p.items {
		if v.Game == game && (o.Category == "" || v.Category == o.Category) && (o.Difficulty == "" || v.Difficulty == o.Difficulty) && !o.ExcludeIDs[v.ID] {
			result = append(result, v)
		}
	}
	return result
}
func eligible(pool []*content.PackItem) []*content.PackItem {
	out := []*content.PackItem{}
	for _, v := range pool {
		if v.PilotEligible {
			out = append(out, v)
		}
	}
	return out
}
func weights(pool []*content.PackItem) map[string]int {
	sorted := append([]*content.PackItem(nil), pool...)
	sort.Slice(sorted, func(i, j int) bool {
		if sorted[i].PilotScore != sorted[j].PilotScore {
			return sorted[i].PilotScore > sorted[j].PilotScore
		}
		return sorted[i].ID < sorted[j].ID
	})
	out := map[string]int{}
	for i, v := range sorted {
		q := 5 * i / len(sorted)
		if q > 4 {
			q = 4
		}
		out[v.ID] = 5 - q
	}
	return out
}
func weight(v *content.PackItem, effective map[string]int) int {
	if effective != nil {
		return effective[v.ID]
	}
	if v.SelectionWeight >= 1 && v.SelectionWeight <= 5 {
		return v.SelectionWeight
	}
	return 1
}
func (p *Pack) PickSeeded(game string, rng *pyrandom.Random, o PickOptions) *content.PackItem {
	var pool []*content.PackItem
	var effective map[string]int
	if p.ranked {
		base := o
		base.ExcludeIDs = nil
		pool = eligible(p.Pool(game, base))
		if len(pool) == 0 {
			return nil
		}
		if o.FilteredShelfWeights {
			effective = weights(pool)
		}
		if len(o.ExcludeIDs) > 0 {
			unplayed := []*content.PackItem{}
			for _, v := range pool {
				if !o.ExcludeIDs[v.ID] {
					unplayed = append(unplayed, v)
				}
			}
			if len(unplayed) > 0 {
				pool = unplayed
			}
		}
	} else {
		pool = p.Pool(game, o)
		if len(pool) == 0 {
			return nil
		}
		preferred := eligible(pool)
		if len(preferred) > 0 {
			pool = preferred
		}
	}
	total := 0
	for _, v := range pool {
		total += weight(v, effective)
	}
	ticket := rng.RandBelow(total)
	for _, v := range pool {
		ticket -= weight(v, effective)
		if ticket < 0 {
			return v
		}
	}
	panic("curated weighted selection exhausted")
}
func (p *Pack) PickDaily(game, daily string, o PickOptions) *content.PackItem {
	floor := o.MinPool
	if !o.MinPoolSet {
		floor = 8
		if o.Category != "" {
			floor = 4
		}
	}
	if floor < 1 {
		floor = 1
	}
	base := o
	base.ExcludeIDs = nil
	pool := p.Pool(game, base)
	preferred := eligible(pool)
	var effective map[string]int
	if p.ranked {
		pool = preferred
		if len(pool) < floor {
			return nil
		}
		if o.FilteredShelfWeights {
			effective = weights(pool)
		}
	} else {
		if len(pool) < floor {
			return nil
		}
		if len(preferred) >= floor {
			pool = preferred
		}
	}
	var chosen *content.PackItem
	var rank [8]byte
	for _, v := range pool {
		key := daily + ":" + game + ":" + o.Category + ":" + o.Difficulty + ":" + v.ID
		r := catalog.Blake2b8([]byte(key))
		for i := 1; i < weight(v, effective); i++ {
			h := catalog.Blake2b8([]byte(key + ":v37:" + strconv.Itoa(i)))
			if bytes.Compare(h[:], r[:]) < 0 {
				r = h
			}
		}
		if chosen == nil || bytes.Compare(r[:], rank[:]) < 0 || (r == rank && v.ID < chosen.ID) {
			chosen = v
			rank = r
		}
	}
	return chosen
}
func (p *Pack) Counts(category string) map[string]int {
	out := map[string]int{}
	for _, game := range []string{"alchimie", "contexto", "lant", "conexiuni"} {
		out[game] = len(p.Pool(game, PickOptions{Category: category}))
	}
	return out
}
func (p *Pack) SelectableCount(game, category, difficulty string) int {
	pool := p.Pool(game, PickOptions{Category: category, Difficulty: difficulty})
	if p.ranked {
		pool = eligible(pool)
	}
	return len(pool)
}
