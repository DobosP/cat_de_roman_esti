package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"unicode/utf8"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contexto"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
)

const (
	reblindSchema      = "cat-v5-board-reblind-compare-1"
	reblindInputSchema = "cat-v5-board-reblind-compare-input-1"
	maxViewDiffBytes   = 8 << 20
	maxReblindInput    = 1 << 20
	maxTranscriptBytes = 1 << 20
	maxReblindBoards   = 512
	maxPlaySteps       = 512
	maxGuesses         = 64
	maxGuessBytes      = 256
)

var commitID = regexp.MustCompile(`^[a-f0-9]{40}$`)

type reblindFiles struct {
	diff, diffSHA, baselineCommit, candidateCommit, root, input string
}

type fileRef struct {
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
}

type reblindCase struct {
	key        boardKey
	before     string
	after      string
	thread     string
	transcript fileRef
	guesses    []string
}

type reblindRow struct {
	boardKey
	ViewSHA256         string  `json:"view_sha256"`
	BaselineViewSHA256 string  `json:"baseline_view_sha256"`
	ThreadID           string  `json:"thread_id"`
	Transcript         fileRef `json:"transcript"`
	Guesses            int     `json:"guesses"`
	CandidateScored    int     `json:"candidate_scored_guesses"`
	BaselineScored     int     `json:"baseline_scored_guesses"`
	CandidateBest      int     `json:"candidate_best_rank"`
	BaselineBest       int     `json:"baseline_best_rank"`
	WonCandidate       bool    `json:"won_candidate"`
	WonBaseline        bool    `json:"won_baseline"`
	K                  int     `json:"k"`
	Verdict            string  `json:"verdict"`
	StockQuality       bool    `json:"stock_quality"`
}

type reblindReceipt struct {
	Schema          string         `json:"schema"`
	Baseline        string         `json:"baseline"`
	SHA             string         `json:"sha"`
	BaselineSHA256  string         `json:"baseline_bundle_sha256"`
	CandidateSHA256 string         `json:"candidate_bundle_sha256"`
	ViewDiffSHA256  string         `json:"board_view_diff_sha256"`
	Boards          []reblindRow   `json:"boards"`
	Totals          map[string]int `json:"totals"`
}

// reblindVerdict is the paired rule for an existing Cald board. k is the
// number of candidate-only concepts ranked above the candidate's best guess.
// Each of them moves an unchanged guess down by one rank. Losing a win that
// the same guesses reach on the baseline is measurably less close.
func reblindVerdict(wonCandidate, wonBaseline bool, candidateBest, baselineBest, k int) string {
	switch {
	case wonCandidate:
		return "win"
	case wonBaseline:
		return "worse"
	case candidateBest <= baselineBest+k:
		return "no-worse"
	default:
		return "worse"
	}
}

func (p reblindFiles) compare(before, after *content.Content, beforeSHA, afterSHA string) (*reblindReceipt, error) {
	if p.diff == "" || !validSHA(p.diffSHA) || !commitID.MatchString(p.baselineCommit) ||
		!commitID.MatchString(p.candidateCommit) || p.root == "" || p.input == "" {
		return nil, errors.New("paired re-blind requires the view diff and its SHA-256, both full commit IDs, the evidence root and the transcript list")
	}
	raw, err := readBoundFile(p.diff, p.diffSHA, maxViewDiffBytes)
	if err != nil {
		return nil, fmt.Errorf("view diff: %w", err)
	}
	var diff report
	if err := decodeStrict(raw, &diff); err != nil {
		return nil, fmt.Errorf("view diff: %w", err)
	}
	if diff.Schema != viewDiffSchema || diff.DryRun != nil || diff.BaselineSHA256 != beforeSHA || diff.CandidateSHA256 != afterSHA {
		return nil, errors.New("view diff is not the full " + viewDiffSchema + " report for these exact bundles")
	}
	disturbed := make(map[boardKey]change, len(diff.Disturbed))
	for _, row := range diff.Disturbed {
		disturbed[row.boardKey] = row
	}
	list, err := readList(p.input)
	if err != nil {
		return nil, fmt.Errorf("transcript list: %w", err)
	}
	var input struct {
		Schema string `json:"schema"`
		Boards []struct {
			boardKey
			Transcript fileRef `json:"transcript"`
		} `json:"boards"`
	}
	if err := decodeStrict(list, &input); err != nil {
		return nil, fmt.Errorf("transcript list: %w", err)
	}
	if input.Schema != reblindInputSchema || len(input.Boards) == 0 || len(input.Boards) > maxReblindBoards {
		return nil, fmt.Errorf("transcript list must be %s with 1 to %d boards", reblindInputSchema, maxReblindBoards)
	}
	root, err := os.OpenRoot(p.root)
	if err != nil {
		return nil, fmt.Errorf("evidence root: %w", err)
	}
	defer root.Close()
	cases := make([]reblindCase, 0, len(input.Boards))
	keys, digests := map[boardKey]bool{}, map[string]bool{}
	for _, board := range input.Boards {
		row, found := disturbed[board.boardKey]
		if board.Game != "contexto" || !found || row.Kind != "changed" || keys[board.boardKey] {
			return nil, fmt.Errorf("%s/%s is not one disturbed existing Cald board of the view diff", board.Game, board.ID)
		}
		if digests[board.Transcript.SHA256] {
			return nil, fmt.Errorf("%s/%s reuses another board's transcript", board.Game, board.ID)
		}
		keys[board.boardKey], digests[board.Transcript.SHA256] = true, true
		raw, err := readEvidence(root, board.Transcript, maxTranscriptBytes)
		if err != nil {
			return nil, fmt.Errorf("%s/%s transcript: %w", board.Game, board.ID, err)
		}
		played, err := parseTranscript(raw)
		if err != nil {
			return nil, fmt.Errorf("%s/%s transcript: %w", board.Game, board.ID, err)
		}
		if played.key != board.boardKey || played.after != row.AfterSHA256 {
			return nil, fmt.Errorf("%s/%s transcript is bound to another board or view", board.Game, board.ID)
		}
		played.before, played.transcript = row.BeforeSHA256, board.Transcript
		cases = append(cases, played)
	}
	rows, err := compareReblind(before, after, cases)
	if err != nil {
		return nil, err
	}
	out := &reblindReceipt{Schema: reblindSchema, Baseline: p.baselineCommit, SHA: p.candidateCommit,
		BaselineSHA256: beforeSHA, CandidateSHA256: afterSHA, ViewDiffSHA256: p.diffSHA, Boards: rows,
		Totals: map[string]int{"win": 0, "no-worse": 0, "worse": 0, "stock_quality": 0}}
	for _, row := range rows {
		out.Totals[row.Verdict]++
		if row.StockQuality {
			out.Totals["stock_quality"]++
		}
	}
	return out, nil
}

// compareReblind replays each critic's typed guesses on both builds with the
// native Cald service. Rows come back in stable board ID order.
func compareReblind(before, after *content.Content, cases []reblindCase) ([]reblindRow, error) {
	left := services{data: before, g: graph.New(before), cald: contexto.New(before)}
	right := services{data: after, g: graph.New(after), cald: contexto.New(after)}
	added := []string{}
	for _, node := range after.Nodes {
		if !left.g.Exists(node.ID) {
			added = append(added, node.ID)
		}
	}
	rows := make([]reblindRow, 0, len(cases))
	for _, c := range cases {
		row := reblindRow{boardKey: c.key, ViewSHA256: c.after, BaselineViewSHA256: c.before,
			ThreadID: c.thread, Transcript: c.transcript, Guesses: len(c.guesses)}
		target := "" // The candidate side runs last and leaves its target here.
		baselineTarget := ""
		for _, side := range []struct {
			s            services
			view         string
			best, scored *int
			won          *bool
		}{{left, c.before, &row.BaselineBest, &row.BaselineScored, &row.WonBaseline},
			{right, c.after, &row.CandidateBest, &row.CandidateScored, &row.WonCandidate}} {
			item, err := side.s.servedCald(c.key.ID)
			if err != nil {
				return nil, fmt.Errorf("%s/%s: %w", c.key.Game, c.key.ID, err)
			}
			view, err := side.s.packView(item)
			if err != nil {
				return nil, fmt.Errorf("%s/%s: %w", c.key.Game, c.key.ID, err)
			}
			if hashFields(view.parts) != side.view {
				return nil, fmt.Errorf("%s/%s: view diff row differs from the native bundle view", c.key.Game, c.key.ID)
			}
			target = item.Payload["target"].(string)
			if side.best == &row.BaselineBest {
				baselineTarget = target
			} else if target != baselineTarget {
				return nil, fmt.Errorf("%s/%s: board target differs between baseline and candidate", c.key.Game, c.key.ID)
			}
			played, err := side.s.cald.BoardReplayForReview(target, item.Difficulty, c.guesses)
			if err != nil {
				return nil, fmt.Errorf("%s/%s: %w", c.key.Game, c.key.ID, err)
			}
			for _, guess := range played {
				if !guess.Scored {
					continue
				}
				if *side.scored == 0 || guess.Rank < *side.best {
					*side.best = guess.Rank
				}
				*side.scored++
				*side.won = *side.won || guess.Won
			}
			if *side.scored == 0 {
				return nil, fmt.Errorf("%s/%s: no typed guess is a scored native guess on both builds", c.key.Game, c.key.ID)
			}
		}
		for _, id := range added {
			if rank, reachable := right.cald.BoardRankForReview(target, id); reachable && rank < row.CandidateBest {
				row.K++
			}
		}
		row.Verdict = reblindVerdict(row.WonCandidate, row.WonBaseline, row.CandidateBest, row.BaselineBest, row.K)
		row.StockQuality = !row.WonCandidate && !row.WonBaseline
		rows = append(rows, row)
	}
	slices.SortFunc(rows, func(a, b reblindRow) int { return compareKeys(a.boardKey, b.boardKey) })
	return rows, nil
}

// servedCald finds the approved, selectable ranked Cald row with this ID.
func (s services) servedCald(id string) (content.PackItem, error) {
	for _, item := range s.data.PackItems {
		if item.Game == "contexto" && item.ID == id {
			if item.Status != "approved" || !item.PilotEligible {
				break
			}
			return item, nil
		}
	}
	return content.PackItem{}, errors.New("board is not a served Cald row in both bundles")
}

// parseTranscript reads the critic transcript that closeout also binds: the
// five board, view and role fields plus play. A play step whose guess member
// is a string is one typed guess, in order. Other steps are feedback.
func parseTranscript(raw []byte) (reblindCase, error) {
	var doc struct {
		Game    string                       `json:"game"`
		ID      string                       `json:"id"`
		View    string                       `json:"view_sha256"`
		Thread  string                       `json:"thread_id"`
		Verdict string                       `json:"verdict"`
		Play    []map[string]json.RawMessage `json:"play"`
	}
	if err := decodeStrict(raw, &doc); err != nil {
		return reblindCase{}, err
	}
	// encoding/json matches member names without case. Closeout needs them exact.
	var members map[string]json.RawMessage
	if err := json.Unmarshal(raw, &members); err != nil || len(members) != 6 {
		return reblindCase{}, errors.New("expected exactly game, id, view_sha256, thread_id, verdict and play")
	}
	for _, name := range []string{"game", "id", "view_sha256", "thread_id", "verdict", "play"} {
		if members[name] == nil {
			return reblindCase{}, errors.New("expected exactly game, id, view_sha256, thread_id, verdict and play")
		}
	}
	if doc.Game == "" || doc.ID == "" || !validSHA(doc.View) || doc.Verdict == "" || doc.Thread == "" ||
		len(doc.Thread) > 128 || strings.TrimSpace(doc.Thread) != doc.Thread {
		return reblindCase{}, errors.New("invalid board, view or critic thread binding")
	}
	if len(doc.Play) == 0 || len(doc.Play) > maxPlaySteps {
		return reblindCase{}, fmt.Errorf("play must have 1 to %d steps", maxPlaySteps)
	}
	guesses := []string{}
	for _, step := range doc.Play {
		if len(step) == 0 {
			return reblindCase{}, errors.New("every play step must be a nonempty object")
		}
		var text string
		if json.Unmarshal(step["guess"], &text) != nil {
			continue
		}
		if strings.TrimSpace(text) == "" || len(text) > maxGuessBytes || !utf8.ValidString(text) {
			return reblindCase{}, fmt.Errorf("a typed guess must be nonblank text within %d bytes", maxGuessBytes)
		}
		guesses = append(guesses, text)
	}
	if len(guesses) == 0 || len(guesses) > maxGuesses {
		return reblindCase{}, fmt.Errorf("play must hold 1 to %d typed guesses", maxGuesses)
	}
	return reblindCase{key: boardKey{doc.Game, doc.ID}, after: doc.View, thread: doc.Thread, guesses: guesses}, nil
}

// readList reads the unpinned transcript list. Every pointer in it carries
// its own digest and is echoed in the receipt.
func readList(path string) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil {
		return nil, err
	}
	data, err := io.ReadAll(io.LimitReader(f, maxReblindInput+1))
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || len(data) > maxReblindInput {
		return nil, errors.New("expected a regular file within its size bound")
	}
	return data, nil
}

func decodeStrict(raw []byte, value any) error {
	if err := strictjson.Validate(raw); err != nil {
		return err
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	return decoder.Decode(value)
}

// readEvidence reads one digest-bound regular file below the evidence root.
// os.Root refuses a path or symlink that leaves the root.
func readEvidence(root *os.Root, ref fileRef, maxBytes int64) ([]byte, error) {
	if !validSHA(ref.SHA256) || ref.Path == "" || strings.ContainsAny(ref.Path, "\\:") || !filepath.IsLocal(filepath.FromSlash(ref.Path)) {
		return nil, errors.New("expected a forward-slash path below the evidence root and a lowercase SHA-256 digest")
	}
	name := filepath.FromSlash(ref.Path)
	info, err := root.Lstat(name)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > maxBytes {
		return nil, errors.New("expected a regular file within its size bound")
	}
	f, err := root.Open(name)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	actual, err := f.Stat()
	if err != nil {
		return nil, err
	}
	if !actual.Mode().IsRegular() || !os.SameFile(info, actual) {
		return nil, errors.New("evidence path changed before opening")
	}
	data, err := io.ReadAll(io.LimitReader(f, maxBytes+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > maxBytes || contentbuild.SHA256(data) != ref.SHA256 {
		return nil, errors.New("exact file SHA-256 mismatch or size bound exceeded")
	}
	return data, nil
}
