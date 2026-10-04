package contentops

import (
	"bytes"
	"crypto/sha512"
	"errors"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
)

type candidateBatch struct {
	category                    string
	candidate, factual, quality Object
	bytes                       []byte
	bindings                    Object
	exclusions                  []Object
}

func preflightCandidates(dir string, s *Sources) ([]candidateBatch, error) {
	entries, e := os.ReadDir(dir)
	if e != nil {
		return nil, e
	}
	batches := []candidateBatch{}
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		cat := entry.Name()
		path := filepath.Join(dir, cat)
		if _, e := os.Stat(filepath.Join(path, "candidates.json")); os.IsNotExist(e) {
			continue
		}
		if !regexp.MustCompile(`^[a-z][a-z0-9_]{0,63}$`).MatchString(cat) || s.Graph.Content.CategoryLabels[cat] == "" {
			return nil, fmt.Errorf("unknown candidate category %s", cat)
		}
		for _, name := range []string{"candidates.json", "verify_factual.json", "verify_quality.json"} {
			if e = s.bindInput(filepath.Join(path, name)); e != nil {
				return nil, e
			}
		}
		c, blob, e := read(filepath.Join(path, "candidates.json"))
		if e != nil {
			return nil, e
		}
		f, fb, e := read(filepath.Join(path, "verify_factual.json"))
		if e != nil {
			return nil, e
		}
		q, qb, e := read(filepath.Join(path, "verify_quality.json"))
		if e != nil {
			return nil, e
		}
		if len(c) != 6 {
			return nil, errors.New("candidates require exactly nodes, edges and four game arrays")
		}
		for _, k := range append([]string{"nodes", "edges"}, Games...) {
			if _, ok := c[k].([]any); !ok {
				return nil, fmt.Errorf("candidates missing %s array", k)
			}
		}
		if len(array(c["nodes"])) != 0 || len(array(c["edges"])) != 0 {
			return nil, errors.New("pack-only import refuses graph additions")
		}
		binding := "sha256:" + digest(blob)
		for _, a := range []Object{f, q} {
			if str(a["category"]) != cat || str(a["candidate_sha256"]) != binding || !nonblank(a["coverage_note"]) {
				return nil, errors.New("stale or incomplete candidate review header")
			}
		}
		if !nonblank(f["reviewer"]) || !nonblank(q["reviewer"]) || normalizedPhrase(str(f["reviewer"])) == normalizedPhrase(str(q["reviewer"])) {
			return nil, errors.New("factual and quality reviewers must be independently identified")
		}
		refs := []string{}
		for _, game := range Games {
			for i, v := range array(c[game]) {
				if obj(v) == nil {
					return nil, errors.New("candidate instance must be object")
				}
				refs = append(refs, fmt.Sprintf("%s[%d]", game, i))
			}
		}
		if len(refs) == 0 {
			return nil, errors.New("empty candidate category")
		}
		reviewed, e := uniqueStrings(f["reviewed_refs"])
		if e != nil {
			return nil, e
		}
		sort.Strings(reviewed)
		sort.Strings(refs)
		if !exactStrings(reviewed, refs) {
			return nil, errors.New("factual coverage does not exactly cover raw candidate refs")
		}
		known := map[string]bool{}
		for _, r := range refs {
			known[r] = true
		}
		blocked := map[string]bool{}
		issues, ok := f["issues"].([]any)
		if !ok {
			return nil, errors.New("factual issues must be array")
		}
		exclusions := []Object{}
		for _, v := range issues {
			row := obj(v)
			ref := str(row["ref"])
			severity := str(row["severity"])
			if row == nil || !known[ref] || !nonblank(row["issue"]) || (severity != "block" && severity != "note") {
				return nil, errors.New("unknown reference, invalid issue or unresolved factual fix")
			}
			if severity == "block" {
				blocked[ref] = true
				exclusions = append(exclusions, Object{"ref": ref, "reason": row["issue"], "layer": "factual"})
			}
		}
		quality := Object{}
		instances, ok := q["instances"].([]any)
		if !ok {
			return nil, errors.New("quality instances must be array")
		}
		for _, v := range instances {
			row := obj(v)
			ref := str(row["ref"])
			verdict := str(row["verdict"])
			if row == nil || !known[ref] || quality[ref] != nil || !nonblank(row["note"]) || (verdict != "keep" && verdict != "drop") {
				return nil, errors.New("quality unknown/duplicate ref, invalid note or unresolved fix")
			}
			quality[ref] = row
			if verdict == "drop" {
				exclusions = append(exclusions, Object{"ref": ref, "reason": row["note"], "layer": "quality"})
			}
		}
		if len(quality) != len(refs) {
			return nil, errors.New("quality coverage incomplete")
		}
		for ref := range blocked {
			quality[ref] = Object{"verdict": "drop"}
		}
		q["indexed"] = quality
		batches = append(batches, candidateBatch{cat, c, f, q, blob, Object{"candidate_sha256": binding, "factual_sha256": "sha256:" + digest(fb), "quality_sha256": "sha256:" + digest(qb), "factual_reviewer": f["reviewer"], "quality_reviewer": q["reviewer"]}, exclusions})
	}
	if len(batches) == 0 {
		return nil, errors.New("no candidate category artifacts")
	}
	return batches, nil
}
func highWater(pack Object) Object {
	out := Object{}
	persisted := obj(obj(pack["meta"])["id_high_water"])
	for _, g := range Games {
		mark := max(0, integer(persisted[g]))
		re := regexp.MustCompile(`^` + prefixes[g] + `_.*_([0-9]+)$`)
		for _, v := range array(pack[g]) {
			m := re.FindStringSubmatch(str(obj(v)["id"]))
			if len(m) > 1 {
				var n int
				fmt.Sscan(m[1], &n)
				mark = max(mark, n)
			}
		}
		out[g] = mark
	}
	return out
}
func (s *Sources) Import(dir string, write bool) (Object, error) {
	batches, e := preflightCandidates(dir, s)
	if e != nil {
		return nil, e
	}
	water := highWater(s.Pack)
	allocated := []Object{}
	provenance := []Object{}
	for _, batch := range batches {
		for _, game := range Games {
			for i, v := range array(batch.candidate[game]) {
				ref := fmt.Sprintf("%s[%d]", game, i)
				if str(obj(obj(batch.quality["indexed"])[ref])["verdict"]) != "keep" {
					continue
				}
				raw := obj(v)
				r := Object{"id": fmt.Sprintf("%s_%s_%03d", prefixes[game], batch.category, integer(water[game])+1), "category": batch.category, "source": "ai", "status": "pending", "difficulty": raw["difficulty"]}
				if str(r["difficulty"]) == "" {
					r["difficulty"] = "normal"
				}
				switch game {
				case "conexiuni":
					groups := array(raw["groups"])
					if len(groups) != 4 {
						return nil, errors.New("candidate needs four groups")
					}
					gm, labels := Object{}, Object{}
					order := []string{}
					for j, v := range groups {
						group := obj(v)
						ids, e := uniqueStrings(group["tiles"])
						if e != nil || len(ids) != 4 || !nonblank(group["label"]) {
							return nil, errors.New("candidate group needs four tiles and label")
						}
						key := fmt.Sprintf("g%d", j+1)
						gm[key] = ids
						labels[key] = group["label"]
						order = append(order, ids...)
					}
					seed := []byte(fmt.Sprintf("%s:%d", batch.category, i))
					hashed := sha512.Sum512(seed)
					combined := append(append([]byte{}, seed...), hashed[:]...)
					pyrandom.New(new(big.Int).SetBytes(combined)).ShuffleStrings(order)
					r["groups"] = gm
					r["group_labels"] = labels
					r["order"] = order
				case "contexto":
					r["target"] = raw["target"]
				case "lant":
					start, target := str(raw["start"]), str(raw["target"])
					for _, debt := range s.LantRejections {
						if str(debt["start"]) == start && str(debt["target"]) == target {
							return nil, fmt.Errorf("candidate reuses rejected directed pair %s", debt["id"])
						}
					}
					r["start"] = start
					r["target"] = target
					distance, ok := s.Graph.DistancesFrom(start)[target]
					if !ok {
						return nil, errors.New("candidate Lanț unreachable")
					}
					r["optimal"] = distance
					band := adjustBand(distance, str(r["difficulty"]), map[string][2]int{"usor": {2, 3}, "normal": {3, 4}, "greu": {4, 6}})
					if band == "" {
						return nil, errors.New("candidate Lanț outside difficulty bounds")
					}
					r["difficulty"] = band
				case "alchimie":
					seeds, e := uniqueStrings(raw["seeds"])
					if e != nil || len(seeds) < 5 || len(seeds) > 7 {
						return nil, errors.New("candidate Alchimie needs 5-7 distinct seeds")
					}
					target := str(raw["target"])
					profile, e := s.RawCraft(seeds, target, batch.category)
					if e != nil {
						return nil, e
					}
					depth := integer(obj(profile["profile"])["target_generation"])
					band := adjustBand(depth, str(r["difficulty"]), map[string][2]int{"usor": {2, 2}, "normal": {2, 3}, "greu": {3, 5}})
					if band == "" {
						return nil, errors.New("candidate Alchimie generation outside difficulty bounds")
					}
					r["difficulty"] = band
					r["seeds"] = seeds
					r["target"] = target
					r["target_depth"] = integer(obj(profile["recipe"])["exact_actions"])
				}
				normalized, err := Decode(canonical(r))
				if err != nil {
					return nil, err
				}
				r = normalized
				errs := append(contentbuild.ValidateEnvelope(game, r), contentbuild.ValidatePayload(s.Graph, game, r)...)
				if len(errs) > 0 {
					return nil, fmt.Errorf("invalid kept candidate %s: %s", ref, strings.Join(errs, "; "))
				}
				s.Pack[game] = append(array(s.Pack[game]), r)
				water[game] = integer(water[game]) + 1
				allocated = append(allocated, Object{"id": r["id"], "game": game, "category": batch.category, "raw_ref": ref})
			}
		}
		provenance = append(provenance, Object{"category": batch.category, "bindings": batch.bindings, "exclusions": batch.exclusions})
	}
	refreshCounts(s.Pack)
	obj(s.Pack["meta"])["id_high_water"] = water
	receipt := Object{"operator": "native-pack-only-import-v1", "source_pack_sha256": digest(s.PackBytes), "kg_sha256": s.KGHash, "rubric_sha256": s.RubricHash, "allocated": allocated, "categories": provenance, "write": write}
	obj(s.Pack["meta"])["last_import"] = copyObject(receipt)
	changes, e := packChanges(s.Root, s.Pack)
	if e != nil {
		return nil, e
	}
	if e = s.validateProspective(changes); e != nil {
		return nil, e
	}
	if write {
		if e = s.commit(changes, s.validateCurrent); e != nil {
			return nil, e
		}
	}
	return receipt, nil
}
func adjustBand(depth int, preferred string, bands map[string][2]int) string {
	if b, ok := bands[preferred]; ok && depth >= b[0] && depth <= b[1] {
		return preferred
	}
	for _, band := range []string{"usor", "normal", "greu"} {
		b := bands[band]
		if depth >= b[0] && depth <= b[1] {
			return band
		}
	}
	return ""
}
func (s *Sources) validateCurrent() error {
	errs := contentbuild.ValidatePack(filepath.Join(s.Root, fixtures+"kg_sample.json"), filepath.Join(s.Root, packCopies[0]))
	if len(errs) > 0 {
		return fmt.Errorf("pack validation failed: %s", strings.Join(errs, "; "))
	}
	_, _, e := mirrors(s.Root)
	return e
}
func (s *Sources) validateProspective(changes map[string][]byte) error {
	b := changes[filepath.Join(s.Root, packCopies[0])]
	if b == nil {
		return errors.New("missing prospective pack")
	}
	pack, e := Decode(b)
	if e != nil {
		return e
	}
	errs := contentbuild.ValidatePackObjects(s.KG, pack)
	if len(errs) > 0 {
		return fmt.Errorf("prospective pack validation failed: %s", strings.Join(errs, "; "))
	}
	current, e := os.ReadFile(filepath.Join(s.Root, packCopies[0]))
	if e != nil {
		return e
	}
	if !bytes.Equal(current, s.PackBytes) {
		return errors.New("source pack changed during preflight")
	}
	return nil
}
