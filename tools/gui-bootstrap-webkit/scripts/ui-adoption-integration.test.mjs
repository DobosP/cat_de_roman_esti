// Synthetic protocol fixtures only; these never qualify Cat's original runtime.
import * as fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createHash } from 'node:crypto';
import { syncKit,checkKit,loadKit,assertFrozenConfig,requireActiveUi } from './kit-sync.mjs';
import { checkVersions } from './versions-check.mjs';
import { checkAst } from './ast-check.mjs';
import { makeUiAdoptionFixture,fixtureArchive,fixtureHash } from './ui-adoption-fixture.mjs';

const json=value=>Buffer.from(JSON.stringify(value,null,2)+'\n');
const sri=bytes=>'sha512-'+createHash('sha512').update(bytes).digest('base64');
function snapshot(root) {
  const rows=[];
  function walk(dir) {for(const name of fs.readdirSync(dir).sort()){const file=path.join(dir,name),stat=fs.lstatSync(file),relative=path.relative(root,file);if(stat.isDirectory()){rows.push([relative,'directory',stat.mode&0o777]);walk(file);}else rows.push([relative,stat.mode&0o777,fixtureHash(fs.readFileSync(file))]);}}
  walk(root);return rows;
}
async function fixture(fn) {
  assert.equal(process.platform,'linux');assert.equal(process.cwd(),'/work');
  const base='/scratch/_temp';assert.equal(fs.realpathSync(base),base);
  const root=fs.mkdtempSync(path.join(base,'synthetic-ui-sync-'));
  try {
    const f=makeUiAdoptionFixture(root),core=JSON.parse(f.bundle.kitFiles.get('package/versions.lock.json'));
    core.tools.push({tool:'node',kind:'runtime',scope:'core',version:'26.10.0'},{tool:'npm',kind:'npm',scope:'core',version:'12.2.0'},{tool:'go',kind:'runtime',scope:'core',version:'1.27.1'});
    f.bundle.kitFiles.set('package/versions.lock.json',json(core));f.bundle.archives.set(f.bundle.kitName,fixtureArchive(f.bundle.kitFiles));
    for(const [name,bytes] of f.bundle.archives)f.put('kit/'+name,bytes);
    f.put('kit/SHA256SUMS',[...f.bundle.archives].map(([name,bytes])=>`${fixtureHash(bytes)}  ${name}\n`).join(''));
    f.put('versions.lock.json',json(core));f.put('.gate.env',f.bundle.kitFiles.get('package/templates/.gate.env'));
    f.put('Taskfile.repo.yml','original synthetic repo hooks\n');
    f.put('server/go.mod','module example.test/synthetic-cat-server\n\ngo 1.27.1\n\nrequire github.com/DobosP/roedu-ui/web-kit v0.0.0\n\nreplace github.com/DobosP/roedu-ui/web-kit => ./third_party/webkit\n');
    fs.mkdirSync(path.join(root,f.config.npm_dir),{recursive:true});
    // Original receipt remains Framer12. Live canonical ownership is Motion14.
    f.manifest.dependencies.motion='14.0.0';delete f.manifest.dependencies['framer-motion'];
    f.lock.packages['']=structuredClone(f.manifest);f.lock.packages['node_modules/motion']={version:'14.0.0',dependencies:{'framer-motion':'14.0.0'}};f.lock.packages['node_modules/framer-motion']={version:'14.0.0'};
    f.put(f.manifestPath,json(f.manifest));f.put(f.lockPath,json(f.lock));f.installSdk(f.old);
    let calls=0;
    f.deps=(_root,target)=>{
      assert.equal(target,'deps');calls++;
      const manifest=JSON.parse(fs.readFileSync(path.join(root,f.manifestPath))),selected=manifest.dependencies['@roedu/ui'].endsWith(f.selected.filename)?f.selected:f.old;
      const lock=JSON.parse(fs.readFileSync(path.join(root,f.lockPath)));lock.packages['']=structuredClone(manifest);
      lock.packages['node_modules/@roedu/ui']={version:selected.manifest.version,resolved:manifest.dependencies['@roedu/ui'],integrity:sri(selected.data),...(selected.manifest.dependencies?{dependencies:selected.manifest.dependencies}:{}),peerDependencies:selected.manifest.peerDependencies};
      lock.packages['node_modules/@roedu/web-kit']={version:'0.1.1',resolved:manifest.devDependencies['@roedu/web-kit'],integrity:sri(f.bundle.archives.get(f.bundle.kitName))};
      f.put(f.lockPath,json(lock));return {status:0,stdout:'',stderr:''};
    };
    f.calls=()=>calls;return await fn(f);
  } finally {fs.rmSync(root,{recursive:true,force:true});}
}

test('synthetic real sync preserves sealed original SDK, stages selected UI/kit/Go and repeats identically',()=>fixture(f=>{
  f.put('frontend/vendor/unrelated.txt','preserve');fs.mkdirSync(path.join(f.root,'frontend/vendor/unrelated-empty'));
  f.put('frontend/vendor/roedu-ui-0.2.0.tgz','owned stale archive');
  const old=fs.readFileSync(path.join(f.root,'frontend/vendor/roedu-ui-0.3.0.tgz')),receipt=fs.readFileSync(path.join(f.root,f.config.ui_adoption.legacy.receipt));
  const result=syncKit(f.root,f.config,{depsRunner:f.deps});assert.equal(result.status,'pass');assert.equal(result.ui_adoption.status,'pending');
  assert.deepEqual(fs.readFileSync(path.join(f.root,'frontend/vendor/roedu-ui-0.3.0.tgz')),old);assert.deepEqual(fs.readFileSync(path.join(f.root,f.config.ui_adoption.legacy.receipt)),receipt);
  assert.equal(fs.existsSync(path.join(f.root,'frontend/vendor/roedu-ui-0.3.0.tgz.sha256')),false);assert.equal(fs.existsSync(path.join(f.root,'frontend/vendor/roedu-ui-0.2.0.tgz')),false);
  assert.equal(fs.readFileSync(path.join(f.root,'frontend/vendor/unrelated.txt'),'utf8'),'preserve');assert.ok(fs.statSync(path.join(f.root,'frontend/vendor/unrelated-empty')).isDirectory());
  assert.deepEqual(fs.readFileSync(path.join(f.root,'frontend/vendor/'+f.selected.filename)),f.selected.data);assert.deepEqual(fs.readFileSync(path.join(f.root,'frontend/vendor/'+f.bundle.kitName)),f.bundle.archives.get(f.bundle.kitName));
  assert.ok(fs.readFileSync(path.join(f.root,'server/go.mod'),'utf8').includes('v0.0.0-core-v1.1'));assert.deepEqual(fs.readFileSync(path.join(f.root,'server/third_party/webkit/tokens/fixture.go')),f.bundle.goFiles.get('web-kit/tokens/fixture.go'));
  assert.equal(fs.readFileSync(path.join(f.root,'Taskfile.repo.yml'),'utf8'),'original synthetic repo hooks\n');
  const before=snapshot(f.root),repeat=syncKit(f.root,f.config,{depsRunner:f.deps});assert.deepEqual(repeat.changed,[]);assert.deepEqual(snapshot(f.root),before);
  assert.equal(checkKit(f.root,f.config).ui_adoption.status,'pending');assert.throws(()=>requireActiveUi(f.root,f.config),/active UI is required/);
  const active={...f.config};delete active.ui_adoption;
  syncKit(f.root,active,{depsRunner:f.deps});assert.equal(fs.existsSync(path.join(f.root,'frontend/vendor/roedu-ui-0.3.0.tgz')),false);assert.equal(checkKit(f.root,active).ui_adoption,undefined);
  // Lock-only sync must not manufacture an installed/M2 proof.
  assert.equal(JSON.parse(fs.readFileSync(path.join(f.root,'frontend/node_modules/@roedu/ui/package.json'))).version,'0.3.0');
  assert.throws(()=>requireActiveUi(f.root,active),error=>/installed UI/.test(error.message)||(/^Missing input: /.test(error.message)&&error.message.includes('frontend/node_modules/@roedu/ui/')));
  const activeInstalled=f.activate();assert.equal(requireActiveUi(f.root,activeInstalled).status,'pass');
  const after=snapshot(f.root),calls=f.calls();assert.throws(()=>syncKit(f.root,f.config,{depsRunner:f.deps}),/must already be exactly/);assert.equal(f.calls(),calls);assert.deepEqual(snapshot(f.root),after);
}));

test('synthetic corrupted SDK/phase/frozen configuration refuse before any sync write',()=>fixture(f=>{
  const corrupted={...f.config,ui_adoption:{...f.config.ui_adoption,until:'S1-M3'}};
  const before=snapshot(f.root);assert.throws(()=>syncKit(f.root,corrupted,{depsRunner:f.deps}),/phase/);assert.deepEqual(snapshot(f.root),before);assert.equal(f.calls(),0);
  const capture={schema:1,target:'kit:sync',sha:'a'.repeat(40),tree_sha256:'b'.repeat(64),toolchain_digest:'sha256:'+'c'.repeat(64),config:f.config,config_sha256:fixtureHash(JSON.stringify(f.config))};
  f.put('.gate/kit-sync/wrapper-kit-config.json',json(capture));assert.deepEqual(assertFrozenConfig(f.root,f.config),f.config);
  const changed=structuredClone(f.config);changed.ui_adoption.legacy.source_sha='d'.repeat(40);assert.throws(()=>syncKit(f.root,changed,{depsRunner:f.deps}),/frozen wrapper configuration/);assert.equal(f.calls(),0);
  f.put('frontend/vendor/roedu-ui-0.3.0.tgz','corrupted sealed archive');const snapshotCorrupt=snapshot(f.root);assert.throws(()=>syncKit(f.root,f.config,{depsRunner:f.deps}),/SDK SHA256 differs/);assert.deepEqual(snapshot(f.root),snapshotCorrupt);assert.equal(f.calls(),0);
}));

test('synthetic staged UI grants no dependency graph or actual AST style exemption',()=>fixture(async f=>{
  syncKit(f.root,f.config,{depsRunner:f.deps});
  f.put('frontend/src/unsafe.tsx','export const Unsafe = () => <div style={{color:"red"}}>Unsafe</div>;\n');
  f.put('lint/scope.json',json({schema:1,entries:[{paths:['frontend/src/unsafe.tsx'],rules:['banned-packages'],reason:'Synthetic original React declaration through migration',expires:'S1-M2'}]}));
  const ast=await checkAst({root:f.root,config:f.config});assert.equal(ast.status,'fail');assert.ok(ast.legacy_pending.some(finding=>finding.rule==='banned-packages'&&finding.tool_or_import==='react'));assert.ok(ast.errors.some(error=>error.rule==='inline-style'&&error.paths.some(name=>name.endsWith('unsafe.tsx'))));
  const manifest=JSON.parse(fs.readFileSync(path.join(f.root,f.manifestPath)));manifest.dependencies['framer-motion']='12.42.2';f.put(f.manifestPath,json(manifest));
  const lock=JSON.parse(fs.readFileSync(path.join(f.root,f.lockPath)));lock.packages['']=structuredClone(manifest);lock.packages['node_modules/framer-motion'].version='12.42.2';f.put(f.lockPath,json(lock));
  const versions=await checkVersions({root:f.root,config:f.config});assert.equal(versions.status,'fail');assert.equal(versions.ui_adoption.status,'pending');assert.ok(versions.errors.some(error=>/framer-motion/.test(error.tool_or_import)));
}));
