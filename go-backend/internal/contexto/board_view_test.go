package contexto

import (
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

func TestBoardReplayForReviewUsesLiveGuessPathAndLeavesNoSession(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	s := New(c)
	target := ""
	for _, item := range c.PackItems {
		id, _ := item.Payload["target"].(string)
		if item.Game == "contexto" && item.PilotEligible && s.g.Resolve(s.g.Label(id)) == id {
			target = id
			break
		}
	}
	top, _ := s.BoardTopForReview(target)
	if target == "" || len(top) < 2 || top[0].ID != target {
		t.Fatalf("no served Cald board to replay: %q", target)
	}
	near := top[1].Label
	played, err := s.BoardReplayForReview(target, "normal", []string{near, "qqqqzzzzxxxxjjjj", s.g.Label(target), near})
	if err != nil {
		t.Fatal(err)
	}
	// The guess after the win is never played.
	if len(played) != 3 || !played[0].Scored || played[0].Won || played[1].Scored || !played[2].Scored || !played[2].Won ||
		played[2].ID != target || played[2].Rank != 1 {
		t.Fatalf("unexpected replay: %+v", played)
	}
	if rank, reachable := s.BoardRankForReview(target, played[0].ID); !reachable || rank != played[0].Rank || rank < 2 {
		t.Fatalf("replayed rank %d differs from the board rank %d", played[0].Rank, rank)
	}
	if s.store.Len() != 0 {
		t.Fatalf("review replay left %d sessions", s.store.Len())
	}
	if _, err := s.BoardReplayForReview("missing-concept", "normal", []string{near}); err == nil {
		t.Fatal("unknown target accepted")
	}
	if _, err := s.BoardReplayForReview(target, "normal", []string{"   "}); err == nil || s.store.Len() != 0 {
		t.Fatalf("blank guess must be refused without a leftover session: %v", err)
	}
}
