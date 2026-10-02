package httpapi

import (
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contexto"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/gameapi"
	"net/http"
	"strings"
)

func (s *Server) arcade(w http.ResponseWriter, r *http.Request) bool {
	if r.URL.Path == "/api/alchimie/explore" {
		return s.explore(w, r, nil)
	}
	if strings.HasPrefix(r.URL.Path, "/api/alchimie/explore/") {
		return s.explore(w, r, strings.Split(strings.TrimPrefix(r.URL.Path, "/api/alchimie/explore/"), "/"))
	}
	if !strings.HasPrefix(r.URL.Path, "/api/wordgames/") {
		return false
	}
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/api/wordgames/"), "/")
	if len(parts) < 2 {
		return false
	}
	game := parts[0]
	known := map[string]bool{"perechi": true, "conexiuni": true, "contexto": true, "lant": true, "alchimie": true}
	if !known[game] {
		return false
	}
	var body map[string]any
	var e *gameapi.Error
	done := func() {
		if e != nil {
			write(w, r, e.Status, map[string]any{"detail": e.Detail})
		} else {
			write(w, r, 200, body)
		}
	}
	badmethod := func() { write(w, r, 405, map[string]any{"detail": "Method Not Allowed"}) }
	if parts[1] != "games" || len(parts) > 4 {
		write(w, r, 404, map[string]any{"detail": "Not Found"})
		return true
	}
	if len(parts) == 2 {
		if r.Method != "POST" {
			badmethod()
			return true
		}
		q := queryValues(r.URL.RawQuery)
		seed, f := queryInt(q, "seed")
		if f != nil {
			write(w, r, 422, f)
			return true
		}
		starter, f := queryInt(q, "starter")
		if game == "perechi" && f != nil {
			write(w, r, 422, f)
			return true
		}
		category := last(q, "category")
		if q.Has("category") && s.content.CategoryLabels[category] == "" {
			write(w, r, 400, map[string]any{"detail": "Categorie necunoscută."})
			return true
		}
		daily := last(q, "daily")
		var dailyPtr *string
		if q.Has("daily") {
			dailyPtr = &daily
		}
		difficulty := last(q, "difficulty")
		if !q.Has("difficulty") {
			difficulty = "normal"
		}
		switch game {
		case "perechi":
			if starter != nil && starter.Sign() != 0 && starter.String() != "1" {
				write(w, r, 400, map[string]any{"detail": "starter trebuie să fie 0 sau 1."})
				return true
			}
			body, e = s.perechi.Create(seed, daily, category, last(q, "previous_game_id"), starter != nil && starter.Sign() != 0)
		case "conexiuni":
			body, e = s.conexiuni.Create(seed, daily, category, difficulty)
		case "contexto":
			body, e = s.contexto.Create(seed, difficulty, dailyPtr, category)
		case "lant":
			body, e = s.lant.Create(seed, difficulty, dailyPtr, category)
		case "alchimie":
			body, e = s.alchimie.Create(seed, daily, category, difficulty)
		}
		done()
		return true
	}
	id := parts[2]
	if id == "" {
		write(w, r, 404, map[string]any{"detail": "Not Found"})
		return true
	}
	if len(parts) == 3 {
		if r.Method != "GET" && r.Method != "HEAD" {
			badmethod()
			return true
		}
		switch game {
		case "perechi":
			body, e = s.perechi.Get(id)
		case "conexiuni":
			body, e = s.conexiuni.Get(id)
		case "contexto":
			body, e = s.contexto.Get(id)
		case "lant":
			body, e = s.lant.Get(id)
		case "alchimie":
			body, e = s.alchimie.Get(id)
		}
		done()
		return true
	}
	op := parts[3]
	allowed := map[string]map[string]bool{"perechi": {"match": true, "hint": true}, "conexiuni": {"guess": true, "clue": true}, "contexto": {"guess": true, "clue": true, "giveup": true}, "lant": {"move": true, "hint": true, "undo": true}, "alchimie": {"combine": true, "hint": true, "reset": true}}
	if !allowed[game][op] {
		write(w, r, 404, map[string]any{"detail": "Not Found"})
		return true
	}
	if r.Method != "POST" {
		badmethod()
		return true
	}
	switch game {
	case "perechi":
		if op == "hint" {
			body, e = s.perechi.Hint(id)
		} else {
			body, e = s.perechi.MatchInput(id, func() ([]string, *gameapi.Error) { return idsBody(r, "MatchBody") })
		}
	case "conexiuni":
		if op == "clue" {
			body, e = s.conexiuni.Clue(id)
		} else {
			body, e = s.conexiuni.GuessInput(id, func() ([]string, *gameapi.Error) { return idsBody(r, "GuessBody") })
		}
	case "contexto":
		switch op {
		case "clue":
			body, e = s.contexto.Clue(id)
		case "giveup":
			body, e = s.contexto.GiveUp(id)
		case "guess":
			body, e = s.contexto.GuessInput(id, func() (contexto.GuessBody, *gameapi.Error) {
				obj, err := fields(r, "GuessBody", []fieldRule{{Name: "text", Kind: "string"}, {Name: "confirm", Kind: "string", Optional: true, Nullable: true}}, false)
				if err != nil {
					return contexto.GuessBody{}, err
				}
				return contexto.GuessBody{Text: stringField(obj, "text"), Confirm: optionalString(obj, "confirm")}, nil
			})
		}
	case "lant":
		switch op {
		case "hint":
			body, e = s.lant.Hint(id)
		case "undo":
			body, e = s.lant.Undo(id)
		case "move":
			body, e = s.lant.MoveInput(id, func() (string, *gameapi.Error) { return textBody(r) })
		}
	case "alchimie":
		switch op {
		case "hint":
			body, e = s.alchimie.Hint(id)
		case "reset":
			body, e = s.alchimie.Reset(id)
		case "combine":
			body, e = s.alchimie.CombineInput(id, func() (string, string, *gameapi.Error) { return pairBody(r, false) })
		}
	}
	done()
	return true
}

func (s *Server) explore(w http.ResponseWriter, r *http.Request, parts []string) bool {
	var body map[string]any
	var e *gameapi.Error
	done := func() {
		if e != nil {
			write(w, r, e.Status, map[string]any{"detail": e.Detail})
		} else {
			write(w, r, 200, body)
		}
	}
	badmethod := func() { write(w, r, 405, map[string]any{"detail": "Method Not Allowed"}) }
	if len(parts) == 0 {
		if r.Method != "POST" {
			badmethod()
			return true
		}
		progress, goal, err := exploreCreateBody(r)
		if err != nil {
			e = err
			done()
			return true
		}
		body, e = s.explorer.Create(progress, goal)
		done()
		return true
	}
	id := parts[0]
	if id == "" || len(parts) > 2 {
		write(w, r, 404, map[string]any{"detail": "Not Found"})
		return true
	}
	if len(parts) == 1 {
		if r.Method != "GET" && r.Method != "HEAD" {
			badmethod()
			return true
		}
		body, e = s.explorer.Get(id)
		done()
		return true
	}
	if !map[string]bool{"combine": true, "hint": true, "goal": true}[parts[1]] {
		write(w, r, 404, map[string]any{"detail": "Not Found"})
		return true
	}
	if r.Method != "POST" {
		badmethod()
		return true
	}
	switch parts[1] {
	case "hint":
		body, e = s.explorer.Hint(id)
	case "combine":
		body, e = s.explorer.CombineInput(id, func() (string, string, *gameapi.Error) { return pairBody(r, true) })
	case "goal":
		body, e = s.explorer.GoalInput(id, func() (*string, *gameapi.Error) { return goalBody(r) })
	}
	done()
	return true
}
