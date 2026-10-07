// Execute only through the pinned runner after parent/root integration.
// All generated provenance is explicitly SYNTHETIC helper-test data. It cannot
// count as original Cat runtime qualification or an owner authenticity review.
import * as fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { gzipSync, gunzipSync } from 'node:zlib';
import { inspectUiAdoption, uiAdoptionPending, requireActiveUi } from './kit-sync.mjs';
import { fixtureHash, fixtureArchive, makeUiAdoptionFixture } from './ui-adoption-fixture.mjs';

function fixture(fn, options) {
  assert.equal(process.platform, 'linux');
  assert.equal(process.cwd(), '/work', 'helper fixtures execute only in pinned runner /work');
  const base = '/scratch/_temp'; assert.equal(fs.realpathSync(base), base); assert.ok(fs.lstatSync(base).isDirectory() && !fs.lstatSync(base).isSymbolicLink());
  const root = fs.mkdtempSync(path.join(base, 'synthetic-ui-adoption-'));
  try { return fn(makeUiAdoptionFixture(root, options)); }
  finally { fs.rmSync(root, { recursive: true, force: true }); }
}
const staged = f => inspectUiAdoption(f.root, f.config, f.kit);
test('synthetic staged provenance is verified/read-only/idempotent with absent original sidecar', () => fixture(f => {
  const before = fs.readFileSync(path.join(f.root, f.manifestPath));
  const first = staged(f), second = staged(f);
  assert.deepEqual(first, second); assert.deepEqual(first.preserve, ['frontend/vendor/roedu-ui-0.3.0.tgz']);
  assert.equal(first.receipt.assertion_count, 2); assert.deepEqual(first.receipt.fixture_ids, ['original:behavior', 'original:presence']);
  assert.deepEqual(fs.readFileSync(path.join(f.root, f.manifestPath)), before);
  const pending = uiAdoptionPending(first);
  assert.deepEqual(Object.keys(pending), ['mode', 'status', 'until', 'source', 'config_sha256', 'legacy', 'selected_ui']);
  assert.equal(pending.source, 'repo:kit-config'); assert.equal(pending.config_sha256, fixtureHash(JSON.stringify(f.config)));
  assert.deepEqual(pending.legacy, f.config.ui_adoption.legacy); assert.equal(pending.selected_ui.version, '1.0.1');
  assert.throws(() => requireActiveUi(f.root, f.config), /active UI is required/);
}));
test('synthetic staged phase preserves and validates an existing exact sidecar', () => fixture(f => {
  assert.equal(staged(f).preserve.length, 2);
  f.put('frontend/vendor/roedu-ui-0.3.0.tgz.sha256', '0'.repeat(64) + '  roedu-ui-0.3.0.tgz\n');
  assert.throws(() => staged(f), /sidecar identity differs/);
}, { oldSidecar: true }));
test('synthetic staged receipt retains ORIGINAL graph after live Motion14 normalization', () => fixture(f => {
  f.manifest.dependencies.motion = '14.0.0'; delete f.manifest.dependencies['framer-motion'];
  f.lock.packages[''] = structuredClone(f.manifest); f.lock.packages['node_modules/motion'] = { version: '14.0.0', dependencies: { 'framer-motion': '14.0.0' } }; f.lock.packages['node_modules/framer-motion'].version = '14.0.0';
  f.put(f.manifestPath, f.json(f.manifest)); f.put(f.lockPath, f.json(f.lock));
  assert.equal(staged(f).receipt.runtime_dependencies['framer-motion'], '12.42.2');
  assert.equal(f.config.ui_adoption.legacy.source_sha, 'a'.repeat(40));
}));
test('synthetic staged phase cannot create or reset a UI pointer', () => fixture(f => {
  f.manifest.dependencies['@roedu/ui'] = `file:vendor/${f.selected.filename}`; f.put(f.manifestPath, f.json(f.manifest));
  assert.throws(() => staged(f), /must already be exactly/);
  delete f.manifest.dependencies['@roedu/ui']; f.put(f.manifestPath, f.json(f.manifest));
  assert.throws(() => staged(f), /owning UI dependency declaration/);
}));
test('synthetic staged old pointer cannot hide an already-installed new UI', () => fixture(f => {
  f.installSdk(f.selected); assert.throws(() => staged(f), /installed UI file differs/);
}));
test('synthetic malformed phase/app/version/source fields refuse', () => fixture(f => {
  for (const mutate of [config => { config.ui_adoption.mode = 'active'; }, config => { config.app = 'ro_teacher'; }, config => { config.role = 'core'; }, config => { config.ui_adoption.until = 'S1-M3'; }, config => { config.ui_adoption.extra = true; }, config => { config.ui_adoption.legacy.version = '0.3.1'; }, config => { config.ui_adoption.legacy.source_sha = 'tag'; }]) {
    const config = structuredClone(f.config); mutate(config); assert.throws(() => inspectUiAdoption(f.root, config, f.kit), /phase|sealed/);
  }
}));
test('synthetic changed archive and receipt hashes refuse before adoption', () => fixture(f => {
  f.put('frontend/vendor/roedu-ui-0.3.0.tgz', Buffer.from('changed original')); assert.throws(() => staged(f), /SDK SHA256 differs/);
  f.put('frontend/vendor/roedu-ui-0.3.0.tgz', f.old.data); f.put(f.config.ui_adoption.legacy.receipt, Buffer.from('{}'));
  assert.throws(() => staged(f), /receipt SHA256 differs/);
}));
test('synthetic sealed original SDK rejects Python caches before adoption', () => fixture(f => {
  for (const suffix of ['__pycache__/fixture.py', 'stale.pyc', 'nested/stale.pyo', 'stale.pyc.gz', 'nested/stale.pyo.br']) {
    const changed = fixtureArchive(new Map([...f.old.files, [`package/dist/${suffix}`, Buffer.from('runtime cache')]]));
    f.put('frontend/vendor/roedu-ui-0.3.0.tgz', changed); f.config.ui_adoption.legacy.archive_sha256 = fixtureHash(changed);
    assert.throws(() => staged(f), /excluded Python bytecode\/cache SDK archive member/);
  }
}));
test('synthetic sealed old SDK cannot acquire runtime dependencies', () => fixture(f => {
  f.old.manifest.dependencies = { motion: '14.0.0' }; f.old.files.set('package/package.json', f.json(f.old.manifest));
  const changed = fixtureArchive(f.old.files); f.put('frontend/vendor/roedu-ui-0.3.0.tgz', changed); f.config.ui_adoption.legacy.archive_sha256 = fixtureHash(changed);
  assert.throws(() => staged(f), /original SDK must not gain dependencies/);
}));
test('synthetic preserved graph snapshots are hash-bound and cannot point at live graph', () => fixture(f => {
  f.put(f.receipt.dependency_graph.lock.path, '{}'); assert.throws(() => staged(f), /original lock snapshot bytes differ/);
  f.put(f.receipt.dependency_graph.lock.path, f.json(f.lock));
  f.receipt.dependency_graph.manifest = { path: f.manifestPath, sha256: fixtureHash(f.json(f.manifest)) }; f.saveReceipt();
  assert.throws(() => staged(f), /distinct preserved evidence/);
}));
test('synthetic original graph refuses aliased SDK lock pointer/integrity', () => fixture(f => {
  for (const mutate of [lock => { lock.packages['node_modules/@roedu/ui'].resolved = 'npm:other'; }, lock => { lock.packages['node_modules/@roedu/ui'].integrity = 'sha512-' + 'x'.repeat(88); }, lock => { lock.packages['node_modules/@alias/sdk'] = { name: '@roedu/ui', version: '0.3.0' }; }]) {
    const lock = structuredClone(f.lock); mutate(lock); f.put(f.lockPath, f.json(lock)); assert.throws(() => staged(f), /UI lock|aliased/);
  }
}));
test('synthetic fixture declaration alone cannot masquerade as native original execution', () => fixture(f => {
  const bytes = f.json({ ...f.native, check: 'fixture-declaration' });
  f.receipt.execution.report = f.ref('docs/receipts/original-native.json', bytes); f.receipt.execution.stdout = f.ref('docs/receipts/original.stdout.log', bytes); f.saveReceipt();
  assert.throws(() => staged(f), /not a fixture declaration/);
}));
test('synthetic native execution must exactly bind fixtures/assertions with no skips', () => fixture(f => {
  for (const mutate of [native => { native.fixtures.pop(); }, native => { native.fixtures[0].assertions[0].executed = false; }, native => { native.fixtures[1].assertions[0].status = 'skip'; }, native => { native.runtime_dependencies.react = '18.0.0'; }]) {
    const native = structuredClone(f.native); mutate(native); const bytes = f.json(native);
    f.receipt.execution.report = f.ref('docs/receipts/original-native.json', bytes); f.receipt.execution.stdout = f.ref('docs/receipts/original.stdout.log', bytes); f.saveReceipt();
    assert.throws(() => staged(f), /native original|native executed/);
  }
}));
test('synthetic native stdout must byte-match report, even when both hashes are sealed', () => fixture(f => {
  f.receipt.execution.stdout = f.ref('docs/receipts/original.stdout.log', Buffer.from(f.json(f.native).toString().trim())); f.saveReceipt();
  assert.throws(() => staged(f), /must equal retained actual stdout bytes/);
}));
test('synthetic receipt artifacts refuse symlink ancestors and cache/generated paths', () => fixture(f => {
  const moved = path.join(f.root, 'preserved'); fs.renameSync(path.join(f.root, 'docs/receipts'), moved); fs.symlinkSync(moved, path.join(f.root, 'docs/receipts'));
  assert.ok(fs.lstatSync(path.join(f.root,'docs/receipts')).isSymbolicLink());
  assert.throws(() => staged(f), /Symlink destination|Nonregular destination/);
  for (const receipt of ['.gate/original.json', 'docs/../original.json', 'dist/original.json', 'node_modules/original.json', 'docs/receipts/original.tsbuildinfo', 'docs/__pycache__/original.json', 'docs/receipts/original.pyc', 'docs/receipts/original.pyo.br']) {
    const config = structuredClone(f.config); config.ui_adoption.legacy.receipt = receipt; assert.throws(() => inspectUiAdoption(f.root, config, f.kit));
  }
}));
test('synthetic activation proves exact selected vendor/install/exports/owner graph', () => fixture(f => {
  const active = f.activate(), proof = requireActiveUi(f.root, active);
  assert.equal(proof.pending, false); assert.equal(proof.version, '1.0.1');
  assert.deepEqual(proof.installed_graph, ['node_modules/@roedu/ui', 'node_modules/framer-motion', 'node_modules/motion', 'node_modules/preact']);
  assert.equal(uiAdoptionPending(inspectUiAdoption(f.root, active, f.kit)), undefined);
  assert.deepEqual(requireActiveUi(f.root, active), proof);
  assert.throws(() => staged(f), /must already be exactly/);
}));
test('public active proof refuses caller kit/parser overrides and uses committed kit only', () => fixture(f => {
  const active = f.activate();
  assert.throws(() => requireActiveUi(f.root, active, { ...f.kit, tag: 'core-v1.999' }), /only root\/config/);
  assert.throws(() => requireActiveUi(f.root, active, f.kit, { parseArchive: () => new Map() }), /only root\/config/);
  // Mutating the structural preflight object's identity cannot change actual
  // public proof selection; its source is the complete canonical on-disk kit.
  f.kit.tag = 'core-v1.999'; assert.equal(requireActiveUi(f.root, active).tag, 'core-v1.1');
  fs.rmSync(path.join(f.root, 'kit/CORE_TAG')); assert.throws(() => requireActiveUi(f.root, active), /Missing input|ENOENT/);
}));
test('public active proof refuses changed committed tag, checksum or extra kit input', () => fixture(f => {
  const active = f.activate(), sums = fs.readFileSync(path.join(f.root, 'kit/SHA256SUMS'));
  f.put('kit/CORE_TAG', 'core-v1.2\n'); assert.throws(() => requireActiveUi(f.root, active), /three archives/);
  f.put('kit/CORE_TAG', 'core-v1.1\n'); f.put('kit/SHA256SUMS', sums.toString().replace(/^[a-f0-9]{64}/, '0'.repeat(64)));
  assert.throws(() => requireActiveUi(f.root, active), /Archive hash mismatch/);
  f.put('kit/SHA256SUMS', sums); f.put('kit/unselected.tgz', 'must not be accepted');
  assert.throws(() => requireActiveUi(f.root, active), /three archives/);
}));
test('public active proof hashes each actual UI/web-kit/Go archive before acceptance', () => fixture(f => {
  const active = f.activate();
  for (const [filename, original] of f.bundle.archives) {
    const damaged = Buffer.from(original); damaged[damaged.length - 1] ^= 1; f.put('kit/' + filename, damaged);
    assert.throws(() => requireActiveUi(f.root, active), /Archive hash mismatch/); f.put('kit/' + filename, original);
  }
}));
test('public active proof enforces actual npm owners/Go identity/cache/link archive policy after valid resealing', () => fixture(f => {
  const active = f.activate();
  function restore() {
    for (const [filename, bytes] of f.bundle.archives) f.put('kit/' + filename, bytes);
    f.put('kit/SHA256SUMS', [...f.bundle.archives].map(([filename, bytes]) => `${fixtureHash(bytes)}  ${filename}\n`).join(''));
  }
  function reseal(filename, changed) {
    restore(); f.put('kit/' + filename, changed);
    f.put('kit/SHA256SUMS', [...f.bundle.archives].map(([name, bytes]) => `${fixtureHash(name === filename ? changed : bytes)}  ${name}\n`).join(''));
  }
  const uiFiles = new Map(f.selected.files); uiFiles.set('package/package.json', f.json({ ...f.selected.manifest, name: '@unselected/ui' }));
  reseal(f.selected.filename, fixtureArchive(uiFiles)); assert.throws(() => requireActiveUi(f.root, active), /Npm name\/version mismatch/);
  const kitFiles = new Map(f.bundle.kitFiles); kitFiles.set('package/package.json', f.json({ name: '@unselected/kit', version: '0.1.1' }));
  reseal(f.bundle.kitName, fixtureArchive(kitFiles)); assert.throws(() => requireActiveUi(f.root, active), /Npm name\/version mismatch/);
  const goFiles = new Map(f.bundle.goFiles); goFiles.set('web-kit/go.mod', Buffer.from('module example.invalid/not-the-kit\n\ngo 1.27.1\n'));
  reseal(f.bundle.goName, fixtureArchive(goFiles)); assert.throws(() => requireActiveUi(f.root, active), /Go archive module mismatch/);
  const caches = new Map(f.selected.files); caches.set('package/dist/nested/cache.tsbuildinfo', Buffer.from('excluded compiler state'));
  reseal(f.selected.filename, fixtureArchive(caches)); assert.throws(() => requireActiveUi(f.root, active), /Excluded compiler build state/);
  const linked = gunzipSync(f.selected.data), header = linked.subarray(0, 512); header[156] = 50; header.fill(32, 148, 156);
  header.write(header.reduce((sum, byte) => sum + byte, 0).toString(8).padStart(6, '0') + '\0 ', 148);
  reseal(f.selected.filename, gzipSync(linked)); assert.throws(() => requireActiveUi(f.root, active), /Unsafe tar entry type/);
  restore(); assert.equal(requireActiveUi(f.root, active).status, 'pass');
}));
test('synthetic activation refuses remaining old archive, missing exports and altered installed SDK', () => fixture(f => {
  const active = f.activate(); f.put('frontend/vendor/roedu-ui-0.3.0.tgz', f.old.data);
  assert.throws(() => requireActiveUi(f.root, active), /retains old SDK/); fs.rmSync(path.join(f.root, 'frontend/vendor/roedu-ui-0.3.0.tgz'));
  fs.rmSync(path.join(f.root, 'frontend/node_modules/@roedu/ui/dist/index.d.ts')); assert.throws(() => requireActiveUi(f.root, active), /Missing input/);
  f.installSdk(f.selected); f.put('frontend/node_modules/@roedu/ui/dist/index.js', 'changed runtime'); assert.throws(() => requireActiveUi(f.root, active), /installed UI file differs/);
}));
test('synthetic activation refuses owner lock drift, aliases and exact dependency version mismatch', () => fixture(f => {
  const active = f.activate(), original = JSON.parse(fs.readFileSync(path.join(f.root, f.lockPath)));
  for (const mutate of [lock => { lock.packages['node_modules/@roedu/ui'].integrity = 'sha512-wrong'; }, lock => { lock.packages[''].dependencies.motion = '13.0.0'; }, lock => { lock.packages['node_modules/motion'].version = '13.0.0'; }, lock => { lock.packages['node_modules/motion'].name = 'aliased-motion'; }]) {
    const lock = structuredClone(original); mutate(lock); f.put(f.lockPath, f.json(lock)); assert.throws(() => requireActiveUi(f.root, active), /UI lock|manifest\/lock|exact dependency|graph identity/);
  }
}));
test('synthetic activation refuses missing installed transitive SDK graph identity', () => fixture(f => {
  const active = f.activate(); fs.rmSync(path.join(f.root, 'frontend/node_modules/framer-motion/package.json'));
  assert.throws(() => requireActiveUi(f.root, active), /Missing input/);
}));
test('synthetic staged provenance is distinct from lint-scope exemptions', () => fixture(f => {
  const plan = staged(f), pending = uiAdoptionPending(plan);
  assert.equal(pending.source, 'repo:kit-config'); assert.equal(Object.hasOwn(pending, 'legacy_pending'), false);
  assert.equal(Object.hasOwn(pending, 'rules'), false); assert.equal(Object.hasOwn(pending, 'paths'), false);
  assert.equal(Object.hasOwn(plan, 'scope'), false); assert.equal(Object.hasOwn(f.config, 'lint_scope'), false);
}));
