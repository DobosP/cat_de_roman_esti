import assert from "node:assert/strict";

export const CAT_CSP_ROUTES = Object.freeze([
  "/", "/intrusul", "/perechi", "/conexiuni", "/alchimie?mode=challenges",
  "/alchimie?mode=explore", "/cald-rece", "/lant", "/clasament",
]);
export const FROZEN_BROWSER = Object.freeze({
  receipt: "legacy/original-bundle.json",
  receipt_sha256: "5f9897def4020047f9d0fa199ed96b2e52d6facd1cd878da35c65cafb4e78984",
  archive: "legacy/cat_de_roman_esti-legacy-93066854f67245d4b70c0ea97dc2401445a3218c.tgz",
  archive_sha256: "742bb11130fa2bf52ba5c64cb9cfd452f7d8ac3a4fd9dc6d77e8064a6b8fef65",
  manifest_sha256: "9ed68d3ff5f73bec7ced96e100ff5718043bcc7efc85cf3b3916df5c82867827",
  asset_root: "go-backend/embedfs/legacy", entry: "index.html", asset_prefix: "/",
});

export function catBrowserDescriptor(frozenPages = 0) {
  assert.ok(Number.isInteger(frozenPages) && frozenPages >= 0 && frozenPages < CAT_CSP_ROUTES.length,
    "Frozen page count must leave a nonempty current observation set");
  return { inventory: "frontend/e2e/gui-inventory.json", asset_root: "go-backend/embedfs/dist", entry: "index.html", asset_prefix: "/",
    ...(frozenPages > 0 ? { frozen: { ...FROZEN_BROWSER } } : {}) };
}

// The kit validates the source/image/policy and each selected manifest. This
// consumer projection additionally keeps the exact nine-route coverage intact.
export function catCspObservationSets(current, frozen) {
  assert.ok(Array.isArray(current) && current.length > 0 && Array.isArray(frozen), "Actual current and frozen observation arrays required");
  const all = [...current, ...frozen];
  assert.deepEqual(all.map((item) => item?.page).sort(), [...CAT_CSP_ROUTES].sort(), "Every Cat CSP route must be observed exactly once");
  assert.ok(all.every((item) => /^[a-f0-9]{64}$/.test(item.nonce_sha256))
    && new Set(all.map((item) => item.nonce_sha256)).size === all.length, "Every Cat document must use a distinct actual nonce");
  return { pages: all.length, nonceObservations: current,
    ...(frozen.length > 0 ? { frozen_pages: frozen.length, frozenNonceObservations: frozen } : {}) };
}
