package contentops

import (
	"bytes"
	"errors"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

func gateVerdict(a, v string) string {
	if !validVerdict(a) || !validVerdict(v) {
		return ""
	}
	if a == "promote" && v == "promote" {
		return "promote"
	}
	if a == "reject" || v == "reject" {
		return "reject"
	}
	return "keep"
}
func validVerdict(s string) bool { return s == "promote" || s == "reject" || s == "keep" }
func exactKeys(m Object, expected ...string) bool {
	if len(m) != len(expected) {
		return false
	}
	for _, k := range expected {
		if _, ok := m[k]; !ok {
			return false
		}
	}
	return true
}
func readReview(path, role string) (Object, []byte, error) {
	m, b, e := read(path)
	if e != nil {
		return nil, nil, e
	}
	if !exactKeys(m, "reviewer", "role", "input_ids", "items") || !nonblank(m["reviewer"]) || str(m["reviewer"]) != strings.TrimSpace(str(m["reviewer"])) || str(m["role"]) != role {
		return nil, nil, fmt.Errorf("invalid %s reviewer contract", role)
	}
	ids, e := uniqueStrings(m["input_ids"])
	if e != nil || len(ids) == 0 {
		return nil, nil, errors.New("review input_ids must be unique and nonempty")
	}
	wanted := map[string]bool{}
	for _, id := range ids {
		wanted[id] = true
	}
	seen := map[string]bool{}
	for _, v := range array(m["items"]) {
		r := obj(v)
		game, id := str(r["game"]), str(r["id"])
		k := []string{"id", "game", "verdict", "review_binding", "rationale", "sources"}
		if game == "alchimie" {
			k = append(k, "projection_audit_sha256")
		}
		if !exactKeys(r, k...) || !safeID(id) || !wanted[id] || seen[id] || !gameKnown(game) || !validVerdict(str(r["verdict"])) || !validBinding(str(r["review_binding"])) || !nonblank(r["rationale"]) {
			return nil, nil, fmt.Errorf("invalid %s judgment %s", role, id)
		}
		sources, ok := r["sources"].([]any)
		if !ok || (role == "verifier" && len(sources) == 0) {
			return nil, nil, errors.New("verifier judgments require explicit web sources")
		}
		for _, v := range sources {
			if !contentbuild.ValidReference(str(v)) {
				return nil, nil, errors.New("invalid review source URL")
			}
		}
		if game == "alchimie" && !validHex(str(r["projection_audit_sha256"])) {
			return nil, nil, errors.New("missing projection review digest")
		}
		seen[id] = true
	}
	if len(seen) != len(ids) {
		return nil, nil, errors.New("review coverage incomplete")
	}
	return m, b, nil
}
func indexReview(m Object) map[string]Object {
	out := map[string]Object{}
	for _, v := range array(m["items"]) {
		r := obj(v)
		out[str(r["id"])] = r
	}
	return out
}
func readDossiers(dir string, ids []string, current map[string]Object) (map[string]Object, error) {
	entries, e := os.ReadDir(dir)
	if e != nil {
		return nil, e
	}
	actual := []string{}
	for _, entry := range entries {
		if !entry.IsDir() && strings.HasSuffix(entry.Name(), ".json") {
			actual = append(actual, strings.TrimSuffix(entry.Name(), ".json"))
		}
	}
	expected := append([]string{}, ids...)
	sort.Strings(expected)
	sort.Strings(actual)
	if !exactStrings(actual, expected) {
		return nil, errors.New("dossier directory does not exactly cover batch")
	}
	out := map[string]Object{}
	for _, id := range ids {
		d, _, e := read(filepath.Join(dir, id+".json"))
		if e != nil {
			return nil, e
		}
		if str(d["id"]) != id || str(d["status"]) != "pending" || !gameKnown(str(d["game"])) || str(d["review_binding"]) != binding(d) || current[id] == nil || str(d["review_binding"]) != str(current[id]["review_binding"]) {
			return nil, fmt.Errorf("stale or invalid dossier %s", id)
		}
		out[id] = d
	}
	return out, nil
}
func buildArtifacts(a, v Object, ab, vb []byte, dossiers map[string]Object, projection []byte) (map[string]Object, error) {
	ids, e := uniqueStrings(a["input_ids"])
	if e != nil {
		return nil, e
	}
	other, e := uniqueStrings(v["input_ids"])
	if e != nil || !exactStrings(ids, other) {
		return nil, errors.New("analyst/verifier input_ids differ")
	}
	if normalizedPhrase(str(a["reviewer"])) == normalizedPhrase(str(v["reviewer"])) {
		return nil, errors.New("analyst/verifier must have distinct reviewer IDs")
	}
	ai, vi := indexReview(a), indexReview(v)
	games := map[string]bool{}
	for _, id := range ids {
		d := dossiers[id]
		if d == nil {
			return nil, errors.New("missing dossier")
		}
		games[str(d["game"])] = true
		for _, r := range []Object{ai[id], vi[id]} {
			if str(r["game"]) != str(d["game"]) || str(r["review_binding"]) != str(d["review_binding"]) {
				return nil, fmt.Errorf("review identity/binding mismatch %s", id)
			}
		}
	}
	projectionDigest := ""
	if games["alchimie"] {
		sorted := append([]string{}, ids...)
		sort.Strings(sorted)
		if len(games) != 1 || !exactStrings(ids, sorted) || len(projection) == 0 {
			return nil, errors.New("Alchimie requires sorted separate batch and projection audit")
		}
		projectionDigest = digest(projection)
		for _, id := range ids {
			if str(ai[id]["projection_audit_sha256"]) != projectionDigest || str(vi[id]["projection_audit_sha256"]) != projectionDigest {
				return nil, errors.New("reviewed projection bytes differ")
			}
		}
	} else if len(projection) > 0 {
		return nil, errors.New("projection audit supplied for non-Alchimie batch")
	}
	provenance := Object{"analyst": Object{"path": "reviews/analyst.json", "sha256": "sha256:" + digest(ab), "reviewer": a["reviewer"], "role": "analyst"}, "verifier": Object{"path": "reviews/verifier.json", "sha256": "sha256:" + digest(vb), "reviewer": v["reviewer"], "role": "verifier"}}
	artifacts := map[string]Object{}
	for _, game := range Games {
		verdicts := Object{}
		rows := []Object{}
		for _, id := range ids {
			if str(dossiers[id]["game"]) != game {
				continue
			}
			left, right := ai[id], vi[id]
			final := gateVerdict(str(left["verdict"]), str(right["verdict"]))
			policy := "conservative-keep"
			if final == "promote" {
				policy = "unanimous-promote"
			} else if final == "reject" {
				policy = "reject-wins"
			} else if str(left["verdict"]) == "keep" && str(right["verdict"]) == "keep" {
				policy = "unanimous-keep"
			}
			verdicts[id] = final
			row := Object{"id": id, "game": game, "final": final, "analyst": left["verdict"], "verifier": right["verdict"], "verified": true, "verifier_lost": false, "review_binding": dossiers[id]["review_binding"], "policy": policy, "analyst_review": left, "verifier_review": right}
			if game == "alchimie" {
				row["analyst_projection_audit_sha256"] = projectionDigest
				row["verifier_projection_audit_sha256"] = projectionDigest
			}
			rows = append(rows, row)
		}
		if len(rows) == 0 {
			continue
		}
		batch := Object{"version": 2, "mode": "gate", "input_ids": ids}
		if game == "alchimie" {
			batch["projection_audit_sha256"] = projectionDigest
		}
		artifacts[game] = Object{"game": game, "mode": "gate", "batch": batch, "verdicts": verdicts, "perItem": rows, "coverage": Object{"total": len(rows), "verified": len(rows), "unverifiedClean": 0, "verifiersLost": 0, "lost": 0}, "provenance": provenance}
	}
	return artifacts, nil
}

// BuildReview creates portable artifacts from authored independent judgments.
// It never produces a judgment, approves an item or follows a source URL.
func (s *Sources) BuildReview(analyst, verifier, dossierDir, projectionPath, outDir string, write bool) (Object, error) {
	for _, p := range []string{analyst, verifier} {
		if e := s.bindInput(p); e != nil {
			return nil, e
		}
	}
	if projectionPath != "" {
		if e := s.bindInput(projectionPath); e != nil {
			return nil, e
		}
	}
	a, ab, e := readReview(analyst, "analyst")
	if e != nil {
		return nil, e
	}
	v, vb, e := readReview(verifier, "verifier")
	if e != nil {
		return nil, e
	}
	ids, _ := uniqueStrings(a["input_ids"])
	current, e := s.Dossiers(ids, "pending", "")
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
	var projection []byte
	if projectionPath != "" {
		_, projection, e = read(projectionPath)
		if e != nil {
			return nil, e
		}
		if e = s.validateProjection(projection, ids, dossiers); e != nil {
			return nil, e
		}
	}
	artifacts, e := buildArtifacts(a, v, ab, vb, dossiers, projection)
	if e != nil {
		return nil, e
	}
	receipt := Object{"items": len(ids), "games": len(artifacts), "input_ids": ids, "write": write}
	if !write {
		return receipt, nil
	}
	changes := map[string][]byte{}
	outDir, e = filepath.Abs(outDir)
	if e != nil {
		return nil, e
	}
	if _, e = os.Stat(outDir); e == nil {
		entries, e := os.ReadDir(outDir)
		if e != nil {
			return nil, e
		}
		if len(entries) != 0 {
			return nil, errors.New("refusing to overwrite nonempty review output")
		}
	} else if !os.IsNotExist(e) {
		return nil, e
	}
	if e = os.MkdirAll(filepath.Join(outDir, "dossiers"), 0700); e != nil {
		return nil, e
	}
	if e = os.MkdirAll(filepath.Join(outDir, "reviews"), 0700); e != nil {
		return nil, e
	}
	for game, a := range artifacts {
		b, e := render(a)
		if e != nil {
			return nil, e
		}
		changes[filepath.Join(outDir, game+"_verdicts.json")] = b
	}
	for id, d := range dossiers {
		b, e := render(d)
		if e != nil {
			return nil, e
		}
		changes[filepath.Join(outDir, "dossiers", id+".json")] = b
	}
	changes[filepath.Join(outDir, "reviews/analyst.json")] = ab
	changes[filepath.Join(outDir, "reviews/verifier.json")] = vb
	if len(projection) > 0 {
		changes[filepath.Join(outDir, "projection-audit.json")] = projection
	}
	e = s.commit(changes, nil)
	return receipt, e
}
func (s *Sources) WriteDossiers(ids []string, status, game, dir string, strict, write bool) (Object, error) {
	dossiers, e := s.Dossiers(ids, status, game)
	if e != nil {
		return nil, e
	}
	fails, warns := 0, 0
	changes := map[string][]byte{}
	for _, id := range ids {
		for _, v := range dossiers[id]["lint_findings"].([]Object) {
			if str(v["level"]) == "FAIL" {
				fails++
			} else {
				warns++
			}
		}
		if write {
			b, e := render(dossiers[id])
			if e != nil {
				return nil, e
			}
			changes[filepath.Join(dir, id+".json")] = b
		}
	}
	receipt := Object{"input_ids": ids, "failures": fails, "warnings": warns, "dossiers": dossiers, "write": write}
	if strict && fails > 0 {
		return receipt, fmt.Errorf("strict deterministic critique: %d failures", fails)
	}
	if write {
		dir, e = filepath.Abs(dir)
		if e != nil {
			return nil, e
		}
		if e = os.MkdirAll(dir, 0700); e != nil {
			return nil, e
		}
		changes = map[string][]byte{}
		for _, id := range ids {
			b, _ := render(dossiers[id])
			changes[filepath.Join(dir, id+".json")] = b
		}
		e = s.commit(changes, nil)
	}
	return receipt, e
}
func (s *Sources) ApplyReview(dir string, write bool) (Object, error) {
	return s.applyReview(dir, write, nil)
}
func (s *Sources) applyReview(dir string, write bool, extra map[string][]byte) (Object, error) {
	for _, p := range []string{"reviews/analyst.json", "reviews/verifier.json", "projection-audit.json"} {
		if e := s.bindInput(filepath.Join(dir, p)); e != nil {
			return nil, e
		}
	}
	a, ab, e := readReview(filepath.Join(dir, "reviews/analyst.json"), "analyst")
	if e != nil {
		return nil, e
	}
	v, vb, e := readReview(filepath.Join(dir, "reviews/verifier.json"), "verifier")
	if e != nil {
		return nil, e
	}
	ids, _ := uniqueStrings(a["input_ids"])
	current, e := s.Dossiers(ids, "pending", "")
	if e != nil {
		return nil, e
	}
	if e = s.bindDossiers(filepath.Join(dir, "dossiers"), ids); e != nil {
		return nil, e
	}
	dossiers, e := readDossiers(filepath.Join(dir, "dossiers"), ids, current)
	if e != nil {
		return nil, e
	}
	var projection []byte
	if _, e = os.Stat(filepath.Join(dir, "projection-audit.json")); e == nil {
		_, projection, e = read(filepath.Join(dir, "projection-audit.json"))
		if e != nil {
			return nil, e
		}
		if e = s.validateProjection(projection, ids, dossiers); e != nil {
			return nil, e
		}
	}
	expected, e := buildArtifacts(a, v, ab, vb, dossiers, projection)
	if e != nil {
		return nil, e
	}
	files, e := filepath.Glob(filepath.Join(dir, "*_verdicts.json"))
	if e != nil {
		return nil, e
	}
	if len(files) != len(expected) {
		return nil, errors.New("gate artifact files do not exactly cover games")
	}
	verdicts, bindings, gateDigests := map[string]string{}, map[string]string{}, map[string]string{}
	for game, exp := range expected {
		if e = s.bindInput(filepath.Join(dir, game+"_verdicts.json")); e != nil {
			return nil, e
		}
		got, b, e := read(filepath.Join(dir, game+"_verdicts.json"))
		if e != nil {
			return nil, e
		}
		if !bytes.Equal(canonical(got), canonical(exp)) {
			return nil, errors.New("gate artifact differs from independently archived judgments")
		}
		for id, v := range obj(got["verdicts"]) {
			verdicts[id] = str(v)
			bindings[id] = str(dossiers[id]["review_binding"])
			gateDigests[id] = digest(b)
		}
	}
	promote := map[string]bool{}
	for id, v := range verdicts {
		if v == "promote" {
			promote[id] = true
		}
	}
	rows, games, e := indexPack(s.Pack)
	if e != nil {
		return nil, e
	}
	for id := range promote {
		for _, f := range s.Findings(rows[id], games[id], promote) {
			if str(f["level"]) == "FAIL" {
				return nil, fmt.Errorf("promotion blocked %s: %s", id, f["check"])
			}
		}
	}
	changes := map[string][]byte{}
	stats := Object{"promote": 0, "reject": 0, "keep": 0}
	water := highWater(s.Pack)
	rejected := map[string][]Object{}
	for _, game := range Games {
		kept := []any{}
		for _, v := range array(s.Pack[game]) {
			r := obj(v)
			id := str(r["id"])
			verdict := verdicts[id]
			if verdict == "promote" {
				r = copyObject(r)
				r["status"] = "approved"
				stats["promote"] = integer(stats["promote"]) + 1
				kept = append(kept, r)
			} else if verdict == "reject" {
				stats["reject"] = integer(stats["reject"]) + 1
				rejected[game] = append(rejected[game], r)
			} else {
				kept = append(kept, r)
				if verdict == "keep" {
					stats["keep"] = integer(stats["keep"]) + 1
				}
			}
		}
		s.Pack[game] = kept
	}
	refreshCounts(s.Pack)
	obj(s.Pack["meta"])["id_high_water"] = water
	changes, e = packChanges(s.Root, s.Pack)
	if e != nil {
		return nil, e
	}
	for p, b := range extra {
		changes[p] = b
	}
	for _, game := range []string{"conexiuni", "lant"} {
		if len(rejected[game]) == 0 {
			continue
		}
		ledger, _, e := read(ledgerPath(s.Root, game))
		if e != nil {
			return nil, e
		}
		items := obj(ledger["items"])
		for _, r := range rejected[game] {
			id := str(r["id"])
			entry := Object{"record_sha256": digest(canonical(r)), "review_binding": bindings[id], "source_gate_sha256": gateDigests[id]}
			if game == "conexiuni" {
				gm := Object{}
				for i, k := range keys(obj(r["groups"])) {
					gm[fmt.Sprintf("g%d", i+1)] = obj(r["groups"])[k]
				}
				entry["groups"] = gm
				entry["groups_sha256"] = digest(canonical(gm))
			} else {
				entry["start"] = r["start"]
				entry["target"] = r["target"]
				entry["pair_sha256"] = digest(canonical(Object{"start": r["start"], "target": r["target"]}))
			}
			if old := items[id]; old != nil && !bytes.Equal(canonical(old), canonical(entry)) {
				return nil, errors.New("rejection tombstone ID conflict")
			}
			items[id] = entry
		}
		obj(ledger["meta"])["count"] = len(items)
		if game == "conexiuni" {
			obj(ledger["meta"])["group_count"] = 4 * len(items)
		}
		b, e := render(ledger)
		if e != nil {
			return nil, e
		}
		changes[ledgerPath(s.Root, game)] = b
	}
	if e = s.validateProspective(changes); e != nil {
		return nil, e
	}
	if write {
		e = s.commit(changes, func() error {
			if e := s.validateCurrent(); e != nil {
				return e
			}
			for _, game := range []string{"conexiuni", "lant"} {
				if _, e := loadLedger(s.Root, game); e != nil {
					return e
				}
			}
			return nil
		})
	}
	return Object{"applied": stats, "input_ids": ids, "source_pack_sha256": digest(s.PackBytes), "write": write}, e
}

func (s *Sources) bindDossiers(dir string, ids []string) error {
	for _, id := range ids {
		if !safeID(id) {
			return errors.New("unsafe dossier identifier refused")
		}
		if e := s.bindInput(filepath.Join(dir, id+".json")); e != nil {
			return e
		}
	}
	return nil
}
