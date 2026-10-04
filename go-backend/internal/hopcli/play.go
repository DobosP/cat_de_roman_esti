package hopcli

import (
	"bufio"
	"fmt"
	"io"
	"sort"
	"strconv"
	"strings"
)

func Categories(b *Bundle) []string {
	seen := map[string]bool{}
	for _, p := range b.Puzzles {
		seen[p.Category] = true
	}
	out := []string{}
	for c := range seen {
		out = append(out, c)
	}
	sort.Strings(out)
	return out
}
func Choose(label string, options []string, def string, in *bufio.Scanner, out io.Writer) string {
	fmt.Fprintf(out, "\n%s:\n", label)
	for i, opt := range options {
		marker := ""
		if opt == def {
			marker = "  (default)"
		}
		fmt.Fprintf(out, "  [%d] %s%s\n", i+1, opt, marker)
	}
	for {
		fmt.Fprintf(out, "%s > ", label)
		if !in.Scan() {
			return def
		}
		raw := strings.ToLower(strings.TrimSpace(in.Text()))
		if raw == "" {
			return def
		}
		n, err := strconv.Atoi(raw)
		if err == nil && n >= 1 && n <= len(options) {
			return options[n-1]
		}
		for _, s := range options {
			if raw == s {
				return s
			}
		}
		fmt.Fprintf(out, "  ? please pick 1-%d (or a name)\n", len(options))
	}
}
func Play(g *Game, in *bufio.Scanner, out io.Writer, maxTurns int) map[string]any {
	fmt.Fprintf(out, "\nStart: %s  ->  Target: %s\nType a number to hop, 'q' to quit.\n", g.Graph.Label(g.Current()), g.Graph.Label(g.Puzzle.TargetID))
	for turn := 0; !g.Won() && turn < maxTurns; turn++ {
		cur, tgt := g.Graph.Node(g.Current()), g.Graph.Node(g.Puzzle.TargetID)
		fmt.Fprintf(out, "\n%s\n  HOPS: %d   PAR: %d   MODE: %s\n  TARGET : %s  (%s)\n", strings.Repeat("=", 64), g.Hops(), g.Puzzle.Par, g.Mode, tgt.LabelRO, tgt.Category)
		if tgt.Description != "" {
			fmt.Fprintf(out, "           %s\n", tgt.Description)
		}
		fmt.Fprintf(out, "  CURRENT: %s  (%s)\n", cur.LabelRO, cur.NodeType)
		if cur.Description != "" {
			fmt.Fprintf(out, "           %s\n", cur.Description)
		}
		fmt.Fprintln(out, strings.Repeat("-", 64))
		opts := g.Options()
		hints := map[string]bool{}
		for _, id := range g.Hints() {
			hints[id] = true
		}
		if len(opts) == 0 {
			fmt.Fprintln(out, "  (dead end — no outgoing edges from here)")
		} else {
			fmt.Fprintln(out, "  Neighbours you can hop to:")
		}
		for i, n := range opts {
			fmt.Fprintf(out, "  [%d] %s", i+1, g.Graph.Label(n.ID))
			if g.Mode == "easy" && n.Edge.LabelRO != "" {
				fmt.Fprintf(out, " — %s", n.Edge.LabelRO)
			}
			if hints[n.ID] {
				fmt.Fprint(out, "   <hint>")
			}
			fmt.Fprintln(out)
		}
		fmt.Fprint(out, "\nhop > ")
		if !in.Scan() {
			fmt.Fprintln(out, "\n(input closed — leaving)")
			break
		}
		raw := strings.TrimSpace(in.Text())
		if raw == "q" || raw == "quit" || raw == "exit" {
			fmt.Fprintln(out, "Bye.")
			break
		}
		n, err := strconv.Atoi(raw)
		if err != nil || n < 1 || n > len(opts) {
			fmt.Fprintf(out, "  ? enter 1-%d or 'q'\n", len(opts))
			continue
		}
		result := g.Hop(opts[n-1].ID)
		if !result.OK {
			fmt.Fprintf(out, "  ✗ invalid hop: %s\n", result.Reason)
			continue
		}
		fmt.Fprintf(out, "  → hopped to %s\n", g.Graph.Label(opts[n-1].ID))
	}
	fmt.Fprintf(out, "\n%s\n", strings.Repeat("#", 64))
	if g.Won() {
		fmt.Fprintf(out, "  WIN! %d hops (par %d).  SCORE: %d\n", g.Hops(), g.Puzzle.Par, g.Score())
	} else {
		fmt.Fprintf(out, "  Not solved. %d hops taken.  SCORE: %d\n", g.Hops(), g.Score())
	}
	fmt.Fprintln(out, strings.Repeat("#", 64))
	return g.Summary()
}
