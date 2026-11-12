package contentrails

import (
	"fmt"
	"path/filepath"
)

// installedSourceOperation belongs to one top-level Check/CheckAll/Rebuild.
// Only strict authored-source decoding is reused. Approval, live audits,
// runtime inventories and current fixture bindings are never cached here.
// Callers must verify before and after every adopted reconstruction.
type installedSourceOperation struct {
	root         string
	authoritySHA string
	sources      map[string]*Source
	documents    []installedSourceDocument
}

type installedSourceDocument struct {
	path   string
	sha256 string
}

func (a *installedAuthorities) captureSourceOperation(root string) (*installedSourceOperation, error) {
	absoluteRoot, err := filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	// Preserve every strict source schema/version/parent and archive check.
	sources, err := a.sources(root)
	if err != nil {
		return nil, err
	}
	operation := &installedSourceOperation{root: absoluteRoot, authoritySHA: digest(a.raw), sources: sources}
	for _, v := range rows(a.raw["source_chain"]) {
		e := object(v)
		operation.documents = append(operation.documents, installedSourceDocument{text(e["path"]), text(e["sha256"])})
		for _, v := range object(sources[text(e["sha256"])].Raw["archives"]) {
			d := object(v)
			operation.documents = append(operation.documents, installedSourceDocument{text(d["path"]), text(d["sha256"])})
		}
	}
	return operation, nil
}

func (operation *installedSourceOperation) verify(root string, a *installedAuthorities) error {
	absoluteRoot, err := filepath.Abs(root)
	if err != nil || operation.root != absoluteRoot || operation.authoritySHA != digest(a.raw) {
		return fmt.Errorf("installed source operation root/authority membership changed")
	}
	if _, err = loadInstalledAuthorities(root); err != nil {
		return err
	}
	// Retain every source/archive occurrence, including shared descriptors.
	// Exact reviewed bytes imply the already checked decoded shape and parent;
	// only redundant parsing is omitted. The existing path/regular-file/byte
	// guards still run on every document at each verification boundary.
	for _, document := range operation.documents {
		descriptor := map[string]any{"path": document.path, "sha256": document.sha256}
		if _, _, err = authorityDocument(root, descriptor); err != nil {
			return err
		}
	}
	return nil
}

// withSource preserves the actual pre/post source guard around the existing
// reconstruction, fresh final audit and installed-artifact validation span.
// The closure is private production composition, never an approval provider.
func (operation *installedSourceOperation) withSource(root string, a *installedAuthorities, sha string, build func(*Source) (map[string]any, error)) (map[string]any, error) {
	if err := operation.verify(root, a); err != nil {
		return nil, err
	}
	source := operation.source(sha)
	if source == nil {
		return nil, fmt.Errorf("installed authority does not authorize selected authored source")
	}
	catalog, err := build(source)
	if err != nil {
		return nil, err
	}
	if err = operation.verify(root, a); err != nil {
		return nil, err
	}
	return catalog, nil
}

func (operation *installedSourceOperation) source(sha string) *Source {
	source := operation.sources[sha]
	if source == nil {
		return nil
	}
	// A builder receives private mutable maps/slices. JSON scalars, including
	// strings and json.Number, are immutable values and need no serialization.
	return &Source{Raw: copyInstalledSourceJSON(source.Raw).(map[string]any), SHA256: source.SHA256, Version: source.Version}
}

func copyInstalledSourceJSON(value any) any {
	switch value := value.(type) {
	case map[string]any:
		copied := make(map[string]any, len(value))
		for key, item := range value {
			copied[key] = copyInstalledSourceJSON(item)
		}
		return copied
	case []any:
		copied := make([]any, len(value))
		for index, item := range value {
			copied[index] = copyInstalledSourceJSON(item)
		}
		return copied
	}
	// All inputs are private results of strict JSON decoding, so the remaining
	// possible values are immutable JSON scalars, never caller-owned pointers.
	return value
}
