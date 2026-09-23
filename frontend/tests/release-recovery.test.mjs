import assert from "node:assert/strict";
import test from "node:test";

import {
  RELEASE_RECOVERY_KEY,
  installReleaseRecovery,
} from "../src/releaseRecovery.mjs";

function harness(initialMarker = null) {
  const values = new Map();
  if (initialMarker !== null) values.set(RELEASE_RECOVERY_KEY, initialMarker);
  const listeners = new Map();
  let reloads = 0;
  let prevented = 0;

  const target = {
    addEventListener(type, listener) {
      listeners.set(type, listener);
    },
    removeEventListener(type, listener) {
      if (listeners.get(type) === listener) listeners.delete(type);
    },
  };
  const storage = {
    getItem(key) {
      return values.get(key) ?? null;
    },
    setItem(key, value) {
      values.set(key, value);
    },
    removeItem(key) {
      values.delete(key);
    },
  };
  const location = {
    pathname: "/intrusul",
    search: "?daily=2026-07-30",
    hash: "",
    reload() {
      reloads += 1;
    },
  };
  const dispatch = () =>
    listeners.get("vite:preloadError")?.({
      preventDefault() {
        prevented += 1;
      },
    });

  return {
    target,
    storage,
    location,
    dispatch,
    values,
    reloads: () => reloads,
    prevented: () => prevented,
  };
}

test("a stale lazy chunk reloads once and prevents Vite's rejected import", () => {
  const app = harness();
  installReleaseRecovery(app);

  app.dispatch();
  assert.equal(app.prevented(), 1);
  assert.equal(app.reloads(), 1);
  assert.equal(
    app.values.get(RELEASE_RECOVERY_KEY),
    "/intrusul?daily=2026-07-30",
  );

  app.dispatch();
  assert.equal(app.prevented(), 2);
  assert.equal(app.reloads(), 1);
});

test("the loop guard follows client-side navigation before a lazy import fails", () => {
  const app = harness();
  installReleaseRecovery(app);
  app.location.pathname = "/perechi";
  app.location.search = "";

  app.dispatch();
  assert.equal(app.values.get(RELEASE_RECOVERY_KEY), "/perechi");
  assert.equal(app.reloads(), 1);
});

test("a slow failed chunk cannot outlive the guard and reload every document", (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  let marker = null;
  let reloads = 0;
  for (let document = 0; document < 4; document += 1) {
    const app = harness(marker);
    installReleaseRecovery(app);
    // Expire every timeout before the slow request fails and before the reload.
    t.mock.timers.runAll();
    app.dispatch();
    t.mock.timers.runAll();
    reloads += app.reloads();
    marker = app.values.get(RELEASE_RECOVERY_KEY);
  }
  assert.equal(reloads, 1);
  assert.equal(marker, "/intrusul?daily=2026-07-30");
});

test("cleanup removes the global listener", () => {
  const app = harness();
  const cleanup = installReleaseRecovery(app);
  cleanup();
  app.dispatch();
  assert.equal(app.prevented(), 0);
  assert.equal(app.reloads(), 0);
});

test("a denied default sessionStorage getter cannot abort application startup", (t) => {
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, "sessionStorage");
  Object.defineProperty(globalThis, "sessionStorage", {
    configurable: true,
    get() { throw new DOMException("Storage denied", "SecurityError"); },
  });
  t.after(() => {
    if (descriptor) Object.defineProperty(globalThis, "sessionStorage", descriptor);
    else delete globalThis.sessionStorage;
  });

  for (let document = 0; document < 3; document += 1) {
    const app = harness();
    delete app.storage;
    let cleanup;
    assert.doesNotThrow(() => { cleanup = installReleaseRecovery(app); });
    app.dispatch();
    app.dispatch();
    assert.equal(app.prevented(), 0, "the failed import must reach its error boundary");
    assert.equal(app.reloads(), 0, "no durable marker means no safe automatic reload");
    cleanup();
  }
});

for (const failure of ["getItem", "setItem", "silentWrite", "readBack"]) {
  test(`denied or ineffective storage (${failure}) cannot start a reload loop`, () => {
    const app = harness();
    let reads = 0;
    app.storage = {
      getItem() {
        reads += 1;
        if (failure === "getItem" || (failure === "readBack" && reads >= 2)) {
          throw new DOMException("Storage denied", "SecurityError");
        }
        return null;
      },
      setItem() {
        if (failure === "setItem") throw new DOMException("Storage denied", "SecurityError");
      },
    };
    assert.doesNotThrow(() => installReleaseRecovery(app));
    for (let attempt = 0; attempt < 4; attempt += 1) app.dispatch();
    assert.equal(app.prevented(), 0);
    assert.equal(app.reloads(), 0);
  });
}

test("a pending reload stays bounded even if the persisted marker is removed", () => {
  const app = harness();
  installReleaseRecovery(app);
  app.dispatch();
  app.values.clear();
  app.dispatch();
  assert.equal(app.reloads(), 1);
  assert.equal(app.prevented(), 2);
});

test("the durable marker prevents recovery from looping across documents", (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const initial = harness();
  installReleaseRecovery(initial);
  initial.dispatch();
  assert.equal(initial.reloads(), 1);

  const reloaded = harness(initial.values.get(RELEASE_RECOVERY_KEY));
  installReleaseRecovery(reloaded);
  reloaded.dispatch();
  reloaded.dispatch();
  assert.equal(reloaded.reloads(), 0);
  assert.equal(reloaded.prevented(), 0);
  t.mock.timers.runAll();
  assert.equal(reloaded.values.get(RELEASE_RECOVERY_KEY), "/intrusul?daily=2026-07-30");
});
