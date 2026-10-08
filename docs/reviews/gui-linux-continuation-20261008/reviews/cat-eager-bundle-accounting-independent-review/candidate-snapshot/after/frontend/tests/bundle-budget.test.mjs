import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  ROMANIAN_FONT_SOURCES,
  assertRomanianFontSubsets,
  checkInitialBundle,
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

const eagerAccountRoot = "src/components/AccountBar.tsx";

function eagerAccountManifest() {
  return {
    "src/main.tsx": {
      file: "assets/index.js",
      isEntry: true,
      imports: ["_shared.js"],
      dynamicImports: [eagerAccountRoot, "src/screens/Game.tsx"],
      css: ["assets/index.css"],
    },
    "_shared.js": { file: "assets/shared.js", imports: ["_vendor.js"] },
    "_vendor.js": {
      file: "assets/vendor.js",
      css: ["assets/vendor.css"],
      imports: ["_shared.js"],
    },
    [eagerAccountRoot]: {
      file: "assets/account.js",
      isDynamicEntry: true,
      css: ["assets/account.css", "assets/vendor.css"],
      imports: ["_account-vendor.js", "_shared.js", "src/main.tsx"],
      dynamicImports: ["src/screens/Game.tsx"],
    },
    "_account-vendor.js": {
      file: "assets/account-vendor.js",
      css: ["assets/account-vendor.css"],
      imports: ["_account-nested.js", "_shared.js"],
    },
    "_account-nested.js": {
      file: "assets/account-nested.js",
      imports: ["_account-vendor.js"],
    },
    "src/screens/Game.tsx": {
      file: "assets/Game.js",
      css: ["assets/Game.css"],
      isDynamicEntry: true,
    },
    ...Object.fromEntries(
      ROMANIAN_FONT_SOURCES.map((src, index) => [`font-${index}`, { src }]),
    ),
  };
}

const eagerAccountStaticFiles = [
  "assets/index.css",
  "assets/index.js",
  "assets/shared.js",
  "assets/vendor.css",
  "assets/vendor.js",
];

const eagerAccountInitialFiles = [
  "assets/account-nested.js",
  "assets/account-vendor.css",
  "assets/account-vendor.js",
  "assets/account.css",
  "assets/account.js",
  ...eagerAccountStaticFiles,
].sort();

function writeEagerAccountManifest(root, manifest) {
  writeFileSync(join(root, ".vite", "manifest.json"), JSON.stringify(manifest));
}

function writeEagerAccountOutput(root) {
  const manifest = eagerAccountManifest();
  mkdirSync(join(root, ".vite"), { recursive: true });
  mkdirSync(join(root, "assets"), { recursive: true });
  const files = {
    "assets/index.js": "export const entryLabel = 'Acasa';\n",
    "assets/index.css": ".home { display: grid; gap: 1rem; }\n",
    "assets/shared.js": "export const sharedLabel = 'Romania';\n",
    "assets/vendor.js": "export const renderMode = 'fixture';\n",
    "assets/vendor.css": ".shared-control { padding: 0.5rem; }\n",
    "assets/account.js": Array.from(
      { length: 256 },
      (_, index) => `export const accountLabel${index} = '${index}-${(index * 73 + 19) % 9973}';`,
    ).join("\n"),
    "assets/account.css": Array.from(
      { length: 128 },
      (_, index) => `.account-state-${index} { margin-inline: ${(index * 11 + 3) % 97}px; }`,
    ).join("\n"),
    "assets/account-vendor.js": "export const accountStatus = 'anonymous';\n",
    "assets/account-vendor.css": ".account-status { border-radius: 0.5rem; }\n",
    "assets/account-nested.js": "export const accountAction = 'sign-in';\n",
    "assets/Game.js": "export const gameLabel = 'Intrusul';\n",
    "assets/Game.css": ".game-board { display: flex; }\n",
  };
  for (const [file, source] of Object.entries(files)) {
    writeFileSync(join(root, file), source);
  }
  writeEagerAccountManifest(root, manifest);
  return manifest;
}

function eagerAccountMeasurements(root, manifest) {
  const staticMeasurements = measureGzipFiles(root, collectInitialBundleFiles(manifest));
  const fullMeasurements = measureGzipFiles(
    root,
    collectInitialBundleFiles(manifest, { eagerRoots: [eagerAccountRoot] }),
  );
  const staticBytes = staticMeasurements.reduce((sum, item) => sum + item.bytes, 0);
  const fullBytes = fullMeasurements.reduce((sum, item) => sum + item.bytes, 0);
  assert.ok(fullBytes > staticBytes, "eager account JS/CSS must add measured gzip bytes");
  const limitKiB = parseLimitKiB(String((staticBytes + fullBytes) / (2 * 1024)));
  return { staticMeasurements, fullMeasurements, staticBytes, fullBytes, limitKiB };
}

test("explicit eager account roots include recursive JS/CSS once and exclude game routes", () => {
  const manifest = eagerAccountManifest();
  assert.deepEqual(collectInitialBundleFiles(manifest), eagerAccountStaticFiles);
  const selected = collectInitialBundleFiles(manifest, { eagerRoots: [eagerAccountRoot] });
  assert.deepEqual(selected, eagerAccountInitialFiles);
  assert.equal(new Set(selected).size, selected.length);
  assert.equal(selected.includes("assets/Game.js"), false);
  assert.equal(selected.includes("assets/Game.css"), false);
});

test("explicit eager account roots reject missing or malformed chunk files", () => {
  for (const file of [undefined, null, 42, "", "assets/account.png"]) {
    const manifest = eagerAccountManifest();
    if (file === undefined) {
      delete manifest[eagerAccountRoot].file;
    } else {
      manifest[eagerAccountRoot].file = file;
    }
    assert.deepEqual(collectInitialBundleFiles(manifest), eagerAccountStaticFiles);
    assert.throws(
      () => collectInitialBundleFiles(manifest, { eagerRoots: [eagerAccountRoot] }),
      /required eager asset/,
    );
  }
  const missingRoot = eagerAccountManifest();
  delete missingRoot[eagerAccountRoot];
  assert.deepEqual(collectInitialBundleFiles(missingRoot), eagerAccountStaticFiles);
  assert.throws(
    () => collectInitialBundleFiles(missingRoot, { eagerRoots: [eagerAccountRoot] }),
    /required eager root/,
  );
});

test("initial budget counts eager account bytes that the static-only closure misses", () => {
  const root = mkdtempSync(join(tmpdir(), "cat-eager-account-budget-"));
  try {
    const manifest = writeEagerAccountOutput(root);
    const measured = eagerAccountMeasurements(root, manifest);
    const staticResult = {
      measurements: measured.staticMeasurements,
      totalBytes: measured.staticBytes,
      limitBytes: measured.limitKiB * 1024,
    };
    assert.deepEqual(staticResult.measurements.map(({ file }) => file), eagerAccountStaticFiles);
    assert.ok(staticResult.totalBytes < staticResult.limitBytes, "static-only accounting fits this same limit");
    assert.ok(measured.fullBytes > staticResult.limitBytes, "eager account closure exceeds this same limit");
    assert.throws(
      () => checkInitialBundle({ outputDir: root, limitKiB: measured.limitKiB }),
      /Initial JS\/CSS.*budget/,
    );
    const passing = checkInitialBundle({
      outputDir: root,
      limitKiB: parseLimitKiB(String(measured.fullBytes / 1024)),
    });
    assert.equal(passing.totalBytes, measured.fullBytes);
    assert.equal(passing.limitBytes, measured.fullBytes);
    assert.deepEqual(passing.measurements.map(({ file }) => file), eagerAccountInitialFiles);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("initial budget requires the account root even when the caller supplies empty eager roots", () => {
  const root = mkdtempSync(join(tmpdir(), "cat-required-account-root-"));
  try {
    const manifest = writeEagerAccountOutput(root);
    const { fullBytes } = eagerAccountMeasurements(root, manifest);
    const limitKiB = parseLimitKiB(String((fullBytes + 1) / 1024));
    delete manifest[eagerAccountRoot];
    writeEagerAccountManifest(root, manifest);
    assert.deepEqual(collectInitialBundleFiles(manifest), eagerAccountStaticFiles);
    assert.throws(() => checkInitialBundle({ outputDir: root, limitKiB }), /required eager root/);
    assert.throws(
      () => checkInitialBundle({ outputDir: root, limitKiB, eagerRoots: [] }),
      /required eager root/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("initial budget fails closed for missing account JS, CSS, or nested import output", () => {
  for (const missingFile of ["assets/account.js", "assets/account.css", "assets/account-nested.js"]) {
    const root = mkdtempSync(join(tmpdir(), "cat-missing-account-output-"));
    try {
      const manifest = writeEagerAccountOutput(root);
      const { fullBytes } = eagerAccountMeasurements(root, manifest);
      const limitKiB = parseLimitKiB(String((fullBytes + 1) / 1024));
      rmSync(join(root, missingFile));
      assert.throws(
        () => checkInitialBundle({ outputDir: root, limitKiB }),
        (error) => {
          assert.match(error.message, /Manifest asset is missing/);
          assert.ok(error.message.includes(missingFile), `missing output path must be identified: ${missingFile}`);
          return true;
        },
        missingFile,
      );
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  }
});

test("eager root options require bounded own string keys and deduplicate repeated roots", () => {
  const manifest = eagerAccountManifest();
  assert.deepEqual(
    collectInitialBundleFiles(manifest, { eagerRoots: [eagerAccountRoot, eagerAccountRoot] }),
    eagerAccountInitialFiles,
  );
  for (const eagerRoots of [
    null,
    eagerAccountRoot,
    {},
    [42],
    [""],
    ["src/components/MissingAccount.tsx"],
    Array(Object.keys(manifest).length + 1).fill(eagerAccountRoot),
  ]) {
    assert.throws(
      () => collectInitialBundleFiles(manifest, { eagerRoots }),
      /required eager root/,
    );
  }
  const inheritedRoot = "src/components/InheritedAccount.tsx";
  Object.setPrototypeOf(manifest, { [inheritedRoot]: { file: "assets/inherited-account.js" } });
  assert.throws(
    () => collectInitialBundleFiles(manifest, { eagerRoots: [inheritedRoot] }),
    /required eager root/,
  );
});

test("eager account closure rejects malformed shared files, CSS, and static import edges", () => {
  const cases = [
    {
      name: "shared entry import file",
      change: (manifest) => { manifest["_shared.js"].file = 42; },
      message: /required eager asset/,
    },
    {
      name: "nested account import file",
      change: (manifest) => { delete manifest["_account-nested.js"].file; },
      message: /required eager asset/,
    },
    {
      name: "non-array CSS",
      change: (manifest) => { manifest[eagerAccountRoot].css = "assets/account.css"; },
      message: /required eager asset/,
    },
    {
      name: "null CSS",
      change: (manifest) => { manifest[eagerAccountRoot].css = null; },
      message: /required eager asset/,
    },
    {
      name: "non-string CSS file",
      change: (manifest) => { manifest[eagerAccountRoot].css = [42]; },
      message: /required eager asset/,
    },
    {
      name: "non-code CSS file",
      change: (manifest) => { manifest[eagerAccountRoot].css = ["assets/account.png"]; },
      message: /required eager asset/,
    },
    {
      name: "non-array imports",
      change: (manifest) => { manifest[eagerAccountRoot].imports = "_account-vendor.js"; },
      message: /required eager import/,
    },
    {
      name: "null imports",
      change: (manifest) => { manifest[eagerAccountRoot].imports = null; },
      message: /required eager import/,
    },
    {
      name: "non-string import",
      change: (manifest) => { manifest[eagerAccountRoot].imports = [42]; },
      message: /required eager import/,
    },
    {
      name: "empty import",
      change: (manifest) => { manifest[eagerAccountRoot].imports = [""]; },
      message: /required eager import/,
    },
    {
      name: "missing import",
      change: (manifest) => { manifest[eagerAccountRoot].imports = ["_missing-account.js"]; },
      message: /required eager import/,
    },
    {
      name: "inherited import",
      change: (manifest) => {
        manifest[eagerAccountRoot].imports = ["_inherited-account.js"];
        Object.setPrototypeOf(manifest, { "_inherited-account.js": { file: "assets/inherited-account.js" } });
      },
      message: /required eager import/,
    },
  ];
  for (const { name, change, message } of cases) {
    const manifest = eagerAccountManifest();
    change(manifest);
    assert.throws(
      () => collectInitialBundleFiles(manifest, { eagerRoots: [eagerAccountRoot] }),
      message,
      name,
    );
  }
});
