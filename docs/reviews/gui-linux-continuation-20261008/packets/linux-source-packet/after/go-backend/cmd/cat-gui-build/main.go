// cat-gui-build bakes GUI identity before compiling the owning app image.
package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/guibuild"
)

func main() {
	root := flag.String("root", "", "repository build root")
	sha := flag.String("sha", "", "canonical wrapper Git SHA")
	tree := flag.String("tree-sha256", "", "canonical wrapper source snapshot SHA256")
	flag.Parse()
	if *root == "" || *sha == "" || *tree == "" || flag.NArg() != 0 {
		fmt.Fprintln(os.Stderr, "explicit root, sha and tree-sha256 flags are required")
		os.Exit(2)
	}
	if err := guibuild.Generate(*root, *sha, *tree); err != nil {
		fmt.Fprintln(os.Stderr, "GUI build identity generation failed:", err)
		os.Exit(1)
	}
}
