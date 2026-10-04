// Package httpgolden implements bounded native HTTP qualification. Expected
// reference bodies remain independent frozen application contracts.
package httpgolden

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"os/exec"
	"strings"
	"sync"
	"time"
)

const MaxResponse = 4 * 1024 * 1024
const MaxRequest = 65537
const MaxCalls = 10000
const RequestTimeout = 15 * time.Second

type Request struct {
	Method  string            `json:"method"`
	Path    string            `json:"path"`
	Body    string            `json:"body"`
	Headers map[string]string `json:"headers,omitempty"`
}
type Response struct {
	Status   int           `json:"status"`
	Body     any           `json:"body"`
	Headers  http.Header   `json:"-"`
	Raw      []byte        `json:"-"`
	Duration time.Duration `json:"-"`
}
type Transport interface {
	Do(context.Context, Request) (Response, error)
	Close() error
}
type Client struct {
	transport Transport
	limit     int
	mu        sync.Mutex
	calls     int
}

func NewClient(t Transport, limit int) (*Client, error) {
	if limit < 1 || limit > MaxCalls {
		return nil, fmt.Errorf("request limit must be 1..%d", MaxCalls)
	}
	return &Client{transport: t, limit: limit}, nil
}
func (c *Client) Count() int { c.mu.Lock(); defer c.mu.Unlock(); return c.calls }
func (c *Client) Do(ctx context.Context, r Request) (Response, error) {
	if !strings.HasPrefix(r.Path, "/") || strings.HasPrefix(r.Path, "//") || strings.ContainsAny(r.Path, "\r\n#") || len(r.Path) > 16384 {
		return Response{}, fmt.Errorf("request path must be a bounded origin-relative path")
	}
	if _, err := url.ParseRequestURI(r.Path); err != nil {
		return Response{}, fmt.Errorf("invalid request URI")
	}
	if len(r.Body) > MaxRequest {
		return Response{}, fmt.Errorf("request body exceeds %d bytes", MaxRequest)
	}
	switch r.Method {
	case "GET", "HEAD", "POST", "OPTIONS":
	default:
		return Response{}, fmt.Errorf("unsupported qualification method")
	}
	for name := range r.Headers {
		if strings.EqualFold(name, "Authorization") || strings.EqualFold(name, "Cookie") {
			return Response{}, fmt.Errorf("qualification must remain anonymous")
		}
	}
	c.mu.Lock()
	if c.calls >= c.limit {
		c.mu.Unlock()
		return Response{}, fmt.Errorf("request budget exceeded")
	}
	c.calls++
	c.mu.Unlock()
	child, cancel := context.WithTimeout(ctx, RequestTimeout)
	defer cancel()
	return c.transport.Do(child, r)
}
func (c *Client) Close() error { return c.transport.Close() }
func (r Response) Object() (map[string]any, error) {
	body, ok := r.Body.(map[string]any)
	if !ok {
		return nil, fmt.Errorf("response is not a JSON object")
	}
	return body, nil
}
func decode(raw []byte) any {
	if len(raw) == 0 {
		return nil
	}
	var v any
	d := json.NewDecoder(bytes.NewReader(raw))
	d.UseNumber()
	if d.Decode(&v) == nil {
		var extra any
		if d.Decode(&extra) == io.EOF {
			return v
		}
	}
	return string(raw)
}
func JSONRequest(method, path string, body any) Request {
	raw := ""
	if body != nil {
		b, _ := json.Marshal(body)
		raw = string(b)
	}
	return Request{Method: method, Path: path, Body: raw}
}

type httpTransport struct {
	origin    string
	client    *http.Client
	transport *http.Transport
}

func HTTP(origin string) (Transport, error) {
	u, err := url.Parse(origin)
	if err != nil || u.Scheme != "http" && u.Scheme != "https" || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || u.Path != "" && u.Path != "/" {
		return nil, fmt.Errorf("URL must be an explicit HTTP(S) origin without credentials, path or query")
	}
	t := &http.Transport{Proxy: nil, DisableCompression: true, MaxIdleConns: 64, MaxIdleConnsPerHost: 64, IdleConnTimeout: 30 * time.Second, ResponseHeaderTimeout: RequestTimeout}
	return &httpTransport{strings.TrimRight(origin, "/"), &http.Client{Transport: t, Timeout: RequestTimeout, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}, t}, nil
}
func (t *httpTransport) Do(ctx context.Context, r Request) (Response, error) {
	req, err := http.NewRequestWithContext(ctx, r.Method, t.origin+r.Path, strings.NewReader(r.Body))
	if err != nil {
		return Response{}, err
	}
	req.Header.Set("Accept-Encoding", "identity")
	if r.Body != "" {
		req.Header.Set("Content-Type", "application/json")
	}
	for k, v := range r.Headers {
		req.Header.Set(k, v)
	}
	start := time.Now()
	res, err := t.client.Do(req)
	if err != nil {
		return Response{}, fmt.Errorf("HTTP connection failed or exceeded timeout: %w", err)
	}
	defer res.Body.Close()
	raw, err := io.ReadAll(io.LimitReader(res.Body, MaxResponse+1))
	if err != nil {
		return Response{}, err
	}
	if len(raw) > MaxResponse {
		return Response{}, fmt.Errorf("response budget exceeded")
	}
	return Response{res.StatusCode, decode(raw), res.Header, raw, time.Since(start)}, nil
}
func (t *httpTransport) Close() error { t.transport.CloseIdleConnections(); return nil }

type localTransport struct{ handler http.Handler }

type limitedRecorder struct {
	header   http.Header
	status   int
	body     bytes.Buffer
	overflow bool
}

func (w *limitedRecorder) Header() http.Header { return w.header }
func (w *limitedRecorder) WriteHeader(status int) {
	if w.status == 0 {
		w.status = status
	}
}
func (w *limitedRecorder) Write(raw []byte) (int, error) {
	if w.status == 0 {
		w.status = 200
	}
	if len(raw) > MaxResponse-w.body.Len() {
		w.overflow = true
		return 0, fmt.Errorf("response budget exceeded")
	}
	return w.body.Write(raw)
}

func Local(h http.Handler) Transport { return &localTransport{h} }
func (t *localTransport) Do(ctx context.Context, r Request) (Response, error) {
	if err := ctx.Err(); err != nil {
		return Response{}, err
	}
	request := httptest.NewRequest(r.Method, r.Path, strings.NewReader(r.Body)).WithContext(ctx)
	for k, v := range r.Headers {
		request.Header.Set(k, v)
	}
	result := make(chan struct {
		response Response
		err      error
	}, 1)
	start := time.Now()
	go func() {
		w := &limitedRecorder{header: http.Header{}}
		t.handler.ServeHTTP(w, request)
		if w.overflow {
			result <- struct {
				response Response
				err      error
			}{err: fmt.Errorf("response budget exceeded")}
			return
		}
		if w.status == 0 {
			w.status = 200
		}
		result <- struct {
			response Response
			err      error
		}{response: Response{w.status, decode(w.body.Bytes()), w.header, append([]byte{}, w.body.Bytes()...), time.Since(start)}}
	}()
	select {
	case value := <-result:
		return value.response, value.err
	case <-ctx.Done():
		return Response{}, ctx.Err()
	}
}
func (t *localTransport) Close() error { return nil }

type replayTransport struct {
	cmd    *exec.Cmd
	cancel context.CancelFunc
	in     io.WriteCloser
	out    *bufio.Reader
	mu     sync.Mutex
	closed bool
}

func Binary(binary string) (Transport, error) {
	ctx, cancel := context.WithCancel(context.Background())
	cmd := exec.CommandContext(ctx, binary, "--replay")
	cmd.Env = append(os.Environ(), "CAT_ACCOUNTS_ENABLED=0", "CAT_SUBMISSIONS_ENABLED=0")
	in, err := cmd.StdinPipe()
	if err != nil {
		cancel()
		return nil, err
	}
	out, err := cmd.StdoutPipe()
	if err != nil {
		cancel()
		return nil, err
	}
	cmd.Stderr = os.Stderr
	if err = cmd.Start(); err != nil {
		cancel()
		return nil, err
	}
	return &replayTransport{cmd: cmd, cancel: cancel, in: in, out: bufio.NewReaderSize(out, 65536)}, nil
}
func (t *replayTransport) Do(ctx context.Context, r Request) (Response, error) {
	t.mu.Lock()
	defer t.mu.Unlock()
	if t.closed {
		return Response{}, fmt.Errorf("replay process closed")
	}
	start := time.Now()
	raw, err := json.Marshal(r)
	if err != nil {
		return Response{}, err
	}
	result := make(chan struct {
		r Response
		e error
	}, 1)
	go func() {
		_, e := t.in.Write(append(raw, '\n'))
		if e != nil {
			result <- struct {
				r Response
				e error
			}{e: e}
			return
		}
		line := []byte{}
		for {
			chunk, e := t.out.ReadSlice('\n')
			line = append(line, chunk...)
			if len(line) > MaxResponse {
				result <- struct {
					r Response
					e error
				}{e: fmt.Errorf("replay response budget exceeded")}
				return
			}
			if e == bufio.ErrBufferFull {
				continue
			}
			if e != nil {
				result <- struct {
					r Response
					e error
				}{e: e}
				return
			}
			break
		}
		var v struct {
			Status int `json:"status"`
			Body   any `json:"body"`
		}
		d := json.NewDecoder(bytes.NewReader(line))
		d.UseNumber()
		if e = d.Decode(&v); e != nil {
			result <- struct {
				r Response
				e error
			}{e: e}
			return
		}
		result <- struct {
			r Response
			e error
		}{r: Response{Status: v.Status, Body: v.Body, Duration: time.Since(start)}}
	}()
	select {
	case value := <-result:
		return value.r, value.e
	case <-ctx.Done():
		t.closed = true
		t.cancel()
		_ = t.in.Close()
		return Response{}, fmt.Errorf("native replay timeout")
	}
}
func (t *replayTransport) Close() error {
	t.mu.Lock()
	t.closed = true
	_ = t.in.Close()
	t.mu.Unlock()
	done := make(chan error, 1)
	go func() { done <- t.cmd.Wait() }()
	select {
	case err := <-done:
		t.cancel()
		return err
	case <-time.After(5 * time.Second):
		t.cancel()
		return <-done
	}
}
