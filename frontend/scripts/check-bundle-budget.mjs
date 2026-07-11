import { existsSync, readFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

export const DEFAULT_INITIAL_GZIP_LIMIT_KIB = 120;
export const ROMANIAN_FONT_SOURCES = [
  "node_modules/@fontsource-variable/fredoka/files/fredoka-latin-ext-wght-normal.woff2",
  "node_modules/@fontsource-variable/fredoka/files/fredoka-latin-wght-normal.woff2",
  "node_modules/@fontsource-variable/inter/files/inter-latin-ext-wght-normal.woff2",
  "node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2",
];

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const DEFAULT_OUTPUT_DIR = fileURLToPath(
  new URL("../../cat_de_roman_esti/web/static/", import.meta.url),
);

function isCodeOrStyle(path) {
  return /\.(?:css|[cm]?js)$/.test(path);
}

/**
 * Return the JS/CSS files required by every entry before any dynamic import.
 * Vite's `imports` edges are static; `dynamicImports` are intentionally excluded.
 */
export function collectInitialBundleFiles(manifest) {
  const entries = Object.entries(manifest)
    .filter(([, chunk]) => chunk?.isEntry)
    .map(([key]) => key);
  if (entries.length === 0) {
    throw new Error("Vite manifest contains no entry chunk");
  }

  const visited = new Set();
  const files = new Set();

  function visit(key) {
    if (visited.has(key)) return;
    const chunk = manifest[key];
    if (!chunk) {
      throw new Error(`Vite manifest references missing static import: ${key}`);
    }
    visited.add(key);
    if (typeof chunk.file === "string" && isCodeOrStyle(chunk.file)) {
      files.add(chunk.file);
    }
    for (const css of chunk.css ?? []) {
      if (typeof css === "string" && isCodeOrStyle(css)) files.add(css);
    }
    for (const imported of chunk.imports ?? []) visit(imported);
  }

  for (const entry of entries) visit(entry);
  return [...files].sort();
}

function resolveInside(root, relativePath) {
  const absolute = resolve(root, relativePath);
  const prefix = root.endsWith(sep) ? root : `${root}${sep}`;
  if (!absolute.startsWith(prefix)) {
    throw new Error(`Bundle path escapes output directory: ${relativePath}`);
  }
  return absolute;
}

export function measureGzipFiles(outputDir, files) {
  const root = resolve(outputDir);
  return files.map((file) => {
    const path = resolveInside(root, file);
    if (!existsSync(path)) throw new Error(`Manifest asset is missing: ${file}`);
    return { file, bytes: gzipSync(readFileSync(path), { level: 9 }).byteLength };
  });
}

export function parseLimitKiB(raw = String(DEFAULT_INITIAL_GZIP_LIMIT_KIB)) {
  const value = Number(raw);
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error("INITIAL_BUNDLE_GZIP_LIMIT_KIB must be a positive number");
  }
  return value;
}

export function assertRomanianFontSubsets(manifest) {
  const actual = Object.values(manifest)
    .map((chunk) => chunk?.src)
    .filter((source) => typeof source === "string" && source.endsWith(".woff2"))
    .sort();
  const expected = [...ROMANIAN_FONT_SOURCES].sort();
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      "Font assets must be exactly the Fredoka/Inter Latin and Latin Extended subsets; " +
        `found: ${actual.join(", ") || "none"}`,
    );
  }
  return actual;
}

export function checkInitialBundle({
  outputDir = DEFAULT_OUTPUT_DIR,
  limitKiB = parseLimitKiB(process.env.INITIAL_BUNDLE_GZIP_LIMIT_KIB),
} = {}) {
  const manifestPath = resolve(outputDir, ".vite", "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const fonts = assertRomanianFontSubsets(manifest);
  const measurements = measureGzipFiles(outputDir, collectInitialBundleFiles(manifest));
  const totalBytes = measurements.reduce((total, item) => total + item.bytes, 0);
  const limitBytes = limitKiB * 1024;

  console.log(`Initial JS/CSS gzip budget (limit ${limitKiB.toFixed(1)} KiB):`);
  for (const { file, bytes } of measurements) {
    console.log(`  ${(bytes / 1024).toFixed(2).padStart(7)} KiB  ${file}`);
  }
  console.log(`  ${(totalBytes / 1024).toFixed(2).padStart(7)} KiB  total`);
  console.log(`Romanian font subsets: ${fonts.length} (Latin + Latin Extended only)`);

  if (totalBytes > limitBytes) {
    throw new Error(
      `Initial JS/CSS is ${(totalBytes / 1024).toFixed(2)} KiB gzip; ` +
        `budget is ${limitKiB.toFixed(2)} KiB`,
    );
  }
  return { measurements, totalBytes, limitBytes };
}

if (process.argv[1] && resolve(process.argv[1]) === SCRIPT_PATH) {
  try {
    checkInitialBundle();
  } catch (error) {
    console.error(error instanceof Error ? error.message : error);
    process.exitCode = 1;
  }
}
