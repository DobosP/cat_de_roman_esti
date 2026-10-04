package contentops

import (
	"bytes"
	"errors"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// The V38 source-ID freeze is independent of live approvals and ranking changes.
// It is the original 123-source snapshot; a wider cap requires a new decision.
var derivedSources = strings.Fields(`cx_arta_cultura_003 cx_arta_cultura_004 cx_arta_cultura_005 cx_arta_cultura_007 cx_arta_cultura_091 cx_arta_cultura_092 cx_arta_cultura_094 cx_arta_cultura_159 cx_arta_cultura_161 cx_arta_cultura_162 cx_arta_cultura_239 cx_arta_cultura_240 cx_arta_cultura_241 cx_film_tv_008 cx_film_tv_009 cx_film_tv_011 cx_film_tv_013 cx_film_tv_165 cx_film_tv_167 cx_film_tv_169 cx_film_tv_243 cx_film_tv_244 cx_gastronomie_171 cx_gastronomie_173 cx_geografie_028 cx_geografie_110 cx_geografie_177 cx_geografie_178 cx_geografie_179 cx_geografie_252 cx_istorie_001 cx_istorie_029 cx_istorie_030 cx_istorie_034 cx_istorie_115 cx_istorie_117 cx_istorie_118 cx_istorie_181 cx_istorie_182 cx_istorie_183 cx_istorie_255 cx_limba_037 cx_limba_038 cx_limba_122 cx_limba_187 cx_limba_192 cx_limba_260 cx_literatura_040 cx_literatura_041 cx_literatura_043 cx_literatura_044 cx_literatura_126 cx_literatura_127 cx_literatura_128 cx_literatura_131 cx_literatura_193 cx_literatura_194 cx_literatura_198 cx_literatura_264 cx_literatura_266 cx_meme_net_045 cx_meme_net_048 cx_meme_net_137 cx_meme_net_201 cx_meme_net_204 cx_meme_net_267 cx_muzica_053 cx_muzica_055 cx_muzica_138 cx_muzica_141 cx_muzica_143 cx_muzica_205 cx_muzica_208 cx_muzica_209 cx_muzica_273 cx_personalitati_059 cx_personalitati_063 cx_personalitati_064 cx_personalitati_144 cx_personalitati_145 cx_personalitati_210 cx_personalitati_213 cx_personalitati_214 cx_personalitati_275 cx_personalitati_276 cx_personalitati_277 cx_societate_065 cx_societate_067 cx_societate_068 cx_societate_151 cx_societate_152 cx_societate_155 cx_societate_216 cx_societate_217 cx_societate_220 cx_societate_278 cx_societate_280 cx_societate_290 cx_sport_072 cx_sport_073 cx_sport_074 cx_sport_075 cx_sport_076 cx_sport_077 cx_sport_156 cx_sport_157 cx_sport_160 cx_sport_161 cx_sport_222 cx_sport_225 cx_sport_226 cx_sport_282 cx_sport_284 cx_stiinta_081 cx_stiinta_083 cx_stiinta_162 cx_stiinta_165 cx_stiinta_167 cx_stiinta_227 cx_stiinta_285 cx_viata_de_roman_236 cx_viata_de_roman_238 cx_viata_de_roman_288`)

func mean(v []float64) float64 {
	sum := 0.0
	for _, x := range v {
		sum += x
	}
	if len(v) == 0 {
		return 0
	}
	return sum / float64(len(v))
}
func minFloat(v []float64) float64 {
	m := math.Inf(1)
	for _, x := range v {
		m = min(m, x)
	}
	if len(v) == 0 {
		return 0
	}
	return m
}
func lowerQuartile(v []float64) float64 {
	if len(v) == 0 {
		return 0
	}
	sorted := append([]float64{}, v...)
	sort.Float64s(sorted)
	return sorted[(len(sorted)-1)/4]
}
func score(v float64) int { return int(math.Floor(max(0.0, min(100.0, v)) + .5)) }

var correctionMembers = [][]string{{"n_gas_varza_a_la_cluj", "n_gas_covrigi_buzau", "n_gas_baclava_dobrogeana", "n_gas_bucovina_gastronomica"}, {"n_v2gas_branza", "n_gas_telemea", "n_gas_urda", "n_gas_branza_smantana"}}
var correctionBefore = []string{"Localitatea e deja în meniu", "Alb, sărat, din zona laptelui"}
var correctionAfter = []string{"Denumiri cu trimitere geografică", "Produse lactate"}

func correctionSource(pack Object) error {
	rows, _, e := indexPack(pack)
	if e != nil {
		return e
	}
	r := rows["cx_gastronomie_171"]
	if r == nil || str(r["status"]) != "approved" {
		return errors.New("reviewed label correction source missing/held")
	}
	restored := copyObject(r)
	labels := copyObject(obj(r["group_labels"]))
	restored["group_labels"] = labels
	state := ""
	for i, key := range []string{"g1", "g3"} {
		ids, e := stringsOf(obj(r["groups"])[key])
		if e != nil || !exactStrings(ids, correctionMembers[i]) {
			return errors.New("reviewed label correction members drift")
		}
		label := str(labels[key])
		next := ""
		if label == correctionBefore[i] {
			next = "before"
		} else if label == correctionAfter[i] {
			next = "after"
		} else {
			return errors.New("reviewed label correction label drift")
		}
		if state != "" && state != next {
			return errors.New("partial reviewed label correction")
		}
		state = next
		labels[key] = correctionBefore[i]
	}
	if digest(canonical(restored)) != "baf8750543974819f7d65cf6d3b7f09a00c2117c7448c71aeaefb7b107e9ab56" {
		return errors.New("reviewed label correction complete source drift")
	}
	return nil
}
func identityPayload(game, source string, payload Object) Object {
	if source != "cx_gastronomie_171" {
		return payload
	}
	m := copyObject(payload)
	pieces := []Object{}
	size := 3
	if game == "intrusul" {
		pieces = append(pieces, m)
	} else {
		size = 2
		pairs := []Object{}
		for _, v := range array(payload["pairs"]) {
			p := copyObject(obj(v))
			pairs = append(pairs, p)
			pieces = append(pieces, p)
		}
		m["pairs"] = pairs
	}
	for _, piece := range pieces {
		ids, _ := stringsOf(piece["members"])
		for i, members := range correctionMembers {
			if len(ids) == size && overlap(ids, members) == size && str(piece["group_label"]) == correctionAfter[i] {
				piece["group_label"] = correctionBefore[i]
			}
		}
	}
	return m
}
func derivedID(game, source string, payload Object) string {
	prefix := "vi"
	if game == "perechi" {
		prefix = "vp"
	}
	return prefix + "_" + digest(canonical(Object{"game": game, "source_id": source, "payload": identityPayload(game, source, payload)}))[:20]
}
func visible(r Object) []string {
	p := obj(r["payload"])
	if str(r["game"]) == "intrusul" {
		ids, _ := stringsOf(p["members"])
		return append(ids, str(p["intruder"]))
	}
	ids := []string{}
	for _, v := range array(p["pairs"]) {
		members, _ := stringsOf(obj(v)["members"])
		ids = append(ids, members...)
	}
	return ids
}
func (s *Sources) undirectedStrength() map[string]map[string]float64 {
	m := map[string]map[string]float64{}
	for _, e := range s.Graph.Content.Edges {
		if e.IsDistractor {
			continue
		}
		for _, pair := range [][2]string{{e.Src, e.Dst}, {e.Dst, e.Src}} {
			if m[pair[0]] == nil {
				m[pair[0]] = map[string]float64{}
			}
			m[pair[0]][pair[1]] = max(m[pair[0]][pair[1]], max(0.0, min(1.0, e.Strength)))
		}
	}
	return m
}
func (s *Sources) derivedBase(r Object, game string, payload Object, ids []string) Object {
	sal := []float64{}
	for _, id := range ids {
		sal = append(sal, s.Graph.Salience(id))
	}
	f := score(100 * (.65*mean(sal) + .35*minFloat(sal)))
	if game == "perechi" {
		f = score(100 * (.50*mean(sal) + .30*lowerQuartile(sal) + .20*minFloat(sal)))
	}
	return Object{"id": derivedID(game, str(r["id"]), payload), "game": game, "source_id": r["id"], "category": r["category"], "difficulty": r["difficulty"], "romanian_familiarity": f, "play_quality": 0, "standard_score": 0, "starter_score": 0, "starter_eligible": false, "standard_rank": 0, "starter_rank": nil, "payload": payload}
}
func finishDerived(row Object, quality float64, starter bool) {
	q := score(quality)
	f := float64(integer(row["romanian_familiarity"]))
	row["play_quality"] = q
	row["standard_score"] = score(.6*f + .4*float64(q))
	row["starter_score"] = score(.75*f + .25*float64(q))
	row["starter_eligible"] = starter
}
func (s *Sources) generateDerived() (Object, error) {
	if e := correctionSource(s.Pack); e != nil {
		return nil, e
	}
	indexed, _, e := indexPack(s.Pack)
	if e != nil {
		return nil, e
	}
	records := []Object{}
	for _, id := range derivedSources {
		if indexed[id] == nil {
			return nil, fmt.Errorf("frozen source missing %s", id)
		}
		records = append(records, indexed[id])
	}
	strength := s.undirectedStrength()
	raw := []Object{}
	intrusul, perechi := 0, 0
	for _, r := range records {
		groups := keys(obj(r["groups"]))
		for _, group := range groups {
			ids := members(r, group)
			sort.Strings(ids)
			for skip := 0; skip < 4; skip++ {
				trio := []string{}
				for i, id := range ids {
					if i != skip {
						trio = append(trio, id)
					}
				}
				typ := s.Graph.Node(trio[0]).NodeType
				same := true
				for _, id := range trio {
					if s.Graph.Node(id).NodeType != typ {
						same = false
					}
				}
				if !same {
					continue
				}
				all, positive := []float64{}, []float64{}
				for i, a := range trio {
					for _, b := range trio[i+1:] {
						v := strength[a][b]
						all = append(all, v)
						if v >= .6 {
							positive = append(positive, v)
						}
					}
				}
				if len(positive) < 2 {
					continue
				}
				for _, foreign := range groups {
					if foreign == group {
						continue
					}
					foreignIDs := members(r, foreign)
					sort.Strings(foreignIDs)
					for _, intruder := range foreignIDs {
						if s.Graph.Node(intruder).NodeType != typ {
							continue
						}
						linked := false
						for _, id := range trio {
							if _, ok := strength[id][intruder]; ok {
								linked = true
							}
						}
						if linked {
							continue
						}
						payload := Object{"members": trio, "intruder": intruder, "group_label": obj(r["group_labels"])[group]}
						visible := append(append([]string{}, trio...), intruder)
						row := s.derivedBase(r, "intrusul", payload, visible)
						sal := []float64{}
						for _, id := range visible {
							sal = append(sal, s.Graph.Salience(id))
						}
						finishDerived(row, .55*100*(.60*mean(positive)+.40*minFloat(positive))+.25*100*float64(len(positive))/3+20, minFloat(sal) >= .35 && minFloat(all) >= .7)
						raw = append(raw, row)
						intrusul++
					}
				}
			}
		}
		type option struct {
			a, b, group string
			strength    float64
		}
		options := [][]option{}
		for _, group := range groups {
			ids := members(r, group)
			sort.Strings(ids)
			choices := []option{}
			for i, a := range ids {
				for _, b := range ids[i+1:] {
					if strength[a][b] >= .6 {
						choices = append(choices, option{a, b, group, strength[a][b]})
					}
				}
			}
			options = append(options, choices)
		}
		var walk func([]option, int)
		walk = func(chosen []option, index int) {
			if index < 4 {
				for _, opt := range options[index] {
					walk(append(append([]option{}, chosen...), opt), index+1)
				}
				return
			}
			ids := []string{}
			intended := map[string]bool{}
			st := []float64{}
			pairs := []any{}
			for _, o := range chosen {
				ids = append(ids, o.a, o.b)
				intended[o.a+"\x00"+o.b] = true
				st = append(st, o.strength)
				pairs = append(pairs, Object{"members": []string{o.a, o.b}, "group_label": obj(r["group_labels"])[o.group]})
			}
			cross := 0.0
			for i, a := range ids {
				for _, b := range ids[i+1:] {
					left, right := a, b
					if left > right {
						left, right = right, left
					}
					if !intended[left+"\x00"+right] {
						cross = max(cross, strength[a][b])
					}
				}
			}
			if cross >= .6 {
				return
			}
			payload := Object{"pairs": pairs}
			row := s.derivedBase(r, "perechi", payload, ids)
			sal := []float64{}
			for _, id := range ids {
				sal = append(sal, s.Graph.Salience(id))
			}
			association := 100 * (.6*mean(st) + .4*minFloat(st))
			separation := 100 * max(0.0, 1-cross/.6)
			finishDerived(row, .75*association+.25*separation, minFloat(sal) >= .35 && minFloat(st) >= .7 && cross == 0)
			raw = append(raw, row)
			perechi++
		}
		walk(nil, 0)
	}
	if intrusul != 800 || perechi != 9164 {
		return nil, fmt.Errorf("strict derivation count drift: intrusul=%d perechi=%d", intrusul, perechi)
	}
	rows := rankAndCap(raw)
	byGame, sources, starters := Object{}, Object{}, Object{}
	for _, game := range []string{"intrusul", "perechi"} {
		n, starter := 0, 0
		seen := map[string]bool{}
		for _, r := range rows {
			if str(r["game"]) == game {
				n++
				seen[str(r["source_id"])] = true
				if r["starter_eligible"] == true {
					starter++
				}
			}
		}
		byGame[game] = n
		sources[game] = len(seen)
		starters[game] = starter
	}
	if integer(byGame["intrusul"]) != 183 || integer(byGame["perechi"]) != 153 {
		return nil, errors.New("frozen diversity cap count drift")
	}
	if e = s.bindInput(filepath.Join(s.Root, fixtures+"board_rankings_v37.json")); e != nil {
		return nil, e
	}
	ranking, e := os.ReadFile(filepath.Join(s.Root, fixtures+"board_rankings_v37.json"))
	if e != nil {
		return nil, e
	}
	return Object{"meta": Object{"schema_version": 1, "formula_version": "v38-derived-1", "pack_sha256": textDigest(s.PackBytes), "kg_sha256": s.KGHash, "rubric_sha256": s.RubricHash, "v37_rankings_sha256": textDigest(ranking), "counts": Object{"total": len(rows), "by_game": byGame, "sources_by_game": sources, "starter_by_game": starters}}, "boards": rows}, nil
}
func rankAndCap(raw []Object) []Object {
	sources := map[string][]Object{}
	for _, r := range raw {
		key := str(r["game"]) + "\x00" + str(r["source_id"])
		sources[key] = append(sources[key], r)
	}
	ks := []string{}
	for k := range sources {
		ks = append(ks, k)
	}
	sort.Strings(ks)
	rows := []Object{}
	for _, k := range ks {
		remaining := sources[k]
		used := map[string]bool{}
		for count := 0; count < 3 && len(remaining) > 0; count++ {
			novel := func(r Object) int {
				n := 0
				for _, id := range visible(r) {
					if !used[id] {
						n++
					}
				}
				return n
			}
			sort.Slice(remaining, func(i, j int) bool {
				a, b := remaining[i], remaining[j]
				if novel(a) != novel(b) {
					return novel(a) > novel(b)
				}
				for _, key := range []string{"standard_score", "play_quality", "romanian_familiarity"} {
					if integer(a[key]) != integer(b[key]) {
						return integer(a[key]) > integer(b[key])
					}
				}
				return str(a["id"]) < str(b["id"])
			})
			chosen := remaining[0]
			remaining = remaining[1:]
			rows = append(rows, chosen)
			for _, id := range visible(chosen) {
				used[id] = true
			}
		}
	}
	for _, game := range []string{"intrusul", "perechi"} {
		group, starter := []Object{}, []Object{}
		for _, r := range rows {
			if str(r["game"]) == game {
				group = append(group, r)
				if r["starter_eligible"] == true {
					starter = append(starter, r)
				}
			}
		}
		competitionRanks(group, "standard_score", "standard_rank")
		competitionRanks(starter, "starter_score", "starter_rank")
	}
	sort.Slice(rows, func(i, j int) bool {
		a, b := rows[i], rows[j]
		if str(a["game"]) != str(b["game"]) {
			return str(a["game"]) == "intrusul"
		}
		if integer(a["standard_rank"]) != integer(b["standard_rank"]) {
			return integer(a["standard_rank"]) < integer(b["standard_rank"])
		}
		return str(a["id"]) < str(b["id"])
	})
	return rows
}
func competitionRanks(rows []Object, scoreField, rankField string) {
	sort.Slice(rows, func(i, j int) bool {
		if integer(rows[i][scoreField]) != integer(rows[j][scoreField]) {
			return integer(rows[i][scoreField]) > integer(rows[j][scoreField])
		}
		return str(rows[i]["id"]) < str(rows[j]["id"])
	})
	last, rank := -1, 0
	for i, r := range rows {
		score := integer(r[scoreField])
		if score != last {
			rank = i + 1
			last = score
		}
		r[rankField] = rank
	}
}
func (s *Sources) sidecar(document Object, name string, write bool) (Object, error) {
	changes := map[string][]byte{}
	formatDrift := false
	blob, e := render(document)
	if e != nil {
		return nil, e
	}
	for _, rel := range []string{fixtures + name, "tests/fixtures/" + name} {
		path := filepath.Join(s.Root, rel)
		got, b, e := read(path)
		if e != nil {
			return nil, e
		}
		if !write && !bytes.Equal(canonical(got), canonical(document)) {
			return nil, fmt.Errorf("%s is semantically stale; regenerate with --write", rel)
		}
		formatDrift = formatDrift || !bytes.Equal(b, blob)
		changes[path] = blob
	}
	if write {
		e = s.commit(changes, nil)
	}
	return Object{"artifact": name, "counts": obj(document["meta"])["counts"], "semantic_match": !write, "format_drift": formatDrift, "write": write}, e
}
func (s *Sources) Derive(write bool) (Object, error) {
	document, e := s.generateDerived()
	if e != nil {
		return nil, e
	}
	return s.sidecar(document, "derived_catalog_v38.json", write)
}
