package contentops

import (
	"errors"
	"fmt"
	"path/filepath"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
)

// Check validates source mechanics and regenerated native sidecars without the
// sealed export's fixed reviewed pins. Export and authority remain separate gates.
// Maps are compared semantically; native sidecars also require render's exact
// sorted-key bytes. Arrays, numbers, source bindings and weights remain exact.
func (s *Sources) Check() (result Object, err error) {
	defer func() {
		err = errors.Join(err, checkSnapshots(s.Inputs), s.checkInventory())
	}()
	if err = checkSnapshots(s.Inputs); err != nil {
		return nil, err
	}
	if err = s.checkInventory(); err != nil {
		return nil, err
	}
	if failures := contentbuild.ValidateFixture(filepath.Join(s.Root, fixtures+"kg_sample.json")); len(failures) != 0 {
		return nil, fmt.Errorf("graph validation: %s", strings.Join(failures, "; "))
	}
	// Validate the actual source, not LoadSources' in-memory high-water repair.
	pack, err := Decode(s.PackBytes)
	if err != nil {
		return nil, err
	}
	if failures := contentbuild.ValidatePackObjects(s.KG, pack); len(failures) != 0 {
		return nil, fmt.Errorf("pack validation: %s", strings.Join(failures, "; "))
	}
	rank, err := s.Rank(false)
	if err != nil {
		return nil, err
	}
	if err = requireNativeFormat(rank, "rank"); err != nil {
		return nil, err
	}
	derived, err := s.Derive(false)
	if err != nil {
		return nil, err
	}
	if err = requireNativeFormat(derived, "derive"); err != nil {
		return nil, err
	}
	boards := 0
	for _, game := range Games {
		boards += len(array(pack[game]))
	}
	return Object{
		"scope":    "graph, pack, native rankings and derived catalog; export and authority checked separately",
		"checks":   4,
		"nodes":    len(array(s.KG["kg_nodes"])),
		"edges":    len(array(s.KG["kg_edges"])),
		"puzzles":  len(array(s.KG["kg_puzzles"])),
		"boards":   boards,
		"rankings": rank,
		"derived":  derived,
		"write":    false,
	}, nil
}

func requireNativeFormat(report Object, command string) error {
	if report["format_drift"] == true {
		return fmt.Errorf("format_drift: %s; regenerate both mirrors with cat-content-ops %s --root ROOT --write", str(report["artifact"]), command)
	}
	return nil
}
