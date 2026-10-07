// SYNTHETIC STRUCTURAL FIXTURE BUILDER ONLY. This generates fake package/receipt
// bytes for helper tests; it does not qualify Cat's original runtime or execute
// its behavior/Presence assertions. The real parent reviews original execution.
import * as fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { gzipSync } from 'node:zlib';

export const fixtureHash = bytes => createHash('sha256').update(bytes).digest('hex');
const json = value => Buffer.from(JSON.stringify(value, null, 2) + '\n');
const sri = bytes => `sha512-${createHash('sha512').update(bytes).digest('base64')}`;
export function fixtureArchive(files) {
  const blocks = [];
  for (const [name, bytes] of [...files].sort(([left], [right]) => left.localeCompare(right))) {
    const header = Buffer.alloc(512);
    if (Buffer.byteLength(name) > 100) throw Error('synthetic tar fixture path too long');
    header.write(name, 0); header.write('0000644\0', 100); header.write('0000000\0', 108); header.write('0000000\0', 116);
    header.write(bytes.length.toString(8).padStart(11, '0') + '\0', 124); header.write('00000000000\0', 136); header.fill(32, 148, 156);
    header[156] = 48; header.write('ustar\0', 257); header.write('00', 263);
    const sum = header.reduce((total, byte) => total + byte, 0);
    header.write(sum.toString(8).padStart(6, '0') + '\0 ', 148);
    blocks.push(header, bytes, Buffer.alloc((512 - bytes.length % 512) % 512));
  }
  return gzipSync(Buffer.concat([...blocks, Buffer.alloc(1024)]));
}
function sdk(version) {
  const old = version === '0.3.0';
  const manifest = {
    name: '@roedu/ui', version, type: 'module', license: 'UNLICENSED', files: ['dist'],
    exports: old ? { '.': { types: './dist/index.d.ts', import: './dist/index.js' }, './styles.css': './dist/roedu-ui.css' } : { '.': { types: './dist/index.d.ts', import: './dist/index.js' }, './tokens.css': './dist/tokens.css' },
    peerDependencies: old ? { react: '>=18', 'react-dom': '>=18' } : { preact: '11.0.0' },
    ...(!old ? { dependencies: { motion: '14.0.0' } } : {})
  };
  const files = new Map([['package/package.json', json(manifest)], ['package/dist/index.js', Buffer.from(`export const version = '${version}';\n`)], ['package/dist/index.d.ts', Buffer.from('export declare const version: string;\n')], [old ? 'package/dist/roedu-ui.css' : 'package/dist/tokens.css', Buffer.from(':root { --fixture: 1; }\n')]]);
  // Hidden Vite inventories are distribution metadata, not compiler state.
  if (!old) files.set('package/dist/.roedu-vite-bundle.json', json({ schema: 1, fixture: true }));
  return { manifest, files, data: fixtureArchive(files), filename: `roedu-ui-${version}.tgz` };
}
// A complete canonical input set exercises the public helper's actual loadKit
// boundary. All archives are synthetic fixture inputs, not release artifacts.
export function stageFixtureKit(root, selected) {
  const tag = 'core-v1.1', kitName = 'roedu-web-kit-0.1.1.tgz', goName = `web-kit-go-${tag}.tgz`;
  const coreLock = { schema: 2, core_tag: tag, resolved: '2026-10-07', tools: [
    { tool: 'preact', kind: 'npm', scope: 'core', version: '11.0.0' },
    { tool: 'motion', kind: 'npm', scope: 'core', version: '14.0.0' },
    { tool: 'framer-motion', kind: 'npm', scope: 'core', version: '14.0.0', status: 'transitive-only', dependants: ['motion'] }
  ], toolchain_image: { version: 'roedu-toolchain:synthetic-core-v1.1', image_id: 'sha256:' + 'c'.repeat(64) } };
  const kitFiles = new Map([
    ['package/package.json', json({ name: '@roedu/web-kit', version: '0.1.1', type: 'module' })],
    ['package/versions.lock.json', json(coreLock)],
    ['package/scripts/kit-sync.mjs', Buffer.from('// Synthetic loadKit fixture only; never execute.\n')],
    ['package/templates/gate.sh', Buffer.from('#!/usr/bin/env bash\n# Synthetic fixture; never execute.\n')],
    ['package/templates/compose.gate.yml', Buffer.from('services: {}\n')],
    ['package/templates/Taskfile.yml', Buffer.from('version: 3\n')],
    ['package/templates/Dockerfile.toolchain', Buffer.from('FROM synthetic-fixture\n')],
    ['package/templates/.gate.env', Buffer.from(`TOOLCHAIN_IMAGE=${coreLock.toolchain_image.version}\nTOOLCHAIN_DIGEST=${coreLock.toolchain_image.image_id}\nPG_MAJOR=16\n`)]
  ]);
  const goFiles = new Map([
    ['web-kit/go.mod', Buffer.from('module github.com/DobosP/roedu-ui/web-kit\n\ngo 1.27.1\n')],
    ['web-kit/tokens/fixture.go', Buffer.from('package tokens\n// Synthetic archive fixture only.\n')]
  ]);
  const archives = new Map([[selected.filename, selected.data], [kitName, fixtureArchive(kitFiles)], [goName, fixtureArchive(goFiles)]]);
  const directory = path.join(root, 'kit'); fs.mkdirSync(directory, { recursive: true });
  fs.writeFileSync(path.join(directory, 'CORE_TAG'), tag + '\n');
  for (const [filename, bytes] of archives) fs.writeFileSync(path.join(directory, filename), bytes);
  fs.writeFileSync(path.join(directory, 'SHA256SUMS'), [...archives].map(([filename, bytes]) => `${fixtureHash(bytes)}  ${filename}\n`).join(''));
  return { tag, archives, kitFiles, goFiles, kitName, goName };
}
export function makeUiAdoptionFixture(root, { oldSidecar = false } = {}) {
  const put = (relative, bytes) => { const file = path.join(root, relative); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, bytes); };
  const ref = (relative, bytes) => { put(relative, bytes); return { path: relative, sha256: fixtureHash(bytes) }; };
  const old = sdk('0.3.0'), selected = sdk('1.0.1');
  const bundle = stageFixtureKit(root, selected);
  const vendor = 'frontend/vendor', manifestPath = 'frontend/package.json', lockPath = 'frontend/package-lock.json';
  const pointer = 'file:vendor/roedu-ui-0.3.0.tgz';
  const manifest = { name: 'synthetic-cat-consumer', version: '1.0.0', private: true, dependencies: { '@roedu/ui': pointer, react: '^19.2.7', 'react-dom': '^19.2.7', 'framer-motion': '^12.42.2' } };
  const sdkRow = { version: '0.3.0', resolved: pointer, integrity: sri(old.data), peerDependencies: old.manifest.peerDependencies };
  const lock = { name: manifest.name, version: manifest.version, lockfileVersion: 3, packages: { '': structuredClone(manifest), 'node_modules/@roedu/ui': sdkRow, 'node_modules/react': { version: '19.2.7' }, 'node_modules/react-dom': { version: '19.2.7' }, 'node_modules/framer-motion': { version: '12.42.2' } } };
  put(`${vendor}/${old.filename}`, old.data);
  if (oldSidecar) put(`${vendor}/${old.filename}.sha256`, `${fixtureHash(old.data)}  ${old.filename}\n`);
  put(manifestPath, json(manifest)); put(lockPath, json(lock));
  const dependencyGraph = { manifest: ref('docs/receipts/original-manifest.json', json(manifest)), lock: ref('docs/receipts/original-lock.json', json(lock)) };
  const fixtures = [
    { id: 'original:behavior', suite: 'behavior', source: ref('docs/receipts/original-behavior.mjs', Buffer.from('// Synthetic immutable behavior fixture source.\n')), assertions: [{ id: 'state-order', status: 'pass' }] },
    { id: 'original:presence', suite: 'presence', source: ref('docs/receipts/original-presence.mjs', Buffer.from('// Synthetic immutable Presence fixture source.\n')), assertions: [{ id: 'exit-before-enter', status: 'pass' }] }
  ];
  const runtimeSdk = { name: '@roedu/ui', version: '0.3.0', archive_sha256: fixtureHash(old.data), manifest_sha256: fixtureHash(old.files.get('package/package.json')), entry: 'dist/index.js', entry_sha256: fixtureHash(old.files.get('package/dist/index.js')) };
  const identity = { schema: 1, status: 'pass', app: 'cat_de_roman_esti', sha: 'a'.repeat(40), tree_sha256: 'b'.repeat(64), toolchain_digest: 'sha256:' + 'c'.repeat(64), runtime_sdk: runtimeSdk, runtime_dependencies: { react: '19.2.7', 'react-dom': '19.2.7', 'framer-motion': '12.42.2' }, dependency_graph: dependencyGraph };
  const native = { ...identity, check: 'cat-original-ui-runtime-execution', fixtures: fixtures.map(fixture => ({ ...fixture, executed: true, assertions: fixture.assertions.map(assertion => ({ ...assertion, executed: true })) })) };
  const nativeBytes = json(native);
  const receipt = { ...identity, check: 'cat-original-ui-runtime', fixtures, execution: { kind: 'actual-original-runtime', command: 'node', args: ['frontend/tests/original-runtime.mjs'], exit_code: 0, started: '2026-10-07T00:00:00.000Z', finished: '2026-10-07T00:00:01.000Z', report: ref('docs/receipts/original-native.json', nativeBytes), stdout: ref('docs/receipts/original.stdout.log', nativeBytes), stderr: ref('docs/receipts/original.stderr.log', Buffer.alloc(0)) } };
  const config = { role: 'consumer', app: 'cat_de_roman_esti', npm_dir: 'frontend/node_modules/@roedu/web-kit', vendor_dir: vendor, go_dirs: ['server'], ui_adoption: { mode: 'staged-react', until: 'S1-M2', legacy: { version: '0.3.0', archive_sha256: fixtureHash(old.data), source_sha: identity.sha, receipt: 'docs/receipts/original-ui.json', receipt_sha256: '' } } };
  function saveReceipt() { const bytes = json(receipt); put(config.ui_adoption.legacy.receipt, bytes); config.ui_adoption.legacy.receipt_sha256 = fixtureHash(bytes); }
  saveReceipt();
  const kit = { tag: 'core-v1.1', ui: { data: selected.data, filename: selected.filename, manifest: selected.manifest }, sums: new Map([[selected.filename, fixtureHash(selected.data)]]) };
  function installSdk(value) { for (const [name, bytes] of value.files) put(`frontend/node_modules/@roedu/ui/${name.slice(8)}`, bytes); }
  function activate() {
    const active = { ...config }; delete active.ui_adoption;
    fs.rmSync(`${root}/${vendor}/${old.filename}`, { force: true }); fs.rmSync(`${root}/${vendor}/${old.filename}.sha256`, { force: true });
    put(`${vendor}/${selected.filename}`, selected.data); put(`${vendor}/${selected.filename}.sha256`, `${fixtureHash(selected.data)}  ${selected.filename}\n`);
    const activeManifest = { name: manifest.name, version: manifest.version, private: true, dependencies: { '@roedu/ui': `file:vendor/${selected.filename}`, motion: '14.0.0', preact: '11.0.0' } };
    const motion = { name: 'motion', version: '14.0.0', dependencies: { 'framer-motion': '14.0.0' } }, framer = { name: 'framer-motion', version: '14.0.0' }, preact = { name: 'preact', version: '11.0.0' };
    const activeLock = { name: activeManifest.name, version: activeManifest.version, lockfileVersion: 3, packages: { '': structuredClone(activeManifest), 'node_modules/@roedu/ui': { version: selected.manifest.version, resolved: activeManifest.dependencies['@roedu/ui'], integrity: sri(selected.data), dependencies: selected.manifest.dependencies, peerDependencies: selected.manifest.peerDependencies }, 'node_modules/motion': motion, 'node_modules/framer-motion': framer, 'node_modules/preact': preact } };
    put(manifestPath, json(activeManifest)); put(lockPath, json(activeLock));
    fs.rmSync(path.join(root, 'frontend/node_modules/@roedu/ui'), { recursive: true, force: true }); installSdk(selected);
    for (const pkg of [motion, framer, preact]) put(`frontend/node_modules/${pkg.name}/package.json`, json(pkg));
    return active;
  }
  return { root, config, kit, bundle, old, selected, manifest, lock, receipt, native, put, ref, saveReceipt, installSdk, activate, json, pointer, manifestPath, lockPath };
}
