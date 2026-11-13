package main

import (
	"cmp"
	"fmt"
	"maps"
	"slices"
	"strings"
	"unicode"
	"unicode/utf8"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

const eligible = "screened"

type stagedForm struct {
	item int
	form int
}

func (a *authority) screen(proposals []proposal) ([]itemResult, []fuzzyChange) {
	items := slices.Clone(proposals)
	slices.SortFunc(items, func(a, b proposal) int { return cmp.Compare(a.ID, b.ID) })
	results := make([]itemResult, len(items))
	claims := map[string][]stagedForm{}
	positions := map[string]int{}
	for index, item := range items {
		positions[item.ID] = index
		result := itemResult{
			ID: item.ID, Kind: item.Kind, OwnerID: item.OwnerID, State: eligible,
			Reason: eligible, AcceptedForms: []string{}, Forms: make([]formResult, len(item.Forms)),
		}
		owner := a.graph.Node(item.OwnerID)
		for formIndex, surface := range item.Forms {
			form := a.checkForm(item, owner, surface)
			result.Forms[formIndex] = form
			if form.Reason == eligible {
				claims[form.Key] = append(claims[form.Key], stagedForm{index, formIndex})
			}
		}
		results[index] = result
	}
	for _, forms := range claims {
		if len(forms) < 2 {
			continue
		}
		for _, f := range forms {
			results[f.item].Forms[f.form].Reason = "batch_key_collision"
		}
	}
	for index, result := range results {
		familyReason := eligible
		for _, form := range result.Forms {
			if reasonOrder(form.Reason) < reasonOrder(familyReason) {
				familyReason = form.Reason
			}
		}
		results[index].setReason(familyReason)
	}
	var changes = []fuzzyChange{}
	fuzzyBefore := map[string]string{}
	for {
		a.resolveDependencies(items, results, positions)
		current, affected := a.compareFuzzy(results, fuzzyBefore)
		changes = append(changes, current...)
		if len(affected) == 0 {
			break
		}
		for _, index := range affected {
			results[index].setReason("fuzzy_neighbor_owner_change")
		}
	}
	slices.SortFunc(changes, func(a, b fuzzyChange) int {
		return cmp.Or(cmp.Compare(a.Probe, b.Probe), cmp.Compare(a.BeforeOwner, b.BeforeOwner),
			cmp.Compare(a.AfterOwner, b.AfterOwner), slices.Compare(a.ItemIDs, b.ItemIDs))
	})
	changes = slices.CompactFunc(changes, func(a, b fuzzyChange) bool {
		return a.Probe == b.Probe && a.BeforeOwner == b.BeforeOwner &&
			a.AfterOwner == b.AfterOwner && slices.Equal(a.ItemIDs, b.ItemIDs)
	})
	for index := range results {
		item := &results[index]
		slices.SortFunc(item.Forms, func(a, b formResult) int {
			return cmp.Or(cmp.Compare(a.Key, b.Key), cmp.Compare(a.Surface, b.Surface))
		})
		for formIndex := range item.Forms {
			form := &item.Forms[formIndex]
			if item.State == eligible {
				item.AcceptedForms = append(item.AcceptedForms, form.Surface)
				form.ProspectiveOwner = item.OwnerID
			} else if form.Reason == eligible {
				form.Reason = "family_blocked"
			}
		}
	}
	return results, changes
}

func (result *itemResult) setReason(reason string) {
	result.Reason = reason
	switch {
	case reason == eligible:
		result.State = eligible
	case strings.HasPrefix(reason, "owner_hold_"):
		result.State = "held_owner"
	case reason == "already_served":
		result.State = "already_served"
	case reason == "registry_duplicate":
		result.State = "duplicate"
	case reason == "registry_prerequisite" || reason == "dependency_unavailable" || reason == "co_landing_incomplete":
		result.State = "parked"
	case reason == "registry_recorded_hold" || reason == "recorded_exclusion" || reason == "historical_exclusion" || reason == "recorded_test_exclusion":
		result.State = "held_recorded"
	default:
		result.State = "rejected"
	}
}

// Stronger holds take precedence when a family has more than one reason.
func reasonOrder(code string) int {
	order := []string{
		"owner_hold_bare_sucitoare", "owner_hold_ie", "owner_hold_named_family", "owner_hold_adr0210", "owner_hold_registry",
		"invalid_surface", "pilot_diminutive", "registry_identity_mismatch", "unknown_owner",
		"native_reviewed_unresolved", "native_fuzzy_deny", "resolver_exact_collision", "already_served",
		"cald_projection_collision", "alchimie_world_collision", "inventory_collision",
		"recorded_test_exclusion", "recorded_exclusion", "historical_exclusion", "registry_rejected", "registry_recorded_hold",
		"registry_prerequisite", "registry_duplicate", "batch_key_collision", "fuzzy_owner_collision",
		eligible,
	}
	rank := slices.Index(order, code)
	if rank < 0 {
		panic(fmt.Sprintf("unexpected per-form reason %q", code))
	}
	return rank
}

func (a *authority) checkForm(item proposal, owner *content.Node, surface string) formResult {
	key := a.graph.Normalize(surface)
	form := formResult{Surface: surface, Key: key, Reason: eligible, Refs: []string{}}
	form.ExactOwner = a.graph.Resolve(surface)
	form.FuzzyOwner = form.ExactOwner
	form.ProspectiveOwner = form.ExactOwner
	add := func(code, ref string) {
		if reasonOrder(code) < reasonOrder(form.Reason) {
			form.Reason = code
		}
		if ref != "" {
			form.Refs = append(form.Refs, ref)
		}
	}
	// Explicit permanent rulings are evaluated using the runtime's folded key.
	if key == "sucitoare" {
		add("owner_hold_bare_sucitoare", "docs/CONTENT_LOOP.md#lanes")
	}
	label := ""
	if owner != nil {
		label = a.graph.Normalize(owner.LabelRO)
	}
	if (item.OwnerID == "n_v1_33_ie" || label == "ie") && (key == "ii" || key == "iei") {
		add("owner_hold_ie", "docs/CONTENT_LOOP.md#lanes")
	}
	if item.OwnerID == "n_v2art_manastire" || item.OwnerID == "n_v84_food_sucitor" ||
		label == "manastire" || label == "sucitor" {
		add("owner_hold_named_family", "docs/CONTENT_LOOP.md#lanes")
	}
	if row, exists := a.registry[item.ID]; exists {
		ref := fmt.Sprintf("%s:%d", registryPath, row.Line)
		switch {
		case row.State == "held_owner":
			add("owner_hold_registry", ref)
		case row.Retry.Predicate == "owner_answer":
			add("owner_hold_adr0210", ref)
		case row.Type != item.Kind || row.Identity.OwnerID != item.OwnerID ||
			!sameFamily(row.Payload.Forms, item.Forms):
			add("registry_identity_mismatch", ref)
		case row.State == "held_recorded":
			add("registry_recorded_hold", ref)
		case row.State == "rejected" || row.State == "duplicate" || strings.HasPrefix(row.State, "retracted("):
			add("registry_rejected", ref)
		case strings.HasPrefix(row.State, "parked("):
			add("registry_prerequisite", ref)
		case row.State == "landed" || row.State == "already_served":
			add("already_served", ref)
		}
	}
	if !validSurface(surface) || key == "" || utf8.RuneCountInString(key) > 96 {
		add("invalid_surface", "")
	}
	if owner == nil {
		add("unknown_owner", fixturePath)
	}
	if item.Kind == "diminutive" {
		add("pilot_diminutive", "docs/CONTENT_LOOP.md#lanes")
	}
	if a.graph.ReviewedUnresolved(surface) {
		add("native_reviewed_unresolved", graphSource+"#ReviewedUnresolved")
	}
	// These native fuzzy exceptions would be bypassed by a newly exact key.
	if key == "intrigii" || key == "intrigilor" {
		add("native_fuzzy_deny", graphSource+"#ResolveFuzzy")
	}
	if form.ExactOwner != "" {
		if form.ExactOwner == item.OwnerID {
			add("already_served", bundlePath+"#normalized_index")
		} else {
			add("resolver_exact_collision", bundlePath+"#normalized_index")
		}
	}
	for _, entry := range a.families[item.OwnerID] {
		add(entry.code, entry.ref)
	}
	for _, entry := range a.denials[key] {
		if entry.owner == "" || entry.owner == item.OwnerID || entry.code == "owner_hold_adr0210" {
			add(entry.code, entry.ref)
		}
	}
	for _, entry := range a.inventory[key] {
		if entry.owner != item.OwnerID {
			add(entry.code, entry.ref)
		}
	}
	if form.Reason == eligible {
		for _, id := range a.stock[key] {
			if id != item.ID {
				row := a.registry[id]
				if row.State == "landed" || row.State == "already_served" ||
					row.CoLandingGroup == nil && len(row.Dependencies) == 0 &&
						registeredOwner(row) == item.OwnerID && !sameFamily(row.Payload.Forms, item.Forms) {
					continue
				}
				add("registry_duplicate", fmt.Sprintf("%s:%d", registryPath, row.Line))
			}
		}
		form.FuzzyOwner = a.graph.ResolveFuzzy(surface)
		if form.FuzzyOwner != "" && form.FuzzyOwner != item.OwnerID {
			add("fuzzy_owner_collision", graphSource+"#ResolveFuzzy")
		}
	}
	slices.Sort(form.Refs)
	form.Refs = slices.Compact(form.Refs)
	return form
}

func validSurface(surface string) bool {
	if utf8.RuneCountInString(surface) > 96 || strings.TrimSpace(surface) != surface || strings.Contains(surface, "  ") {
		return false
	}
	hasLetter := false
	for _, char := range surface {
		switch {
		case unicode.Is(unicode.Latin, char) && unicode.IsLetter(char):
			hasLetter = true
		case char >= '0' && char <= '9', char == ' ', char == '-', char == '\'', char == '’',
			strings.ContainsRune("\u0302\u0306\u0326\u0327", char):
		default:
			return false
		}
	}
	return hasLetter
}

func sameFamily(a, b []string) bool {
	left, right := slices.Clone(a), slices.Clone(b)
	slices.Sort(left)
	slices.Sort(right)
	return slices.Equal(left, right)
}

func registeredOwner(row registryRow) string {
	if row.Identity.OwnerID != "" {
		return row.Identity.OwnerID
	}
	return row.Payload.NodeID
}

func (a *authority) resolveDependencies(items []proposal, results []itemResult, positions map[string]int) {
	groups := map[string][]string{}
	for id, row := range a.registry {
		if row.CoLandingGroup != nil {
			group := *row.CoLandingGroup
			groups[group] = append(groups[group], id)
		}
	}
	for changed := true; changed; {
		changed = false
		for index, item := range items {
			if results[index].State != eligible {
				continue
			}
			record := a.registry[item.ID]
			if record.CoLandingGroup != nil {
				for _, id := range groups[*record.CoLandingGroup] {
					member, found := positions[id]
					if !found || results[member].State != eligible {
						results[index].setReason("co_landing_incomplete")
						break
					}
				}
				if results[index].State != eligible {
					changed = true
					continue
				}
			}
			group := append(slices.Clone(item.CoLanding), item.ID)
			slices.Sort(group)
			for _, id := range item.CoLanding {
				member, found := positions[id]
				if !found || results[member].State != eligible {
					results[index].setReason("co_landing_incomplete")
					break
				}
				otherGroup := append(slices.Clone(items[member].CoLanding), id)
				slices.Sort(otherGroup)
				if !slices.Equal(otherGroup, group) {
					results[index].setReason("co_landing_incomplete")
					break
				}
			}
			if results[index].State == eligible {
				requires := slices.Concat(item.Requires, record.Dependencies)
				for _, id := range requires {
					if a.registry[id].State == "landed" {
						continue
					}
					required, found := positions[id]
					if !found || results[required].State != eligible {
						results[index].setReason("dependency_unavailable")
						break
					}
				}
			}
			changed = changed || results[index].State != eligible
		}
	}
}

func (a *authority) compareFuzzy(results []itemResult, fuzzyBefore map[string]string) ([]fuzzyChange, []int) {
	keys := map[string]int{}
	probes := map[string]bool{"scriitoarele": true, "sucitoare": true, "ii": true, "iei": true}
	for index, result := range results {
		if result.State != eligible {
			continue
		}
		for _, form := range result.Forms {
			keys[form.Key] = index
			for _, probe := range neighbors(form.Key) {
				probes[probe] = true
			}
		}
	}
	if len(keys) == 0 {
		return nil, nil
	}
	for key := range a.denials {
		probes[key] = true
	}
	index := maps.Clone(a.graph.Content.NormalizedIndex)
	for key, item := range keys {
		index[key] = results[item].OwnerID
	}
	prospective := graph.New(&content.Content{
		NormalizedIndex: index, NormalizationMap: a.graph.Content.NormalizationMap,
		AccentNormalizationMap: a.graph.Content.AccentNormalizationMap,
	})
	changes := []fuzzyChange{}
	affected := map[int]bool{}
	for probe := range probes {
		if _, proposed := keys[probe]; proposed || a.graph.Resolve(probe) != "" {
			continue
		}
		probeLength := utf8.RuneCountInString(probe)
		involved := map[int]bool{}
		for key, item := range keys {
			keyLength := utf8.RuneCountInString(key)
			if 2*float64(min(keyLength, probeLength))/float64(keyLength+probeLength) >= .84 &&
				graph.SequenceRatio(key, probe) >= .84 {
				involved[item] = true
			}
		}
		if len(involved) == 0 {
			continue
		}
		before, cached := fuzzyBefore[probe]
		if !cached {
			before = a.graph.ResolveFuzzy(probe)
			fuzzyBefore[probe] = before
		}
		after := prospective.ResolveFuzzy(probe)
		if before == after {
			continue
		}
		ids := []string{}
		for item := range involved {
			ids = append(ids, results[item].ID)
			// New fuzzy recognition is expected near new forms. Preserve
			// existing owners and the deliberately unresolved keys.
			if before != "" || len(a.denials[probe]) != 0 || probe == "sucitoare" ||
				probe == "ii" && after == "n_v1_33_ie" || probe == "iei" && after == "n_v1_33_ie" {
				affected[item] = true
			}
		}
		slices.Sort(ids)
		changes = append(changes, fuzzyChange{probe, before, after, ids})
	}
	return changes, slices.Sorted(maps.Keys(affected))
}

// Probe a bounded, documented typo sample. S7 runs the all-target resolver
// diff; this screen only attributes exact before/after behavior on these keys.
func neighbors(key string) []string {
	runes := []rune(key)
	if len(runes) < 3 {
		return nil
	}
	positions := []int{0, len(runes) / 2, len(runes) - 1}
	out := make([]string, 0, 6)
	for _, i := range positions {
		if runes[i] == ' ' {
			continue
		}
		out = append(out, strings.TrimSpace(string(runes[:i])+string(runes[i+1:])))
		if i+1 < len(runes) && runes[i+1] != ' ' && runes[i] != runes[i+1] {
			typo := slices.Clone(runes)
			typo[i], typo[i+1] = typo[i+1], typo[i]
			out = append(out, string(typo))
		}
	}
	return out
}
