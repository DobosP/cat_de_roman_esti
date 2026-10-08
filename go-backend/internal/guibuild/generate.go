package guibuild

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/DobosP/roedu-ui/web-kit/health"
)

func outputDirectory(root string) (string, error) {
	cursor := root
	for _, part := range []string{"go-backend", "embedfs", "build", "dist"} {
		cursor = filepath.Join(cursor, part)
		info, err := os.Lstat(cursor)
		if os.IsNotExist(err) {
			if err := os.Mkdir(cursor, 0755); err != nil {
				return "", err
			}
			continue
		}
		if err != nil {
			return "", err
		}
		if info.Mode()&os.ModeSymlink != 0 || !info.IsDir() {
			return "", fmt.Errorf("GUI build output ancestor refused")
		}
	}
	return cursor, nil
}

func writeAtomic(directory, name string, data []byte) error {
	destination := filepath.Join(directory, name)
	if info, err := os.Lstat(destination); err == nil {
		if !info.Mode().IsRegular() {
			return fmt.Errorf("GUI build output is not regular")
		}
	} else if !os.IsNotExist(err) {
		return err
	}
	file, err := os.CreateTemp(directory, ".gui-build-*")
	if err != nil {
		return err
	}
	temporary := file.Name()
	defer os.Remove(temporary)
	if err := file.Chmod(0644); err != nil {
		file.Close()
		return err
	}
	if _, err := file.Write(data); err != nil {
		file.Close()
		return err
	}
	if err := file.Close(); err != nil {
		return err
	}
	return os.Rename(temporary, destination)
}

// Generate is called only after the image's real frontend build and owning
// assets sync. SHA/tree are explicit canonical Docker build arguments, never
// ambient runtime environment or a locally invented source snapshot recipe.
func Generate(root, sha, tree string) (result error) {
	root, err := filepath.Abs(root)
	if err != nil {
		return err
	}
	resolved, err := filepath.EvalSymlinks(root)
	if err != nil {
		return err
	}
	if resolved != root {
		return fmt.Errorf("GUI build root alias refused")
	}
	info, err := os.Lstat(root)
	if err != nil {
		return err
	}
	if info.Mode()&os.ModeSymlink != 0 || !info.IsDir() {
		return fmt.Errorf("GUI build root refused")
	}
	directory, err := outputDirectory(root)
	if err != nil {
		return err
	}
	descriptor := filepath.Join(directory, filepath.Base(DescriptorPath))
	if info, err := os.Lstat(descriptor); err == nil {
		if !info.Mode().IsRegular() {
			return fmt.Errorf("GUI build descriptor output refused")
		}
		if err := os.Remove(descriptor); err != nil {
			return err
		}
	} else if !os.IsNotExist(err) {
		return err
	}
	// A failed regeneration cannot leave an earlier qualifying descriptor.
	defer func() {
		if result != nil {
			_ = os.Remove(descriptor)
		}
	}()
	inputs := os.DirFS(root)
	manifest, err := readRegular(inputs, "go-backend/embedfs/"+ManifestPath, 4*1024*1024)
	if err != nil {
		return err
	}
	lock, err := readRegular(inputs, "versions.lock.json", 2*1024*1024)
	if err != nil {
		return err
	}
	identity, err := health.NewIdentity(sha, tree, manifest, lock)
	if err != nil {
		return err
	}
	data, err := json.Marshal(identity)
	if err != nil {
		return err
	}
	data = append(data, '\n')
	if err := writeAtomic(directory, filepath.Base(VersionsLockPath), lock); err != nil {
		return err
	}
	if err := writeAtomic(directory, filepath.Base(DescriptorPath), data); err != nil {
		return err
	}
	embedded := os.DirFS(filepath.Join(root, "go-backend", "embedfs"))
	verified, err := Load(embedded, embedded)
	if err != nil {
		return err
	}
	if *verified != *identity {
		return fmt.Errorf("GUI build output verification failed")
	}
	return nil
}
