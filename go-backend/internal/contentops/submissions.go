package contentops

import (
	"bytes"
	"errors"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"io"
	"os"
	"path/filepath"
	"strings"
)

func readQueue(path string) ([]Object, []byte, error) {
	f, e := os.Open(path)
	if os.IsNotExist(e) {
		return []Object{}, []byte{}, nil
	}
	if e != nil {
		return nil, nil, e
	}
	defer f.Close()
	blob, e := io.ReadAll(io.LimitReader(f, MaxDocumentBytes+1))
	if e != nil {
		return nil, nil, e
	}
	if len(blob) > MaxDocumentBytes {
		return nil, nil, errors.New("submission queue exceeds 32 MiB bound")
	}
	rows := []Object{}
	seen := map[string]bool{}
	for _, line := range bytes.Split(blob, []byte("\n")) {
		if len(bytes.TrimSpace(line)) == 0 {
			continue
		}
		r, e := Decode(line)
		if e != nil {
			return nil, nil, e
		}
		id := str(obj(r["item"])["id"])
		if !safeID(id) || seen[id] || !gameKnown(str(r["game"])) {
			return nil, nil, errors.New("submission queue identity duplicate or unknown game")
		}
		seen[id] = true
		rows = append(rows, r)
		if len(rows) > MaxRecords {
			return nil, nil, errors.New("submission queue exceeds record bound")
		}
	}
	return rows, blob, nil
}
func renderQueue(rows []Object) ([]byte, error) {
	var b bytes.Buffer
	for _, r := range rows {
		blob, e := render(r)
		if e != nil {
			return nil, e
		}
		b.Write(bytes.ReplaceAll(bytes.TrimSpace(blob), []byte("\n"), []byte(" ")))
		b.WriteByte('\n')
	}
	return b.Bytes(), nil
}

// Submissions are always offline and reviewed. "stage" reserves pending stock
// while leaving the queue intact. "promote" requires the complete review directory
// and atomically removes queue rows only when the same pending stock is approved.
func (s *Sources) Submissions(command, dir string, ids []string, reviewDir string, write bool) (Object, error) {
	dir, e := filepath.Abs(dir)
	if e != nil {
		return nil, e
	}
	path := filepath.Join(dir, "submissions.jsonl")
	for _, p := range []string{path, filepath.Join(dir, "submissions-rejected.jsonl")} {
		if e = s.bindInput(p); e != nil {
			return nil, e
		}
	}
	queue, _, e := readQueue(path)
	if e != nil {
		return nil, e
	}
	selected := map[string]bool{}
	for _, id := range ids {
		if id == "" || selected[id] {
			return nil, errors.New("submission ids must be nonempty and unique")
		}
		selected[id] = true
	}
	if command == "list" {
		out := []Object{}
		for _, entry := range queue {
			r := obj(entry["item"])
			errors := append(contentbuild.ValidateEnvelope(str(entry["game"]), r), contentbuild.ValidatePayload(s.Graph, str(entry["game"]), r)...)
			out = append(out, Object{"validation_errors": errors, "id": r["id"], "game": entry["game"], "category": r["category"], "difficulty": r["difficulty"], "status": r["status"]})
		}
		return Object{"entries": out, "count": len(out)}, nil
	}
	if len(ids) == 0 {
		return nil, errors.New("submission mutation requires exact ids")
	}
	chosen, remaining := []Object{}, []Object{}
	for _, entry := range queue {
		if selected[str(obj(entry["item"])["id"])] {
			chosen = append(chosen, entry)
		} else {
			remaining = append(remaining, entry)
		}
	}
	if len(chosen) != len(ids) {
		return nil, errors.New("one or more requested submission ids absent from queue")
	}
	rows, games, e := indexPack(s.Pack)
	if e != nil {
		return nil, e
	}
	changes := map[string][]byte{}
	switch command {
	case "reject":
		for _, entry := range chosen {
			if rows[str(obj(entry["item"])["id"])] != nil {
				return nil, errors.New("staged stock rejection requires independently bound apply-review; queue-only reject refused")
			}
		}
		rejectedPath := filepath.Join(dir, "submissions-rejected.jsonl")
		rejected, _, e := readQueue(rejectedPath)
		if e != nil {
			return nil, e
		}
		existing := map[string]bool{}
		for _, r := range rejected {
			existing[str(obj(r["item"])["id"])] = true
		}
		for _, entry := range chosen {
			if existing[str(obj(entry["item"])["id"])] {
				return nil, errors.New("submission already appears in rejection audit trail")
			}
			rejected = append(rejected, entry)
		}
		blob, e := renderQueue(rejected)
		if e != nil {
			return nil, e
		}
		changes[rejectedPath] = blob
		blob, e = renderQueue(remaining)
		if e != nil {
			return nil, e
		}
		changes[path] = blob
	case "stage":
		rejected, _, err := readQueue(filepath.Join(dir, "submissions-rejected.jsonl"))
		if err != nil {
			return nil, err
		}
		retired := map[string]bool{}
		for _, r := range append(append([]Object{}, s.Rejections...), s.LantRejections...) {
			retired[str(r["id"])] = true
		}
		for _, entry := range rejected {
			retired[str(obj(entry["item"])["id"])] = true
		}
		for _, entry := range chosen {
			game := str(entry["game"])
			r := copyObject(obj(entry["item"]))
			id := str(r["id"])
			if retired[id] {
				return nil, errors.New("submission ID already retired by rejection evidence")
			}
			r["source"] = "user"
			r["status"] = "pending"
			errs := append(contentbuild.ValidateEnvelope(game, r), contentbuild.ValidatePayload(s.Graph, game, r)...)
			if len(errs) > 0 {
				return nil, fmt.Errorf("invalid submission %s: %s", id, strings.Join(errs, "; "))
			}
			if old := rows[id]; old != nil {
				if games[id] != game || !bytes.Equal(canonical(old), canonical(r)) {
					return nil, errors.New("submission collides with current stock")
				}
				continue
			}
			s.Pack[game] = append(array(s.Pack[game]), r)
		}
		refreshCounts(s.Pack)
		obj(s.Pack["meta"])["id_high_water"] = highWater(s.Pack)
		changes, e = packChanges(s.Root, s.Pack)
		if e != nil {
			return nil, e
		}
		if e = s.validateProspective(changes); e != nil {
			return nil, e
		}
	case "promote":
		if reviewDir == "" {
			return nil, errors.New("submission promotion requires --reviews with independently bound gate artifacts; stage first")
		}
		for _, entry := range chosen {
			game := str(entry["game"])
			r := copyObject(obj(entry["item"]))
			id := str(r["id"])
			r["source"] = "user"
			r["status"] = "pending"
			if rows[id] == nil || games[id] != game || !bytes.Equal(canonical(rows[id]), canonical(r)) {
				return nil, errors.New("submission must first be staged unchanged as pending")
			}
		}
		analyst, _, e := readReview(filepath.Join(reviewDir, "reviews/analyst.json"), "analyst")
		if e != nil {
			return nil, e
		}
		batch, _ := uniqueStrings(analyst["input_ids"])
		if len(batch) != len(ids) {
			return nil, errors.New("submission promotion batch must exactly cover selected ids")
		}
		for _, id := range batch {
			if !selected[id] {
				return nil, errors.New("submission promotion batch contains an unselected id")
			}
		}
		verifier, _, e := readReview(filepath.Join(reviewDir, "reviews/verifier.json"), "verifier")
		if e != nil {
			return nil, e
		}
		ai, vi := indexReview(analyst), indexReview(verifier)
		for _, id := range ids {
			if gateVerdict(str(ai[id]["verdict"]), str(vi[id]["verdict"])) != "promote" {
				return nil, errors.New("submission promote requires unanimous promotion for every selected id")
			}
		}
		blob, e := renderQueue(remaining)
		if e != nil {
			return nil, e
		}
		return s.applyReview(reviewDir, write, map[string][]byte{path: blob})
	default:
		return nil, fmt.Errorf("unknown submissions command %s", command)
	}
	if write {
		verify := func() error {
			if command == "stage" {
				return s.validateCurrent()
			}
			_, _, e := readQueue(path)
			if e != nil {
				return e
			}
			_, _, e = readQueue(filepath.Join(dir, "submissions-rejected.jsonl"))
			return e
		}
		if e = s.commit(changes, verify); e != nil {
			return nil, e
		}
	}
	return Object{"command": command, "ids": ids, "write": write, "status": strings.ToUpper(command)}, nil
}
