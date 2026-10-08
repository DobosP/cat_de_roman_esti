import * as fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { isDeepStrictEqual } from 'node:util';
import { pathToFileURL } from 'node:url';

// Resolution only. This does not import SDK code, execute setup/deps, accept a
// phase/receipt, prove installed bytes, or return a passing gate/release result.
const BOOTSTRAP = 'tools/gui-bootstrap-webkit';
const BOOTSTRAP_FILES = Object.freeze({
  'package.json': 'e669f64606d08208ea8c23b0cb05822a8f0939527f03f6e453736ff10e8eef1f',
  'scripts/run-task.mjs': '10c72f96c031e880988fb62f761f9c5ae5f50a6eaf2dd3fd553ed25dba43389f',
  'scripts/locate-kit.mjs': '3b61fcfd3184c663d1acc5c3764af707b95c2fe6952de77393ef914d1692647c',
  'scripts/ui-adoption-config.mjs': 'c1292e5b377b64934cafeaaf3ab2ba45f8f5393229716f4a71b5a65ad9122f60',
  'scripts/ast-artifacts.mjs': 'aaa1ed835db6963d95e345e264d4bdcc5b5d748f345294db67af6be3cd439265',
  'scripts/kit-sync.mjs': '0d76e09e3d0c9e7d959e98a0e1093b4ad4d82deca29d1e61f77e0576ffb5f300',
  'schemas/validate.mjs': '32552ef83c2baf911f5412b7053bf70e832ac19e43ed611ebc522c50186f40f4',
  'schemas/ui-adoption.schema.json': 'e8b3f95ffd875a78fc97898d2cedc540ce719ddc84e5f3f9f1ee99f33bbffa64',
});
const PRIMARY = new Set(['unit', 'full', 'gen', 'deps', 'kit:sync', 'build', 'image',
  'baseline', 'golden:capture', 'golden:verify', 'contract:refresh', 'legacy:freeze',
  'e2e', 'perf', 'qualify', 'shell']);
const HOOK = new Set(['setup', 'deps', 'gen', 'unit', 'full', 'build', 'baseline',
  'assets-sync', 'legacy-freeze', 'e2e', 'perf']);
// The trusted Taskfile's _runner installs through repo:setup whenever its
// configured runner is absent, including gen; this is not a setup CLI target.
const SETUP_PRIMARY = new Set(['unit', 'full', 'gen', 'build', 'image', 'baseline',
  'golden:capture', 'golden:verify', 'contract:refresh', 'legacy:freeze', 'e2e', 'perf']);
const HEX = /^[a-f0-9]{64}$/;
const SHA = /^[a-f0-9]{40}(?:[a-f0-9]{24})?$/;
const UUID = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

function fail(message) { throw Error('Cat hook runtime: ' + message); }
function object(value, fields, optional = []) {
  return !!value && typeof value === 'object' && !Array.isArray(value)
    && fields.every(key => Object.hasOwn(value, key))
    && Object.keys(value).every(key => fields.includes(key) || optional.includes(key))
    && Object.values(Object.getOwnPropertyDescriptors(value)).every(desc => Object.hasOwn(desc, 'value'));
}
function relative(value, dot = false) {
  if (dot && value === '.') return value;
  if (typeof value !== 'string' || !value || /[\\:\x00-\x1f\x7f]/.test(value)
      || value.startsWith('/') || value.split('/').some(part =>
        !/^[A-Za-z0-9_@.-]+$/.test(part) || part === '.' || part === '..'
        || part.endsWith('.') || /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(part))) {
    fail('unsafe literal relative path');
  }
  return value;
}
function canonicalRoot(root) {
  if (typeof root !== 'string' || !path.isAbsolute(root) || path.resolve(root) !== root) fail('canonical absolute root required');
  let current = root;
  while (true) {
    const stat = fs.lstatSync(current);
    if (stat.isSymbolicLink() || !stat.isDirectory()) fail('nonregular root or ancestor');
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  if (fs.realpathSync.native(root) !== root) fail('root alias refused');
  return root;
}
function regular(root, name, directory = false) {
  relative(name);
  const parts = name.split('/');
  let current = root;
  for (let index = 0; index < parts.length; index++) {
    current = path.join(current, parts[index]);
    const stat = fs.lstatSync(current);
    if (stat.isSymbolicLink()) fail('symlink runtime or configuration component');
    if (index < parts.length - 1 || directory) {
      if (!stat.isDirectory()) fail('runtime directory required');
    } else if (!stat.isFile()) fail('regular runtime file required');
  }
  if (fs.realpathSync.native(current) !== current) fail('runtime alias refused');
  return current;
}
function bytes(root, name) {
  const file = regular(root, name), before = fs.lstatSync(file, { bigint: true });
  const data = fs.readFileSync(file), after = fs.lstatSync(file, { bigint: true });
  if (!after.isFile() || after.isSymbolicLink() || before.dev !== after.dev
      || before.ino !== after.ino || before.size !== after.size
      || before.mtimeNs !== after.mtimeNs || BigInt(data.length) !== after.size) fail('source changed during read');
  regular(root, name);
  return data;
}
function canonicalConfig(config) {
  if (!object(config, ['role', 'app', 'npm_dir', 'vendor_dir', 'go_dirs'], ['ui_adoption'])
      || config.role !== 'consumer' || config.app !== 'cat_de_roman_esti') fail('explicit Cat consumer configuration required');
  relative(config.npm_dir); relative(config.vendor_dir);
  if (!Array.isArray(config.go_dirs) || !config.go_dirs.length
      || new Set(config.go_dirs).size !== config.go_dirs.length) fail('explicit unique Go directories required');
  config.go_dirs.forEach(value => relative(value, true));
  // The existing trusted producer validates the complete E1 phase. Retain it
  // byte-for-byte in its canonical projection; this resolver never activates it.
  return { role: config.role, app: config.app, npm_dir: config.npm_dir,
    vendor_dir: config.vendor_dir, go_dirs: [...config.go_dirs],
    ...(Object.hasOwn(config, 'ui_adoption') ? { ui_adoption: config.ui_adoption } : {}) };
}
function assertProjection(target, primary) {
  if (target === 'setup') {
    if (!SETUP_PRIMARY.has(primary)) fail('setup lacks a real _runner primary projection');
  } else if (target === 'deps') {
    if (!['deps', 'gen', 'kit:sync'].includes(primary)) fail('deps primary projection refused');
  } else if (target === 'assets-sync') {
    if (primary !== 'build') fail('assets-sync primary projection refused');
  } else if (primary !== (target === 'legacy-freeze' ? 'legacy:freeze' : target)) {
    fail('hook primary projection refused');
  }
}
function currentConfig(root, target, config) {
  const descriptor = JSON.parse(bytes(root, '.gate/wrapper-current.json'));
  const fields = ['schema', 'invocation', 'target', 'sha', 'tree_sha256', 'toolchain_digest',
    'config_sha256', 'config_path', 'config_file_sha256'];
  if (!object(descriptor, fields) || descriptor.schema !== 1 || !UUID.test(descriptor.invocation)
      || !PRIMARY.has(descriptor.target) || !SHA.test(descriptor.sha)
      || !HEX.test(descriptor.tree_sha256) || !/^sha256:[a-f0-9]{64}$/.test(descriptor.toolchain_digest)
      || descriptor.sha !== process.env.GATE_SHA || descriptor.tree_sha256 !== process.env.GATE_TREE_SHA256
      || descriptor.toolchain_digest !== process.env.TOOLCHAIN_DIGEST
      || !HEX.test(descriptor.config_sha256) || !HEX.test(descriptor.config_file_sha256)) {
    fail('closed current wrapper source/tree/image identity required');
  }
  assertProjection(target, descriptor.target);
  const capturedPath = '.gate/' + descriptor.target.replaceAll(':', '-') + '/wrapper-kit-config.json';
  if (descriptor.config_path !== capturedPath) fail('current primary config reference differs');
  const capturedBytes = bytes(root, capturedPath), captured = JSON.parse(capturedBytes);
  if (!object(captured, ['schema', 'target', 'sha', 'tree_sha256', 'toolchain_digest', 'config', 'config_sha256', 'command'])
      || sha(capturedBytes) !== descriptor.config_file_sha256 || captured.schema !== 1
      || captured.target !== descriptor.target || captured.sha !== descriptor.sha
      || captured.tree_sha256 !== descriptor.tree_sha256 || captured.toolchain_digest !== descriptor.toolchain_digest
      || captured.config_sha256 !== descriptor.config_sha256) fail('current frozen config bytes or identity differ');
  const command = captured.command;
  if (!object(command, ['command', 'args', 'exit_code', 'duration_ms', 'stdout_sha256', 'stderr_sha256'])
      || command.command !== 'task' || !isDeepStrictEqual(command.args, ['--silent', 'repo:kit-config'])
      || command.exit_code !== 0 || !Number.isInteger(command.duration_ms) || command.duration_ms < 0
      || typeof command.stdout_sha256 !== 'string' || !HEX.test(command.stdout_sha256)
      || typeof command.stderr_sha256 !== 'string' || !HEX.test(command.stderr_sha256)) {
    fail('current config command witness differs');
  }
  const selected = canonicalConfig(config), frozen = canonicalConfig(captured.config);
  if (!isDeepStrictEqual(frozen, selected) || !isDeepStrictEqual(captured.config, frozen)
      || descriptor.config_sha256 !== sha(JSON.stringify(frozen))) fail('complete frozen configuration differs');
  return descriptor;
}

export function resolveHookRuntime(root, target, config) {
  root = canonicalRoot(root);
  if (!HOOK.has(target)) fail('unsupported actual Cat repo hook target');
  const descriptor = currentConfig(root, target, config);
  const bootstrap = target === 'deps' || target === 'setup';
  const selected = bootstrap ? BOOTSTRAP : config.npm_dir;
  regular(root, selected, true);
  if (bootstrap) {
    for (const [name, expected] of Object.entries(BOOTSTRAP_FILES)) {
      if (sha(bytes(root, selected + '/' + name)) !== expected) fail('reviewed committed bootstrap source drift: ' + name);
    }
  } else {
    // Structural confinement of this actual module's current import/read graph.
    // No future installed payload hash is invented; actual selected-byte proof
    // still belongs to owning setup, kit checks and native qualification.
    for (const name of Object.keys(BOOTSTRAP_FILES)) regular(root, selected + '/' + name);
  }
  const manifest = JSON.parse(bytes(root, selected + '/package.json'));
  if (manifest.name !== '@roedu/web-kit' || typeof manifest.version !== 'string'
      || !/^\d+\.\d+\.\d+$/.test(manifest.version)) fail('runtime module owner identity differs');
  const url = pathToFileURL(regular(root, selected + '/scripts/run-task.mjs')).href;
  return Object.freeze({ url, mode: bootstrap ? 'committed-bootstrap-helper' : 'configured-selected-helper',
    wrapper_target: descriptor.target, wrapper_invocation: descriptor.invocation });
}
