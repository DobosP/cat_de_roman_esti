import * as fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { gunzipSync, gzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import { isDeepStrictEqual } from 'node:util';

const MODULE = 'github.com/DobosP/roedu-ui/web-kit';
const MAX_ARCHIVE = 128 * 1024 * 1024;
const GATE_FILES = ['scripts/gate.sh', 'compose.gate.yml', 'Taskfile.yml', 'Dockerfile.toolchain'];
const GO_DIRS = new Set(['assets', 'budget', 'static', 'csp', 'island', 'health', 'golden', 'routes', 'engine', 'tokens', 'i18n', 'vm', 'tmplfn', 'ui', 'cmd', 'lint', 'sample', 'testdata']);
const NPM_KIT_DIRS = new Set(['vite-preset', 'budget', 'playwright', 'lint', 'scripts', 'templates', 'schemas', 'testdata']);
const PACKAGE_FILES = new Set(['package.json', 'README.md', 'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'NOTICE']);
const sha = data => createHash('sha256').update(data).digest('hex');
const json = data => Buffer.from(JSON.stringify(data, null, 2) + '\n');
const fail = message => { throw Error(message); };

/** Runtime bytecode is cache state, never an owning package/source input. */
export function isPythonBytecodePath(value) {
  return value.split(/[\\/]/).some(part => /^__pycache__$|\.py[co](?:\.(?:gz|br))?$/i.test(part));
}

export function safePath(value, allowDot = false) {
  if (allowDot && value === '.') return '.';
  if (typeof value !== 'string' || !value || value.startsWith('/') || /[\\:\x00-\x1f\x7f]/.test(value)) fail(`Unsafe path: ${String(value)}`);
  const normalized = value.endsWith('/') ? value.slice(0, -1) : value;
  if (normalized.split('/').some(part => !part || part === '.' || part === '..')) fail(`Unsafe path: ${value}`);
  return normalized;
}
function noLinks(root, relative, allowMissing = false) {
  const clean = safePath(relative, true);
  let cursor = root;
  for (const part of clean === '.' ? [] : clean.split('/')) {
    cursor = path.join(cursor, part);
    if (!fs.existsSync(cursor)) {
      try { if (fs.lstatSync(cursor).isSymbolicLink()) fail(`Symlink destination: ${relative}`); } catch (error) { if (error.code !== 'ENOENT') throw error; }
      if (allowMissing) continue;
      fail(`Missing input: ${relative}`);
    }
    const stat = fs.lstatSync(cursor);
    if (stat.isSymbolicLink() || (!stat.isDirectory() && !stat.isFile())) fail(`Nonregular destination: ${relative}`);
  }
  return cursor;
}
function regularTree(directory, relative = '') {
  if (!fs.existsSync(directory)) return new Map();
  const entries = new Map();
  for (const name of fs.readdirSync(directory).sort()) {
    const rel = relative ? `${relative}/${name}` : name, file = path.join(directory, name), stat = fs.lstatSync(file);
    safePath(rel);
    if (stat.isSymbolicLink() || (!stat.isDirectory() && !stat.isFile())) fail(`Nonregular tree entry: ${rel}`);
    if (stat.isDirectory()) for (const [key, item] of regularTree(file, rel)) entries.set(key, item);
    else entries.set(rel, { data: fs.readFileSync(file), mode: stat.mode & 0o777 });
  }
  return entries;
}
function octal(block, offset, length, label) {
  const text = block.subarray(offset, offset + length).toString('ascii').replace(/\0.*$/s, '').trim();
  if (!/^[0-7]+$/.test(text)) fail(`Invalid tar ${label}`);
  const value = Number.parseInt(text, 8);
  if (!Number.isSafeInteger(value) || value > MAX_ARCHIVE) fail(`Tar ${label} exceeds limit`);
  return value;
}
function field(block, start, length) {
  const bytes = block.subarray(start, start + length), zero = bytes.indexOf(0);
  if (zero >= 0 && !bytes.subarray(zero).every(byte => byte === 0)) fail('Malformed tar string padding');
  return new TextDecoder('utf-8', { fatal: true }).decode(zero < 0 ? bytes : bytes.subarray(0, zero));
}
function pax(data) {
  const result = {};
  let position = 0;
  while (position < data.length) {
    const space = data.indexOf(32, position);
    if (space < 0) fail('Malformed PAX length');
    const length = data.subarray(position, space).toString('ascii');
    if (!/^\d+$/.test(length)) fail('Malformed PAX length');
    const count = Number(length);
    if (!Number.isSafeInteger(count) || count < 5 || position + count > data.length || data[position + count - 1] !== 10) fail('Malformed PAX record');
    const record = new TextDecoder('utf-8', { fatal: true }).decode(data.subarray(space + 1, position + count - 1));
    const equal = record.indexOf('=');
    if (equal < 1) fail('Malformed PAX value');
    const key = record.slice(0, equal), value = record.slice(equal + 1);
    if (!['path', 'size', 'mtime', 'atime', 'ctime', 'comment', 'uid', 'gid', 'uname', 'gname'].includes(key) || key in result || value.includes('\0')) fail(`Unsupported PAX field: ${key}`);
    if (key === 'path') safePath(value);
    result[key] = value; position += count;
  }
  return result;
}
/** Strict regular-file/directory USTAR parser. PAX metadata and git's global comment are supported. */
export function parseTar(buffer) {
  if (!Buffer.isBuffer(buffer) || buffer.length > MAX_ARCHIVE || buffer.length % 512) fail('Malformed tar size');
  const entries = new Map();
  let position = 0, extended = {}, longName;
  while (position < buffer.length) {
    const block = buffer.subarray(position, position + 512);
    if (block.every(byte => byte === 0)) {
      if (position + 1024 > buffer.length || !buffer.subarray(position).every(byte => byte === 0)) fail('Malformed tar end marker');
      if (Object.keys(extended).length || longName) fail('Dangling tar extension');
      return entries;
    }
    const checksum = octal(block, 148, 8, 'checksum');
    let actual = 0; for (let index = 0; index < 512; index++) actual += index >= 148 && index < 156 ? 32 : block[index];
    if (checksum !== actual) fail('Tar checksum mismatch');
    if (!['ustar', 'ustar '].includes(field(block, 257, 6))) fail('Unsupported tar format');
    const size = octal(block, 124, 12, 'size'), mode = octal(block, 100, 8, 'mode');
    if (mode & ~0o777) fail('Unsafe tar permissions');
    const type = String.fromCharCode(block[156] || 48), end = position + 512 + Math.ceil(size / 512) * 512;
    if (end > buffer.length) fail('Truncated tar entry');
    const data = buffer.subarray(position + 512, position + 512 + size);
    if (!buffer.subarray(position + 512 + size, end).every(byte => byte === 0)) fail('Nonzero tar padding');
    position = end;
    if (type === 'x' || type === 'g') {
      const metadata = pax(data);
      if (type === 'g') { if ('path' in metadata || 'size' in metadata) fail('Unsafe global PAX path/size'); }
      else { if (Object.keys(extended).length) fail('Repeated PAX extension'); extended = metadata; }
      continue;
    }
    if (type === 'L') {
      if (longName) fail('Repeated long-name extension');
      longName = safePath(new TextDecoder('utf-8', { fatal: true }).decode(data).replace(/\0$/, ''));
      continue;
    }
    if (type !== '0' && type !== '5') fail(`Unsafe tar entry type: ${type}`);
    if (field(block, 157, 100)) fail('Tar link target forbidden');
    if (type === '5' && size !== 0) fail('Directory has tar payload');
    if (extended.size !== undefined && (!/^\d+$/.test(extended.size) || Number(extended.size) !== size)) fail('PAX size mismatch');
    const prefix = field(block, 345, 155), name = field(block, 0, 100);
    const entry = safePath(extended.path ?? longName ?? (prefix ? `${prefix}/${name}` : name));
    extended = {}; longName = undefined;
    if (entries.has(entry)) fail(`Duplicate tar path: ${entry}`);
    for (let parent = path.posix.dirname(entry); parent !== '.'; parent = path.posix.dirname(parent)) if (entries.get(parent)?.type === 'file') fail(`Tar ancestor is a file: ${parent}`);
    if (type === '0' && [...entries.keys()].some(key => key.startsWith(`${entry}/`))) fail(`Tar file shadows directory: ${entry}`);
    entries.set(entry, { type: type === '5' ? 'directory' : 'file', mode, data: Buffer.from(data) });
    if (entries.size > 20000) fail('Too many tar entries');
  }
  fail('Tar end marker missing');
}
export function readTarGz(buffer) {
  if (!Buffer.isBuffer(buffer) || buffer.length > MAX_ARCHIVE) fail('Archive exceeds limit');
  return parseTar(gunzipSync(buffer, { maxOutputLength: MAX_ARCHIVE }));
}
function stableVersion(version) { return typeof version === 'string' && /^\d+\.\d+\.\d+$/.test(version); }
export function compareVersions(left, right) {
  if (left === right) return 0;
  if (typeof left !== 'string' || typeof right !== 'string') fail('Incomparable versions');
  const tokenize = value => value.replace(/^v(?=\d)/, '').match(/\d+|[^\d]+/g);
  const a = tokenize(left), b = tokenize(right);
  if (!a || !b) fail('Incomparable versions');
  for (let index = 0; index < Math.max(a.length, b.length); index++) {
    const x = a[index] ?? '', y = b[index] ?? '';
    if (x === y) continue;
    if (/^\d+$/.test(x) && /^\d+$/.test(y)) return BigInt(x) > BigInt(y) ? 1 : -1;
    return x > y ? 1 : -1;
  }
  return 0;
}
function tools(lock) {
  if (!lock || !Array.isArray(lock.tools)) fail('Version lock tools required');
  const result = new Map();
  for (const entry of lock.tools) {
    if (!entry || typeof entry.tool !== 'string' || !['core', 'app', 'environment'].includes(entry.scope) || result.has(entry.tool)) fail('Malformed or duplicate version entry');
    result.set(entry.tool, entry);
  }
  return result;
}
/** Exact PROGRAM9-8 merge; returns new objects and never mutates either input. */
export function mergeVersions(appLock, coreLock, tag, app) {
  if (!/^core-v1\.\d+$/.test(tag) || typeof app !== 'string' || !app) fail('Invalid core tag/app');
  for (const lock of [appLock, coreLock]) if (lock.resolved !== undefined && !/^\d{4}-\d{2}-\d{2}$/.test(lock.resolved)) fail('Invalid lock resolution date');
  const previous = tools(appLock), incoming = tools(coreLock), merged = [];
  for (const [name, entry] of incoming) {
    const local = previous.get(name); previous.delete(name);
    if (entry.scope === 'core' || entry.scope === 'environment') {
      if (local && entry.scope === 'core' && entry.version !== null && local.version !== null && compareVersions(local.version, entry.version) > 0) fail(`Higher core version refused: ${name}`);
      merged.push(structuredClone(entry));
    } else if (local) merged.push(structuredClone(compareVersions(local.version, entry.version) >= 0 ? local : entry));
    else if (Array.isArray(entry.apps) && entry.apps.includes(app)) merged.push(structuredClone(entry));
  }
  for (const entry of previous.values()) if (entry.scope === 'app') merged.push(structuredClone(entry));
  if (!coreLock.toolchain_image || typeof coreLock.toolchain_image.image_id !== 'string') fail('Core toolchain image required');
  if (appLock.toolchain_image?.version && coreLock.toolchain_image.version && compareVersions(appLock.toolchain_image.version, coreLock.toolchain_image.version) > 0) fail('Higher core toolchain version refused');
  return { ...structuredClone(appLock), ...structuredClone(coreLock), tools: merged, toolchain_image: structuredClone(coreLock.toolchain_image), resolved: [appLock.resolved, coreLock.resolved].filter(Boolean).sort().at(-1), core_tag: tag };
}
function archiveFile(entries, file) {
  const entry = entries.get(file); if (entry?.type !== 'file') fail(`Archive file required: ${file}`); return entry;
}
/** Validate one actual npm owner archive without requiring a release tag or Go bundle. */
export function npmArchive(data, expectedName, filename) {
  if (!['@roedu/ui', '@roedu/web-kit'].includes(expectedName)) fail('Unsupported npm archive owner');
  const entries = readTarGz(data);
  for (const [name, entry] of entries) {
    if (name !== 'package' && !name.startsWith('package/')) fail(`Unknown npm archive root: ${name}`);
    if (name === 'package') { if (entry.type !== 'directory') fail('Npm archive root must be a directory'); continue; }
    const rel = name.slice(8), first = rel.split('/')[0];
    if (isPythonBytecodePath(rel)) fail(`Excluded Python bytecode/cache in npm archive: ${name}`);
    if (/\.tsbuildinfo(?:\.(?:gz|br))?$/.test(rel)) fail(`Excluded compiler build state in npm archive: ${name}`);
    if (rel.split('/').some(part => ['.git', 'node_modules', '.gate', '.vitest', 'test-results', 'TASK_BRIEF.md', 'TASK_RESULT.md', 'SWARM_RESULT.md'].includes(part) || part === '.env' || part.startsWith('.env.'))) fail(`Excluded cache/secret member in npm archive: ${name}`);
    const allowed = expectedName === '@roedu/ui' ? first === 'dist' || PACKAGE_FILES.has(rel) : NPM_KIT_DIRS.has(first) || PACKAGE_FILES.has(rel) || rel === 'versions.lock.json';
    if (!allowed) fail(`Unknown npm archive path: ${name}`);
    if ((first === 'dist' || NPM_KIT_DIRS.has(first)) && rel === first && entry.type !== 'directory') fail(`Archive package directory required: ${name}`);
  }
  const manifest = JSON.parse(archiveFile(entries, 'package/package.json').data.toString('utf8'));
  if (manifest.name !== expectedName || !stableVersion(manifest.version)) fail('Npm name/version mismatch');
  const basename = `${expectedName === '@roedu/ui' ? 'roedu-ui' : 'roedu-web-kit'}-${manifest.version}.tgz`;
  if (filename !== basename) fail('Npm archive filename/version mismatch');
  const exported = value => {
    if (typeof value === 'string' && value.startsWith('./')) archiveFile(entries, `package/${safePath(value.slice(2))}`);
    else if (value && typeof value === 'object') Object.values(value).forEach(exported);
  };
  exported(manifest.exports);
  if (expectedName === '@roedu/ui') archiveFile(entries, 'package/dist/index.js');
  else archiveFile(entries, 'package/scripts/kit-sync.mjs');
  return { entries, manifest, filename, data };
}
/** Closed Native E1 configuration. Absence is active; only Cat may stage the sealed original SDK. */
export function validateUiAdoption(config) {
  if (!Object.hasOwn(config, 'ui_adoption')) return undefined;
  const phase = config.ui_adoption;
  const fields = (value, keys) => !!value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
  if (config.role !== 'consumer' || config.app !== 'cat_de_roman_esti' || !fields(phase, ['mode', 'until', 'legacy']) || phase.mode !== 'staged-react' || phase.until !== 'S1-M2') throw Error('Unsupported or malformed ui_adoption phase');
  const legacy = phase.legacy;
  if (!fields(legacy, ['version', 'archive_sha256', 'source_sha', 'receipt', 'receipt_sha256']) || legacy.version !== '0.3.0' || typeof legacy.archive_sha256 !== 'string' || typeof legacy.source_sha !== 'string' || typeof legacy.receipt_sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(legacy.archive_sha256) || !/^[a-f0-9]{40}([a-f0-9]{24})?$/.test(legacy.source_sha) || !/^[a-f0-9]{64}$/.test(legacy.receipt_sha256)) throw Error('Malformed sealed original UI identity');
  const receipt = legacy.receipt;
  const excluded = new Set(['kit', 'node_modules', 'third_party', 'vendor', 'dist', 'embedfs', 'test-results', 'TASK_BRIEF.md', 'TASK_RESULT.md', 'SWARM_RESULT.md']);
  if (typeof receipt !== 'string' || !receipt || receipt.startsWith('/') || /\.tsbuildinfo(?:\.(?:gz|br))?$/.test(receipt) || receipt.split('/').some(part => !/^[A-Za-z0-9_@.-]+$/.test(part) || part === '.' || part === '..' || part.startsWith('.') || excluded.has(part))) throw Error('Original UI receipt must be a literal source-owned path outside caches, inputs and dependencies');
  if ([config.vendor_dir ?? 'frontend/vendor', config.npm_dir ?? 'frontend/node_modules/@roedu/web-kit'].some(directory => typeof directory === 'string' && (receipt === directory || receipt.startsWith(directory + '/')))) throw Error('Original UI receipt overlaps a configured dependency directory');
  return { mode: 'staged-react', until: 'S1-M2', legacy: { version: '0.3.0', archive_sha256: legacy.archive_sha256, source_sha: legacy.source_sha, receipt, receipt_sha256: legacy.receipt_sha256 } };
}

// Inline after validateUiAdoption in standalone kit-sync.mjs. Uses its existing
// fs/path/sha/readTarGz/safePath/noLinks/isDeepStrictEqual/loadKit/readConsumerConfig.
// No import is introduced into the checksum-verified first-sync script.
const UI_ADOPTION_FIELDS = ['dependencies', 'devDependencies', 'optionalDependencies', 'peerDependencies'];
const UI_ADOPTION_ARCHIVE_FILES = new Set(['package.json', 'README.md', 'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'NOTICE']);
const UI_ADOPTION_RUNTIME_FIELDS = ['dependencies', 'optionalDependencies', 'peerDependencies', 'peerDependenciesMeta'];
const uiAdoptionFail = message => { throw Error(`UI_ADOPTION ${message}`); };
const uiAdoptionCheck = (value, message) => { if (!value) uiAdoptionFail(message); };
const uiAdoptionHash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const uiAdoptionSha = value => typeof value === 'string' && /^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(value);
function uiAdoptionObject(value, keys, label) {
  uiAdoptionCheck(value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key)), `closed ${label} object required`);
  return value;
}
function uiAdoptionEvidencePath(value) {
  const clean = safePath(value);
  uiAdoptionCheck(clean === value && clean.split('/').every(part => /^[A-Za-z0-9_@.-]+$/.test(part) && !part.startsWith('.') && !['kit', 'node_modules', 'third_party', 'vendor', 'dist', 'embedfs', 'test-results', 'TASK_BRIEF.md', 'TASK_RESULT.md', 'SWARM_RESULT.md'].includes(part)) && !/\.tsbuildinfo(?:\.(?:gz|br))?$/.test(clean) && !isPythonBytecodePath(clean), 'receipt/evidence path must be literal, confined and outside caches or installed/generated output');
  return clean;
}
function uiAdoptionFile(root, relative, allowMissing = false) {
  const file = noLinks(root, relative, allowMissing);
  if (!fs.existsSync(file)) { uiAdoptionCheck(allowMissing, `missing regular file ${relative}`); return undefined; }
  uiAdoptionCheck(fs.lstatSync(file).isFile(), `regular file required: ${relative}`);
  return fs.readFileSync(file);
}
function uiAdoptionEvidence(root, ref, label) {
  uiAdoptionObject(ref, ['path', 'sha256'], label);
  uiAdoptionEvidencePath(ref.path); uiAdoptionCheck(uiAdoptionHash(ref.sha256), `${label} SHA256 required`);
  const bytes = uiAdoptionFile(root, ref.path);
  uiAdoptionCheck(sha(bytes) === ref.sha256, `${label} bytes differ from receipt`);
  return bytes;
}
function uiAdoptionJSON(bytes, label) {
  try { return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes)); }
  catch { uiAdoptionFail(`${label} must be UTF-8 JSON`); }
}
function uiAdoptionDeclaration(manifest, expected, required = true) {
  uiAdoptionCheck(manifest && typeof manifest === 'object' && !Array.isArray(manifest), 'owning package manifest required');
  const sections = UI_ADOPTION_FIELDS.filter(field => Object.hasOwn(manifest[field] ?? {}, '@roedu/ui'));
  uiAdoptionCheck(sections.length <= 1 && (!required || sections.length === 1), 'exactly one owning UI dependency declaration required');
  if (!sections.length) return undefined;
  uiAdoptionCheck(sections[0] !== 'peerDependencies' && manifest[sections[0]]['@roedu/ui'] === expected, `owning UI pointer must already be exactly ${expected}`);
  return sections[0];
}
function uiAdoptionArchive(data, version, filename, parseArchive = readTarGz) {
  const entries = parseArchive(data);
  uiAdoptionCheck(entries instanceof Map, 'strict archive parser entries required');
  for (const [name, entry] of entries) {
    const clean = safePath(name);
    uiAdoptionCheck(name === clean && (name === 'package' || name.startsWith('package/')), 'unknown SDK archive root');
    if (name === 'package') { uiAdoptionCheck(entry.type === 'directory', 'SDK archive root must be directory'); continue; }
    const relative = name.slice(8), first = relative.split('/')[0];
    uiAdoptionCheck(first === 'dist' || UI_ADOPTION_ARCHIVE_FILES.has(relative), `unknown SDK archive member ${name}`);
    uiAdoptionCheck(!isPythonBytecodePath(relative), `excluded Python bytecode/cache SDK archive member ${name}`);
    uiAdoptionCheck(!relative.split('/').some(part => ['.git', '.gate', '.vitest', 'node_modules', 'test-results', 'TASK_BRIEF.md', 'TASK_RESULT.md', 'SWARM_RESULT.md'].includes(part) || part === '.env' || part.startsWith('.env.')) && !/\.tsbuildinfo(?:\.(?:gz|br))?$/.test(relative), `excluded SDK archive member ${name}`);
    uiAdoptionCheck(entry.type === 'file' || entry.type === 'directory', `nonregular SDK archive member ${name}`);
    if (relative === 'dist') uiAdoptionCheck(entry.type === 'directory', 'SDK dist root must be directory');
  }
  const manifestEntry = entries.get('package/package.json');
  uiAdoptionCheck(manifestEntry?.type === 'file', 'SDK regular package.json missing');
  const manifest = uiAdoptionJSON(manifestEntry.data, 'SDK manifest');
  uiAdoptionCheck(manifest.name === '@roedu/ui' && manifest.version === version && filename === `roedu-ui-${version}.tgz`, 'SDK name/version/filename identity differs');
  function exported(value) {
    if (typeof value === 'string') {
      uiAdoptionCheck(value.startsWith('./'), 'SDK export must use a literal local path');
      const target = safePath(value.slice(2)); uiAdoptionCheck(entries.get(`package/${target}`)?.type === 'file', `SDK export file missing: ${value}`);
    } else if (Array.isArray(value)) value.forEach(exported);
    else if (value && typeof value === 'object') Object.values(value).forEach(exported);
    else uiAdoptionFail('SDK export must name actual files');
  }
  uiAdoptionCheck(manifest.exports && typeof manifest.exports === 'object', 'SDK exports required');
  Object.values(manifest.exports).forEach(exported);
  for (const field of ['main', 'module', 'types']) if (manifest[field] !== undefined) exported(manifest[field].startsWith('./') ? manifest[field] : './' + manifest[field]);
  uiAdoptionCheck(entries.get('package/dist/index.js')?.type === 'file', 'SDK runtime entry missing');
  if (version === '0.3.0') {
    for (const field of ['dependencies', 'optionalDependencies']) uiAdoptionCheck(!manifest[field] || (typeof manifest[field] === 'object' && !Array.isArray(manifest[field]) && Object.keys(manifest[field]).length === 0), `original SDK must not gain ${field}`);
    for (const field of ['bundledDependencies', 'bundleDependencies']) uiAdoptionCheck(manifest[field] === undefined || (Array.isArray(manifest[field]) && manifest[field].length === 0), 'original SDK must not bundle dependencies');
    uiAdoptionCheck(isDeepStrictEqual(manifest.peerDependencies, { react: '>=18', 'react-dom': '>=18' }) && (!manifest.peerDependenciesMeta || Object.keys(manifest.peerDependenciesMeta).length === 0), 'original SDK React peer metadata differs');
    uiAdoptionCheck(isDeepStrictEqual(manifest.files, ['dist']) && isDeepStrictEqual(manifest.exports, { '.': { types: './dist/index.d.ts', import: './dist/index.js' }, './styles.css': './dist/roedu-ui.css' }), 'original SDK file/export metadata differs');
  }
  return { data, entries, manifest, filename, sha256: sha(data), integrity: `sha512-${createHash('sha512').update(data).digest('base64')}` };
}
function uiAdoptionSelected(kit, parseArchive) {
  uiAdoptionCheck(kit && /^core-v1\.\d+$/.test(kit.tag) && kit.ui && Buffer.isBuffer(kit.ui.data), 'verified selected kit/UI required');
  const version = kit.ui.manifest?.version;
  uiAdoptionCheck(typeof version === 'string' && /^\d+\.\d+\.\d+$/.test(version) && compareVersions(version, '1.0.0') >= 0, 'selected native UI version required');
  const selected = uiAdoptionArchive(kit.ui.data, version, kit.ui.filename, parseArchive);
  uiAdoptionCheck(isDeepStrictEqual(selected.manifest, kit.ui.manifest) && kit.sums?.get(selected.filename) === selected.sha256, 'selected UI differs from sealed kit identity');
  return selected;
}
function uiAdoptionLayout(config) {
  const vendor = safePath(config.vendor_dir);
  uiAdoptionCheck(vendor === config.vendor_dir && vendor.split('/').every(part => /^[A-Za-z0-9_@.-]+$/.test(part) && !part.startsWith('.') && !['kit', 'node_modules', 'third_party', 'dist', 'test-results'].includes(part)), 'unsafe UI vendor path');
  const parent = path.posix.dirname(vendor), prefix = parent === '.' ? '' : parent + '/';
  return { vendor, parent, manifest: prefix + 'package.json', lock: prefix + 'package-lock.json', installed: prefix + 'node_modules/@roedu/ui', pointer: filename => `file:${path.posix.basename(vendor)}/${filename}` };
}
function uiAdoptionLock(manifest, lock, sdk, pointer) {
  uiAdoptionCheck(lock?.lockfileVersion === 3 && lock.packages && typeof lock.packages === 'object' && !Array.isArray(lock.packages), 'actual npm v3 owning lock graph required');
  const owner = lock.packages['']; uiAdoptionCheck(owner && !owner.link, 'owning lock root required');
  for (const field of UI_ADOPTION_FIELDS) uiAdoptionCheck(isDeepStrictEqual(owner[field] ?? {}, manifest[field] ?? {}), `owning manifest/lock ${field} differs`);
  uiAdoptionCheck(owner.name === manifest.name && owner.version === manifest.version, 'owning manifest/lock identity differs');
  uiAdoptionDeclaration(manifest, pointer);
  const row = lock.packages['node_modules/@roedu/ui'];
  uiAdoptionCheck(row && !row.link && row.version === sdk.manifest.version && row.resolved === pointer && row.integrity === sdk.integrity, 'owning UI lock pointer/version/integrity differs');
  for (const field of UI_ADOPTION_RUNTIME_FIELDS) uiAdoptionCheck(isDeepStrictEqual(row[field] ?? {}, sdk.manifest[field] ?? {}), `SDK lock ${field} metadata differs`);
  for (const [key, candidate] of Object.entries(lock.packages)) if (key !== 'node_modules/@roedu/ui' && (candidate.name === '@roedu/ui' || key.endsWith('node_modules/@roedu/ui'))) uiAdoptionFail('aliased, duplicate or nested UI lock record refused');
  return row;
}
function uiAdoptionRuntimeGraph(manifest, lock) {
  const runtime = {};
  for (const name of ['react', 'react-dom', 'framer-motion']) {
    uiAdoptionCheck(typeof manifest.dependencies?.[name] === 'string', `original runtime direct ${name} declaration required`);
    const row = lock.packages[`node_modules/${name}`];
    uiAdoptionCheck(row && !row.link && /^\d+\.\d+\.\d+$/.test(row.version) && (row.name === undefined || row.name === name), `original resolved ${name} runtime identity missing`);
    runtime[name] = row.version;
  }
  uiAdoptionCheck(/^19\./.test(runtime.react) && runtime.react === runtime['react-dom'] && /^12\./.test(runtime['framer-motion']), 'original React19/Framer12 runtime facts differ');
  return runtime;
}
/** Content proof only: execution authenticity is reviewed by the parent before first sync. */
export function verifyUiAdoptionReceipt(root, phase, sdk, layout) {
  const receiptBytes = uiAdoptionFile(root, uiAdoptionEvidencePath(phase.legacy.receipt));
  uiAdoptionCheck(sha(receiptBytes) === phase.legacy.receipt_sha256, 'original receipt SHA256 differs');
  const receipt = uiAdoptionJSON(receiptBytes, 'original receipt');
  uiAdoptionObject(receipt, ['schema', 'check', 'status', 'app', 'sha', 'tree_sha256', 'toolchain_digest', 'runtime_sdk', 'runtime_dependencies', 'dependency_graph', 'fixtures', 'execution'], 'original receipt');
  uiAdoptionCheck(receipt.schema === 1 && receipt.check === 'cat-original-ui-runtime' && receipt.status === 'pass' && receipt.app === 'cat_de_roman_esti' && uiAdoptionSha(receipt.sha) && receipt.sha === phase.legacy.source_sha && uiAdoptionHash(receipt.tree_sha256) && /^sha256:[a-f0-9]{64}$/.test(receipt.toolchain_digest), 'original receipt outcome/source/toolchain identity differs');
  const runtimeSdk = { name: '@roedu/ui', version: '0.3.0', archive_sha256: sdk.sha256, manifest_sha256: sha(sdk.entries.get('package/package.json').data), entry: 'dist/index.js', entry_sha256: sha(sdk.entries.get('package/dist/index.js').data) };
  uiAdoptionObject(receipt.runtime_sdk, Object.keys(runtimeSdk), 'original runtime SDK');
  uiAdoptionCheck(isDeepStrictEqual(receipt.runtime_sdk, runtimeSdk), 'original runtime SDK evidence differs from sealed archive');
  uiAdoptionObject(receipt.dependency_graph, ['manifest', 'lock'], 'original dependency graph');
  const originalManifest = uiAdoptionJSON(uiAdoptionEvidence(root, receipt.dependency_graph.manifest, 'original manifest snapshot'), 'original manifest snapshot');
  const originalLock = uiAdoptionJSON(uiAdoptionEvidence(root, receipt.dependency_graph.lock, 'original lock snapshot'), 'original lock snapshot');
  uiAdoptionCheck(receipt.dependency_graph.manifest.path !== layout.manifest && receipt.dependency_graph.lock.path !== layout.lock && receipt.dependency_graph.manifest.path !== receipt.dependency_graph.lock.path, 'original manifest/lock snapshots must be distinct preserved evidence, not mutable live graph');
  uiAdoptionLock(originalManifest, originalLock, sdk, layout.pointer(sdk.filename));
  const runtime = uiAdoptionRuntimeGraph(originalManifest, originalLock);
  uiAdoptionObject(receipt.runtime_dependencies, ['react', 'react-dom', 'framer-motion'], 'original runtime dependencies');
  uiAdoptionCheck(isDeepStrictEqual(receipt.runtime_dependencies, runtime), 'original runtime dependency versions differ from original lock');
  uiAdoptionCheck(Array.isArray(receipt.fixtures) && receipt.fixtures.length >= 2, 'executed original behavior and Presence fixtures required');
  const ids = new Set(), suites = new Set();
  for (const fixture of receipt.fixtures) {
    uiAdoptionObject(fixture, ['id', 'suite', 'source', 'assertions'], 'original fixture');
    uiAdoptionCheck(typeof fixture.id === 'string' && /^[A-Za-z0-9][A-Za-z0-9_.:/-]*$/.test(fixture.id) && !ids.has(fixture.id) && ['behavior', 'presence'].includes(fixture.suite), 'distinct original fixture IDs/suites required');
    ids.add(fixture.id); suites.add(fixture.suite); uiAdoptionEvidence(root, fixture.source, 'original immutable fixture source');
    uiAdoptionCheck(Array.isArray(fixture.assertions) && fixture.assertions.length > 0, 'original fixture assertions must be nonempty');
    const assertionIds = new Set();
    for (const assertion of fixture.assertions) {
      uiAdoptionObject(assertion, ['id', 'status'], 'original assertion');
      uiAdoptionCheck(typeof assertion.id === 'string' && assertion.id.trim() && !assertionIds.has(assertion.id) && assertion.status === 'pass', 'distinct passing original assertion records required');
      assertionIds.add(assertion.id);
    }
  }
  uiAdoptionCheck(suites.has('behavior') && suites.has('presence'), 'both original behavior and Presence execution required');
  const execution = uiAdoptionObject(receipt.execution, ['kind', 'command', 'args', 'exit_code', 'started', 'finished', 'report', 'stdout', 'stderr'], 'original execution');
  uiAdoptionCheck(execution.kind === 'actual-original-runtime' && typeof execution.command === 'string' && /^[A-Za-z0-9_./-]+$/.test(execution.command) && execution.command !== '.' && Array.isArray(execution.args) && execution.args.length > 0 && execution.args.every(arg => typeof arg === 'string' && !/[\x00-\x1f\x7f]/.test(arg)) && execution.exit_code === 0, 'actual original command/exit evidence required');
  const started = Date.parse(execution.started), finished = Date.parse(execution.finished);
  uiAdoptionCheck(typeof execution.started === 'string' && typeof execution.finished === 'string' && Number.isFinite(started) && Number.isFinite(finished) && finished > started, 'actual original execution timestamps required');
  uiAdoptionCheck(new Set([execution.report.path, execution.stdout.path, execution.stderr.path]).size === 3, 'distinct raw original output artifacts required');
  const reportBytes = uiAdoptionEvidence(root, execution.report, 'original native execution report'), stdout = uiAdoptionEvidence(root, execution.stdout, 'original native stdout');
  uiAdoptionEvidence(root, execution.stderr, 'original native stderr');
  uiAdoptionCheck(reportBytes.equals(stdout), 'original native report must equal retained actual stdout bytes');
  const native = uiAdoptionJSON(reportBytes, 'original native execution report');
  uiAdoptionObject(native, ['schema', 'check', 'status', 'app', 'sha', 'tree_sha256', 'toolchain_digest', 'runtime_sdk', 'runtime_dependencies', 'dependency_graph', 'fixtures'], 'native original execution');
  for (const key of ['schema', 'status', 'app', 'sha', 'tree_sha256', 'toolchain_digest', 'runtime_sdk', 'runtime_dependencies', 'dependency_graph']) uiAdoptionCheck(isDeepStrictEqual(native[key], receipt[key]), `native original ${key} binding differs`);
  uiAdoptionCheck(native.check === 'cat-original-ui-runtime-execution', 'native actual execution report required, not a fixture declaration');
  const executed = receipt.fixtures.map(fixture => ({ ...fixture, executed: true, assertions: fixture.assertions.map(assertion => ({ ...assertion, executed: true })) }));
  uiAdoptionCheck(isDeepStrictEqual(native.fixtures, executed), 'native executed fixtures/assertions must exactly cover all immutable original records, with no skips');
  return { path: phase.legacy.receipt, sha256: phase.legacy.receipt_sha256, source_sha: receipt.sha, tree_sha256: receipt.tree_sha256, toolchain_digest: receipt.toolchain_digest, runtime_sdk: runtimeSdk, runtime_dependencies: runtime, dependency_graph: receipt.dependency_graph, fixture_ids: [...ids], assertion_count: receipt.fixtures.reduce((count, fixture) => count + fixture.assertions.length, 0), evidence_paths: [receipt.dependency_graph.manifest.path, receipt.dependency_graph.lock.path, ...receipt.fixtures.map(fixture => fixture.source.path), execution.report.path, execution.stdout.path, execution.stderr.path] };
}
function uiAdoptionInstalled(root, layout, sdk, allowAbsent = false) {
  const directory = noLinks(root, layout.installed, true);
  if (!fs.existsSync(directory)) { uiAdoptionCheck(allowAbsent, 'selected UI installation missing'); return undefined; }
  uiAdoptionCheck(fs.lstatSync(directory).isDirectory(), 'installed UI must be regular directory');
  for (const [name, entry] of sdk.entries) if (entry.type === 'file') {
    const bytes = uiAdoptionFile(root, `${layout.installed}/${name.slice(8)}`);
    uiAdoptionCheck(bytes.equals(entry.data), `installed UI file differs from selected/sealed SDK: ${name}`);
  }
  return uiAdoptionJSON(uiAdoptionFile(root, `${layout.installed}/package.json`), 'installed UI manifest');
}
/** Pure read-only preflight. Staged mode cannot create/restore an old UI pointer. */
export function inspectUiAdoption(root, config, kit, { parseArchive = readTarGz } = {}) {
  root = fs.realpathSync(root);
  const phase = validateUiAdoption(config), layout = uiAdoptionLayout(config), selected = uiAdoptionSelected(kit, parseArchive);
  const manifest = uiAdoptionJSON(uiAdoptionFile(root, layout.manifest), 'owning UI manifest');
  const publicConfig = { role: config.role, app: config.app, npm_dir: safePath(config.npm_dir ?? 'frontend/node_modules/@roedu/web-kit'), vendor_dir: layout.vendor, go_dirs: config.go_dirs.map(directory => safePath(directory, true)), ...(phase ? { ui_adoption: phase } : {}) };
  const common = { selected: { tag: kit.tag, name: '@roedu/ui', version: selected.manifest.version, filename: selected.filename, archive_sha256: selected.sha256, pointer: layout.pointer(selected.filename) }, manifest: layout.manifest, lock: layout.lock, installed: layout.installed, vendor_dir: layout.vendor, public_config: publicConfig, config_sha256: sha(JSON.stringify(publicConfig)) };
  if (!phase) return { ...common, mode: 'active', pending: false, preserve: [] };
  const legacyName = 'roedu-ui-0.3.0.tgz', archive = `${layout.vendor}/${legacyName}`, sidecar = archive + '.sha256';
  uiAdoptionDeclaration(manifest, layout.pointer(legacyName));
  const bytes = uiAdoptionFile(root, archive);
  uiAdoptionCheck(sha(bytes) === phase.legacy.archive_sha256, 'sealed original SDK SHA256 differs');
  const legacy = uiAdoptionArchive(bytes, '0.3.0', legacyName, parseArchive);
  const existingSidecar = uiAdoptionFile(root, sidecar, true);
  if (existingSidecar) uiAdoptionCheck(existingSidecar.equals(Buffer.from(`${legacy.sha256}  ${legacyName}\n`)), 'original SDK sidecar identity differs');
  const shrinkwrap = (layout.parent === '.' ? '' : layout.parent + '/') + 'npm-shrinkwrap.json';
  uiAdoptionCheck(!fs.existsSync(noLinks(root, shrinkwrap, true)), 'alternate staged npm shrinkwrap graph refused');
  uiAdoptionLock(manifest, uiAdoptionJSON(uiAdoptionFile(root, layout.lock), 'live owning npm lock'), legacy, layout.pointer(legacyName));
  // Existing new UI bytes/manifest cannot be reverted by a staged configuration.
  // No node_modules is copied or relinked; an absent first-sync installation is valid.
  uiAdoptionInstalled(root, layout, legacy, true);
  const receipt = verifyUiAdoptionReceipt(root, phase, legacy, layout);
  return { ...common, mode: 'staged-react', pending: true, until: 'S1-M2', legacy: { version: '0.3.0', filename: legacyName, archive, archive_sha256: legacy.sha256, pointer: layout.pointer(legacyName), ...(existingSidecar ? { sidecar } : {}), source_sha: phase.legacy.source_sha, receipt: receipt.path, receipt_sha256: receipt.sha256 }, preserve: [archive, ...(existingSidecar ? [sidecar] : [])], receipt };
}
/** Separate from lint/scope.json: never exempts any source/style/dependency rule. */
export function uiAdoptionPending(plan) {
  if (plan.mode === 'active') return undefined;
  uiAdoptionCheck(plan.mode === 'staged-react' && plan.pending === true && plan.receipt, 'verified staged UI plan required');
  return { mode: 'staged-react', status: 'pending', until: 'S1-M2', source: 'repo:kit-config', config_sha256: plan.config_sha256, legacy: structuredClone(plan.public_config.ui_adoption.legacy), selected_ui: { version: plan.selected.version, archive_sha256: plan.selected.archive_sha256 } };
}
function uiAdoptionDependencyClosure(root, layout, lock, sdk) {
  const rows = lock.packages, seen = new Set(), queue = ['node_modules/@roedu/ui'];
  function target(parent, name) {
    uiAdoptionCheck(/^(@[A-Za-z0-9_.-]+\/)?[A-Za-z0-9_.-]+$/.test(name), 'nonliteral SDK dependency name refused');
    let cursor = parent;
    while (true) {
      const key = (cursor ? cursor + '/' : '') + 'node_modules/' + name;
      if (Object.hasOwn(rows, key)) return key;
      if (!cursor) return undefined;
      const next = path.posix.dirname(cursor); cursor = next === '.' ? '' : next;
    }
  }
  while (queue.length) {
    const key = queue.shift(); if (seen.has(key)) continue; seen.add(key);
    const row = rows[key]; uiAdoptionCheck(row && !row.link && typeof row.version === 'string', 'SDK installed graph links/aliases refused');
    const relative = (layout.parent === '.' ? '' : layout.parent + '/') + safePath(key) + '/package.json';
    const installed = uiAdoptionJSON(uiAdoptionFile(root, relative), 'installed SDK dependency manifest');
    const expectedName = key.split('node_modules/').at(-1);
    uiAdoptionCheck(installed.name === (row.name ?? expectedName) && installed.name === expectedName && installed.version === row.version, `installed SDK dependency graph identity differs: ${key}`);
    for (const field of UI_ADOPTION_RUNTIME_FIELDS) uiAdoptionCheck(isDeepStrictEqual(installed[field] ?? {}, row[field] ?? {}), `installed SDK dependency metadata differs: ${key}/${field}`);
    const refs = { ...installed.dependencies, ...installed.optionalDependencies, ...installed.peerDependencies };
    for (const name of Object.keys(refs)) {
      const found = target(key, name), optional = Object.hasOwn(installed.optionalDependencies ?? {}, name) || installed.peerDependenciesMeta?.[name]?.optional === true;
      if (!found) { uiAdoptionCheck(optional, `installed SDK dependency graph edge missing: ${key}/${name}`); continue; }
      uiAdoptionCheck(typeof refs[name] === 'string' && !refs[name].startsWith('npm:'), `SDK dependency alias refused: ${key}/${name}`);
      if (/^\d+\.\d+\.\d+$/.test(refs[name])) uiAdoptionCheck(rows[found].version === refs[name], `selected SDK exact dependency version differs: ${key}/${name}`);
      // Optional platform dependencies may be recorded but not installed. Other
      // runtime edges must resolve to real manifests and are recursively proven.
      const filename = (layout.parent === '.' ? '' : layout.parent + '/') + safePath(found) + '/package.json';
      if (optional && !fs.existsSync(noLinks(root, filename, true))) continue;
      queue.push(found);
    }
  }
  uiAdoptionCheck(seen.has('node_modules/@roedu/ui') && sdk.manifest.name === '@roedu/ui', 'installed SDK graph root missing');
  return [...seen].sort();
}
/** Application M2 hooks must execute this proof; a pending label is insufficient. */
export function requireActiveUi(root = process.cwd(), config = readConsumerConfig(root)) {
  uiAdoptionCheck(arguments.length <= 2, 'requireActiveUi accepts only root/config; kit and parser overrides are refused');
  root = fs.realpathSync(root);
  uiAdoptionCheck(config.role === 'consumer' && validateUiAdoption(config) === undefined, 'active UI is required; staged-react cannot qualify M2');
  // Selection and every archive boundary come solely from committed actual kit
  // inputs. Neither caller-created kit objects nor caller parsers can qualify M2.
  const kit = loadKit(root), layout = uiAdoptionLayout(config), selected = uiAdoptionSelected(kit, readTarGz), plan = inspectUiAdoption(root, config, kit);
  const manifest = uiAdoptionJSON(uiAdoptionFile(root, layout.manifest), 'active owning manifest');
  uiAdoptionDeclaration(manifest, layout.pointer(selected.filename));
  const archive = `${layout.vendor}/${selected.filename}`, sidecar = archive + '.sha256';
  uiAdoptionCheck(uiAdoptionFile(root, archive).equals(selected.data) && uiAdoptionFile(root, sidecar).equals(Buffer.from(`${selected.sha256}  ${selected.filename}\n`)), 'active vendor UI bytes/sidecar differ from selected kit');
  uiAdoptionCheck(!fs.existsSync(noLinks(root, `${layout.vendor}/roedu-ui-0.3.0.tgz`, true)) && !fs.existsSync(noLinks(root, `${layout.vendor}/roedu-ui-0.3.0.tgz.sha256`, true)), 'active UI retains old SDK archive/sidecar');
  const shrinkwrap = (layout.parent === '.' ? '' : layout.parent + '/') + 'npm-shrinkwrap.json';
  uiAdoptionCheck(!fs.existsSync(noLinks(root, shrinkwrap, true)), 'alternate active npm shrinkwrap graph refused');
  const lockBytes = uiAdoptionFile(root, layout.lock), lock = uiAdoptionJSON(lockBytes, 'active owning npm lock');
  uiAdoptionLock(manifest, lock, selected, layout.pointer(selected.filename));
  uiAdoptionInstalled(root, layout, selected);
  const graph = uiAdoptionDependencyClosure(root, layout, lock, selected);
  return { schema: 1, check: 'require-active-ui', status: 'pass', mode: 'active', pending: false, tag: kit.tag, pointer: plan.selected.pointer, version: selected.manifest.version, archive_sha256: selected.sha256, installed_manifest_sha256: sha(uiAdoptionFile(root, `${layout.installed}/package.json`)), owning_lock_sha256: sha(lockBytes), installed_graph: graph };
}

function goArchive(data) {
  const entries = readTarGz(data), source = new Map();
  for (const [name, entry] of entries) {
    if (name === 'web-kit') { if (entry.type !== 'directory') fail('Go archive root must be a directory'); continue; }
    if (!name.startsWith('web-kit/')) fail(`Unknown Go archive root: ${name}`);
    const rel = name.slice(8), first = rel.split('/')[0];
    if (isPythonBytecodePath(rel)) fail(`Excluded Python bytecode/cache in Go archive: ${name}`);
    if (rel.split('/').some(part => ['.git', 'node_modules', '.gate', '.vitest', 'test-results', 'TASK_BRIEF.md', 'TASK_RESULT.md', 'SWARM_RESULT.md'].includes(part) || part === '.env' || part.startsWith('.env.'))) fail(`Excluded cache/secret member in Go archive: ${name}`);
    if (!GO_DIRS.has(first) && !['go.mod', 'go.sum', 'README.md', 'LICENSE', 'LICENSE.md', 'LICENSE.txt'].includes(rel)) fail(`Unknown Go archive path: ${name}`);
    if (GO_DIRS.has(first) && rel === first && entry.type !== 'directory') fail(`Go package directory required: ${name}`);
    // budget is a mixed Go/npm directory. Only its owning Go source and the
    // two fixtures read by the actual Go schema test cross this archive boundary.
    if (first === 'budget') {
      const directory = rel === 'budget' || rel === 'budget/testdata';
      const file = /^budget\/[^/]+\.go$/.test(rel) || ['budget/testdata/budgets.seed.json', 'budget/testdata/schema-cases.json'].includes(rel);
      if (!directory && !file) fail(`Npm or unregistered budget file in Go archive: ${name}`);
      if (entry.type !== (directory ? 'directory' : 'file')) fail(`Go budget member type mismatch: ${name}`);
    }
    if (first === 'lint' && rel !== 'lint' && !rel.startsWith('lint/rawcheck/')) fail(`Npm lint file in Go archive: ${name}`);
    if (first === 'sample' && (/(^|\/)(e2e|src|node_modules|package\.json|package-lock\.json|vite\.config\.[^/]+|playwright\.config\.[^/]+)(\/|$)/.test(rel))) fail(`Npm sample file in Go archive: ${name}`);
    if (first === 'testdata' && rel !== 'testdata' && !/^testdata\/(djt|golden|rawcheck)(\/|$)/.test(rel)) fail(`Npm testdata in Go archive: ${name}`);
    if (entry.type === 'file') source.set(rel, entry);
  }
  const mod = source.get('go.mod')?.data.toString('utf8');
  if (!mod || goRecords(mod).find(record => record.kind === 'module')?.module !== MODULE) fail('Go archive module mismatch');
  return source;
}
/** Private canonical byte admission; only source-owned readers call this closure. */
function admitCanonicalKitBundle(names, readBytes) {
  if (!Array.isArray(names) || names.some(name => typeof name !== 'string') || new Set(names).size !== names.length || typeof readBytes !== 'function') fail('Canonical kit names/raw reader required');
  for (const name of names) safePath(name);
  const read = name => {
    const data = readBytes(name);
    if (!Buffer.isBuffer(data)) fail(`Actual kit bytes required: ${name}`);
    return data;
  };
  const tagText = read('CORE_TAG').toString('utf8');
  if (!/^core-v1\.\d+\n?$/.test(tagText)) fail('Malformed committed CORE_TAG');
  const tag = tagText.trim(), goName = `web-kit-go-${tag}.tgz`;
  const uiName = names.find(name => /^roedu-ui-\d+\.\d+\.\d+\.tgz$/.test(name));
  const kitName = names.find(name => /^roedu-web-kit-\d+\.\d+\.\d+\.tgz$/.test(name));
  const expected = ['CORE_TAG', 'SHA256SUMS', uiName, kitName, goName];
  if (!uiName || !kitName || names.length !== expected.length || names.some(name => !expected.includes(name))) fail('Kit must contain exactly CORE_TAG, SHA256SUMS and the three archives');
  const sums = new Map();
  for (const line of read('SHA256SUMS').toString('utf8').split('\n').filter(Boolean)) {
    const match = /^([a-f0-9]{64}) [ *]([^/\\\s]+)$/.exec(line);
    if (!match || sums.has(match[2]) || ![uiName, kitName, goName].includes(match[2])) fail('Malformed/duplicate/unknown SHA256SUMS entry');
    sums.set(match[2], match[1]);
  }
  if (sums.size !== 3) fail('All three archive hashes required');
  const archives = new Map();
  for (const name of [uiName, kitName, goName]) {
    const data = read(name); if (sha(data) !== sums.get(name)) fail(`Archive hash mismatch: ${name}`); archives.set(name, data);
  }
  const ui = npmArchive(archives.get(uiName), '@roedu/ui', uiName), npm = npmArchive(archives.get(kitName), '@roedu/web-kit', kitName);
  const coreLock = JSON.parse(archiveFile(npm.entries, 'package/versions.lock.json').data.toString('utf8'));
  if (coreLock.core_tag !== undefined && coreLock.core_tag !== tag) fail('Npm lock core_tag differs from committed CORE_TAG');
  const source = goArchive(archives.get(goName));
  const templates = new Map();
  for (const file of GATE_FILES) templates.set(file, archiveFile(npm.entries, `package/templates/${file === 'scripts/gate.sh' ? 'gate.sh' : file}`));
  const environment = archiveFile(npm.entries, 'package/templates/.gate.env').data.toString('utf8');
  return { tag, ui, npm, source, templates, environment, coreLock, sums };
}
export function loadKit(root) {
  root = fs.realpathSync(root);
  const kitDir = noLinks(root, 'kit');
  const names = fs.readdirSync(kitDir).sort();
  for (const name of names) { safePath(name); const stat = fs.lstatSync(path.join(kitDir, name)); if (!stat.isFile() || stat.isSymbolicLink()) fail(`Invalid kit input: ${name}`); }
  return admitCanonicalKitBundle(names, name => fs.readFileSync(noLinks(root, `kit/${name}`)));
}
function regularFileDestination(root, relative, allowMissing = false) {
  const filename = noLinks(root, relative, allowMissing);
  if (fs.existsSync(filename) && !fs.lstatSync(filename).isFile()) fail(`File destination must be regular or absent: ${relative}`);
  return filename;
}
function directoryDestination(root, relative, allowMissing = false) {
  const directory = noLinks(root, relative, allowMissing);
  if (fs.existsSync(directory) && !fs.lstatSync(directory).isDirectory()) fail(`Directory destination required: ${relative}`);
  return directory;
}
/** Decodes Go's quoted/raw string tokens without executing or importing Go code. */
function goTokens(line) {
  const result = [];
  let index = 0;
  while (index < line.length) {
    if (/\s/.test(line[index])) { index++; continue; }
    if (line.slice(index, index + 2) === '//') break;
    if ('()'.includes(line[index])) { result.push(line[index++]); continue; }
    if (line.slice(index, index + 2) === '=>') { result.push('=>'); index += 2; continue; }
    if (line[index] === '"' || line[index] === '`') {
      const quote = line[index++]; let value = '', closed = false;
      while (index < line.length) {
        let character = line[index++];
        if (character === quote) { closed = true; break; }
        if (character === '\\' && quote === '"') {
          const escape = line[index++], simple = { a: '\x07', b: '\b', f: '\f', n: '\n', r: '\r', t: '\t', v: '\x0b', '\\': '\\', '"': '"' };
          if (Object.hasOwn(simple, escape)) character = simple[escape];
          else {
            let digits, base;
            if (escape === 'x' || escape === 'u' || escape === 'U') {
              const count = escape === 'x' ? 2 : escape === 'u' ? 4 : 8; digits = line.slice(index, index + count); index += count; base = 16;
              if (digits.length !== count || !/^[a-fA-F0-9]+$/.test(digits)) fail('Malformed quoted Go escape');
            } else if (/[0-7]/.test(escape ?? '')) {
              digits = escape + line.slice(index, index + 2); index += 2; base = 8;
              if (!/^[0-7]{3}$/.test(digits)) fail('Malformed quoted Go escape');
            } else fail('Malformed quoted Go escape');
            const point = Number.parseInt(digits, base);
            if (point > 0x10ffff || (point >= 0xd800 && point <= 0xdfff) || (base === 8 && point > 255)) fail('Invalid quoted Go code point');
            character = String.fromCodePoint(point);
          }
        }
        value += character;
      }
      if (!closed || /[\x00-\x1f\x7f]/.test(value)) fail('Malformed quoted Go path');
      result.push(value); continue;
    }
    const begin = index;
    while (index < line.length && !/\s/.test(line[index]) && !'()'.includes(line[index]) && line.slice(index, index + 2) !== '//' && line.slice(index, index + 2) !== '=>') index++;
    result.push(line.slice(begin, index));
  }
  return result;
}
function goRecords(text) {
  if (text.includes('\0')) fail('Malformed Go module text');
  let block = '', modules = 0;
  const records = [];
  for (const [index, line] of text.split(/\r?\n/).entries()) {
    const tokens = goTokens(line); if (!tokens.length) continue;
    if (tokens[0] === ')') { if (!block || tokens.length !== 1) fail('Malformed Go directive block'); block = ''; continue; }
    if (tokens.length === 2 && tokens[1] === '(') { if (block) fail('Nested Go directive block'); block = tokens[0]; continue; }
    const kind = block || tokens[0], body = block ? tokens : tokens.slice(1);
    if (kind === 'module') { if (body.length !== 1) fail('Malformed Go module directive'); modules++; records.push({ index, kind, module: body[0] }); }
    if (kind === 'require') {
      if (body.length !== 2) fail('Malformed Go require directive');
      records.push({ index, kind, module: body[0], version: body[1] });
    }
    if (kind === 'replace') {
      const arrow = body.indexOf('=>');
      if (![1, 2].includes(arrow) || ![arrow + 2, arrow + 3].includes(body.length)) fail('Malformed Go replace directive');
      records.push({ index, kind, module: body[0], version: arrow === 2 ? body[1] : undefined, target: body[arrow + 1], targetVersion: body[arrow + 2] });
    }
  }
  if (block || modules !== 1) fail('One complete Go module directive required');
  return records;
}
function discoverGoDirs(root, relative = '.') {
  const current = relative === '.' ? root : directoryDestination(root, relative), found = [];
  const modRelative = relative === '.' ? 'go.mod' : `${relative}/go.mod`;
  const mod = regularFileDestination(root, modRelative, true);
  if (fs.existsSync(mod) && goRecords(fs.readFileSync(mod, 'utf8')).some(record => record.kind === 'replace' && record.module === MODULE)) found.push(relative);
  for (const item of fs.readdirSync(current, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    if (item.name.startsWith('.') || ['kit', 'node_modules', 'third_party', 'vendor', 'sample', 'testdata', 'dist', 'test-results', 'TASK_BRIEF.md', 'TASK_RESULT.md', 'SWARM_RESULT.md'].includes(item.name)) continue;
    if (item.isSymbolicLink()) fail('Symlink encountered during Go-module discovery');
    if (item.isDirectory()) found.push(...discoverGoDirs(root, relative === '.' ? item.name : `${relative}/${item.name}`));
  }
  return found;
}
export function validateConfig(root, config) {
  if (!config || typeof config !== 'object' || Array.isArray(config) || Object.keys(config).some(key => !['role', 'app', 'npm_dir', 'vendor_dir', 'go_dirs', 'ui_adoption'].includes(key))) fail('Unknown consumer config fields');
  const uiAdoption=validateUiAdoption(config);
  if (config.role !== 'consumer' || typeof config.app !== 'string' || !/^[A-Za-z][A-Za-z0-9_-]*$/.test(config.app)) fail('Explicit consumer role/app required');
  const portable = (value, dot = false) => { const normalized = safePath(value, dot); if (normalized !== '.' && normalized.split('/').some(part => !/^[A-Za-z0-9_@.-]+$/.test(part))) fail('Unsafe nonliteral configured path'); return normalized; };
  if (config.npm_dir !== undefined) portable(config.npm_dir);
  const vendor = portable(config.vendor_dir ?? 'frontend/vendor');
  if (vendor.split('/').some(part => part.startsWith('.') || ['kit', 'node_modules', 'third_party', 'dist', 'test-results', 'TASK_BRIEF.md', 'TASK_RESULT.md', 'SWARM_RESULT.md'].includes(part))) fail('Unsafe npm vendor destination');
  const goDirs = config.go_dirs ?? discoverGoDirs(root);
  if (!Array.isArray(goDirs) || !goDirs.length || new Set(goDirs).size !== goDirs.length) fail('Consumer Go module directories required');
  for (const directory of goDirs) {
    portable(directory, true);
    if (directory !== '.' && directory.split('/').some(part => part.startsWith('.') || ['kit', 'third_party', 'node_modules', 'vendor', 'dist', 'test-results', 'TASK_BRIEF.md', 'TASK_RESULT.md', 'SWARM_RESULT.md'].includes(part))) fail('Unsafe Go module destination');
    directoryDestination(root, directory); regularFileDestination(root, directory === '.' ? 'go.mod' : `${directory}/go.mod`);
  }
  const contains = (parent, child) => parent === child || child.startsWith(parent + '/');
  const trees = [vendor, ...goDirs.map(directory => (directory === '.' ? '' : portable(directory, true) + '/') + 'third_party/webkit')];
  const immutable = ['scripts/gate.sh', 'compose.gate.yml', 'Taskfile.yml', 'Dockerfile.toolchain', '.gate.env', 'versions.lock.json', 'Taskfile.repo.yml', '.codex', '.agent', '.github/workflows', 'ci.yml', 'kit', 'legacy', 'web-kit/templates', 'web-kit/schemas', 'lint/scope.json', 'kit.lock.json', 'AGENTS.md', 'docs/PROGRAM.md', 'budgets.json', 'engine.json', '.gitattributes'];
  if (trees.some((tree, index) => trees.some((other, otherIndex) => index !== otherIndex && (contains(tree, other) || contains(other, tree))))) fail('Unsafe overlapping kit destinations');
  if (trees.some(tree => immutable.some(file => contains(tree, file) || contains(file, tree)))) fail('Unsafe kit destination overlaps hooks or protected config');
  const manifest = path.posix.join(path.posix.dirname(vendor), 'package.json');
  regularFileDestination(root, manifest); directoryDestination(root, vendor, true);
  for (const file of [...GATE_FILES, '.gate.env', 'versions.lock.json']) regularFileDestination(root, file, true);
  return { role: 'consumer', app: config.app, npm_dir: config.npm_dir, vendor_dir: vendor, go_dirs: [...goDirs], ...(uiAdoption?{ui_adoption:uiAdoption}:{}), manifest };
}
function pinManifest(manifest, kit, adoption) {
  if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest)) fail('Consumer package manifest required');
  const result = structuredClone(manifest);
  for (const [name, filename, fallback] of [['@roedu/ui', kit.ui.filename, 'dependencies'], ['@roedu/web-kit', kit.npm.filename, 'devDependencies']]) {
    if(name==='@roedu/ui'&&adoption?.mode==='staged-react')continue;
    const sections = ['dependencies', 'devDependencies', 'optionalDependencies', 'peerDependencies'].filter(section => result[section] && Object.hasOwn(result[section], name));
    if (sections.length > 1) fail(`Duplicate consumer dependency declaration: ${name}`);
    const section = sections[0] ?? fallback;
    if (section === 'peerDependencies') fail('A consumer kit must be an installed dependency, not a peer');
    result[section] ??= {}; result[section][name] = `file:${path.posix.basename(kit.vendor_dir)}/${filename}`;
  }
  return result;
}
/** Align only dependencies already declared by this consumer to the selected core lock. */
export function alignCoreNpm(manifest, coreLock) {
  const result = structuredClone(manifest), changes = [];
  for (const entry of tools(coreLock).values()) {
    if (entry.scope !== 'core' || entry.kind !== 'npm' || !['pinned', 'optional'].includes(entry.status ?? 'pinned')) continue;
    for (const section of ['dependencies', 'devDependencies', 'optionalDependencies', 'peerDependencies']) {
      if (!result[section] || !Object.hasOwn(result[section], entry.tool)) continue;
      if (!stableVersion(entry.version)) fail(`Stable core npm version required: ${entry.tool}`);
      const previous = result[section][entry.tool];
      if (previous === entry.version) continue;
      const floor = typeof previous === 'string' && /^(?:\^|~|>=)?(\d+)(?:\.(\d+))?(?:\.(\d+))?$/.exec(previous);
      if (!floor) fail(`Unsupported core npm declaration: ${entry.tool}; align its manifest explicitly before kit sync`);
      const minimum = `${floor[1]}.${floor[2] ?? '0'}.${floor[3] ?? '0'}`;
      if (compareVersions(minimum, entry.version) > 0) fail(`Higher core npm manifest version refused: ${entry.tool}`);
      result[section][entry.tool] = entry.version;
      changes.push({ dependency: entry.tool, section, from: previous, to: entry.version });
    }
  }
  return { manifest: result, changes };
}
export function assertRuntimeCompatible(coreLock, actual) {
  const required = [...tools(coreLock).values()].filter(entry => entry.scope === 'core' && (entry.kind === 'runtime' || entry.tool === 'npm'));
  for (const entry of required) {
    const found = actual[entry.tool];
    if (!stableVersion(entry.version) || !stableVersion(found)) fail(`Runtime prerequisite unavailable: ${entry.tool}`);
    if (compareVersions(found, entry.version) < 0) fail(`KIT_SYNC_RUNTIME_TOO_OLD ${entry.tool} required=${entry.version} executing=${found}; owner must start kit sync with the selected compatible toolchain before dependency generation`);
  }
}
function runnerVersions(coreLock) {
  const actual = { node: process.versions.node };
  for (const entry of tools(coreLock).values()) {
    if (entry.scope !== 'core' || (entry.kind !== 'runtime' && entry.tool !== 'npm') || entry.tool === 'node') continue;
    if (!['go', 'npm'].includes(entry.tool)) fail(`Unsupported runtime prerequisite: ${entry.tool}`);
    const result = spawnSync(entry.tool, entry.tool === 'go' ? ['version'] : ['--version'], { cwd: os.tmpdir(), env: { ...process.env, GOTOOLCHAIN: 'local' }, encoding: 'utf8', maxBuffer: 1024 * 1024 });
    if (result.error || result.status !== 0) fail(`Runtime prerequisite unavailable: ${entry.tool}`);
    const version = entry.tool === 'go' ? /\bgo(\d+\.\d+\.\d+)\b/.exec(result.stdout)?.[1] : result.stdout.trim();
    actual[entry.tool] = version;
  }
  return actual;
}
function goPins(text) {
  const records = goRecords(text).filter(record => record.module === MODULE), requires = records.filter(record => record.kind === 'require'), replaces = records.filter(record => record.kind === 'replace');
  if (requires.length > 1 || replaces.length > 1) fail('Duplicate web-kit Go require/replace');
  return { require: requires[0]?.version, replace: replaces[0] ? { target: replaces[0].target, version: replaces[0].targetVersion } : undefined, records };
}
export function pinGoMod(text, tag) {
  const desired = `v0.0.0-${tag}`, current = goPins(text);
  if (current.require === desired && current.replace?.target === './third_party/webkit' && !current.replace.version) return text;
  const remove = new Set(current.records.filter(record => record.kind === 'require' || record.kind === 'replace').map(record => record.index));
  const lines = text.split(/\r?\n/).filter((_line, index) => !remove.has(index));
  return lines.join('\n').trimEnd() + `\n\nrequire ${MODULE} ${desired}\nreplace ${MODULE} => ./third_party/webkit\n`;
}
function environmentLine(text, name) {
  const matches = [...text.matchAll(new RegExp(`^${name}=([^\\r\\n]*)`, 'gm'))];
  if (matches.length !== 1 || !matches[0][1]) fail(`Exactly one ${name} line required`);
  return matches[0][1];
}
export function mergeEnvironment(current, template, coreLock) {
  let result = current;
  for (const [name, expected] of [['TOOLCHAIN_IMAGE', coreLock.toolchain_image.version], ['TOOLCHAIN_DIGEST', coreLock.toolchain_image.image_id]]) {
    const value = environmentLine(template, name); environmentLine(current, name);
    if (value !== expected || /[\s'"`$]/.test(value) || (name === 'TOOLCHAIN_DIGEST' && !/^sha256:[a-f0-9]{64}$/.test(value))) fail(`Template ${name} does not match core lock`);
    result = result.replace(new RegExp(`^${name}=[^\\r\\n]*`, 'm'), `${name}=${value}`);
  }
  return result;
}
function planGoDependencies(root, goDirs, kit, writes, replacements) {
  for (const directory of goDirs) {
    const prefix = directory === '.' ? '' : `${directory}/`, vendor = `${prefix}third_party/webkit`;
    directoryDestination(root, vendor, true); regularTree(noLinks(root, vendor, true)); replacements.set(vendor, kit.source);
    const goMod = `${prefix}go.mod`, stat = fs.statSync(noLinks(root, goMod));
    writes.set(goMod, { data: Buffer.from(pinGoMod(fs.readFileSync(noLinks(root, goMod), 'utf8'), kit.tag)), mode: stat.mode & 0o777 });
  }
}
function prepare(root, config, kit, environmentMode = 'source') {
  const cfg = validateConfig(root, config); kit = { ...kit, vendor_dir: cfg.vendor_dir };
  const writes = new Map(), replacements = new Map(), removals = [];
  const manifestOriginal = fs.readFileSync(noLinks(root, cfg.manifest));
  const adoption=inspectUiAdoption(root,cfg,kit);
  const manifest = JSON.parse(manifestOriginal.toString('utf8')), alignment = alignCoreNpm(pinManifest(manifest, kit, adoption), kit.coreLock), pinned = alignment.manifest;
  writes.set(cfg.manifest, { data: JSON.stringify(manifest) === JSON.stringify(pinned) ? manifestOriginal : json(pinned), mode: fs.statSync(noLinks(root, cfg.manifest)).mode & 0o777 });
  for (const npm of [kit.ui, kit.npm]) {
    writes.set(`${cfg.vendor_dir}/${npm.filename}`, { data: npm.data, mode: 0o644 });
    writes.set(`${cfg.vendor_dir}/${npm.filename}.sha256`, { data: Buffer.from(`${kit.sums.get(npm.filename)}  ${npm.filename}\n`), mode: 0o644 });
  }
  const oldVendorDirectory = directoryDestination(root, cfg.vendor_dir, true);
  if (fs.existsSync(oldVendorDirectory)) for (const name of fs.readdirSync(oldVendorDirectory)) if (/^roedu-(ui|web-kit)-[^/]+\.tgz(?:\.sha256)?$/.test(name)) regularFileDestination(root, `${cfg.vendor_dir}/${name}`);
  const oldVendor = regularTree(oldVendorDirectory);
  for (const filename of oldVendor.keys()) if (/^roedu-(ui|web-kit)-[^/]+\.tgz(?:\.sha256)?$/.test(filename) && !writes.has(`${cfg.vendor_dir}/${filename}`)&&!adoption.preserve.includes(`${cfg.vendor_dir}/${filename}`)) removals.push(`${cfg.vendor_dir}/${filename}`);
  planGoDependencies(root, cfg.go_dirs, kit, writes, replacements);
  for (const [destination, entry] of kit.templates) writes.set(destination, entry);
  const currentEnv = fs.readFileSync(noLinks(root, '.gate.env'), 'utf8');
  const sourceEnv = mergeEnvironment(currentEnv, kit.environment, kit.coreLock);
  writes.set('.gate.env', { data: Buffer.from(environmentMode === 'runner' ? kit.environment : sourceEnv), mode: fs.statSync(noLinks(root, '.gate.env')).mode & 0o777 });
  const currentLockBytes = fs.readFileSync(noLinks(root, 'versions.lock.json'));
  const currentLock = JSON.parse(currentLockBytes.toString('utf8')), merged = mergeVersions(currentLock, kit.coreLock, kit.tag, cfg.app);
  writes.set('versions.lock.json', { data: JSON.stringify(currentLock) === JSON.stringify(merged) ? currentLockBytes : json(merged), mode: fs.statSync(noLinks(root, 'versions.lock.json')).mode & 0o777 });
  for (const destination of [...writes.keys(), ...removals]) regularFileDestination(root, destination, true);
  for (const [vendor, tree] of replacements) for (const file of tree.keys()) regularFileDestination(root, `${vendor}/${safePath(file)}`, true);
  return { cfg, kit, writes, replacements, removals, npmChanges: alignment.changes, adoption };
}
function equalFile(root, relative, entry) {
  const filename = noLinks(root, relative, true);
  if (!fs.existsSync(filename)) return false;
  const stat = fs.lstatSync(filename);
  return stat.isFile() && fs.readFileSync(filename).equals(entry.data) && (stat.mode & 0o111) === (entry.mode & 0o111);
}
function equalTree(root, relative, expected) {
  const actual = regularTree(noLinks(root, relative, true));
  return actual.size === expected.size && [...expected].every(([file, entry]) => actual.get(file)?.data.equals(entry.data) && (actual.get(file).mode & 0o111) === (entry.mode & 0o111));
}
function writeFile(root, relative, entry) {
  const file = noLinks(root, relative, true); fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, entry.data, { mode: entry.mode }); fs.chmodSync(file, entry.mode);
}
function command(root, target) {
  const result = spawnSync('task', ['--silent', target], { cwd: root, encoding: 'utf8', env: process.env, maxBuffer: 32 * 1024 * 1024 });
  if (result.error) throw result.error;
  if (result.status !== 0) fail(`task ${target} exited ${result.status}: ${result.stderr || result.stdout}`);
  return result;
}
export function assertFrozenConfig(root, config, required = false) {
  const metadata = regularFileDestination(root, '.gate/kit-sync/wrapper-kit-config.json', true);
  if (!fs.existsSync(metadata)) { if (required) fail('kit:sync requires the wrapper captured configuration'); return config; }
  const captured = JSON.parse(fs.readFileSync(metadata, 'utf8'));
  if (captured.schema !== 1 || captured.target !== 'kit:sync' || !/^[a-f0-9]{40}([a-f0-9]{24})?$/.test(captured.sha) || !/^[a-f0-9]{64}$/.test(captured.tree_sha256) || !/^sha256:[a-f0-9]{64}$/.test(captured.toolchain_digest)) fail('Invalid frozen wrapper configuration identity');
  if (required && (captured.sha !== process.env.GATE_SHA || captured.tree_sha256 !== process.env.GATE_TREE_SHA256)) fail('Frozen wrapper configuration belongs to another invocation');
  const canonical = input => { const cfg = validateConfig(root, input); return { role: cfg.role, app: cfg.app, npm_dir: safePath(cfg.npm_dir ?? 'frontend/node_modules/@roedu/web-kit'), vendor_dir: cfg.vendor_dir, go_dirs: cfg.go_dirs.map(directory => safePath(directory, true)), ...(cfg.ui_adoption?{ui_adoption:cfg.ui_adoption}:{}) }; };
  const expected = canonical(captured.config), actual = canonical(config);
  if (captured.config_sha256 !== sha(JSON.stringify(expected)) || !isDeepStrictEqual(expected, actual)) fail('repo:kit-config changed from the frozen wrapper configuration');
  return expected;
}
export function readConsumerConfig(root) {
  const result = command(root, 'repo:kit-config');
  try { const config = JSON.parse(result.stdout); validateConfig(root, config); return config; } catch (error) { fail(`repo:kit-config must emit only explicit consumer JSON: ${error.message}`); }
}
function checked(checks, name, fn) {
  const start = Date.now();
  try { const result = fn(); checks.push({ name, status: 'pass', duration_ms: Date.now() - start }); return result; }
  catch (error) { checks.push({ name, status: 'fail', reason: error.message, duration_ms: Date.now() - start }); error.checks = checks; throw error; }
}
function drift(root, plan, select) {
  for (const [destination, entry] of plan.writes) if (select(destination) && !equalFile(root, destination, entry)) fail(`Kit drift: ${destination}`);
}
function postChecks(root, plan, checks) {
  if(plan.adoption.pending){checked(checks,'ui-adoption',()=>inspectUiAdoption(root,plan.cfg,plan.kit));checks.at(-1).reason='ui-staged-pending';}
  checked(checks, 'npm-vendor', () => { drift(root, plan, file => file === plan.cfg.manifest || file.startsWith(`${plan.cfg.vendor_dir}/`)); if (plan.removals.some(file => fs.existsSync(noLinks(root, file, true)))) fail('Stale npm kit archive remains'); });
  checked(checks, 'go-vendor', () => { for (const [directory, expected] of plan.replacements) if (!equalTree(root, directory, expected)) fail(`Go source drift: ${directory}`); drift(root, plan, file => file.endsWith('go.mod')); });
  checked(checks, 'gate-templates', () => drift(root, plan, file => GATE_FILES.includes(file) || file === '.gate.env'));
  checked(checks, 'versions-merge', () => drift(root, plan, file => file === 'versions.lock.json'));
}
export function checkKit(root, config) {
  root = fs.realpathSync(root); const checks = [];
  const kit = checked(checks, 'kit-input', () => loadKit(root));
  const plan = checked(checks, 'consumer-config', () => prepare(root, config, kit));
  postChecks(root, plan, checks);
  return { mode: 'check', status: 'pass', tag: kit.tag, changed: [], checks, ...(plan.adoption.pending?{ui_adoption:uiAdoptionPending(plan.adoption)}:{}) };
}
export function syncKit(root, config, options = {}) {
  root = fs.realpathSync(root); config = assertFrozenConfig(root, config); const checks = [], changed = [];
  const kit = checked(checks, 'kit-input', () => loadKit(root));
  // Every input, destination, archive member and downgrade is checked before writes begin.
  checked(checks, 'runner-runtime', () => assertRuntimeCompatible(kit.coreLock, runnerVersions(kit.coreLock)));
  const plan = checked(checks, 'consumer-config', () => prepare(root, config, kit, 'runner'));
  for (const relative of plan.removals) { fs.unlinkSync(noLinks(root, relative)); changed.push(relative); }
  for (const [directory, tree] of plan.replacements) if (!equalTree(root, directory, tree)) {
    fs.rmSync(noLinks(root, directory, true), { recursive: true, force: true });
    for (const [relative, entry] of tree) writeFile(root, `${directory}/${relative}`, entry);
    changed.push(directory);
  }
  for (const [relative, entry] of plan.writes) if (!equalFile(root, relative, entry)) { writeFile(root, relative, entry); changed.push(relative); }
  checked(checks, 'deps', () => {
    const result = options.depsRunner ? options.depsRunner(root, 'deps') : command(root, 'deps');
    if (result?.status !== 0) fail(`Dependency task failed: ${result?.status}`);
    if (result.stdout) process.stderr.write(result.stdout); if (result.stderr) process.stderr.write(result.stderr);
    return result;
  });
  // Dependencies may canonicalize manifests; rebuild their comparison plan, then prove delivery identity.
  const finalPlan = prepare(root, config, kit, 'runner'); postChecks(root, finalPlan, checks);
  return { mode: 'sync', status: 'pass', tag: kit.tag, changed, manifest_changes: plan.npmChanges, checks, ...(finalPlan.adoption.pending?{ui_adoption:uiAdoptionPending(finalPlan.adoption)}:{}) };
}
/** Synthetic USTAR encoder used only to exercise the parser/self-test, never release packing. */
export function fixtureTar(files) {
  const records = [];
  for (const [filename, value] of files) {
    const header = Buffer.alloc(512), data = Buffer.isBuffer(value) ? value : Buffer.from(value);
    if (Buffer.byteLength(filename) > 100) fail('Fixture tar name exceeds USTAR field');
    header.write(filename, 0, 100, 'utf8');
    const number = (offset, length, value) => header.write(value.toString(8).padStart(length - 1, '0') + '\0', offset, length, 'ascii');
    number(100, 8, 0o644); number(108, 8, 0); number(116, 8, 0); number(124, 12, data.length); number(136, 12, 0);
    header.fill(32, 148, 156); header[156] = 48; header.write('ustar\0', 257, 6, 'ascii'); header.write('00', 263, 2, 'ascii');
    const checksum = [...header].reduce((total, value) => total + value, 0);
    header.write(checksum.toString(8).padStart(6, '0') + '\0 ', 148, 8, 'ascii');
    records.push(header, data, Buffer.alloc((512 - data.length % 512) % 512));
  }
  return Buffer.concat([...records, Buffer.alloc(1024)]);
}
function fixtureArchive(files) { return gzipSync(fixtureTar(files)); }
function patchHeader(tar, patch) {
  const result = Buffer.from(tar); patch(result.subarray(0, 512)); result.fill(32, 148, 156);
  const checksum = [...result.subarray(0, 512)].reduce((total, value) => total + value, 0);
  result.write(checksum.toString(8).padStart(6, '0') + '\0 ', 148, 8, 'ascii'); return result;
}
function snapshot(root, relative = '') {
  const records = [];
  for (const name of fs.readdirSync(path.join(root, relative)).sort()) {
    const file = relative ? `${relative}/${name}` : name, absolute = path.join(root, file), stat = fs.lstatSync(absolute);
    if (stat.isSymbolicLink()) records.push([file, `symlink:${fs.readlinkSync(absolute)}`, stat.mode & 0o777]);
    else if (stat.isDirectory()) { records.push([`${file}/`, 'directory', stat.mode & 0o777]); records.push(...snapshot(root, file)); }
    else records.push([file, sha(fs.readFileSync(absolute)), stat.mode & 0o777]);
  }
  return records.sort((a, b) => a[0].localeCompare(b[0]));
}
export function selfTest() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'roedu-kit-fixture-'));
  const checks = [];
  try {
    const fixtureRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../testdata/kit-consumer');
    fs.cpSync(fixtureRoot, root, { recursive: true });
    const config = JSON.parse(fs.readFileSync(path.join(root, 'consumer-config.json'), 'utf8'));
    const tag = 'core-v1.0', image = 'roedu-toolchain:fixture-core-v1.0', imageID = `sha256:${'1'.repeat(64)}`;
    const coreLock = { schema: 2, resolved: '2026-10-06', policy: { kit_sync_merge: 'fixture of PROGRAM9-8' }, tools: [
      { tool: 'preact', kind: 'npm', scope: 'core', version: '11.0.0' },
      { tool: 'docker', kind: 'apt', scope: 'environment', version: '29.0.0' },
      { tool: 'vite', kind: 'npm', scope: 'core', version: '8.0.0' },
      { tool: 'shared-app', kind: 'npm', scope: 'app', apps: ['fixture_consumer'], version: '2.0.0' },
      { tool: 'other-app', kind: 'npm', scope: 'app', apps: ['other_consumer'], version: '3.0.0' },
    ], toolchain_image: { version: image, image_id: imageID } };
    const appLock = { schema: 2, resolved: '2026-10-07', tools: [
      { tool: 'preact', kind: 'npm', scope: 'core', version: '10.0.0' },
      { tool: 'shared-app', kind: 'npm', scope: 'app', apps: ['fixture_consumer'], version: '2.0.0', approved_by: 'synthetic fixture metadata' },
      { tool: 'app-only', kind: 'npm', scope: 'app', version: '4.0.0' },
      { tool: 'obsolete-core', kind: 'npm', scope: 'core', version: '1.0.0' },
      { tool: 'obsolete-host', kind: 'apt', scope: 'environment', version: '1.0.0' },
    ], toolchain_image: { version: image, image_id: imageID } };
    const uiManifest = { name: '@roedu/ui', version: '1.0.0', type: 'module', exports: { '.': './dist/index.js' } };
    const kitManifest = { name: '@roedu/web-kit', version: '0.1.0', type: 'module' };
    const envTemplate = `TOOLCHAIN_IMAGE=${image}\nTOOLCHAIN_DIGEST=${imageID}\nPG_MAJOR=16\n`;
    const npmKitFiles = new Map([
      ['package/package.json', json(kitManifest)], ['package/versions.lock.json', json(coreLock)], ['package/scripts/kit-sync.mjs', Buffer.from('// synthetic fixture launcher\n')],
      ['package/templates/gate.sh', Buffer.from('#!/usr/bin/env bash\n# synthetic fixture wrapper\n')], ['package/templates/compose.gate.yml', Buffer.from('services: {}\n')],
      ['package/templates/Taskfile.yml', Buffer.from('version: 3\n')], ['package/templates/Dockerfile.toolchain', Buffer.from('FROM fixture\n')], ['package/templates/.gate.env', Buffer.from(envTemplate)],
      ['package/templates/Taskfile.repo.yml', Buffer.from('must never overwrite\n')], ['package/templates/ci.yml', Buffer.from('must never install\n')], ['package/templates/.codex/config.toml', Buffer.from('must never install\n')],
      ['package/testdata/kit-consumer/consumer-config.json', fs.readFileSync(path.join(fixtureRoot, 'consumer-config.json'))],
      ['package/testdata/npm-consumer/consumer.tsx', fs.readFileSync(path.join(fixtureRoot, '../npm-consumer/consumer.tsx'))],
    ]);
    const sourceFiles = new Map([['web-kit/go.mod', Buffer.from(`module "${MODULE}"\n\ngo 1.27.1\n`)], ['web-kit/tokens/tokens.go', Buffer.from('package tokens\nconst Fixture = "fixture"\n')], ['web-kit/sample/embedfs/dist/.keep', Buffer.from('approved Go embed layout\n')]]);
    const archiveNames = ['roedu-ui-1.0.0.tgz', 'roedu-web-kit-0.1.0.tgz', `web-kit-go-${tag}.tgz`];
    const makeKit = (extraNpm, extraGo) => {
      npmKitFiles.set('package/versions.lock.json', json(coreLock));
      const kitDirectory = path.join(root, 'kit'); fs.mkdirSync(kitDirectory, { recursive: true });
      const ui = fixtureArchive(new Map([['package/package.json', json(uiManifest)], ['package/dist/index.js', Buffer.from('export const fixture = true;\n')]]));
      const npm = fixtureArchive(new Map([...npmKitFiles, ...(extraNpm ?? [])]));
      const go = fixtureArchive(new Map([...sourceFiles, ...(extraGo ?? [])]));
      fs.writeFileSync(path.join(kitDirectory, 'CORE_TAG'), tag + '\n');
      for (const [index, data] of [ui, npm, go].entries()) fs.writeFileSync(path.join(kitDirectory, archiveNames[index]), data);
      fs.writeFileSync(path.join(kitDirectory, 'SHA256SUMS'), [ui, npm, go].map((data, index) => `${sha(data)}  ${archiveNames[index]}\n`).join(''));
    };
    fs.mkdirSync(path.join(root, 'frontend/vendor'), { recursive: true });
    fs.writeFileSync(path.join(root, 'frontend/vendor/roedu-ui-0.3.0.tgz'), 'old synthetic archive');
    fs.writeFileSync(path.join(root, 'frontend/vendor/unrelated.txt'), 'preserve');
    const originalSourceEnv = `# keep this exact comment\r\nTOOLCHAIN_IMAGE=old-fixture\r\nTOOLCHAIN_DIGEST=sha256:${'0'.repeat(64)}\r\nPG_MAJOR=16\r\nPG_SCRATCH_ROOT=/fixture/keep\r\n`;
    fs.writeFileSync(path.join(root, '.gate.env'), originalSourceEnv);
    fs.writeFileSync(path.join(root, 'versions.lock.json'), json(appLock));
    fs.writeFileSync(path.join(root, 'Taskfile.repo.yml'), 'original fixture repo task\n');
    fs.mkdirSync(path.join(root, '.codex')); fs.writeFileSync(path.join(root, '.codex/config.toml'), 'original fixture config\n');
    makeKit();
    checked(checks, 'fixture-canonical-bundle-private-parity', () => {
      function legacyLoadKitForBundleParity(root) {
        root = fs.realpathSync(root);
        const kitDir = noLinks(root, 'kit');
        const names = fs.readdirSync(kitDir).sort();
        for (const name of names) { safePath(name); const stat = fs.lstatSync(path.join(kitDir, name)); if (!stat.isFile() || stat.isSymbolicLink()) fail(`Invalid kit input: ${name}`); }
        const tagText = fs.readFileSync(noLinks(root, 'kit/CORE_TAG'), 'utf8');
        if (!/^core-v1\.\d+\n?$/.test(tagText)) fail('Malformed committed CORE_TAG');
        const tag = tagText.trim(), goName = `web-kit-go-${tag}.tgz`;
        const uiName = names.find(name => /^roedu-ui-\d+\.\d+\.\d+\.tgz$/.test(name));
        const kitName = names.find(name => /^roedu-web-kit-\d+\.\d+\.\d+\.tgz$/.test(name));
        const expected = ['CORE_TAG', 'SHA256SUMS', uiName, kitName, goName];
        if (!uiName || !kitName || names.length !== expected.length || names.some(name => !expected.includes(name))) fail('Kit must contain exactly CORE_TAG, SHA256SUMS and the three archives');
        const sums = new Map();
        for (const line of fs.readFileSync(noLinks(root, 'kit/SHA256SUMS'), 'utf8').split('\n').filter(Boolean)) {
          const match = /^([a-f0-9]{64}) [ *]([^/\\\s]+)$/.exec(line);
          if (!match || sums.has(match[2]) || ![uiName, kitName, goName].includes(match[2])) fail('Malformed/duplicate/unknown SHA256SUMS entry');
          sums.set(match[2], match[1]);
        }
        if (sums.size !== 3) fail('All three archive hashes required');
        const archives = new Map();
        for (const name of [uiName, kitName, goName]) {
          const data = fs.readFileSync(noLinks(root, `kit/${name}`)); if (sha(data) !== sums.get(name)) fail(`Archive hash mismatch: ${name}`); archives.set(name, data);
        }
        const ui = npmArchive(archives.get(uiName), '@roedu/ui', uiName), npm = npmArchive(archives.get(kitName), '@roedu/web-kit', kitName);
        const coreLock = JSON.parse(archiveFile(npm.entries, 'package/versions.lock.json').data.toString('utf8'));
        if (coreLock.core_tag !== undefined && coreLock.core_tag !== tag) fail('Npm lock core_tag differs from committed CORE_TAG');
        const source = goArchive(archives.get(goName));
        const templates = new Map();
        for (const file of GATE_FILES) templates.set(file, archiveFile(npm.entries, `package/templates/${file === 'scripts/gate.sh' ? 'gate.sh' : file}`));
        const environment = archiveFile(npm.entries, 'package/templates/.gate.env').data.toString('utf8');
        return { tag, ui, npm, source, templates, environment, coreLock, sums };
      }
      // SYNTHETIC NON-RELEASE fixture bytes only; no runtime/qualification claim.
      const beforeRoot = snapshot(root);
      const files = new Map(fs.readdirSync(path.join(root, 'kit')).sort().map(name => [name, fs.readFileSync(noLinks(root, `kit/${name}`))]));
      const clone = () => new Map([...files].map(([name, bytes]) => [name, Buffer.from(bytes)]));
      const readCalls = [];
      const admit = (input, names = [...input.keys()].sort()) => {
        readCalls.length = 0;
        return admitCanonicalKitBundle(names, name => { readCalls.push(name); return input.get(name); });
      };
      const resign = input => {
        input.set('SHA256SUMS', Buffer.from(archiveNames.map(name => `${sha(input.get(name))}  ${name}\n`).join('')));
        return input;
      };
      const replaceArchive = (name, bytes) => resign(new Map([...clone(), [name, bytes]]));
      const parsed = admit(files), legacy = legacyLoadKitForBundleParity(root);
      assert.deepEqual(parsed, legacy);
      assert.deepEqual(loadKit(root), legacy);
      assert.deepEqual(Object.keys(parsed), ['tag', 'ui', 'npm', 'source', 'templates', 'environment', 'coreLock', 'sums']);
      assert.deepEqual([...parsed.templates.keys()], GATE_FILES);
      assert.deepEqual(parsed.environment, envTemplate);
      assert.deepEqual(readCalls, ['CORE_TAG', 'SHA256SUMS', ...archiveNames]);
      assert.equal(parsed.tag, tag);
      assert.equal(parsed.ui.manifest.name, '@roedu/ui');
      assert.equal(parsed.npm.manifest.name, '@roedu/web-kit');
      assert.deepEqual(parsed.source.get('tokens/tokens.go').data, sourceFiles.get('web-kit/tokens/tokens.go'));
      assert.equal(parsed.sums.size, 3);
      const noLF = clone(); noLF.set('CORE_TAG', Buffer.from(tag)); assert.equal(admit(noLF).tag, tag);
      const paddedTag = 'core-v1.00', paddedGo = `web-kit-go-${paddedTag}.tgz`, padded = clone();
      padded.set('CORE_TAG', Buffer.from(paddedTag)); padded.set(paddedGo, padded.get(archiveNames[2])); padded.delete(archiveNames[2]);
      padded.set('SHA256SUMS', Buffer.from([...padded].filter(([name]) => name.endsWith('.tgz')).map(([name, bytes]) => `${sha(bytes)}  ${name}\n`).join('')));
      assert.equal(admit(padded).tag, paddedTag); // Exact current decimal family, no new normalization.
      for (const invalidTag of ['core-v2.0', 'core-v1.0-rc1', ' core-v1.0', 'core-v1.0\r\n']) {
        const input = clone(); input.set('CORE_TAG', Buffer.from(invalidTag)); assert.throws(() => admit(input), /Malformed committed CORE_TAG/);
        assert.deepEqual(readCalls, ['CORE_TAG']);
      }
      for (const missing of ['SHA256SUMS', ...archiveNames]) {
        const input = clone(); input.delete(missing); assert.throws(() => admit(input), /exactly CORE_TAG, SHA256SUMS and the three archives/);
        assert.deepEqual(readCalls, ['CORE_TAG']);
      }
      const extra = clone(); extra.set('unexpected.txt', Buffer.from('must never be read'));
      assert.throws(() => admit(extra), /exactly CORE_TAG, SHA256SUMS and the three archives/); assert.deepEqual(readCalls, ['CORE_TAG']);
      const wrongGoName = clone(); wrongGoName.set('web-kit-go-core-v2.0.tgz', wrongGoName.get(archiveNames[2])); wrongGoName.delete(archiveNames[2]);
      assert.throws(() => admit(wrongGoName), /exactly CORE_TAG, SHA256SUMS and the three archives/);
      assert.throws(() => admit(files, [...files.keys(), 'CORE_TAG']), /Canonical kit names\/raw reader required/); assert.deepEqual(readCalls, []);
      for (const unsafe of ['../outside', '/outside', 'nested/file', 'unsafe\\file']) {
        const input = clone(); input.set(unsafe, Buffer.from('inert'));
        assert.throws(() => admit(input)); assert.ok(!readCalls.includes(unsafe));
      }
      const missingTag = clone(); missingTag.delete('CORE_TAG'); assert.throws(() => admit(missingTag), /Actual kit bytes required: CORE_TAG/);
      const metadata = clone(); metadata.set(archiveNames[0], { data: files.get(archiveNames[0]), sha256: sha(files.get(archiveNames[0])) });
      assert.throws(() => admit(metadata), /Actual kit bytes required/);
      const stringTag = clone(); stringTag.set('CORE_TAG', tag); assert.throws(() => admit(stringTag), /Actual kit bytes required/);
      const sumLines = files.get('SHA256SUMS').toString('utf8').trimEnd().split('\n');
      for (const badSums of [sumLines.slice(0, 2).join('\n'), [...sumLines, sumLines[0]].join('\n'), [...sumLines, `${'0'.repeat(64)}  unknown.tgz`].join('\n'), `not-a-checksum\n`, sumLines.join('\r\n')]) {
        const input = clone(); input.set('SHA256SUMS', Buffer.from(badSums)); assert.throws(() => admit(input));
        assert.deepEqual(readCalls, ['CORE_TAG', 'SHA256SUMS']);
      }
      const binaryMarker = clone(); binaryMarker.set('SHA256SUMS', Buffer.from(sumLines.map(line => line.replace('  ', ' *')).join('\n') + '\n'));
      assert.equal(admit(binaryMarker).sums.size, 3);
      const blankLines = clone(); blankLines.set('SHA256SUMS', Buffer.from('\n' + sumLines.join('\n\n') + '\n'));
      assert.equal(admit(blankLines).sums.size, 3);
      for (const name of archiveNames) {
        const input = clone(), bytes = input.get(name); bytes[bytes.length - 1] ^= 1;
        assert.throws(() => admit(input), /Archive hash mismatch/);
      }
      assert.throws(() => admit(replaceArchive(archiveNames[0], Buffer.from('not a gzip archive'))));
      assert.deepEqual(readCalls, ['CORE_TAG', 'SHA256SUMS', ...archiveNames]); // All hashes checked before parser admission.
      const wrongUi = new Map([['package/package.json', json({ ...uiManifest, name: '@wrong/ui' })], ['package/dist/index.js', Buffer.from('inert')]]);
      assert.throws(() => admit(replaceArchive(archiveNames[0], fixtureArchive(wrongUi))), /Npm name\/version mismatch/);
      const wrongVersion = new Map([['package/package.json', json({ ...uiManifest, version: '2.0.0' })], ['package/dist/index.js', Buffer.from('inert')]]);
      assert.throws(() => admit(replaceArchive(archiveNames[0], fixtureArchive(wrongVersion))), /Npm archive filename\/version mismatch/);
      const missingUiEntry = new Map([['package/package.json', json(uiManifest)]]);
      assert.throws(() => admit(replaceArchive(archiveNames[0], fixtureArchive(missingUiEntry))), /Archive file required/);
      for (const member of ['package/scripts/kit-sync.mjs', 'package/versions.lock.json', ...GATE_FILES.map(name => `package/templates/${name === 'scripts/gate.sh' ? 'gate.sh' : name}`), 'package/templates/.gate.env']) {
        const payload = new Map(npmKitFiles); payload.delete(member);
        assert.throws(() => admit(replaceArchive(archiveNames[1], fixtureArchive(payload))), /Archive file required/);
      }
      const mismatchedLock = new Map([...npmKitFiles, ['package/versions.lock.json', json({ ...coreLock, core_tag: 'core-v1.1' })]]);
      assert.throws(() => admit(replaceArchive(archiveNames[1], fixtureArchive(mismatchedLock))), /Npm lock core_tag differs/);
      const matchingLock = new Map([...npmKitFiles, ['package/versions.lock.json', json({ ...coreLock, core_tag: tag })]]);
      assert.equal(admit(replaceArchive(archiveNames[1], fixtureArchive(matchingLock))).coreLock.core_tag, tag);
      const wrongModule = new Map([...sourceFiles, ['web-kit/go.mod', Buffer.from('module example.invalid/wrong\n\ngo 1.27.1\n')]]);
      assert.throws(() => admit(replaceArchive(archiveNames[2], fixtureArchive(wrongModule))), /Go archive module mismatch/);
      const npmInGo = new Map([...sourceFiles, ['web-kit/budget/index.mjs', Buffer.from('must not cross Go archive boundary')]]);
      assert.throws(() => admit(replaceArchive(archiveNames[2], fixtureArchive(npmInGo))), /Npm or unregistered budget file/);
      assert.deepEqual(snapshot(root), beforeRoot); // Admission itself never materializes product files.
    });
    checked(checks, 'fixture-private-go-planning-parity-and-refusal', () => {
      // Literal pre-extraction loop oracle; this only collects proposals.
      function originalGoPlanningLoop(root, cfg, kit, writes, replacements) {
  for (const directory of cfg.go_dirs) {
    const prefix = directory === '.' ? '' : `${directory}/`, vendor = `${prefix}third_party/webkit`;
    directoryDestination(root, vendor, true); regularTree(noLinks(root, vendor, true)); replacements.set(vendor, kit.source);
    const goMod = `${prefix}go.mod`, stat = fs.statSync(noLinks(root, goMod));
    writes.set(goMod, { data: Buffer.from(pinGoMod(fs.readFileSync(noLinks(root, goMod), 'utf8'), kit.tag)), mode: stat.mode & 0o777 });
  }
      }
      const sourceBefore = snapshot(root), kit = loadKit(root);
      const sourceEntries = [...kit.source].map(([name, entry]) => [name, entry, entry.data, Buffer.from(entry.data), entry.mode]);
      const planRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'roedu-kit-go-planning-'));
      try {
        fs.cpSync(fixtureRoot, planRoot, { recursive: true });
        const rootMod = path.join(planRoot, 'go.mod'), serverMod = path.join(planRoot, 'server/go.mod');
        const rootBytes = Buffer.from(`module example.invalid/root-consumer\n\ngo 1.27.1\nrequire ${MODULE} v0.0.0-${kit.tag}\nreplace ${MODULE} => ./third_party/webkit\n`);
        fs.writeFileSync(rootMod, rootBytes); fs.chmodSync(rootMod, 0o600); fs.chmodSync(serverMod, 0o640);
        const serverBytes = fs.readFileSync(serverMod), rootMode = fs.statSync(rootMod).mode & 0o777, serverMode = fs.statSync(serverMod).mode & 0o777;
        const rootVendor = path.join(planRoot, 'third_party/webkit'), serverVendor = path.join(planRoot, 'server/third_party/webkit');
        for (const directory of [rootVendor, serverVendor]) { fs.mkdirSync(directory, { recursive: true }); fs.writeFileSync(path.join(directory, 'existing.go'), 'package existing\n'); }
        const cfg = validateConfig(planRoot, { ...config, go_dirs: ['.', 'server'] }), reversed = validateConfig(planRoot, { ...config, go_dirs: ['server', '.'] });
        const cfgBefore = [...cfg.go_dirs], reversedBefore = [...reversed.go_dirs];
        const sentinel = { data: Buffer.from('preserved proposal\n'), mode: 0o601 }, oldModule = { data: Buffer.from('prior proposal\n'), mode: 0o602 }, sentinelTree = new Map([['canary.go', sentinel]]);
        const retainedEntries = [sentinel, oldModule].map(entry => [entry, entry.data, Buffer.from(entry.data), entry.mode]), retainedTreeKeys = [...sentinelTree.keys()];
        const assertRetained = () => {
          for (const [entry, data, bytes, mode] of retainedEntries) { assert.equal(entry.data, data); assert.deepEqual(entry.data, bytes); assert.equal(entry.mode, mode); }
          assert.deepEqual([...sentinelTree.keys()], retainedTreeKeys); assert.equal(sentinelTree.get('canary.go'), sentinel);
        };
        const seeded = () => ({ writes: new Map([['server/go.mod', oldModule], ['unrelated.txt', sentinel]]), replacements: new Map([['third_party/webkit', sentinelTree], ['unrelated-tree', sentinelTree]]) });
        const compare = (selected, refusal, seed = seeded) => {
          const original = seed(), projected = seed(), before = snapshot(planRoot);
          let originalError, projectedError;
          try { originalGoPlanningLoop(planRoot, selected, kit, original.writes, original.replacements); } catch (error) { originalError = error; }
          assertRetained();
          assert.deepEqual(snapshot(planRoot), before);
          try { planGoDependencies(planRoot, selected.go_dirs, kit, projected.writes, projected.replacements); } catch (error) { projectedError = error; }
          assertRetained();
          assert.deepEqual(snapshot(planRoot), before);
          if (refusal) {
            assert.ok(originalError instanceof Error); assert.ok(projectedError instanceof Error);
            assert.match(originalError.message, refusal); assert.equal(projectedError.constructor, originalError.constructor);
            assert.equal(projectedError.code, originalError.code); assert.equal(projectedError.message, originalError.message);
          } else { assert.equal(originalError, undefined); assert.equal(projectedError, undefined); }
          assert.deepEqual([...projected.writes.keys()], [...original.writes.keys()]);
          for (const [name, entry] of original.writes) {
            const actual = projected.writes.get(name); assert.ok(Buffer.isBuffer(actual.data)); assert.deepEqual(actual.data, entry.data); assert.equal(actual.mode, entry.mode);
          }
          assert.deepEqual([...projected.replacements.keys()], [...original.replacements.keys()]);
          for (const [name, tree] of original.replacements) assert.equal(projected.replacements.get(name), tree);
          assert.equal(projected.writes.get('unrelated.txt'), sentinel); assert.equal(projected.replacements.get('unrelated-tree'), sentinelTree);
          assert.deepEqual(cfg.go_dirs, cfgBefore); assert.deepEqual(reversed.go_dirs, reversedBefore);
          assert.deepEqual([...kit.source.keys()], sourceEntries.map(([name]) => name));
          for (const [name, entry, data, bytes, mode] of sourceEntries) { assert.equal(kit.source.get(name), entry); assert.equal(entry.data, data); assert.deepEqual(entry.data, bytes); assert.equal(entry.mode, mode); }
          assert.deepEqual(snapshot(root), sourceBefore);
          return projected;
        };
        for (const selected of [cfg, reversed]) {
          const projected = compare(selected);
          assert.deepEqual([...projected.writes.keys()], ['server/go.mod', 'unrelated.txt', 'go.mod']);
          assert.deepEqual([...projected.replacements.keys()], ['third_party/webkit', 'unrelated-tree', 'server/third_party/webkit']);
          assert.equal(projected.replacements.get('third_party/webkit'), kit.source); assert.equal(projected.replacements.get('server/third_party/webkit'), kit.source);
          assert.deepEqual(projected.writes.get('go.mod').data, rootBytes); assert.equal(projected.writes.get('go.mod').mode, rootMode);
          assert.deepEqual(projected.writes.get('server/go.mod').data, Buffer.from(serverBytes.toString('utf8').trimEnd() + `\n\nrequire ${MODULE} v0.0.0-${kit.tag}\nreplace ${MODULE} => ./third_party/webkit\n`));
          assert.equal(projected.writes.get('server/go.mod').mode, serverMode);
          const ordered = compare(selected, undefined, () => ({ writes: new Map([['unrelated.txt', sentinel]]), replacements: new Map([['unrelated-tree', sentinelTree]]) }));
          assert.deepEqual([...ordered.writes.keys()], ['unrelated.txt', ...selected.go_dirs.map(directory => directory === '.' ? 'go.mod' : `${directory}/go.mod`)]);
          assert.deepEqual([...ordered.replacements.keys()], ['unrelated-tree', ...selected.go_dirs.map(directory => directory === '.' ? 'third_party/webkit' : `${directory}/third_party/webkit`)]);
        }
        fs.rmSync(serverVendor, { recursive: true }); fs.writeFileSync(serverVendor, 'blocked directory\n');
        const blocked = compare(cfg, /Directory destination required/);
        assert.equal(blocked.replacements.has('server/third_party/webkit'), false); assert.equal(blocked.writes.get('server/go.mod'), oldModule); assert.deepEqual(blocked.writes.get('go.mod').data, rootBytes);
        fs.unlinkSync(serverVendor); fs.mkdirSync(serverVendor); fs.writeFileSync(path.join(serverVendor, 'existing.go'), 'package existing\n');
        const link = path.join(serverVendor, 'linked'); fs.symlinkSync('../..', link, 'dir');
        const linked = compare(cfg, /Nonregular tree entry/);
        assert.equal(linked.replacements.has('server/third_party/webkit'), false); assert.equal(linked.writes.get('server/go.mod'), oldModule); fs.unlinkSync(link);
        fs.unlinkSync(serverMod);
        const missing = compare(cfg, /Missing input: server\/go\.mod/);
        assert.equal(missing.replacements.get('server/third_party/webkit'), kit.source); assert.equal(missing.writes.get('server/go.mod'), oldModule);
        fs.writeFileSync(serverMod, serverBytes); fs.chmodSync(serverMod, serverMode);
        fs.writeFileSync(serverMod, `module example.invalid/duplicate-consumer\nrequire ${MODULE} v0.0.0-old\nrequire ${MODULE} v0.0.0-other\n`);
        const duplicate = compare(cfg, /Duplicate web-kit Go require\/replace/);
        assert.equal(duplicate.replacements.get('server/third_party/webkit'), kit.source); assert.equal(duplicate.writes.get('server/go.mod'), oldModule);
        fs.writeFileSync(serverMod, serverBytes); fs.chmodSync(serverMod, serverMode);
        compare(cfg); assert.deepEqual(snapshot(root), sourceBefore);
      } finally { fs.rmSync(planRoot, { recursive: true, force: true }); }
    });
    let deps = 0;
    const depsRunner = (_directory, target) => { assert.equal(target, 'deps'); deps++; return { status: 0, stdout: '', stderr: '' }; };
    checked(checks, 'fixture-sync', () => {
      const result = syncKit(root, config, { depsRunner }); assert.equal(result.status, 'pass'); assert.ok(result.changed.length > 0); assert.equal(deps, 1);
      assert.equal(fs.existsSync(path.join(root, 'frontend/vendor/roedu-ui-0.3.0.tgz')), false); assert.equal(fs.readFileSync(path.join(root, 'frontend/vendor/unrelated.txt'), 'utf8'), 'preserve');
      assert.equal(fs.readFileSync(path.join(root, 'Taskfile.repo.yml'), 'utf8'), 'original fixture repo task\n'); assert.equal(fs.readFileSync(path.join(root, '.codex/config.toml'), 'utf8'), 'original fixture config\n'); assert.equal(fs.existsSync(path.join(root, 'ci.yml')), false);
      assert.equal(fs.readFileSync(path.join(root, '.gate.env'), 'utf8'), envTemplate);
      const installed = JSON.parse(fs.readFileSync(path.join(root, 'frontend/package.json'), 'utf8'));
      assert.equal(installed.dependencies.preact, '11.0.0'); assert.equal(installed.devDependencies.vite, '8.0.0'); assert.equal(installed.dependencies['fixture-app-only'], '^1.2.3');
      assert.ok(!Object.hasOwn(installed.dependencies, 'shared-app')); assert.equal(result.manifest_changes.length, 2);
    });
    checked(checks, 'fixture-idempotence', () => { const before = snapshot(root); const result = syncKit(root, config, { depsRunner }); assert.deepEqual(result.changed, []); assert.deepEqual(snapshot(root), before); assert.equal(deps, 2); });
    checked(checks, 'fixture-readonly-check', () => { const before = snapshot(root); assert.equal(checkKit(root, config).status, 'pass'); assert.deepEqual(snapshot(root), before); });
    checked(checks, 'fixture-merge', () => {
      const appBefore = structuredClone(appLock), coreBefore = structuredClone(coreLock), merged = mergeVersions(appLock, coreLock, tag, config.app);
      assert.deepEqual(appLock, appBefore); assert.deepEqual(coreLock, coreBefore); assert.equal(merged.core_tag, tag); assert.equal(merged.resolved, '2026-10-07');
      assert.deepEqual(merged.tools.find(entry => entry.tool === 'shared-app'), appLock.tools[1]); assert.ok(merged.tools.some(entry => entry.tool === 'app-only')); assert.ok(!merged.tools.some(entry => entry.tool === 'other-app'));
      assert.ok(!merged.tools.some(entry => ['obsolete-core', 'obsolete-host'].includes(entry.tool)));
      const higher = structuredClone(appLock); higher.tools[0].version = '12.0.0'; assert.throws(() => mergeVersions(higher, coreLock, tag, config.app), /Higher core/);
      const higherApp = structuredClone(appLock); higherApp.tools[1].version = '3.0.0'; assert.equal(mergeVersions(higherApp, coreLock, tag, config.app).tools.find(entry => entry.tool === 'shared-app').version, '3.0.0');
      const lowerApp = structuredClone(appLock); lowerApp.tools[1].version = '1.0.0'; assert.equal(mergeVersions(lowerApp, coreLock, tag, config.app).tools.find(entry => entry.tool === 'shared-app').version, '2.0.0');
    });
    checked(checks, 'fixture-source-environment-roundtrip', () => {
      const expectedSource = mergeEnvironment(originalSourceEnv, envTemplate, coreLock);
      assert.equal(expectedSource.replace(/^TOOLCHAIN_(?:IMAGE|DIGEST)=[^\r\n]*/gm, ''), '# keep this exact comment\r\n\r\n\r\nPG_MAJOR=16\r\nPG_SCRATCH_ROOT=/fixture/keep\r\n');
      fs.writeFileSync(path.join(root, '.gate.env'), expectedSource);
      const before = snapshot(root); assert.equal(checkKit(root, config).status, 'pass'); assert.deepEqual(snapshot(root), before);
      syncKit(root, config, { depsRunner }); assert.equal(fs.readFileSync(path.join(root, '.gate.env'), 'utf8'), envTemplate);
      // This models the wrapper's approved source sync-back from the runner's full template.
      fs.writeFileSync(path.join(root, '.gate.env'), mergeEnvironment(expectedSource, fs.readFileSync(path.join(root, '.gate.env'), 'utf8'), coreLock));
      assert.deepEqual(snapshot(root), before);
    });
    checked(checks, 'fixture-default-task-deps-route', () => {
      const bin = path.join(root, 'fixture-bin'), witness = path.join(root, 'task-witness.json'); fs.mkdirSync(bin);
      const executable = path.join(bin, 'task');
      fs.writeFileSync(executable, `#!${process.execPath}\nconst fs=require('node:fs');fs.writeFileSync(${JSON.stringify(witness)},JSON.stringify(process.argv.slice(2)));\n`, { mode: 0o755 });
      const previousPath = process.env.PATH;
      try { process.env.PATH = `${bin}${path.delimiter}${previousPath}`; syncKit(root, config); }
      finally { process.env.PATH = previousPath; }
      assert.deepEqual(JSON.parse(fs.readFileSync(witness, 'utf8')), ['--silent', 'deps']);
    });
    checked(checks, 'fixture-directory-destinations-before-write', () => {
      const gate = path.join(root, 'scripts/gate.sh'), original = fs.readFileSync(gate), mode = fs.statSync(gate).mode & 0o777;
      fs.unlinkSync(gate); fs.mkdirSync(gate);
      const before = snapshot(root), previousDeps = deps;
      assert.throws(() => syncKit(root, config, { depsRunner }), /File destination must be regular/);
      assert.deepEqual(snapshot(root), before); assert.equal(deps, previousDeps); fs.rmdirSync(gate); fs.writeFileSync(gate, original, { mode });
      const old = path.join(root, 'frontend/vendor/roedu-ui-0.0.0.tgz'); fs.mkdirSync(old); const beforeOld = snapshot(root);
      assert.throws(() => syncKit(root, config, { depsRunner }), /File destination must be regular/); assert.deepEqual(snapshot(root), beforeOld); fs.rmdirSync(old);
      const goFile = path.join(root, 'server/third_party/webkit/tokens/tokens.go'), goOriginal = fs.readFileSync(goFile); fs.unlinkSync(goFile); fs.mkdirSync(goFile); const beforeGo = snapshot(root);
      assert.throws(() => syncKit(root, config, { depsRunner }), /File destination must be regular/); assert.deepEqual(snapshot(root), beforeGo); fs.rmdirSync(goFile); fs.writeFileSync(goFile, goOriginal);
    });
    checked(checks, 'fixture-quoted-go-paths-and-discovery', () => {
      const quoted = `module "example.invalid/kit-consumer"\n\ngo 1.27.1\nrequire (\n "${MODULE}" "v0.0.0-core-v0.1" // old pin\n example.invalid/preserved "v1.2.3"\n)\nreplace (\n "${MODULE}" "v0.0.0-core-v0.1" => "./older-webkit"\n example.invalid/preserved => "./local"\n)\n`;
      const rewritten = pinGoMod(quoted, tag), selected = goPins(rewritten);
      assert.equal(selected.require, `v0.0.0-${tag}`); assert.equal(selected.replace.target, './third_party/webkit'); assert.equal(selected.records.filter(record => record.kind === 'require').length, 1); assert.equal(selected.records.filter(record => record.kind === 'replace').length, 1);
      assert.ok(rewritten.includes('example.invalid/preserved "v1.2.3"')); assert.equal(pinGoMod(rewritten, tag), rewritten);
      const rawQuote = String.fromCharCode(96), escapedModule = MODULE.replace('/', String.fromCharCode(92) + 'x2f');
      const rawModule = `module ${rawQuote}example.invalid/raw${rawQuote}\nrequire ${rawQuote}${MODULE}${rawQuote} ${rawQuote}v0.0.0-${tag}${rawQuote}\nreplace ${rawQuote}${MODULE}${rawQuote} => ${rawQuote}./third_party/webkit${rawQuote}\n`;
      assert.equal(pinGoMod(rawModule, tag), rawModule);
      const escaped = `module "example.invalid/escaped"\nrequire "${escapedModule}" v0.0.0-${tag}\nreplace "${escapedModule}" => "./third_party/webkit"\n`;
      assert.equal(pinGoMod(escaped, tag), escaped);
      const goFile = path.join(root, 'server/go.mod'), original = fs.readFileSync(goFile); fs.writeFileSync(goFile, quoted);
      const { go_dirs: _omit, ...discoveryConfig } = config;
      assert.deepEqual(validateConfig(root, discoveryConfig).go_dirs, ['server']);
      const nested = path.join(root, 'server/sample'); fs.mkdirSync(nested); fs.writeFileSync(path.join(nested, 'go.mod'), quoted);
      assert.deepEqual(validateConfig(root, discoveryConfig).go_dirs, ['server']); fs.rmSync(nested, { recursive: true });
      const linkTarget = path.join(root, 'link-target.mod'); fs.writeFileSync(linkTarget, quoted); fs.unlinkSync(goFile); fs.symlinkSync(linkTarget, goFile); const before = snapshot(root);
      assert.throws(() => syncKit(root, discoveryConfig, { depsRunner }), /Nonregular destination/); assert.deepEqual(snapshot(root), before);
      fs.unlinkSync(goFile); fs.writeFileSync(goFile, original); fs.unlinkSync(linkTarget);
    });
    checked(checks, 'fixture-core-npm-alignment-and-runtime-refusal', () => {
      const manifest = JSON.parse(fs.readFileSync(path.join(root, 'frontend/package.json'), 'utf8'));
      const higher = structuredClone(manifest); higher.dependencies.preact = '12.0.0'; assert.throws(() => alignCoreNpm(higher, coreLock), /Higher core npm manifest/);
      const local = structuredClone(manifest); local.dependencies.preact = 'file:local-preact.tgz'; assert.throws(() => alignCoreNpm(local, coreLock), /Unsupported core npm declaration/);
      const packageFile = path.join(root, 'frontend/package.json'), original = fs.readFileSync(packageFile); fs.writeFileSync(packageFile, json(higher)); const beforeHigher = snapshot(root);
      assert.throws(() => syncKit(root, config, { depsRunner }), /Higher core npm manifest/); assert.deepEqual(snapshot(root), beforeHigher); fs.writeFileSync(packageFile, original);
      coreLock.tools.push({ tool: 'node', kind: 'runtime', scope: 'core', version: '999.0.0' }); makeKit(); const beforeFuture = snapshot(root), previousDeps = deps;
      assert.throws(() => syncKit(root, config, { depsRunner }), /KIT_SYNC_RUNTIME_TOO_OLD node required=999\.0\.0 executing=/); assert.deepEqual(snapshot(root), beforeFuture); assert.equal(deps, previousDeps);
      coreLock.tools.pop(); makeKit();
      assert.throws(() => assertRuntimeCompatible({ tools: [{ tool: 'go', kind: 'runtime', scope: 'core', version: '1.28.0' }] }, { go: '1.27.1' }), /KIT_SYNC_RUNTIME_TOO_OLD go/);
    });
    checked(checks, 'fixture-producer-tag-authority', () => {
      assert.equal(coreLock.core_tag, undefined); assert.equal(checkKit(root, config).tag, tag);
      coreLock.core_tag = 'core-v1.999'; makeKit(); const before = snapshot(root);
      assert.throws(() => syncKit(root, config, { depsRunner }), /core_tag differs/); assert.deepEqual(snapshot(root), before);
      delete coreLock.core_tag; makeKit(); assert.equal(checkKit(root, config).status, 'pass');
    });
    checked(checks, 'fixture-corruption-before-write', () => {
      const archive = path.join(root, 'kit', archiveNames[0]), original = fs.readFileSync(archive), corrupted = Buffer.from(original); corrupted[corrupted.length - 1] ^= 1; fs.writeFileSync(archive, corrupted);
      const before = snapshot(root); assert.throws(() => syncKit(root, config, { depsRunner }), /hash mismatch/); assert.deepEqual(snapshot(root), before); fs.writeFileSync(archive, original);
    });
    checked(checks, 'fixture-npm-testdata-boundary', () => {
      const valid = fixtureArchive(npmKitFiles), parsed = npmArchive(valid, '@roedu/web-kit', archiveNames[1]);
      for (const name of ['package/testdata/kit-consumer/consumer-config.json', 'package/testdata/npm-consumer/consumer.tsx']) assert.deepEqual(parsed.entries.get(name)?.data, npmKitFiles.get(name));
      const uiFiles = new Map([['package/package.json', json(uiManifest)], ['package/dist/index.js', Buffer.from('export const fixture = true;\n')]]);
      assert.equal(npmArchive(fixtureArchive(uiFiles), '@roedu/ui', archiveNames[0]).manifest.name, '@roedu/ui');
      for (const [owner, files, archive, prefix] of [['@roedu/ui', uiFiles, archiveNames[0], 'dist'], ['@roedu/web-kit', npmKitFiles, archiveNames[1], 'testdata']]) {
        for (const suffix of ['tsconfig.tsbuildinfo', 'nested/stale.tsbuildinfo', 'stale.tsbuildinfo.gz', 'stale.tsbuildinfo.br']) assert.throws(() => npmArchive(fixtureArchive(new Map([...files, [`package/${prefix}/${suffix}`, Buffer.from('compiler cache')]])), owner, archive), /Excluded compiler build state/);
      }
      assert.throws(() => npmArchive(fixtureArchive(new Map([...uiFiles, ['package/testdata/fixture.json', Buffer.from('{}')]])), '@roedu/ui', archiveNames[0]), /Unknown npm archive path/);
      assert.throws(() => npmArchive(valid, '@unknown/owner', archiveNames[1]), /Unsupported npm archive owner/);
      for (const name of ['package/testdata-extra/fixture.json', 'package/unknown/fixture.json']) assert.throws(() => npmArchive(fixtureArchive(new Map([...npmKitFiles, [name, Buffer.from('unexpected')]])), '@roedu/web-kit', archiveNames[1]), /Unknown npm archive path/);
      for (const suffix of ['node_modules/fixture/package.json', '.git/config', '.gate/result.json', '.vitest/cache.json', 'test-results/report.json', '.env', '.env.local', 'TASK_RESULT.md']) assert.throws(() => npmArchive(fixtureArchive(new Map([...npmKitFiles, [`package/testdata/${suffix}`, Buffer.from('excluded')]])), '@roedu/web-kit', archiveNames[1]), /Excluded cache\/secret member/);
      const linkTar = fixtureTar(new Map([['package/testdata/link', Buffer.from('')], ...npmKitFiles]));
      for (const type of [49, 50]) assert.throws(() => npmArchive(gzipSync(patchHeader(linkTar, header => { header[156] = type; header.write('outside', 157); })), '@roedu/web-kit', archiveNames[1]), /Unsafe tar entry type/);
      const escaped = patchHeader(linkTar, header => { header.fill(0, 0, 100); header.write('package/testdata/../outside', 0); });
      assert.throws(() => npmArchive(gzipSync(escaped), '@roedu/web-kit', archiveNames[1]), /Unsafe path/);
    });
    checked(checks, 'fixture-unknown-paths-before-write', () => {
      makeKit(new Map([['package/unknown/file.js', Buffer.from('unexpected')]])); const before = snapshot(root); assert.throws(() => syncKit(root, config, { depsRunner }), /Unknown npm archive path/); assert.deepEqual(snapshot(root), before);
      makeKit(undefined, new Map([['web-kit/scripts/unknown.mjs', Buffer.from('unexpected')]])); const beforeGo = snapshot(root); assert.throws(() => syncKit(root, config, { depsRunner }), /Unknown Go archive path/); assert.deepEqual(snapshot(root), beforeGo); makeKit();
    });
    checked(checks, 'fixture-go-budget-source-delivery', () => {
      const sourceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
      const names = ['budget/budget.go', 'budget/budget_test.go', 'budget/schema_cases_test.go', 'budget/testdata/budgets.seed.json', 'budget/testdata/schema-cases.json'];
      const budget = new Map(names.map(name => [`web-kit/${name}`, fs.readFileSync(noLinks(sourceRoot, name))]));
      // Structural fixture envelope; the budget payload is exact current source.
      makeKit(new Map([['package/budget/index.mjs', fs.readFileSync(noLinks(sourceRoot, 'budget/index.mjs'))]]), budget);
      const kit = loadKit(root);
      assert.deepEqual(kit.npm.entries.get('package/budget/index.mjs').data, fs.readFileSync(noLinks(sourceRoot, 'budget/index.mjs')));
      for (const name of names) { assert.deepEqual(kit.source.get(name)?.data, budget.get(`web-kit/${name}`)); assert.equal(kit.source.get(name)?.mode, 0o644); }
      assert.equal(kit.source.has('budget/index.mjs'), false);
      assert.equal(syncKit(root, config, { depsRunner }).status, 'pass');
      for (const name of names) {
        const filename = path.join(root, 'server/third_party/webkit', name);
        assert.deepEqual(fs.readFileSync(filename), budget.get(`web-kit/${name}`)); assert.equal(fs.statSync(filename).mode & 0o777, 0o644);
      }
      assert.equal(fs.existsSync(path.join(root, 'server/third_party/webkit/budget/index.mjs')), false);
      const repeated = snapshot(root); assert.deepEqual(syncKit(root, config, { depsRunner }).changed, []); assert.deepEqual(snapshot(root), repeated);
      const filename = path.join(root, 'server/third_party/webkit/budget/budget.go'), original = fs.readFileSync(filename);
      fs.writeFileSync(filename, 'package changed\n'); assert.throws(() => checkKit(root, config), /Go source drift/); fs.writeFileSync(filename, original);
      fs.unlinkSync(filename); assert.throws(() => checkKit(root, config), /Go source drift/); fs.writeFileSync(filename, original);
      assert.equal(checkKit(root, config).status, 'pass'); makeKit(); syncKit(root, config, { depsRunner });
    });
    checked(checks, 'fixture-go-budget-refusal-before-write', () => {
      for (const name of ['budget/index.mjs', 'budget/package.json', 'budget/package-lock.json', 'budget/nested/extra.go', 'budget/testdata/extra.json', 'budget/testdata/index.mjs', 'budget/other.txt', 'budget-extra/extra.go', 'budget/__pycache__/cache.pyc', 'budget/stale.pyc.gz', 'budget/.git/fixture', 'budget/.env.local', 'budget/TASK_RESULT.md']) {
        makeKit(undefined, new Map([[`web-kit/${name}`, Buffer.from('injected sibling')]]));
        const before = snapshot(root), previousDeps = deps;
        assert.throws(() => loadKit(root), /Go archive path|budget file|Python bytecode\/cache|cache\/secret/);
        assert.throws(() => syncKit(root, config, { depsRunner }), /Go archive path|budget file|Python bytecode\/cache|cache\/secret/);
        assert.deepEqual(snapshot(root), before); assert.equal(deps, previousDeps);
      }
      const reseal = tar => {
        const bytes = gzipSync(tar), file = archiveNames[2]; fs.writeFileSync(path.join(root, 'kit', file), bytes);
        const sums = archiveNames.map(name => `${sha(fs.readFileSync(path.join(root, 'kit', name)))}  ${name}\n`).join('');
        fs.writeFileSync(path.join(root, 'kit/SHA256SUMS'), sums);
      };
      const refusal = (tar, pattern) => {
        makeKit(); reseal(tar); const before = snapshot(root), previousDeps = deps;
        assert.throws(() => loadKit(root), pattern); assert.throws(() => syncKit(root, config, { depsRunner }), pattern);
        assert.deepEqual(snapshot(root), before); assert.equal(deps, previousDeps);
      };
      for (const name of ['budget', 'budget/testdata']) refusal(fixtureTar(new Map([[`web-kit/${name}`, Buffer.alloc(0)]])), /Go package directory required|member type mismatch/);
      for (const name of ['budget/budget.go', 'budget/testdata/schema-cases.json']) {
        const tar = fixtureTar(new Map([[`web-kit/${name}`, Buffer.alloc(0)]]));
        refusal(patchHeader(tar, header => { header[156] = 53; }), /member type mismatch/);
      }
      const directory = name => patchHeader(fixtureTar(new Map([[name, Buffer.alloc(0)]])), header => { header[156] = 53; }).subarray(0, 512);
      makeKit(); const valid = fixtureTar(sourceFiles), directories = Buffer.concat([directory('web-kit/budget'), directory('web-kit/budget/testdata'), valid]);
      reseal(directories); assert.equal(loadKit(root).source.has('go.mod'), true); assert.equal(syncKit(root, config, { depsRunner }).status, 'pass');
      const file = fixtureTar(new Map([['web-kit/budget/budget.go', Buffer.from('package budget\n')]]));
      for (const type of [49, 50]) refusal(patchHeader(file, header => { header[156] = type; header.write('outside', 157); }), /Unsafe tar entry type/);
      refusal(patchHeader(file, header => { header.fill(0, 0, 100); header.write('web-kit/budget/../outside', 0); }), /Unsafe path/);
      refusal(patchHeader(file, header => { header.write('0004644\0', 100); }), /Unsafe tar permissions/);
      refusal(Buffer.concat([file.subarray(0, file.length - 1024), file]), /Duplicate tar path/);
      refusal(fixtureTar(new Map([['web-kit/budget/budget.go', Buffer.alloc(0)], ['web-kit/budget/budget.go/child', Buffer.alloc(0)]])), /Tar ancestor is a file/);
      makeKit();
    });
    checked(checks, 'fixture-python-cache-before-go-write', () => {
      for (const suffix of ['__pycache__/fixture.py', 'nested/__pycache__/fixture.pyc', 'stale.pyc', 'nested/stale.pyo', 'stale.pyc.gz', 'nested/stale.pyo.br']) {
        makeKit(undefined, new Map([[`web-kit/tokens/${suffix}`, Buffer.from('runtime cache')]]));
        const before = snapshot(root), previousDeps = deps;
        assert.throws(() => syncKit(root, config, { depsRunner }), /Excluded Python bytecode\/cache/);
        assert.deepEqual(snapshot(root), before); assert.equal(deps, previousDeps);
      }
      makeKit();
    });
    checked(checks, 'fixture-extra-kit-input', () => {
      const extra = path.join(root, 'kit/extra.txt'); fs.writeFileSync(extra, 'unexpected input'); const before = snapshot(root);
      assert.throws(() => syncKit(root, config, { depsRunner }), /exactly CORE_TAG/); assert.deepEqual(snapshot(root), before); fs.unlinkSync(extra);
    });
    checked(checks, 'fixture-tar-malformation', () => {
      const tar = fixtureTar(new Map([['package/file', Buffer.from('payload')]])); assert.equal(parseTar(tar).get('package/file').data.toString(), 'payload');
      assert.throws(() => parseTar(patchHeader(tar, header => { header.fill(0, 0, 100); header.write('../outside', 0); })), /Unsafe path/);
      assert.throws(() => parseTar(patchHeader(tar, header => { header[156] = 50; header.write('outside', 157); })), /Unsafe tar entry type/);
      assert.throws(() => parseTar(patchHeader(tar, header => { header[156] = 49; header.write('outside', 157); })), /Unsafe tar entry type/);
      const checksum = Buffer.from(tar); checksum[0] ^= 1; assert.throws(() => parseTar(checksum), /checksum mismatch/);
      assert.throws(() => parseTar(tar.subarray(0, tar.length - 512)), /end marker/);
      assert.throws(() => parseTar(fixtureTar([['package/file', Buffer.from('one')], ['package/file', Buffer.from('two')]])), /Duplicate tar path/);
      assert.throws(() => parseTar(patchHeader(tar, header => { header.write('0004755\0', 100, 8, 'ascii'); })), /Unsafe tar permissions/);
      assert.throws(() => parseTar(fixtureTar(new Map([['package/file/child', Buffer.from('one')], ['package/file', Buffer.from('two')]]))), /shadows directory/);
    });
    checked(checks, 'fixture-config-refusal', () => {
      for (const vendor of ['../outside', '/outside', 'kit/vendor', 'frontend\\vendor']) assert.throws(() => validateConfig(root, { ...config, vendor_dir: vendor }), /Unsafe/);
      assert.throws(() => validateConfig(root, { ...config, npm_dir: '../outside' }), /Unsafe path/);
      const before = snapshot(root); assert.throws(() => syncKit(root, { ...config, role: 'core' }, { depsRunner }), /consumer/); assert.deepEqual(snapshot(root), before);
      const target = path.join(root, 'frontend/vendor/linked'); fs.symlinkSync(os.tmpdir(), target); assert.throws(() => checkKit(root, config), /Nonregular tree/); fs.unlinkSync(target);
    });
    checked(checks, 'fixture-frozen-wrapper-config', () => {
      const cfg = validateConfig(root, config), selected = { role: cfg.role, app: cfg.app, npm_dir: safePath(cfg.npm_dir ?? 'frontend/node_modules/@roedu/web-kit'), vendor_dir: cfg.vendor_dir, go_dirs: cfg.go_dirs };
      const frozen = { schema: 1, target: 'kit:sync', sha: 'a'.repeat(40), tree_sha256: 'b'.repeat(64), toolchain_digest: imageID, config: selected, config_sha256: sha(JSON.stringify(selected)) };
      const metadata = path.join(root, '.gate/kit-sync/wrapper-kit-config.json'); fs.mkdirSync(path.dirname(metadata), { recursive: true }); fs.writeFileSync(metadata, json(frozen));
      assert.deepEqual(assertFrozenConfig(root, config), selected);
      assert.throws(() => assertFrozenConfig(root, { ...config, app: 'changed_app' }), /changed from the frozen/);
      frozen.config_sha256 = '0'.repeat(64); fs.writeFileSync(metadata, json(frozen)); assert.throws(() => assertFrozenConfig(root, config), /changed from the frozen/);
      fs.unlinkSync(metadata); assert.throws(() => assertFrozenConfig(root, config, true), /requires the wrapper/);
      assert.equal(fs.readFileSync(path.join(root, 'server/third_party/webkit/sample/embedfs/dist/.keep'), 'utf8'), 'approved Go embed layout\n');
    });
    checked(checks, 'fixture-drift', () => {
      const target = path.join(root, 'server/third_party/webkit/tokens/tokens.go'), original = fs.readFileSync(target); fs.writeFileSync(target, 'package changed\n'); assert.throws(() => checkKit(root, config), /Go source drift/); fs.writeFileSync(target, original);
      const manifest = path.join(root, 'frontend/package.json'), originalManifest = fs.readFileSync(manifest), altered = JSON.parse(originalManifest); altered.dependencies['@roedu/ui'] = '1.0.0'; fs.writeFileSync(manifest, json(altered)); assert.throws(() => checkKit(root, config), /Kit drift/); fs.writeFileSync(manifest, originalManifest);
      assert.equal(checkKit(root, config).status, 'pass');
    });
    return { mode: 'self-test', status: 'pass', checks };
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
}
export function main(argv = process.argv.slice(2)) {
  if (argv.length > 1 || (argv.length === 1 && !['--check', '--self-test'].includes(argv[0]))) fail('Usage: kit-sync.mjs [--check|--self-test]');
  if (argv[0] === '--self-test') return selfTest();
  const root = process.cwd(), config = readConsumerConfig(root);
  return argv[0] === '--check' ? checkKit(root, config) : syncKit(root, assertFrozenConfig(root, config, true));
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { process.stdout.write(JSON.stringify(main()) + '\n'); }
  catch (error) { process.stdout.write(JSON.stringify({ status: 'fail', reason: error.message, checks: error.checks ?? [] }) + '\n'); process.exitCode = 1; }
}
