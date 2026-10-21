package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"io/fs"
	"net"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/embedfs"
)

// The test binary doubles as cat-server, so startup runs exactly as main does.
const runAsServer = "CAT_SERVER_TEST_RUN_MAIN"

func TestMain(m *testing.M) {
	if os.Getenv(runAsServer) == "1" {
		main()
		os.Exit(0)
	}
	os.Exit(m.Run())
}

func serverProcess(t *testing.T, env map[string]string, args ...string) *exec.Cmd {
	t.Helper()
	cmd := exec.Command(os.Args[0], args...)
	cmd.Env = append(os.Environ(), runAsServer+"=1", "PORT=", "CAT_ACCOUNTS_ENABLED=0", "CAT_SUBMISSIONS_ENABLED=0",
		"CAT_ALLOWED_HOSTS=", "CAT_DOMAIN=", "CAT_UI=", "CAT_CSP_ENFORCE=")
	for key, value := range env {
		cmd.Env = append(cmd.Env, key+"="+value)
	}
	return cmd
}

func freeAddress(t *testing.T) string {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	return listener.Addr().String()
}

// startServer returns the process exit, or a nil error once /healthz answers.
func startServer(t *testing.T, env map[string]string) (exited bool, exitErr error, stderr string, addr string, stop func()) {
	t.Helper()
	addr = freeAddress(t)
	cmd := serverProcess(t, env, "-listen", addr)
	var output bytes.Buffer
	cmd.Stdout, cmd.Stderr = io.Discard, &output
	if err := cmd.Start(); err != nil {
		t.Fatal(err)
	}
	done := make(chan error, 1)
	go func() { done <- cmd.Wait() }()
	stop = func() {
		_ = cmd.Process.Kill()
		<-done
	}
	client := &http.Client{Timeout: time.Second}
	deadline := time.Now().Add(60 * time.Second)
	for time.Now().Before(deadline) {
		select {
		case err := <-done:
			return true, err, output.String(), addr, func() {}
		case <-time.After(50 * time.Millisecond):
		}
		if response, err := client.Get("http://" + addr + "/healthz"); err == nil {
			response.Body.Close()
			return false, nil, "", addr, stop
		}
	}
	stop()
	t.Fatal("cat-server neither exited nor answered /healthz within 60s")
	return
}

func managedUIBuilt() bool {
	_, err := fs.Stat(embedfs.Files, "dist/.vite/manifest.json")
	return err == nil
}

// DCR-1: a managed UI that cannot be admitted once gave a site-wide 503 while
// /healthz stayed 200. Serving now refuses to start instead.
func TestServingRefusesUnavailableManagedUI(t *testing.T) {
	cases := []struct {
		name   string
		env    map[string]string
		reason string
	}{
		{"invalid CAT_UI", map[string]string{"CAT_UI": "invalid"}, "CAT_UI must be current or legacy"},
		{"invalid CAT_CSP_ENFORCE", map[string]string{"CAT_CSP_ENFORCE": "yes"}, "CAT_CSP_ENFORCE must be true or false"},
	}
	if !managedUIBuilt() {
		// An unbuilt scaffold is itself unavailable and is refused before the flag is read.
		cases[1].reason = "manifest"
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			exited, err, stderr, addr, stop := startServer(t, c.env)
			if !exited {
				defer stop()
				status := 0
				if response, getErr := http.Get("http://" + addr + "/"); getErr == nil {
					status = response.StatusCode
					response.Body.Close()
				}
				t.Fatalf("cat-server answered /healthz with an unavailable managed UI (GET / = %d)", status)
			}
			var exit *exec.ExitError
			if !errors.As(err, &exit) || exit.ExitCode() == 0 {
				t.Fatalf("cat-server exit = %v, want a failed start", err)
			}
			if !strings.Contains(stderr, "managed UI unavailable: ") || !strings.Contains(stderr, c.reason) {
				t.Fatalf("startup refusal does not name the managed UI cause %q: %q", c.reason, stderr)
			}
		})
	}
}

func TestServingStartsOnlyWithAdmittedManagedUI(t *testing.T) {
	exited, err, stderr, addr, stop := startServer(t, nil)
	if !managedUIBuilt() {
		if !exited {
			stop()
			t.Fatal("cat-server served from the unbuilt managed UI scaffold")
		}
		var exit *exec.ExitError
		if !errors.As(err, &exit) || !strings.Contains(stderr, "managed UI unavailable: ") {
			t.Fatalf("unbuilt scaffold start = %v, stderr %q", err, stderr)
		}
		return
	}
	if exited {
		t.Fatalf("cat-server refused an admitted managed UI: %v, stderr %q", err, stderr)
	}
	defer stop()
	response, err := http.Get("http://" + addr + "/")
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK || !strings.HasPrefix(response.Header.Get("Content-Type"), "text/html") {
		t.Fatalf("GET / = %d %q, want the managed document", response.StatusCode, response.Header.Get("Content-Type"))
	}
}

// Offline replay serves API contracts only, so an unbuilt or unselected UI keeps it usable.
func TestReplayDoesNotRequireManagedUI(t *testing.T) {
	cmd := serverProcess(t, map[string]string{"CAT_UI": "invalid"}, "-replay")
	cmd.Stdin = strings.NewReader(`{"method":"GET","path":"/api/health"}` + "\n")
	var stdout, stderr bytes.Buffer
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	if err := cmd.Run(); err != nil {
		t.Fatalf("replay with an unavailable managed UI failed: %v, stderr %q", err, stderr.String())
	}
	var row struct {
		Status int `json:"status"`
	}
	if err := json.Unmarshal(stdout.Bytes(), &row); err != nil || row.Status != http.StatusOK {
		t.Fatalf("replayed /api/health = %q, error %v", stdout.String(), err)
	}
}
