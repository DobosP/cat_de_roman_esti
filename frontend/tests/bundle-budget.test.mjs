import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  ROMANIAN_FONT_SOURCES,
  assertRomanianFontSubsets,
  collectInitialBundleFiles,
  measureGzipFiles,
  parseLimitKiB,
} from "../scripts/check-bundle-budget.mjs";

test("initial bundle follows recursive static imports but excludes dynamic routes", () => {
  const manifest = {
    "src/main.tsx": {
      file: "assets/index.js",
      isEntry: true,
      imports: ["_vendor.js"],
      dynamicImports: ["src/screens/Game.tsx"],
      css: ["assets/index.css"],
      assets: ["assets/font.woff2"],
    },
    "_vendor.js": {
      file: "assets/vendor.js",
      imports: ["_shared.js"],
      css: ["assets/vendor.css"],
    },
    "_shared.js": { file: "assets/shared.js", imports: ["_vendor.js"] },
    "src/screens/Game.tsx": { file: "assets/Game.js", isDynamicEntry: true },
  };

  assert.deepEqual(collectInitialBundleFiles(manifest), [
    "assets/index.css",
    "assets/index.js",
    "assets/shared.js",
    "assets/vendor.css",
    "assets/vendor.js",
  ]);
});

test("gzip measurement reads only manifest-selected output files", () => {
  const root = mkdtempSync(join(tmpdir(), "cat-bundle-budget-"));
  try {
    mkdirSync(join(root, "assets"));
    writeFileSync(join(root, "assets", "index.js"), "export const answer = 42;\n".repeat(20));
    const measured = measureGzipFiles(root, ["assets/index.js"]);
    assert.equal(measured.length, 1);
    assert.equal(measured[0].file, "assets/index.js");
    assert.ok(measured[0].bytes > 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("budget configuration rejects zero, non-numeric, and infinite values", () => {
  assert.equal(parseLimitKiB("120"), 120);
  for (const bad of ["0", "-1", "wat", "Infinity"]) {
    assert.throws(() => parseLimitKiB(bad), /must be a positive number/);
  }
});

test("font guard requires both Romanian-capable subsets for both families", () => {
  const manifest = Object.fromEntries(
    ROMANIAN_FONT_SOURCES.map((src, index) => [`font-${index}`, { src }]),
  );
  assert.deepEqual(assertRomanianFontSubsets(manifest), [...ROMANIAN_FONT_SOURCES].sort());

  manifest.hebrew = {
    src: "node_modules/@fontsource-variable/fredoka/files/fredoka-hebrew-wght-normal.woff2",
  };
  assert.throws(() => assertRomanianFontSubsets(manifest), /Font assets must be exactly/);
});
