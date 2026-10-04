package contentbuild

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type exportSnapshot struct {
	data   []byte
	exists bool
	mode   os.FileMode
}

func exportPath(root, name string) (string, error) {
	p := filepath.Join(root, "go-backend", "internal", "content", name)
	parent, e := filepath.EvalSymlinks(filepath.Dir(p))
	if e != nil {
		return "", e
	}
	if parent != filepath.Dir(p) {
		return "", fmt.Errorf("symlinked export parent refused")
	}
	if info, e := os.Lstat(p); e == nil {
		if !info.Mode().IsRegular() {
			return "", fmt.Errorf("export target must be regular and not a symlink")
		}
		if info.Size() > 64<<20 {
			return "", fmt.Errorf("existing private export exceeds snapshot bound")
		}
	} else if !os.IsNotExist(e) {
		return "", e
	}
	return p, nil
}
func atomicExport(path string, data []byte, mode os.FileMode) error {
	f, e := os.CreateTemp(filepath.Dir(path), ".cat-content-export-")
	if e != nil {
		return e
	}
	tmp := f.Name()
	defer os.Remove(tmp)
	if e = f.Chmod(mode); e == nil {
		_, e = f.Write(data)
	}
	if e == nil {
		e = f.Sync()
	}
	closeErr := f.Close()
	if e == nil {
		e = closeErr
	}
	if e != nil {
		return e
	}
	if e = os.Rename(tmp, path); e != nil {
		return e
	}
	dir, e := os.Open(filepath.Dir(path))
	if e != nil {
		return e
	}
	defer dir.Close()
	return dir.Sync()
}

// exportTransaction shares the source operator's lock. Production builds run
// inside the acquired lock; test callbacks only inject failures in synthetic roots.
func exportTransaction(root string, produce func() ([]byte, []byte, error), verify func() error, afterWrite func(int) error) (result error) {
	root, e := filepath.Abs(root)
	if e != nil {
		return e
	}
	root = filepath.Clean(root)
	lock, e := os.OpenFile(filepath.Join(root, ".cat-content-ops.lock"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return fmt.Errorf("content operator is locked: %w", e)
	}
	defer os.Remove(lock.Name())
	if e = lock.Close(); e != nil {
		return e
	}
	paths := []string{}
	original := map[string]exportSnapshot{}
	for _, name := range []string{"bundled.json", "digest.go"} {
		path, e := exportPath(root, name)
		if e != nil {
			return e
		}
		data, e := os.ReadFile(path)
		if e != nil && !os.IsNotExist(e) {
			return e
		}
		s := exportSnapshot{data: data, exists: e == nil, mode: 0644}
		if s.exists {
			info, e := os.Stat(path)
			if e != nil {
				return e
			}
			s.mode = info.Mode().Perm()
		}
		paths = append(paths, path)
		original[path] = s
	}
	bundle, pin, e := produce()
	if e != nil {
		return e
	}
	if len(bundle) > 64<<20 || len(pin) > 64<<10 {
		return fmt.Errorf("private export exceeds write bounds")
	}
	changes := map[string][]byte{paths[0]: bundle, paths[1]: pin}
	sort.Strings(paths)
	defer func() {
		if result == nil {
			return
		}
		failures := []string{}
		for _, p := range paths {
			s := original[p]
			if s.exists {
				if e := atomicExport(p, s.data, s.mode); e != nil {
					failures = append(failures, e.Error())
				}
			} else if e := os.Remove(p); e != nil && !os.IsNotExist(e) {
				failures = append(failures, e.Error())
			}
		}
		for _, p := range paths {
			s := original[p]
			data, e := os.ReadFile(p)
			if s.exists && (e != nil || !bytes.Equal(data, s.data)) || !s.exists && !os.IsNotExist(e) {
				failures = append(failures, "rollback mismatch: "+p)
			}
		}
		if len(failures) > 0 {
			result = fmt.Errorf("%w; export rollback incomplete: %s", result, strings.Join(failures, "; "))
		}
	}()
	for i, p := range paths {
		if e = atomicExport(p, changes[p], original[p].mode); e != nil {
			return e
		}
		if afterWrite != nil {
			if e = afterWrite(i); e != nil {
				return e
			}
		}
	}
	if verify != nil {
		return verify()
	}
	return nil
}
