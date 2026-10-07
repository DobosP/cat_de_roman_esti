import * as fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { gzipSync, brotliCompressSync } from "node:zlib";
import { createHash } from "node:crypto";
import { chromium } from "../frontend/node_modules/playwright/index.mjs";
import AxeBuilder from "../frontend/node_modules/@axe-core/playwright/dist/index.mjs";

const root = process.cwd(), capture = process.argv[2] === "capture";
const output = capture ? "baselines/cat" : ".gate/full/baseline-comparison";
fs.mkdirSync(output, { recursive: true });
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const routes = ["/", "/intrusul", "/perechi", "/conexiuni", "/alchimie?mode=challenges", "/alchimie?mode=explore", "/cald-rece", "/lant", "/clasament"];
const source = fs.existsSync("frontend/dist/.vite/manifest.json") ? "frontend/dist" : "cat_de_roman_esti/web/static";
const manifest = JSON.parse(fs.readFileSync(`${source}/.vite/manifest.json`));
const sizes = Object.fromEntries(Object.entries(manifest).map(([entry, item]) => {
  const data = fs.readFileSync(`${source}/${item.file}`);
  return [entry, { file: item.file, bytes: data.length, gz: gzipSync(data).length, br: brotliCompressSync(data).length }];
}));
const cssFiles = [...new Set(Object.values(manifest).flatMap((item) => [...item.css || [], ...(item.file.endsWith(".css") ? [item.file] : [])]))].sort();
const css = cssFiles.map((file) => {
  const data = fs.readFileSync(`${source}/${file}`);
  return { file, bytes: data.length, gz: gzipSync(data).length, br: brotliCompressSync(data).length };
});
const cssTotal = css.reduce((sum, item) => sum + item.gz, 0);
const closures = Object.fromEntries(Object.keys(manifest).map((entry) => {
  const entries = new Set(), files = new Set();
  function visit(key) { if (entries.has(key)) return; entries.add(key); const item = manifest[key]; files.add(item.file); for (const file of item.css || []) files.add(file); for (const dependency of item.imports || []) visit(dependency); }
  visit(entry);
  const measured = [...files].sort().map((file) => { const data = fs.readFileSync(`${source}/${file}`); return { file, gz: gzipSync(data).length, br: brotliCompressSync(data).length }; });
  return [entry, { files: measured, gz: measured.reduce((sum, item) => sum + item.gz, 0), br: measured.reduce((sum, item) => sum + item.br, 0) }];
}));
const axeSource = fs.readFileSync("frontend/node_modules/axe-core/axe.min.js", "utf8");
const axeVersion = JSON.parse(fs.readFileSync("frontend/node_modules/axe-core/package.json")).version;
if (axeVersion !== "4.14.0") throw new Error(`Required axeSource4.14.0 is unavailable (actual ${axeVersion}); retain the original dependency graph until its proof`);
const server = !process.env.GATE_APP_URL ? spawn(process.env.CDR_NATIVE_BINARY, ["-listen", "127.0.0.1:8138"], { cwd: root, stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, CAT_ACCOUNTS_ENABLED: "0", CAT_SUBMISSIONS_ENABLED: "0" } }) : null;
const origin = process.env.GATE_APP_URL || "http://127.0.0.1:8138";
if (server) { server.stdout.on("data", (data) => process.stderr.write(data)); server.stderr.on("data", (data) => process.stderr.write(data)); }
const browser = await chromium.launch();
try {
  let ready = false;
  for (let tries = 0; tries < 100; tries++) {
    try { if ((await fetch(`${origin}/api/health`)).ok) { ready = true; break; } } catch { /* bounded startup polling */ }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  if (!ready) throw new Error("Actual baseline server did not start");
  const pages = [];
  for (const [index, route] of routes.entries()) {
    const page = await browser.newPage({ viewport: { width: 1000, height: 800 }, reducedMotion: "reduce", locale: "ro-RO", timezoneId: "Europe/Bucharest" });
    await page.goto(origin + route);
    await page.locator(".screen").first().waitFor();
    await page.waitForFunction(() => document.querySelector(".screen") && getComputedStyle(document.querySelector(".screen")).opacity === "1");
    const name = `route-${index}.png`, image = await page.screenshot({ path: `${output}/${name}`, fullPage: true });
    const axe = await new AxeBuilder({ page, axeSource }).analyze();
    const fingerprint = axe.violations.map((violation) => ({ id: violation.id, impact: violation.impact, targets: violation.nodes.map((node) => node.target) }));
    pages.push({ route, screenshot: `${output}/${name}`, sha256: hash(image), axe: fingerprint });
    await page.close();
  }
  // Vitals are measured by the actual library, loaded before page JS, under the
  // required CDP throttle. Missing tooling cannot become fabricated timing values.
  const vitalsSource = fs.readFileSync("frontend/node_modules/web-vitals/dist/web-vitals.iife.js", "utf8");
  const vitals = [];
  for (const [route, selector] of [["/conexiuni", ".connections-grid button"], ["/alchimie?mode=challenges", ".alchemy-inventory-grid button"]]) {
    const runs = [];
    for (let run = 0; run < 5; run++) {
      const page = await browser.newPage({ viewport: { width: 1000, height: 800 }, reducedMotion: "reduce" });
      const cdp = await page.context().newCDPSession(page);
      await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
      await cdp.send("Network.enable");
      await cdp.send("Network.emulateNetworkConditions", { offline: false, latency: 150, downloadThroughput: 1600 * 1000 / 8, uploadThroughput: 750 * 1000 / 8 });
      await page.addInitScript({ content: `${vitalsSource}\nwindow.__catVitals={};webVitals.onLCP(m=>window.__catVitals.lcp=m.value,{reportAllChanges:true});webVitals.onINP(m=>window.__catVitals.inp=m.value,{reportAllChanges:true});webVitals.onCLS(m=>window.__catVitals.cls=m.value,{reportAllChanges:true});` });
      await page.goto(origin + route);
      await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
      const button = page.locator(selector).first(); await button.waitFor(); await button.click();
      if (route.startsWith("/alchimie")) {
        await page.locator(selector).nth(1).click();
      }
      await page.waitForTimeout(1000);
      await page.evaluate(() => document.dispatchEvent(new Event("visibilitychange")));
      const observed = await page.evaluate(() => window.__catVitals);
      if (!Number.isFinite(observed.lcp) || !Number.isFinite(observed.inp)) throw new Error("Actual LCP/INP did not arrive from web-vitals");
      runs.push(observed); await page.close();
    }
    const median = (key) => runs.map((item) => item[key]).sort((a, b) => a - b)[2];
    vitals.push({ route, runs, median: { lcp: median("lcp"), inp: median("inp"), cls: median("cls") } });
  }
  const report = { schema: 1, mode: capture ? "capture" : "verify", sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, toolchain_digest: process.env.TOOLCHAIN_DIGEST, sizes, closures, css, cssTotal, pages, axeVersion, vitals, method: { runs: 5, reducedMotion: "reduce", cpu: 4, rtt_ms: 150, down_kbps: 1600 } };
  fs.writeFileSync(`${output}/capture.json`, JSON.stringify(report, null, 2) + "\n");
  if (!capture) {
    const baseline = JSON.parse(fs.readFileSync("baselines/cat/capture.json"));
    if (JSON.stringify(baseline.pages.map((item) => [item.route, item.axe])) !== JSON.stringify(pages.map((item) => [item.route, item.axe]))) throw new Error("Axe or route fingerprint changed");
    for (const [index, page] of pages.entries()) {
      const original = baseline.pages[index];
      if (original.route !== page.route || !fs.readFileSync(original.screenshot).equals(fs.readFileSync(page.screenshot))) throw new Error(`Exact original screenshot pixels changed: ${page.route}`);
    }
    for (const [index, item] of vitals.entries()) for (const key of ["lcp", "inp"]) {
      const expected = baseline.vitals[index].median[key];
      if (Math.abs(item.median[key] - expected) > Math.max(expected * .1, 50)) throw new Error(`Vitals baseline mismatch: ${item.route} ${key}`);
    }
  }
  process.stdout.write(JSON.stringify(report) + "\n");
} finally { await browser.close(); server?.kill("SIGTERM"); }
