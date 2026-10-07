// This script runs only through the pinned gate runner. It never edits the
// source module or rewrites fixture references to make isolated tests pass.
import {
  constants, chmodSync, closeSync, fstatSync, lstatSync, mkdirSync, mkdtempSync,
  openSync, readFileSync, readdirSync, realpathSync, rmSync, writeFileSync,
} from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, extname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { isPythonBytecodePath } from './kit-sync.mjs';

const source = resolve(fileURLToPath(new URL('../', import.meta.url)));
const report = {
  schema: 1, check: 'go-distribution', status: 'fail', source_module: source,
  isolation: 'standalone module copy and isolated TMPDIR; no original fixtures injected',
  files: [], excluded: [], fixture_paths: [], commands: [], packages: [], tests: [], skips: [],
};
let scratch;
const hash = data => createHash('sha256').update(data).digest('hex');
const inside = (root, filename) => filename === root || filename.startsWith(root + sep);
const fail = message => { throw new Error(message); };
const npmDirectories = new Set(['node_modules', '.git', '.gate', '.vitest']);
const npmRootDirectories = new Set(['scripts', 'templates', 'schemas', 'docs', '.codex']);
const npmMetadata = new Set(['package.json', 'package-lock.json', 'npm-shrinkwrap.json', '.npmrc', '.nvmrc']);
const npmExtensions = new Set(['.mjs', '.cjs', '.ts', '.tsx', '.jsx']);
const rootFiles = new Set(['go.mod', 'go.sum', 'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING', 'NOTICE']);

// O_NOFOLLOW plus inode checks prevent copying symlinks or following a file
// replaced between inventory and read. Only regular files under source qualify.
function readRegular(filename, allowedRoot = source) {
  if (!inside(allowedRoot, filename)) fail(`outside allowed module: ${filename}`);
  const before = lstatSync(filename);
  if (!before.isFile() || before.isSymbolicLink()) fail(`not a regular source file: ${filename}`);
  if (before.mode & 0o7000) fail(`privileged source permissions: ${filename}`);
  const fd = openSync(filename, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const current = fstatSync(fd);
    if (!current.isFile() || current.ino !== before.ino || current.dev !== before.dev) fail(`source changed during read: ${filename}`);
    return { data: readFileSync(fd), mode: current.mode & 0o777 };
  } finally { closeSync(fd); }
}

function inventory(directory, entries, packageDirs, directoryModes) {
  const info = lstatSync(directory);
  if (!info.isDirectory() || info.isSymbolicLink() || (info.mode & 0o7000)) fail(`unsafe source directory: ${directory}`);
  directoryModes.set(relative(source, directory), info.mode & 0o777);
  const names = readdirSync(directory).sort();
  if (directory !== source && names.includes('go.mod')) {
    report.excluded.push({ path: relative(source, directory), reason: 'nested Go module' });
    return;
  }
  for (const name of names) {
    const filename = join(directory, name), rel = relative(source, filename);
    if (isPythonBytecodePath(rel)) { report.excluded.push({ path: rel, reason: 'Python bytecode/cache' }); continue; }
    if (npmDirectories.has(name)) { report.excluded.push({ path: rel, reason: 'npm/cache/SCM directory' }); continue; }
    if (directory === source && npmRootDirectories.has(name)) { report.excluded.push({ path: rel, reason: 'npm kit tooling/templates directory' }); continue; }
    const stat = lstatSync(filename);
    if (stat.isSymbolicLink()) fail(`source symlink refused: ${rel}`);
    if (stat.isDirectory()) { inventory(filename, entries, packageDirs, directoryModes); continue; }
    if (!stat.isFile()) fail(`non-regular source entry refused: ${rel}`);
    entries.push({ filename, rel, directory, mode: stat.mode & 0o777 });
    if (name.endsWith('.go')) packageDirs.add(directory);
  }
}

function selected(entry, packageDirs) {
  const parts = entry.rel.split(sep);
  const fixture = parts.includes('testdata');
  const inPackage = [...packageDirs].some(pkg => inside(pkg, entry.filename));
  const root = entry.directory === source && rootFiles.has(parts.at(-1));
  if (!fixture && !inPackage && !root) return false;
  // Fixture files keep their actual formats, including JS/JSON/npm-named test
  // inputs. Mixed Go/npm package directories omit executable npm-only siblings.
  if (!fixture && (npmMetadata.has(parts.at(-1)) || npmExtensions.has(extname(entry.filename)))) return false;
  return true;
}

// Small lexical reader for direct literal fixture paths in Go tests. It skips
// comments and string bodies, so example text and HTTP path fixtures are not
// mistaken for filesystem calls. Variable paths are not rewritten or supplied;
// their tests must succeed using the isolated copy and TMPDIR on their own.
function goTokens(sourceText) {
  const tokens = [];
  for (let i = 0; i < sourceText.length;) {
    const c = sourceText[i];
    if (/\s/.test(c)) { i++; continue; }
    if (sourceText.startsWith('//', i)) { const end = sourceText.indexOf('\n', i + 2); i = end < 0 ? sourceText.length : end; continue; }
    if (sourceText.startsWith('/*', i)) { const end = sourceText.indexOf('*/', i + 2); if (end < 0) fail('unterminated Go comment'); i = end + 2; continue; }
    if (c === '"' || c === '`' || c === "'") {
      const start = i++;
      while (i < sourceText.length) {
        if (c !== '`' && sourceText[i] === '\\') { i += 2; continue; }
        if (sourceText[i++] === c) break;
      }
      const raw = sourceText.slice(start, i);
      tokens.push({ kind: c === "'" ? 'rune' : 'string', raw });
      continue;
    }
    const word = /^[A-Za-z_][A-Za-z0-9_]*/.exec(sourceText.slice(i));
    if (word) { tokens.push({ kind: 'identifier', raw: word[0] }); i += word[0].length; continue; }
    tokens.push({ kind: 'symbol', raw: c }); i++;
  }
  return tokens;
}

function goString(raw) {
  if (raw.startsWith('`')) return raw.slice(1, -1).replaceAll('\r', '');
  // JSON handles ordinary Go quoted paths. Non-JSON Go escape forms fail
  // closed, instead of guessing an escaped traversal or absolute pathname.
  try { return JSON.parse(raw); } catch { fail(`fixture path uses an unsupported quoted escape: ${raw}`); }
}

function checkLiteralFixtures(filename, data, copiedModule) {
  const tokens = goTokens(data.toString('utf8'));
  const receivers = new Set(['os', 'ioutil']);
  const functions = new Set(['ReadFile', 'Open', 'OpenFile', 'Stat', 'Lstat', 'ReadDir', 'DirFS']);
  for (let i = 0; i + 4 < tokens.length; i++) {
    if (!receivers.has(tokens[i].raw) || tokens[i + 1].raw !== '.' || !functions.has(tokens[i + 2].raw) || tokens[i + 3].raw !== '(' || tokens[i + 4].kind !== 'string') continue;
    const value = goString(tokens[i + 4].raw);
    const packageDirectory = join(copiedModule, dirname(relative(source, filename)));
    const target = resolve(packageDirectory, value);
    const record = { test_file: relative(source, filename), call: `${tokens[i].raw}.${tokens[i + 2].raw}`, path: value, resolved_path: target };
    report.fixture_paths.push(record);
    if (isAbsolute(value) || !inside(copiedModule, target)) fail(`source-external fixture path in ${record.test_file}: ${value}`);
  }
}

function jsonObjects(text) {
  const values = [];
  let start = -1, depth = 0, quoted = false, escaped = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (start < 0) {
      if (/\s/.test(c)) continue;
      if (c !== '{') fail('go list emitted non-JSON output');
      start = i; depth = 1; continue;
    }
    if (quoted) { if (escaped) escaped = false; else if (c === '\\') escaped = true; else if (c === '"') quoted = false; continue; }
    if (c === '"') quoted = true;
    else if (c === '{' || c === '[') depth++;
    else if (c === '}' || c === ']') {
      if (--depth === 0) { values.push(JSON.parse(text.slice(start, i + 1))); start = -1; }
    }
  }
  if (start >= 0) fail('go list emitted incomplete JSON');
  return values;
}

function command(args, cwd, env) {
  const started = Date.now();
  const result = spawnSync('go', args, { cwd, env, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, timeout: 600000 });
  const stdout = result.stdout || '', stderr = result.stderr || '';
  const record = {
    executable: 'go', args, cwd, exit_code: result.status, signal: result.signal,
    duration_ms: Date.now() - started, stdout_sha256: hash(stdout), stderr_sha256: hash(stderr),
    stdout_bytes: Buffer.byteLength(stdout), stderr_bytes: Buffer.byteLength(stderr),
    env: { CGO_ENABLED: env.CGO_ENABLED, GOWORK: env.GOWORK, GOTOOLCHAIN: env.GOTOOLCHAIN, GOFLAGS: env.GOFLAGS, GOENV: env.GOENV, TMPDIR: env.TMPDIR },
  };
  if (result.error) record.error = result.error.message;
  if (result.status !== 0 || result.error) { record.stdout_tail = stdout.slice(-16000); record.stderr_tail = stderr.slice(-16000); }
  report.commands.push(record);
  return { ...result, stdout, stderr, record };
}

function requireSuccess(result, label) {
  if (result.error || result.status !== 0) fail(`${label} failed${result.error ? `: ${result.error.message}` : ` with exit ${result.status}`}`);
}

function removeDisposableCopy(directory) {
  // Restore owner traversal/write only inside the newly-created scratch tree
  // before deletion, so copied read-only fixture permissions do not leak it.
  const writable = filename => {
    const stat = lstatSync(filename);
    if (stat.isSymbolicLink() || !stat.isDirectory()) return;
    chmodSync(filename, (stat.mode & 0o777) | 0o700);
    for (const name of readdirSync(filename)) writable(join(filename, name));
  };
  writable(directory);
  rmSync(directory, { recursive: true, force: true });
}

try {
  if (process.platform !== 'linux' || source !== '/work/web-kit') fail('go-distribution runs only in the pinned Linux runner at /work/web-kit');
  const sourceInfo = lstatSync(source);
  if (!sourceInfo.isDirectory() || sourceInfo.isSymbolicLink() || realpathSync(source) !== source) fail('module root must be a real directory');
  const parallel = Number(process.env.GOMAXPROCS);
  if (!Number.isInteger(parallel) || parallel < 1 || parallel > 4) fail('runner GOMAXPROCS must be between 1 and 4');
  for (const directory of ['/scratch', '/scratch/_temp']) {
    const stat = lstatSync(directory);
    if (!stat.isDirectory() || stat.isSymbolicLink() || realpathSync(directory) !== directory) fail(`unsafe runner scratch root: ${directory}`);
  }
  scratch = mkdtempSync('/scratch/_temp/go-distribution-');
  chmodSync(scratch, 0o700);
  const copiedModule = join(scratch, 'module'), temporary = join(scratch, 'tmp');
  mkdirSync(copiedModule, { mode: 0o700 });
  mkdirSync(temporary, { mode: 0o700 });
  report.copied_module = copiedModule;

  const entries = [], packageDirs = new Set(), directoryModes = new Map();
  inventory(source, entries, packageDirs, directoryModes);
  if (packageDirs.size === 0) fail('owning module has no Go packages');
  const chosen = entries.filter(entry => selected(entry, packageDirs));
  for (const entry of entries) {
    if (!selected(entry, packageDirs)) report.excluded.push({ path: entry.rel, reason: 'npm-only/non-Go-module source' });
  }
  if (!chosen.some(entry => entry.rel === 'go.mod')) fail('owning go.mod missing');
  if (!chosen.some(entry => entry.rel === 'go.sum')) fail('owning go.sum missing');

  const copiedDirs = new Set(['']);
  for (const entry of chosen) {
    const { data, mode } = readRegular(entry.filename);
    const target = join(copiedModule, entry.rel);
    mkdirSync(dirname(target), { recursive: true, mode: 0o700 });
    for (let directory = dirname(entry.rel); directory !== '.'; directory = dirname(directory)) copiedDirs.add(directory);
    const fd = openSync(target, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_NOFOLLOW, mode);
    try { writeFileSync(fd, data); } finally { closeSync(fd); }
    chmodSync(target, mode);
    report.files.push({ path: entry.rel, sha256: hash(data), bytes: data.length, mode: mode.toString(8), copied_path: target });
    if (entry.rel.endsWith('_test.go')) checkLiteralFixtures(entry.filename, data, copiedModule);
  }
  for (const directory of [...copiedDirs].sort((a, b) => b.length - a.length)) {
    const mode = directoryModes.get(directory);
    if (mode !== undefined) chmodSync(join(copiedModule, directory), mode);
  }

  const goMod = readRegular(join(source, 'go.mod')).data;
  const moduleMatch = /^\s*module\s+(?:"([^"\n]+)"|([^\s]+))\s*$/m.exec(goMod.toString('utf8'));
  if (!moduleMatch) fail('cannot resolve owning module path');
  report.module_path = moduleMatch[1] || moduleMatch[2];
  report.go_mod_sha256 = hash(goMod);
  report.go_sum_sha256 = hash(readRegular(join(source, 'go.sum')).data);
  const env = { ...process.env, CGO_ENABLED: '1', GOWORK: 'off', GOTOOLCHAIN: 'local', GOENV: 'off', GOFLAGS: `-mod=readonly -p=${parallel}`, TMPDIR: temporary };

  const metadata = command(['mod', 'edit', '-json'], copiedModule, env);
  requireSuccess(metadata, 'go mod metadata');
  const replacements = JSON.parse(metadata.stdout).Replace || [];
  if (replacements.some(replacement => !replacement.New.Version)) fail('standalone Go distribution contains a local module replacement');

  const listing = command(['list', '-json', './...'], copiedModule, env);
  requireSuccess(listing, 'go list');
  const packages = jsonObjects(listing.stdout);
  if (packages.length === 0) fail('standalone distribution lists no Go packages');
  for (const pkg of packages) {
    if (!inside(copiedModule, resolve(pkg.Dir)) || pkg.Module?.Path !== report.module_path || resolve(pkg.Module.Dir) !== copiedModule || pkg.Error) fail(`package is outside owning distribution: ${pkg.ImportPath}`);
    report.packages.push({ import_path: pkg.ImportPath, directory: pkg.Dir, go_files: pkg.GoFiles || [], test_files: pkg.TestGoFiles || [], external_test_files: pkg.XTestGoFiles || [], ignored_go_files: pkg.IgnoredGoFiles || [] });
  }
  const vet = command(['vet', './...'], copiedModule, env);
  requireSuccess(vet, 'standalone go vet');
  const tests = command(['test', '-race', '-json', '-count=1', './...'], copiedModule, env);
  const events = tests.stdout.split('\n').filter(line => line.trim()).map(line => JSON.parse(line));
  const actualPackages = new Set(packages.map(pkg => pkg.ImportPath));
  const started = new Set(), passed = new Set(), failed = [];
  const packageRuns = new Map(), packagePasses = new Set();
  for (const event of events) {
    if (!actualPackages.has(event.Package)) fail(`unexpected tested package: ${event.Package}`);
    const key = `${event.Package}\0${event.Test || ''}`;
    if (event.Action === 'run' && event.Test) { started.add(key); packageRuns.set(event.Package, (packageRuns.get(event.Package) || 0) + 1); }
    if (event.Action === 'pass' && event.Test) passed.add(key);
    if (event.Action === 'pass' && !event.Test) packagePasses.add(event.Package);
    if (event.Action === 'fail') failed.push({ package: event.Package, test: event.Test || null, time: event.Time });
    if (event.Action === 'skip') report.skips.push({ package: event.Package, test: event.Test || null, time: event.Time });
  }
  report.tests = [...started].sort().map(key => {
    const [pkg, test] = key.split('\0');
    return { package: pkg, test, status: passed.has(key) ? 'pass' : 'fail' };
  });
  report.executed_tests = started.size;
  report.failed_tests = failed;
  requireSuccess(tests, 'standalone race tests');
  if (started.size === 0) fail('standalone race suite executed no tests');
  if (report.skips.length) fail(`standalone race suite skipped ${report.skips.length} test/package events`);
  if (failed.length || [...started].some(key => !passed.has(key))) fail('standalone race suite did not pass every executed test');
  for (const pkg of actualPackages) {
    if (!packageRuns.get(pkg) || !packagePasses.has(pkg)) fail(`package lacks executed passing tests: ${pkg}`);
  }

  // Read-only module flags and post-run byte/mode checks catch accidental lock
  // or fixture mutation in either the original source or distribution copy.
  for (const file of report.files) {
    const original = readRegular(join(source, file.path));
    const copiedInfo = lstatSync(file.copied_path);
    if (!copiedInfo.isFile() || copiedInfo.isSymbolicLink()) fail(`copied source changed type: ${file.path}`);
    const copied = readRegular(file.copied_path, copiedModule);
    if (hash(original.data) !== file.sha256 || original.mode.toString(8) !== file.mode || hash(copied.data) !== file.sha256 || copied.mode.toString(8) !== file.mode) fail(`source/fixture/lock drift during distribution tests: ${file.path}`);
  }
  report.status = 'pass';
} catch (error) {
  report.error = error.message;
  process.exitCode = 1;
} finally {
  // This removes only the uniquely-created disposable copy, never task work.
  if (scratch) {
    try { removeDisposableCopy(scratch); report.scratch_removed = true; }
    catch (error) { report.status = 'fail'; report.cleanup_error = error.message; process.exitCode = 1; }
  }
  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
}
