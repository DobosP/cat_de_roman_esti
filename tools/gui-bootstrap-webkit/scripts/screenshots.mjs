import { chromium } from '@playwright/test';
import * as fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

const mode = process.argv[2];
assert.equal(process.argv.length, 3, 'Usage: screenshots.mjs capture|verify');
assert.ok(['capture', 'verify'].includes(mode));
assert.match(process.env.GATE_SHA ?? '', /^[a-f0-9]{40}([a-f0-9]{24})?$/);
assert.match(process.env.GATE_TREE_SHA256 ?? '', /^[a-f0-9]{64}$/);
assert.match(process.env.GATE_APP_IMAGE_ID ?? '', /^sha256:[a-f0-9]{64}$/);
const origin = new URL(process.env.GATE_APP_URL).origin;
const stage = process.env.CSP_STAGE ?? 'report-only';
assert.ok(['report-only', 'enforced'].includes(stage));
const routes = ['/', '/pongo2', '/islands', '/behaviors', '/motion', '/templ'];
const sha = value => createHash('sha256').update(value).digest('hex');
const base = 'baselines/core/chromium';
const target = mode === 'capture' ? 'baseline' : 'full';
const output = `.gate/${target}`;
const viewport = { width: 1000, height: 800 };
const fileFor = route => `${base}/${route === '/' ? 'home' : route.slice(1)}.png`;
const regular = filename => {
  const relative = path.relative(process.cwd(), path.resolve(filename));
  assert.ok(relative && !relative.startsWith('../') && !path.isAbsolute(relative), 'Screenshot path must remain in the repository');
  let current = process.cwd();
  for (const part of relative.split(path.sep)) { current = path.join(current, part); assert.ok(!fs.lstatSync(current).isSymbolicLink(), 'Screenshot inputs cannot be symlinks'); }
  assert.ok(fs.lstatSync(current).isFile());
  return fs.readFileSync(current);
};
const manifestBytes = regular('web-kit/sample/embedfs/dist/.vite/manifest.json');
const manifest = JSON.parse(manifestBytes);
const entry = 'src/sample/main.ts';
const expectedCSS = new Set(), expectedPreloads = new Set(), allowedCSS = new Set(), allowedJS = new Set();
function closure(key, eager, seen = new Set()) {
  if (seen.has(key)) return;
  seen.add(key);
  const item = manifest[key]; assert.ok(item && typeof item.file === 'string', 'Screenshot requires the actual Vite entry closure');
  const url = file => { assert.ok(!file.startsWith('/') && !file.split('/').includes('..')); return new URL(`/static/${file}`, origin).href; };
  allowedJS.add(url(item.file));
  for (const file of item.css ?? []) { allowedCSS.add(url(file)); if (eager) expectedCSS.add(url(file)); }
  for (const dep of item.imports ?? []) { assert.ok(manifest[dep]); if (eager) expectedPreloads.add(url(manifest[dep].file)); closure(dep, eager, seen); }
  if (!eager) for (const dep of item.dynamicImports ?? []) closure(dep, false, seen);
}
closure(entry, true); closure(entry, false);
async function getJSON(route) {
  const response = await fetch(new URL(route, origin), { redirect: 'error' });
  assert.equal(response.status, 200);
  return response.json();
}
function conservation(value) {
  assert.equal(value.stage, stage);
  assert.ok(Number.isSafeInteger(value.violations) && value.violations >= 0);
  assert.ok(value.directives && typeof value.directives === 'object' && !Array.isArray(value.directives));
  const counts = Object.values(value.directives);
  assert.ok(counts.every(count => Number.isSafeInteger(count) && count >= 0));
  assert.equal(counts.reduce((sum, count) => sum + count, 0), value.violations, 'Actual bounded server summaries must conserve every report');
}
const identity = await getJSON('/__gate/identity');
assert.equal(identity.sha, process.env.GATE_SHA); assert.equal(identity.tree_sha256, process.env.GATE_TREE_SHA256);
assert.equal(identity.manifest_sha256, sha(manifestBytes)); assert.equal(identity.versions_lock_sha256, sha(regular('versions.lock.json')));
const serverBefore = await getJSON('/__gate/csp'); conservation(serverBefore);
const receipt = { schema: 1, mode, status: 'fail', sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, app_image_id: process.env.GATE_APP_IMAGE_ID, manifest_sha256: sha(manifestBytes), identity, viewport, reducedMotion: 'reduce', stage, server_before: serverBefore, pages: [] };
const browser = await chromium.launch({ headless: true });
receipt.browser = browser.version();
fs.mkdirSync(output, { recursive: true });
try {
  let baseline;
  if (mode === 'verify') {
    const baselineBytes = regular(`${base}/capture.json`);
    receipt.baseline_sha256 = sha(baselineBytes);
    baseline = JSON.parse(baselineBytes);
    assert.equal(baseline.schema, 1); assert.equal(baseline.mode, 'capture'); assert.equal(baseline.status, 'pass');
    assert.match(baseline.sha, /^[a-f0-9]{40}([a-f0-9]{24})?$/); assert.match(baseline.tree_sha256, /^[a-f0-9]{64}$/);
    assert.match(baseline.app_image_id, /^sha256:[a-f0-9]{64}$/); assert.match(baseline.manifest_sha256, /^[a-f0-9]{64}$/);
    assert.equal(baseline.identity.sha, baseline.sha); assert.equal(baseline.identity.tree_sha256, baseline.tree_sha256);
    assert.equal(baseline.identity.manifest_sha256, baseline.manifest_sha256); assert.match(baseline.identity.versions_lock_sha256, /^[a-f0-9]{64}$/);
    assert.ok(['report-only', 'enforced'].includes(baseline.stage));
    assert.equal(baseline.browser, receipt.browser, 'Baseline uses the same locked Chromium build');
    assert.deepEqual(baseline.viewport, viewport); assert.equal(baseline.reducedMotion, 'reduce');
    assert.deepEqual(baseline.pages.map(record => record.route), routes, 'Baseline must contain every sample page exactly once');
    assert.deepEqual(baseline.pages.map(record => record.file), routes.map(fileFor));
    for (const record of baseline.pages) {
      const bytes = regular(record.file); assert.equal(bytes.length, record.bytes); assert.equal(sha(bytes), record.sha256, 'Committed PNG must match its capture metadata');
    }
  }
  for (const route of routes) {
    const page = await browser.newPage({ viewport, reducedMotion: 'reduce', deviceScaleFactor: 1, locale: 'en-US', colorScheme: 'light', timezoneId: 'UTC' });
    const record = { route, file: fileFor(route), console: [], errors: [], network: [], csp: [], islands: [] };
    receipt.pages.push(record);
    page.on('pageerror', error => record.errors.push({ message: error.message, stack: error.stack }));
    page.on('console', message => { if (['warning', 'error'].includes(message.type())) record.console.push({ type: message.type(), text: message.text().replace(/nonce-[A-Za-z0-9+/_=-]+/g, 'nonce-[redacted]') }); });
    page.on('requestfailed', request => record.network.push({ url: request.url(), failure: request.failure() }));
    page.on('response', response => { if (response.status() >= 400) record.network.push({ url: response.url(), status: response.status() }); });
    await page.addInitScript(() => {
      window.__screenshotCSP = []; window.__screenshotIslands = [];
      document.addEventListener('island:failed', event => window.__screenshotIslands.push({ key: event.detail.key, error: String(event.detail.error) }));
      document.addEventListener('securitypolicyviolation', event => {
        const prefix = event.sample?.split('|')[0].trim() ?? '';
        const sink = /^(HTML[A-Za-z]*Element|Element|Document|Range|DOMParser) [A-Za-z][A-Za-z0-9]*$/.test(prefix) && prefix.length <= 80 ? prefix : 'unknown';
        window.__screenshotCSP.push({ directive: event.effectiveDirective, sink, disposition: event.disposition, line: event.lineNumber, column: event.columnNumber });
      });
    });
    try {
      record.server_before = await getJSON('/__gate/csp'); conservation(record.server_before);
      const response = await page.goto(new URL(route, origin).href); assert.equal(response.status(), 200);
      record.url = page.url(); assert.equal(record.url, new URL(route, origin).href);
      const policy = response.headers()[stage === 'enforced' ? 'content-security-policy' : 'content-security-policy-report-only'];
      const nonce = policy?.match(/'nonce-([^']+)'/)?.[1]; assert.ok(nonce);
      assert.ok(policy.includes("worker-src 'self'")); assert.ok(!/unsafe-inline|unsafe-eval/.test(policy));
      const bindings = await page.evaluate(() => ({
        scripts: [...document.scripts].map(script => ({ id: script.id, type: script.type, src: script.src, nonce: script.nonce })),
        hosts: [...document.querySelectorAll('[data-props]')].map(host => host.dataset.props),
        links: [...document.querySelectorAll('link[rel="stylesheet"],link[rel="modulepreload"]')].map(link => ({ rel: link.rel, href: link.href, nonce: link.nonce })),
      }));
      const json = bindings.scripts.filter(script => script.type === 'application/json');
      assert.equal(json.length, 7); assert.equal(new Set(json.map(script => script.id)).size, 7); assert.deepEqual(bindings.hosts.sort(), json.map(script => script.id).sort());
      assert.ok(bindings.scripts.every(script => script.nonce === nonce)); assert.ok(bindings.links.length && bindings.links.every(link => link.nonce === nonce));
      assert.deepEqual(bindings.scripts.filter(script => script.type === 'module' && script.src).map(script => script.src), [new URL(`/static/${manifest[entry].file}`, origin).href]);
      const css = bindings.links.filter(link => link.rel === 'stylesheet').map(link => link.href), preloads = bindings.links.filter(link => link.rel === 'modulepreload').map(link => link.href);
      assert.ok(css.every(url => allowedCSS.has(url)) && preloads.every(url => allowedJS.has(url)));
      assert.ok([...expectedCSS].every(url => css.includes(url)) && [...expectedPreloads].every(url => preloads.includes(url)));
      record.nonce = { sha256: sha(nonce), scripts: bindings.scripts.length, json: json.length, assetLinks: bindings.links.length, css, preloads };
      await page.locator('[data-island="stress-counter"][data-load="eager"]').getByRole('button', { name: 'Increment counter' }).waitFor();
      await page.locator('[data-island="stress-presence"]').getByRole('button', { name: 'Replace panel' }).waitFor();
      await page.locator('[data-island="stress-events"]').getByRole('button', { name: 'Send event' }).waitFor();
      await page.evaluate(async () => { await document.fonts.ready; await Promise.all(document.getAnimations().map(animation => animation.finished.catch(() => {}))); await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))); });
      const png = await page.screenshot({ fullPage: true, animations: 'disabled', caret: 'hide' });
      assert.ok(png.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])));
      record.sha256 = sha(png); record.bytes = png.length;
      record.actual_file = `${output}/screenshots/${path.basename(record.file)}`;
      fs.mkdirSync(path.dirname(record.actual_file), { recursive: true }); fs.writeFileSync(record.actual_file, png);
      if (mode === 'capture') { fs.mkdirSync(base, { recursive: true }); fs.writeFileSync(record.file, png); }
      else assert.deepEqual(png, regular(record.file), `Actual screenshot differs from committed ${route} baseline`);
    } finally {
      try {
        // Read browser observations after the asynchronous report-delivery window.
        await page.waitForTimeout(400);
        const observed = await page.evaluate(() => ({ csp: window.__screenshotCSP, islands: window.__screenshotIslands }));
        assert.ok(Array.isArray(observed.csp) && Array.isArray(observed.islands), 'Browser diagnostics are unavailable');
        Object.assign(record, observed); record.diagnostics_available = true;
      } catch (error) {
        record.diagnostics_error = error.message; throw error;
      } finally {
        try { record.server_after = await getJSON('/__gate/csp'); conservation(record.server_after); }
        catch (error) { record.server_error = error.message; throw error; }
        finally { await page.close(); }
      }
    }
    assert.equal(record.diagnostics_available, true); assert.ok(!record.diagnostics_error && !record.server_error);
    assert.deepEqual(record.console, []); assert.deepEqual(record.errors, []); assert.deepEqual(record.network, []); assert.deepEqual(record.csp, []); assert.deepEqual(record.islands, []);
  }
  receipt.server_after = await getJSON('/__gate/csp'); conservation(receipt.server_after);
  assert.equal(receipt.server_after.violations, 0); assert.equal(new Set(receipt.pages.map(record => record.nonce.sha256)).size, routes.length);
  assert.deepEqual(receipt.pages.map(record => record.route), routes);
  receipt.status = 'pass';
  if (mode === 'capture') fs.writeFileSync(`${base}/capture.json`, JSON.stringify(receipt, null, 2) + '\n');
} catch (error) {
  receipt.error = error.message;
  throw error;
} finally {
  // Preserve actual diagnostics and PNG paths even when an assertion fails.
  fs.writeFileSync(`${output}/screenshots.json`, JSON.stringify(receipt, null, 2) + '\n');
  process.stdout.write(JSON.stringify(receipt) + '\n');
  await browser.close();
}
