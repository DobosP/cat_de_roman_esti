// Package embedfs owns the managed UI build and byte-frozen rollback bundle.
package embedfs

import "embed"

// Files contains the output populated by the owning assets-sync gate before
// compiling a server. all: also retains the private Vite manifests and scaffold.
//go:embed all:dist all:legacy
var Files embed.FS

// BuildIdentity is private generated metadata, separate from the exact managed
// dist/legacy asset inventories. Missing metadata never qualifies a build.
//go:embed all:build/dist
var BuildIdentity embed.FS
