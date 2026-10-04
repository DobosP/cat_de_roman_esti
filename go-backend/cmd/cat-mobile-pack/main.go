package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/hopcli"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/mobilepack"
	"os"
	"path/filepath"
	"reflect"
)

func run() error {
	root := flag.String("root", "..", "repository root")
	fixture := flag.String("fixture", "", "input KG fixture")
	out := flag.String("out", "", "output public app-pack")
	check := flag.Bool("check", false, "compare public contract without writing")
	flag.Parse()
	if flag.NArg() != 0 {
		return errors.New("unexpected argument")
	}
	if *fixture == "" {
		*fixture = filepath.Join(*root, "cat_de_roman_esti/fixtures/kg_sample.json")
	}
	if *out == "" {
		*out = filepath.Join(*root, "tests/fixtures/cat_mobile_app_pack_contract.json")
	}
	b, err := hopcli.ReadFixture(*fixture)
	if err != nil {
		return err
	}
	data, err := mobilepack.Bytes(b.Raw)
	if err != nil {
		return err
	}
	if *check {
		existing, err := os.ReadFile(*out)
		if err != nil {
			return err
		}
		var a, b any
		if err = json.Unmarshal(existing, &a); err != nil {
			return err
		}
		if err = json.Unmarshal(data, &b); err != nil {
			return err
		}
		if !reflect.DeepEqual(a, b) {
			return errors.New("public mobile app-pack is stale")
		}
		fmt.Println("public mobile app-pack current")
		return nil
	}
	if bytes.Contains(data, []byte("solution_path")) || bytes.Contains(data, []byte("hint_neighbors")) {
		return errors.New("private helpers escaped public projection")
	}
	f, err := os.CreateTemp(filepath.Dir(*out), ".mobile-*")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	if err = f.Chmod(0644); err == nil {
		_, err = f.Write(data)
	}
	if err == nil {
		err = f.Sync()
	}
	ce := f.Close()
	if err != nil {
		return err
	}
	if ce != nil {
		return ce
	}
	return os.Rename(name, *out)
}
func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "cat-mobile-pack:", err)
		os.Exit(1)
	}
}
