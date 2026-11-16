// Authored final M0 replacements, NOT RUN. History is explicit fictional local
// presentation data. Static-closure assertions compare genuine build artifacts
// with served bytes; lazy startup requests are permitted, not mistaken for imports.
import { test, expect } from "@playwright/test";
import { createHash } from "node:crypto";
import { existsSync, lstatSync, readFileSync, realpathSync } from "node:fs";
import { resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { collectInitialBundleFiles } from "../scripts/check-bundle-budget.mjs";

const root = fileURLToPath(new URL("../../", import.meta.url));
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");

function artifactBytes(directory, relative) {
  expect(typeof relative).toBe("string");
  expect(relative.length).toBeGreaterThan(0);
  const parts = relative.split("/");
  expect(parts.every((part) => part && part !== "." && part !== ".." && !part.includes("\\"))).toBe(true);
  const absolute = resolve(directory, ...parts);
  expect(absolute.startsWith(resolve(directory) + sep)).toBe(true);
  let current = resolve(directory);
  expect(realpathSync(current)).toBe(current);
  for (const part of parts) {
    current = resolve(current, part);
    expect(lstatSync(current).isSymbolicLink()).toBe(false);
  }
  expect(lstatSync(absolute).isFile()).toBe(true);
  return readFileSync(absolute);
}

test("the actual served build keeps optional account/game chunks outside static imports while binding emitted bytes", async ({ page, request }, testInfo) => {
  const requested = new Set();
  page.on("request", (item) => requested.add(new URL(item.url()).pathname));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
  const origin = new URL(page.url()).origin;
  const modules = await page.locator("script[type=module][src]").evaluateAll((elements) => elements.map((element) => element.src));
  expect(modules.length).toBeGreaterThan(0);
  const candidates = ["frontend/dist", "cat_de_roman_esti/web/static", "go-backend/embedfs/dist"];
  const matches = [];
  for (const relative of candidates) {
    const directory = resolve(root, relative), manifestFile = resolve(directory, ".vite/manifest.json");
    if (!existsSync(manifestFile)) continue;
    const manifestBytes = artifactBytes(directory, ".vite/manifest.json"), manifest = JSON.parse(manifestBytes);
    const entries = Object.entries(manifest).filter(([, row]) => row.isEntry);
    for (const [entry, row] of entries) {
      const module = modules.find((url) => {
        const parsed = new URL(url); return parsed.origin === origin && parsed.pathname.endsWith("/" + row.file);
      });
      if (!module) continue;
      const prefix = new URL(module).pathname.slice(0, -row.file.length);
      const response = await request.get(module);
      expect(response.status()).toBe(200);
      if (!(await response.body()).equals(artifactBytes(directory, row.file))) continue;
      matches.push({ directory, relative, manifest, manifestBytes, entry, prefix });
    }
  }
  expect(matches.length, "A genuine local build manifest must bind the actually served module bytes").toBeGreaterThan(0);
  for (const match of matches) {
    const staticOwners = new Set(), dynamicImports = new Set();
    function manifestRow(key) {
      expect(typeof key).toBe("string");
      expect(key.length).toBeGreaterThan(0);
      expect(Object.hasOwn(match.manifest, key)).toBe(true);
      const row = match.manifest[key];
      expect(row !== null && typeof row === "object" && !Array.isArray(row)).toBe(true);
      expect(typeof row.file).toBe("string");
      expect(row.file.length).toBeGreaterThan(0);
      return row;
    }
    function visitStaticOwner(key) {
      const row = manifestRow(key);
      if (staticOwners.has(key)) return;
      staticOwners.add(key);
      for (const field of ["imports", "dynamicImports"]) {
        const references = row[field] === undefined ? [] : row[field];
        expect(Array.isArray(references)).toBe(true);
        for (const reference of references) {
          if (field === "imports") visitStaticOwner(reference);
          else {
            manifestRow(reference);
            dynamicImports.add(reference);
          }
        }
      }
    }
    // Follow only the genuine served entry's static owners, never dynamic edges.
    visitStaticOwner(match.entry);
    const closure = collectInitialBundleFiles(match.manifest);
    expect(closure.length).toBeGreaterThan(0);
    // Every M3 screen is current. Home is selected lazily, but its entire
    // static closure and the mandatory AccountBar are charged for this page.
    const ui = await page.locator("html").getAttribute("data-ui");
    const ported = ["src/components/AccountBar.tsx", "src/screens/Home.tsx", "src/screens/Intrusul.tsx", "src/screens/Perechi.tsx", "src/screens/Conexiuni.tsx", "src/screens/Alchimie.tsx", "src/screens/CaldRece.tsx", "src/screens/Lant.tsx", "src/screens/Ranking.tsx"];
    const unported = [];
    expect(ui).toBe("preact");
    for (const key of unported) expect(match.manifest[key]).toBeUndefined();
    const history = match.manifest["src/components/ResultsHistory.tsx"];
    expect(history?.isDynamicEntry).toBe(true);
    expect(closure).not.toContain(history.file);
    expect(requested.has(match.prefix + history.file)).toBe(false);
    const optional = ported
      .map((key) => {
        const row = match.manifest[key];
        expect(row).toBeDefined();
        expect(row.isDynamicEntry).toBe(true);
        expect(closure).not.toContain(row.file);
        expect(dynamicImports.has(key)).toBe(true);
        return { key, file: row.file };
      });
    const homeClosure = collectInitialBundleFiles(match.manifest, {
      eagerRoots: ["src/components/AccountBar.tsx", "src/screens/Home.tsx"],
    });
    for (const key of ["src/components/AccountBar.tsx", "src/screens/Home.tsx"]) {
      expect(homeClosure).toContain(match.manifest[key].file);
    }
    for (const file of homeClosure) expect(requested.has(match.prefix + file), `Home initial dependency requested: ${file}`).toBe(true);
    for (const key of ["src/screens/AlchimieChallenge.tsx", "src/screens/AlchimieExplore.tsx"]) {
      expect(match.manifest[key], "Alchimie is one lazy route, with no separately emitted mode leaf").toBeUndefined();
    }
    const bound = [];
    for (const file of [...new Set([...homeClosure, ...optional.map(({ file }) => file)])]) {
      const bytes = artifactBytes(match.directory, file), url = new URL(match.prefix + file, origin).href;
      const response = await request.get(url);
      expect(response.status()).toBe(200);
      expect(response.url()).toBe(url);
      expect((await response.body()).equals(bytes)).toBe(true);
      expect(bytes.length).toBeGreaterThan(0);
      bound.push({ file, bytes: bytes.length, sha256: hash(bytes) });
    }
    await testInfo.attach(`static-closure-${match.relative.replaceAll("/", "-")}`, {
      body: JSON.stringify({ scope: "Observed build artifact/HTTP byte integrity, not a no-startup-fetch claim",
        artifact_root: match.relative, manifest_sha256: hash(match.manifestBytes), entry: match.entry,
        initial_static_files: closure, home_initial_files: homeClosure, optional_dynamic_files: optional, bound }, null, 2), contentType: "application/json",
    });
  }
});
