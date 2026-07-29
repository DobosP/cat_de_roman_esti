import assert from "node:assert/strict";
import test from "node:test";

import {
  RELEASE_RECOVERY_KEY,
  RELEASE_RECOVERY_RESET_MS,
  installReleaseRecovery,
} from "../src/releaseRecovery.mjs";

function harness(initialMarker = null) {
  const values = new Map();
  if (initialMarker !== null) values.set(RELEASE_RECOVERY_KEY, initialMarker);
  const listeners = new Map();
  const scheduled = [];
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
  const schedule = (callback, delay) => scheduled.push({ callback, delay });
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
    schedule,
    dispatch,
    scheduled,
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

test("a successful reloaded bundle clears the loop guard after a bounded delay", () => {
  const page = "/intrusul?daily=2026-07-30";
  const app = harness(page);
  installReleaseRecovery(app);

  assert.equal(app.scheduled.length, 1);
  assert.equal(app.scheduled[0].delay, RELEASE_RECOVERY_RESET_MS);
  app.scheduled[0].callback();
  assert.equal(app.values.has(RELEASE_RECOVERY_KEY), false);
});

test("cleanup removes the global listener", () => {
  const app = harness();
  const cleanup = installReleaseRecovery(app);
  cleanup();
  app.dispatch();
  assert.equal(app.prevented(), 0);
  assert.equal(app.reloads(), 0);
});
