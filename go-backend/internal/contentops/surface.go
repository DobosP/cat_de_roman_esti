package contentops

import (
	"regexp"
	"strings"
)

type surfaceRule struct{ kind, value string }

func parseSurface(label string) *surfaceRule {
	s := normalizedPhrase(label)
	for _, row := range []surfaceRule{{"punctuation", "-"}, {"punctuation", "!"}, {"year", ""}, {"digit", ""}, {"one_word", ""}, {"uppercase_length", "3"}, {"same_person_initial", ""}, {"word_count", "3"}, {"first_name_length", "4"}} {
		hit := false
		switch row.kind {
		case "punctuation":
			if row.value == "-" {
				hit = strings.Contains(s, "contine o cratima")
			} else {
				hit = strings.Contains(s, "contine semnul exclamarii")
			}
		case "year":
			hit = strings.Contains(s, "cu anul in denumire")
		case "digit":
			hit = strings.Contains(s, "cu cifra in nume") || strings.Contains(s, "cu o cifra in nume")
		case "one_word":
			hit = strings.Contains(s, "dintr-un singur cuvant") || strings.Contains(s, "dintr un singur cuvant")
		case "uppercase_length":
			hit = regexp.MustCompile(`exact (trei|3) litere majuscule`).MatchString(s)
		case "same_person_initial":
			hit = strings.Contains(s, "aceeasi initiala la prenume si nume")
		case "word_count":
			hit = regexp.MustCompile(`numele afisat are exact (trei|3) cuvinte`).MatchString(s)
		case "first_name_length":
			hit = regexp.MustCompile(`prenume(le)? (din|are) exact (patru|4) litere`).MatchString(s)
		}
		if hit {
			return &row
		}
	}
	rows := []struct{ kind, pattern string }{{"prefix", `(?:primul cuvant al numelui|prenume(?:le)? care) (?:incep|incepe) cu(?: litera)? ([a-z])(?:\b|$)`}, {"prefix", `(?:incep|incepe) cu(?: litera| sirul)? [„"']?([a-z]+)[”"']?(?: sau [a-z])?(?:\b|$)`}, {"suffix", `se termina (?:in|cu)(?: litera)? [„"']?-?([a-z]+)[”"']?\s*$`}, {"contains", `contine sirul de litere ([a-z]{2,})\s*$`}, {"contains", `cu ([a-z]{3,}) in denumire\s*$`}, {"contains_word", `au cuvantul [„"']?([a-z]{2,})[”"']? in denumire\s*$`}, {"first_name", `(?:cu )?prenumele ([a-z]+)\s*$`}, {"last_name_prefix", `nume de familie care (?:incep|incepe) cu ([a-z])\s*$`}}
	for _, row := range rows {
		m := regexp.MustCompile(row.pattern).FindStringSubmatch(s)
		if len(m) > 1 {
			return &surfaceRule{row.kind, m[1]}
		}
	}
	return nil
}
func matchesSurface(rule *surfaceRule, raw string) bool {
	folded := normalizedPhrase(raw)
	words := regexp.MustCompile(`[a-z0-9]+`).FindAllString(folded, -1)
	switch rule.kind {
	case "punctuation":
		return strings.Contains(raw, rule.value)
	case "year":
		return regexp.MustCompile(`\b[0-9]{4}\b`).MatchString(raw)
	case "digit":
		return regexp.MustCompile(`[0-9]`).MatchString(raw)
	case "one_word":
		return len(words) == 1
	case "uppercase_length":
		return regexp.MustCompile(`^[A-ZĂÂÎȘȚŞŢ]{3}$`).MatchString(raw)
	case "prefix":
		return strings.HasPrefix(folded, rule.value)
	case "suffix":
		return strings.HasSuffix(folded, rule.value)
	case "contains":
		return strings.Contains(folded, rule.value)
	case "contains_word":
		for _, w := range words {
			if w == rule.value {
				return true
			}
		}
	case "first_name":
		return len(words) > 0 && words[0] == rule.value
	case "first_name_length":
		return len(words) > 0 && len(words[0]) == 4
	case "last_name_prefix":
		return len(words) > 0 && strings.HasPrefix(words[len(words)-1], rule.value)
	case "same_person_initial":
		return len(words) >= 2 && words[0][0] == words[len(words)-1][0]
	case "word_count":
		return len(words) == 3
	}
	return false
}
func (s *Sources) surfaceFindings(r Object, level string) []Object {
	out := []Object{}
	parsed := 0
	types := map[string]bool{}
	for _, group := range keys(obj(r["groups"])) {
		rule := parseSurface(str(obj(r["group_labels"])[group]))
		if rule == nil {
			continue
		}
		all := true
		for _, id := range members(r, group) {
			if !matchesSurface(rule, s.Graph.Label(id)) {
				all = false
			}
		}
		if !all {
			continue
		}
		parsed++
		foreign := []string{}
		for _, other := range keys(obj(r["groups"])) {
			for _, id := range members(r, other) {
				if n := s.Graph.Node(id); n != nil {
					types[n.NodeType] = true
				}
				if other != group && matchesSurface(rule, s.Graph.Label(id)) {
					foreign = append(foreign, id)
				}
			}
		}
		if len(foreign) > 0 {
			out = append(out, finding("surface_predicate_crossfit", level, group+" matches foreign tiles: "+strings.Join(foreign, ", ")))
		}
	}
	if parsed >= 3 && len(types) > 1 {
		out = append(out, finding("visible_string_worksheet", "WARN", "at least three literal display rules across multiple types"))
	}
	return out
}
