package catalog

import "github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"

// PreferredForReview applies the same preference filter as serving. A
// baseline probe forces preferredShelf to reveal whether it retains score.
func PreferredForReview(score int) bool {
	candidate := &content.Board{OverallScore: score}
	witness := &content.Board{OverallScore: 100}
	return preferredShelf([]*content.Board{candidate, witness})[0] == candidate
}
