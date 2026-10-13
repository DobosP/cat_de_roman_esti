import test from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { CAT_CSP_ROUTES, FROZEN_BROWSER, catBrowserDescriptor, catCspObservationSets } from "../../scripts/gui-csp-observations.mjs";
import { verifyFrozenDescriptor } from "../../tools/gui-bootstrap-webkit/scripts/csp-measurement.mjs";
import { readTarGz } from "../../tools/gui-bootstrap-webkit/scripts/kit-sync.mjs";

const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const observed = () => CAT_CSP_ROUTES.map((page, index) => ({ page, nonce_sha256: hash(`synthetic-nonce-${index}`) }));
void test("M2 current plus frozen observations count all nine routes and declare the frozen contract", () => {
  const rows = observed(), before = structuredClone(rows), result = catCspObservationSets(rows.slice(0, 4), rows.slice(4));
  assert.equal(result.pages, 9); assert.equal(result.nonceObservations.length, 4);
  assert.equal(result.frozen_pages, 5); assert.equal(result.frozenNonceObservations.length, 5);
  assert.deepEqual(catBrowserDescriptor(result.frozen_pages).frozen, FROZEN_BROWSER);
  assert.deepEqual(rows, before);
});
void test("all-current M3 omits the frozen declaration and both frozen fields", () => {
  const result = catCspObservationSets(observed(), []), descriptor = catBrowserDescriptor();
  assert.equal(result.pages, 9);
  for (const name of ["frozen_pages", "frozenNonceObservations"]) assert.equal(Object.hasOwn(result, name), false);
  assert.equal(Object.hasOwn(descriptor, "frozen"), false);
});
for (const value of [-1, 0.5, 9, 10, "5", null, NaN]) void test(`invalid frozen page count refuses ${String(value)}`, () => {
  assert.throws(() => catBrowserDescriptor(value), /Frozen page count/);
});
void test("partial, duplicate, unknown, empty-current and duplicate-nonce observations refuse", () => {
  const rows = observed();
  for (const [current, frozen] of [
    [rows.slice(0, 4), rows.slice(5)], [rows.slice(0, 4), [...rows.slice(4), rows[0]]],
    [[{ ...rows[0], page: "/unknown" }, ...rows.slice(1)], []], [[], rows],
    [[{ ...rows[0], nonce_sha256: rows[1].nonce_sha256 }, ...rows.slice(1)], []],
    [[{ ...rows[0], nonce_sha256: "unbound" }, ...rows.slice(1)], []],
  ]) assert.throws(() => catCspObservationSets(current, frozen));
});
void test("Cat descriptor loads the genuine frozen receipt/archive/manifest through delivered core validation", () => {
  // Exact committed historical bytes, supplied in memory. This checks consumer
  // compatibility only and creates no synthetic qualification receipt/tree.
  const root = fileURLToPath(new URL("../../", import.meta.url)), source = new Map();
  for (const name of [FROZEN_BROWSER.receipt, FROZEN_BROWSER.archive, FROZEN_BROWSER.archive + ".sha256"])
    source.set(name, fs.readFileSync(root + name));
  const archive = readTarGz(source.get(FROZEN_BROWSER.archive));
  for (const [name, entry] of archive) { assert.equal(entry.type, "file"); source.set(FROZEN_BROWSER.asset_root + "/" + name, entry.data); }
  const input = { read: (name) => { assert.ok(source.has(name), `unexpected frozen read: ${name}`); return source.get(name); },
    listFiles: () => [...archive.keys()], appURL: "http://localhost:8080" };
  const descriptor = verifyFrozenDescriptor(catBrowserDescriptor(5).frozen, input);
  assert.equal(descriptor.manifest[descriptor.entry].isEntry, true); assert.equal(archive.size, 30);
  assert.equal(hash(descriptor.manifestBytes), FROZEN_BROWSER.manifest_sha256);
  assert.ok(descriptor.eagerCss.size > 0);
  assert.throws(() => verifyFrozenDescriptor(FROZEN_BROWSER, { ...input, listFiles: () => [...archive.keys(), ".keep"] }), /missing\/extra/);
  assert.throws(() => verifyFrozenDescriptor({ ...FROZEN_BROWSER, entry: "missing.html" }, input), /manifest closure/);
  source.set(FROZEN_BROWSER.asset_root + "/.vite/manifest.json", Buffer.from("{}"));
  assert.throws(() => verifyFrozenDescriptor(FROZEN_BROWSER, input), /member differs/);
});
