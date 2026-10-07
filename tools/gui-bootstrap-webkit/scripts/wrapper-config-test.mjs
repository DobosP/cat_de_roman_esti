import * as fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';

const hash = value => createHash('sha256').update(value).digest('hex');
const wrapper = fs.readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../templates/gate.sh'), 'utf8');
function block(label) {
  const start = wrapper.indexOf(`<<'${label}'\n`), end = wrapper.indexOf(`\n${label}\n`, start);
  assert(start >= 0 && end > start, `missing trusted inline ${label}`);
  return wrapper.slice(start + label.length + 5, end);
}
const configCode = block('JS_WRAPPER_CONFIG').split('// WRAPPER_CONFIG_MAIN')[0] + '\nexport { normalConfig };\n';
const { normalConfig } = await import('data:text/javascript;base64,' + Buffer.from(configCode).toString('base64'));
const commands = [], checks = [];
function run(command, args, input) {
  const started = Date.now(), result = spawnSync(command, args, { encoding: 'utf8', input, maxBuffer: 8 * 1024 * 1024 });
  commands.push({ command, args_sha256: hash(JSON.stringify(args)), exit_code: result.status, duration_ms: Date.now() - started, stdout_sha256: hash(result.stdout ?? ''), stderr_sha256: hash(result.stderr ?? '') });
  return result;
}
function checked(name, fn) { fn(); checks.push({ name, status: 'pass' }); }
const parent = path.resolve('.gate/wrapper-config-fixtures'); fs.mkdirSync(parent, { recursive: true });
const fixture = fs.mkdtempSync(path.join(parent, 'run-')), source = path.join(fixture, 'source'), mirror = path.join(fixture, 'mirror'), control = path.join(fixture, 'control');
const put = (root, file, bytes) => { const target = path.join(root, file); fs.mkdirSync(path.dirname(target), { recursive: true }); fs.writeFileSync(target, bytes); };
try {
  assert.equal(process.argv.length, 2, 'wrapper-config-test accepts no arguments');
  fs.mkdirSync(control, { recursive: true });
  const module = 'github.com/DobosP/roedu-ui/web-kit';
  put(source, 'go.mod', `module "example.test/root"\ngo 1.27.1\nreplace "${module}" => ./third_party/webkit\n`);
  put(source, 'services/server/go.mod', `module example.test/server\ngo 1.27.1\nreplace (\n\t\`${module}\` => ./third_party/webkit\n)\n`);
  put(source, 'third_party/webkit/go.mod', `module ${module}\ngo 1.27.1\n`);
  put(source, 'services/server/third_party/webkit/go.mod', `module ${module}\ngo 1.27.1\n`);
  put(source, 'services/server/third_party/webkit/sample/embedfs/dist/.keep', 'original approved embed member');
  put(source, 'client/package.json', '{"name":"fixture-app"}\n');
  put(source, 'client/packages/roedu-ui-0.3.0.tgz', 'old owned fixture bytes');
  put(source, 'client/packages/roedu-ui-0.3.0.tgz.sha256', 'old sidecar fixture bytes');
  put(source, 'client/packages/another-app.tgz', 'unrelated vendor bytes');
  for (const name of ['scripts/gate.sh', 'compose.gate.yml', 'Taskfile.yml', 'Dockerfile.toolchain', 'versions.lock.json', 'Taskfile.repo.yml', '.codex/config.toml', '.github/workflows/ci.yml', 'kit/CORE_TAG', 'ci.yml']) put(source, name, 'immutable fixture ' + name);
  put(source, 'other/vendor/roedu-ui-0.3.0.tgz', 'unrelated suffix owner');
  put(source, 'other/package.json', 'unrelated manifest');
  fs.cpSync(source, mirror, { recursive: true });
  const raw = { role: 'consumer', app: 'fixture_app', npm_dir: 'client/node_modules/@roedu/web-kit', vendor_dir: 'client/packages', go_dirs: ['.', 'services/server'] };
  const config = normalConfig(mirror, raw);
  checked('literal custom basename, root module and nested module', () => assert.deepEqual(config, raw));
  checked('default discovery skips nested dependency modules and supports quoted replacements', () => {
    const { go_dirs: _omitted, ...input } = raw;
    assert.deepEqual(normalConfig(mirror, input).go_dirs, ['.', 'services/server']);
  });
  checked('portable literal refusal', () => {
    for (const vendor_dir of ['/escape', '../escape', 'client/ven*', 'client/my vendor', 'client/ven?', 'client/[vendor]', 'kit/vendor', '.codex/vendor', 'client/dist/vendor', 'scripts', 'client/node_modules/vendor']) assert.throws(() => normalConfig(mirror, { ...raw, vendor_dir }));
    for (const go_dirs of [[], ['services/*'], ['services/my server'], ['/server'], ['../server'], ['services/server', 'services/server/'], ['client/dist']]) assert.throws(() => normalConfig(mirror, { ...raw, go_dirs }));
    assert.throws(() => normalConfig(mirror, { ...raw, npm_dir: '.codex/kit' }));
  });
  checked('Go discovery rejects a symlink before reading its go.mod', () => {
    const target = path.join(mirror, 'services/server/go.mod'), original = fs.readFileSync(target);
    fs.unlinkSync(target); fs.symlinkSync(path.join(source, 'services/server/go.mod'), target);
    const { go_dirs: _omitted, ...input } = raw;
    assert.throws(() => normalConfig(mirror, input)); fs.unlinkSync(target); fs.writeFileSync(target, original);
  });
  const metadata = { schema: 1, target: 'kit:sync', sha: 'a'.repeat(40), tree_sha256: 'b'.repeat(64), toolchain_digest: 'sha256:' + 'c'.repeat(64), config, config_sha256: hash(JSON.stringify(config)), command: { command: 'task', args: ['--silent', 'repo:kit-config'], exit_code: 0, duration_ms: 1, stdout_sha256: 'd'.repeat(64), stderr_sha256: hash('') } };
  const metadataPath = path.join(control, 'config-before.json'); fs.writeFileSync(metadataPath, JSON.stringify(metadata));
  const plan = () => run('python3', ['-I', '-', metadataPath, source, mirror, metadata.target, metadata.sha, metadata.tree_sha256, metadata.toolchain_digest, control], block('PY_METADATA'));
  checked('actual metadata generator guards both trees and keeps plan outside /work', () => {
    assert.equal(plan().status, 0); assert(!control.startsWith(mirror + path.sep));
  });
  const records = file => fs.readFileSync(path.join(control, file), 'utf8').split('\0').filter(Boolean);
  const files = records('file.paths'), trees = records('tree.paths'), patterns = records('sync.paths');
  checked('exact anchored permissions omit broad DEPS and XS', () => {
    assert(patterns.every(pattern => pattern.startsWith('/')));
    assert(patterns.includes('/client/packages/roedu-ui-*.tgz'));
    assert(patterns.includes('/services/server/third_party/webkit/***'));
    assert(patterns.includes('/third_party/webkit/***'));
    assert(!patterns.includes('/Taskfile.repo.yml') && !patterns.includes('/kit.lock.json') && !patterns.includes('/other/package.json'));
  });
  const snapshot = (root, apply, preserved = records('preserved.paths')) => {
    const result = run('python3', ['-I', '-', root, 'protected', config.vendor_dir, String(apply), String(files.length), String(trees.length), String(preserved.length), ...files, ...trees, ...preserved, '/none'], block('PY_SNAPSHOT'));
    assert.equal(result.status, 0, result.stderr); return result.stdout.trim();
  };
  checked('protected hashing includes owned Go dist members', () => {
    const before = snapshot(mirror, 0); put(mirror, 'services/server/third_party/webkit/sample/embedfs/dist/.keep', 'changed approved embed member');
    assert.notEqual(snapshot(mirror, 0), before);
  });
  checked('kit exemptions use exact vendor parent, not Python slash-crossing wildcards', () => {
    const before = snapshot(mirror, 1); put(mirror, 'client/packages/roedu-ui-folder/nested.tgz', 'not an owned archive');
    assert.notEqual(snapshot(mirror, 1), before); fs.rmSync(path.join(mirror, 'client/packages/roedu-ui-folder'), { recursive: true });
  });
  checked('hooks, workflows, kit inputs and unrelated vendor files remain protected', () => {
    for (const file of ['Taskfile.repo.yml', '.github/workflows/ci.yml', 'kit/CORE_TAG', '.codex/config.toml', 'ci.yml', 'client/packages/another-app.tgz']) {
      const before = snapshot(mirror, 1), original = fs.readFileSync(path.join(mirror, file)); put(mirror, file, 'attempted mutation');
      assert.notEqual(snapshot(mirror, 1), before, file); put(mirror, file, original);
    }
  });
  checked('source and runner symlink ancestors fail before return', () => {
    for (const root of [source, mirror]) {
      const target = path.join(root, 'client/packages'), held = target + '-held'; fs.renameSync(target, held); fs.symlinkSync(held, target);
      assert.notEqual(plan().status, 0); fs.unlinkSync(target); fs.renameSync(held, target);
    }
  });
  checked('owned archive directories cannot be deleted as stale files', () => {
    const target = path.join(source, 'client/packages/roedu-ui-directory.tgz'); fs.mkdirSync(target);
    assert.notEqual(plan().status, 0); fs.rmdirSync(target); assert.equal(plan().status, 0);
  });
  checked('closed UI phase remains canonical in capture and every target', () => {
    const oldSDK='client/packages/roedu-ui-0.3.0.tgz', sidecar=oldSDK+'.sha256', receipt='docs/original-ui-runtime.json';
    const sdkBytes=fs.readFileSync(path.join(source,oldSDK)), oldSidecar=fs.readFileSync(path.join(source,sidecar)), receiptBytes=Buffer.from('{"schema":1,"kind":"synthetic wrapper seal fixture only"}\n');
    const originalManifests=new Map([source,mirror].map(root=>[root,fs.readFileSync(path.join(root,'client/package.json'))]));
    for(const root of [source,mirror]) {put(root,'client/package.json',JSON.stringify({name:'fixture-app',dependencies:{'@roedu/ui':'file:packages/roedu-ui-0.3.0.tgz'}}));put(root,sidecar,hash(sdkBytes)+'  roedu-ui-0.3.0.tgz\n');put(root,receipt,receiptBytes);}
    const phase={mode:'staged-react',until:'S1-M2',legacy:{version:'0.3.0',archive_sha256:hash(sdkBytes),source_sha:'e'.repeat(40),receipt,receipt_sha256:hash(receiptBytes)}};
    const phased=normalConfig(mirror,{...raw,app:'cat_de_roman_esti',ui_adoption:phase});
    assert.deepEqual(phased.ui_adoption,phase);
    for(const patch of [{role:'core'}, {app:'another_app'}, {ui_adoption:null}, {ui_adoption:{mode:'active'}}, {ui_adoption:{...phase,extra:true}}, {ui_adoption:{...phase,until:'S1-M1'}}, {ui_adoption:{...phase,legacy:{...phase.legacy,version:'0.3.1'}}}, {ui_adoption:{...phase,legacy:{...phase.legacy,receipt:'dist/original.json'}}}, {ui_adoption:{...phase,legacy:{...phase.legacy,archive_sha256:'not-a-hash'}}}])assert.throws(()=>normalConfig(mirror,{...phased,...patch}));
    for(const receipt of ['embedfs/original.json','docs/original.tsbuildinfo','docs/original.tsbuildinfo.gz','docs/original.tsbuildinfo.br','client/packages/original.json'])assert.throws(()=>normalConfig(mirror,{...phased,ui_adoption:{...phase,legacy:{...phase.legacy,receipt}}}));
    const original={config:metadata.config,config_sha256:metadata.config_sha256,target:metadata.target};
    metadata.config=phased;metadata.config_sha256=hash(JSON.stringify(phased));
    try {
      for(const target of ['unit','full','gen','deps','build','baseline','e2e','perf','kit:sync']){metadata.target=target;fs.writeFileSync(metadataPath,JSON.stringify(metadata));assert.equal(plan().status,0,`phase metadata target ${target}`);}
      const preserved=records('preserved.paths');assert.deepEqual(preserved,[oldSDK,sidecar,receipt]);
      const originalSDK=fs.readFileSync(path.join(mirror,oldSDK)), before=snapshot(mirror,1,preserved);put(mirror,oldSDK,'attempted sealed SDK mutation');assert.notEqual(snapshot(mirror,1,preserved),before);assert.notEqual(plan().status,0);put(mirror,oldSDK,originalSDK);
      const manifest=path.join(mirror,'client/package.json'), manifestBytes=fs.readFileSync(manifest);put(mirror,'client/package.json',JSON.stringify({name:'fixture-app',dependencies:{'@roedu/ui':'file:packages/roedu-ui-1.0.1.tgz'}}));assert.notEqual(plan().status,0);fs.writeFileSync(manifest,manifestBytes);
      const originalReceipt=fs.readFileSync(path.join(mirror,receipt));put(mirror,receipt,'altered receipt');assert.notEqual(plan().status,0);put(mirror,receipt,originalReceipt);
      for(const root of [source,mirror]){const filename=path.join(root,receipt), held=filename+'-held';fs.renameSync(filename,held);fs.symlinkSync(held,filename);assert.notEqual(plan().status,0);fs.unlinkSync(filename);fs.renameSync(held,filename);}
      for(const root of [source,mirror])fs.unlinkSync(path.join(root,sidecar));assert.equal(plan().status,0);put(mirror,sidecar,hash(sdkBytes)+'\n');assert.notEqual(plan().status,0);fs.unlinkSync(path.join(mirror,sidecar));assert.equal(plan().status,0);
      metadata.config={...phased,ui_adoption:{...phase,legacy:{...phase.legacy,receipt_sha256:'0'.repeat(64)}}};metadata.config_sha256=hash(JSON.stringify(metadata.config));fs.writeFileSync(metadataPath,JSON.stringify(metadata));assert.notEqual(plan().status,0);
    } finally {
      metadata.config=original.config;metadata.config_sha256=original.config_sha256;metadata.target=original.target;fs.writeFileSync(metadataPath,JSON.stringify(metadata));
      for(const root of [source,mirror]){put(root,'client/package.json',originalManifests.get(root));put(root,sidecar,oldSidecar);fs.unlinkSync(path.join(root,receipt));}
      assert.equal(plan().status,0);
    }
  });
  fs.unlinkSync(path.join(mirror, 'client/packages/roedu-ui-0.3.0.tgz')); fs.unlinkSync(path.join(mirror, 'client/packages/roedu-ui-0.3.0.tgz.sha256'));
  put(mirror, 'client/packages/roedu-ui-1.0.0.tgz', 'new owned fixture bytes'); put(mirror, 'client/packages/roedu-ui-1.0.0.tgz.sha256', 'new owned sidecar bytes');
  put(mirror, 'client/package-lock.json', 'new configured lock'); put(mirror, 'other/package.json', 'not returned'); put(mirror, 'other/vendor/roedu-ui-0.3.0.tgz', 'not returned');
  fs.mkdirSync(path.join(source,'unrelated-empty'),{recursive:true});
  fs.mkdirSync(path.join(source,'client/packages/unrelated-empty'),{recursive:true});
  const syncReturn = () => run('python3',['-I','-',control,source,mirror],block('PY_KIT_RETURN'));
  checked('actual rsync returns owned members and deletes only owned stale archives', () => {
    const result = syncReturn(); assert.equal(result.status, 0, result.stderr);
    assert(!fs.existsSync(path.join(source, 'client/packages/roedu-ui-0.3.0.tgz')));
    assert(!fs.existsSync(path.join(source, 'client/packages/roedu-ui-0.3.0.tgz.sha256')));
    assert.equal(fs.readFileSync(path.join(source, 'client/packages/roedu-ui-1.0.0.tgz'), 'utf8'), 'new owned fixture bytes');
    assert.equal(fs.readFileSync(path.join(source, 'client/packages/another-app.tgz'), 'utf8'), 'unrelated vendor bytes');
    assert.equal(fs.readFileSync(path.join(source, 'services/server/third_party/webkit/sample/embedfs/dist/.keep'), 'utf8'), 'changed approved embed member');
    assert.equal(fs.readFileSync(path.join(source, 'other/package.json'), 'utf8'), 'unrelated manifest');
    assert.equal(fs.readFileSync(path.join(source, 'other/vendor/roedu-ui-0.3.0.tgz'), 'utf8'), 'unrelated suffix owner');
    assert(fs.statSync(path.join(source,'unrelated-empty')).isDirectory(),'unrelated root empty directory survives');
    assert(fs.statSync(path.join(source,'client/packages/unrelated-empty')).isDirectory(),'unrelated vendor empty directory survives');
  });
  checked('actual rsync second return is idempotent', () => {
    const before = snapshot(source, 0), result = syncReturn(); assert.equal(result.status, 0, result.stderr); assert.equal(snapshot(source, 0), before);
  });
  process.stdout.write(JSON.stringify({ schema: 1, check: 'wrapper-config', status: 'pass', checks, commands }) + '\n');
} catch (error) {
  process.stderr.write(error.message + '\n'); process.stdout.write(JSON.stringify({ schema: 1, check: 'wrapper-config', status: 'fail', checks, commands, reason: error.message }) + '\n'); process.exitCode = 1;
} finally { fs.rmSync(fixture, { recursive: true, force: true }); }
