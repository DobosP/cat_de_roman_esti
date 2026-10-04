package contentops

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

var inventoryFiles = map[string]string{"kg": fixtures + "kg_sample.json", "pack": fixtures + "games_pack.json", "derived": fixtures + "derived_catalog_v38.json", "quick": fixtures + "quick_games_v92.json", "rankings": fixtures + "board_rankings_v37.json"}

func boundedGit(root string, args ...string) ([]byte, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, "git", append([]string{"-C", root}, args...)...)
	var out limitedBuffer
	out.limit = MaxDocumentBytes
	cmd.Stdout = &out
	var stderr limitedBuffer
	stderr.limit = 4096
	cmd.Stderr = &stderr
	if e := cmd.Run(); e != nil {
		return nil, fmt.Errorf("Git command failed: %w (%s)", e, stderr.String())
	}
	return out.Bytes(), nil
}

type limitedBuffer struct {
	bytes.Buffer
	limit int
}

func (b *limitedBuffer) Write(p []byte) (int, error) {
	if b.Len()+len(p) > b.limit {
		return 0, errors.New("command output exceeds bound")
	}
	return b.Buffer.Write(p)
}
func documents(root, commit string) (map[string]Object, error) {
	out := map[string]Object{}
	for name, path := range inventoryFiles {
		var b []byte
		var e error
		if commit != "" {
			if name != "kg" && name != "pack" {
				present, err := boundedGit(root, "ls-tree", "--name-only", commit, "--", path)
				if err != nil {
					return nil, err
				}
				if len(bytes.TrimSpace(present)) == 0 {
					continue
				}
			}
			b, e = boundedGit(root, "show", commit+":"+path)
		} else {
			b, e = os.ReadFile(filepath.Join(root, path))
		}
		if e != nil {
			if commit == "" && os.IsNotExist(e) && name != "kg" && name != "pack" {
				continue
			}
			return nil, e
		}
		m, e := Decode(b)
		if e != nil {
			return nil, e
		}
		out[name] = m
	}
	return out, nil
}
func indexRows(v any, label string) (Object, error) {
	a, ok := v.([]any)
	if !ok {
		return nil, fmt.Errorf("%s must be an array", label)
	}
	out := Object{}
	for _, v := range a {
		r := obj(v)
		id := str(r["id"])
		if r == nil || id == "" || out[id] != nil {
			return nil, fmt.Errorf("%s empty/duplicate id", label)
		}
		out[id] = r
	}
	return out, nil
}
func inventory(docs map[string]Object) (Object, error) {
	kg, pack := docs["kg"], docs["pack"]
	if kg == nil || pack == nil {
		return nil, errors.New("KG and pack inventory required")
	}
	nodes, e := indexRows(kg["kg_nodes"], "nodes")
	if e != nil {
		return nil, e
	}
	concepts, forms := Object{}, Object{}
	for id, v := range nodes {
		r := obj(v)
		c := copyObject(r)
		delete(c, "aliases")
		concepts[id] = c
		rawAliases, exists := r["aliases"]
		if !exists {
			rawAliases = []any{}
		}
		aliases, ok := rawAliases.([]any)
		if !ok {
			return nil, errors.New("aliases must be array")
		}
		for _, v := range aliases {
			form, ok := v.(string)
			if !ok {
				return nil, errors.New("alias must be string")
			}
			key := string(canonical([]string{id, form}))
			if _, ok = forms[key]; ok {
				return nil, errors.New("duplicate alias form")
			}
			forms[key] = form
		}
	}
	edges, e := indexRows(kg["kg_edges"], "edges")
	if e != nil {
		return nil, e
	}
	puzzles, e := indexRows(kg["kg_puzzles"], "puzzles")
	if e != nil {
		return nil, e
	}
	boards := Object{}
	for _, name := range []string{"derived", "quick"} {
		if docs[name] == nil {
			continue
		}
		rows, e := indexRows(docs[name]["boards"], name)
		if e != nil {
			return nil, e
		}
		for id, v := range rows {
			if boards[id] != nil {
				return nil, errors.New("derived/quick id collision")
			}
			game := str(obj(v)["game"])
			if game != "intrusul" && game != "perechi" {
				return nil, errors.New("unknown derived game")
			}
			boards[id] = v
		}
	}
	var rankings Object
	if docs["rankings"] != nil {
		rankings, e = indexRows(docs["rankings"]["boards"], "rankings")
		if e != nil {
			return nil, e
		}
	}
	packInventory, derived := Object{}, Object{}
	seen := map[string]bool{}
	for _, game := range Games {
		rows, e := indexRows(pack[game], game)
		if e != nil {
			return nil, e
		}
		approved := Object{}
		var eligible Object
		if rankings != nil {
			eligible = Object{}
		}
		for id, v := range rows {
			if seen[id] {
				return nil, errors.New("pack ids duplicate across games")
			}
			seen[id] = true
			r := obj(v)
			if str(r["status"]) == "approved" {
				approved[id] = true
			}
			if rankings != nil {
				rank := obj(rankings[id])
				b, ok := rank["pilot_eligible"].(bool)
				if rank == nil || str(rank["game"]) != game || str(rank["status"]) != str(r["status"]) || !ok {
					return nil, fmt.Errorf("ranking identity/eligibility mismatch %s", id)
				}
				if b {
					if approved[id] == nil {
						return nil, errors.New("nonapproved eligible ranking")
					}
					eligible[id] = true
				}
			}
		}
		packInventory[game] = Object{"records": rows, "approved": approved, "declared_ranked_eligible": eligible}
	}
	if rankings != nil && len(rankings) != len(seen) {
		return nil, errors.New("ranking coverage mismatch")
	}
	for _, game := range []string{"intrusul", "perechi"} {
		rows := Object{}
		for id, v := range boards {
			if str(obj(v)["game"]) == game {
				rows[id] = v
			}
		}
		derived[game] = rows
	}
	return Object{"concepts": concepts, "forms": forms, "connections": edges, "puzzles": puzzles, "pack": packInventory, "derived": derived}, nil
}
func recordDelta(a, b Object) Object {
	added, removed, changed := []string{}, []string{}, []string{}
	retained := 0
	for id, v := range a {
		other, ok := b[id]
		if !ok {
			removed = append(removed, id)
		} else {
			retained++
			if !bytes.Equal(canonical(v), canonical(other)) {
				changed = append(changed, id)
			}
		}
	}
	for id := range b {
		if _, ok := a[id]; !ok {
			added = append(added, id)
		}
	}
	sort.Strings(added)
	sort.Strings(removed)
	sort.Strings(changed)
	return Object{"before_count": len(a), "after_count": len(b), "added_count": len(added), "removed_count": len(removed), "changed_count": len(changed), "retained_count": retained, "unchanged_count": retained - len(changed), "all_baseline_ids_retained": len(removed) == 0, "all_baseline_records_unchanged": len(removed) == 0 && len(changed) == 0, "added_ids": added, "removed_ids": removed, "changed_ids": changed}
}
func Delta(root, baseline string) (Object, error) {
	if baseline == "" || strings.HasPrefix(baseline, "-") || strings.ContainsRune(baseline, 0) {
		return nil, errors.New("baseline must be a Git ref, not an option")
	}
	commit, e := boundedGit(root, "rev-parse", "--verify", "--end-of-options", baseline+"^{commit}")
	if e != nil {
		return nil, e
	}
	ref := strings.TrimSpace(string(commit))
	if len(ref) != 40 && len(ref) != 64 {
		return nil, errors.New("invalid Git object id")
	}
	before, e := documents(root, ref)
	if e != nil {
		return nil, e
	}
	after, e := documents(root, "")
	if e != nil {
		return nil, e
	}
	a, e := inventory(before)
	if e != nil {
		return nil, e
	}
	b, e := inventory(after)
	if e != nil {
		return nil, e
	}
	result := Object{}
	for _, key := range []string{"concepts", "forms", "connections", "puzzles"} {
		result[key] = recordDelta(obj(a[key]), obj(b[key]))
	}
	p, d := Object{}, Object{}
	for _, game := range Games {
		g := Object{}
		for _, key := range []string{"records", "approved", "declared_ranked_eligible"} {
			old, new := obj(obj(obj(a["pack"])[game])[key]), obj(obj(obj(b["pack"])[game])[key])
			if old == nil || new == nil {
				g[key] = nil
			} else {
				g[key] = recordDelta(old, new)
			}
		}
		p[game] = g
	}
	for _, game := range []string{"intrusul", "perechi"} {
		d[game] = recordDelta(obj(obj(a["derived"])[game]), obj(obj(b["derived"])[game]))
	}
	result["pack"] = p
	result["derived"] = d
	forms := obj(result["forms"])
	for _, key := range []string{"added_ids", "removed_ids", "changed_ids"} {
		pairs := [][]string{}
		for _, id := range array(forms[key]) {
			var pair []string
			if e := json.Unmarshal([]byte(str(id)), &pair); e != nil {
				return nil, e
			}
			pairs = append(pairs, pair)
		}
		sort.Slice(pairs, func(i, j int) bool {
			if pairs[i][0] != pairs[j][0] {
				return pairs[i][0] < pairs[j][0]
			}
			return pairs[i][1] < pairs[j][1]
		})
		forms[key] = pairs
	}
	result["schema_version"] = 1
	result["baseline_ref"] = baseline
	result["baseline_commit"] = ref
	result["comparison"] = "working_tree"
	result["synonyms"] = Object{"count": nil, "reason": "Alias data does not classify true synonyms."}
	result["notes"] = []string{"Forms are exact [node_id, form] pairs, not necessarily new concepts or synonyms.", "Concept changes exclude aliases; other record fields are compared exactly.", "Approved additions include new records and promotions of existing records.", "Ranked eligibility is declared by the sidecar; run content/runtime gates separately.", "Missing historical derived catalogs count as zero; missing rankings are unknown.", "Quick-game boards include the frozen V38 catalog and reviewed authored supplements."}
	return result, nil
}

func DeltaText(report Object) string {
	lines := []string{"Content delta: " + str(report["baseline_commit"]) + " -> working tree"}
	line := func(label string, d Object) {
		if d == nil {
			lines = append(lines, label+": unavailable (ranking sidecar missing in one snapshot)")
			return
		}
		lines = append(lines, fmt.Sprintf("%s: %d -> %d; +%d -%d changed %d; unchanged %d", label, integer(d["before_count"]), integer(d["after_count"]), integer(d["added_count"]), integer(d["removed_count"]), integer(d["changed_count"]), integer(d["unchanged_count"])))
	}
	for _, key := range []string{"concepts", "connections", "forms", "puzzles"} {
		line(key, obj(report[key]))
	}
	for _, game := range Games {
		for _, key := range []string{"records", "approved", "declared_ranked_eligible"} {
			line(game+" "+key, obj(obj(obj(report["pack"])[game])[key]))
		}
	}
	for _, game := range []string{"intrusul", "perechi"} {
		line(game+" catalog boards", obj(obj(report["derived"])[game]))
	}
	notes, _ := stringsOf(report["notes"])
	lines = append(lines, notes...)
	return strings.Join(lines, "\n")
}
