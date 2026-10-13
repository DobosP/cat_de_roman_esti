import * as fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { regularPath, relativePath } from './locate-kit.mjs';
import { readTarGz } from './kit-sync.mjs';

const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const HEX = /^[a-f0-9]{64}$/;
const SHA = /^[a-f0-9]{40}(?:[a-f0-9]{24})?$/;
const integer = value => Number.isInteger(value) && value >= 0;
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const fail = message => { throw Error(message); };
const demand = (condition, message) => { if (!condition) fail(message); };
const fields = (value, names) => value && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).length === names.length && names.every(name => Object.hasOwn(value, name));
const frozenFields = ['receipt', 'receipt_sha256', 'archive', 'archive_sha256', 'manifest_sha256', 'asset_root', 'entry', 'asset_prefix'];
function assetPath(value) {
  relativePath(value);
  demand(value.split('/').every(part => /^[A-Za-z0-9_@.-]+$/.test(part)), 'Nonliteral manifest asset path');
  return value;
}
function list(value = []) {
  demand(Array.isArray(value) && new Set(value).size === value.length && value.every(item => typeof item === 'string'), 'Invalid manifest asset list');
  return value;
}
function appOrigin(appURL) {
  const url = new URL(appURL);
  demand(['http:', 'https:'].includes(url.protocol) && !url.username && !url.password && !url.search && !url.hash, 'Invalid actual application URL');
  return url.origin;
}

// Pure graph construction: both current and frozen observations use the same
// entry, eager import, dynamic import and exact-URL rules.
export function manifestDescriptor(descriptor, manifestBytes, appURL) {
  demand(descriptor && typeof descriptor === 'object', 'Actual browser descriptor required');
  relativePath(descriptor.asset_root); assetPath(descriptor.entry);
  const manifest = JSON.parse(manifestBytes), origin = appOrigin(appURL), prefix = descriptor.asset_prefix ?? '/static/';
  demand(typeof prefix === 'string' && prefix.endsWith('/') && !/[\x00-\x20\x7f]/.test(prefix) && /^\/(?:[A-Za-z0-9_@.-]+\/)*$/.test(prefix)
    && !prefix.split('/').some(part => part === '.' || part === '..'), 'Invalid actual asset prefix');
  demand(manifest && typeof manifest === 'object' && !Array.isArray(manifest), 'Actual asset manifest required');
  const entries = new Set(), files = new Set(), eagerCss = new Set(), eagerPreloads = new Set(), allowedCss = new Set(), allowedJs = new Set();
  function visit(key) {
    assetPath(key);
    if (entries.has(key)) return;
    const entry = Object.hasOwn(manifest, key) && manifest[key];
    demand(entry && typeof entry === 'object' && !Array.isArray(entry), 'Missing manifest closure entry');
    assetPath(entry.file); entries.add(key); files.add(entry.file);
    if (entry.file.endsWith('.js')) allowedJs.add(entry.file);
    for (const file of [...list(entry.css), ...list(entry.assets)]) { assetPath(file); files.add(file); }
    for (const file of list(entry.css)) { demand(file.endsWith('.css'), 'Manifest CSS must name a stylesheet'); allowedCss.add(file); }
    for (const dependency of [...list(entry.imports), ...list(entry.dynamicImports)]) visit(dependency);
  }
  visit(descriptor.entry);
  demand(manifest[descriptor.entry].file.endsWith('.js'), 'Actual JavaScript module entry required');
  const eagerVisited = new Set();
  function eager(key) {
    if (eagerVisited.has(key)) return;
    eagerVisited.add(key);
    const entry = manifest[key];
    for (const file of list(entry.css)) eagerCss.add(file);
    for (const dependency of list(entry.imports)) {
      demand(manifest[dependency]?.file.endsWith('.js'), 'Eager preload must name JavaScript');
      eagerPreloads.add(manifest[dependency].file); eager(dependency);
    }
  }
  eager(descriptor.entry);
  const url = file => new URL(prefix + assetPath(file), origin).href;
  return { ...descriptor, manifestBytes, manifest, entries, files, eagerCss, eagerPreloads, allowedCss, allowedJs, url };
}

/** Pure fixture seam; production supplies confined regular reads and exact tree discovery. */
export function verifyFrozenDescriptor(descriptor, { read, listFiles, appURL, parseArchive = readTarGz }) {
  demand(fields(descriptor, frozenFields), 'Explicit closed frozen browser descriptor required');
  for (const key of ['receipt', 'archive', 'asset_root']) relativePath(descriptor[key]);
  for (const key of ['receipt_sha256', 'archive_sha256', 'manifest_sha256']) demand(HEX.test(descriptor[key]), 'Frozen descriptor digest required');
  demand(!descriptor.receipt.split('/').some(part => ['.gate', 'node_modules', 'dist'].includes(part)), 'Committed frozen receipt required');
  const receiptBytes = read(descriptor.receipt), receipt = JSON.parse(receiptBytes);
  demand(hash(receiptBytes) === descriptor.receipt_sha256 && fields(receipt, ['schema', 'sha', 'tree_sha256', 'toolchain_digest', 'archive', 'sha256', 'files'])
    && receipt.schema === 1 && SHA.test(receipt.sha) && HEX.test(receipt.tree_sha256) && /^sha256:[a-f0-9]{64}$/.test(receipt.toolchain_digest)
    && receipt.archive === descriptor.archive && receipt.sha256 === descriptor.archive_sha256
    && Array.isArray(receipt.files) && receipt.files.length > 0, 'Frozen receipt identity differs');
  const archiveBytes = read(descriptor.archive), sidecar = read(`${descriptor.archive}.sha256`);
  demand(hash(archiveBytes) === descriptor.archive_sha256
    && String(sidecar) === `${descriptor.archive_sha256}  ${path.posix.basename(descriptor.archive)}\n`, 'Frozen archive/sidecar identity differs');
  const archive = parseArchive(archiveBytes), wanted = new Set();
  for (const item of receipt.files) {
    demand(fields(item, ['path', 'bytes', 'sha256']) && integer(item.bytes) && HEX.test(item.sha256), 'Invalid frozen member receipt');
    assetPath(item.path); demand(!wanted.has(item.path), 'Duplicate frozen member'); wanted.add(item.path);
    const member = archive.get(item.path), actual = read(`${descriptor.asset_root}/${item.path}`);
    demand(member?.type === 'file' && member.data.length === item.bytes && hash(member.data) === item.sha256
      && actual.length === item.bytes && hash(actual) === item.sha256 && Buffer.from(actual).equals(member.data), 'Frozen archive/tree member differs');
  }
  // Directory headers are allowed only when they own an exact listed member.
  for (const [name, member] of archive) demand(wanted.has(name) ? member.type === 'file'
    : member.type === 'directory' && [...wanted].some(file => file.startsWith(`${name}/`)), 'Extra frozen archive member');
  const actualFiles = listFiles(descriptor.asset_root);
  demand(Array.isArray(actualFiles) && new Set(actualFiles).size === actualFiles.length
    && equal([...actualFiles].sort(), [...wanted].sort()), 'Frozen tree has missing/extra members');
  demand(wanted.has('.vite/manifest.json'), 'Frozen manifest missing from receipt/archive');
  const manifestBytes = read(`${descriptor.asset_root}/.vite/manifest.json`);
  demand(hash(manifestBytes) === descriptor.manifest_sha256, 'Frozen manifest identity differs');
  const result = manifestDescriptor(descriptor, manifestBytes, appURL);
  demand(result.manifest[descriptor.entry].isEntry === true, 'Frozen descriptor must select an actual manifest entry');
  demand([...result.files].every(file => wanted.has(file)), 'Frozen manifest closure escapes the exact archive');
  return { ...result, artifacts: [descriptor.receipt, descriptor.archive, `${descriptor.archive}.sha256`, ...[...wanted].sort().map(file => `${descriptor.asset_root}/${file}`)] };
}

export function loadBrowserDescriptor({ root, role, browser, appURL }) {
  demand(['core', 'consumer'].includes(role), 'Explicit browser role required');
  if (role === 'core') demand(!Object.hasOwn(browser ?? {}, 'frozen'), 'Core cannot declare frozen browser assets');
  const descriptor = role === 'core'
    ? { inventory: 'web-kit/sample/e2e/inventory.json', asset_root: 'web-kit/sample/embedfs/dist', entry: 'src/sample/main.ts', asset_prefix: '/static/' }
    : browser;
  demand(descriptor && typeof descriptor.inventory === 'string' && !/^(?:\.gate|node_modules|dist)(?:\/|$)/.test(descriptor.inventory), 'Full requires committed browser inventory');
  relativePath(descriptor.inventory);
  const read = relative => {
    const filename = regularPath(root, relative), before = fs.lstatSync(filename, { bigint: true });
    demand(before.isFile(), 'Regular browser evidence file required');
    const fd = fs.openSync(filename, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
    try {
      const opened = fs.fstatSync(fd, { bigint: true });
      demand(opened.isFile() && opened.ino === before.ino && opened.dev === before.dev, 'Browser evidence replaced');
      const bytes = fs.readFileSync(fd), after = fs.fstatSync(fd, { bigint: true });
      const named = fs.lstatSync(regularPath(root, relative), { bigint: true });
      demand(named.ino === before.ino && named.dev === before.dev && before.size === after.size && before.mtimeNs === after.mtimeNs
        && before.ctimeNs === after.ctimeNs && after.size === BigInt(bytes.length), 'Browser evidence changed while reading');
      return bytes;
    } finally { fs.closeSync(fd); }
  };
  const listFiles = base => {
    const result = [];
    function visit(relative = '') {
      const directory = regularPath(root, relative ? `${base}/${relative}` : base);
      demand(fs.lstatSync(directory).isDirectory(), 'Regular frozen asset directory required');
      for (const item of fs.readdirSync(directory, { withFileTypes: true })) {
        const name = relative ? `${relative}/${item.name}` : item.name;
        demand(!item.isSymbolicLink(), 'Symlink in frozen asset tree');
        if (item.isDirectory()) visit(name);
        else { demand(item.isFile(), 'Nonregular frozen asset tree member'); result.push(name); }
      }
    }
    visit(); return result;
  };
  const current = manifestDescriptor(descriptor, read(`${descriptor.asset_root}/.vite/manifest.json`), appURL);
  if (Object.hasOwn(descriptor, 'frozen')) current.frozen = verifyFrozenDescriptor(descriptor.frozen, { read, listFiles, appURL });
  return current;
}

function validObservation(item, descriptor, appURL) {
  if (!item || typeof item.page !== 'string' || !item.page.startsWith('/') || item.page.startsWith('//') || /[\\\x00-\x1f\x7f#]/.test(item.page)) return false;
  const origin = appOrigin(appURL), page = new URL(item.page, origin);
  if (page.origin !== origin || page.pathname + page.search !== item.page) return false;
  const pathFor = file => new URL(descriptor.url(file)).pathname;
  const exactURL = (value, pathname) => {
    try { const url = new URL(value); return typeof value === 'string' && url.origin === origin && !url.search && !url.hash
      && !url.username && !url.password && value === url.href && url.href === new URL(pathname, origin).href; } catch { return false; }
  };
  return HEX.test(item.nonce_sha256) && integer(item.scripts) && item.scripts > 0 && integer(item.json) && item.json <= item.scripts
    && integer(item.assetLinks) && item.assetLinks > 0 && item.module === pathFor(descriptor.manifest[descriptor.entry].file) && exactURL(item.module_url, item.module)
    && Array.isArray(item.css) && Array.isArray(item.preloads) && Array.isArray(item.css_urls) && Array.isArray(item.preload_urls)
    && new Set(item.css).size === item.css.length && new Set(item.preloads).size === item.preloads.length
    && item.css_urls.length === item.css.length && item.preload_urls.length === item.preloads.length && item.assetLinks === item.css.length + item.preloads.length
    && item.css.every((file, index) => [...descriptor.allowedCss].some(allowed => pathFor(allowed) === file) && exactURL(item.css_urls[index], file))
    && item.preloads.every((file, index) => [...descriptor.allowedJs].some(allowed => pathFor(allowed) === file) && exactURL(item.preload_urls[index], file))
    && [...descriptor.eagerCss].every(file => item.css.includes(pathFor(file))) && [...descriptor.eagerPreloads].every(file => item.preloads.includes(pathFor(file)));
}

/** Counts include both bundles; violation counters retain their original meaning. */
export function validateCspMeasurement({ measured, context, descriptor, role, appURL, appImageId, mtimeMs }) {
  demand(['core', 'consumer'].includes(role) && measured?.schema === 1 && measured.sha === context.sha && measured.tree_sha256 === context.tree_sha256
    && measured.app_image_id === appImageId && measured.stage === context.stage && integer(measured.violations) && integer(measured.legacy_violations)
    && integer(measured.pages) && measured.pages > 0 && Array.isArray(measured.nonceObservations) && measured.nonceObservations.length > 0
    && Number.isFinite(mtimeMs) && mtimeMs >= Date.parse(context.started), 'Fresh source/image/policy-bound CSP measurement required');
  const frozen = descriptor.frozen;
  if (frozen) demand(role === 'consumer' && Array.isArray(measured.frozenNonceObservations) && measured.frozenNonceObservations.length > 0
    && measured.frozen_pages === measured.frozenNonceObservations.length, 'Explicit nonempty frozen observations required');
  else demand(!Object.hasOwn(measured, 'frozenNonceObservations') && !Object.hasOwn(measured, 'frozen_pages'), 'Frozen observations require a verified consumer descriptor');
  const all = [...measured.nonceObservations, ...(frozen ? measured.frozenNonceObservations : [])];
  demand(all.length === measured.pages && new Set(all.map(item => item?.page)).size === measured.pages
    && new Set(all.map(item => item?.nonce_sha256)).size === measured.pages
    && measured.nonceObservations.every(item => validObservation(item, descriptor, appURL))
    && (!frozen || measured.frozenNonceObservations.every(item => validObservation(item, frozen, appURL))), 'Complete globally distinct CSP observations and exact manifest assets required');
  return { stage: measured.stage, violations: measured.violations, legacy_violations: measured.legacy_violations };
}

export function coreCspPagesMatch(measured, exported) {
  return Array.isArray(exported) && exported.length > 0 && new Set(exported).size === exported.length
    && Array.isArray(measured.nonceObservations) && equal(measured.nonceObservations.map(item => item.page).sort(), [...exported].sort());
}
