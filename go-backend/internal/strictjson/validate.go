// Package strictjson validates private source/operator envelopes without silently
// repairing Unicode or allowing duplicate fields to shadow review bindings.
package strictjson

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"strconv"
	"unicode/utf8"
)

func Validate(raw []byte) error {
	if !utf8.Valid(raw) || !json.Valid(raw) {
		return errors.New("invalid UTF-8 JSON")
	}
	for i := 0; i < len(raw); i++ {
		if raw[i] != '"' {
			continue
		}
		i++
		for i < len(raw) && raw[i] != '"' {
			if raw[i] != '\\' {
				i++
				continue
			}
			if raw[i+1] != 'u' {
				i += 2
				continue
			}
			code, _ := strconv.ParseUint(string(raw[i+2:i+6]), 16, 16)
			if code >= 0xdc00 && code <= 0xdfff {
				return errors.New("unpaired UTF-16 low surrogate")
			}
			if code >= 0xd800 && code <= 0xdbff {
				if i+11 >= len(raw) || raw[i+6] != '\\' || raw[i+7] != 'u' {
					return errors.New("unpaired UTF-16 high surrogate")
				}
				next, err := strconv.ParseUint(string(raw[i+8:i+12]), 16, 16)
				if err != nil || next < 0xdc00 || next > 0xdfff {
					return errors.New("unpaired UTF-16 high surrogate")
				}
				i += 12
				continue
			}
			i += 6
		}
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.UseNumber()
	var walk func(int) error
	walk = func(depth int) error {
		if depth > 64 {
			return errors.New("JSON nesting exceeds 64")
		}
		token, err := d.Token()
		if err != nil {
			return err
		}
		delim, ok := token.(json.Delim)
		if !ok {
			return nil
		}
		switch delim {
		case '{':
			seen := map[string]bool{}
			for d.More() {
				k, err := d.Token()
				if err != nil {
					return err
				}
				key, ok := k.(string)
				if !ok || seen[key] {
					return errors.New("duplicate JSON object key")
				}
				seen[key] = true
				if err = walk(depth + 1); err != nil {
					return err
				}
			}
		case '[':
			for d.More() {
				if err = walk(depth + 1); err != nil {
					return err
				}
			}
		default:
			return errors.New("unexpected JSON delimiter")
		}
		_, err = d.Token()
		return err
	}
	if err := walk(0); err != nil {
		return err
	}
	if _, err := d.Token(); err != io.EOF {
		return errors.New("trailing JSON")
	}
	return nil
}
