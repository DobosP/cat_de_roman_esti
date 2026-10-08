package main

import (
	"context"
	"io"

	"github.com/DobosP/roedu-ui/web-kit/health"
)

// The canonical compose app invokes /app healthcheck. Dockerfile.gui binds its
// server to 8080; this command uses the existing SDK's bounded native probe.
func guiHealthcheck(args []string, out io.Writer) error {
	return health.Command(context.Background(), args, out, health.Options{URL: "http://127.0.0.1:8080/healthz"})
}
