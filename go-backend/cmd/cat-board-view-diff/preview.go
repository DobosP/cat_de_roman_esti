package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"path/filepath"
	"runtime"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
)

type previewFiles struct {
	root, kg, kgSHA, pack, packSHA string
}

func (p previewFiles) compare(before *content.Content) (*report, error) {
	if runtime.Version() != "go1.27.3" {
		return nil, fmt.Errorf("one-word preview requires go1.27.3, got %s", runtime.Version())
	}
	if p.root == "" || p.kg == "" || p.pack == "" || !validSHA(p.kgSHA) || !validSHA(p.packSHA) {
		return nil, errors.New("one-word preview requires baseline root, prospective KG and pack paths, and both lowercase SHA-256 digests")
	}
	root, err := filepath.Abs(p.root)
	if err != nil {
		return nil, err
	}
	kgBytes, err := readBoundFile(p.kg, p.kgSHA, 16<<20)
	if err != nil {
		return nil, fmt.Errorf("prospective KG: %w", err)
	}
	packBytes, err := readBoundFile(p.pack, p.packSHA, 8<<20)
	if err != nil {
		return nil, fmt.Errorf("prospective pack: %w", err)
	}
	kg, err := contentops.Decode(kgBytes)
	if err != nil {
		return nil, fmt.Errorf("prospective KG: %w", err)
	}
	graph, err := contentbuild.BoardViewGraph(kg)
	if err != nil {
		return nil, fmt.Errorf("prospective KG: %w", err)
	}
	word, err := additiveWord(before, graph.Content)
	if err != nil {
		return nil, err
	}
	if err := validateDegrees(graph.Content); err != nil {
		return nil, err
	}
	after, err := contentops.BoardViewPreview(root, before, graph, contentbuild.TextSHA256(kgBytes), packBytes)
	if err != nil {
		return nil, err
	}
	result, err := compareMode(before, after, true)
	if err != nil {
		return nil, err
	}
	result.DryRun = &dryRunResult{WordID: word, Limit: 10, Hold: result.DisturbedTotal > 10,
		KGSHA256: p.kgSHA, PackSHA256: p.packSHA}
	return result, nil
}

func writeReport(result *report, output io.Writer) error {
	enc := json.NewEncoder(output)
	enc.SetIndent("", "  ")
	return enc.Encode(result)
}

func validateDegrees(c *content.Content) error {
	degree := make(map[string]int, len(c.Nodes))
	for _, edge := range c.Edges {
		degree[edge.Src]++
		degree[edge.Dst]++
	}
	for _, node := range c.Nodes {
		if node.Degree != degree[node.ID] {
			return fmt.Errorf("prospective node degree mismatch for %s", node.ID)
		}
	}
	return nil
}
