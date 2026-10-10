import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import assert from "node:assert/strict";

const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const freeze = (value) => { if (value && typeof value === "object") { Object.values(value).forEach(freeze); Object.freeze(value); } return value; };
export const HOME = freeze([
  { key: "alchimie", name: "Joacă Alchimie — Combină și descoperă", original: ".game-card.card:nth-child(1)", current: ".home-game--alchimie.game-card.card" },
  { key: "intrusul", name: "Joacă Intrusul — Începe aici", original: ".game-card--featured", current: ".game-card--featured" },
  { key: "perechi", name: "Joacă Perechi — Potrivește câte două", original: ".game-card.card:nth-child(3)", current: ".home-game--perechi.game-card.card" },
  { key: "conexiuni", name: "Joacă Conexiuni — Găsește grupurile", original: ".game-card.card:nth-child(4)", current: ".home-game--conexiuni.game-card.card" },
  { key: "contexto", name: "Joacă Cald sau Rece — Mai cald, mai rece", original: ".game-card.card:nth-child(5)", current: ".home-game--contexto.game-card.card" },
  { key: "lant", name: "Joacă Lanțul Cuvintelor — Leagă conceptele", original: ".game-card.card:nth-child(6)", current: ".home-game--lant.game-card.card" },
]);
export const FOOTER = "Toate cele șase jocuri folosesc aceeași hartă de legături culturale românești.";
export const ORIGINAL_BASELINE_SHA256 = "ff055e404bf138ce0442381ab33eb643d431f922e4284f66a5002efcc397be68";
const SOURCES = {
  "frontend/src/games.ts": "ce6a53bd118fae4f0cfa62eb12d6afadb31596a1e265c5122e202560ef26b0ad",
  "frontend/src/screens/Home.tsx": "1d081bda1472f0a5226116c98f94d1ee68a0c77ec726942670eb9ac15928c29a",
  "baselines/cat/capture.json": ORIGINAL_BASELINE_SHA256,
};
const liveContexts = new WeakSet(), identifiedContexts = new WeakSet(), liveWitnesses = new WeakSet();
const hex = (value, length) => typeof value === "string" && value.length === length && !/[^a-f0-9]/.test(value);
const uuid = (value) => typeof value === "string" && value.length === 36 && /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}(?![\s\S])/.test(value);
const image = (value) => typeof value === "string" && value.startsWith("sha256:") && hex(value.slice(7), 64);
const fields = (value, keys) => value && !Array.isArray(value) && Reflect.ownKeys(value).length === keys.length
  && keys.every((key) => Object.hasOwn(value, key))
  && Object.values(Object.getOwnPropertyDescriptors(value)).every((item) => Object.hasOwn(item, "value"));
export async function deadline(operation, label, milliseconds = 5000) {
  let timer;
  try { return await Promise.race([operation, new Promise((_, reject) => { timer = setTimeout(() => reject(Error(label)), milliseconds); })]); }
  finally { clearTimeout(timer); }
}
function read(root, relative, limit = 8 * 1024 * 1024) {
  assert.ok(relative && !path.isAbsolute(relative) && !/[\\:\x00-\x1f\x7f]/.test(relative)
    && relative.split("/").every((part) => part && part !== "." && part !== ".."), "Confined baseline input required");
  let file = root;
  for (const [index, part] of relative.split("/").entries()) {
    file = path.join(file, part); const info = fs.lstatSync(file);
    assert.ok(!info.isSymbolicLink() && fs.realpathSync(file) === file
      && (index === relative.split("/").length - 1 ? info.isFile() : info.isDirectory()), "Regular baseline input required");
  }
  const before = fs.lstatSync(file, { bigint: true }); assert.ok(before.size <= BigInt(limit));
  const fd = fs.openSync(file, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
  try {
    const opened = fs.fstatSync(fd, { bigint: true }), bytes = fs.readFileSync(fd), after = fs.fstatSync(fd, { bigint: true });
    assert.ok(opened.isFile() && opened.dev === before.dev && opened.ino === before.ino
      && ["dev", "ino", "size", "mode", "mtimeNs", "ctimeNs"].every((key) => opened[key] === after[key])
      && BigInt(bytes.length) === after.size, "Baseline input changed");
    return { bytes, path: relative, sha256: hash(bytes), size: bytes.length };
  } finally { fs.closeSync(fd); }
}
function ownedDirectory(root, directory) {
  let current = root;
  const relative = path.relative(root, directory);
  assert.ok(relative && !relative.startsWith("..") && !path.isAbsolute(relative));
  for (const part of relative.split(path.sep)) {
    current = path.join(current, part); const info = fs.lstatSync(current);
    assert.ok(info.isDirectory() && !info.isSymbolicLink() && info.uid === process.getuid()
      && (info.mode & 0o002) === 0 && fs.realpathSync(current) === current, "Owned no-follow evidence directory required");
  }
}
export function prepareVerification(root, mode) {
  assert.ok(["verify", "owner-diagnostic"].includes(mode), "Explicit baseline verification mode required");
  assert.equal(process.platform, "linux"); assert.equal(root, "/work"); assert.equal(fs.realpathSync(root), root);
  const target = mode === "owner-diagnostic" ? "shell" : "full";
  if (target === "shell") assert.equal(process.env.GATE_DIRTY, "false", "Owner diagnostic requires clean source");
  assert.ok(["false", "true"].includes(process.env.GATE_DIRTY));
  assert.equal(process.env.GATE_APP_URL, "http://localhost:8080");
  assert.ok(image(process.env.GATE_APP_IMAGE_ID) && image(process.env.TOOLCHAIN_DIGEST));
  const inputs = [];
  const acquire = (name) => { const row = read(root, name); inputs.push({ path: name, bytes: row.size, sha256: row.sha256 }); return row; };
  const raw = acquire(".gate/wrapper-current.json"), descriptor = JSON.parse(raw.bytes);
  assert.ok(raw.bytes.equals(acquire(".gate/" + target + "/wrapper-current.json").bytes));
  assert.ok(fields(descriptor, ["schema", "invocation", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256", "config_path", "config_file_sha256"])
    && descriptor.schema === 1 && descriptor.target === target && uuid(descriptor.invocation)
    && hex(descriptor.sha, 40) && hex(descriptor.tree_sha256, 64)
    && descriptor.config_path === ".gate/" + target + "/wrapper-kit-config.json");
  for (const [key, value] of [["sha", process.env.GATE_SHA], ["tree_sha256", process.env.GATE_TREE_SHA256], ["toolchain_digest", process.env.TOOLCHAIN_DIGEST]]) assert.equal(descriptor[key], value);
  const configRaw = acquire(descriptor.config_path), config = JSON.parse(configRaw.bytes);
  assert.ok(fields(config, ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config", "config_sha256", "command"])
    && config.schema === 1 && configRaw.sha256 === descriptor.config_file_sha256
    && ["target", "sha", "tree_sha256", "toolchain_digest", "config_sha256"].every((key) => config[key] === descriptor[key])
    && hash(JSON.stringify(config.config)) === descriptor.config_sha256
    && config.config?.role === "consumer" && config.config?.app === "cat_de_roman_esti");
  for (const [name, expected] of Object.entries(SOURCES)) assert.equal(acquire(name).sha256, expected, "Reviewed Home source or immutable baseline changed: " + name);
  for (const name of ["scripts/gate.sh", "compose.gate.yml", "Taskfile.yml", "Taskfile.repo.yml",
    "scripts/gui-baseline.mjs", "scripts/gui-baseline-checks.mjs", "frontend/package.json", "frontend/package-lock.json"]) acquire(name);
  const installed = JSON.parse(acquire("frontend/node_modules/playwright/package.json").bytes);
  const npm = JSON.parse(read(root, "frontend/package-lock.json").bytes);
  assert.ok(installed.name === "playwright" && installed.version === "1.63.0" && npm.packages?.["node_modules/playwright"]?.version === "1.63.0");
  const manifest = acquire("go-backend/embedfs/dist/.vite/manifest.json"), lock = acquire("versions.lock.json");
  const binding = freeze({ target, invocation: descriptor.invocation, sha: descriptor.sha, tree_sha256: descriptor.tree_sha256,
    toolchain_digest: descriptor.toolchain_digest, config_sha256: descriptor.config_sha256, config_file_sha256: descriptor.config_file_sha256,
    descriptor_sha256: raw.sha256, manifest_sha256: manifest.sha256, versions_lock_sha256: lock.sha256,
    app_image_id: process.env.GATE_APP_IMAGE_ID, image_authority: "Producer declaration; owning wrapper/parent host verify actual CID/IID",
    origin: process.env.GATE_APP_URL, dirty: process.env.GATE_DIRTY === "true", playwright_version: installed.version });
  const context = { identity: null };
  for (const [key, value] of Object.entries({ root, mode, binding, inputs: freeze(inputs) }))
    Object.defineProperty(context, key, { value, enumerable: true, writable: false, configurable: false });
  liveContexts.add(context); return context;
}
export function diagnosticOutput(context) {
  assert.ok(liveContexts.has(context) && context.mode === "owner-diagnostic");
  const parent = path.join(context.root, ".gate/shell"); ownedDirectory(context.root, parent);
  const namespace = path.join(parent, context.binding.invocation);
  fs.mkdirSync(namespace, { mode: 0o700 }); // Fresh invocation only, never overwrite/reset.
  assert.equal(fs.lstatSync(namespace).mode & 0o7777, 0o700);
  const output = path.join(namespace, "baseline-comparison"); fs.mkdirSync(output, { mode: 0o700 });
  assert.equal(fs.lstatSync(output).mode & 0o7777, 0o700);
  ownedDirectory(context.root, output); return path.relative(context.root, output);
}
function writePrivate(context, output, name, bytes) {
  assert.ok(liveContexts.has(context)); assert.ok(/^[a-zA-Z0-9.-]+(?![\s\S])/.test(name) && name !== "." && name !== "..");
  const directory = path.resolve(context.root, output); ownedDirectory(context.root, directory);
  assert.equal(directory, context.mode === "owner-diagnostic"
    ? path.join(context.root, ".gate/shell", context.binding.invocation, "baseline-comparison")
    : path.join(context.root, ".gate/full/baseline-comparison"), "Fixed owning evidence scope required");
  if (context.mode === "owner-diagnostic") {
    assert.equal(fs.lstatSync(path.join(context.root, ".gate/shell", context.binding.invocation)).mode & 0o7777, 0o700);
    assert.equal(fs.lstatSync(directory).mode & 0o7777, 0o700);
  }
  const before = fs.lstatSync(directory), parent = fs.openSync(directory, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
  try {
    const opened = fs.fstatSync(parent); assert.ok(opened.dev === before.dev && opened.ino === before.ino);
    const fd = fs.openSync("/proc/self/fd/" + parent + "/" + name, fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_NOFOLLOW, 0o600);
    try { fs.writeFileSync(fd, bytes); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
    fs.fsyncSync(parent);
  } finally { fs.closeSync(parent); }
  const row = read(context.root, path.relative(context.root, path.join(directory, name)));
  assert.ok(row.bytes.equals(bytes) && (fs.lstatSync(path.join(directory, name)).mode & 0o7777) === 0o600);
  return { path: row.path, bytes: row.size, sha256: row.sha256 };
}
export async function identifyPage(page, response, context, output) {
  assert.ok(liveContexts.has(context));
  assert.ok(response && response.status() === 200 && response.request().redirectedFrom() === null);
  assert.equal(page.url(), context.binding.origin + "/");
  const state = await deadline(page.evaluate(() => ({ origin: location.origin, secure: window.isSecureContext })), "Baseline origin deadline");
  assert.ok(state.origin === context.binding.origin && state.secure === true);
  const reply = await deadline(page.evaluate(async () => {
    const response = await fetch("/api/gui-build", { redirect: "error", cache: "no-store", credentials: "omit", signal: AbortSignal.timeout(5000) });
    const reader = response.body?.getReader(); if (!reader) throw Error("Missing build response");
    const bytes = []; let size = 0;
    try { while (true) { const part = await reader.read(); if (part.done) break; size += part.value.length; if (size > 16384) throw Error("Build body exceeds bound"); bytes.push(...part.value); } }
    finally { await reader.cancel(); }
    return { url: response.url, status: response.status, redirected: response.redirected, bytes };
  }), "Baseline image identity deadline");
  const bytes = Buffer.from(reply.bytes);
  context.identity = { url: reply.url, status: reply.status, redirected: reply.redirected,
    bytes: bytes.length, sha256: hash(bytes), raw_response: null, body: null };
  context.identity.raw_response = writePrivate(context, output, "identity-response.bin", bytes);
  assert.ok(bytes.length === 307 && reply.status === 200 && !reply.redirected && reply.url === context.binding.origin + "/api/gui-build");
  let body;
  try { body = JSON.parse(bytes); } catch { throw Error("Actual four-field build JSON refused; raw response retained privately"); }
  assert.ok(fields(body, ["sha", "tree_sha256", "manifest_sha256", "versions_lock_sha256"])
    && ["sha", "tree_sha256", "manifest_sha256", "versions_lock_sha256"].every((key) => body[key] === context.binding[key]));
  context.identity.body = body; identifiedContexts.add(context);
}
export function assertHomeData(value) {
  assert.ok(value && Array.isArray(value.cards) && value.cards.length === 6 && value.footer, "Complete Home witness DATA required");
  for (const [index, expected] of HOME.entries()) {
    const item = value.cards[index];
    assert.ok(item && item.key === expected.key && item.order === index && item.original === expected.original && item.current === expected.current
      && item.tag === "button" && item.type === "button" && item.role_attribute === null
      && item.aria_label === expected.name && item.aria_labelledby === null && item.aria_hidden === null && item.disabled === false
      && item.visible === true && item.enabled === true && item.old_current_same === true && item.order_same === true && item.computed_name_same === true
      && typeof item.aria_snapshot === "string" && item.aria_snapshot.length > 0, "Original unique native Home button/name join required");
  }
  const footer = value.footer;
  assert.ok(footer.tag === "p" && footer.text === FOOTER && footer.role_attribute === null && footer.aria_label === null
    && footer.aria_labelledby === null && footer.aria_hidden === null && footer.old_current_same === true && footer.text_same === true
    && typeof footer.aria_snapshot === "string" && footer.aria_snapshot.length > 0, "Original unique footer P/text join required");
}
export async function captureHomeWitness(page, context) {
  assert.ok(identifiedContexts.has(context), "Live identified source/image context required");
  const count = (locator) => deadline(locator.count(), "Home count deadline");
  async function same(left, right) {
    assert.ok(await count(left) === 1 && await count(right) === 1);
    const handle = await deadline(right.elementHandle({ timeout: 5000 }), "Home element deadline");
    try { return !!handle && await deadline(left.evaluate((node, other) => node === other, handle), "Home node identity deadline"); }
    finally { if (handle) await deadline(handle.dispose(), "Home element disposal deadline"); }
  }
  const observe = (locator) => deadline(locator.evaluate((node) => {
    const clone = node.cloneNode(true);
    for (const element of [clone, ...clone.querySelectorAll("*")]) element.removeAttribute("nonce");
    if (clone.querySelector("script,style,meta,link,iframe,object,embed,input,textarea")) throw Error("Unexpected Home descendant");
    return { tag: node.tagName.toLowerCase(), type: node.getAttribute("type"), role_attribute: node.getAttribute("role"),
      aria_label: node.getAttribute("aria-label"), aria_labelledby: node.getAttribute("aria-labelledby"), aria_hidden: node.getAttribute("aria-hidden"),
      disabled: node.hasAttribute("disabled"), text: node.textContent.trim(), outer_html_without_nonce: clone.outerHTML };
  }), "Home node observation deadline");
  const cards = page.locator(".games-grid .game-card"), data = { binding: context.binding, cards: [], footer: null };
  assert.equal(await count(cards), 6);
  for (const [index, expected] of HOME.entries()) {
    const locator = page.locator(expected.current); assert.equal(await count(locator), 1);
    const item = { key: expected.key, order: index, original: expected.original, current: expected.current, ...await observe(locator),
      aria_snapshot: await deadline(locator.ariaSnapshot({ timeout: 5000 }), "Home ariaSnapshot deadline"),
      visible: await deadline(locator.isVisible(), "Home visibility deadline"), enabled: await deadline(locator.isEnabled(), "Home enabled deadline"),
      old_current_same: await same(page.locator(expected.original), locator), order_same: await same(cards.nth(index), locator),
      computed_name_same: await same(page.getByRole("button", { name: expected.name, exact: true }), locator) };
    data.cards.push(item);
  }
  const footer = page.locator(".home-footer"); assert.equal(await count(footer), 1);
  data.footer = { ...await observe(footer), aria_snapshot: await deadline(footer.ariaSnapshot({ timeout: 5000 }), "Footer ariaSnapshot deadline"),
    old_current_same: await same(page.locator(".container > .faint"), footer), text_same: await same(page.getByText(FOOTER, { exact: true }), footer) };
  assert.equal(page.url(), context.binding.origin + "/");
  const final = await deadline(page.evaluate(() => ({ origin: location.origin, secure: window.isSecureContext })), "Home final origin deadline");
  assert.ok(final.origin === context.binding.origin && final.secure === true);
  assertHomeData(data); freeze(data); liveWitnesses.add(data); return data;
}
export function recheckVerification(context) {
  assert.ok(liveContexts.has(context));
  for (const row of context.inputs) assert.equal(read(context.root, row.path).sha256, row.sha256, "Baseline source/context changed");
}
function canonicalHome(original, current) {
  const old = structuredClone(original), next = structuredClone(current);
  assert.equal(old.length, 2); assert.equal(next.length, 2);
  assert.ok(old[0].id === "label-content-name-mismatch" && old[0].impact === "serious" && old[0].targets.length === 6
    && old[1].id === "region" && old[1].impact === "moderate" && old[1].targets.length === 1);
  for (const [index, item] of HOME.entries()) {
    assert.deepEqual(old[0].targets[index], [item.original]);
    assert.ok(JSON.stringify(next[0].targets[index]) === JSON.stringify([item.original])
      || JSON.stringify(next[0].targets[index]) === JSON.stringify([item.current]), "Unreviewed Home Axe target");
    next[0].targets[index] = [item.original];
  }
  assert.deepEqual(old[1].targets, [[".container > .faint"]]);
  assert.ok(JSON.stringify(next[1].targets) === JSON.stringify([[".container > .faint"]])
    || JSON.stringify(next[1].targets) === JSON.stringify([[".home-footer"]]), "Unreviewed footer Axe target");
  next[1].targets = [[".container > .faint"]];
  assert.deepEqual(next, old, "Axe IDs/impacts/order/counts/other fields changed"); return next;
}
export function assertHomeAliasData(original, current) {
  // Pure DATA refusal tests receive no canonicalized output or live authority.
  canonicalHome(original, current);
}
export function assertAxePages(original, current, witness, binding) {
  const before = original.map((item) => [item.route, item.axe]), after = current.map((item) => [item.route, item.axe]);
  if (JSON.stringify(before) === JSON.stringify(after)) return;
  assert.ok(liveWitnesses.has(witness) && witness.binding === binding, "Live Home node/name witness required for exact aliases");
  const candidate = structuredClone(after);
  assert.equal(before.length, candidate.length);
  for (const [index, row] of before.entries()) {
    assert.equal(candidate[index][0], row[0], "Route identity/order changed");
    if (row[0] === "/") candidate[index][1] = canonicalHome(row[1], candidate[index][1]);
  }
  assert.deepEqual(candidate, before, "Axe or route fingerprint changed");
}
export function comparisonOutcomes(baseline, current, witness, binding, pngs) {
  const outcomes = [];
  const check = (name, operation) => {
    try { operation(); outcomes.push({ name, status: "pass" }); }
    catch { outcomes.push({ name, status: "fail" }); }
  };
  check("home-live-semantic-witness", () => assert.ok(liveWitnesses.has(witness) && witness.binding === binding));
  check("axe-route-fingerprints", () => assertAxePages(baseline.pages, current.pages, witness, binding));
  for (const [index, page] of current.pages.entries()) check("png:" + page.route, () => {
    const original = baseline.pages[index], pair = pngs[index];
    assert.ok(original.route === page.route && Buffer.isBuffer(pair.original) && Buffer.isBuffer(pair.current) && pair.original.equals(pair.current), "Exact original screenshot pixels changed");
  });
  for (const [index, item] of current.vitals.entries()) for (const key of ["lcp", "inp"]) {
    const expected = baseline.vitals[index].median[key], actual = item.median[key];
    check("vitals:" + item.route + ":" + key, () => {
      assert.ok(Number.isFinite(expected) && expected >= 0 && Number.isFinite(actual) && actual >= 0, "Actual finite nonnegative baseline metrics required");
      assert.ok(!(actual - expected > Math.max(expected * .1, 50)), "Vitals baseline regression");
    });
    Object.assign(outcomes.at(-1), { expected, actual, absolute_delta: Math.abs(actual - expected), tolerance: Math.max(expected * .1, 50) });
  }
  return outcomes;
}
export function writeVerification(context, output, name, value) {
  return writePrivate(context, output, name, Buffer.from(JSON.stringify(value, null, 2) + "\n"));
}
