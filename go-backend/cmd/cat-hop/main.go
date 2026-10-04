// cat-hop is the native original terminal semantic-hop client.
package main

import (
	"bufio"
	"context"
	"flag"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/hopcli"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/roeduclient"
	"os"
	"path/filepath"
	"time"
)

func run() error {
	offline := flag.Bool("offline", false, "use an offline fixture")
	fixture := flag.String("fixture", "", "offline fixture path")
	root := flag.String("root", "..", "repository root")
	category := flag.String("category", "", "game category")
	difficulty := flag.String("difficulty", "", "easy or hard")
	defaultBase := os.Getenv("ROEDU_API_URL")
	if defaultBase == "" {
		defaultBase = "http://127.0.0.1:8077"
	}
	base := flag.String("api-url", defaultBase, "RO-EDU base URL")
	list := flag.Bool("list", false, "list categories/puzzles")
	flag.Parse()
	if flag.NArg() != 0 {
		return fmt.Errorf("unexpected argument")
	}
	if *difficulty != "" && *difficulty != "easy" && *difficulty != "hard" {
		return fmt.Errorf("difficulty must be easy or hard")
	}
	if *fixture == "" {
		*fixture = filepath.Join(*root, "cat_de_roman_esti/fixtures/kg_sample.json")
	}
	var b *hopcli.Bundle
	var err error
	if *offline {
		if *fixture == "" {
			*fixture = filepath.Join(*root, "cat_de_roman_esti/fixtures/kg_sample.json")
		}
		b, err = hopcli.ReadFixture(*fixture)
	} else {
		c, e := roeduclient.New(*base, os.Getenv("ROEDU_API_KEY"), roeduclient.DefaultLimits())
		if e != nil {
			return e
		}
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
		defer cancel()
		var fallback bool
		b, fallback, err = hopcli.LoadOnline(ctx, c, *fixture, *category, *difficulty)
		if fallback {
			fmt.Fprintln(os.Stderr, "! server health unavailable; using the offline fixture")
		}
	}
	if err != nil {
		return err
	}
	if len(b.Puzzles) == 0 {
		return fmt.Errorf("no puzzles available")
	}
	cats := hopcli.Categories(b)
	if *list {
		fmt.Println("Categories:", cats)
		fmt.Printf("Puzzles available: %d\n", len(b.Puzzles))
		for _, cat := range cats {
			count := 0
			for _, p := range b.Puzzles {
				if p.Category == cat {
					count++
				}
			}
			fmt.Printf("  %s: %d\n", cat, count)
		}
		return nil
	}
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1024), 65536)
	if *category == "" {
		*category = hopcli.Choose("Pick a category", cats, cats[0], scanner, os.Stdout)
	}
	if *difficulty == "" {
		*difficulty = hopcli.Choose("Pick a difficulty", []string{"easy", "hard"}, "easy", scanner, os.Stdout)
	}
	for _, p := range b.Puzzles {
		if p.Category == *category && p.Difficulty == *difficulty {
			g, e := hopcli.New(b.Graph, p, *difficulty)
			if e != nil {
				return e
			}
			hopcli.Play(g, scanner, os.Stdout, 100)
			return scanner.Err()
		}
	}
	return fmt.Errorf("no matching category/difficulty puzzle")
}
func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "cat-hop:", err)
		os.Exit(1)
	}
}
