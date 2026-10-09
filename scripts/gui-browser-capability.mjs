import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { pathToFileURL } from "node:url";

export const CAPABILITY_CHECK = "cat-browser-capability";
const UUID = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
const SHA = /^[a-f0-9]{40}(?:[a-f0-9]{24})?$/;
const HEX = /^[a-f0-9]{64}$/;
const DIGEST = /^sha256:[a-f0-9]{64}$/;
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const requireData = (condition, message) => { if (!condition) throw Error(message); };
const closed = (value, fields) => value !== null && typeof value === "object" && !Array.isArray(value)
  && [Object.prototype, null].includes(Object.getPrototypeOf(value))
  && Object.keys(value).length === fields.length && fields.every((field) => Object.hasOwn(value, field))
  && Object.values(Object.getOwnPropertyDescriptors(value)).every((descriptor) => Object.hasOwn(descriptor, "value"));

// The trusted wrapper selects this exact origin. No alternate URL or server is selected here.
export function requireWrapperOrigin(value) {
  requireData(typeof value === "string" && value.length > 0, "Actual wrapper app URL required");
  const url = new URL(value);
  requireData(["http:", "https:"].includes(url.protocol) && !url.username && !url.password
    && !url.search && !url.hash && url.pathname === "/" && value === url.origin,
  "Bare canonical wrapper origin required");
  return url.origin;
}

// Pure DATA assertions: they cannot prove an actual browser, image or command ran.
export function assertBrowserObservation(expected, actual) {
  requireData(closed(actual, ["project", "requested_origin", "document_origin", "document_status",
    "document_redirected", "secure_context", "locks", "identity"]), "Complete browser observation required");
  requireData(["desktop", "mobile"].includes(actual.project), "Existing Chromium project required");
  const origin = requireWrapperOrigin(expected.origin);
  requireData(actual.requested_origin === origin && actual.document_origin === origin,
    "Actual browser origin differs from wrapper origin");
  requireData(actual.document_status === 200 && actual.document_redirected === false,
    "Actual root must return200 without redirect");
  requireData(actual.secure_context === true, "Actual served browser context is not secure");
  requireData(closed(actual.locks, ["request", "query", "acquired", "held", "released", "absent_after_release"])
    && Object.values(actual.locks).every((value) => value === true), "Actual native Web Locks acquisition/query/release required");
  assertBuildResponse(expected, actual.identity);
  requireData(actual.identity.raw_response.path === `.gate/full/browser-capability/${expected.invocation}/${actual.project}-identity-response.bin`,
    "Retained identity response differs from actual project");
}

export function assertBuildResponse(expected, identity) {
  const origin = requireWrapperOrigin(expected.origin);
  requireData(closed(identity, ["url", "status", "redirected", "bytes", "sha256", "raw_response", "body"])
    && identity.url === new URL("/api/gui-build", origin).href && identity.status === 200
    && identity.redirected === false && Number.isSafeInteger(identity.bytes) && identity.bytes > 0
    && identity.bytes <= 16384 && HEX.test(identity.sha256), "Actual same-origin build response required");
  requireData(UUID.test(expected.invocation || "")
    && closed(identity.raw_response, ["path", "bytes", "sha256"])
    && ["desktop", "mobile"].some((project) => identity.raw_response.path
      === `.gate/full/browser-capability/${expected.invocation}/${project}-identity-response.bin`)
    && identity.raw_response.bytes === identity.bytes && identity.raw_response.sha256 === identity.sha256,
  "Acquired raw identity response reference required");
  requireData(closed(identity.body, ["sha", "tree_sha256", "manifest_sha256", "versions_lock_sha256"])
    && SHA.test(identity.body.sha) && HEX.test(identity.body.tree_sha256)
    && HEX.test(identity.body.manifest_sha256) && HEX.test(identity.body.versions_lock_sha256), "Actual closed build identity required");
  requireData(identity.body.sha === expected.sha && identity.body.tree_sha256 === expected.tree_sha256
    && identity.body.versions_lock_sha256 === expected.versions_lock_sha256,
  "Actual app source/tree/versions identity differs from this full");
}

// This narrow synchronous seam makes retention-before-parse ordering reviewable.
// The real CLI supplies only its fixed private wx writer below. A synthetic test
// sink proves ordering/refusal only; its return value cannot authorize anything.
export function retainAndParseBuildResponseData(expected, project, identity, raw, writeRaw) {
  requireData(UUID.test(expected.invocation || "") && ["desktop", "mobile"].includes(project)
    && Buffer.isBuffer(raw) && raw.length <= 16384 && typeof writeRaw === "function"
    && closed(identity, ["url", "status", "redirected", "bytes", "sha256", "raw_response", "body"])
    && identity.raw_response === null && identity.body === null,
  "Owned bounded unprocessed identity response required");
  const ref = { path: `.gate/full/browser-capability/${expected.invocation}/${project}-identity-response.bin`,
    bytes: raw.length, sha256: hash(raw) };
  identity.bytes = ref.bytes; identity.sha256 = ref.sha256; // actual acquired bytes, even if retention refuses
  writeRaw(raw); // return value ignored; throw refuses, with no invented retained ref
  identity.raw_response = ref; // acquired before parse or strict identity refusal
  const body = JSON.parse(raw);
  assertBuildResponse(expected, { ...identity, body });
  identity.body = body;
}

// One fixed command through the existing trusted SDK hook. The caller supplies no URL,
// executable, browser, observer or success callback. Tests use only a NON-RELEASE hook double.
export function checkFullBrowserCapability(hook) {
  requireData(hook.context.target === "full" && UUID.test(hook.context.invocation), "Actual full invocation required");
  hook.check(CAPABILITY_CHECK, () => hook.run("node", ["scripts/gui-browser-capability.mjs", "full", hook.context.invocation]));
  return hook.checks.find((item) => item.name === CAPABILITY_CHECK)?.status === "pass";
}

function readRegular(root, relative, limit = 2 * 1024 * 1024) {
  requireData(typeof relative === "string" && !path.isAbsolute(relative) && !/[\\:\x00-\x1f\x7f]/.test(relative)
    && relative.split("/").every((part) => part && part !== "." && part !== ".."), "Confined input path required");
  let current = root;
  const parts = relative.split("/");
  for (const [index, part] of parts.entries()) {
    current = path.join(current, part);
    const info = fs.lstatSync(current);
    requireData(!info.isSymbolicLink() && (index === parts.length - 1 ? info.isFile() : info.isDirectory())
      && fs.realpathSync.native(current) === current, "Canonical regular input required");
  }
  const before = fs.lstatSync(current, { bigint: true });
  requireData(before.size <= BigInt(limit), "Bounded input required");
  const bytes = fs.readFileSync(current), after = fs.lstatSync(current, { bigint: true });
  requireData(after.isFile() && !after.isSymbolicLink() && before.dev === after.dev && before.ino === after.ino
    && before.size === after.size && before.mtimeNs === after.mtimeNs && BigInt(bytes.length) === after.size,
  "Input changed during capability acquisition");
  return { bytes, ref: { path: relative, bytes: bytes.length, sha256: hash(bytes) } };
}

function acquireContext(invocation) {
  const root = process.cwd();
  requireData(process.platform === "linux" && root === "/work" && fs.realpathSync.native(root) === root,
    "Actual native owning /work runner required");
  requireData(process.argv.length === 4 && process.argv[2] === "full" && UUID.test(invocation), "Actual full arguments required");
  requireData(SHA.test(process.env.GATE_SHA || "") && HEX.test(process.env.GATE_TREE_SHA256 || "")
    && DIGEST.test(process.env.TOOLCHAIN_DIGEST || "") && DIGEST.test(process.env.GATE_APP_IMAGE_ID || "")
    && ["true", "false"].includes(process.env.GATE_DIRTY)
    && ["report-only", "enforced"].includes(process.env.CSP_STAGE), "Actual wrapper full identity required");
  const origin = requireWrapperOrigin(process.env.GATE_APP_URL);
  const wrapper = readRegular(root, ".gate/wrapper-current.json"), copy = readRegular(root, ".gate/full/wrapper-current.json");
  requireData(wrapper.bytes.equals(copy.bytes), "Current wrapper descriptor copies differ");
  const descriptor = JSON.parse(wrapper.bytes);
  requireData(closed(descriptor, ["schema", "invocation", "target", "sha", "tree_sha256", "toolchain_digest",
    "config_sha256", "config_path", "config_file_sha256"]) && descriptor.schema === 1 && descriptor.target === "full"
    && UUID.test(descriptor.invocation) && descriptor.config_path === ".gate/full/wrapper-kit-config.json"
    && HEX.test(descriptor.config_sha256) && HEX.test(descriptor.config_file_sha256), "Actual frozen full descriptor required");
  for (const [field, value] of [["sha", process.env.GATE_SHA], ["tree_sha256", process.env.GATE_TREE_SHA256],
    ["toolchain_digest", process.env.TOOLCHAIN_DIGEST]]) requireData(descriptor[field] === value, "Wrapper descriptor identity differs");
  const configFile = readRegular(root, descriptor.config_path), config = JSON.parse(configFile.bytes);
  requireData(closed(config, ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config", "config_sha256", "command"])
    && configFile.ref.sha256 === descriptor.config_file_sha256 && config.schema === 1 && config.target === "full"
    && config.sha === descriptor.sha && config.tree_sha256 === descriptor.tree_sha256
    && config.toolchain_digest === descriptor.toolchain_digest && config.config_sha256 === descriptor.config_sha256
    && hash(JSON.stringify(config.config)) === descriptor.config_sha256
    && config.config?.role === "consumer" && config.config?.app === "cat_de_roman_esti",
  "Actual frozen Cat configuration differs");
  const inputs = [wrapper.ref, copy.ref, configFile.ref];
  for (const name of ["versions.lock.json", "scripts/gui-browser-capability.mjs", "scripts/gui-repo-hook.mjs",
    "frontend/playwright.config.mjs", "frontend/playwright.gui.config.mjs", "frontend/package.json", "frontend/package-lock.json",
    "frontend/node_modules/playwright/package.json"]) inputs.push(readRegular(root, name, name.endsWith("package-lock.json") ? 8 * 1024 * 1024 : undefined).ref);
  const installed = JSON.parse(readRegular(root, "frontend/node_modules/playwright/package.json").bytes);
  const lock = JSON.parse(readRegular(root, "frontend/package-lock.json", 8 * 1024 * 1024).bytes);
  requireData(installed.name === "playwright" && typeof installed.version === "string"
    && installed.version === lock.packages?.["node_modules/playwright"]?.version, "Installed Playwright differs from owning lock");
  return { root, inputs, expected: { origin, invocation, sha: descriptor.sha, tree_sha256: descriptor.tree_sha256,
    versions_lock_sha256: inputs.find((item) => item.path === "versions.lock.json").sha256 },
  binding: { target: "full", invocation, wrapper_invocation: descriptor.invocation, sha: descriptor.sha,
    tree_sha256: descriptor.tree_sha256, toolchain_digest: descriptor.toolchain_digest,
    config_sha256: descriptor.config_sha256, config_file_sha256: descriptor.config_file_sha256,
    versions_lock_sha256: inputs.find((item) => item.path === "versions.lock.json").sha256,
    app_image_id: process.env.GATE_APP_IMAGE_ID, origin, dirty: process.env.GATE_DIRTY === "true", csp_stage: process.env.CSP_STAGE,
    playwright_version: installed.version } };
}

function outputDirectory(root, invocation) {
  const parent = path.join(root, ".gate/full/browser-capability");
  if (!fs.existsSync(parent)) fs.mkdirSync(parent, { mode: 0o700 });
  const info = fs.lstatSync(parent);
  requireData(info.isDirectory() && !info.isSymbolicLink() && fs.realpathSync.native(parent) === parent
    && info.uid === process.getuid() && (info.mode & 0o777) === 0o700, "Private capability parent required");
  const directory = path.join(parent, invocation);
  fs.mkdirSync(directory, { mode: 0o700 }); // existing output is refused, never overwritten/deleted
  return directory;
}
function writeExclusive(directory, name, value) {
  fs.writeFileSync(path.join(directory, name), JSON.stringify(value, null, 2) + "\n", { flag: "wx", mode: 0o600 });
}
async function deadline(operation, milliseconds, label) {
  let timer;
  try { return await Promise.race([operation, new Promise((_, reject) => { timer = setTimeout(() => reject(Error(label)), milliseconds); })]); }
  finally { clearTimeout(timer); }
}

async function main() {
  let acquired, directory, browser, context, record, stage = "context";
  let failed = false;
  const cleanup = [];
  try {
    acquired = acquireContext(process.argv[3]);
    directory = outputDirectory(acquired.root, acquired.binding.invocation);
    record = { check: CAPABILITY_CHECK, status: "fail", binding: acquired.binding, inputs: acquired.inputs,
      browser: null, projects: [], failure: null, cleanup };
    writeExclusive(directory, "context.json", { binding: acquired.binding, inputs: acquired.inputs });
    stage = "browser-launch";
    const { chromium, devices } = await deadline(import("../frontend/node_modules/playwright/index.mjs"), 5000, "Playwright import deadline");
    browser = await chromium.launch({ timeout: 10000 });
    record.browser = { version: browser.version(), executable_path: chromium.executablePath() };
    for (const [project, deviceName] of [["desktop", "Desktop Chrome"], ["mobile", "Pixel 7"]]) {
      stage = `${project}-context`;
      const device = devices[deviceName];
      requireData(device, "Existing Chromium device descriptor missing");
      context = await deadline(browser.newContext({ userAgent: device.userAgent, viewport: device.viewport,
        ...(device.screen ? { screen: device.screen } : {}), deviceScaleFactor: device.deviceScaleFactor,
        isMobile: device.isMobile, hasTouch: device.hasTouch, locale: "ro-RO", timezoneId: "Europe/Bucharest", reducedMotion: "reduce" }), 5000, "Browser context deadline");
      const observation = { project, requested_origin: acquired.expected.origin, document_origin: null,
        document_status: null, document_redirected: null, secure_context: null, locks: null, identity: null };
      record.projects.push(observation);
      try {
        const page = await deadline(context.newPage(), 5000, "Browser page deadline");
        page.setDefaultTimeout(5000);
        stage = `${project}-navigation`;
        const response = await page.goto(new URL("/", acquired.expected.origin).href, { waitUntil: "domcontentloaded", timeout: 10000 });
        requireData(response, "Actual root response missing");
        observation.document_status = response.status();
        observation.document_redirected = response.request().redirectedFrom() !== null;
        requireData(page.url() === new URL("/", acquired.expected.origin).href, "Actual root URL changed");
        const state = await deadline(page.evaluate(() => ({ origin: location.origin, secure: window.isSecureContext,
          request: typeof navigator.locks?.request === "function", query: typeof navigator.locks?.query === "function" })), 5000, "Browser observation deadline");
        observation.document_origin = state.origin; observation.secure_context = state.secure;
        observation.locks = { request: state.request, query: state.query, acquired: null, held: null, released: null, absent_after_release: null };
        requireData(observation.document_status === 200 && observation.document_redirected === false
          && observation.document_origin === acquired.expected.origin, "Actual root status/origin/redirect refused");
        stage = `${project}-identity`;
        const identity = await deadline(page.evaluate(async () => {
          const response = await fetch("/api/gui-build", { redirect: "error", cache: "no-store", credentials: "omit", signal: AbortSignal.timeout(5000) });
          const reader = response.body?.getReader();
          if (!reader) throw Error("Actual build body missing");
          const chunks = []; let size = 0;
          try {
            while (true) { const part = await reader.read(); if (part.done) break; size += part.value.length;
              if (size > 16384) throw Error("Build body bound exceeded"); chunks.push(...part.value); }
          } finally { await reader.cancel(); }
          return { url: response.url, status: response.status, redirected: response.redirected, bytes: chunks };
        }), 7000, "Actual build identity deadline");
        const raw = Buffer.from(identity.bytes);
        observation.identity = { url: identity.url, status: identity.status, redirected: identity.redirected,
          bytes: raw.length, sha256: hash(raw), raw_response: null, body: null };
        retainAndParseBuildResponseData(acquired.expected, project, observation.identity, raw, (bytes) => {
          // Fixed CLI writer: no caller-controlled sink/path or observer substitution.
          fs.writeFileSync(path.join(directory, `${project}-identity-response.bin`), bytes, { flag: "wx", mode: 0o600 });
        });
        // Bind the actual image source before refusing an untrusted served context.
        requireData(state.secure === true && state.request && state.query, "Actual secure-context/native Web Locks unavailable");
        stage = `${project}-native-lock`;
        const locked = await deadline(page.evaluate(async (name) => {
          const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 4000);
          let acquired = false, held = false, released = false;
          try {
            await navigator.locks.request(name, { mode: "exclusive", signal: controller.signal }, async (lock) => {
              acquired = !!lock && lock.name === name && lock.mode === "exclusive";
              const state = await navigator.locks.query();
              held = state.held.some((item) => item.name === name && item.mode === "exclusive");
            });
            released = true;
            const state = await navigator.locks.query();
            return { acquired, held, released, absent_after_release: !state.held.some((item) => item.name === name)
              && !state.pending.some((item) => item.name === name) };
          } finally { clearTimeout(timer); }
        }, `cat-gate-capability-${acquired.binding.invocation}-${project}`), 6000, "Native Web Lock deadline");
        Object.assign(observation.locks, locked);
        requireData(page.url() === new URL("/", acquired.expected.origin).href, "Final root URL changed");
        const final = await deadline(page.evaluate(() => ({ origin: location.origin, secure: window.isSecureContext })), 5000, "Final browser origin deadline");
        requireData(final.origin === acquired.expected.origin && final.secure === true, "Final browser origin/context changed");
        assertBrowserObservation(acquired.expected, observation);
      } catch (error) {
        record.failure = { stage, reason: "Actual project acquisition/assertion failed" };
        throw error;
      } finally {
        writeExclusive(directory, `${project}-observation.json`, observation);
        if (context) {
          stage = `${project}-context-cleanup`;
          try {
            await deadline(context.close(), 5000, "Browser context cleanup deadline");
            cleanup.push({ subject: project, status: "closed" }); context = undefined;
          } catch (error) { cleanup.push({ subject: project, status: "failed" }); throw error; }
        }
      }
    }
    stage = "input-recheck";
    for (const input of acquired.inputs) requireData(readRegular(acquired.root, input.path,
      input.path.endsWith("package-lock.json") ? 8 * 1024 * 1024 : undefined).ref.sha256 === input.sha256,
    "A bound capability input changed");
    record.status = "pass";
  } catch {
    failed = true;
    if (record && !record.failure) record.failure = { stage, reason: "Actual capability acquisition/assertion failed" };
    process.stderr.write(`Cat browser capability failed at ${record?.failure?.stage || stage}; partial owned evidence retained when acquired.\n`);
  } finally {
    for (const [subject, resource] of [["context", context], ["browser", browser]]) {
      if (resource) {
        try { await deadline(resource.close(), 5000, "Browser final cleanup deadline"); cleanup.push({ subject, status: "closed" }); }
        catch { failed = true; cleanup.push({ subject, status: "failed" }); }
      }
    }
    if (record) {
      if (failed) record.status = "fail";
      try { writeExclusive(directory, "result.json", record); process.stdout.write(JSON.stringify(record) + "\n"); }
      catch { failed = true; process.stderr.write("Capability result retention failed; original partial files retained.\n"); }
    }
  }
  // Bound this own process even if Chromium cleanup failed; that failure never passes.
  process.exit(failed ? 1 : 0);
}

// Importing the pure assertions/orchestration never starts a browser or touches files.
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  await main();
}
