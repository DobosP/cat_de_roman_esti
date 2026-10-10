// INERT proposal. Run only inside the genuine current full, never host Node.
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import net from 'node:net';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const [phase, filename] = process.argv.slice(2);
assert.equal(process.argv.slice(2).length, 2);
assert.ok(['preflight', 'observe', 'confirm'].includes(phase));
const root = path.dirname(filename);
assert.equal(path.basename(filename), 'request.json');
assert.equal(path.dirname(root), '/work/.gate/full/legacy-owner');
assert.equal(fs.realpathSync(root), root);
assert.equal(fs.lstatSync(root).mode & 0o777, 0o700);
assert.equal(fs.lstatSync(root).uid, process.getuid());
const hash = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
function read(name, maximum = 2 * 1024 * 1024) {
  const fd = fs.openSync(name, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
  try {
    const before = fs.fstatSync(fd);
    assert.ok(before.isFile() && before.size <= maximum);
    const bytes = fs.readFileSync(fd), after = fs.fstatSync(fd);
    assert.equal(bytes.length, before.size);
    assert.equal(after.ino, before.ino); assert.equal(after.size, before.size); assert.equal(after.mtimeMs, before.mtimeMs);
    return bytes;
  } finally { fs.closeSync(fd); }
}
function save(name, bytes) {
  assert.match(name, /^[a-z0-9.-]+$/);
  const pending = path.join(root, name + '.pending');
  const fd = fs.openSync(pending, fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_NOFOLLOW, 0o600);
  try { fs.writeFileSync(fd, bytes); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
  fs.linkSync(pending, path.join(root, name)); fs.unlinkSync(pending);
}
const methodBytes = read(fileURLToPath(import.meta.url));
async function waitFile(name, milliseconds) {
  const deadline = Date.now() + milliseconds;
  while (!fs.existsSync(path.join(root, name))) {
    assert.ok(Date.now() < deadline, 'Required owner record absent: ' + name);
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  return read(path.join(root, name));
}
const requestBytes = await waitFile('request.json', 60000), request = JSON.parse(requestBytes);
const descriptorBytes = read('/work/.gate/full/wrapper-current.json');
const descriptor = JSON.parse(descriptorBytes);
assert.equal(hash(descriptorBytes), request.descriptor_sha256);
assert.equal(request.run_id, path.basename(root));
assert.equal(request.run_id, request.wrapper_invocation);
assert.equal(descriptor.target, 'full'); assert.equal(request.target, 'full');
for (const [key, expected] of [['sha', request.source_sha], ['tree_sha256', request.tree_sha256],
  ['toolchain_digest', request.toolchain_digest], ['invocation', request.wrapper_invocation]]) assert.equal(descriptor[key], expected);
assert.equal(process.env.GATE_SHA, request.source_sha);
assert.equal(process.env.GATE_TREE_SHA256, request.tree_sha256);
assert.equal(process.env.TOOLCHAIN_DIGEST, request.toolchain_digest);
assert.equal(process.env.GATE_APP_IMAGE_ID, request.app_image_id);
assert.equal(process.env.GATE_DIRTY, 'false');
const bootstrap = JSON.parse(read('/work/.gate/full/bootstrap-execution.json'));
assert.equal(bootstrap.invocation, request.runner_invocation); assert.equal(bootstrap.wrapper_invocation, request.wrapper_invocation);
assert.equal(bootstrap.sha, request.source_sha); assert.equal(bootstrap.tree_sha256, request.tree_sha256);
assert.equal(process.env.GATE_APP_URL, 'http://localhost:8080');
assert.ok(['report-only', 'enforced'].includes(process.env.CSP_STAGE));
assert.ok(['report-only', 'enforced'].includes(request.expected_legacy_policy_stage));
assert.equal(request.expected_legacy_policy_stage, process.env.CSP_STAGE);
const report = { scope: 'One actual same-full owner-provisioned immutable-image legacy observation; not aggregate full/E3/M0/M1/KIT_BUMP/device acceptance',
  request_sha256: hash(requestBytes), method_sha256: hash(methodBytes),
  source: request.source_sha, tree_sha256: request.tree_sha256, wrapper_invocation: request.wrapper_invocation, runner_invocation: request.runner_invocation,
  toolchain_digest: request.toolchain_digest, actual_csp_stage: process.env.CSP_STAGE,
  app_image_id: request.app_image_id, errors: [], status: 'fail' };
const origin = 'http://localhost:8081';
const require = createRequire('/work/frontend/package.json');
const { chromium, expect } = require('@playwright/test');
assert.equal(require('@playwright/test/package.json').version, '1.63.0');
const { collectInitialBundleFiles, assertRomanianFontSubsets, ROMANIAN_FONT_SOURCES } = await import('/work/frontend/scripts/check-bundle-budget.mjs');
function get(url, name, maximum = 2 * 1024 * 1024) {
  const u = new URL(url);
  assert.ok(['http://localhost:8080', origin].includes(u.origin) && !u.username && !u.password && !u.hash);
  return new Promise((resolve, reject) => {
    const outgoing = http.get(u, { headers: { 'Accept-Encoding': 'identity' }, timeout: 5000 }, (response) => {
      const chunks = []; let count = 0;
      response.on('data', (part) => { count += part.length; if (count > maximum) response.destroy(new Error('Body limit exceeded')); else chunks.push(part); });
      response.on('error', reject);
      response.on('end', () => {
        const body = Buffer.concat(chunks);
        if (name) save(name, body); // Actual body retained before JSON parsing.
        resolve({ status: response.statusCode, body, headers: response.headers });
      });
    });
    outgoing.on('timeout', () => outgoing.destroy(new Error('HTTP deadline exceeded')));
    outgoing.on('error', reject);
  });
}
function closedPort() {
  return new Promise((resolve, reject) => {
    const socket = net.connect({ host: '127.0.0.1', port: 8081 });
    socket.setTimeout(1000, () => socket.destroy(new Error('Port preflight timed out')));
    socket.once('connect', () => { socket.destroy(); reject(new Error('Port8081 already occupied')); });
    socket.once('error', (error) => error.code === 'ECONNREFUSED' ? resolve() : reject(error));
  });
}
function frozenInputs() {
  const proofBytes = read('/work/legacy/original-bundle.json');
  const proof = JSON.parse(proofBytes);
  assert.equal(proof.schema, 1); assert.equal(proof.sha256, '742bb11130fa2bf52ba5c64cb9cfd452f7d8ac3a4fd9dc6d77e8064a6b8fef65');
  assert.equal(proof.files.length, 30); assert.equal(new Set(proof.files.map((r) => r.path)).size, 30);
  assert.match(proof.archive, /^legacy\/cat_de_roman_esti-legacy-[0-9a-f]{40}\.tgz$/);
  assert.equal(hash(read('/work/' + proof.archive, 16 * 1024 * 1024)), proof.sha256);
  const rows = new Map();
  for (const row of proof.files) {
    assert.ok(row.path && !row.path.startsWith('/') && !/[\\:\x00-\x1f\x7f]/.test(row.path));
    assert.ok(row.path.split('/').every((p) => p && p !== '.' && p !== '..'));
    const file = '/work/go-backend/embedfs/legacy/' + row.path;
    assert.equal(fs.realpathSync(file), file);
    const body = read(file, 16 * 1024 * 1024);
    assert.equal(body.length, row.bytes); assert.equal(hash(body), row.sha256);
    rows.set(row.path, { ...row, full_mode: fs.lstatSync(file).mode });
  }
  const manifest = JSON.parse(read('/work/go-backend/embedfs/legacy/.vite/manifest.json'));
  assert.ok(manifest['index.html'].isEntry && rows.has(manifest['index.html'].file));
  assert.equal(Object.values(manifest).filter((item) => item.isEntry).length, 1);
  const staticFiles = collectInitialBundleFiles(manifest, { eagerRoots: ["src/components/AccountBar.tsx", "src/screens/Intrusul.tsx"] });
  assert.ok(staticFiles.every((file) => rows.has(file)));
  assertRomanianFontSubsets(manifest);
  const fonts = ROMANIAN_FONT_SOURCES.map((source) => {
    const [key, record] = Object.entries(manifest).find(([, item]) => item.src === source);
    assert.ok(record.file.endsWith('.woff2') && rows.has(record.file));
    return { key, source, file: record.file, url: origin + '/' + record.file };
  });
  assert.equal(new Set(fonts.map((font) => font.file)).size, 4);
  return { rows, manifest, staticFiles, fonts, proof_sha256: hash(proofBytes), archive_sha256: proof.sha256 };
}
function selectedPolicy(headers, stage) {
  const name = stage === 'enforced' ? 'content-security-policy' : 'content-security-policy-report-only';
  const value = headers[name]; assert.equal(typeof value, 'string');
  const nonce = value.match(/script-src 'self' 'nonce-([A-Za-z0-9+/]{32})' 'strict-dynamic'/)?.[1];
  assert.ok(nonce, 'Actual strict nonce policy required');
  if (stage === 'enforced') {
    const strict = `default-src 'self'; script-src 'self' 'nonce-${nonce}' 'strict-dynamic'; script-src-attr 'none'; style-src 'self' 'nonce-${nonce}'; style-src-attr 'none'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; connect-src 'self'; img-src 'self' data:; font-src 'self'; worker-src 'self'; report-uri /csp-report`;
    const trustedTypesReportOnly = "require-trusted-types-for 'script'; trusted-types roedu roedu-hovercard roedu-islands; report-uri /csp-report";
    assert.equal(value, strict, 'Exact SDK strict enforced policy required');
    assert.equal(headers['content-security-policy-report-only'], trustedTypesReportOnly, 'Separate SDK Trusted Types report-only policy required');
  }
  return { name, value, nonce, canonical: value.replace(/'nonce-[A-Za-z0-9+/]{32}'/g, "'nonce-[nonce]'"), sha256: hash(value) };
}
let browser;
const deadlineTimer = setTimeout(() => {
  report.errors.push('Managed legacy probe exceeded240s'); report.status = 'fail';
  try { save('deadline.json', Buffer.from(JSON.stringify(report) + '\n')); } finally { process.exit(1); }
}, 240000);
deadlineTimer.unref();
try {
  const current = await get('http://localhost:8080/api/gui-build', phase + '-current-identity.bin');
  assert.equal(current.status, 200);
  const identity = JSON.parse(current.body);
  assert.deepEqual(identity, { sha: request.source_sha, tree_sha256: request.tree_sha256,
    manifest_sha256: request.current_manifest_sha256, versions_lock_sha256: request.current_versions_lock_sha256 });
  const frozen = frozenInputs();
  report.frozen = { archive_sha256: frozen.archive_sha256, proof_sha256: frozen.proof_sha256, files: [...frozen.rows.values()] };
  if (phase === 'preflight') {
    await closedPort(); report.port_8081_closed = true;
  } else if (phase === 'observe') {
    const ready = JSON.parse(await waitFile('owner-ready.json', 60000));
    assert.equal(ready.request_sha256, report.request_sha256);
    assert.equal(ready.status, 'ready'); assert.equal(ready.primary.id, request.primary_cid);
    assert.equal(ready.legacy.image, request.app_image_id); assert.notEqual(ready.legacy.id, request.primary_cid);
    assert.equal(ready.legacy.owner_run, request.run_id); assert.equal(ready.legacy.owner_primary, request.primary_cid);
    const preflightBytes = read(path.join(root, 'preflight.json'));
    assert.equal(hash(preflightBytes), ready.preflight_sha256);
    assert.deepEqual(JSON.parse(preflightBytes).frozen.files, report.frozen.files);
    report.legacy_cid = ready.legacy.id;
    let health;
    for (let attempt = 0; attempt < 30; attempt++) {
      try { health = await get(origin + '/healthz', null, 4096); if (health.status === 200) break; } catch (error) { report.startup_attempts = (report.startup_attempts || 0) + 1; }
      await new Promise((resolve) => setTimeout(resolve, 200));
    }
    assert.equal(health?.status, 200); save('legacy-health.bin', health.body); assert.deepEqual(JSON.parse(health.body), { ok: true });
    const legacyIdentity = await get(origin + '/api/gui-build', 'legacy-identity.bin', 4096);
    assert.equal(legacyIdentity.status, 503); assert.equal(JSON.parse(legacyIdentity.body).detail, 'GUI build identity unavailable');
    const primaryHTML = await get('http://localhost:8080/', 'primary-index.bin');
    assert.equal(primaryHTML.status, 200);
    const primaryPolicy = selectedPolicy(primaryHTML.headers, process.env.CSP_STAGE);
    browser = await chromium.launch({ headless: true }); assert.equal(browser.version(), '153.0.8010.12');
    const context = await browser.newContext(); const page = await context.newPage();
    const policyEvents = [], consoleRefusals = [], pageErrors = [], assetTasks = [], observedAssets = new Map();
    let creates = 0;
    const fontURLs = new Set(frozen.fonts.map((font) => font.url)), fontRequests = [];
    page.on('request', (r) => { if (r.resourceType() === 'font') fontRequests.push({ url: r.url(), method: r.method() }); });
    const fontsFinished = Promise.all(frozen.fonts.map((font) => page.waitForResponse((response) => response.url() === font.url
      && response.request().resourceType() === 'font', { timeout: 20000 })))
      .then((responses) => ({ responses }), (error) => ({ error }));
    page.on('request', (r) => { const u = new URL(r.url()); if (r.method() === 'POST' && u.origin === origin && u.pathname === '/api/wordgames/intrusul/games') creates++; });
    page.on('pageerror', (e) => pageErrors.push(hash(e.message)));
    page.on('console', (m) => { if (/Content Security Policy|Refused to (?:execute|apply|load)/i.test(m.text())) consoleRefusals.push({ type: m.type(), sha256: hash(m.text()) }); });
    await page.addInitScript(() => {
      window.__ownerLegacyPolicyEvents = [];
      document.addEventListener('securitypolicyviolation', (e) => window.__ownerLegacyPolicyEvents.push({ directive: e.violatedDirective, effectiveDirective: e.effectiveDirective, disposition: e.disposition,
        blocked: ['inline', 'eval', 'wasm-eval', 'trusted-types-policy', 'trusted-types-sink'].includes(e.blockedURI) ? e.blockedURI : '[redacted]' }));
    });
    page.on('response', (response) => {
      const u = new URL(response.url()), file = u.pathname.slice(1);
      if (u.origin !== origin || !frozen.rows.has(file) || file === 'index.html' || file === '.vite/manifest.json') return;
      assetTasks.push((async () => {
        assert.equal(u.search + u.hash, ''); assert.equal(response.status(), 200);
        const body = await response.body(), expected = frozen.rows.get(file);
        assert.equal(body.length, expected.bytes); assert.equal(hash(body), expected.sha256);
        observedAssets.set(file, { file, bytes: body.length, sha256: hash(body), url: u.href });
      })().catch((error) => report.errors.push('asset: ' + error.message)));
    });
    const response = await page.goto(origin + '/intrusul', { waitUntil: 'networkidle', timeout: 20000 });
    assert.equal(response.status(), 200); save('legacy-index.bin', await response.body());
    assert.equal(await page.locator('html').getAttribute('data-ui'), 'legacy');
    const policy = selectedPolicy(response.headers(), request.expected_legacy_policy_stage);
    assert.equal(policy.canonical, primaryPolicy.canonical, 'Same strict policy directives required; only nonce and header disposition may differ');
    const entryURL = origin + '/' + frozen.manifest['index.html'].file;
    const scripts = await page.locator('script[type="module"]').evaluateAll((items) => items.map((s) => ({ src: s.src, nonce: s.nonce })));
    assert.equal(scripts.length, 1); assert.equal(scripts[0].src, entryURL); assert.equal(scripts[0].nonce, policy.nonce);
    const fontPreloads = await page.locator('link[rel~="preload"]').evaluateAll((items) => items.map((item) => ({
      href: item.href, rel: item.getAttribute('rel'), as: item.getAttribute('as'), type: item.getAttribute('type'),
      crossorigin: item.getAttribute('crossorigin'), nonce: item.nonce, attributes: [...item.attributes].map((attribute) => attribute.name),
    })));
    const ordinalFonts = (a, b) => a < b ? -1 : a > b ? 1 : 0;
    assert.equal(fontPreloads.length, 4);
    assert.deepEqual(fontPreloads.map((font) => font.href).sort(ordinalFonts), [...fontURLs].sort(ordinalFonts));
    for (const font of fontPreloads) {
      assert.deepEqual(font.attributes.sort(ordinalFonts), ['as', 'crossorigin', 'href', 'nonce', 'rel', 'type']);
      assert.equal(font.rel, 'preload'); assert.equal(font.as, 'font'); assert.equal(font.type, 'font/woff2');
      assert.equal(font.crossorigin, 'anonymous'); assert.equal(font.nonce, policy.nonce);
    }
    const loadedFonts = await fontsFinished;
    assert.ok(!loadedFonts.error, loadedFonts.error?.message);
    const fontResponses = [];
    for (const [index, actual] of loadedFonts.responses.entries()) {
      const expectedFont = frozen.fonts[index], expectedBody = frozen.rows.get(expectedFont.file);
      assert.equal(actual.url(), expectedFont.url); assert.equal(actual.status(), 200);
      assert.equal(actual.request().resourceType(), 'font'); assert.equal(actual.request().method(), 'GET');
      assert.match(actual.headers()['content-type'] || '', /^font\/woff2(?:;|$)/);
      const body = await actual.body(); assert.equal(body.length, expectedBody.bytes); assert.equal(hash(body), expectedBody.sha256);
      fontResponses.push({ ...expectedFont, status: actual.status(), bytes: body.length, sha256: hash(body) });
    }
    assert.ok(fontRequests.every((font) => fontURLs.has(font.url) && font.method === 'GET'));
    assert.deepEqual([...new Set(fontRequests.map((font) => font.url))].sort(ordinalFonts), [...fontURLs].sort(ordinalFonts));
    report.font_preloads = fontPreloads.map(({ nonce, ...font }) => ({ ...font, nonce_sha256: hash(nonce) }));
    report.font_responses = fontResponses;
    report.legacy_document_marker = 'html[data-ui=legacy]';
    const cssURLs = await page.locator('link[rel="stylesheet"]').evaluateAll((items) => items.map((s) => s.href));
    const ordinal = (a, b) => a < b ? -1 : a > b ? 1 : 0;
    assert.deepEqual(cssURLs.sort(ordinal), frozen.staticFiles.filter((file) => file.endsWith('.css')).map((file) => origin + '/' + file).sort(ordinal));
    const created = page.waitForResponse((r) => r.request().method() === 'POST' && new URL(r.url()).origin === origin && new URL(r.url()).pathname === '/api/wordgames/intrusul/games', { timeout: 10000 });
    await page.getByRole('button', { name: /^Joacă(?: →)?$/ }).click();
    const stateResponse = await created; assert.equal(stateResponse.status(), 200);
    const stateBytes = await stateResponse.body(); assert.ok(stateBytes.length <= 256 * 1024); save('create-state.bin', stateBytes);
    const state = JSON.parse(stateBytes); assert.equal(typeof state.game_id, 'string'); assert.ok(state.game_id.length > 0);
    await expect(page.locator('.intrusul-grid')).toBeVisible();
    await page.waitForLoadState('networkidle'); await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await Promise.all(assetTasks); assert.equal(creates, 1); assert.deepEqual(pageErrors, []);
    assert.ok(observedAssets.has(frozen.manifest['index.html'].file));
    assert.ok(frozen.staticFiles.every((file) => observedAssets.has(file)), 'Every real frozen static dependency must load with exact bytes');
    policyEvents.push(...await page.evaluate(() => window.__ownerLegacyPolicyEvents));
    report.journey = { path: '/intrusul', start_post_status: 200, creates, game_id_sha256: hash(state.game_id), real_board_visible: true };
    report.policy = { header: policy.name, sha256: policy.sha256, nonce_sha256: hash(policy.nonce), same_directives_as_primary: true };
    report.assets = [...observedAssets.values()]; report.policy_events = policyEvents; report.console_refusals = consoleRefusals;
    report.legacy_violations = policyEvents.length + consoleRefusals.length;
    report.legacy_count_definition = 'Conservative observation count: browser policy events plus matching console messages; channels may overlap. Advisory, never hardcoded zero.';
    assert.deepEqual([...frozenInputs().rows.values()], [...frozen.rows.values()]);
  } else {
    const lifecycleBytes = await waitFile('owner-lifecycle.json', 120000);
    const lifecycle = JSON.parse(lifecycleBytes), probeBytes = read(path.join(root, 'probe-result.json'));
    const probe = JSON.parse(probeBytes);
    assert.equal(lifecycle.request_sha256, report.request_sha256); assert.equal(lifecycle.status, 'pass');
    assert.equal(lifecycle.cleanup_verified, true); assert.deepEqual(lifecycle.errors, []);
    assert.equal(probe.request_sha256, report.request_sha256); assert.equal(probe.status, 'pass'); assert.deepEqual(probe.errors, []);
    assert.equal(probe.runner_invocation, request.runner_invocation); assert.equal(probe.wrapper_invocation, request.wrapper_invocation);
    assert.ok(Number.isInteger(probe.legacy_violations) && probe.legacy_violations >= 0);
    report.legacy_violations = probe.legacy_violations; report.legacy_cid = probe.legacy_cid;
    report.journey = probe.journey; report.policy = probe.policy;
    report.probe_sha256 = hash(probeBytes); report.owner_lifecycle_sha256 = hash(lifecycleBytes);
    report.cleanup_verified = true;
  }
  assert.deepEqual(report.errors, []); report.status = 'pass';
} catch (error) { report.errors.push(error.message); }
finally {
  let forceExit = false;
  try {
    if (browser) await Promise.race([browser.close(), new Promise((_, reject) => {
      const timer = setTimeout(() => reject(new Error('Browser close exceeded5s')), 5000); timer.unref();
    })]);
  } catch (error) { report.errors.push('browser cleanup: ' + error.message); report.status = 'fail'; forceExit = true; }
  try { assert.deepEqual(read(filename), requestBytes); assert.deepEqual(read('/work/.gate/full/wrapper-current.json'), descriptorBytes); assert.deepEqual(read(fileURLToPath(import.meta.url)), methodBytes); }
  catch (error) { report.errors.push('input changed: ' + error.message); report.status = 'fail'; }
  save(phase === 'preflight' ? 'preflight.json' : phase === 'observe' ? 'probe-result.json' : 'confirm.json', Buffer.from(JSON.stringify(report, null, 2) + '\n'));
  clearTimeout(deadlineTimer);
  if (forceExit) process.exit(1); // Playwright's owning Node process exit; never leave this child waiting forever.
}
process.exitCode = report.status === 'pass' ? 0 : 1;
