package httpapi

import (
	"bufio"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
	"time"
)

const prebodyResponseDeadline = 2 * time.Second

// tcpHeadersOnly keeps the write side open after declaring a request body. A
// Recorder, a zero-length body, CloseWrite or an uploaded dummy body cannot
// exercise net/http's post-handler unread-body drain. The socket deadline is
// deliberately below cat-server's production 15-second ReadTimeout.
func tcpHeadersOnly(t *testing.T, serverURL, method, path string, contentLength int64, headers http.Header, wantStatus int) {
	t.Helper()
	endpoint, err := url.Parse(serverURL)
	if err != nil {
		t.Fatal("TCP fixture URL invalid")
	}
	conn, err := net.DialTimeout("tcp", endpoint.Host, prebodyResponseDeadline)
	if err != nil {
		t.Fatal("TCP fixture dial failed")
	}
	defer conn.Close()
	if err = conn.SetDeadline(time.Now().Add(prebodyResponseDeadline)); err != nil {
		t.Fatal("TCP fixture deadline failed")
	}
	host := endpoint.Host
	if value := headers.Get("Host"); value != "" {
		host = value
	}
	var request strings.Builder
	fmt.Fprintf(&request, "%s %s HTTP/1.1\r\nHost: %s\r\nContent-Length: %d\r\n", method, path, host, contentLength)
	for name, values := range headers {
		if strings.EqualFold(name, "Host") || strings.EqualFold(name, "Content-Length") {
			continue
		}
		for _, value := range values {
			fmt.Fprintf(&request, "%s: %s\r\n", name, value)
		}
	}
	request.WriteString("\r\n")
	// Send only the headers. Do not close or half-close the request's write side.
	if _, err = io.WriteString(conn, request.String()); err != nil {
		t.Fatal("TCP fixture header write failed")
	}
	response, err := http.ReadResponse(bufio.NewReader(conn), &http.Request{Method: method})
	if err != nil {
		t.Fatalf("headers-only request did not receive HTTP %d within %s: %v", wantStatus, prebodyResponseDeadline, err)
	}
	defer response.Body.Close()
	if response.StatusCode != wantStatus {
		t.Fatalf("headers-only refusal returned HTTP %d, want %d", response.StatusCode, wantStatus)
	}
	if _, err = io.ReadAll(io.LimitReader(response.Body, 4<<10)); err != nil {
		t.Fatalf("refusal response body did not complete within %s: %v", prebodyResponseDeadline, err)
	}
	if !response.Close {
		t.Fatal("unread-body refusal must close the HTTP connection")
	}
	if wantStatus == http.StatusRequestEntityTooLarge && response.Header.Get("Cache-Control") != "no-store" {
		t.Fatal("oversized refusal lost existing no-store boundary")
	}
}

func TestTCPEarlyOversizedRefusalWithoutBodyUpload(t *testing.T) {
	server := httptest.NewUnstartedServer(testServer(t))
	server.Config.ReadHeaderTimeout = 5 * time.Second
	server.Config.ReadTimeout = 15 * time.Second
	server.Config.WriteTimeout = 30 * time.Second
	server.Start()
	t.Cleanup(server.Close)
	for _, contentType := range []string{"application/json", "text/plain"} {
		t.Run(contentType, func(t *testing.T) {
			tcpHeadersOnly(t, server.URL, "POST", prefix, int64(MaxRequestBytes+1), http.Header{"Content-Type": []string{contentType}}, http.StatusRequestEntityTooLarge)
		})
	}
}

func tcpFixtureHeaders(t *testing.T, f *arcadeFixture, client *http.Client, csrf bool) http.Header {
	t.Helper()
	headers := http.Header{"Content-Type": []string{"application/json"}, "Origin": []string{f.web.URL}}
	endpoint, err := url.Parse(f.web.URL)
	if err != nil {
		t.Fatal("TCP account fixture URL invalid")
	}
	if client == nil || client.Jar == nil {
		return headers
	}
	cookies := []string{}
	for _, cookie := range client.Jar.Cookies(endpoint) {
		cookies = append(cookies, cookie.Name+"="+cookie.Value)
		if csrf && cookie.Name == "csrftoken" {
			headers.Set("X-CSRFToken", cookie.Value)
		}
	}
	if len(cookies) > 0 {
		headers.Set("Cookie", strings.Join(cookies, "; "))
	}
	return headers
}

func TestTCPEarlyAccountAndPrivacyRefusalsWithoutBodyUpload(t *testing.T) {
	f := newArcadeFixture(t)
	owner, other := f.client(), f.client()
	f.register(t, owner, "tcp-prebody-owner")
	f.register(t, other, "tcp-prebody-other")
	status, created, _ := f.request(t, owner, "POST", prefix+"?seed=17", nil, true)
	if status != http.StatusOK {
		t.Fatal("synthetic private-game fixture creation failed")
	}
	gameID, ok := created["game_id"].(string)
	if !ok || gameID == "" {
		t.Fatal("synthetic private-game fixture ID missing")
	}
	cases := []struct {
		name, method, path string
		client             *http.Client
		csrf               bool
		contentLength      int64
		host               string
		wantStatus         int
	}{
		{"known-oversized-auth-body", "POST", "/api/auth/signup", nil, false, int64(MaxRequestBytes + 1), "", http.StatusRequestEntityTooLarge},
		{"private-account-no-session", "GET", "/api/me/scores", nil, false, 1, "", http.StatusForbidden},
		{"unauthenticated-account-write", "POST", "/api/me/consent", nil, false, 1, "", http.StatusForbidden},
		{"account-csrf-before-json", "POST", "/api/me/profile", owner, false, 1, "", http.StatusForbidden},
		{"shared-auth-csrf-before-json", "POST", "/api/auth/signup", nil, false, 1, "", http.StatusForbidden},
		{"private-game-anonymous", "POST", prefix + "/" + gameID + "/guess", nil, false, 1, "", http.StatusNotFound},
		{"private-game-other-owner", "POST", prefix + "/" + gameID + "/guess", other, true, 1, "", http.StatusNotFound},
		{"private-game-csrf-before-json", "POST", prefix + "/" + gameID + "/guess", owner, false, 1, "", http.StatusForbidden},
		{"account-host-before-body", "POST", "/api/me/consent", nil, false, 1, "evil.invalid", http.StatusBadRequest},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			headers := tcpFixtureHeaders(t, f, test.client, test.csrf)
			if test.host != "" {
				headers.Set("Host", test.host)
			}
			tcpHeadersOnly(t, f.web.URL, test.method, test.path, test.contentLength, headers, test.wantStatus)
		})
	}
}

func TestTCPEarlyAnonymousConfiguredHostRefusalWithoutBodyUpload(t *testing.T) {
	handler := testServer(t)
	handler.allowedHosts = []string{"allowed.example"}
	server := httptest.NewUnstartedServer(handler)
	server.Config.ReadHeaderTimeout = 5 * time.Second
	server.Config.ReadTimeout = 15 * time.Second
	server.Config.WriteTimeout = 30 * time.Second
	server.Start()
	t.Cleanup(server.Close)
	tcpHeadersOnly(t, server.URL, "POST", prefix, 1000, http.Header{"Host": []string{"blocked.example"}, "Content-Type": []string{"application/json"}}, http.StatusBadRequest)
}

func TestTCPEarlyOversizedChunkedRefusalWithoutTerminatingChunk(t *testing.T) {
	server := httptest.NewUnstartedServer(testServer(t))
	server.Config.ReadHeaderTimeout = 5 * time.Second
	server.Config.ReadTimeout = 15 * time.Second
	server.Config.WriteTimeout = 30 * time.Second
	server.Start()
	t.Cleanup(server.Close)
	endpoint, err := url.Parse(server.URL)
	if err != nil {
		t.Fatal("TCP chunk fixture URL invalid")
	}
	conn, err := net.DialTimeout("tcp", endpoint.Host, prebodyResponseDeadline)
	if err != nil {
		t.Fatal("TCP chunk fixture dial failed")
	}
	defer conn.Close()
	if err = conn.SetDeadline(time.Now().Add(prebodyResponseDeadline)); err != nil {
		t.Fatal("TCP chunk fixture deadline failed")
	}
	// The server's limit reader stops after MaxRequestBytes+1 bytes. Supplying an
	// even larger chunk leaves unread payload and omitting the terminal zero chunk
	// keeps the request incomplete, exercising actual net/http body cleanup.
	payload := strings.Repeat("x", MaxRequestBytes+2)
	var request strings.Builder
	fmt.Fprintf(&request, "POST %s HTTP/1.1\r\nHost: %s\r\nContent-Type: application/json\r\nTransfer-Encoding: chunked\r\n\r\n%x\r\n", prefix, endpoint.Host, len(payload))
	request.WriteString(payload)
	request.WriteString("\r\n")
	// Keep the socket's write side open; deliberately send no 0\r\n\r\n chunk.
	if _, err = io.WriteString(conn, request.String()); err != nil {
		t.Fatal("TCP chunk fixture partial upload failed")
	}
	response, err := http.ReadResponse(bufio.NewReader(conn), &http.Request{Method: "POST"})
	if err != nil {
		t.Fatalf("unterminated oversized chunk did not receive HTTP 413 within %s: %v", prebodyResponseDeadline, err)
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusRequestEntityTooLarge {
		t.Fatalf("unterminated oversized chunk returned HTTP %d, want 413", response.StatusCode)
	}
	if _, err = io.ReadAll(io.LimitReader(response.Body, 4<<10)); err != nil {
		t.Fatalf("chunk refusal body did not complete within %s: %v", prebodyResponseDeadline, err)
	}
	if !response.Close || response.Header.Get("Cache-Control") != "no-store" {
		t.Fatal("chunk refusal lost connection-close or existing no-store boundary")
	}
}
