import { strict as assert } from 'node:assert';
import { test } from 'node:test';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { auditGoModules, normalizeGoRequirements } from './go-module-audit.mjs';
import { walkRepository } from '../lint/validation-files.mjs';

const config = { role: 'consumer', app: 'cat_de_roman_esti', npm_dir: 'frontend/node_modules/@roedu/web-kit', vendor_dir: 'frontend/vendor', go_dirs: ['go-backend'] };
const remote = 'example.test/remote v1.2.3 h1:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\n';
const entries = new Map([['example.test/remote', { kind: 'gomod', version: 'v1.2.3' }]]);
const mod = (name, body = '') => `module ${name}\n\ngo 1.27.1\n\n${body}`;

function fixture(t, extra = {}) {
  const root = mkdtempSync('/scratch/_temp/go-local-audit-');
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const put = (file, value) => { const path = join(root, file); mkdirSync(dirname(path), { recursive: true }); writeFileSync(path, value); };
  for (const [file, value] of Object.entries({
    'go-backend/go.mod': mod('example.test/backend', 'require (\n example.test/auth v0.0.0\n example.test/remote v1.2.3\n)\nreplace example.test/auth => ../shared-go/authcore\n'),
    'go-backend/go.sum': remote,
    'shared-go/authcore/go.mod': mod('example.test/auth'),
    ...extra,
  })) put(file, value);
  const files = () => walkRepository(root, config).files;
  const audit = (options = {}) => auditGoModules({ root, config, files: options.files ?? files(), entries, lock: { core_tag: 'core-v1.1' }, ...options });
  return { root, put, files, audit };
}

test('same-repo authcore is audited without becoming a kit receiver or needing a remote sum', t => {
  const f = fixture(t), report = f.audit();
  assert.deepEqual(report.receivers, ['go-backend']);
  assert.deepEqual(report.modules.map(row => row.dir), ['go-backend', 'shared-go/authcore']);
  assert.deepEqual(report.local_edges, [{ from: 'go-backend', module: 'example.test/auth', version: 'v0.0.0', old_version: '', literal: '../shared-go/authcore', target: 'shared-go/authcore' }]);
  assert.equal(report.modules[1].sum_sha256, null);
  assert.equal(report.modules[0].requirements.find(row => row.module === 'example.test/auth').resolution, 'same-repo');
  assert.equal(report.modules[0].requirements.find(row => row.module === 'example.test/remote').resolution, 'remote');
  assert(report.commands.every(row => row.command === 'go' && row.args[1] === 'edit' && row.args[2] === '-json' && row.exit_code === 0));
});

test('native parsing preserves quoted literal paths and version-qualified replace blocks', t => {
  const f = fixture(t, {
    'go-backend/go.mod': mod('example.test/backend', 'require example.test/auth v0.0.0\nreplace (\n example.test/auth v0.0.0 => "../shared auth" // ignored => comment\n)\n'),
    'shared auth/go.mod': mod('"example.test/auth"'),
  });
  const report = f.audit(); assert.equal(report.local_edges[0].target, 'shared auth');
  assert.equal(report.local_edges[0].old_version, 'v0.0.0');
});

test('recursive diamonds and cycles audit each module once and repeat without source mutation', t => {
  const f = fixture(t, {
    'go-backend/go.mod': mod('example.test/backend', 'require (\n example.test/auth v0.0.0\n example.test/service v0.0.0\n)\nreplace (\n example.test/auth => ../shared-go/authcore\n example.test/service => ../service\n)\n'),
    'shared-go/authcore/go.mod': mod('example.test/auth', 'require example.test/util v0.0.0\nreplace example.test/util => ../../utility\n'),
    'service/go.mod': mod('example.test/service', 'require example.test/util v0.0.0\nreplace example.test/util => ../utility\n'),
    'utility/go.mod': mod('example.test/util', 'require (\n example.test/backend v0.0.0\n example.test/remote v1.2.3\n)\nreplace example.test/backend => ../go-backend\n'),
    'utility/go.sum': remote,
  });
  const before = new Map(f.files().filter(path => /go\.(?:mod|sum)$/.test(path)).map(path => [path, readFileSync(join(f.root, path))]));
  const originalConfig = structuredClone(config), first = f.audit(), second = f.audit();
  assert.equal(first.modules.length, 4); assert.equal(first.commands.length, 4);
  assert.equal(new Set(first.modules.map(row => row.dir)).size, 4);
  assert.equal(first.local_edges.length, 5); assert.deepEqual(second, first); assert.deepEqual(config, originalConfig);
  for (const [path, bytes] of before) assert.deepEqual(readFileSync(join(f.root, path)), bytes);
});

test('registered local requirements retain ordinary exact version pins', t => {
  const f = fixture(t, { 'go-backend/go.mod': mod('example.test/backend', 'require example.test/auth v1.2.3\nreplace example.test/auth => ../shared-go/authcore\n') });
  const registered = new Map(entries); registered.set('example.test/auth', { kind: 'gomod', version: 'v1.2.3' });
  assert.equal(f.audit({ entries: registered }).modules[0].requirements[0].resolution, 'same-repo');
  f.put('go-backend/go.mod', mod('example.test/backend', 'require example.test/auth v1.2.2\nreplace example.test/auth => ../shared-go/authcore\n'));
  assert.throws(() => f.audit({ entries: registered }), /exact Go version differs/);
});

test('recursive local targets cannot hide remote pins or missing content checksums', t => {
  const f = fixture(t, { 'shared-go/authcore/go.mod': mod('example.test/auth', 'require example.test/remote v1.2.3\n') });
  assert.throws(() => f.audit(), /actual content hash/);
  f.put('shared-go/authcore/go.sum', remote.replace('v1.2.3 ', 'v1.2.3/go.mod '));
  assert.throws(() => f.audit(), /actual content hash/);
  f.put('shared-go/authcore/go.sum', remote);
  assert.equal(f.audit().modules[1].requirements[0].resolution, 'remote');
  f.put('shared-go/authcore/go.mod', mod('example.test/auth', 'require example.test/remote v1.2.2\n'));
  assert.throws(() => f.audit(), /exact Go version differs/);
});

test('unused and mismatched replacement selectors remain unaudited refusals', t => {
  const f = fixture(t);
  f.put('go-backend/go.mod', mod('example.test/backend', 'require example.test/remote v1.2.3\nreplace example.test/auth => ../shared-go/authcore\n'));
  assert.throws(() => f.audit(), /no matching actual requirement/);
  f.put('go-backend/go.mod', mod('example.test/backend', 'require example.test/auth v0.0.0\nreplace example.test/auth v0.0.1 => ../shared-go/authcore\n'));
  assert.throws(() => f.audit(), /no matching actual requirement/);
});

test('native normalization cannot hide an earlier unsafe duplicate replacement', t => {
  const f = fixture(t, { 'go-backend/go.mod': mod('example.test/backend', 'require example.test/auth v0.0.0\nreplace example.test/auth => /outside/unsafe\nreplace example.test/auth => ../shared-go/authcore\n') });
  assert.throws(() => f.audit(), /dropped declared replacement rows|duplicate replacement selector|native Go parser refused/);
});

test('absolute escaped cached ignored undiscovered and remote-version targets are refused', t => {
  const f = fixture(t);
  for (const [target, failure] of [
    ['/outside/auth', /literal relative/], ['../../outside/auth', /escapes/], ['C:/outside/auth', /literal relative|native Go parser refused/],
    ['example.test/alternate v1.0.0', /remote module\/version/], ['../dist/auth', /ignored or cache/],
    ['../.cache/auth', /ignored or cache/], ['../cache/auth', /ignored or cache/], ['../fixtures/auth', /ignored or cache/],
  ]) {
    f.put('go-backend/go.mod', mod('example.test/backend', `require example.test/auth v0.0.0\nreplace example.test/auth => ${target}\n`));
    assert.throws(() => f.audit(), failure, target);
  }
  f.put('go-backend/go.mod', mod('example.test/backend', 'require example.test/auth v0.0.0\nreplace example.test/auth => ../shared-go/authcore\n'));
  assert.throws(() => f.audit({ files: f.files().filter(path => path !== 'shared-go/authcore/go.mod') }), /not an audited source module/);
});

test('local replacement identity symlinks and literal unsafe intermediate hops are refused', t => {
  const f = fixture(t); f.put('shared-go/authcore/go.mod', mod('example.test/other'));
  assert.throws(() => f.audit(), /declared module identity differs/);
  f.put('shared-go/authcore/go.mod', mod('example.test/auth')); const discovered = f.files();
  rmSync(join(f.root, 'shared-go/authcore/go.mod'));
  symlinkSync(join(f.root, 'go-backend/go.mod'), join(f.root, 'shared-go/authcore/go.mod'));
  assert.throws(() => f.audit({ files: discovered }), /symlink/);
  rmSync(join(f.root, 'shared-go/authcore/go.mod')); f.put('shared-go/authcore/go.mod', mod('example.test/auth'));
  symlinkSync(join(f.root, 'shared-go'), join(f.root, 'alias'));
  f.put('go-backend/go.mod', mod('example.test/backend', 'require example.test/auth v0.0.0\nreplace example.test/auth => ../alias/../shared-go/authcore\n'));
  assert.throws(() => f.audit({ files: discovered }), /symlink/);
});

test('frozen consumer kit edge stays distinct from the same-repo source allowance', t => {
  const kit = 'github.com/DobosP/roedu-ui/web-kit';
  const f = fixture(t, { 'go-backend/go.mod': mod('example.test/backend', `require ${kit} v0.0.0-core-v1.1\nreplace ${kit} => ./third_party/webkit\n`), 'go-backend/third_party/webkit/go.mod': mod(kit) });
  const report = f.audit(); assert.equal(report.local_edges.length, 0); assert.equal(report.kit_edges.length, 1);
  assert.equal(report.modules.length, 1); assert.equal(report.kit_edges[0].target, 'go-backend/third_party/webkit');
  f.put('go-backend/go.mod', mod('example.test/backend', `require ${kit} v0.0.0-core-v1.0\nreplace ${kit} => ./third_party/webkit\n`));
  assert.throws(() => f.audit(), /kit Go tag\/path mismatch/);
  f.put('go-backend/go.mod', mod('example.test/backend', 'require example.test/auth v0.0.0\nreplace example.test/auth => ./third_party/webkit\n'));
  assert.throws(() => f.audit(), /ignored or cache/);
});


test('actual native omitted Indirect stays direct and unknown direct requirements remain refused', t => {
  const f=fixture(t),report=f.audit();
  const raw=JSON.parse(report.commands[0].stdout),declared=raw.Require.find(row=>row.Path==='example.test/remote');
  assert.equal(Object.hasOwn(declared,'Indirect'),false,'pinned native Go omits its false flag');
  assert.equal(report.modules[0].requirements.find(row=>row.module==='example.test/remote').indirect,false);
  assert.equal(report.commands[0].stderr,'');
  f.put('go-backend/go.mod',mod('example.test/backend','require example.test/unknown v0.0.0\n'));
  f.put('go-backend/go.sum','example.test/unknown v0.0.0 h1:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\n');
  assert.throws(()=>f.audit(),/unregistered direct Go requirement/);
  f.put('go-backend/go.mod',mod('example.test/backend','require example.test/unknown v0.0.0 // indirect\n'));
  const indirect=f.audit(),native=JSON.parse(indirect.commands[0].stdout);
  assert.equal(native.Require[0].Indirect,true);assert.equal(indirect.modules[0].requirements[0].indirect,true);
});

test('native requirement normalization accepts booleans and refuses malformed flags duplicate and unknown fields', () => {
  const direct={Path:'example.test/direct',Version:'v0.0.0'};
  assert.deepEqual(normalizeGoRequirements([direct],'fixture/go.mod'),[{...direct,Indirect:false}]);
  assert.deepEqual(normalizeGoRequirements([{...direct,Indirect:false}],'fixture/go.mod'),[{...direct,Indirect:false}]);
  assert.deepEqual(normalizeGoRequirements([{...direct,Indirect:true}],'fixture/go.mod'),[{...direct,Indirect:true}]);
  for(const Indirect of [null,0,1,'false',{},[]])assert.throws(()=>normalizeGoRequirements([{...direct,Indirect}],'fixture/go.mod'),/malformed/);
  assert.throws(()=>normalizeGoRequirements([direct,direct],'fixture/go.mod'),/duplicate/);
  assert.throws(()=>normalizeGoRequirements([{...direct,Unknown:true}],'fixture/go.mod'),/malformed/);
  for(const row of [null,{},[],{Path:direct.Path},{...direct,Version:''}])assert.throws(()=>normalizeGoRequirements([row],'fixture/go.mod'),/malformed/);
});
