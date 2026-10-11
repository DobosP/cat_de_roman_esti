package main

import (
	"context"
	"errors"
	"io"
	"os"
	"strconv"

	"github.com/DobosP/roedu-ui/web-kit/health"
)

// defaultPort is the container port when PORT is unset or empty, as the
// pre-M1 shell form `${PORT:-8000}` did; compose.gate.yml sets PORT=8080.
const defaultPort = "8000"

// The canonical image runs without a shell, so PORT is read here: the
// server binds ":"+PORT unless -listen is given, and /app healthcheck probes
// the same port on loopback through the existing SDK's bounded native probe.
func guiHealthcheck(args []string, out io.Writer) error {
	port, err := envPort()
	if err != nil {
		return err
	}
	return health.Command(context.Background(), args, out, health.Options{URL: "http://127.0.0.1:" + port + "/healthz"})
}

// envPort returns PORT as a decimal 1..65535 (ASCII digits only), defaulting
// to 8000 when unset or empty. Anything else fails closed without echoing it.
func envPort() (string, error) {
	raw := os.Getenv("PORT")
	if raw == "" {
		return defaultPort, nil
	}
	if len(raw) > 5 {
		return "", errors.New("PORT must be a decimal port from 1 to 65535")
	}
	for i := 0; i < len(raw); i++ {
		if raw[i] < '0' || raw[i] > '9' {
			return "", errors.New("PORT must be a decimal port from 1 to 65535")
		}
	}
	n, err := strconv.Atoi(raw)
	if err != nil || n < 1 || n > 65535 {
		return "", errors.New("PORT must be a decimal port from 1 to 65535")
	}
	return strconv.Itoa(n), nil
}

// listenAddress keeps an explicit -listen verbatim; otherwise it is ":"+PORT.
func listenAddress(listen string, explicit bool) (string, error) {
	if explicit {
		return listen, nil
	}
	port, err := envPort()
	if err != nil {
		return "", err
	}
	return ":" + port, nil
}
