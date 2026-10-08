// Package health implements the distroless-friendly healthcheck command.
package health

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Options names the local HTTP endpoint and optional engine report callback.
// URL is required; no shell or external executable is used.
type Options struct {
	URL string
	Client *http.Client
	Engines func() any
}

// Command handles healthcheck [--engines]. It returns an error for an unhealthy
// endpoint, malformed arguments, or an unavailable engine report.
func Command(ctx context.Context, args []string, out io.Writer, o Options) error {
	if len(args) == 0 || args[0] != "healthcheck" || len(args) > 2 || (len(args) == 2 && args[1] != "--engines") {
		return errors.New("usage: healthcheck [--engines]")
	}
	if o.URL == "" { return errors.New("healthcheck URL is required") }
	client := o.Client
	if client == nil { client = &http.Client{Timeout: 3 * time.Second} }
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, o.URL, nil)
	if err != nil { return fmt.Errorf("healthcheck request: %w", err) }
	resp, err := client.Do(req)
	if err != nil { return fmt.Errorf("healthcheck endpoint unavailable: %w", err) }
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK { return fmt.Errorf("healthcheck status: %d", resp.StatusCode) }
	// Bound reads even when an incorrectly configured endpoint never finishes.
	if _, err := io.Copy(io.Discard, io.LimitReader(resp.Body, 4096)); err != nil { return err }
	if len(args) == 2 {
		if o.Engines == nil { return errors.New("engine report is unavailable") }
		return json.NewEncoder(out).Encode(o.Engines())
	}
	_, err = io.WriteString(out, "healthy\n")
	return err
}
