//go:build linux

package contentbuild

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/sys/unix"
)

type pendingDirectoryIdentity struct {
	path string
	dev  uint64
	ino  uint64
	uid  uint32
	gid  uint32
	mode uint32
}

// The caller exclusively owns this scratch directory for the entire operation.
// Same-UID peers must respect that task ownership. Malicious same-UID processes
// and administrators can defeat process/file isolation and are outside this
// contract; an observed replacement is nevertheless refused and preserved.
func privatePendingDirectoryMode(stat *unix.Stat_t, systemUID, operatorUID uint32, final bool) error {
	if stat.Mode&unix.S_IFMT != unix.S_IFDIR || stat.Uid != operatorUID && stat.Uid != systemUID || stat.Mode&(unix.S_ISUID|unix.S_ISGID) != 0 {
		return fmt.Errorf("pending scratch ancestor must be a trusted owned directory")
	}
	if final {
		if stat.Uid != operatorUID || stat.Mode&07777 != 0700 {
			return fmt.Errorf("pending output parent must be owned by effective UID with mode 0700")
		}
	} else if stat.Mode&0022 != 0 && stat.Mode&unix.S_ISVTX == 0 {
		return fmt.Errorf("pending scratch ancestor is writable without sticky protection")
	}
	return nil
}

func openPrivatePendingParent(path string) (*os.File, []pendingDirectoryIdentity, error) {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || strings.ContainsAny(path, "\x00\r\n") {
		return nil, nil, fmt.Errorf("pending parent requires a canonical absolute path")
	}
	fd, err := unix.Open("/", unix.O_RDONLY|unix.O_DIRECTORY|unix.O_NOFOLLOW|unix.O_CLOEXEC, 0)
	if err != nil {
		return nil, nil, err
	}
	var rootStat unix.Stat_t
	if err = unix.Fstat(fd, &rootStat); err != nil {
		_ = unix.Close(fd)
		return nil, nil, err
	}
	systemUID, operatorUID := rootStat.Uid, uint32(os.Geteuid())
	identities := []pendingDirectoryIdentity{}
	current := "/"
	parts := []string{}
	if path != "/" {
		parts = strings.Split(strings.TrimPrefix(path, "/"), "/")
	}
	for i := -1; i < len(parts); i++ {
		if i >= 0 {
			next, err := unix.Openat2(fd, parts[i], &unix.OpenHow{Flags: uint64(unix.O_RDONLY | unix.O_DIRECTORY | unix.O_NOFOLLOW | unix.O_CLOEXEC), Resolve: uint64(unix.RESOLVE_BENEATH | unix.RESOLVE_NO_SYMLINKS)})
			_ = unix.Close(fd)
			if err != nil {
				return nil, nil, fmt.Errorf("open pending ancestor without symlinks: %w", err)
			}
			fd = next
			current = filepath.Join(current, parts[i])
		}
		var stat unix.Stat_t
		if err := unix.Fstat(fd, &stat); err != nil {
			_ = unix.Close(fd)
			return nil, nil, err
		}
		if err := privatePendingDirectoryMode(&stat, systemUID, operatorUID, i == len(parts)-1); err != nil {
			_ = unix.Close(fd)
			return nil, nil, err
		}
		identities = append(identities, pendingDirectoryIdentity{current, uint64(stat.Dev), stat.Ino, stat.Uid, stat.Gid, stat.Mode})
	}
	return os.NewFile(uintptr(fd), path), identities, nil
}

func recheckPrivatePendingParent(path string, expected []pendingDirectoryIdentity) error {
	parent, actual, err := openPrivatePendingParent(path)
	if err != nil {
		return err
	}
	defer parent.Close()
	if len(actual) != len(expected) {
		return fmt.Errorf("pending ancestor membership changed")
	}
	for i := range actual {
		if actual[i] != expected[i] {
			return fmt.Errorf("pending ancestor identity, owner or mode changed")
		}
	}
	return nil
}

// ValidatePrivatePendingParent fails before intake unless the canonical output
// parent is operator-owned 0700 and every ancestor has trusted ownership and
// no unprotected group/other write access. A sticky system /tmp is admissible.
func ValidatePrivatePendingParent(output string) error {
	if !filepath.IsAbs(output) || filepath.Clean(output) != output || strings.ContainsAny(output, "\x00\r\n") {
		return fmt.Errorf("private pending output requires a canonical absolute path")
	}
	parent, _, err := openPrivatePendingParent(filepath.Dir(output))
	if err == nil {
		err = parent.Close()
	}
	return err
}

// linkPendingFD publishes the held anonymous inode, never a visible staging
// basename. Unprivileged Linux callers use the kernel's /proc/self/fd magic
// link when AT_EMPTY_PATH requires a capability. Unsupported filesystems or
// missing procfs fail closed; there is no named temporary-file fallback.
func linkPendingFD(file, parent *os.File, name string) error {
	err := unix.Linkat(int(file.Fd()), "", int(parent.Fd()), name, unix.AT_EMPTY_PATH)
	if err == nil {
		return nil
	}
	if err != unix.EPERM && err != unix.ENOENT && err != unix.EINVAL {
		return err
	}
	proc, e := unix.Open("/proc", unix.O_RDONLY|unix.O_DIRECTORY|unix.O_NOFOLLOW|unix.O_CLOEXEC, 0)
	if e != nil {
		return fmt.Errorf("pending fd publication requires procfs: %w", e)
	}
	var fs unix.Statfs_t
	e = unix.Fstatfs(proc, &fs)
	_ = unix.Close(proc)
	if e != nil || fs.Type != unix.PROC_SUPER_MAGIC {
		return fmt.Errorf("pending fd publication requires kernel procfs")
	}
	return unix.Linkat(unix.AT_FDCWD, fmt.Sprintf("/proc/self/fd/%d", file.Fd()), int(parent.Fd()), name, unix.AT_SYMLINK_FOLLOW)
}

func verifyPendingPublished(parent *os.File, name string, own os.FileInfo, expected []byte) error {
	fd, err := unix.Openat(int(parent.Fd()), name, unix.O_RDONLY|unix.O_NOFOLLOW|unix.O_NONBLOCK|unix.O_CLOEXEC, 0)
	if err != nil {
		return err
	}
	file := os.NewFile(uintptr(fd), name)
	defer file.Close()
	info, err := file.Stat()
	var stat unix.Stat_t
	if err != nil || !info.Mode().IsRegular() || !os.SameFile(own, info) || info.Mode().Perm() != 0600 || info.Mode()&(os.ModeSetuid|os.ModeSetgid|os.ModeSticky) != 0 {
		return fmt.Errorf("published pending inode/type/private mode differs")
	}
	if err = unix.Fstat(fd, &stat); err != nil || stat.Uid != uint32(os.Geteuid()) {
		return fmt.Errorf("published pending owner differs")
	}
	b, err := io.ReadAll(io.LimitReader(file, int64(len(expected))+1))
	if err != nil || !bytes.Equal(b, expected) {
		return fmt.Errorf("published pending bytes differ")
	}
	after, err := file.Stat()
	if err != nil || !os.SameFile(info, after) || after.Size() != int64(len(expected)) || after.Mode() != info.Mode() {
		return fmt.Errorf("published pending inode changed while checking")
	}
	return nil
}

// cleanupPendingOwned runs only while the complete private-directory policy
// remains intact. unlinkat is not an atomic compare-and-unlink syscall: safety
// relies on exclusive task ownership of the 0700 parent, excluding malicious
// same-UID/admin writers. An already observed replacement is never removed.
func cleanupPendingOwned(parent *os.File, parentPath, name string, chain []pendingDirectoryIdentity, own os.FileInfo) error {
	if err := recheckPrivatePendingParent(parentPath, chain); err != nil {
		return fmt.Errorf("pending cleanup refused after parent control changed: %w", err)
	}
	fd, err := unix.Openat(int(parent.Fd()), name, unix.O_RDONLY|unix.O_NOFOLLOW|unix.O_NONBLOCK|unix.O_CLOEXEC, 0)
	if err == unix.ENOENT {
		return nil
	}
	if err != nil {
		return fmt.Errorf("pending cleanup refused for replaced destination: %w", err)
	}
	file := os.NewFile(uintptr(fd), name)
	info, err := file.Stat()
	_ = file.Close()
	if err != nil || !info.Mode().IsRegular() || !os.SameFile(own, info) {
		return fmt.Errorf("pending cleanup refused for another inode")
	}
	if err = unix.Unlinkat(int(parent.Fd()), name, 0); err != nil {
		return err
	}
	return parent.Sync()
}

// WritePrivatePendingArtifact publishes one new 0600 scratch artifact from a
// held anonymous inode. The guard invokes commit exactly once under its input
// readset/root lock and rechecks inputs afterward. Actual linking stays inside
// that guard; cancellation/input failure removes only the owned output while
// the dedicated private-parent policy remains intact. It is not an installer.
func WritePrivatePendingArtifact(path string, data []byte, guard func(func() error) error) (result error) {
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || strings.ContainsAny(path, "\x00\r\n") || len(data) > 32<<20 || guard == nil {
		return fmt.Errorf("private pending output path/byte/guard bound")
	}
	parentPath, name := filepath.Dir(path), filepath.Base(path)
	parent, chain, err := openPrivatePendingParent(parentPath)
	if err != nil {
		return err
	}
	defer parent.Close()
	fd, err := unix.Openat(int(parent.Fd()), ".", unix.O_TMPFILE|unix.O_RDWR|unix.O_CLOEXEC, 0600)
	if err != nil {
		return fmt.Errorf("pending output requires anonymous private staging: %w", err)
	}
	file := os.NewFile(uintptr(fd), "anonymous quick pending inode")
	if err = file.Chmod(0600); err != nil {
		_ = file.Close()
		return err
	}
	own, err := file.Stat()
	if err != nil {
		_ = file.Close()
		return err
	}
	published, calls := false, 0
	defer func() {
		if result != nil && published {
			if err := cleanupPendingOwned(parent, parentPath, name, chain, own); err != nil {
				result = fmt.Errorf("%w; %v", result, err)
			}
		}
	}()
	defer func() {
		if err := file.Close(); result == nil {
			result = err
		}
	}()
	result = guard(func() error {
		calls++
		if calls != 1 {
			return fmt.Errorf("pending publication guard invoked twice")
		}
		if n, err := file.Write(data); err != nil {
			return err
		} else if n != len(data) {
			return fmt.Errorf("short pending artifact write")
		}
		if err := file.Sync(); err != nil {
			return err
		}
		if err := recheckPrivatePendingParent(parentPath, chain); err != nil {
			return err
		}
		if err := linkPendingFD(file, parent, name); err != nil {
			return err
		}
		published = true
		if err := verifyPendingPublished(parent, name, own, data); err != nil {
			return err
		}
		return parent.Sync()
	})
	if result == nil {
		result = recheckPrivatePendingParent(parentPath, chain)
	}
	if result == nil && (calls != 1 || !published) {
		result = fmt.Errorf("pending publication guard did not commit exactly once")
	}
	if result == nil {
		result = verifyPendingPublished(parent, name, own, data)
	}
	return result
}

func pendingFileMetadata(file *os.File) (string, error) {
	var stat unix.Stat_t
	if err := unix.Fstat(int(file.Fd()), &stat); err != nil {
		return "", err
	}
	return fmt.Sprintf("%d:%d:%d:%d", stat.Uid, stat.Gid, stat.Ctim.Sec, stat.Ctim.Nsec), nil
}
