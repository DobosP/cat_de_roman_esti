// cat-form-probes compares exact corpus surfaces with proposed aliases using
// the same normalization and SequenceMatcher direction as the Cald resolver.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"maps"
	"os"
	"slices"
	"strings"
	"unicode/utf8"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
)

const (
	maxForms        = 100
	maxProbeBytes   = 256
	maxCorpusBytes  = 64 << 20
	maxCorpusRows   = 2_000_000
	suggestionFloor = .78
	fuzzyFloor      = .84
)

type proposal struct {
	ItemID  string `json:"item_id"`
	OwnerID string `json:"owner_id"`
	Surface string `json:"surface"`
}

type frequencyWitness struct {
	Probe string `json:"probe"`
	Token string `json:"token"`
}

type batch struct {
	Proposals          []proposal         `json:"proposals"`
	Profanity          []string           `json:"profanity"`
	FrequencyWitnesses []frequencyWitness `json:"frequency_witnesses"`
	UncoveredTitles    []string           `json:"uncovered_titles"`
}

type proposalResult struct {
	proposal
	Key                string `json:"key"`
	ExistingExactOwner string `json:"existing_exact_owner,omitempty"`
	ReviewedUnresolved bool   `json:"reviewed_unresolved,omitempty"`
	DuplicateKey       bool   `json:"duplicate_key,omitempty"`
	ProfanityExact     bool   `json:"profanity_exact,omitempty"`
	NearbyCount        int    `json:"nearby_count"`
	UnavailableCount   int    `json:"unavailable_count"`
}

type neighbor struct {
	Surface            string `json:"surface"`
	ProposalIndexes    []int  `json:"proposal_indexes"`
	ReviewedUnresolved bool   `json:"reviewed_unresolved,omitempty"`
}

type unsafeResolution struct {
	Probe             string `json:"probe"`
	BeforeOwner       string `json:"before_owner"`
	AfterOwner        string `json:"after_owner"`
	NearbyProposals   []int  `json:"nearby_proposals"`
	SingleFormChanges []int  `json:"single_form_changes"`
	RemovalChanges    []int  `json:"removal_changes"`
}

type result struct {
	Proposals           []proposalResult   `json:"proposals"`
	Neighbors           []neighbor         `json:"neighbors"`
	Unavailable         []neighbor         `json:"unavailable_neighbors"`
	NearbyCoverageGaps  []neighbor         `json:"nearby_titles_with_coverage_gaps"`
	UnsafeResolutions   []unsafeResolution `json:"unsafe_resolutions"`
	SupportedCorpusRows int                `json:"supported_corpus_rows"`
}

func readFile(path string, maxBytes int64) ([]byte, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Size() > maxBytes {
		return nil, errors.New("expected a bounded regular file")
	}
	raw, err := io.ReadAll(io.LimitReader(file, maxBytes+1))
	if err != nil || int64(len(raw)) != info.Size() {
		return nil, errors.New("input changed size or could not be read")
	}
	return raw, nil
}

func readJSON(path string, maxBytes int64, dest any) error {
	raw, err := readFile(path, maxBytes)
	if err != nil {
		return err
	}
	if !utf8.Valid(raw) || strictjson.Validate(raw) != nil {
		return errors.New("expected strict UTF-8 JSON")
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	return decoder.Decode(dest)
}

func validProbe(raw string) bool {
	return utf8.ValidString(raw) && len(raw) <= maxProbeBytes && strings.TrimSpace(raw) != ""
}

type word struct {
	key    string
	length int
	counts map[rune]int
}

func normalizedWord(key string) word {
	w := word{key: key, counts: map[rune]int{}}
	for _, ch := range key {
		w.counts[ch]++
		w.length++
	}
	return w
}

func near(proposal, typed word, threshold float64) bool {
	if proposal.key == typed.key {
		return true
	}
	length := float64(proposal.length + typed.length)
	if 2*float64(min(proposal.length, typed.length))/length < threshold {
		return false
	}
	// A matched rune consumes an occurrence on each side. The multiset
	// intersection is therefore an upper bound on SequenceRatio's matches.
	matches := 0
	for ch, count := range proposal.counts {
		matches += min(count, typed.counts[ch])
	}
	return 2*float64(matches)/length >= threshold &&
		graph.SequenceRatio(proposal.key, typed.key) >= threshold
}

func prospective(data *content.Content, index map[string]string) *graph.Service {
	// Only these tables participate in Resolve and ResolveFuzzy.
	return graph.New(&content.Content{
		NormalizationMap:       data.NormalizationMap,
		AccentNormalizationMap: data.AccentNormalizationMap,
		NormalizedIndex:        index,
	})
}

func unsafeResolutions(data *content.Content, rows []proposalResult, words []word, probes []string) []unsafeResolution {
	baseline := prospective(data, data.NormalizedIndex)
	all := make(map[string]string, len(data.NormalizedIndex)+len(rows))
	maps.Copy(all, data.NormalizedIndex)
	additions := []int{}
	for i, row := range rows {
		if row.ExistingExactOwner == "" && !row.ReviewedUnresolved && !row.DuplicateKey {
			all[row.Key] = row.OwnerID
			additions = append(additions, i)
		}
	}
	after := prospective(data, all)
	out := []unsafeResolution{}
	for _, probe := range probes {
		typed := normalizedWord(probe)
		related := []int{}
		for _, i := range additions {
			if near(words[i], typed, fuzzyFloor) {
				related = append(related, i)
			}
		}
		if len(related) == 0 {
			continue
		}
		old := baseline.ResolveFuzzy(probe)
		next := after.ResolveFuzzy(probe)
		single, removal := []int{}, []int{}
		for _, i := range related {
			row := rows[i]
			index := make(map[string]string, len(data.NormalizedIndex)+1)
			maps.Copy(index, data.NormalizedIndex)
			index[row.Key] = row.OwnerID
			got := prospective(data, index).ResolveFuzzy(probe)
			if got != "" && got != old {
				single = append(single, i)
			}
			if next != "" && next != old && len(related) > 1 {
				without := maps.Clone(all)
				delete(without, row.Key)
				if prospective(data, without).ResolveFuzzy(probe) != next {
					removal = append(removal, i)
				}
			}
		}
		if next == old {
			next = ""
		}
		if next != "" || len(single) > 0 {
			out = append(out, unsafeResolution{probe, old, next, related, single, removal})
		}
	}
	return out
}

func orderedSurface(i int, surface, previous string) error {
	if surface == "" || len(surface) > 1024 || (i > 0 && surface <= previous) {
		return errors.New("expected strictly sorted exact corpus surfaces of at most 1024 bytes")
	}
	return nil
}

func nearby(g *graph.Service, words []word, surface string) neighbor {
	row := neighbor{Surface: surface}
	typed := normalizedWord(g.Normalize(surface))
	if typed.key == "" {
		return row
	}
	for i, query := range words {
		if near(query, typed, suggestionFloor) {
			row.ProposalIndexes = append(row.ProposalIndexes, i)
		}
	}
	if len(row.ProposalIndexes) != 0 {
		row.ReviewedUnresolved = g.ReviewedUnresolved(surface)
	}
	return row
}

func scan(data *content.Content, input batch, corpus []string) (result, error) {
	out := result{
		Proposals: []proposalResult{}, Neighbors: []neighbor{},
		Unavailable: []neighbor{}, UnsafeResolutions: []unsafeResolution{}, NearbyCoverageGaps: []neighbor{},
		SupportedCorpusRows: len(corpus),
	}
	if len(input.Proposals) == 0 || len(input.Proposals) > maxForms || len(input.Profanity) == 0 ||
		len(input.Profanity) >= 1000-maxForms || len(input.UncoveredTitles) > maxCorpusRows || len(corpus) == 0 || len(corpus) > maxCorpusRows {
		return out, errors.New("invalid proposal, profanity, or corpus count")
	}
	g := prospective(data, data.NormalizedIndex)
	profanity := map[string]bool{}
	for _, raw := range input.Profanity {
		if !validProbe(raw) || raw != g.Normalize(raw) || profanity[raw] {
			return out, errors.New("expected distinct normalized profanity probes")
		}
		profanity[raw] = true
	}
	if len(input.FrequencyWitnesses) == 0 {
		return out, errors.New("expected pinned FrequencyWords witnesses")
	}
	for _, witness := range input.FrequencyWitnesses {
		if !profanity[witness.Probe] || g.Normalize(witness.Token) != witness.Probe {
			return out, errors.New("FrequencyWords witness does not normalize to its tracked probe")
		}
	}
	keys := map[string]int{}
	words := make([]word, len(input.Proposals))
	for i, row := range input.Proposals {
		key := g.Normalize(row.Surface)
		if row.ItemID == "" || data.Labels[row.OwnerID] == "" || !validProbe(row.Surface) || key == "" {
			return out, fmt.Errorf("invalid proposal %d", i)
		}
		words[i] = normalizedWord(key)
		keys[key]++
		out.Proposals = append(out.Proposals, proposalResult{
			proposal: row, Key: key, ExistingExactOwner: data.NormalizedIndex[key],
			ReviewedUnresolved: g.ReviewedUnresolved(row.Surface), ProfanityExact: profanity[key],
		})
	}
	for i := range out.Proposals {
		out.Proposals[i].DuplicateKey = keys[out.Proposals[i].Key] > 1
	}

	previous := ""
	for i, surface := range corpus {
		if err := orderedSurface(i, surface, previous); err != nil {
			return out, err
		}
		previous = surface
		row := nearby(g, words, surface)
		if len(row.ProposalIndexes) == 0 {
			continue
		}
		if validProbe(surface) {
			out.Neighbors = append(out.Neighbors, row)
			for _, j := range row.ProposalIndexes {
				out.Proposals[j].NearbyCount++
			}
		} else {
			out.Unavailable = append(out.Unavailable, row)
			for _, j := range row.ProposalIndexes {
				out.Proposals[j].UnavailableCount++
			}
		}
	}

	previous = ""
	for i, title := range input.UncoveredTitles {
		if err := orderedSurface(i, title, previous); err != nil {
			return out, err
		}
		previous = title
		row := nearby(g, words, title)
		if len(row.ProposalIndexes) != 0 {
			out.NearbyCoverageGaps = append(out.NearbyCoverageGaps, row)
		}
	}

	slices.Sort(input.Profanity)
	out.UnsafeResolutions = unsafeResolutions(data, out.Proposals, words, input.Profanity)
	return out, nil
}

func run(args []string, output io.Writer) error {
	flags := flag.NewFlagSet("cat-form-probes", flag.ContinueOnError)
	bundlePath := flags.String("bundle", "", "exact baseline bundle")
	batchPath := flags.String("batch", "", "bound batch inputs")
	corpusPath := flags.String("corpus", "", "strictly sorted exact corpus JSON array")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 || *bundlePath == "" || *batchPath == "" || *corpusPath == "" {
		return errors.New("--bundle, --batch and --corpus are required")
	}
	bundle, err := readFile(*bundlePath, 32<<20)
	if err != nil {
		return fmt.Errorf("bundle: %w", err)
	}
	data, err := content.Decode(bundle)
	if err != nil {
		return fmt.Errorf("bundle: %w", err)
	}
	var input batch
	if err := readJSON(*batchPath, 16<<20, &input); err != nil {
		return fmt.Errorf("batch: %w", err)
	}
	var corpus []string
	if err := readJSON(*corpusPath, maxCorpusBytes, &corpus); err != nil {
		return fmt.Errorf("corpus: %w", err)
	}
	report, err := scan(data, input, corpus)
	if err != nil {
		return err
	}
	return json.NewEncoder(output).Encode(report)
}

func main() {
	if err := run(os.Args[1:], os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
