// Runner-only qualification of actual UI/kit packages and strict consumers.
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { chmodSync,copyFileSync,existsSync,lstatSync,mkdirSync,mkdtempSync,readFileSync,readdirSync,realpathSync,rmSync,writeFileSync } from 'node:fs';
import { basename,dirname,join,relative,resolve,sep } from 'node:path';
import { pathToFileURL,fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';
import { INVENTORY } from './vite-inventory.mjs';
import { npmArchive,isPythonBytecodePath } from './kit-sync.mjs';
import { packageSource } from './core-task.mjs';

const root=resolve(fileURLToPath(new URL('../../',import.meta.url)));
const report={schema:1,check:'npm-distribution',status:'fail',packages:[],commands:[],proofs:[],installed_files:[],dependency_provenance:[]};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const sri=bytes=>'sha512-'+createHash('sha512').update(bytes).digest('base64');
const fail=message=>{throw new Error(message);};
const assert=(condition,message)=>{if(!condition)fail(message);};
const portable=value=>value.split(sep).join('/');
let scratch,rawDirectory;
const target=process.argv[2]??'unit';
assert(['unit','full'].includes(target),'distribution evidence target must be unit or full');
const sourceHashes=new Map();
const injectedPythonCaches=[],createdPythonCacheDirectories=[];
function reservePythonCache(relativePath) {
  const owner=join(root,'web-kit'),file=join(owner,relativePath);
  assert(isPythonBytecodePath(relativePath)&&file.startsWith(owner+sep)&&!relativePath.split('/').includes('..'),'probe must be an owned Python-cache path');
  let directory=owner;
  for(const name of portable(relative(owner,dirname(file))).split('/').filter(Boolean)) {
    directory=join(directory,name);
    if(existsSync(directory))assert(lstatSync(directory).isDirectory()&&!lstatSync(directory).isSymbolicLink(),'cache probe ancestor must be a real directory');
    else {mkdirSync(directory);createdPythonCacheDirectories.push(directory);}
  }
  assert(!existsSync(file),'cache probe must never overwrite existing source/cache bytes');
  const entry={file,path:relativePath};injectedPythonCaches.push(entry);return entry;
}
function preservePythonCacheEvidence(entry,kind) {
  assert(existsSync(entry.file)&&lstatSync(entry.file).isFile()&&!lstatSync(entry.file).isSymbolicLink(),'actual Python cache probe file missing');
  const bytes=readFileSync(entry.file),artifact=retainRaw(`python-cache-probe-${injectedPythonCaches.indexOf(entry)}.bin`,bytes);
  entry.sha256=sha(bytes);entry.kind=kind;entry.bytes=bytes.length;entry.artifact=artifact;
  report.python_cache_probes??=[];report.python_cache_probes.push({path:entry.path,kind,bytes:entry.bytes,sha256:entry.sha256,artifact});
}
function cleanupInjectedPythonCaches() {
  const removed=[];
  for(const entry of [...injectedPythonCaches].reverse())if(existsSync(entry.file)) {
    assert(lstatSync(entry.file).isFile()&&!lstatSync(entry.file).isSymbolicLink()&&(!entry.sha256||sha(readFileSync(entry.file))===entry.sha256),'refuse cleanup of changed or foreign cache probe');
    rmSync(entry.file);removed.push(entry.path);
  }
  for(const directory of [...createdPythonCacheDirectories].reverse())if(existsSync(directory)) {
    assert(lstatSync(directory).isDirectory()&&!lstatSync(directory).isSymbolicLink(),'refuse cleanup of changed cache probe directory');
    if(readdirSync(directory).length===0)rmSync(directory,{recursive:true});
  }
  assert(injectedPythonCaches.every(entry=>!existsSync(entry.file)),'injected source cache debris remains');
  if(injectedPythonCaches.length)report.proofs.push({name:'actual-python-cache-probe-source-cleanup',status:'pass',removed:removed.sort(),retained_raw_artifacts:injectedPythonCaches.filter(entry=>entry.artifact).map(entry=>entry.artifact)});
}

function retainRaw(name,bytes) {
  assert(/^[a-z0-9.-]+$/.test(name),'unsafe raw evidence name');
  if(!rawDirectory){const parent=join(root,'.gate',target);for(const directory of [join(root,'.gate'),parent]){if(existsSync(directory))assert(lstatSync(directory).isDirectory()&&!lstatSync(directory).isSymbolicLink(),'raw evidence directory must be regular');else mkdirSync(directory);}rawDirectory=mkdtempSync(join(parent,'npm-distribution-raw-'));}
  const file=join(rawDirectory,name);writeFileSync(file,bytes,{flag:'wx',mode:0o600});const evidence={path:portable(relative(root,file)),sha256:sha(bytes),bytes:Buffer.byteLength(bytes)};
  report.raw_artifacts??=[];report.raw_artifacts.push(evidence);return evidence;
}

function list(directory) {
  const files=[];
  function walk(dir) {
    for(const name of readdirSync(dir).sort()) {
      const p=join(dir,name),s=lstatSync(p);
      if(s.isSymbolicLink())fail(`distribution source/package symlink refused: ${p}`);
      if(s.isDirectory())walk(p);else if(s.isFile())files.push(p);else fail(`distribution nonregular entry: ${p}`);
    }
  }
  walk(directory);return files;
}
function command(executable,args,cwd,expected=0) {
  const env={...process.env};delete env.NODE_PATH;delete env.TS_NODE_PROJECT;delete env.TS_NODE_COMPILER_OPTIONS;
  const r=spawnSync(executable,args,{cwd,env,encoding:'utf8',maxBuffer:64*1024*1024,timeout:600000});
  const stdout=r.stdout??'',stderr=r.stderr??'';
  const ordinal=String(report.commands.length).padStart(3,'0'),stdoutFile=retainRaw(`${ordinal}.stdout.log`,stdout),stderrFile=retainRaw(`${ordinal}.stderr.log`,stderr);
  report.commands.push({executable,args,cwd,exit_code:r.status,signal:r.signal,stdout_sha256:sha(stdout),stderr_sha256:sha(stderr),stdout_file:stdoutFile.path,stderr_file:stderrFile.path,...(r.status!==expected?{stdout_tail:stdout.slice(-20000),stderr_tail:stderr.slice(-20000)}:{})});
  if(r.error)fail(r.error.message);
  if(expected===0)assert(r.status===0,`${executable} failed with exit ${r.status}`);else assert(r.status!==0,`${executable} unexpectedly accepted invalid fixture`);
  return {stdout,stderr,status:r.status};
}
function readJSON(p){return JSON.parse(readFileSync(p,'utf8'));}
function npm(args,cwd){return command('npm',args,cwd).stdout;}
function pack(owner,destination,sourceOwner=owner,purpose='consumer') {
  const manifest=readJSON(join(owner,'package.json'));
  const data=JSON.parse(npm(['pack',owner,'--json','--ignore-scripts','--workspaces=false','--pack-destination',destination],owner));
  // npm 12 emits an owner-keyed object. Keep the actual output for diagnosis;
  // reject every extra owner before accessing the one explicitly packed owner.
  report.pack_observations??=[];report.pack_observations.push({owner:portable(relative(root,sourceOwner))||'.',purpose,output:data});
  assert(data&&typeof data==='object'&&!Array.isArray(data)&&Object.keys(data).length===1&&Object.hasOwn(data,manifest.name),'actual npm12 pack must return exactly the owning package key');
  const result=data[manifest.name];
  assert(result&&result.name===manifest.name&&result.version===manifest.version,'actual pack result differs from the explicitly selected owner');
  assert(typeof result.filename==='string'&&result.filename===`${manifest.name.replace('@','').replace('/','-')}-${manifest.version}.tgz`,'actual owner tarball filename differs');
  const path=join(destination,result.filename),bytes=readFileSync(path);
  assert(result.name===manifest.name&&result.version===manifest.version&&result.integrity===sri(bytes),'actual owner/pack integrity differs');
  const info={owner:portable(relative(root,sourceOwner))||'.',name:result.name,version:result.version,filename:result.filename,sha256:sha(bytes),integrity:result.integrity,files:result.files.map(f=>f.path).sort()};
  // Qualify these exact npm-produced UI/kit bytes through the consumer's real
  // archive policy before installation, without a fabricated release or Go archive.
  const parsed=npmArchive(bytes,manifest.name,result.filename),archiveManifest=parsed.entries.get('package/package.json');
  assert(archiveManifest?.type==='file','actual owner TGZ has no regular package manifest');
  assert(!info.files.some(path=>/\.tsbuildinfo(?:\.(?:gz|br))?$/.test(path))&&![...parsed.entries.keys()].some(path=>/\.tsbuildinfo(?:\.(?:gz|br))?$/.test(path)),'actual owner TGZ contains compiler build state');
  assert(!info.files.some(isPythonBytecodePath)&&![...parsed.entries.keys()].some(isPythonBytecodePath),'actual owner TGZ contains Python cache/bytecode');
  const packedManifest=parsed.manifest;
  report.proofs.push({name:'actual-npm-pack-through-kit-sync-parser',status:'pass',owner:manifest.name,filename:result.filename,archive_sha256:sha(bytes),integrity:result.integrity,entries:parsed.entries.size,testdata_files:[...parsed.entries.keys()].filter(name=>name.startsWith('package/testdata/')).sort()});
  report.proofs.push({name:'actual-npm-pack-without-compiler-build-state',status:'pass',owner:manifest.name,filename:result.filename,archive_sha256:sha(bytes),entries:parsed.entries.size});
  assert(packedManifest.name===manifest.name&&packedManifest.version===manifest.version,'packed manifest differs from explicit owner identity');
  info.package_json_sha256=sha(archiveManifest.data);
  // Preserve the actual npm-produced bytes before ephemeral pack/consumer
  // cleanup. Parent compares these owning archives directly with build TGZs.
  info.archive_artifact=retainRaw(`pack-${report.pack_observations.length-1}-${result.filename}`,bytes);
  assert(info.archive_artifact.sha256===info.sha256,'retained owning TGZ differs from actual pack bytes');
  if(purpose==='consumer')report.packages.push(info);return {manifest,packedManifest,path,info};
}
function refs(row){return {...row.dependencies,...row.optionalDependencies,...row.peerDependencies};}
function lockTarget(rows,parent,name) {
  let cursor=parent;
  while(true){const key=(cursor?cursor+'/':'')+'node_modules/'+name;if(rows[key]&&!rows[key].link)return key;if(!cursor)return null;const next=dirname(cursor);cursor=next==='.'?'':portable(next);}
}
function copyPackOwner(source,destination) {
  mkdirSync(destination,{recursive:true});
  const copied=[];
  function walk(dir) {
    for(const name of readdirSync(dir).sort()) {
      if(['node_modules','.git','.gate','.vitest'].includes(name)||isPythonBytecodePath(portable(relative(source,join(dir,name)))))continue;
      const from=join(dir,name),stat=lstatSync(from),rel=relative(source,from),to=join(destination,rel);
      assert(!stat.isSymbolicLink(),'pack source symlink refused');
      if(stat.isDirectory()){mkdirSync(to,{recursive:true});walk(from);}
      else {assert(stat.isFile()&&!(stat.mode&0o7000),'unsafe pack source entry');mkdirSync(dirname(to),{recursive:true});copyFileSync(from,to);chmodSync(to,stat.mode&0o777);assert(readFileSync(from).equals(readFileSync(to)),'pack source copy changed bytes');copied.push({path:portable(rel),sha256:sha(readFileSync(to)),mode:(stat.mode&0o777).toString(8)});}
    }
  }
  walk(source);return copied;
}
function registryTuple(key,row) {
  const tuple={name:row.name??key.split('node_modules/').at(-1)};
  for(const field of ['version','resolved','integrity','dependencies','optionalDependencies','peerDependencies','peerDependenciesMeta','engines','bin','os','cpu','libc','license','hasInstallScript'])if(field in row)tuple[field]=row[field];
  return tuple;
}
function stable(value) {
  if(Array.isArray(value))return value.map(stable);
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,stable(v)]));
  return value;
}
function validateGeneratedLock(source,generated,manifest,ui,kit) {
  assert(generated.lockfileVersion===3&&generated.packages,'actual npm-generated v3 lock required');
  assert(!Object.hasOwn(generated,'workspaces')&&!Object.hasOwn(generated.packages['']??{},'workspaces'),'consumer root lock retained active workspace configuration');
  assert(generated.name===manifest.name&&generated.version===manifest.version&&generated.packages['']?.name===manifest.name,'npm must reconcile the seed to the actual consumer root');
  for(const field of ['dependencies','devDependencies','engines'])assert(JSON.stringify(stable(generated.packages[''][field]??{}))===JSON.stringify(stable(manifest[field]??{})),`generated consumer root differs: ${field}`);
  const official=new Set(Object.entries(source.packages).filter(([key,row])=>key.includes('node_modules/')&&!row.link&&row.resolved&&row.integrity).map(([key,row])=>JSON.stringify(stable(registryTuple(key,row)))));
  for(const [key,row] of Object.entries(generated.packages)) {
    if(!key)continue;
    assert(key.startsWith('node_modules/')&&!Object.hasOwn(row,'link'),'consumer lock contains an active link or non-installed producer location');
    const name=row.name??key.split('node_modules/').at(-1);
    const packed=[ui,kit].find(p=>p.manifest.name===name);
    if(packed) {
      assert(key===`node_modules/${packed.manifest.name}`&&name===packed.packedManifest.name&&row.version===packed.packedManifest.version&&row.integrity===packed.info.integrity&&row.resolved===manifest.dependencies[name],'actual tarball location/name/version/resolution/integrity does not bind npm pack bytes');
      // npm12 serializes a dependency manifest's workspaces field as inert metadata.
      // Only an exact actual-owner TGZ may carry it; never strip or rewrite the field.
      assert(Object.hasOwn(row,'workspaces')===Object.hasOwn(packed.packedManifest,'workspaces')&&JSON.stringify(stable(row.workspaces))===JSON.stringify(stable(packed.packedManifest.workspaces)),'TGZ workspace metadata differs from its exact packed manifest');
      if(Object.hasOwn(row,'workspaces'))report.proofs.push({name:'exact-owner-tarball-workspace-metadata',status:'pass',path:key,resolved:row.resolved,integrity:row.integrity,package_json_sha256:packed.info.package_json_sha256,metadata:row.workspaces});
      report.dependency_provenance.push({path:key,name,version:row.version,resolved:row.resolved,integrity:row.integrity,source:'actual-owner-tarball'});
    } else {
      assert(!Object.hasOwn(row,'workspaces'),'non-owner registry row carries workspace metadata');
      const tuple=registryTuple(key,row);assert(official.has(JSON.stringify(stable(tuple))),`npm generated registry tuple absent from actual owner lock: ${name}`);
      report.dependency_provenance.push({path:key,...tuple,source:'actual-owner-registry-lock'});
    }
    for(const name of Object.keys(refs(row)))assert(lockTarget(generated.packages,key,name)||row.peerDependenciesMeta?.[name]?.optional||name in (row.optionalDependencies??{}),`generated required dependency closure missing: ${name}`);
  }
  for(const name of Object.keys({...manifest.dependencies,...manifest.devDependencies}))assert(lockTarget(generated.packages,'',name),`generated direct dependency missing: ${name}`);
}
/** The published npm12 CLI is the authority for virtual and actual workspace classification. */
function verifyNoActiveWorkspaces(consumer, manifest, packageLockOnly) {
  const mode=packageLockOnly?'lock':'installed',options=['--json','--offline','--allow-remote=none',...(packageLockOnly?['--package-lock-only']:[])];
  const rootOutput=npm(['query',':root',...options,'--expect-result-count=1'],consumer),roots=JSON.parse(rootOutput);
  assert(Array.isArray(roots)&&roots.length===1&&roots[0].name===manifest.name,'actual npm query must see the consumer root, not an absent tree');
  const output=npm(['query','.workspace',...options,'--expect-result-count=0'],consumer),workspaces=JSON.parse(output);
  assert(Array.isArray(workspaces)&&workspaces.length===0,'actual npm graph contains an active workspace');
  report.proofs.push({name:`actual-npm-${mode}-workspace-graph`,status:'pass',root_count:roots.length,root_name:roots[0].name,workspace_count:workspaces.length,root_query_sha256:sha(rootOutput),workspace_query_sha256:sha(output),package_lock_only:packageLockOnly});
}
function retainPinnedNpmQuerySource(version) {
  const cli=realpathSync(join(dirname(process.execPath),'npm')),owner=dirname(dirname(cli)),manifest=readJSON(join(owner,'package.json'));
  assert(manifest.name==='npm'&&manifest.version===version,'primary query source must belong to the same pinned npm release');
  const source=readFileSync(join(owner,'lib/commands/query.js'));
  report.npm_query_primary_source={...retainRaw('npm-query.js',source),package_name:manifest.name,package_version:manifest.version,cli_path:cli,source_role:'actual pinned npm CLI query implementation; parent review of packageLockOnly/loadVirtual branch'};
}
function exportedTargets(value) {
  if(typeof value==='string')return [value];if(Array.isArray(value))return value.flatMap(exportedTargets);
  if(value&&typeof value==='object')return Object.values(value).flatMap(exportedTargets);return [];
}
function inspectPackage(directory,packed) {
  const p=readJSON(join(directory,'package.json'));assert(p.name===packed.manifest.name&&p.version===packed.manifest.version,'installed package owner/version changed');
  for(const target of Object.values(p.exports??{}).flatMap(exportedTargets)) {
    assert(target.startsWith('./')&&!target.split('/').includes('..'),'unsafe actual package export');
    assert(existsSync(join(directory,target)),`installed export missing: ${p.name} ${target}`);
  }
  const files=list(directory);
  for(const path of files) {
    const rel=portable(relative(directory,path)),bytes=readFileSync(path);
    report.installed_files.push({owner:p.name,path:rel,sha256:sha(bytes),bytes:bytes.length});
    if(/\.d\.(?:ts|mts|cts)$|\.d\.css\.ts$/.test(rel)) {
      const text=bytes.toString('utf8');
      assert(!/(?:from\s*|import\s*\()\s*["'](?:react(?:-dom|-router)?(?:[/-][^"']*)?|@types\/react[^"']*|preact\/compat)["']/.test(text),`published declaration leaks React/compat: ${rel}`);
      assert(!/declare\s+module\s+["']\*\.css["']/.test(text),'CSS wildcard would mask invalid stylesheet imports');
      for(const m of text.matchAll(/(?:import\s*|from\s*)["'](\.[^"']+\.css)["']/g)) {
        const css=resolve(dirname(path),m[1]);assert(css.startsWith(directory+sep)&&existsSync(css),`declaration stylesheet not actually shipped: ${rel} -> ${m[1]}`);
        assert(existsSync(css.replace(/\.css$/,'.d.css.ts')),`specific CSS declaration missing: ${rel}`);
      }
    }
  }
  return p;
}
function inspectKit(installed) {
  const required=[
    'versions.lock.json','templates/gate.sh','templates/compose.gate.yml','templates/Taskfile.yml','templates/Taskfile.repo.yml','templates/Dockerfile.toolchain','templates/.gate.env','templates/Dockerfile','templates/compose.test.yml','templates/ci.yml','templates/AGENTS-block.md','templates/PLANS.md','templates/CORE_REQUESTS.md','templates/GATE_REQUESTS.md','templates/.codex/config.toml','templates/.codex/hooks.json',
    'schemas/result.schema.json','schemas/budgets.schema.json','schemas/kit-lock.schema.json','schemas/lint-scope.schema.json','schemas/ui-adoption.schema.json','schemas/validate.mjs',
    'lint/oxlint.json','lint/v11-lint.mjs','lint/lint-scope.mjs','lint/validation-files.mjs','lint/check_docs.py','lint/docs_gate.py','lint/PROVENANCE.md',
    'scripts/kit-sync.mjs','scripts/versions-check.mjs','scripts/core-lock-floor.mjs','scripts/npm-lock-graph.mjs','scripts/resolve-versions.mjs','scripts/resolve-versions.sh','scripts/run-task.mjs',
  ];
  for(const rel of required) {
    const path=join(installed,rel),owner=rel==='versions.lock.json'?join(root,rel):join(root,'web-kit',rel);assert(existsSync(path)&&lstatSync(path).isFile(),`packed kit artifact missing: ${rel}`);
    assert(existsSync(owner)&&readFileSync(path).equals(readFileSync(owner)),`packed artifact differs from actual source owner: ${rel}`);
  }
  assert(readFileSync(join(installed,'versions.lock.json')).equals(readFileSync(join(root,'versions.lock.json'))),'packed kit lock differs from actual release lock');
  for(const [rel,owner] of [['templates/gate.sh','scripts/gate.sh'],['templates/compose.gate.yml','compose.gate.yml'],['templates/Taskfile.yml','Taskfile.yml'],['templates/Dockerfile.toolchain','Dockerfile.toolchain']])assert(readFileSync(join(installed,rel)).equals(readFileSync(join(root,owner))),`packaged gate template identity differs: ${rel}`);
  return required;
}

try {
  assert(process.platform==='linux'&&root==='/work','npm-distribution runs only through pinned Linux /work runner');
  for(const p of ['/scratch','/scratch/_temp'])assert(lstatSync(p).isDirectory()&&!lstatSync(p).isSymbolicLink()&&realpathSync(p)===p,'safe runner scratch required');
  for(const path of ['package.json','package-lock.json','web-kit/package.json','web-kit/package-lock.json','versions.lock.json',...['Taskfile.yml','consumer.tsx','tsconfig.json','broken-css.ts','package.json','package-lock.json','npm-shrinkwrap.json'].map(name=>'web-kit/testdata/npm-consumer/'+name)].map(p=>join(root,p)))sourceHashes.set(path,existsSync(path)?sha(readFileSync(path)):null);
  const lock=readJSON(join(root,'versions.lock.json')),versions=new Map(lock.tools.map(e=>[e.tool,e.version]));
  assert(process.versions.node===versions.get('node'),'executing Node differs from release pin');
  assert(npm(['--version'],root).trim()===versions.get('npm'),'executing npm differs from release pin');
  scratch=mkdtempSync('/scratch/_temp/npm-distribution-');const packedDir=join(scratch,'packed'),consumer=join(scratch,'consumer');mkdirSync(packedDir);mkdirSync(consumer);

  // Establish an actual clean package before contaminating generated output.
  // Equal exported files alone would miss volatile diagnostics shipped in dist.
  npm(['run','build'],root);
  const cleanPackedDir=join(scratch,'clean-packed');mkdirSync(cleanPackedDir);
  const cleanUi=pack(root,cleanPackedDir,root,'clean-reproduction-reference');
  const cleanPublishedReport=readFileSync(join(root,'dist/.roedu-asset-report.json'));

  // An actual rebuild must collect poisoned runtime files and compiler state.
  // Force declarations to be re-emitted even with an existing incremental cache.
  const stale='obsolete-distribution-probe-12345678.js';
  writeFileSync(join(root,'dist',stale),'throw Error("stale output must not ship");\n');writeFileSync(join(root,'dist',stale+'.gz'),'stale sidecar');writeFileSync(join(root,'dist',stale+'.br'),'stale sidecar');
  const caches=['tsconfig.tsbuildinfo','nested/stale.tsbuildinfo','stale.tsbuildinfo.gz','stale.tsbuildinfo.br'];
  for(const name of caches){const file=join(root,'dist',name);mkdirSync(dirname(file),{recursive:true});writeFileSync(file,'poisoned compiler build state');}
  const declaration=readFileSync(join(root,'dist/index.d.ts'));
  rmSync(join(root,'dist/index.d.ts'));
  npm(['run','build'],root);
  for(const name of [stale,stale+'.gz',stale+'.br'])assert(!existsSync(join(root,'dist',name)),'actual rebuild retained poisoned stale JS');
  for(const name of caches)assert(!existsSync(join(root,'dist',name)),'actual rebuild retained poisoned compiler build state');
  assert(!list(join(root,'dist')).some(file=>/\.tsbuildinfo(?:\.(?:gz|br))?$/.test(file)),'distribution contains compiler build state after actual rebuild');
  assert(existsSync(join(root,'.vitest/tsconfig.tsbuildinfo'))&&lstatSync(join(root,'.vitest/tsconfig.tsbuildinfo')).isFile(),'actual compiler cache must be outside published dist');
  assert(readFileSync(join(root,'dist/index.d.ts')).equals(declaration),'postbuild unexpectedly rewrote public declarations');
  assert(readFileSync(join(root,'dist/.roedu-asset-report.json')).equals(cleanPublishedReport),'published asset diagnostics depend on prior build state');
  report.proofs.push({name:'actual-vite-stale-prune',status:'pass',inventory_sha256:sha(readFileSync(join(root,'dist',INVENTORY)))});
  report.proofs.push({name:'actual-fresh-declarations-and-build-state-prune',status:'pass',declaration_sha256:sha(declaration),cache_path:'.vitest/tsconfig.tsbuildinfo',removed:caches});

  const kitOwner=join(root,'web-kit'),cleanKitSource=join(scratch,'clean-kit-pack-source'),cleanKitPackedDir=join(scratch,'clean-kit-packed');
  const cleanCopied=copyPackOwner(kitOwner,cleanKitSource);copyFileSync(join(root,'versions.lock.json'),join(cleanKitSource,'versions.lock.json'));mkdirSync(cleanKitPackedDir);
  assert(cleanCopied.every(row=>!isPythonBytecodePath(row.path))&&!list(cleanKitSource).some(file=>isPythonBytecodePath(portable(relative(cleanKitSource,file)))),'clean owning-kit source copy contains Python cache');
  const cleanKit=pack(cleanKitSource,cleanKitPackedDir,kitOwner,'clean-kit-reproduction-reference');
  const pythonSources=cleanKit.info.files.filter(path=>path.endsWith('.py')).map(path=>{
    const file=join(kitOwner,path),bytes=readFileSync(file),mode=lstatSync(file).mode&0o777;sourceHashes.set(file,sha(bytes));return {path,sha256:sha(bytes),bytes:bytes.length,mode};
  });
  assert(pythonSources.some(row=>row.path==='lint/check_docs.py')&&pythonSources.some(row=>row.path==='lint/docs_gate.py'),'actual published checker Python sources must remain present');
  const probe='roedu-python-cache-probe-'+basename(scratch),nested='lint/'+probe+'-nested';
  for(const path of ['__pycache__/'+probe+'.pyc','lint/__pycache__/'+probe+'.pyc']) {
    const entry=reservePythonCache(path);
    command('python3',['-B','-c','import py_compile,sys; py_compile.compile(sys.argv[1],cfile=sys.argv[2],doraise=True)',join(kitOwner,'lint/check_docs.py'),entry.file],root);
    preservePythonCacheEvidence(entry,'actual-py_compile-output');
  }
  for(const path of [probe+'.pyc',probe+'.pyo','lint/'+probe+'.pyc','lint/'+probe+'.pyo',nested+'/'+probe+'.pyc',nested+'/'+probe+'.pyo',nested+'/__pycache__/'+probe+'.pyo','lint/'+probe+'.pyc.gz',nested+'/'+probe+'.pyo.br']) {
    const entry=reservePythonCache(path);writeFileSync(entry.file,'poisoned Python compiler-cache fixture '+path+'\n',{flag:'wx'});preservePythonCacheEvidence(entry,'poisoned-cache-path');
  }
  const packSource=join(scratch,'kit-pack-source');
  report.kit_pack_source=copyPackOwner(kitOwner,packSource);
  copyFileSync(join(root,'versions.lock.json'),join(packSource,'versions.lock.json'));
  report.kit_release_lock_sha256=sha(readFileSync(join(packSource,'versions.lock.json')));
  assert(report.kit_pack_source.every(row=>!isPythonBytecodePath(row.path))&&injectedPythonCaches.every(entry=>!existsSync(join(packSource,entry.path))),'consumer source copier retained actual/poisoned Python caches');
  const releaseSource=join(scratch,'release-kit-pack-source'),releasePackedDir=join(scratch,'release-kit-packed');
  packageSource(kitOwner,releaseSource);copyFileSync(join(root,'versions.lock.json'),join(releaseSource,'versions.lock.json'));mkdirSync(releasePackedDir);
  assert(injectedPythonCaches.every(entry=>!existsSync(join(releaseSource,entry.path)))&&!list(releaseSource).some(file=>isPythonBytecodePath(portable(relative(releaseSource,file)))),'actual release source copier retained Python caches');
  for(const source of pythonSources)for(const directory of [cleanKitSource,packSource,releaseSource]) {
    const file=join(directory,source.path);assert(existsSync(file)&&sha(readFileSync(file))===source.sha256&&(lstatSync(file).mode&0o777)===source.mode,'source copier changed/dropped Python source bytes or mode');
  }
  const ui=pack(root,packedDir),kit=pack(packSource,packedDir,kitOwner),releaseKit=pack(releaseSource,releasePackedDir,kitOwner,'actual-release-copier-reproduction');mkdirSync(join(consumer,'vendor'));
  for(const candidate of [kit,releaseKit])assert(readFileSync(candidate.path).equals(readFileSync(cleanKit.path))&&candidate.info.sha256===cleanKit.info.sha256&&candidate.info.integrity===cleanKit.info.integrity,'actual clean/contaminated consumer/release KIT TGZ bytes/SHA/SRI differ');
  for(const source of pythonSources)assert(sha(readFileSync(join(kitOwner,source.path)))===source.sha256&&(lstatSync(join(kitOwner,source.path)).mode&0o777)===source.mode,'Python compilation/cache probe changed owning source');
  report.proofs.push({name:'actual-clean-versus-contaminated-kit-tgz',status:'pass',filename:kit.info.filename,clean_sha256:cleanKit.info.sha256,contaminated_sha256:kit.info.sha256,release_sha256:releaseKit.info.sha256,clean_integrity:cleanKit.info.integrity,contaminated_integrity:kit.info.integrity,release_integrity:releaseKit.info.integrity,bytes:readFileSync(kit.path).length,python_sources:pythonSources,actual_source_copiers:['copyPackOwner','packageSource'],probes:report.python_cache_probes,compiler_cache_members:0});
  assert(readFileSync(ui.path).equals(readFileSync(cleanUi.path))&&ui.info.sha256===cleanUi.info.sha256&&ui.info.integrity===cleanUi.info.integrity,'actual clean and stale-contaminated UI packages differ');
  report.proofs.push({name:'actual-clean-versus-contaminated-ui-tgz',status:'pass',clean_sha256:cleanUi.info.sha256,contaminated_sha256:ui.info.sha256,filename:ui.info.filename,bytes:readFileSync(ui.path).length,poisoned_runtime:[stale,stale+'.gz',stale+'.br'],poisoned_compiler_state:caches,declaration_sha256:sha(declaration),published_inventory_sha256:sha(cleanPublishedReport)});
  for(const packed of [ui,kit]){const destination=join(consumer,'vendor',packed.info.filename);copyFileSync(packed.path,destination);assert(sha(readFileSync(destination))===packed.info.sha256&&sri(readFileSync(destination))===packed.info.integrity,'consumer vendor TGZ differs from actual npm pack bytes');}
  const deps={'@roedu/ui':'file:vendor/'+ui.info.filename,'@roedu/web-kit':'file:vendor/'+kit.info.filename,preact:versions.get('preact')};
  const dev={};for(const name of ['typescript','vite','@preact/preset-vite','@babel/core','@types/node','@playwright/test','axe-core','@axe-core/playwright','web-vitals']){assert(versions.get(name),`required consuming tool pin missing: ${name}`);dev[name]=versions.get(name);}
  const manifest={name:'roedu-packed-consumer',version:'1.0.0',private:true,type:'module',engines:{node:`>=${versions.get('node')}`,npm:`>=${versions.get('npm')}`},dependencies:deps,devDependencies:dev};
  writeFileSync(join(consumer,'package.json'),JSON.stringify(manifest,null,2)+'\n');writeFileSync(join(consumer,'.npmrc'),'save-exact=true\nengine-strict=true\n');
  const official=readJSON(join(root,'package-lock.json'));
  // Seed the complete official owning lock byte-for-byte. npm alone reconciles
  // its virtual tree to this consumer manifest; no rows/fields are synthesized or removed.
  const ownerLockBytes=readFileSync(join(root,'package-lock.json')),seedHash=sha(ownerLockBytes);
  assert(seedHash===sourceHashes.get(join(root,'package-lock.json')),'owning lock provenance differs');
  report.owner_lock_seed=retainRaw('owner-package-lock.json',ownerLockBytes);
  assert(!existsSync(join(consumer,'package-lock.json')),'isolated consumer already has an unexpected lock');
  copyFileSync(join(root,'package-lock.json'),join(consumer,'package-lock.json'));
  assert(readFileSync(join(consumer,'package-lock.json')).equals(ownerLockBytes),'consumer seed must retain every official owner-lock byte');
  report.consumer_lock_seed={source:'byte-identical-owning-lock',sha256:seedHash,npm_reconciles_current_manifest:true};
  retainPinnedNpmQuerySource(versions.get('npm'));
  const fixture=join(root,'web-kit/testdata/npm-consumer'),taskfile=join(fixture,'Taskfile.yml');
  assert(lstatSync(taskfile).isFile()&&!lstatSync(taskfile).isSymbolicLink(),'owned fixture deps Taskfile required');
  const taskfileBytes=readFileSync(taskfile),consumerTaskfile=join(consumer,'Taskfile.yml');
  report.fixture_taskfile_sha256=sha(taskfileBytes);copyFileSync(taskfile,consumerTaskfile);chmodSync(consumerTaskfile,lstatSync(taskfile).mode&0o777);
  assert(readFileSync(consumerTaskfile).equals(taskfileBytes),'committed fixture Taskfile copy changed bytes');
  report.consumer_taskfile={file:consumerTaskfile,sha256:sha(readFileSync(consumerTaskfile)),byte_identical:true};
  command('task',['--taskfile',consumerTaskfile,'--dir',consumer,'deps'],consumer);
  assert(readFileSync(taskfile).equals(taskfileBytes)&&readFileSync(consumerTaskfile).equals(taskfileBytes),'deps changed the source or copied fixture Taskfile');
  // Retain actual npm output before parsing or rejecting any leftover rows.
  const generatedBytes=readFileSync(join(consumer,'package-lock.json')),generatedFile=retainRaw('generated-package-lock.json',generatedBytes);
  report.generated_lock={...generatedFile,owner_seed_sha256:seedHash,npm_reconciled_from_unedited_owner_lock:true};
  const generated=JSON.parse(generatedBytes);
  report.generated_lock.root=generated.packages?.[''];report.generated_lock.top_level_workspaces=generated.workspaces??null;
  report.generated_lock.unsupported_rows=Object.entries(generated.packages??{}).filter(([key,row])=>key&&(!key.startsWith('node_modules/')||row.link||row.workspaces)).map(([key,row])=>({path:key,reasons:[...(!key.startsWith('node_modules/')?['outside-node_modules']:[]),...(row.link?['link']:[]),...(row.workspaces?['workspaces']:[])],row}));
  validateGeneratedLock(official,generated,manifest,ui,kit);
  verifyNoActiveWorkspaces(consumer,manifest,true);
  const before=sha(readFileSync(join(consumer,'package-lock.json'))),manifestBefore=sha(readFileSync(join(consumer,'package.json')));
  npm(['ci','--offline','--allow-remote=none','--ignore-scripts','--no-audit','--no-fund'],consumer);
  assert(sha(readFileSync(join(consumer,'package-lock.json')))===before&&sha(readFileSync(join(consumer,'package.json')))===manifestBefore,'offline ci changed npm-generated manifest/lock');
  const installed=readJSON(join(consumer,'package-lock.json'));
  for(const [key,row] of Object.entries(installed.packages))if(key.includes('node_modules/'))assert(!/^(?:react(?:$|-)|@types\/react(?:$|-))/.test(key.split('node_modules/').at(-1)),'consumer lock includes React packages/types');
  const uiDir=join(consumer,'node_modules/@roedu/ui'),kitDir=join(consumer,'node_modules/@roedu/web-kit');
  for(const directory of [uiDir,kitDir])assert(lstatSync(directory).isDirectory()&&!lstatSync(directory).isSymbolicLink()&&realpathSync(directory).startsWith(realpathSync(consumer)+sep),'actual TGZ installation must be a real isolated package directory, never a workspace link');
  verifyNoActiveWorkspaces(consumer,manifest,false);
  inspectPackage(uiDir,ui);const kitManifest=inspectPackage(kitDir,kit);const artifacts=inspectKit(kitDir);
  for(const name of ['react','react-dom','@types/react','@types/react-dom'])assert(!existsSync(join(consumer,'node_modules',name)),'consumer installed React runtime/types');
  report.proofs.push({name:'actual-offline-file-tarball-install',status:'pass',lock_sha256:before,artifacts});

  for(const name of ['consumer.tsx','tsconfig.json'])copyFileSync(join(fixture,name),join(consumer,name));
  const ts=readJSON(join(consumer,'tsconfig.json'));assert(ts.compilerOptions.skipLibCheck===false&&ts.compilerOptions.noUncheckedSideEffectImports===true&&ts.compilerOptions.strict===true&&ts.compilerOptions.types.length===0&&!ts.compilerOptions.paths,'strict consumer must not use source aliases or ambient types');
  const compiler=join(consumer,'node_modules/.bin/tsc');const compilerVersion=command(compiler,['--version'],consumer);assert(/Version\s+(\S+)/.exec(compilerVersion.stdout)?.[1]===versions.get('typescript'),'executing consumer TypeScript differs from release pin');command(compiler,['--project','tsconfig.json'],consumer);
  copyFileSync(join(fixture,'broken-css.ts'),join(consumer,'broken-css.ts'));
  writeFileSync(join(consumer,'tsconfig.negative.json'),JSON.stringify({...ts,include:['broken-css.ts']},null,2)+'\n');
  const negative=command(compiler,['--project','tsconfig.negative.json'],consumer,1);assert(/not-a-real-stylesheet\.css/.test(negative.stdout+negative.stderr),'negative proof failed for an unrelated compiler error');
  report.proofs.push({name:'strict-typescript7-six-surface-consumer',status:'pass',fixture_sha256:sha(readFileSync(join(consumer,'consumer.tsx'))),negative_css_rejected:true});

  writeFileSync(join(consumer,'index.html'),'<!doctype html><html><head><title>Actual packed consumer</title></head><body><script type="module" src="/consumer.tsx"></script></body></html>\n');
  writeFileSync(join(consumer,'vite.config.mjs'),"import {defineConfig} from 'vite';\nimport preact from '@preact/preset-vite';\nexport default defineConfig({plugins:[preact({reactAliasesEnabled:false})],oxc:{jsx:{runtime:'automatic',importSource:'preact'}},build:{manifest:true}});\n");
  command(join(consumer,'node_modules/.bin/vite'),['build'],consumer);
  assert(existsSync(join(consumer,'dist/.vite/manifest.json')),'actual packed consumer browser build missing');
  for(const target of Object.values(kitManifest.exports).flatMap(exportedTargets).filter(p=>p.endsWith('.mjs')))await import(pathToFileURL(join(kitDir,target)));
  report.proofs.push({name:'packed-consumer-vite-and-kit-runtime-imports',status:'pass',manifest_sha256:sha(readFileSync(join(consumer,'dist/.vite/manifest.json')))});
  const validator=await import(pathToFileURL(join(kitDir,'schemas/validate.mjs')));
  assert(typeof validator.validate==='function','actual packaged schema validator export missing');
  const budgetSchema=readJSON(join(kitDir,'schemas/budgets.schema.json')),budgets=readJSON(join(root,'budgets.json'));
  validator.validate(budgetSchema,budgets);
  const missingTarget=structuredClone(budgets);delete missingTarget.js['cat-initial'].target_gz;
  let rejected=false;try{validator.validate(budgetSchema,missingTarget);}catch{rejected=true;}assert(rejected,'packaged schema accepted missing cat target');
  const badNull=structuredClone(budgets);badNull.js['server-page'].limit_gz=null;
  rejected=false;try{validator.validate(budgetSchema,badNull);}catch{rejected=true;}assert(rejected,'packaged schema accepted null JS limit');
  const budget=await import(pathToFileURL(join(kitDir,'budget/index.mjs')));
  assert(typeof budget.evaluate==='function'&&typeof budget.gateBudgets==='function','actual packaged budget APIs missing');
  const assetsRoot=join(consumer,'dist'),assetManifest=readJSON(join(assetsRoot,'.vite/manifest.json'));
  const entry=Object.keys(assetManifest).find(key=>assetManifest[key].isEntry);assert(entry,'actual consumer manifest entry missing');
  for(const path of list(assetsRoot).filter(p=>/\.(?:js|css)$/.test(p)))writeFileSync(path+'.gz',gzipSync(readFileSync(path)));
  const globalCSS=[...new Set(Object.values(assetManifest).flatMap(item=>item.css??[]))].sort();
  const actualRoute=[{name:'consumer',method:'GET',path:'/',template:'index.html'}];
  const config={schema:1,routes:{consumer:{class:'island-route',entries:[entry],islands:[],widgets:[],vendors:[]}},global_css:globalCSS,vendors:{}};
  const measured=await budget.evaluate(budgets,assetManifest,actualRoute,config,assetsRoot);budget.gateBudgets(measured);
  const tooSmall=structuredClone(budgets);tooSmall.js['island-route'].limit_gz=0;
  const exceeded=await budget.evaluate(tooSmall,assetManifest,actualRoute,config,assetsRoot);assert(exceeded.status==='fail'&&Object.values(budget.gateBudgets(exceeded)).some(row=>row.status==='fail'),'packaged budget must report real bytes over zero limit as failed');
  const corrupt=Object.values(assetManifest).find(item=>item.file.endsWith('.js'))?.file;assert(corrupt,'actual consumer JS asset missing');
  writeFileSync(join(assetsRoot,corrupt+'.gz'),gzipSync(Buffer.from('stale actual-sidecar probe')));
  rejected=false;try{await budget.evaluate(budgets,assetManifest,actualRoute,config,assetsRoot);}catch{rejected=true;}assert(rejected,'packaged budget accepted stale gzip bytes');
  report.proofs.push({name:'actual-packaged-schema-budget-positive-negative',status:'pass',measurements:measured,missing_target_rejected:true,null_js_rejected:true,over_budget_rejected:true,stale_gzip_rejected:true});
  report.status='pass';
}catch(error){report.error=error.message;process.exitCode=1;}
finally{
  try{cleanupInjectedPythonCaches();}catch(error){report.cleanup_python_probe_error=error.message;report.status='fail';process.exitCode=1;}
  for(const [path,expected] of sourceHashes){const actual=existsSync(path)?sha(readFileSync(path)):null;report.proofs.push({name:'owning-source-byte-preservation',path:portable(relative(root,path)),before_sha256:expected,after_sha256:actual,status:actual===expected?'pass':'fail'});if(actual!==expected){report.status='fail';report.source_mutation=portable(relative(root,path));process.exitCode=1;}}
  if(scratch){try{rmSync(scratch,{recursive:true,force:true});report.scratch_removed=true;}catch(error){report.cleanup_error=error.message;report.status='fail';process.exitCode=1;}}
  process.stdout.write(JSON.stringify(report,null,2)+'\n');
}
