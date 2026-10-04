// cat-browser-plan runs only in the private browser test process.
package main

import (
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/browserplan"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"os"
	"strings"
)

func run() error {
	c, err := content.Load()
	if err != nil {
		return err
	}
	args := os.Args[1:]
	if len(args) == 0 {
		return fmt.Errorf("usage: cat-browser-plan GAME [PACK_ID] [--daily=DAY] | --caption PACK_ID | --starts")
	}
	var value any
	if args[0] == "--starts" {
		starts := map[string]any{}
		for _, game := range browserplan.Games {
			p, e := browserplan.Solution(c, game, "", "")
			if e != nil {
				return e
			}
			starts[game] = p.Initial
		}
		value = starts
	} else if args[0] == "--caption" {
		if len(args) != 2 {
			return fmt.Errorf("--caption requires one pack ID")
		}
		value, err = browserplan.CaptionJourney(c, args[1])
	} else {
		game, packID, daily := args[0], "", ""
		for _, a := range args[1:] {
			if strings.HasPrefix(a, "--daily=") {
				daily = strings.TrimPrefix(a, "--daily=")
			} else if packID == "" {
				packID = a
			} else {
				return fmt.Errorf("unexpected planner argument")
			}
		}
		value, err = browserplan.Solution(c, game, packID, daily)
	}
	if err != nil {
		return err
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	return enc.Encode(value)
}
func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
