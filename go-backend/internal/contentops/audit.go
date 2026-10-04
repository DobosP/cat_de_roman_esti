package contentops

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/alchimie"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
)

func (s *Sources) runtimeManifest() ([]Object, error) {
	names := []string{}
	inventory, e := runtimeInventory(s.Root)
	if e != nil {
		return nil, e
	}
	for _, path := range inventory {
		relative, e := filepath.Rel(s.Root, path)
		if e != nil {
			return nil, e
		}
		names = append(names, filepath.ToSlash(relative))
	}
	if _, e := os.Stat(filepath.Join(s.Root, fixtures+"alchimie_recipe_extensions_v92.json")); e == nil {
		names = append(names, fixtures+"alchimie_recipe_extensions_v92.json")
	}
	sort.Strings(names)
	entries := []Object{}
	for _, name := range names {
		b, e := os.ReadFile(filepath.Join(s.Root, name))
		if e != nil {
			return nil, e
		}
		entries = append(entries, Object{"path": name, "sha256": digest(b)})
	}
	if len(entries) < 4 {
		return nil, errors.New("native projection source manifest incomplete")
	}
	return entries, nil
}
func (s *Sources) audit(ids []string, dossiers map[string]Object) (Object, error) {
	sorted := append([]string{}, ids...)
	sort.Strings(sorted)
	if len(ids) == 0 || !exactStrings(ids, sorted) {
		return nil, errors.New("projection ids must be sorted and nonempty")
	}
	rows, games, e := indexPack(s.Pack)
	if e != nil {
		return nil, e
	}
	for _, id := range ids {
		if rows[id] == nil || games[id] != "alchimie" || str(rows[id]["status"]) != "pending" || dossiers[id] == nil {
			return nil, errors.New("projection batch must be exact pending Alchimie-only")
		}
	}
	c := s.Graph.Content
	if _, e := os.Stat(filepath.Join(s.Root, fixtures+"alchimie_recipe_extensions_v92.json")); e == nil {
		extensions, _, e := read(filepath.Join(s.Root, fixtures+"alchimie_recipe_extensions_v92.json"))
		if e != nil {
			return nil, e
		}
		if e = contentbuild.ValidateRecipeExtensions(extensions); e != nil {
			return nil, e
		}
		c.RecipeExtensions = extensions
	}
	svc := alchimie.New(c)
	runtime, e := s.runtimeManifest()
	if e != nil {
		return nil, e
	}
	generatorPath := "go-backend/internal/contentops/audit.go"
	generator, e := os.ReadFile(filepath.Join(s.Root, generatorPath))
	if e != nil {
		return nil, e
	}
	manifest := []Object{}
	items := []Object{}
	for _, id := range ids {
		r := rows[id]
		seeds, e := uniqueStrings(r["seeds"])
		if e != nil {
			return nil, e
		}
		target, category := str(r["target"]), str(r["category"])
		projection := svc.ProjectionForReview(seeds, target, category)
		if projection == nil {
			return nil, fmt.Errorf("runtime cannot project %s", id)
		}
		par, certified := contentbuild.MinimumAlchimieActions(s.Graph, seeds, target, category)
		if !certified {
			return nil, errors.New("exact raw action par not certified")
		}
		if par != projection.Par || par != integer(r["target_depth"]) {
			return nil, errors.New("declared/live/exact action par disagree")
		}
		owned := map[string]bool{}
		concepts := map[string]bool{}
		for _, x := range seeds {
			owned[x] = true
			concepts[x] = true
		}
		pairs := []alchimie.Pair{}
		for pair := range projection.Recipes {
			pairs = append(pairs, pair)
		}
		sort.Slice(pairs, func(i, j int) bool {
			if pairs[i][0] != pairs[j][0] {
				return pairs[i][0] < pairs[j][0]
			}
			return pairs[i][1] < pairs[j][1]
		})
		recipes := []Object{}
		maxOutputs := 0
		for _, pair := range pairs {
			results := projection.Recipes[pair]
			recipes = append(recipes, Object{"pair": pair, "results": results})
			maxOutputs = max(maxOutputs, len(results))
			for _, x := range pair {
				concepts[x] = true
			}
			for _, x := range results {
				concepts[x] = true
			}
		}
		openings := []Object{}
		seedSort := append([]string{}, seeds...)
		sort.Strings(seedSort)
		for i, a := range seedSort {
			for _, b := range seedSort[i+1:] {
				results := []Object{}
				pairKey := alchimie.Pair{a, b}
				for _, x := range projection.Recipes[pairKey] {
					if !owned[x] {
						results = append(results, Object{"id": x, "label": s.Graph.Label(x)})
					}
				}
				if len(results) > 0 {
					openings = append(openings, Object{"left": Object{"id": a, "label": s.Graph.Label(a)}, "right": Object{"id": b, "label": s.Graph.Label(b)}, "results": results})
				}
			}
		}
		bounds := Object{"declared_par_matches_exact": true, "projection_par_matches_exact": true, "route_limit": len(projection.Routes) <= 4, "recipe_pair_limit": len(recipes) <= 24, "projected_concept_limit": len(concepts) <= 32, "result_per_pair_limit": maxOutputs <= 2, "e2_live_opening_floor": len(openings) >= 2}
		for _, v := range bounds {
			if v != true {
				return nil, fmt.Errorf("live projection bounds fail %s", id)
			}
		}
		structural := Object{"par": projection.Par, "recipes": recipes, "routes": projection.Routes}
		items = append(items, Object{"id": id, "review_binding": dossiers[id]["review_binding"], "record_sha256": digest(canonical(r)), "source_record": r, "category": category, "difficulty": r["difficulty"], "seeds": seeds, "target": Object{"id": target, "label": s.Graph.Label(target)}, "declared_target_depth": r["target_depth"], "exact_action_par": par, "projection_par": projection.Par, "projection_sha256": digest(canonical(structural)), "projected_opening_pair_count": len(openings), "projected_opening_pairs": openings, "route_count": len(projection.Routes), "recipe_pair_count": len(recipes), "projected_concept_count": len(concepts), "max_results_per_pair": maxOutputs, "routes": projection.Routes, "bounds": bounds})
		manifest = append(manifest, Object{"id": id, "review_binding": dossiers[id]["review_binding"]})
	}
	return Object{"schema": "alchimie-live-projection-audit-v1", "game": "alchimie", "mode": "gate", "status": "pending", "input_ids": ids, "input_ids_sha256": digest([]byte(strings.Join(ids, "\n") + "\n")), "pack_sha256": digest(s.PackBytes), "kg_sha256": s.KGHash, "rubric_sha256": s.RubricHash, "dossier_manifest_sha256": digest(canonical(manifest)), "runtime_sources": runtime, "runtime_source_manifest_sha256": digest(canonical(runtime)), "generator": Object{"path": generatorPath, "sha256": digest(generator)}, "summary": Object{"records": len(items), "live_opening_floor_failures": 0}, "items": items}, nil
}
func (s *Sources) validateProjection(blob []byte, ids []string, dossiers map[string]Object) error {
	got, e := Decode(blob)
	if e != nil {
		return e
	}
	expected, e := s.audit(ids, dossiers)
	if e != nil {
		return e
	}
	if !bytes.Equal(canonical(got), canonical(expected)) {
		return errors.New("stale or unreproducible native projection audit")
	}
	return nil
}
func (s *Sources) AuditProjections(ids []string, dossierDir, out string, write bool) (Object, error) {
	current, e := s.Dossiers(ids, "pending", "alchimie")
	if e != nil {
		return nil, e
	}
	if e = s.bindDossiers(dossierDir, ids); e != nil {
		return nil, e
	}
	dossiers, e := readDossiers(dossierDir, ids, current)
	if e != nil {
		return nil, e
	}
	audit, e := s.audit(ids, dossiers)
	if e != nil {
		return nil, e
	}
	if write {
		out, e = filepath.Abs(out)
		if e != nil {
			return nil, e
		}
		blob, e := render(audit)
		if e != nil {
			return nil, e
		}
		if e = s.commit(map[string][]byte{out: blob}, nil); e != nil {
			return nil, e
		}
	}
	return audit, nil
}
