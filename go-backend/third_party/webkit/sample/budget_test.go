package main

import (
    "encoding/json"
    "io/fs"
    "os"
    "path/filepath"
    "testing"

    "github.com/DobosP/roedu-ui/web-kit/budget"
    "github.com/DobosP/roedu-ui/web-kit/routes"
)

// TestRouteBudgets qualifies this actual router and embedded generated assets.
// It requires a fresh gate budget build; absent output is an error, never a skip.
func TestRouteBudgets(t *testing.T) {
    root := filepath.Join("..", "..")
    target := "unit"
    if os.Getenv("GATE_APP_URL") != "" { target = "full" }
    limitsBytes, err := os.ReadFile(filepath.Join(root, "budgets.json"))
    if err != nil { t.Fatal(err) }
    limits, err := budget.Load(limitsBytes)
    if err != nil { t.Fatal(err) }
    bindingBytes, err := os.ReadFile(filepath.Join(root, ".gate", target, "budget-bindings.json"))
    if err != nil { t.Fatal(err) }
    binding, err := budget.LoadConfig(bindingBytes)
    if err != nil { t.Fatal(err) }
    files, err := fs.Sub(embedded, "embedfs/dist")
    if err != nil { t.Fatal(err) }
    manifest, err := budget.LoadManifest(files, ".vite/manifest.json")
    if err != nil { t.Fatal(err) }
    mux, _, err := newRouterWithOptions(embedded, handlerOptions{})
    if err != nil { t.Fatal(err) }
    report := budget.TestRouteBudgets(t, limits, manifest, routes.Export(mux), binding)
    if len(report.Routes) != len(pageRoutes()) { t.Fatal("every real sample page must be measured") }
    if report.GlobalCSS.Status != "recorded" && limits.GlobalCSS.LimitGZ == nil { t.Fatal("null CSS limit must record actual bytes") }
    if data, err := json.Marshal(report); err != nil || len(data) == 0 { t.Fatal("actual budget report required") }
}
