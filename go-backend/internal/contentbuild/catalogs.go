package contentbuild

import (
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"math"
	"net/url"
	"sort"
	"strings"
)

func bindings(meta map[string]any, want map[string]any) error {
	for k, v := range want {
		if meta[k] != v {
			return fmt.Errorf("source binding drift: %s", k)
		}
	}
	return nil
}
func sha(v any) bool {
	s := str(v)
	if len(s) != 64 {
		return false
	}
	for _, c := range s {
		if !(c >= '0' && c <= '9' || c >= 'a' && c <= 'f') {
			return false
		}
	}
	return true
}
func score(m map[string]any, k string) bool { n, ok := integer(m[k]); return ok && n >= 0 && n <= 100 }
func validateRankings(raw, pack map[string]any, digests map[string]any) (map[string]map[string]any, error) {
	fail := func(s string) (map[string]map[string]any, error) { return nil, fmt.Errorf("board rankings: %s", s) }
	meta := object(raw["meta"])
	if !exact(raw, "meta", "boards") || !exact(meta, "schema_version", "pack_sha256", "kg_sha256", "rubric_sha256", "counts") || number(meta["schema_version"]) != 1 {
		return fail("schema drift")
	}
	if e := bindings(meta, map[string]any{"pack_sha256": digests["games_pack.json"], "kg_sha256": digests["kg_sample.json"], "rubric_sha256": RubricSHA256}); e != nil {
		return fail(e.Error())
	}
	expected := map[string][2]string{}
	counts, byGame, eligibleBy := map[string]any{}, map[string]any{}, map[string]any{}
	approved := 0
	for _, game := range Games {
		byGame[game] = len(array(pack[game]))
		for _, v := range array(pack[game]) {
			m := object(v)
			expected[str(m["id"])] = [2]string{game, str(m["status"])}
			if m["status"] == "approved" {
				approved++
			}
		}
	}
	indexed := map[string]map[string]any{}
	for _, v := range array(raw["boards"]) {
		m := object(v)
		id := str(m["id"])
		if !exact(m, "id", "game", "status", "romanian_familiarity", "play_quality", "pilot_score", "rank", "pilot_eligible", "selection_weight") || id == "" || indexed[id] != nil {
			return fail("board schema/duplicate id")
		}
		if exp, ok := expected[id]; !ok || exp != [2]string{str(m["game"]), str(m["status"])} {
			return fail("identity/status drift")
		}
		for _, key := range []string{"romanian_familiarity", "play_quality", "pilot_score"} {
			if !score(m, key) {
				return fail("invalid score")
			}
		}
		if number(m["pilot_score"]) != math.Floor((6*number(m["romanian_familiarity"])+4*number(m["play_quality"])+5)/10) {
			return fail("score formula drift")
		}
		if n, ok := integer(m["rank"]); !ok || n < 1 {
			return fail("invalid rank")
		}
		eligible, ok := m["pilot_eligible"].(bool)
		if !ok {
			return fail("invalid eligibility")
		}
		w, ok := integer(m["selection_weight"])
		if !ok || w < 1 || w > 5 || (!eligible && w != 1) || eligible && m["status"] != "approved" {
			return fail("invalid selection weight/status")
		}
		indexed[id] = m
	}
	if len(indexed) != len(expected) {
		return fail("coverage drift")
	}
	for _, game := range Games {
		rows := []map[string]any{}
		for _, m := range indexed {
			if m["game"] == game {
				rows = append(rows, m)
			}
		}
		sort.Slice(rows, func(i, j int) bool {
			if number(rows[i]["pilot_score"]) != number(rows[j]["pilot_score"]) {
				return number(rows[i]["pilot_score"]) > number(rows[j]["pilot_score"])
			}
			return str(rows[i]["id"]) < str(rows[j]["id"])
		})
		eligible := []map[string]any{}
		for i, m := range rows {
			if number(m["rank"]) != float64(i+1) {
				return fail("rank order drift")
			}
			if m["pilot_eligible"] == true {
				eligible = append(eligible, m)
			}
		}
		for i, m := range eligible {
			w := 5 - 5*i/len(eligible)
			if w < 1 {
				w = 1
			}
			if number(m["selection_weight"]) != float64(w) {
				return fail("quintile weight drift")
			}
		}
		eligibleBy[game] = len(eligible)
	}
	totalEligible := 0
	for _, v := range eligibleBy {
		totalEligible += int(number(v))
	}
	counts["total"] = len(expected)
	counts["approved"] = approved
	counts["pilot_eligible"] = totalEligible
	counts["by_game"] = byGame
	counts["eligible_by_game"] = eligibleBy
	if !equal(meta["counts"], counts) {
		return fail("count drift")
	}
	return indexed, nil
}
func validateReserve(raw, pack map[string]any) (map[string]string, error) {
	fail := func(s string) (map[string]string, error) { return nil, fmt.Errorf("release reserve: %s", s) }
	meta := object(raw["meta"])
	if !exact(raw, "meta", "ids", "pack", "quick") || meta["kind"] != "v1-release-reserve-v1" || number(meta["count"]) != 20 || number(meta["quick_count"]) != 3 || len(array(raw["pack"])) != 20 || len(array(raw["quick"])) != 3 {
		return fail("schema/count drift")
	}
	if Normalize(str(meta["author"])) == Normalize(str(meta["reviewer"])) || Normalize(str(meta["reviewer"])) == "" {
		return fail("reviewer independence")
	}
	for _, key := range []string{"proposal_sha256", "alchimie_proposal_sha256", "quality_review_sha256"} {
		if !sha(meta[key]) {
			return fail("invalid review binding")
		}
	}
	ids := []string{}
	seen := map[string]bool{}
	for _, v := range array(raw["pack"]) {
		m := object(v)
		id, game := str(m["id"]), str(m["game"])
		if !exact(m, "id", "game", "record_sha256") || id == "" || seen[id] || !contains(Games, game) || !sha(m["record_sha256"]) {
			return fail("invalid pack row")
		}
		seen[id] = true
		ids = append(ids, id)
		found := false
		for _, p := range array(pack[game]) {
			if object(p)["id"] == id {
				if valueDigest(p) != str(m["record_sha256"]) {
					return fail("reviewed record drift")
				}
				found = true
			}
		}
		if !found {
			return fail("missing reviewed pack record")
		}
	}
	sort.Strings(ids)
	if !equal(raw["ids"], ids) {
		return fail("ids inventory drift")
	}
	out := map[string]string{}
	for _, v := range array(raw["quick"]) {
		m := object(v)
		id := str(m["id"])
		if !exact(m, "id", "game", "source_id", "record_sha256", "definition_sha256") || id == "" || out[id] != "" || !sha(m["record_sha256"]) || !sha(m["definition_sha256"]) || !contains([]string{"intrusul", "perechi"}, str(m["game"])) || str(m["source_id"]) == "" {
			return fail("invalid quick reserve")
		}
		out[id] = str(m["definition_sha256"])
	}
	return out, nil
}
func candidateID(game, source string, p map[string]any, r map[string]any) string {
	p = copyObject(p)
	if game == "perechi" {
		pieces := []any{}
		for _, v := range array(p["pairs"]) {
			pieces = append(pieces, copyObject(object(v)))
		}
		p["pairs"] = pieces
	}
	for _, v := range array(r["label_corrections"]) {
		cor := object(v)
		if cor["item_id"] != source {
			continue
		}
		pieces := []map[string]any{p}
		if game == "perechi" {
			pieces = nil
			for _, x := range array(p["pairs"]) {
				pieces = append(pieces, object(x))
			}
		}
		for _, piece := range pieces {
			for _, x := range array(cor["groups"]) {
				cg := object(x)
				memberSet := stringsOf(cg["members"])
				match := true
				for _, n := range stringsOf(piece["members"]) {
					if !contains(memberSet, n) {
						match = false
					}
				}
				if match && piece["group_label"] == cg["after"] {
					piece["group_label"] = cg["before"]
				}
			}
		}
	}
	prefix := "vi"
	if game == "perechi" {
		prefix = "vp"
	}
	return prefix + "_" + valueDigest(map[string]any{"game": game, "source_id": source, "payload": p})[:20]
}
func validateDerived(raw, pack map[string]any, digests map[string]any, r map[string]any) error {
	fail := func(s string) error { return fmt.Errorf("derived catalog: %s", s) }
	meta := object(raw["meta"])
	if !exact(raw, "meta", "boards") || !exact(meta, "schema_version", "formula_version", "pack_sha256", "kg_sha256", "rubric_sha256", "v37_rankings_sha256", "counts") || number(meta["schema_version"]) != 1 || meta["formula_version"] != "v38-derived-1" {
		return fail("schema drift")
	}
	if e := bindings(meta, map[string]any{"pack_sha256": digests["games_pack.json"], "kg_sha256": digests["kg_sample.json"], "v37_rankings_sha256": digests["board_rankings_v37.json"], "rubric_sha256": RubricSHA256}); e != nil {
		return fail(e.Error())
	}
	sources := map[string]map[string]any{}
	for _, v := range array(pack["conexiuni"]) {
		m := object(v)
		sources[str(m["id"])] = m
	}
	for _, v := range array(r["label_corrections"]) {
		cor := object(v)
		m := sources[str(cor["item_id"])]
		restored := copyObject(m)
		labels := copyObject(object(m["group_labels"]))
		restored["group_labels"] = labels
		state := ""
		for _, v := range array(cor["groups"]) {
			cg := object(v)
			key := str(cg["key"])
			if !equal(object(m["groups"])[key], cg["members"]) {
				return fail("label correction member drift")
			}
			s := str(labels[key])
			if s != str(cg["before"]) && s != str(cg["after"]) {
				return fail("label correction drift")
			}
			which := "after"
			if s == str(cg["before"]) {
				which = "before"
			}
			if state != "" && state != which {
				return fail("partial label correction")
			}
			state = which
			labels[key] = cg["before"]
		}
		if m["status"] != "approved" || valueDigest(restored) != str(cor["before_sha256"]) {
			return fail("label correction identity drift")
		}
	}
	seen := map[string]bool{}
	byGame, sourceCounts, starter := map[string]any{}, map[string]any{}, map[string]any{}
	for _, game := range []string{"intrusul", "perechi"} {
		byGame[game] = 0
		starter[game] = 0
	}
	families := map[string]bool{}
	familyCounts := map[string]int{}
	for _, v := range array(raw["boards"]) {
		m := object(v)
		id, game, source := str(m["id"]), str(m["game"]), str(m["source_id"])
		s := sources[source]
		if !exact(m, "id", "game", "source_id", "category", "difficulty", "romanian_familiarity", "play_quality", "standard_score", "starter_score", "starter_eligible", "standard_rank", "starter_rank", "payload") || id == "" || seen[id] || !contains([]string{"intrusul", "perechi"}, game) || s == nil || s["status"] != "approved" {
			return fail("identity/schema drift")
		}
		seen[id] = true
		byGame[game] = int(number(byGame[game])) + 1
		if m["category"] != s["category"] || m["difficulty"] != s["difficulty"] {
			return fail("source metadata drift")
		}
		for _, key := range []string{"romanian_familiarity", "play_quality", "standard_score", "starter_score"} {
			if !score(m, key) {
				return fail("invalid score")
			}
		}
		if number(m["standard_score"]) != math.Floor((6*number(m["romanian_familiarity"])+4*number(m["play_quality"])+5)/10) || number(m["starter_score"]) != math.Floor((75*number(m["romanian_familiarity"])+25*number(m["play_quality"])+50)/100) {
			return fail("score formula drift")
		}
		eligible, ok := m["starter_eligible"].(bool)
		if !ok {
			return fail("invalid starter eligibility")
		}
		if eligible {
			starter[game] = int(number(starter[game])) + 1
		} else if m["starter_rank"] != nil {
			return fail("ineligible starter rank")
		}
		p := object(m["payload"])
		if e := derivedPayload(game, p, s); e != nil {
			return fail(e.Error())
		}
		if id != candidateID(game, source, p, r) {
			return fail("candidate id drift")
		}
		families[game+"\x00"+source] = true
		familyCounts[game+"\x00"+source]++
		if familyCounts[game+"\x00"+source] > 3 {
			return fail("source family cap")
		}
	}
	for _, game := range []string{"intrusul", "perechi"} {
		n := 0
		for family := range families {
			if strings.HasPrefix(family, game+"\x00") {
				n++
			}
		}
		sourceCounts[game] = n
	}
	if !equal(meta["counts"], map[string]any{"total": len(seen), "by_game": byGame, "sources_by_game": sourceCounts, "starter_by_game": starter}) {
		return fail("counts drift")
	}
	return competitionRanks(array(raw["boards"]))
}
func derivedPayload(game string, p, s map[string]any) error {
	groups, labels := object(s["groups"]), object(s["group_labels"])
	pieces := []any{p}
	if game == "intrusul" {
		if !exact(p, "members", "intruder", "group_label") || len(array(p["members"])) != 3 {
			return fmt.Errorf("intrusul payload shape")
		}
	} else {
		if !exact(p, "pairs") || len(array(p["pairs"])) != 4 {
			return fmt.Errorf("perechi payload shape")
		}
		pieces = array(p["pairs"])
	}
	usedGroups, usedNodes := map[string]bool{}, map[string]bool{}
	for _, v := range pieces {
		piece := object(v)
		members := stringsOf(piece["members"])
		if game == "perechi" && (!exact(piece, "members", "group_label") || len(members) != 2) {
			return fmt.Errorf("pair shape")
		}
		matching := ""
		for key, values := range groups {
			all := true
			for _, n := range members {
				if !contains(stringsOf(values), n) {
					all = false
				}
			}
			if all {
				if matching != "" {
					return fmt.Errorf("ambiguous source group")
				}
				matching = key
			}
		}
		if matching == "" || usedGroups[matching] || piece["group_label"] != labels[matching] {
			return fmt.Errorf("source group/label drift")
		}
		usedGroups[matching] = true
		for _, n := range members {
			if usedNodes[n] {
				return fmt.Errorf("reused node")
			}
			usedNodes[n] = true
		}
		if game == "intrusul" {
			intruder := str(p["intruder"])
			if intruder == "" || usedNodes[intruder] || contains(stringsOf(groups[matching]), intruder) {
				return fmt.Errorf("invalid intruder")
			}
			known := false
			for _, values := range groups {
				known = known || contains(stringsOf(values), intruder)
			}
			if !known {
				return fmt.Errorf("intruder outside source")
			}
		}
	}
	return nil
}
func competitionRanks(rows []any) error {
	for _, game := range []string{"intrusul", "perechi"} {
		for _, field := range []string{"standard_score", "starter_score"} {
			ordered := []map[string]any{}
			for _, v := range rows {
				m := object(v)
				if m["game"] == game && (field == "standard_score" || m["starter_eligible"] == true) {
					ordered = append(ordered, m)
				}
			}
			sort.Slice(ordered, func(i, j int) bool {
				if number(ordered[i][field]) != number(ordered[j][field]) {
					return number(ordered[i][field]) > number(ordered[j][field])
				}
				return str(ordered[i]["id"]) < str(ordered[j]["id"])
			})
			rank, previous := 0, -1
			key := "standard_rank"
			if field == "starter_score" {
				key = "starter_rank"
			}
			for i, m := range ordered {
				sc := int(number(m[field]))
				if sc != previous {
					rank = i + 1
					previous = sc
				}
				if n, ok := integer(m[key]); !ok || n != rank {
					return fmt.Errorf("competition rank drift")
				}
			}
		}
	}
	return nil
}
func validReference(v any) bool {
	s := str(v)
	u, e := url.Parse(s)
	if e != nil || u.Hostname() == "" || u.User != nil || u.Scheme != "http" && u.Scheme != "https" || strings.IndexFunc(s, pySpace) >= 0 {
		return false
	}
	if p := u.Port(); p != "" {
		for _, c := range p {
			if c < '0' || c > '9' {
				return false
			}
		}
		if p == "0" {
			return false
		}
	}
	return true
}
func independentReviews(v any) bool {
	rows := array(v)
	if len(rows) != 2 {
		return false
	}
	a, b := object(rows[0]), object(rows[1])
	return Normalize(str(a["reviewer"])) != "" && Normalize(str(b["reviewer"])) != "" && Normalize(str(a["reviewer"])) != Normalize(str(b["reviewer"])) && ((a["role"] == "factual" && b["role"] == "quality") || (a["role"] == "quality" && b["role"] == "factual")) && sha(a["sha256"]) && sha(b["sha256"])
}
func validateQuick(raw, derived map[string]any, g *graph.Service, digests map[string]any) error {
	fail := func(s string) error { return fmt.Errorf("quick catalog: %s", s) }
	if raw["kind"] != "quick-content-catalog-v1" || len(array(raw["authored"])) == 0 || len(array(raw["authored"])) > 256 || !sha(raw["candidate_sha256"]) || !independentReviews(raw["reviews"]) {
		return fail("schema/reviews/bounds")
	}
	want := map[string]any{"kg_sha256": digests["kg_sample.json"], "pack_sha256": digests["games_pack.json"], "core_catalog_sha256": digests["derived_catalog_v38.json"], "rubric_sha256": RubricSHA256}
	if e := bindings(object(raw["bindings"]), want); e != nil {
		return fail(e.Error())
	}
	// Recompute the historical indented UTF-8 core-payload binding natively.
	if object(raw["bindings"])["core_payload_sha256"] != indentedDigest(derived["boards"]) {
		return fail("frozen core payload binding drift")
	}
	rated := []any{}
	seen := map[string]bool{}
	for _, v := range array(raw["authored"]) {
		m := object(v)
		id := str(m["id"])
		if !exact(m, "id", "game", "source_id", "category", "difficulty", "payload", "sources", "rationale") || id == "" || seen[id] || str(m["rationale"]) == "" {
			return fail("authored shape/identity")
		}
		seen[id] = true
		for _, u := range array(m["sources"]) {
			if !validReference(u) {
				return fail("source reference")
			}
		}
		if len(array(m["sources"])) < 1 || len(array(m["sources"])) > 16 {
			return fail("source reference bound")
		}
		rating, e := rateQuick(m, g)
		if e != nil {
			return fail(e.Error())
		}
		rated = append(rated, rating)
	}
	assignRanks(rated)
	if !equal(rated, raw["boards"]) {
		return fail("native rating or payload drift")
	}
	visible := map[string]bool{}
	trios := map[string]bool{}
	families := map[string]int{}
	for _, v := range array(derived["boards"]) {
		m := object(v)
		ids := quickVisible(m)
		sort.Strings(ids)
		visible[str(m["game"])+strings.Join(ids, "\x00")] = true
		if m["game"] == "intrusul" {
			members := stringsOf(object(m["payload"])["members"])
			sort.Strings(members)
			trios[strings.Join(members, "\x00")] = true
		}
	}
	nodes := map[string]any{}
	for _, v := range rated {
		m := object(v)
		ids := quickVisible(m)
		sort.Strings(ids)
		key := str(m["game"]) + strings.Join(ids, "\x00")
		if visible[key] {
			return fail("reused visible board")
		}
		visible[key] = true
		if m["game"] == "intrusul" {
			members := stringsOf(object(m["payload"])["members"])
			sort.Strings(members)
			key := strings.Join(members, "\x00")
			if trios[key] {
				return fail("reused inlier trio")
			}
			trios[key] = true
		}
		family := str(m["game"]) + "\x00" + str(m["source_id"])
		families[family]++
		if families[family] > 3 {
			return fail("source family cap")
		}
		for _, n := range ids {
			nodes[n] = nodeMap(*g.Node(n))
		}
	}
	if !equal(raw["nodes"], nodes) {
		return fail("concept provenance drift")
	}
	return nil
}
func quickVisible(m map[string]any) []string {
	p := object(m["payload"])
	if m["game"] == "intrusul" {
		return append(stringsOf(p["members"]), str(p["intruder"]))
	}
	ids := []string{}
	for _, v := range array(p["pairs"]) {
		ids = append(ids, stringsOf(object(v)["members"])...)
	}
	return ids
}
func graphStrengths(g *graph.Service) map[string]float64 {
	strengths := map[string]float64{}
	for _, e := range g.Content.Edges {
		if e.IsDistractor {
			continue
		}
		p := []string{e.Src, e.Dst}
		sort.Strings(p)
		key := strings.Join(p, "\x00")
		s := math.Min(1, math.Max(0, e.Strength))
		if strengths[key] < s {
			strengths[key] = s
		}
	}
	return strengths
}
func rateQuick(m map[string]any, g *graph.Service) (map[string]any, error) {
	fail := func(s string) (map[string]any, error) { return nil, fmt.Errorf("%s", s) }
	game := str(m["game"])
	p := object(m["payload"])
	r, _ := frozenRules()
	if !contains([]string{"intrusul", "perechi"}, game) || object(r["category_labels"])[str(m["category"])] == nil || !contains([]string{"usor", "normal", "greu"}, str(m["difficulty"])) || !strings.HasPrefix(str(m["source_id"]), "aq92_") {
		return fail("game/category/source")
	}
	prefix := "iq92_"
	if game == "perechi" {
		prefix = "pq92_"
	}
	if !strings.HasPrefix(str(m["id"]), prefix) {
		return fail("authored namespace")
	}
	if game == "intrusul" {
		if !exact(p, "members", "intruder", "group_label") || len(array(p["members"])) != 3 || str(p["intruder"]) == "" || strings.TrimSpace(str(p["group_label"])) == "" {
			return fail("intrusul shape")
		}
	} else {
		if !exact(p, "pairs") || len(array(p["pairs"])) != 4 {
			return fail("perechi shape")
		}
		for _, v := range array(p["pairs"]) {
			pair := object(v)
			if !exact(pair, "members", "group_label") || len(array(pair["members"])) != 2 || strings.TrimSpace(str(pair["group_label"])) == "" {
				return fail("perechi pair shape")
			}
		}
	}
	ids := quickVisible(m)
	seen := map[string]bool{}
	sal := []float64{}
	for _, id := range ids {
		n := g.Node(id)
		if n == nil || seen[id] {
			return fail("unknown/duplicate concept")
		}
		seen[id] = true
		sal = append(sal, n.Salience)
	}
	strengths := graphStrengths(g)
	strength := func(a, b string) float64 {
		p := []string{a, b}
		sort.Strings(p)
		return strengths[strings.Join(p, "\x00")]
	}
	mean := func(s []float64) float64 {
		sum := 0.
		for _, v := range s {
			sum += v
		}
		return sum / float64(len(s))
	}
	min := func(s []float64) float64 {
		v := 1.
		for _, x := range s {
			v = math.Min(v, x)
		}
		return v
	}
	max := func(s []float64) float64 {
		v := 0.
		for _, x := range s {
			v = math.Max(v, x)
		}
		return v
	}
	sc := func(v float64) int { return int(math.Floor(math.Min(100, math.Max(0, v)) + .5)) }
	familiarity, quality := 0, 0
	starter := false
	if game == "intrusul" {
		for _, id := range ids {
			if g.Node(id).NodeType != g.Node(ids[0]).NodeType {
				return fail("intrusul type shortcut")
			}
		}
		members := stringsOf(p["members"])
		inside, positive := []float64{}, []float64{}
		for i, a := range members {
			for _, b := range members[i+1:] {
				s := strength(a, b)
				inside = append(inside, s)
				if s >= .60 {
					positive = append(positive, s)
				}
			}
		}
		if len(positive) < 2 {
			return fail("weak trio")
		}
		for _, a := range members {
			pair := []string{a, str(p["intruder"])}
			sort.Strings(pair)
			if _, ok := strengths[strings.Join(pair, "\x00")]; ok {
				return fail("intruder has inlier link")
			}
		}
		familiarity = sc(100 * (.65*mean(sal) + .35*min(sal)))
		cohesion := 100 * (.60*mean(positive) + .40*min(positive))
		quality = sc(.55*cohesion + .25*(100*float64(len(positive))/3) + 20)
		starter = min(sal) >= .35 && min(inside) >= .70
	} else {
		pairs := map[string]bool{}
		intended, cross := []float64{}, []float64{}
		for _, v := range array(p["pairs"]) {
			members := stringsOf(object(v)["members"])
			pair := append([]string{}, members...)
			sort.Strings(pair)
			pairs[strings.Join(pair, "\x00")] = true
			intended = append(intended, strength(members[0], members[1]))
		}
		for i, a := range ids {
			for _, b := range ids[i+1:] {
				pair := []string{a, b}
				sort.Strings(pair)
				if !pairs[strings.Join(pair, "\x00")] {
					cross = append(cross, strength(a, b))
				}
			}
		}
		if min(intended) < .60 || max(cross) >= .60 {
			return fail("ambiguous/weak matching")
		}
		ordered := append([]float64{}, sal...)
		sort.Float64s(ordered)
		familiarity = sc(100 * (.50*mean(sal) + .30*ordered[(len(ordered)-1)/4] + .20*min(sal)))
		association := 100 * (.60*mean(intended) + .40*min(intended))
		separation := 100 * math.Max(0, 1-max(cross)/.60)
		quality = sc(.75*association + .25*separation)
		starter = min(sal) >= .35 && min(intended) >= .70 && max(cross) == 0
	}
	standard := sc(.60*float64(familiarity) + .40*float64(quality))
	if standard < 55 {
		return fail("below preferred shelf")
	}
	return map[string]any{"id": candidateID(game, str(m["source_id"]), p, r), "game": game, "source_id": m["source_id"], "category": m["category"], "difficulty": m["difficulty"], "payload": p, "romanian_familiarity": familiarity, "play_quality": quality, "standard_score": standard, "starter_score": sc(.75*float64(familiarity) + .25*float64(quality)), "starter_eligible": starter, "standard_rank": 0, "starter_rank": nil}, nil
}
func assignRanks(rows []any) {
	for _, game := range []string{"intrusul", "perechi"} {
		for _, field := range []string{"standard_score", "starter_score"} {
			ordered := []map[string]any{}
			for _, v := range rows {
				m := object(v)
				if m["game"] == game && (field == "standard_score" || m["starter_eligible"] == true) {
					ordered = append(ordered, m)
				}
			}
			sort.Slice(ordered, func(i, j int) bool {
				if number(ordered[i][field]) != number(ordered[j][field]) {
					return number(ordered[i][field]) > number(ordered[j][field])
				}
				return str(ordered[i]["id"]) < str(ordered[j]["id"])
			})
			rank, previous := 0, -1
			key := "standard_rank"
			if field == "starter_score" {
				key = "starter_rank"
			}
			for i, m := range ordered {
				score := int(number(m[field]))
				if score != previous {
					rank = i + 1
					previous = score
				}
				m[key] = rank
			}
		}
	}
}
