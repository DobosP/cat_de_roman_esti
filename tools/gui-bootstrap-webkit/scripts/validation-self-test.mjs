import './bootstrap-cache.test.mjs';
import './go-module-audit.test.mjs';
import './ui-adoption-test.mjs';
import './ui-adoption-integration.test.mjs';
import { strict as assert } from 'node:assert';
import { test } from 'node:test';
import { readFileSync,mkdirSync,mkdtempSync,writeFileSync,rmSync,symlinkSync } from 'node:fs';
import { join,dirname } from 'node:path';
import { loadScope,sourceFindings,finish } from '../lint/lint-scope.mjs';
import { walkRepository,parseJSONC } from '../lint/validation-files.mjs';
import { checkVersions } from './versions-check.mjs';
import { graph } from './npm-lock-graph.mjs';
import { tarFile } from './core-lock-floor.mjs';
import { npmArchive, fixtureTar } from './kit-sync.mjs';
import { readTarGz as bootstrapArchive } from './kit-bootstrap.mjs';
import { gzipSync } from 'node:zlib';

const cases=JSON.parse(readFileSync(new URL('../testdata/validation/cases.json',import.meta.url)));
const digest='sha256:'+ '1'.repeat(64);
const fixtureLock={schema:2,core_tag:'core-v1.0',tools:[
  {tool:'node',kind:'runtime',scope:'core',version:'26.10.0',build_arg:'NODE_VERSION'},
  {tool:'npm',kind:'npm',scope:'core',version:'12.2.0'},
  {tool:'go',kind:'runtime',scope:'core',version:'1.27.1'},
  {tool:'good',kind:'npm',scope:'core',version:'1.2.3'},
  {tool:'example.com/good',kind:'gomod',scope:'core',version:'v1.2.3'},
  {tool:'react',kind:'npm',scope:'core',status:'banned',version:null},
  {tool:'react-dom',kind:'npm',scope:'core',status:'banned',version:null},
  {tool:'react-router',kind:'npm',scope:'core',status:'banned',version:null},
  {tool:'preact',kind:'npm',scope:'core',version:'11.0.0'},
  {tool:'framer-motion',kind:'npm',scope:'core',status:'transitive-only',version:'14.0.0',dependants:['motion']},
  {tool:'motion',kind:'npm',scope:'core',version:'14.0.0'},
  {tool:'fixture-base',kind:'image',scope:'core',version:'fixture-base:1',digest},
  {tool:'postgres',kind:'image',scope:'core',version:'16',image:'postgres:16-trixie',digest},
  {tool:'@playwright/test',kind:'npm',scope:'core',version:'1.63.0'},
  {tool:'playwright',kind:'npm',scope:'core',version:'1.63.0'},
  {tool:'playwright-image',kind:'image',scope:'core',version:'mcr.microsoft.com/playwright:v1.63.0-noble',digest},
],toolchain_image:{version:'fixture-toolchain:1',image_id:digest}};
const engines={node:'>=26.10.0',npm:'>=12.2.0'};
const config={role:'consumer',app:'fixture-app',npm_dir:'frontend/node_modules/@roedu/web-kit',vendor_dir:'frontend/vendor',go_dirs:['go']};

function fixture(t,extra={}) {
  const root=mkdtempSync('/scratch/_temp/validation-self-test-');t.after(()=>rmSync(root,{recursive:true,force:true}));
  const put=(name,value)=>{const p=join(root,name);mkdirSync(dirname(p),{recursive:true});writeFileSync(p,typeof value==='string'?value:JSON.stringify(value));};
  mkdirSync(join(root,config.npm_dir),{recursive:true});mkdirSync(join(root,config.vendor_dir),{recursive:true});
  const manifest={name:'fixture-app',version:'1.0.0',engines,dependencies:{good:'1.2.3'}};
  const rows={'':manifest,'node_modules/good':{version:'1.2.3'}};
  for(const [name,value] of Object.entries({
    'versions.lock.json':fixtureLock,'kit/CORE_TAG':'core-v1.0\n','frontend/package.json':manifest,
    'frontend/package-lock.json':{lockfileVersion:3,packages:rows},'frontend/src/clean.ts':cases.clean,
    '.nvmrc':'26.10.0\n','.npmrc':'save-exact=true\nengine-strict=true\n',
    'Dockerfile.toolchain':`ARG NODE_VERSION=26.10.0\nFROM fixture-base:1@${digest}\n`,
    'Dockerfile':`FROM fixture-base:1@${digest}\n`,
    '.gate.env':`TOOLCHAIN_IMAGE=fixture-toolchain:1\nTOOLCHAIN_DIGEST=${digest}\nPG_MAJOR=16\nGATE_DB_IMAGE=postgres:16-trixie@${digest}\n`,
    'go/go.mod':'module fixture/app\n\ngo 1.27.1\n\nrequire example.com/good v1.2.3\n',
    'go/go.sum':'example.com/good v1.2.3 h1:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\n',...extra,
  }))put(name,value);
  return {root,put};
}
const scope=(paths=['frontend/src/**'],rules=['banned-imports'])=>({schema:1,entries:[{paths,rules,reason:'Frozen legacy fixture pending removal',expires:'S1 M4'}]});
function scoped(t,extra={},s=scope()) {
  const f=fixture(t,{'frontend/src/old.jsx':cases.scoped,'lint/scope.json':s,...extra});
  const {files}=walkRepository(f.root,config),packages=new Set(['frontend']);
  const entries=new Map(fixtureLock.tools.map(e=>[e.tool,e]));
  return {...f,files,packages,entries,scope:loadScope(f.root,config,files,packages)};
}

test('narrow scopes retain exact legacy evidence and unscoped sibling failures',t=> {
  const f=scoped(t,{'frontend/other/new.mts':cases.unscoped});
  const report=finish(sourceFindings(f.root,f.files,f.entries),f.scope,f.packages);
  assert.equal(report.status,'fail');assert.equal(report.reason,'legacy-pending');
  assert(report.errors.some(e=>e.paths.includes('frontend/other/new.mts')));
  assert(report.legacy_pending.length>=4);
  for(const item of report.legacy_pending)assert.deepEqual(Object.keys(item).sort(),['expires','paths','rule','source','tool_or_import']);
  assert(report.legacy_pending.every(e=>e.source==='lint/scope.json'&&e.expires==='S1 M4'));
});
test('root whole-package traversal kit-shim and core scopes fail closed',t=> {
  for(const paths of [['**'],['frontend/**'],['../src/**'],['frontend\\src\\**'],['frontend/kit-shims/**'],['frontend/*']]) {
    const f=fixture(t,{'lint/scope.json':scope(paths),'frontend/src/old.jsx':cases.scoped});
    const {files}=walkRepository(f.root,config);assert.throws(()=>loadScope(f.root,config,files,new Set(['frontend'])));
  }
  const f=fixture(t,{'lint/scope.json':{schema:1,entries:[]}});
  assert.throws(()=>loadScope(f.root,{...config,role:'core'},[],new Set(['frontend'])),/role core/);
});
test('stale entries missing reason expiry and unsupported rules fail',t=> {
  const f=scoped(t,{'frontend/src/old.jsx':cases.clean});
  const report=finish(sourceFindings(f.root,f.files,f.entries),f.scope,f.packages);
  assert.equal(report.status,'fail');assert(report.errors.some(e=>e.tool_or_import==='stale entry'));
  for(const change of [{reason:''},{expires:''},{rules:['inline-style']}]) {
    f.put('lint/scope.json',{schema:1,entries:[{...scope().entries[0],...change}]});
    assert.throws(()=>loadScope(f.root,config,f.files,f.packages));
  }
});
test('scope never suppresses v11 attributes unsafe URL or disable checks',t=> {
  const f=scoped(t,{'frontend/src/old.jsx':cases.v11,'frontend/src/disable.ts':cases.inlineDisable,'go/view.go':'package view\nfunc x(){ _ = templ.SafeURL("/") }'});
  const report=finish(sourceFindings(f.root,f.files,f.entries),f.scope,f.packages);
  for(const rule of ['forwardRef','inline-style','inline-handler','inline-disable','templ-SafeURL'])assert(report.errors.some(e=>e.rule===rule),rule);
  assert(report.legacy_pending.some(e=>e.rule==='banned-imports'));
});
test('escaped static imports are findings and string examples remain clean',t=> {
  const f=scoped(t,{'frontend/src/old.jsx':cases.escaped});
  const findings=sourceFindings(f.root,f.files,f.entries);
  assert(findings.some(e=>e.tool_or_import==='react'));assert(!findings.some(e=>e.paths.includes('frontend/src/clean.ts')));
});
test('source traversal rejects symlinks and keeps production templates',t=> {
  const f=fixture(t,{'embedfs/templates/page.html':'<div style="color:red">x</div>'});
  const walked=walkRepository(f.root,config);assert(walked.files.includes('embedfs/templates/page.html'));
  symlinkSync(join(f.root,'frontend/src'),join(f.root,'escaped'));assert.throws(()=>walkRepository(f.root,config),/symlink/);
});
test('workspace ownership reaches shared hoisted lock nodes without sibling exemption',t=> {
  const rows={'':{name:'root'},'frontend':{dependencies:{react:'18.0.0'}},'admin':{dependencies:{react:'18.0.0'}},'node_modules/react':{version:'18.0.0'}};
  const g=graph(rows,'.',new Set(['.','frontend','admin']));
  assert.deepEqual([...g.owners.get('node_modules/react')].sort(),['admin','frontend']);
  const f=scoped(t,{'admin/package.json':{name:'admin'},'admin/src/new.ts':cases.unscoped});
  const report=finish([
    {rule:'banned-packages',tool_or_import:'react',paths:['package-lock.json#node_modules/react'],package_dir:'frontend',scopable:true},
    {rule:'banned-packages',tool_or_import:'react',paths:['package-lock.json#node_modules/react'],package_dir:'admin',scopable:true},
  ],loadScope(f.root,config,f.files,new Set(['frontend','admin'])),new Set(['frontend','admin']));
  // This scope covers imports only; no blanket lock exemption is inferred.
  assert.equal(report.legacy_pending.length,0);assert.equal(report.status,'fail');
  f.put('lint/scope.json',scope(['frontend/src/**'],['banned-packages']));
  const next=finish([
    {rule:'banned-packages',tool_or_import:'react',paths:['package-lock.json#node_modules/react'],package_dir:'frontend',scopable:true},
    {rule:'banned-packages',tool_or_import:'react',paths:['package-lock.json#node_modules/react'],package_dir:'admin',scopable:true},
  ],loadScope(f.root,config,f.files,new Set(['frontend','admin'])),new Set(['frontend','admin']));
  assert.equal(next.legacy_pending.length,1);assert.equal(next.errors.length,1);
});
test('full versions check exactness mutations legacy package scopes and TS7 isolation',async t=> {
  const f=fixture(t);let result=await checkVersions({root:f.root,config,floor:fixtureLock});assert.equal(result.status,'pass',JSON.stringify(result.errors));
  const m={name:'fixture-app',version:'1.0.0',engines,dependencies:{good:'1.2.3',react:'18.0.0'}};
  f.put('frontend/package.json',m);f.put('frontend/package-lock.json',{lockfileVersion:3,packages:{'':m,'node_modules/good':{version:'1.2.3'},'node_modules/react':{version:'18.0.0'}}});
  f.put('frontend/src/old.jsx',cases.unscoped);f.put('lint/scope.json',scope(['frontend/src/**'],['banned-imports','banned-packages','compat-paths']));f.put('frontend/tsconfig.json',cases.compat);
  result=await checkVersions({root:f.root,config,floor:fixtureLock});assert.equal(result.status,'pass',JSON.stringify(result.errors));assert.equal(result.reason,'legacy-pending');assert(result.legacy_pending.some(e=>e.rule==='compat-paths'));
  f.put('frontend/tsconfig.json',cases.unsafeCompat);result=await checkVersions({root:f.root,config,floor:fixtureLock});assert.equal(result.status,'fail');assert(result.errors.some(e=>e.rule==='tsconfig:frontend/tsconfig.json'));assert(result.legacy_pending.length>0);
  f.put('frontend/tsconfig.json',cases.compat);m.dependencies.good='^1.2.3';f.put('frontend/package.json',m);result=await checkVersions({root:f.root,config,floor:fixtureLock});assert.equal(result.status,'fail');assert(result.errors.some(e=>e.tool_or_import.includes('nonexact')));
});
test('full checker rejects core pin changes and transitive-only direct dependencies',async t=> {
  const f=fixture(t);const changed=structuredClone(fixtureLock);changed.tools.find(e=>e.tool==='good').version='1.0.0';f.put('versions.lock.json',changed);
  let result=await checkVersions({root:f.root,config,floor:fixtureLock});assert.equal(result.status,'fail');assert(result.errors.some(e=>e.rule==='core-floor'));
  f.put('versions.lock.json',fixtureLock);const m={name:'fixture-app',version:'1.0.0',engines,dependencies:{'framer-motion':'14.0.0'}};f.put('frontend/package.json',m);f.put('frontend/package-lock.json',{packages:{'':m,'node_modules/framer-motion':{version:'14.0.0'}}});
  result=await checkVersions({root:f.root,config,floor:fixtureLock});assert.equal(result.status,'fail');assert(result.errors.some(e=>e.tool_or_import.includes('transitive-only')));
});
test('multiple package locks retain only the matching package legacy scope',async t=> {
  const f=fixture(t),m={name:'legacy',version:'1.0.0',engines,dependencies:{react:'18.0.0'}};
  for(const dir of ['frontend','admin']) {
    f.put(dir+'/package.json',m);f.put(dir+'/package-lock.json',{packages:{'':m,'node_modules/react':{version:'18.0.0'}}});
    f.put(dir+'/src/code.jsx',dir==='frontend'?cases.unscoped:cases.clean);
  }
  f.put('lint/scope.json',scope(['frontend/src/**'],['banned-imports','banned-packages']));
  const result=await checkVersions({root:f.root,config,floor:fixtureLock});
  assert.equal(result.status,'fail');assert.equal(result.reason,'legacy-pending');
  assert(result.legacy_pending.some(e=>e.paths.some(p=>p.startsWith('frontend/package-lock.json'))));
  assert(!result.legacy_pending.some(e=>e.paths.some(p=>p.startsWith('admin/'))));
  assert(result.errors.some(e=>e.rule==='banned-packages'&&e.paths.some(p=>p.startsWith('admin/package-lock.json'))));
});
test('shared workspace lock cannot borrow a sibling package scope',async t=> {
  const f=fixture(t),front={name:'frontend',version:'1.0.0',engines,dependencies:{react:'18.0.0'}},admin={...front,name:'admin'};
  const rootManifest={name:'workspace-root',version:'1.0.0',engines,workspaces:['frontend','admin']};
  f.put('package.json',rootManifest);f.put('frontend/package.json',front);f.put('admin/package.json',admin);
  rmSync(join(f.root,'frontend/package-lock.json'));
  f.put('package-lock.json',{packages:{'':rootManifest,frontend:front,admin,'node_modules/react':{version:'18.0.0'},'node_modules/frontend':{link:true,resolved:'frontend'},'node_modules/admin':{link:true,resolved:'admin'}}});
  f.put('frontend/src/old.jsx',cases.unscoped);f.put('admin/src/new.ts',cases.clean);
  f.put('lint/scope.json',scope(['frontend/src/**'],['banned-imports','banned-packages']));
  const result=await checkVersions({root:f.root,config,floor:fixtureLock});
  assert.equal(result.status,'fail');
  assert(result.errors.some(e=>e.rule==='banned-packages'&&e.package_dir==='admin'));
  assert(result.legacy_pending.some(e=>e.rule==='banned-packages'&&e.paths.includes('package-lock.json#node_modules/react')));
});
test('JSONC strings and npm archive root/link rejection do not create bypasses',()=> {
  assert.equal(parseJSONC('{/*c*/"x":"value,}","compilerOptions":{},}').x,'value,}');
  assert.throws(()=>tarFile(gzipSync(Buffer.alloc(1024)),'package/versions.lock.json'),/lacks/);
});

test('npm bootstrap and version-floor archives reject Python caches and retain Python sources',()=> {
  const python=Buffer.from('# owning Python source must remain byte-identical\n');
  const kit=new Map([
    ['package/package.json',Buffer.from(JSON.stringify({name:'@roedu/web-kit',version:'0.1.1',exports:{'.':'./scripts/kit-sync.mjs'}}))],
    ['package/scripts/kit-sync.mjs',Buffer.from('export const fixture=true;\n')],
    ['package/versions.lock.json',Buffer.from('{}')],
    ['package/lint/check_docs.py',python],
  ]);
  const archive=files=>gzipSync(fixtureTar(files));
  const clean=archive(kit);
  assert.deepEqual(npmArchive(clean,'@roedu/web-kit','roedu-web-kit-0.1.1.tgz').entries.get('package/lint/check_docs.py').data,python);
  assert.deepEqual(bootstrapArchive(clean).get('package/lint/check_docs.py').data,python);
  assert.deepEqual(tarFile(clean,'package/lint/check_docs.py'),python);
  const ui=new Map([
    ['package/package.json',Buffer.from(JSON.stringify({name:'@roedu/ui',version:'1.0.1',exports:{'.':'./dist/index.js'}}))],
    ['package/dist/index.js',Buffer.from('export const fixture=true;\n')],
  ]);
  for(const suffix of ['__pycache__/fixture.py','nested/__pycache__/fixture.pyc','stale.pyc','nested/stale.pyo','stale.pyc.gz','nested/stale.pyo.br','nested/STALE.PYC']) {
    const dirty=archive(new Map([...kit,[`package/lint/${suffix}`,Buffer.from('runtime cache')]]));
    assert.throws(()=>npmArchive(dirty,'@roedu/web-kit','roedu-web-kit-0.1.1.tgz'),/Excluded Python bytecode\/cache/);
    assert.throws(()=>bootstrapArchive(dirty),/Excluded Python bytecode\/cache/);
    assert.throws(()=>tarFile(dirty,'package/versions.lock.json'),/Excluded Python bytecode\/cache/);
    assert.throws(()=>npmArchive(archive(new Map([...ui,[`package/dist/${suffix}`,Buffer.from('runtime cache')]])),'@roedu/ui','roedu-ui-1.0.1.tgz'),/Excluded Python bytecode\/cache/);
    assert.throws(()=>bootstrapArchive(archive(new Map([[`web-kit/tokens/${suffix}`,Buffer.from('runtime cache')]]))),/Excluded Python bytecode\/cache/);
  }
});


test('same-repo Go audit integrates recursive identity and preserves exact consumer floors',async t=> {
  const f=fixture(t,{
    'go/go.mod':'module fixture/app\n\ngo 1.27.1\n\nrequire example.com/auth v0.0.0\nreplace example.com/auth => ../shared/auth\n',
    'shared/auth/go.mod':'module example.com/auth\n\ngo 1.27.1\n\nrequire example.com/good v1.2.3\n',
    'shared/auth/go.sum':'example.com/good v1.2.3 h1:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\n',
  });
  const before=structuredClone(config),first=await checkVersions({root:f.root,config,floor:fixtureLock});
  assert.equal(first.status,'pass',JSON.stringify(first.errors));assert.equal(first.counts.go_receivers,1);assert.equal(first.counts.go_modules,2);
  assert.deepEqual(first.go_audit.receivers,['go']);assert.equal(first.go_audit.local_edges[0].target,'shared/auth');assert.deepEqual(config,before);
  const second=await checkVersions({root:f.root,config,floor:fixtureLock});assert.deepEqual(second.go_audit,first.go_audit);
  f.put('shared/auth/go.mod','module example.com/auth\n\ngo 1.27.1\n\nrequire example.com/good v1.2.2\n');
  const refused=await checkVersions({root:f.root,config,floor:fixtureLock});assert.equal(refused.status,'fail');assert(refused.errors.some(item=>item.rule==='go-modules'&&item.tool_or_import.includes('exact Go version differs')));
});
