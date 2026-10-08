import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { resolveHookRuntime } from '../../scripts/gui-hook-runtime.mjs';

// Future native unit source only. Compose exposes the retained host _temp gate
// as /work; each synthetic fixture stays in /work/.gate/_temp. No committed
// bootstrap/package is modified.
// Resolution success is never import/setup/installed-byte/phase qualification.
const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const bootstrap = 'tools/gui-bootstrap-webkit';
const closure = ['package.json', 'scripts/run-task.mjs', 'scripts/locate-kit.mjs',
  'scripts/ui-adoption-config.mjs', 'scripts/ast-artifacts.mjs', 'scripts/kit-sync.mjs',
  'schemas/validate.mjs', 'schemas/ui-adoption.schema.json'];
const digest = data => createHash('sha256').update(data).digest('hex');
const sourcePins = JSON.parse(fs.readFileSync(new URL('./fixtures/gui-hook-runtime-bootstrap.json', import.meta.url)));
const identity = { sha: 'a'.repeat(40), tree_sha256: 'b'.repeat(64),
  toolchain_digest: 'sha256:' + 'c'.repeat(64) };
const selected = 'frontend/node_modules/@roedu/web-kit';
const base = { role: 'consumer', app: 'cat_de_roman_esti', npm_dir: selected,
  vendor_dir: 'frontend/vendor', go_dirs: ['go-backend'] };

function sourceBytes(name) {
  let current = repo;
  const parts = (bootstrap + '/' + name).split('/');
  for (let index = 0; index < parts.length; index++) {
    current = path.join(current, parts[index]);
    const stat = fs.lstatSync(current);
    assert.equal(stat.isSymbolicLink(), false, 'committed fixture source cannot redirect reads');
    assert.equal(index < parts.length - 1 ? stat.isDirectory() : stat.isFile(), true);
  }
  assert.equal(fs.realpathSync.native(current), current, 'committed fixture source must be canonical');
  const data = fs.readFileSync(current);
  assert.equal(digest(data), sourcePins.sha256[name], 'read only exact committed bootstrap fixture bytes');
  return data;
}
function write(root, relative, data) {
  const file = path.join(root, ...relative.split('/'));
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  fs.writeFileSync(file, data, { flag: 'wx', mode: 0o600 });
}
function fixture(t, primary = 'kit:sync', config = base) {
  if (process.platform !== 'linux' || repo !== '/work') throw Error('Actual native Compose /work runner required');
  let ancestor = repo;
  while (true) {
    const stat = fs.lstatSync(ancestor);
    if (!stat.isDirectory() || stat.isSymbolicLink()) throw Error('Nonregular synthetic staging ancestor');
    const parent = path.dirname(ancestor);
    if (parent === ancestor) break;
    ancestor = parent;
  }
  if (fs.realpathSync.native(repo) !== repo) throw Error('Canonical native staging required');
  const gate = path.join(repo, '.gate'), gateStat = fs.lstatSync(gate);
  if (!gateStat.isDirectory() || gateStat.isSymbolicLink() || fs.realpathSync.native(gate) !== gate) {
    throw Error('Actual native gate directory required');
  }
  const actualDescriptorPath = path.join(gate, 'wrapper-current.json');
  const actualDescriptorStat = fs.lstatSync(actualDescriptorPath);
  if (!actualDescriptorStat.isFile() || actualDescriptorStat.isSymbolicLink()
      || fs.realpathSync.native(actualDescriptorPath) !== actualDescriptorPath) throw Error('Actual current descriptor required');
  const actualDescriptorBytes = fs.readFileSync(actualDescriptorPath);
  const actual = JSON.parse(actualDescriptorBytes);
  if (actual.schema !== 1 || !['unit', 'full'].includes(actual.target)
      || !/^[a-f0-9]{40}$/.test(actual.sha) || !/^[a-f0-9]{64}$/.test(actual.tree_sha256)
      || !/^sha256:[a-f0-9]{64}$/.test(actual.toolchain_digest)
      || actual.sha !== process.env.GATE_SHA || actual.tree_sha256 !== process.env.GATE_TREE_SHA256
      || actual.toolchain_digest !== process.env.TOOLCHAIN_DIGEST) throw Error('Actual native unit/full descriptor identity required');
  const prior = Object.fromEntries(['GATE_SHA', 'GATE_TREE_SHA256', 'TOOLCHAIN_DIGEST']
    .map(name => [name, process.env[name]]));
  const staging = path.join(gate, '_temp/gui-hook-runtime-synthetic');
  let current = repo;
  for (const part of ['.gate', '_temp', 'gui-hook-runtime-synthetic']) {
    current = path.join(current, part);
    if (!fs.existsSync(current)) fs.mkdirSync(current, { mode: 0o700 });
    const stat = fs.lstatSync(current);
    if (!stat.isDirectory() || stat.isSymbolicLink() || fs.realpathSync.native(current) !== current) {
      throw Error('Nonregular private staging directory');
    }
  }
  const root = fs.mkdtempSync(path.join(staging, 'NON-RELEASE-'));
  fs.chmodSync(root, 0o700);
  t.after(() => {
    for (const [name, value] of Object.entries(prior)) {
      if (value === undefined) delete process.env[name]; else process.env[name] = value;
    }
    // Preserve all surviving files after any assertion failure. No cleanup.
    const rows = [];
    function inventory(directory) {
      for (const name of fs.readdirSync(directory)) {
        const file = path.join(directory, name), stat = fs.lstatSync(file);
        const relative = path.relative(root, file).split(path.sep).join('/');
        if (stat.isSymbolicLink()) rows.push({ path: relative, kind: 'literal-symlink', target: fs.readlinkSync(file), followed: false });
        else if (stat.isDirectory()) inventory(file);
        else if (stat.isFile()) rows.push({ path: relative, kind: 'regular', sha256: digest(fs.readFileSync(file)) });
      }
    }
    inventory(root);
    write(root, 'retained-inventory.json', JSON.stringify({ scope: 'NON-RELEASE-SYNTHETIC',
      native_staging_descriptor_sha256: digest(actualDescriptorBytes), rows }, null, 2));
    t.diagnostic('Retained synthetic runtime-resolution fixture: ' + root);
  });
  write(root, 'NON-RELEASE-FIXTURE.txt', 'Synthetic resolver evidence only. Never a gate/release receipt.\n');
  const copied = structuredClone(config);
  const config_sha256 = digest(JSON.stringify(copied));
  const config_path = '.gate/' + primary.replaceAll(':', '-') + '/wrapper-kit-config.json';
  // Synthetic command witness fields mirror the real gate.sh:338 producer.
  // This fixture has executed no task/config command and is no real receipt.
  const command = { command: 'task', args: ['--silent', 'repo:kit-config'], exit_code: 0,
    duration_ms: 0, stdout_sha256: digest(JSON.stringify(copied) + '\n'), stderr_sha256: digest('') };
  const captured = Buffer.from(JSON.stringify({ schema: 1, target: primary, ...identity,
    config: copied, config_sha256, command }) + '\n');
  const wrapperW = randomUUID();
  write(root, config_path, captured);
  write(root, '.gate/wrapper-current.json', JSON.stringify({ schema: 1, invocation: wrapperW,
    target: primary, ...identity, config_sha256, config_path, config_file_sha256: digest(captured) }));
  for (const name of closure) {
    write(root, bootstrap + '/' + name, sourceBytes(name));
  }
  process.env.GATE_SHA = identity.sha;
  process.env.GATE_TREE_SHA256 = identity.tree_sha256;
  process.env.TOOLCHAIN_DIGEST = identity.toolchain_digest;
  return { root, config: copied, wrapperW };
}
function resolve(f, target) { return resolveHookRuntime(f.root, target, f.config); }
function editPrivateCapture(f, mutate) {
  // Rebind only this synthetic descriptor's file hash so refusal exercises the
  // malformed capture/witness itself, not an unrelated stale hash.
  const descriptorFile = path.join(f.root, '.gate/wrapper-current.json');
  const descriptor = JSON.parse(fs.readFileSync(descriptorFile));
  const capturedFile = path.join(f.root, descriptor.config_path);
  const captured = JSON.parse(fs.readFileSync(capturedFile));
  mutate(captured);
  const data = Buffer.from(JSON.stringify(captured) + '\n');
  fs.writeFileSync(capturedFile, data);
  descriptor.config_file_sha256 = digest(data);
  fs.writeFileSync(descriptorFile, JSON.stringify(descriptor));
}
async function pinnedValidators(f) {
  // Future import of an exact private committed-bootstrap copy for negative
  // validator tests only; never selected installed-package/adoption evidence.
  return import(resolve(f, 'deps').url);
}
function installInertSelection(f) {
  // Copies are inert data for resolution; this does not install or import npm.
  for (const name of closure) {
    write(f.root, f.config.npm_dir + '/' + name, fs.readFileSync(path.join(f.root, bootstrap, name)));
  }
}
function fileSnapshot(root) {
  return closure.map(name => [name, digest(fs.readFileSync(path.join(root, bootstrap, name)))]);
}

test('deps selects the committed helper while the configured installed package is absent', { concurrency: false }, t => {
  const f = fixture(t);
  const before = fileSnapshot(f.root);
  const result = resolve(f, 'deps');
  assert.equal(result.url, pathToFileURL(path.join(f.root, bootstrap, 'scripts/run-task.mjs')).href);
  assert.equal(result.mode, 'committed-bootstrap-helper');
  assert.equal(result.wrapper_invocation, f.wrapperW);
  assert.equal(fs.existsSync(path.join(f.root, selected)), false);
  assert.deepEqual(fileSnapshot(f.root), before);
  assert.deepEqual(f.config, base);
});
test('setup supports the real gen missing-runner projection without a setup CLI target', { concurrency: false }, t => {
  const f = fixture(t, 'gen');
  assert.equal(resolve(f, 'setup').mode, 'committed-bootstrap-helper');
  assert.equal(fs.existsSync(path.join(f.root, selected)), false);
});
test('the actual eight-field captured producer shape is structurally accepted without execution evidence', { concurrency: false }, t => {
  const f = fixture(t);
  const captured = JSON.parse(fs.readFileSync(path.join(f.root, '.gate/kit-sync/wrapper-kit-config.json')));
  assert.deepEqual(Object.keys(captured), ['schema', 'target', 'sha', 'tree_sha256',
    'toolchain_digest', 'config', 'config_sha256', 'command']);
  assert.deepEqual(Object.keys(captured.command), ['command', 'args', 'exit_code', 'duration_ms', 'stdout_sha256', 'stderr_sha256']);
  assert.equal(resolve(f, 'deps').mode, 'committed-bootstrap-helper');
  assert.equal(fs.existsSync(path.join(f.root, 'frontend/package-lock.json')), false);
});
for (const [label, mutate] of [
  ['missing eighth command field', captured => { delete captured.command; }],
  ['missing config field', captured => { delete captured.config; }],
  ['extra captured field', captured => { captured.extra = 'synthetic'; }],
]) {
  test('closed actual captured shape rejects ' + label, { concurrency: false }, t => {
    const f = fixture(t);
    editPrivateCapture(f, mutate);
    assert.throws(() => resolve(f, 'deps'), /current frozen config bytes or identity differ/);
  });
}
for (const [label, mutate] of [
  ['wrong executable', command => { command.command = 'npm'; }],
  ['wrong task target', command => { command.args = ['--silent', 'repo:setup']; }],
  ['reordered args', command => { command.args.reverse(); }],
  ['extra argument', command => { command.args.push('--force'); }],
  ['failed exit', command => { command.exit_code = 1; }],
  ['negative duration', command => { command.duration_ms = -1; }],
  ['noninteger duration', command => { command.duration_ms = 0.5; }],
  ['missing stdout hash', command => { delete command.stdout_sha256; }],
  ['malformed stderr hash', command => { command.stderr_sha256 = 'NOT-A-SHA256'; }],
  ['nonstring stdout hash', command => { command.stdout_sha256 = ['a'.repeat(64)]; }],
  ['extra command field', command => { command.claimed_execution = true; }],
]) {
  test('actual command witness rejects ' + label, { concurrency: false }, t => {
    const f = fixture(t);
    editPrivateCapture(f, captured => mutate(captured.command));
    assert.throws(() => resolve(f, 'deps'), /current config command witness differs/);
  });
}
for (const target of ['gen', 'unit', 'full', 'build']) {
  test('generic ' + target + ' refuses absent configured package without bootstrap fallback', { concurrency: false }, t => {
    const f = fixture(t, target);
    assert.throws(() => resolve(f, target), /ENOENT/);
    assert.equal(fs.existsSync(path.join(f.root, selected)), false);
    assert.deepEqual(fileSnapshot(f.root).length, closure.length);
  });
}
test('generic lookup uses only its explicit selected locator and returns no qualifying report', { concurrency: false }, t => {
  const f = fixture(t, 'gen');
  installInertSelection(f);
  const result = resolve(f, 'gen');
  assert.equal(fileURLToPath(result.url), path.join(f.root, selected, 'scripts/run-task.mjs'));
  assert.equal(result.mode, 'configured-selected-helper');
  assert.deepEqual(Object.keys(result).sort(), ['mode', 'url', 'wrapper_invocation', 'wrapper_target']);
  for (const field of ['status', 'checks', 'actions', 'ui_adoption', 'installed', 'release']) assert.equal(Object.hasOwn(result, field), false);
});
test('setup/deps resolution does not call generic main or old loadKit qualification', { concurrency: false }, t => {
  const f = fixture(t, 'unit');
  const result = resolve(f, 'setup');
  assert.equal(result.mode, 'committed-bootstrap-helper');
  assert.equal(fs.existsSync(path.join(f.root, '.gate/unit/result.json')), false);
  assert.equal(fs.existsSync(path.join(f.root, 'kit')), false);
  assert.equal(fs.existsSync(path.join(f.root, 'frontend/package-lock.json')), false);
});
test('a resolved URL cannot substitute for the actual setup process witness/report', { concurrency: false }, async t => {
  const f = fixture(t);
  const result = resolve(f, 'deps');
  const { validateSetupWitness } = await pinnedValidators(f);
  assert.throws(() => validateSetupWitness(result, { ...identity, invocation: randomUUID() }), /Missing actual setup process witness/);
  assert.throws(() => validateSetupWitness({ command: 'task', target: 'repo:setup',
    exit_code: 0, duration_ms: 0, report: result }, { ...identity, invocation: randomUUID() }));
  assert.equal(fs.existsSync(path.join(f.root, '.gate/setup/result.json')), false);
});
test('dependency bridge requires actual successful lock/tidy actions in addition to resolution', { concurrency: false }, async t => {
  const f = fixture(t);
  const { validateDependencyActions } = await pinnedValidators(f);
  assert.throws(() => validateDependencyActions([]), /Actual sanctioned dependency command missing/);
  const failedLock = [{ check: 'npm-lock', kind: 'command', command: 'npm',
    args_sha256: digest(JSON.stringify(['install', '--package-lock-only', '--ignore-scripts'])), exit_code: 1 }];
  assert.throws(() => validateDependencyActions(failedLock), /Actual sanctioned dependency command missing/);
  assert.equal(fs.existsSync(path.join(f.root, 'frontend/package-lock.json')), false);
});
test('a synthetic valid-shaped npm action cannot hide missing or failed Go tidy evidence', { concurrency: false }, async t => {
  const f = fixture(t);
  const { validateDependencyActions } = await pinnedValidators(f);
  // Counterexample data only: neither command was executed or attested here.
  const lockShape = { check: 'npm-lock', kind: 'command', command: 'npm',
    args_sha256: digest(JSON.stringify(['install', '--package-lock-only', '--ignore-scripts'])), exit_code: 0 };
  assert.throws(() => validateDependencyActions([lockShape]), /Actual sanctioned dependency command missing: go-mod-tidy/);
  const failedTidy = { check: 'go-mod-tidy', kind: 'command', command: 'go',
    args_sha256: digest(JSON.stringify(['mod', 'tidy'])), exit_code: 1 };
  assert.throws(() => validateDependencyActions([lockShape, failedTidy]), /Actual sanctioned dependency command missing: go-mod-tidy/);
  assert.equal(fs.existsSync(path.join(f.root, 'go-backend/go.mod')), false);
});
for (const bad of ['../outside', '/outside', 'frontend\\alias', 'frontend/C:alias', 'frontend/con', 'frontend/alias.']) {
  test('unsafe configured locator refuses before helper resolution: ' + bad, { concurrency: false }, t => {
    const f = fixture(t, 'gen');
    f.config.npm_dir = bad;
    assert.throws(() => resolve(f, 'gen'), /unsafe literal relative path/);
  });
}
test('changed actual repo configuration refuses instead of mutating captured configuration', { concurrency: false }, t => {
  const f = fixture(t);
  f.config.npm_dir = 'tools/another-helper';
  assert.throws(() => resolve(f, 'deps'), /complete frozen configuration differs/);
});
test('the complete staged phase is retained and changed phase evidence refuses', { concurrency: false }, t => {
  const phase = { mode: 'staged-react', until: 'S1-M2', legacy: { version: '0.3.0',
    archive_sha256: '1'.repeat(64), source_sha: '2'.repeat(40),
    receipt: 'docs/reviews/SYNTHETIC-NON-RELEASE/receipt.json', receipt_sha256: '3'.repeat(64) } };
  const f = fixture(t, 'kit:sync', { ...base, ui_adoption: phase });
  const before = structuredClone(f.config);
  assert.equal(resolve(f, 'deps').mode, 'committed-bootstrap-helper');
  assert.deepEqual(f.config, before);
  assert.equal(fs.existsSync(path.join(f.root, phase.legacy.receipt)), false);
  f.config.ui_adoption.legacy.receipt_sha256 = '4'.repeat(64);
  assert.throws(() => resolve(f, 'deps'), /complete frozen configuration differs/);
});
test('captured config byte drift refuses even before a configuration comparison', { concurrency: false }, t => {
  const f = fixture(t);
  fs.appendFileSync(path.join(f.root, '.gate/kit-sync/wrapper-kit-config.json'), '\n ');
  assert.throws(() => resolve(f, 'deps'), /current frozen config bytes or identity differ/);
});
test('wrapper W is preserved independently of a distinct caller hook I', { concurrency: false }, t => {
  const f = fixture(t);
  const callerI = randomUUID();
  const result = resolve(f, 'deps');
  assert.notEqual(result.wrapper_invocation, callerI);
  assert.equal(result.wrapper_invocation, f.wrapperW);
  assert.equal(Object.hasOwn(result, 'invocation'), false);
});
test('bootstrap payload drift refuses even with an otherwise bound current descriptor', { concurrency: false }, t => {
  const f = fixture(t);
  fs.appendFileSync(path.join(f.root, bootstrap, 'scripts/run-task.mjs'), '\n// private mutation\n');
  assert.throws(() => resolve(f, 'deps'), /reviewed committed bootstrap source drift/);
});
test('transitive schema drift refuses before exposing a module URL', { concurrency: false }, t => {
  const f = fixture(t);
  fs.appendFileSync(path.join(f.root, bootstrap, 'schemas/ui-adoption.schema.json'), '\n ');
  assert.throws(() => resolve(f, 'deps'), /reviewed committed bootstrap source drift/);
});
test('runtime symlink components refuse for committed bootstrap', { concurrency: false }, t => {
  const f = fixture(t);
  const original = path.join(f.root, bootstrap, 'scripts/run-task.mjs');
  const retained = original + '.retained';
  fs.renameSync(original, retained);
  fs.symlinkSync(retained, original);
  assert.throws(() => resolve(f, 'deps'), /symlink runtime or configuration component/);
});
test('runtime symlink components refuse for the generic selected module', { concurrency: false }, t => {
  const f = fixture(t, 'gen');
  installInertSelection(f);
  const source = path.join(f.root, selected, 'scripts/run-task.mjs');
  const retained = source + '.retained';
  fs.renameSync(source, retained);
  fs.symlinkSync(retained, source);
  assert.throws(() => resolve(f, 'gen'), /symlink runtime or configuration component/);
});
test('a symlinked selected directory refuses before following its module', { concurrency: false }, t => {
  const f = fixture(t, 'gen');
  installInertSelection(f);
  const original = path.join(f.root, 'frontend'), retained = original + '.retained';
  fs.renameSync(original, retained);
  fs.symlinkSync(retained, original, 'dir');
  assert.throws(() => resolve(f, 'gen'), /symlink runtime or configuration component/);
});
test('the captured configuration cannot be read through a symlink', { concurrency: false }, t => {
  const f = fixture(t);
  const original = path.join(f.root, '.gate/kit-sync/wrapper-kit-config.json'), retained = original + '.retained';
  fs.renameSync(original, retained);
  fs.symlinkSync(retained, original);
  assert.throws(() => resolve(f, 'deps'), /symlink runtime or configuration component/);
});
test('a symlinked root alias cannot grant runtime authority', { concurrency: false }, t => {
  const f = fixture(t);
  const alias = path.join(f.root, 'private-root-alias');
  fs.symlinkSync(f.root, alias, 'dir');
  assert.throws(() => resolveHookRuntime(alias, 'deps', f.config), /nonregular root or ancestor/);
});
test('package owner mismatch refuses without an alternative locator', { concurrency: false }, t => {
  const f = fixture(t, 'gen');
  installInertSelection(f);
  fs.writeFileSync(path.join(f.root, selected, 'package.json'), JSON.stringify({ name: '@unknown/owner', version: '0.1.1' }));
  assert.throws(() => resolve(f, 'gen'), /runtime module owner identity differs/);
});
test('an unbound source/image environment refuses even if the config checksum is valid', { concurrency: false }, t => {
  const f = fixture(t);
  process.env.GATE_SHA = 'd'.repeat(40);
  assert.throws(() => resolve(f, 'deps'), /closed current wrapper source\/tree\/image identity/);
});
test('a descriptor cannot redirect its current config read to another path', { concurrency: false }, t => {
  const f = fixture(t);
  const name = path.join(f.root, '.gate/wrapper-current.json');
  const descriptor = JSON.parse(fs.readFileSync(name));
  descriptor.config_path = 'frontend/package.json';
  fs.writeFileSync(name, JSON.stringify(descriptor));
  assert.throws(() => resolve(f, 'deps'), /current primary config reference differs/);
});
test('historical or mismatched primary target cannot authorize this hook', { concurrency: false }, t => {
  const f = fixture(t, 'unit');
  assert.throws(() => resolve(f, 'deps'), /deps primary projection refused/);
  assert.throws(() => resolve(f, 'gen'), /hook primary projection refused/);
});
test('an invented standalone setup primary cannot supply wrapper authority', { concurrency: false }, t => {
  const f = fixture(t, 'setup');
  assert.throws(() => resolve(f, 'setup'), /closed current wrapper source\/tree\/image identity/);
});
test('unsafe root aliases and unsupported hooks refuse before resolution', { concurrency: false }, t => {
  const f = fixture(t);
  assert.throws(() => resolveHookRuntime(f.root + '/..', 'deps', f.config), /canonical absolute root/);
  assert.throws(() => resolveHookRuntime(f.root, 'fabricated-setup-cli', f.config), /unsupported actual Cat repo hook target/);
});
