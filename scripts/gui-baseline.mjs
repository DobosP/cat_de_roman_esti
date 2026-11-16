import * as fs from "node:fs";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { gzipSync, brotliCompressSync } from "node:zlib";
import { createHash } from "node:crypto";
import { ensureBaselineDependencies } from "./gui-baseline-deps.mjs";
import { chromium } from "../frontend/node_modules/playwright/index.mjs";
import AxeBuilder from "../frontend/node_modules/@axe-core/playwright/dist/index.mjs";
import { nativePlan } from "../frontend/e2e/native-plan.mjs";
import { prepareVerification, diagnosticOutput, identifyPage, captureRedesignHomeWitness, recheckVerification,
  redesignOutcomes, redesignSourceHashes, REDESIGN_CASES, REDESIGN_FIXTURE_PATH, REDESIGN_CHECKSUM_PATH,
  writeVerification, deadline } from "./gui-baseline-checks.mjs";

const root = process.cwd(), mode = process.argv[2], originalCapture = mode === "original-capture";
const capture = mode === "capture" || originalCapture;
if (process.argv.length !== 3 || !["capture", "original-capture", "verify", "owner-diagnostic"].includes(mode)) throw new Error("Explicit supported baseline mode required");
const verification = capture ? null : prepareVerification(root, mode);
const output = mode === "owner-diagnostic" ? diagnosticOutput(verification)
  : mode === "original-capture" ? ".gate/gen/original/baseline" : capture ? "baselines/cat" : ".gate/full/baseline-comparison";
fs.mkdirSync(output, { recursive: true });
if (!capture && fs.readdirSync(output).length) throw new Error("Fresh baseline verification evidence required; previous files retained");
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const originalRoutes = ["/", "/intrusul", "/perechi", "/conexiuni", "/alchimie?mode=challenges", "/alchimie?mode=explore", "/cald-rece", "/lant", "/clasament"];
const fixture = originalCapture ? null : JSON.parse(fs.readFileSync(REDESIGN_FIXTURE_PATH));
if (fixture) assert.ok(fixture.schema === 1 && fixture.rules_version === 2 && !Number.isNaN(Date.parse(fixture.clock)));
const day = fixture?.clock.slice(0, 10);
const sources = originalCapture ? null : redesignSourceHashes(root);
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
const quality = "tools/gui-baseline-quality";
ensureBaselineDependencies(root);
const axeSource = fs.readFileSync(`${quality}/node_modules/axe-core/axe.min.js`, "utf8");
const axeVersion = JSON.parse(fs.readFileSync(`${quality}/node_modules/axe-core/package.json`)).version;
if (axeVersion !== "4.14.0") throw new Error(`Required axeSource4.14.0 is unavailable (actual ${axeVersion}); retain the original dependency graph until its proof`);
const local = mode === "original-capture" || !process.env.GATE_APP_URL;
const server = local ? spawn(process.env.CDR_NATIVE_BINARY, ["-listen", "127.0.0.1:8138"], { cwd: root, stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, CAT_ACCOUNTS_ENABLED: "0", CAT_SUBMISSIONS_ENABLED: "0" } }) : null;
const origin = local ? "http://127.0.0.1:8138" : process.env.GATE_APP_URL;
if (server) { server.stdout.on("data", (data) => process.stderr.write(data)); server.stderr.on("data", (data) => process.stderr.write(data)); }
const browserOptions = mode === "owner-diagnostic" ? { timeout: 10000 } : {};
const browser = await chromium.launch(browserOptions);
let snapshotBrowser;
let homeWitness = null, homeWitnessFailure = null;
const pages = [];
async function paintReady(page) {
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(Array.from(document.images, (image) => image.decode()));
    await Promise.all(document.getAnimations()
      .filter((animation) => Number.isFinite(animation.effect?.getComputedTiming().endTime))
      .map((animation) => animation.finished.catch(() => {})));
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  });
}

async function fixedPage(screen) {
  const context = await snapshotBrowser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, reducedMotion: "reduce",
    colorScheme: screen.theme, locale: "ro-RO", timezoneId: "Europe/Bucharest" });
  const page = await context.newPage();
  await page.clock.setFixedTime(new Date(fixture.clock));
  await page.addInitScript(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.route("**/api/me", (route) => route.fulfill({ json: { accounts_enabled: false, authenticated: false, user: null } }));
  await page.route("**/api/categories", (route) => route.fulfill({ json: fixture.categories }));
  const counts = { creates: 0, guesses: 0 };
  const refused = [];
  await page.route("**/api/wordgames/**", async (route) => {
    const request = route.request(), url = new URL(request.url());
    const base = "/api/wordgames/" + screen.game + "/games";
    if (url.origin === origin && screen.game && request.method() === "POST" && url.pathname === base && counts.creates === 0 &&
        url.searchParams.get("daily") === day && !url.searchParams.has("category")) {
      counts.creates++;
      await route.fulfill({ json: fixture.starts[screen.game] });
    } else if (url.origin === origin && screen.name === "result" && request.method() === "POST" &&
        url.pathname === base + "/visual-intrusul/guess" && counts.guesses === 0 &&
        request.postDataJSON()?.id === fixture.intrusul_result.request.id) {
      counts.guesses++;
      await route.fulfill({ json: fixture.intrusul_result.body });
    } else {
      refused.push(request.method() + " " + url.pathname);
      await route.abort();
    }
  });
  try {
    const response = await page.goto(origin + screen.route);
    if (verification && screen.key === "home-light") await identifyPage(page, response, verification, output);
    await page.locator(screen.ready).first().waitFor();
    if (screen.game) {
      assert.equal(await page.locator(".game-frame-mode").textContent(), "Jocul zilei");
    }
    if (screen.name === "help") {
      await page.getByRole("button", { name: "Cum se joacă", exact: true }).click();
      await page.getByRole("dialog", { name: "Cum se joacă Intrusul", exact: true }).waitFor();
    }
    if (screen.name === "result") {
      const answer = fixture.intrusul_result.body.solution.intruder.label;
      await page.getByRole("button", { name: answer, exact: true }).click();
      await page.locator(".game-result").waitFor();
      await page.getByText("Perfect", { exact: true }).waitFor();
    }
    // Park the pointer away from the game and help controls after scripted clicks.
    await page.mouse.move(389, 843);
    await paintReady(page);
    assert.equal(await page.evaluate(() => matchMedia("(prefers-color-scheme: dark)").matches), screen.theme === "dark");
    assert.deepEqual(counts, { creates: +Boolean(screen.game), guesses: +(screen.name === "result") });
    assert.deepEqual(refused, [], "Unbound game API request during frozen capture");
    if (verification && screen.key === "home-light") {
      try { homeWitness = await captureRedesignHomeWitness(page, verification); }
      catch (error) { homeWitnessFailure = String(error); }
      writeVerification(verification, output, "home-semantics.json", { status: homeWitness ? "pass" : "fail",
        witness: homeWitness, failure: homeWitnessFailure });
    }
    const name = screen.key + ".png";
    const image = await page.screenshot({
      path: `${output}/${name}`, animations: "disabled", caret: "hide", scale: "css",
    });
    const axe = await new AxeBuilder({ page, axeSource }).analyze();
    const fingerprint = axe.violations.map((violation) => ({ id: violation.id, impact: violation.impact,
      targets: violation.nodes.map((node) => node.target) }));
    pages.push({ key: screen.key, route: screen.route, theme: screen.theme, screenshot: `${output}/${name}`,
      captured_file: `${output}/${name}`, sha256: hash(image), axe: fingerprint });
    process.stderr.write(`Captured redesign ${screen.key}: ${JSON.stringify(fingerprint)}\n`);
  } finally {
    await context.close();
  }
}
try {
  let ready = false;
  for (let tries = 0; tries < 100; tries++) {
    try { if ((await fetch(`${origin}/api/health`)).ok) { ready = true; break; } } catch { /* bounded startup polling */ }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  if (!ready) throw new Error("Actual baseline server did not start");
  if (originalCapture) for (const [index, route] of originalRoutes.entries()) {
    const context = await browser.newContext({ viewport: { width: 1000, height: 800 }, reducedMotion: "reduce", locale: "ro-RO", timezoneId: "Europe/Bucharest" });
    const page = await context.newPage();
    await page.goto(origin + route);
    if (route === "/") await page.locator(".hero-title").waitFor();
    else if (route === "/clasament") {
      await page.locator(".ranking-game-select").waitFor({ state: "attached" });
      await page.getByRole("heading", { name: "🏆 Clasament" }).waitFor();
      await page.waitForFunction(() => !document.querySelector('.ranking-state[aria-busy="true"]'));
    } else if (route.includes("mode=explore")) await page.locator(".alchemy-explore-screen").waitFor();
    else await page.locator(".game-intro").waitFor();
    await page.locator(".screen").first().waitFor();
    await page.waitForFunction(() => document.querySelector(".screen") && getComputedStyle(document.querySelector(".screen")).opacity === "1");
    await page.evaluate(() => document.fonts.ready);
    await page.waitForFunction(() => [...document.querySelectorAll(".game-intro, .game-card, .hero-title span, header > p")].every((element) => getComputedStyle(element).opacity === "1"));
    await page.evaluate(async () => { await Promise.all(document.getAnimations().filter((animation) => Number.isFinite(animation.effect?.getComputedTiming().endTime)).map((animation) => animation.finished.catch(() => {}))); });
    const name = `route-${index}.png`, image = await page.screenshot({ path: `${output}/${name}`, fullPage: true });
    const axe = await new AxeBuilder({ page, axeSource }).analyze();
    const fingerprint = axe.violations.map((violation) => ({ id: violation.id, impact: violation.impact, targets: violation.nodes.map((node) => node.target) }));
    pages.push({ route, screenshot: capture ? `baselines/cat/${name}` : `${output}/${name}`, captured_file: `${output}/${name}`, sha256: hash(image), axe: fingerprint });
    process.stderr.write(`Captured original route ${route}: ${fingerprint.length} axe fingerprints\n`);
    await context.close();
  } else {
    // A complete software raster of the fixed viewport keeps rounded edges
    // repeatable across capture and verification. Historical captures and
    // live vitals measurements use their original browser profile.
    snapshotBrowser = await chromium.launch({
      ...browserOptions,
      args: ["--disable-gpu", "--disable-gpu-compositing", "--disable-skia-runtime-opts",
        "--disable-partial-raster", "--run-all-compositor-stages-before-draw"],
    });
    for (const screen of REDESIGN_CASES) await fixedPage(screen);
    if (capture && pages.some((page) => page.axe.length)) throw new Error("All redesign baseline Axe cases require zero findings");
  }
  // Vitals are measured by the actual library, loaded before page JS, under the
  // required CDP throttle. Missing tooling cannot become fabricated timing values.
  const vitalsSource = fs.readFileSync(`${quality}/node_modules/web-vitals/dist/web-vitals.iife.js`, "utf8");
  const vitalsVersion = JSON.parse(fs.readFileSync(`${quality}/node_modules/web-vitals/package.json`)).version;
  if (vitalsVersion !== "6.2.3") throw new Error("Actual locked web-vitals6.2.3 source required");
  const vitals = [];
  for (const [route, selector] of [["/conexiuni", ".connections-grid button"], ["/alchimie?mode=challenges", ".alchemy-inventory-grid button"]]) {
    const runs = [];
    for (let run = 0; run < 5; run++) {
      const context = await browser.newContext({ viewport: { width: 1000, height: 800 }, reducedMotion: "reduce",
        ...(originalCapture ? {} : { timezoneId: "Europe/Bucharest", locale: "ro-RO", colorScheme: "light" }) });
      const page = await context.newPage();
      const cdp = await page.context().newCDPSession(page);
      await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
      await cdp.send("Network.enable");
      await cdp.send("Network.emulateNetworkConditions", { offline: false, latency: 150, downloadThroughput: 1600 * 1000 / 8, uploadThroughput: 750 * 1000 / 8 });
      const metrics = [];
      await page.exposeBinding("__catVital", (_source, metric) => { metrics.push(metric); });
      // Collect native Event Timing and, for a fast first action, the browser's
      // actual First Input entry. Keep the original capture's probe unchanged.
      const firstInput = originalCapture ? "" : "events.observe({type:'first-input',buffered:true});";
      const entryType = originalCapture ? "" : "entryType:e.entryType,";
      await page.addInitScript({ content: `${vitalsSource}\nwindow.__catVitals={};window.__catEvents=[];const entry=e=>({${entryType}name:e.name,startTime:e.startTime,duration:e.duration,interactionId:e.interactionId||0,target:e.target?.closest?.('button')?.className||e.target?.tagName||'',text:e.target?.closest?.('button')?.textContent?.trim()||''});const events=new PerformanceObserver(list=>window.__catEvents.push(...list.getEntries().map(entry)));events.observe({type:'event',buffered:true,durationThreshold:16});${firstInput}const record=m=>{window.__catVitals[m.name.toLowerCase()]=m.value;window.__catVital({name:m.name,id:m.id,value:m.value,rating:m.rating,entries:m.entries.map(entry)})};webVitals.onLCP(record,{reportAllChanges:true});webVitals.onINP(record,{reportAllChanges:true,durationThreshold:0});webVitals.onCLS(record,{reportAllChanges:true});` });
      // Extra attribution belongs only to the explicit diagnostic measurement.
      if (mode === "owner-diagnostic") {
        await page.addInitScript({ content: "window.__catLcpElements=[];new PerformanceObserver(list=>{for(const e of list.getEntries())window.__catLcpElements.push({startTime:e.startTime,renderTime:e.renderTime,loadTime:e.loadTime,size:e.size,resource:e.url?(new URL(e.url,location.href).origin===location.origin?new URL(e.url,location.href).pathname:'[foreign resource]'):null,element:e.element?{tag:e.element.tagName.toLowerCase(),id:e.element.getAttribute('id'),classes:e.element.getAttribute('class')}:null})}).observe({type:'largest-contentful-paint',buffered:true});" });
      }
      const game = route.startsWith("/alchimie") ? "alchimie" : "conexiuni";
      const createPath = `/api/wordgames/${game}/games`;
      if (originalCapture) await page.route(`**${createPath}?*`, async (request) => { const url = new URL(request.request().url()); url.searchParams.set("seed", "38"); await request.continue({ url: url.toString() }); });
      let creation;
      if (!originalCapture) {
        // Playwright's fixed wall clock also replaces Performance, including its
        // interactionCount accessor. Keep native timing and pin only the daily
        // board selection via the real request to the running server.
        await page.route((url) => url.pathname === createPath, async (request) => {
          const url = new URL(request.request().url());
          if (request.request().method() === "POST") url.searchParams.set("daily", day);
          await request.continue({ url: url.toString() });
        }, { times: 1 });
        creation = page.waitForResponse((reply) =>
          reply.request().method() === "POST" && new URL(reply.url()).pathname === createPath);
      }
      await page.goto(origin + route);
      if (originalCapture) await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
      else {
        const reply = await creation;
        if (!reply.ok() || (await reply.json()).daily !== day) {
          throw new Error(`Actual vitals board for ${game} did not open on ${day}`);
        }
      }
      await page.locator(selector).first().waitFor();
      let actionStarted, actionLabel;
      if (route.startsWith("/alchimie")) {
        const step = nativePlan(originalCapture ? [game] : [game, "--daily=" + day]).steps[0];
        const button = (label) => page.locator(".alchemy-inventory-grid").getByRole("button", { name: new RegExp(`^${label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?:,|$)`) });
        await button(step.labels[0]).click();
        actionStarted = await page.evaluate(() => performance.now()); actionLabel = "Alchimie combine";
        const response = page.waitForResponse((response) => response.request().method() === "POST" && new URL(response.url()).pathname.endsWith("/combine"));
        await button(step.labels[1]).click();
        const reply = await response;
        if (reply.status() !== 200) throw new Error("Actual scripted combine did not succeed");
        const fresh = await reply.json();
        if (!fresh.discovered?.length) throw new Error("Scripted combine must create an earned concept");
        await page.waitForFunction((label) => [...document.querySelectorAll(".alchemy-word")].some((element) => element.textContent.includes(label)), fresh.discovered[0].label);
        await page.waitForFunction(() => !document.querySelector(".alchemy-working"));
      } else {
        actionStarted = await page.evaluate(() => performance.now()); actionLabel = "Conexiuni select";
        await page.locator(selector).first().click();
        await page.locator('.connection-tile[aria-pressed="true"]').waitFor();
      }
      if (originalCapture) {
        await page.waitForFunction(() => Number.isFinite(window.__catVitals.lcp) && Number.isFinite(window.__catVitals.inp));
      }
      try {
        await page.waitForFunction((start) => window.__catEvents.some((entry) => entry.interactionId > 0 &&
          entry.startTime >= start && /connection-tile|alchemy-word/.test(entry.target)), actionStarted);
      } catch (error) {
        const received = await page.evaluate(() => ({ events: window.__catEvents, vitals: window.__catVitals,
          interactionCount: performance.interactionCount }));
        throw new Error(`No real performance entry for ${actionLabel} run ${run + 1}: ${JSON.stringify(received)}`, { cause: error });
      }
      if (!originalCapture) {
        // The browser's action observer can run before web-vitals processes its
        // entries in requestIdleCallback. Wait for the genuine first report
        // before leaving, then keep the pagehide-finalized values below.
        await page.waitForFunction(() => Number.isFinite(window.__catVitals.lcp) &&
          Number.isFinite(window.__catVitals.inp), undefined, { polling: 100 });
      }
      const observed = await page.evaluate(() => ({ ...window.__catVitals, events: window.__catEvents }));
      if (mode === "owner-diagnostic") {
        Object.assign(observed, await page.evaluate(() => ({
          lcp_elements: window.__catLcpElements,
          resources: performance.getEntriesByType("resource").filter((entry) => { const url = new URL(entry.name, location.href); return url.origin === location.origin && [".woff2", ".css", ".js"].some((suffix) => url.pathname.endsWith(suffix)); })
            .map((entry) => ({ path: new URL(entry.name, location.href).pathname, initiatorType: entry.initiatorType, startTime: entry.startTime, duration: entry.duration,
              requestStart: entry.requestStart, responseStart: entry.responseStart, responseEnd: entry.responseEnd, transferSize: entry.transferSize, encodedBodySize: entry.encodedBodySize, decodedBodySize: entry.decodedBodySize })),
          fonts: [...document.fonts].map((font) => ({ family: font.family, status: font.status, weight: font.weight, unicodeRange: font.unicodeRange })) })));
      }
      if (originalCapture && (!Number.isFinite(observed.lcp) || !Number.isFinite(observed.inp))) throw new Error("Actual LCP/INP did not arrive from web-vitals");
      const actionEntries = observed.events.filter((entry) => entry.interactionId > 0 && entry.startTime >= actionStarted && /connection-tile|alchemy-word/.test(entry.target));
      // Genuine pagehide finalizes the library callbacks; no synthetic lifecycle event.
      await page.goto("about:blank");
      const final = (name) => metrics.filter((metric) => metric.name === name).at(-1)?.value;
      const lcp = final("LCP"), inp = final("INP"), cls = final("CLS");
      if (!originalCapture && ![lcp, inp, cls].every((value) => Number.isFinite(value) && value >= 0)) {
        throw new Error(`Missing final native web-vitals for ${actionLabel} run ${run + 1}: ${JSON.stringify(metrics)}`);
      }
      runs.push({ ...observed, lcp, inp, cls: originalCapture ? cls ?? 0 : cls,
        action: { name: actionLabel, startTime: actionStarted, entries: actionEntries,
          latency_ms: Math.max(...actionEntries.map((entry) => entry.duration)) }, metrics });
      await context.close();
      process.stderr.write(`Measured ${actionLabel} run ${run + 1}/5 with actual callbacks and action entries\n`);
    }
    const median = (key) => runs.map((item) => item[key]).sort((a, b) => a - b)[2];
    vitals.push({ route, runs, median: { lcp: median("lcp"), inp: median("inp"), cls: median("cls") } });
  }
  // M2 binding migration: the active SDK archive is whatever the manifest pointer selects; the
  // original 0.3.0 archive is bound from the frozen original receipt, never from the vendor tree.
  const activeSdk = /^file:(vendor\/roedu-ui-\d+\.\d+\.\d+\.tgz)$/.exec(JSON.parse(fs.readFileSync("frontend/package.json")).dependencies?.["@roedu/ui"] ?? "")?.[1];
  if (!activeSdk) throw new Error("Active @roedu/ui vendor pointer required");
  const inputs = Object.fromEntries(["frontend/package.json", "frontend/package-lock.json", `frontend/${activeSdk}`, "docs/reviews/gui-original-react/original-ui-0.3.0.tgz", `${quality}/package.json`, `${quality}/package-lock.json`].map((file) => [file, hash(fs.readFileSync(file))]));
  const report = { schema: 1, ...(originalCapture ? {} : { design: 2, clock: fixture.clock, vitals_daily: day, source_sha256: sources }), mode: capture ? "capture" : mode, proof_scope: mode === "original-capture" ? "pinned-gen-original-runner-built-server" : mode === "owner-diagnostic" ? "owner-shell-baseline-diagnostic-only-not-full-receipt" : "actual-app-image", sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, toolchain_digest: process.env.TOOLCHAIN_DIGEST, inputs, sizes, closures, css, cssTotal, pages, axeVersion, axe_source_sha256: hash(axeSource), vitalsVersion, vitals_source_sha256: hash(vitalsSource), vitals, method: { runs: 5, reducedMotion: "reduce", cpu: 4, rtt_ms: 150, down_kbps: 1600 },
    ...(verification ? { verification: verification.binding, verification_inputs: verification.inputs, identity: verification.identity, home_semantics: homeWitness, home_semantics_failure: homeWitnessFailure } : {}),
    ...(mode === "owner-diagnostic" ? { diagnostic_attribution: { measurement_overhead: "Extra LCP/resource/font instrumentation; overhead is unmeasured and may affect diagnostic timings" } } : {}) };
  if (verification) writeVerification(verification, output, "capture.json", report);
  else {
    const raw = JSON.stringify(report, null, 2) + "\n";
    fs.writeFileSync(`${output}/capture.json`, raw);
    if (!originalCapture) fs.writeFileSync(REDESIGN_CHECKSUM_PATH, hash(raw) + "  capture.json\n");
  }
  if (verification) {
    let sourceFailed = false;
    try { recheckVerification(verification); } catch { sourceFailed = true; }
    const pngs = pages.map((page, index) => {
      try { return { original: verification.baselinePngs[index], current: fs.readFileSync(page.screenshot) }; }
      catch { return { original: null, current: null }; }
    });
    const outcomes = redesignOutcomes(verification.baseline, verification.original, report,
      sourceFailed ? null : homeWitness, verification.binding, pngs);
    outcomes.unshift({ name: "verification-context-recheck", status: sourceFailed ? "fail" : "pass" });
    writeVerification(verification, output, "comparisons.json", { scope: mode === "owner-diagnostic" ? "Owner-shell diagnostic only; no full/baseline qualification receipt" : "Actual baseline predicates", binding: verification.binding, outcomes });
    const failures = outcomes.filter((item) => item.status === "fail").map((item) => item.name);
    if (failures.length) throw new Error("Baseline comparisons failed: " + failures.join(", "));
  }
  process.stdout.write(JSON.stringify(report) + "\n");
} finally {
  const closeBrowsers = () => Promise.all([browser.close(), snapshotBrowser?.close()]);
  if (mode === "owner-diagnostic") {
    let closed = false;
    try { await deadline(closeBrowsers(), "Owner diagnostic browser cleanup deadline"); closed = true; }
    finally { writeVerification(verification, output, "cleanup.json", { scope: "Owner-shell diagnostic only", binding: verification.binding, browser: closed ? "closed" : "failed" }); }
  } else await closeBrowsers();
  server?.kill("SIGTERM");
}
