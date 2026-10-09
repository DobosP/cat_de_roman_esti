import test from "node:test";
import assert from "node:assert/strict";
import { CAPABILITY_CHECK, assertBrowserObservation, assertBuildResponse,
  requireWrapperOrigin, checkFullBrowserCapability, retainAndParseBuildResponseData } from "../../scripts/gui-browser-capability.mjs";

// AUTHORED NOT RUN. In-memory NON-RELEASE DATA only: no browser, filesystem,
// environment changes, command, gate receipt or physical evidence is fabricated.
const expected = { origin: "http://localhost:8080", invocation: "12345678-1234-4234-8234-123456789abc", sha: "a".repeat(40),
  tree_sha256: "b".repeat(64), versions_lock_sha256: "c".repeat(64) };
function observation(project = "desktop") {
  return { project, requested_origin: expected.origin, document_origin: expected.origin,
    document_status: 200, document_redirected: false, secure_context: true,
    locks: { request: true, query: true, acquired: true, held: true, released: true, absent_after_release: true },
    identity: { url: expected.origin + "/api/gui-build", status: 200, redirected: false,
      bytes: 321, sha256: "d".repeat(64),
      raw_response: { path: `.gate/full/browser-capability/${expected.invocation}/${project}-identity-response.bin`,
        bytes: 321, sha256: "d".repeat(64) }, body: { sha: expected.sha, tree_sha256: expected.tree_sha256,
        manifest_sha256: "e".repeat(64), versions_lock_sha256: expected.versions_lock_sha256 } } };
}

void test("synthetic complete observations conform without changing caller data or emitting a receipt", () => {
  for (const project of ["desktop", "mobile"]) {
    const value = observation(project), before = structuredClone(value);
    assert.equal(assertBrowserObservation(expected, value), undefined);
    assert.deepEqual(value, before);
  }
});

const refusals = [
  ["insecure context", (value) => { value.secure_context = false; }],
  ["unacquired secure context", (value) => { value.secure_context = null; }],
  ["wrong document origin", (value) => { value.document_origin = "http://roedu-gate.test:8080"; }],
  ["wrong requested origin", (value) => { value.requested_origin = "http://127.0.0.1:8080"; }],
  ["redirected document", (value) => { value.document_redirected = true; }],
  ["missing root response", (value) => { value.document_status = null; }],
  ["non200 root", (value) => { value.document_status = 503; }],
  ["foreign project", (value) => { value.project = "synthetic-engine"; }],
  ["missing native request", (value) => { value.locks.request = false; }],
  ["missing native query", (value) => { value.locks.query = false; }],
  ["failed acquisition", (value) => { value.locks.acquired = false; }],
  ["held lock never queried", (value) => { value.locks.held = null; }],
  ["release failed", (value) => { value.locks.released = false; }],
  ["lock remains held", (value) => { value.locks.absent_after_release = false; }],
  ["missing lock observations", (value) => { value.locks = null; }],
  ["missing actual identity", (value) => { value.identity = null; }],
  ["foreign identity endpoint", (value) => { value.identity.url = "http://127.0.0.1:8080/api/gui-build"; }],
  ["core endpoint substitution", (value) => { value.identity.url = expected.origin + "/__gate/identity"; }],
  ["redirected identity", (value) => { value.identity.redirected = true; }],
  ["identity non200", (value) => { value.identity.status = 503; }],
  ["empty identity bytes", (value) => { value.identity.bytes = 0; }],
  ["unbounded identity", (value) => { value.identity.bytes = 16385; }],
  ["identity hash missing", (value) => { value.identity.sha256 = "UNSET"; }],
  ["stale app source", (value) => { value.identity.body.sha = "f".repeat(40); }],
  ["stale app tree", (value) => { value.identity.body.tree_sha256 = "f".repeat(64); }],
  ["stale root versions", (value) => { value.identity.body.versions_lock_sha256 = "f".repeat(64); }],
  ["missing manifest identity", (value) => { delete value.identity.body.manifest_sha256; }],
  ["unknown identity field", (value) => { value.identity.body.app_image_id = "sha256:" + "f".repeat(64); }],
  ["future callback claim", (value) => { value.observer_passed = true; }],
];
for (const [name, mutate] of refusals) void test("refuses " + name, () => {
  const value = observation(); mutate(value);
  assert.throws(() => assertBrowserObservation(expected, value));
});

void test("closed DATA refuses an accessor without invoking it", () => {
  const value = observation(); let invoked = false;
  Object.defineProperty(value, "secure_context", { enumerable: true, get() { invoked = true; return true; } });
  assert.throws(() => assertBrowserObservation(expected, value));
  assert.equal(invoked, false);
});

void test("identity-only assertion binds source before secure-context refusal", () => {
  const value = observation(); value.secure_context = false;
  assert.equal(assertBuildResponse(expected, value.identity), undefined);
  value.identity.body.sha = "f".repeat(40);
  assert.throws(() => assertBuildResponse(expected, value.identity));
});

void test("manifest comparison remains the later full witness obligation", () => {
  const value = observation(); value.identity.body.manifest_sha256 = "f".repeat(64);
  assert.equal(assertBuildResponse(expected, value.identity), undefined);
  // This only admits a present actual hash in DATA; no unacquired local manifest is asserted.
});

for (const value of ["", "http://user:pass@localhost:8080", "http://localhost:8080/",
  "http://localhost:8080/other", "http://localhost:8080?private=1", "http://localhost:8080#fragment",
  "file:///work/index.html", "HTTP://LOCALHOST:8080"]) void test("refuses noncanonical wrapper URL " + value, () => {
  assert.throws(() => requireWrapperOrigin(value));
});

void test("old wrapper alias is never silently changed to localhost or declared secure", () => {
  const origin = "http://roedu-gate.test:8080";
  assert.equal(requireWrapperOrigin(origin), origin);
  const value = observation(); value.requested_origin = origin; value.document_origin = origin;
  value.identity.url = origin + "/api/gui-build"; value.secure_context = false;
  assert.throws(() => assertBrowserObservation({ ...expected, origin }, value), /not secure/);
});

// The double verifies only the real exported fixed-command seam and returned refusal.
// It executes no process and supplies no observer to the real CLI or browser.
function hookDouble(failure = false) {
  const calls = [];
  return { context: { target: "full", invocation: "12345678-1234-4234-8234-123456789abc" }, checks: [], calls,
    check(name, operation) { try { operation(); this.checks.push({ name, status: "pass" }); }
      catch { this.checks.push({ name, status: "fail" }); } },
    run(...args) { calls.push(args); if (failure) throw Error("NON-RELEASE simulated command refusal"); },
  };
}
void test("full seam owns exactly one fixed command and literal current invocation", () => {
  const hook = hookDouble();
  assert.equal(checkFullBrowserCapability(hook), true);
  assert.deepEqual(hook.calls, [["node", ["scripts/gui-browser-capability.mjs", "full", hook.context.invocation]]]);
  assert.deepEqual(hook.checks, [{ name: CAPABILITY_CHECK, status: "pass" }]);
});
void test("recorded command refusal returns false so full must stop before nativeUnit", () => {
  const hook = hookDouble(true), continuation = [];
  if (checkFullBrowserCapability(hook)) continuation.push("nativeUnit");
  assert.deepEqual(continuation, []);
  assert.deepEqual(hook.checks, [{ name: CAPABILITY_CHECK, status: "fail" }]);
  assert.equal(hook.calls.length, 1);
});
void test("unit is not rerouted through full browser capability", () => {
  const hook = hookDouble(); hook.context.target = "unit";
  assert.throws(() => checkFullBrowserCapability(hook), /full invocation/);
  assert.deepEqual(hook.calls, []);
});
void test("invalid invocation cannot choose a helper argument or output path", () => {
  const hook = hookDouble(); hook.context.invocation = "../../other-worker";
  assert.throws(() => checkFullBrowserCapability(hook), /full invocation/);
  assert.deepEqual(hook.calls, []);
});

// Synthetic in-memory retention journal only. It is not a file, gate artifact,
// browser/CLI substitute or physical acquisition claim. Actual wx/mode/cleanup
// and retained bytes remain mandatory future Linux checks, AUTHORED NOT RUN.
function acquiredIdentityBytes(body) {
  const raw = Buffer.from(typeof body === "string" ? body : JSON.stringify(body));
  const identity = { ...observation().identity, bytes: raw.length, raw_response: null, body: null };
  return { raw, identity };
}
function identityBody() { return structuredClone(observation().identity.body); }

void test("raw write is called before malformed JSON refuses, retaining bound partial ref", () => {
  const { raw, identity } = acquiredIdentityBytes("not JSON");
  const journal = [];
  assert.throws(() => retainAndParseBuildResponseData(expected, "desktop", identity, raw, (bytes) => {
    assert.equal(identity.raw_response, null); assert.equal(identity.body, null);
    journal.push(Buffer.from(bytes));
  }), SyntaxError);
  assert.deepEqual(journal, [raw]);
  assert.equal(identity.raw_response.path, `.gate/full/browser-capability/${expected.invocation}/desktop-identity-response.bin`);
  assert.equal(identity.raw_response.bytes, raw.length);
  assert.equal(identity.raw_response.sha256, "62b8125a6f6d924ec53345b5fcd58ca3ed3f5e7d51e2e146e5f1346508acce69"); // independent literal-byte hash
  assert.equal(identity.body, null);
});

for (const [name, mutate] of [
  ["wrong source", (body) => { body.sha = "f".repeat(40); }],
  ["wrong tree", (body) => { body.tree_sha256 = "f".repeat(64); }],
  ["wrong versions", (body) => { body.versions_lock_sha256 = "f".repeat(64); }],
  ["unknown field", (body) => { body.observer_passed = true; }],
]) void test("raw response is retained before strict " + name + " refusal", () => {
  const body = identityBody(); mutate(body);
  const { raw, identity } = acquiredIdentityBytes(body), journal = [];
  // Matching acquired raw digest is established by the seam, not supplied by a sink.
  assert.throws(() => retainAndParseBuildResponseData(expected, "desktop", identity, raw, (bytes) => {
    journal.push(Buffer.from(bytes)); return { status: "pass" }; // ignored NON-RELEASE return
  }));
  assert.deepEqual(journal, [raw]); assert.equal(identity.raw_response.bytes, raw.length);
  assert.equal(identity.body, null);
});

void test("retention error refuses before parsing and creates no successful ref", () => {
  const { raw, identity } = acquiredIdentityBytes("not JSON"), sentinel = Error("NON-RELEASE sink collision");
  let attempts = 0;
  assert.throws(() => retainAndParseBuildResponseData(expected, "desktop", identity, raw, () => {
    attempts += 1; throw sentinel;
  }), (error) => error === sentinel);
  assert.equal(attempts, 1); assert.equal(identity.raw_response, null); assert.equal(identity.body, null);
});

void test("successful synthetic retention binds exact raw hash/length without sink success authority", () => {
  const { raw, identity } = acquiredIdentityBytes(identityBody());
  assert.equal(retainAndParseBuildResponseData(expected, "mobile", identity, raw, () => false), undefined);
  assert.equal(identity.raw_response.bytes, raw.length);
  assert.equal(identity.raw_response.sha256, identity.sha256);
  assert.deepEqual(identity.body, identityBody());
});

for (const [name, mutate] of [
  ["unacquired raw ref", (value) => { value.identity.raw_response = null; }],
  ["foreign invocation", (value) => { value.identity.raw_response.path = value.identity.raw_response.path.replace(expected.invocation, "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"); }],
  ["other project", (value) => { value.identity.raw_response.path = value.identity.raw_response.path.replace("desktop-", "mobile-"); }],
  ["traversal ref", (value) => { value.identity.raw_response.path += "/../outside"; }],
  ["raw byte mismatch", (value) => { value.identity.raw_response.bytes += 1; }],
  ["raw digest mismatch", (value) => { value.identity.raw_response.sha256 = "f".repeat(64); }],
  ["extra raw-ref field", (value) => { value.identity.raw_response.success = true; }],
]) void test("refuses " + name + " in partial artifact DATA", () => {
  const value = observation(); mutate(value);
  assert.throws(() => assertBrowserObservation(expected, value));
});

void test("an acquired empty response is retained as zero bytes before JSON refusal", () => {
  const { raw, identity } = acquiredIdentityBytes(""); let attempts = 0;
  assert.throws(() => retainAndParseBuildResponseData(expected, "desktop", identity, raw, (bytes) => {
    attempts += 1; assert.equal(bytes.length, 0);
  }), SyntaxError);
  assert.equal(attempts, 1); assert.equal(identity.raw_response.bytes, 0);
  assert.equal(identity.raw_response.sha256, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
  assert.equal(identity.body, null);
});
