// budget reads committed limits and an explicit route-to-asset binding file.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/DobosP/roedu-ui/web-kit/budget"
	"github.com/DobosP/roedu-ui/web-kit/routes"
)

func readJSON(filename string, value any) error {
	data, err := os.ReadFile(filename)
	if err != nil { return err }
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(value); err != nil { return err }
	if err := decoder.Decode(new(any)); err != io.EOF { return fmt.Errorf("trailing route JSON data") }
	return nil
}

// run has no default paths or limit flags. Routes must be the actual inventory
// emitted by the Go application's routes.Export adapter, not URL probes.
func run(args []string, stdout io.Writer) error {
	flags := flag.NewFlagSet("budget", flag.ContinueOnError)
	flags.SetOutput(stdout)
	budgetsPath := flags.String("budgets", "", "committed budgets.json")
	manifestPath := flags.String("manifest", "", "actual Vite manifest, relative to --assets")
	assetPath := flags.String("assets", "", "directory containing the actual built assets")
	configPath := flags.String("config", "", "explicit route-to-asset binding JSON")
	routesPath := flags.String("routes", "", "Go-exported route inventory JSON")
	outputPath := flags.String("out", "", "measurement JSON output")
	if err := flags.Parse(args); err != nil { return err }
	if flags.NArg() != 0 || *budgetsPath == "" || *manifestPath == "" || *assetPath == "" || *configPath == "" || *routesPath == "" || *outputPath == "" {
		return fmt.Errorf("required: --budgets --manifest --assets --config --routes --out; no positional arguments")
	}
	limitsData, err := os.ReadFile(*budgetsPath)
	if err != nil { return err }
	limits, err := budget.Load(limitsData)
	if err != nil { return err }
	configData, err := os.ReadFile(*configPath)
	if err != nil { return err }
	config, err := budget.LoadConfig(configData)
	if err != nil { return err }
	manifest, err := budget.LoadManifest(os.DirFS(*assetPath), *manifestPath)
	if err != nil { return err }
	var table []routes.Route
	if err := readJSON(*routesPath, &table); err != nil { return err }
	report, err := budget.Evaluate(limits, manifest, table, config)
	if err != nil { return err }
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil { return err }
	data = append(data, '\n')
	if err := os.MkdirAll(filepath.Dir(*outputPath), 0755); err != nil { return err }
	if err := os.WriteFile(*outputPath, data, 0644); err != nil { return err }
	if _, err := stdout.Write(data); err != nil { return err }
	if report.Status != "pass" { return fmt.Errorf("route budgets exceeded committed limits") }
	return nil
}

func main() {
	if err := run(os.Args[1:], os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
