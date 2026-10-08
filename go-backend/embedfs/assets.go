// Package embedfs owns the managed UI build and byte-frozen rollback bundle.
package embedfs

import "embed"

// Files contains the output populated by the owning assets-sync gate before
// compiling a server. all: also retains the private Vite manifests and scaffold.
//go:embed all:dist all:legacy
var Files embed.FS
