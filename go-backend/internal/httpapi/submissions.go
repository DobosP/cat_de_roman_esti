package httpapi

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"io"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

type submissionBudget struct{ hits []time.Time }
type submissionQueue struct {
	mu      sync.Mutex
	budgets map[string]submissionBudget
}

func stringsList(value any) ([]string, bool) {
	values, ok := value.([]any)
	if !ok {
		return nil, false
	}
	result := make([]string, len(values))
	for i, v := range values {
		var ok bool
		result[i], ok = v.(string)
		if !ok {
			return nil, false
		}
	}
	return result, true
}
func (s *Server) validateSubmission(game, category, difficulty string, payload map[string]any) []string {
	g := graph.New(s.content)
	if s.content.CategoryLabels[category] == "" {
		return []string{"unknown category"}
	}
	if difficulty != "usor" && difficulty != "normal" && difficulty != "greu" {
		return []string{"unsupported difficulty"}
	}
	switch game {
	case "conexiuni":
		groups, ok := payload["groups"].(map[string]any)
		if !ok || len(groups) != 4 {
			return []string{"groups must contain exactly four groups"}
		}
		labels, ok := payload["group_labels"].(map[string]any)
		if !ok || len(labels) != 4 {
			return []string{"group_labels must match groups"}
		}
		seen := map[string]bool{}
		all := []string{}
		for key, v := range groups {
			ids, ok := stringsList(v)
			if !ok || len(ids) != 4 {
				return []string{"every group needs four node ids"}
			}
			label, ok := labels[key].(string)
			if !ok || strings.TrimSpace(label) == "" {
				return []string{"every group needs a label"}
			}
			for _, id := range ids {
				if !g.Exists(id) || seen[id] {
					return []string{"tiles must be unique known node ids"}
				}
				seen[id] = true
				all = append(all, id)
			}
		}
		order, ok := stringsList(payload["order"])
		if !ok || len(order) != 16 {
			return []string{"order must be a permutation of the board"}
		}
		sort.Strings(all)
		sort.Strings(order)
		for i := range all {
			if all[i] != order[i] {
				return []string{"order must be a permutation of the board"}
			}
		}
	case "contexto":
		target, ok := payload["target"].(string)
		if !ok || !g.Exists(target) {
			return []string{"unknown target node"}
		}
		distances := g.DistancesTo(target)
		responsive := 0
		for _, d := range distances {
			if d >= 1 && d <= 5 {
				responsive++
			}
		}
		if len(distances) < 120 || responsive < 40 {
			return []string{"target lacks the required reachable and responsive zones"}
		}
	case "lant":
		start, ok := payload["start"].(string)
		if !ok || !g.Exists(start) {
			return []string{"unknown start node"}
		}
		target, ok := payload["target"].(string)
		if !ok || !g.Exists(target) || start == target {
			return []string{"target must be a different known node"}
		}
		distance, exists := g.Distance(start, target)
		if !exists {
			return []string{"target is unreachable"}
		}
		optimal, ok := payload["optimal"].(float64)
		if !ok || optimal != float64(distance) {
			return []string{"optimal must equal the actual BFS distance"}
		}
		bands := map[string][2]int{"usor": {2, 3}, "normal": {3, 4}, "greu": {4, 6}}
		band := bands[difficulty]
		if distance < band[0] || distance > band[1] {
			return []string{"route length is outside the difficulty band"}
		}
		from, to := g.DistancesFrom(start), g.DistancesTo(target)
		widths := make([]int, distance+1)
		for id, d := range from {
			other, ok := to[id]
			if ok && d+other == distance {
				widths[d]++
			}
		}
		for _, width := range widths[1:distance] {
			if width < 2 {
				return []string{"shortest path layers need two choices"}
			}
		}
	case "alchimie":
		seeds, ok := stringsList(payload["seeds"])
		if !ok {
			return []string{"seeds must be node ids"}
		}
		target, ok := payload["target"].(string)
		if !ok {
			return []string{"target must be a node id"}
		}
		depth, ok := payload["target_depth"].(float64)
		if !ok || depth != float64(int(depth)) {
			return []string{"target_depth must be an integer"}
		}
		return s.alchimie.ValidateProposal(seeds, target, category, int(depth))
	default:
		return []string{"unknown game"}
	}
	return nil
}
func (s *Server) submit(w http.ResponseWriter, r *http.Request) {
	dir := os.Getenv("CAT_SUBMISSIONS_DIR")
	if dir == "" {
		write(w, r, 503, map[string]any{"detail": "Trimiterea de jocuri nu este activata pe acest server."})
		return
	}
	var body struct {
		Game       string         `json:"game"`
		Category   string         `json:"category"`
		Difficulty string         `json:"difficulty"`
		Payload    map[string]any `json:"payload"`
		Author     *string        `json:"author"`
	}
	r.Body = http.MaxBytesReader(w, r.Body, MaxRequestBytes)
	decoder := json.NewDecoder(r.Body)
	if decoder.Decode(&body) != nil || decoder.Decode(new(any)) != io.EOF {
		write(w, r, 422, map[string]any{"detail": "Propunere invalidă."})
		return
	}
	client, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		client = "unknown"
	}
	now := time.Now()
	s.submissions.mu.Lock()
	defer s.submissions.mu.Unlock()
	if s.submissions.budgets == nil {
		s.submissions.budgets = map[string]submissionBudget{}
	}
	for key, b := range s.submissions.budgets {
		if len(b.hits) == 0 || now.Sub(b.hits[len(b.hits)-1]) >= time.Hour {
			delete(s.submissions.budgets, key)
		}
	}
	b := s.submissions.budgets[client]
	hits := []time.Time{}
	for _, at := range b.hits {
		if now.Sub(at) < time.Hour {
			hits = append(hits, at)
		}
	}
	if len(hits) >= 10 || (len(s.submissions.budgets) >= 4096 && len(hits) == 0) {
		write(w, r, 429, map[string]any{"detail": "Prea multe propuneri; încearcă mai târziu."})
		return
	}
	s.submissions.budgets[client] = submissionBudget{append(hits, now)}
	fields := map[string][]string{"conexiuni": {"groups", "group_labels", "order"}, "contexto": {"target"}, "lant": {"start", "target", "optimal"}, "alchimie": {"seeds", "target", "target_depth"}}
	payload := map[string]any{}
	for _, field := range fields[body.Game] {
		if v, ok := body.Payload[field]; ok {
			payload[field] = v
		}
	}
	if errors := s.validateSubmission(body.Game, body.Category, body.Difficulty, payload); len(errors) > 0 {
		write(w, r, 400, map[string]any{"detail": "Propunere invalidă: " + strings.Join(errors, "; ")})
		return
	}
	var random [6]byte
	if _, err = rand.Read(random[:]); err != nil {
		write(w, r, 503, map[string]any{"detail": "Propunerea nu a putut fi salvată."})
		return
	}
	id := "sub_" + hex.EncodeToString(random[:])
	payload["id"] = id
	payload["category"] = body.Category
	payload["difficulty"] = body.Difficulty
	payload["source"] = "user"
	payload["status"] = "pending"
	var author any
	if body.Author != nil {
		clean := strings.TrimFunc(*body.Author, pySpace)
		runes := []rune(clean)
		if len(runes) > 80 {
			runes = runes[:80]
		}
		if len(runes) > 0 {
			author = string(runes)
		}
	}
	line, err := json.Marshal(map[string]any{"game": body.Game, "author": author, "item": payload})
	if err != nil {
		write(w, r, 503, map[string]any{"detail": "Propunerea nu a putut fi salvată."})
		return
	}
	if err = os.MkdirAll(dir, 0700); err != nil {
		write(w, r, 503, map[string]any{"detail": "Propunerea nu a putut fi salvată."})
		return
	}
	root, err := os.OpenRoot(filepath.Clean(dir))
	if err != nil {
		write(w, r, 503, map[string]any{"detail": "Propunerea nu a putut fi salvată."})
		return
	}
	defer root.Close()
	if info, err := root.Lstat("submissions.jsonl"); err == nil && !info.Mode().IsRegular() {
		write(w, r, 503, map[string]any{"detail": "Propunerea nu a putut fi salvată."})
		return
	}
	file, err := root.OpenFile("submissions.jsonl", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		write(w, r, 503, map[string]any{"detail": "Propunerea nu a putut fi salvată."})
		return
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Size()+int64(len(line))+1 > 32<<20 {
		write(w, r, 503, map[string]any{"detail": "Coada de propuneri este plină."})
		return
	}
	if _, err = file.Write(append(line, '\n')); err != nil {
		write(w, r, 503, map[string]any{"detail": "Propunerea nu a putut fi salvată."})
		return
	}
	write(w, r, 202, map[string]any{"ok": true, "id": id, "status": "pending", "message": "Multumim! Jocul tau intra in validare inainte de publicare."})
}
