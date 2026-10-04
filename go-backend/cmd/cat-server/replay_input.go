package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
	"io"
	"net/url"
	"strings"
)

type replayInput struct {
	Method  string
	Path    string
	Body    string
	Headers map[string]string
}

func decodeReplayInput(raw []byte) (replayInput, error) {
	var input replayInput
	if err := strictjson.Validate(raw); err != nil {
		return input, err
	}
	var fields map[string]json.RawMessage
	if err := json.Unmarshal(raw, &fields); err != nil || fields == nil {
		return input, errors.New("replay object required")
	}
	seen := map[string]bool{}
	for key := range fields {
		canonical := strings.ToLower(key)
		if canonical != "method" && canonical != "path" && canonical != "body" && canonical != "headers" {
			return input, errors.New("unknown replay field")
		}
		if key != canonical && key != strings.ToUpper(canonical[:1])+canonical[1:] || seen[canonical] {
			return input, errors.New("ambiguous replay field")
		}
		if bytes.Equal(bytes.TrimSpace(fields[key]), []byte("null")) {
			return input, errors.New("null replay field refused")
		}
		if canonical == "headers" {
			var values map[string]json.RawMessage
			if err := json.Unmarshal(fields[key], &values); err != nil {
				return input, errors.New("replay headers object required")
			}
			for _, value := range values {
				if bytes.Equal(bytes.TrimSpace(value), []byte("null")) {
					return input, errors.New("null replay header refused")
				}
			}
		}
		seen[canonical] = true
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(&input); err != nil {
		return input, err
	}
	if d.Decode(new(any)) != io.EOF {
		return input, errors.New("trailing replay input")
	}
	if input.Method == "" {
		input.Method = "GET"
	}
	token := func(s string) bool {
		if len(s) == 0 || len(s) > 128 {
			return false
		}
		for _, b := range []byte(s) {
			if !(b >= 'A' && b <= 'Z' || b >= 'a' && b <= 'z' || b >= '0' && b <= '9' || strings.ContainsRune("!#$%&'*+-.^_`|~", rune(b))) {
				return false
			}
		}
		return true
	}
	if !token(input.Method) {
		return input, errors.New("invalid replay method")
	}
	uri, err := url.ParseRequestURI(input.Path)
	if err != nil || !strings.HasPrefix(input.Path, "/") || uri.IsAbs() || uri.Fragment != "" || len(input.Path) > 65536 {
		return input, errors.New("invalid replay path")
	}
	if len(input.Headers) > 64 {
		return input, errors.New("replay header count exceeded")
	}
	for name, value := range input.Headers {
		if !token(name) || len(value) > 8192 || strings.ContainsAny(value, "\r\n\x00") {
			return input, errors.New("invalid replay header")
		}
	}
	return input, nil
}
