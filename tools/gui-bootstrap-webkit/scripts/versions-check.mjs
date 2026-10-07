import { existsSync, readFileSync } from 'node:fs';
import { dirname, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { isDeepStrictEqual } from 'node:util';
import { createHash } from 'node:crypto';
import { localPath, posix, readJSON, readLocal, parseJSONC, validateConfig, walkRepository } from '../lint/validation-files.mjs';
import { bannedName, finish, loadScope, sourceFindings, taskConfig } from '../lint/lint-scope.mjs';
import { graph, packageName, refs, resolveDependency } from './npm-lock-graph.mjs';
import { consumerCoreFloor } from './core-lock-floor.mjs';
import { auditGoModules } from './go-module-audit.mjs';
import { inspectUiAdoption,loadKit,uiAdoptionPending } from './kit-sync.mjs';

const stable=v=>typeof v==='string'&&/^v?\d+\.\d+\.\d+(?:\+[A-Za-z0-9.-]+)?$/.test(v);
const depFields=['dependencies','devDependencies','optionalDependencies','peerDependencies'];
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const check=(condition,message)=>{if(!condition)throw new Error(message);};
const npmBan=(tool,e)=>e?.status==='banned'||/^(?:@types\/react(?:$|[-/])|react(?:$|-))/.test(tool);
const scopeablePackage=tool=>/^(?:@types\/react(?:$|[-/])|react(?:$|-))/.test(tool);

export async function checkVersions({root=process.cwd(),config,toolchain=false,lintOnly=false,additionalFindings=[],floor}) {
  root=resolve(root);const findings=[],checks=[],observed=new Set();
  const add=(rule,tool,paths,extra={})=>findings.push({rule,tool_or_import:tool,paths,scopable:false,...extra});
  const run=(name,fn)=>{try{const count=fn();checks.push({name,status:'pass',observations:count??1});}catch(error){add(name,error.message,[]);checks.push({name,status:'fail',reason:error.message});}};
  let lock,entries,files,packages,manifests,goAudit,uiAdoption,scope={entries:[],present:false};
  try {
    validateConfig(root,config);({files}=walkRepository(root,config));
    lock=readJSON(root,'versions.lock.json');check(lock.schema===2&&Array.isArray(lock.tools)&&lock.tools.length,'nonempty schema2 versions lock required');
    entries=new Map(lock.tools.map(e=>[e.tool,e]));check(entries.size===lock.tools.length,'duplicate lock entries');
    manifests=files.filter(p=>p.split('/').at(-1)==='package.json').map(path=>({path,data:readJSON(root,path)}));
    check(manifests.length,'repository has no audited npm manifests');
    packages=new Set(manifests.map(m=>posix(dirname(m.path))));
    try{scope=loadScope(root,config,files,packages);}catch(error){add('lint-scope',error.message,['lint/scope.json']);}
  }catch(error){return {schema:1,status:'fail',reason:'validation-failed',checks,errors:[{rule:'configuration',tool_or_import:error.message,paths:[]}],legacy_pending:[]};}

  run('lock-policy',()=> {
    for(const e of lock.tools) {
      check(typeof e.tool==='string'&&['npm','runtime','gomod','image','apt'].includes(e.kind)&&['core','app','environment'].includes(e.scope),`invalid tool entry ${e.tool}`);
      if(e.exception)check(typeof e.approved_by==='string'&&e.approved_by.trim(),`unapproved exception ${e.tool}`);
      if(e.scope==='environment')continue;
      check(['pinned','optional','transitive-only','banned'].includes(e.status??'pinned'),`invalid status ${e.tool}`);
      if(e.status==='optional')check(typeof e.notes==='string'&&e.notes.trim()||e.exception,`optional reason missing ${e.tool}`);
      if(e.status==='transitive-only')check(Array.isArray(e.dependants)&&e.dependants.length,`transitive dependants missing ${e.tool}`);
      if(['npm','runtime','gomod'].includes(e.kind)&&e.status!=='banned')check(stable(e.version),`unstable/unresolved version ${e.tool}`);
    }
    return lock.tools.length;
  });
  if(config.role==='consumer')run('core-floor',()=> {
    const incoming=floor??consumerCoreFloor(root,config,manifests);
    const core=new Map(incoming.tools.map(e=>[e.tool,e]));
    for(const e of lock.tools.filter(e=>e.scope==='core'))check(core.has(e.tool)&&isDeepStrictEqual(e,core.get(e.tool)),`consumer changed core pin ${e.tool}`);
    check(isDeepStrictEqual(lock.toolchain_image,incoming.toolchain_image),'consumer changed toolchain pin');
    check(lock.core_tag===readLocal(root,'kit/CORE_TAG').trim(),'core_tag differs from committed kit/CORE_TAG');
    return lock.tools.filter(e=>e.scope==='core').length;
  });
  if(config.ui_adoption&&!lintOnly)run('ui-adoption',()=>{
    const plan=inspectUiAdoption(root,config,loadKit(root));
    check(plan.mode==='staged-react'&&plan.pending===true,'actual original UI provenance required for staged phase');
    uiAdoption=uiAdoptionPending(plan);return plan.receipt.assertion_count;
  });
  if(toolchain) {
    for(const [tool,cmd,args,re] of [['node','node',['--version'],/^v(\S+)/],['npm','npm',['--version'],/^(\S+)/],['go','go',['version'],/go(\d+\.\d+\.\d+)/],['github.com/a-h/templ','templ',['version'],/(v?\d+\.\d+\.\d+)/],['github.com/go-task/task/v3','task',['--version'],/(v?\d+\.\d+\.\d+)/],['oxlint','oxlint',['--version'],/(\d+\.\d+\.\d+)/],['@ast-grep/cli','ast-grep',['--version'],/(\d+\.\d+\.\d+)/]])run('toolchain:'+tool,()=> {
      check(entries.has(tool),`toolchain entry missing ${tool}`);
      const r=spawnSync(cmd,args,{cwd:root,encoding:'utf8'});check(r.status===0&&!r.error,`toolchain command failed ${tool}`);
      check((r.stdout.match(re)?.[1]??'').replace(/^v/,'')===entries.get(tool).version.replace(/^v/,''),`toolchain version differs ${tool}`);
      return 1;
    });
  }
  {
    for(const {path,data:p} of manifests)run('manifest:'+path,()=> {
      let count=0;const pkg=posix(dirname(path));
      for(const field of depFields)for(const [tool,value] of Object.entries(p[field]??{})) {
        count++;const e=entries.get(tool);observed.add(tool);
        if(npmBan(tool,e)){add('banned-packages',tool,[path],{package_dir:pkg,scopable:scopeablePackage(tool)});continue;}
        if(['@roedu/ui','@roedu/web-kit'].includes(tool)&&typeof value==='string'&&value.startsWith('file:')) {
          const target=resolve(root,pkg,value.slice(5));check(target.startsWith(localPath(root,config.vendor_dir,false)+'/'),`${path}: kit tarball outside vendor_dir`);localPath(root,posix(relative(root,target)));continue;
        }
        check(e&&e.kind==='npm',`${path}: unregistered direct dependency ${tool}`);
        check(e.status!=='transitive-only',`${path}: direct transitive-only ${tool}`);
        check(value===e.version,`${path}: nonexact or changed ${tool}`);
      }
      check(p.engines?.node===`>=${entries.get('node')?.version}`&&p.engines?.npm===`>=${entries.get('npm')?.version}`,`${path}: engines disagree with lock`);
      return count;
    });
    const locks=files.filter(p=>p.split('/').at(-1)==='package-lock.json');
    if(!locks.length)add('npm-lock','no audited package locks',[]);
    const represented=new Set();
    for(const path of locks)run('npm-lock:'+path,()=> {
      const data=readJSON(root,path),rows=data.packages,lockDir=posix(dirname(path));
      check(rows&&Object.keys(rows).length,`${path}: nonempty packages map required`);
      const g=graph(rows,lockDir,packages);let count=0;
      for(const [key,row] of Object.entries(rows)) {
        if(!key.includes('node_modules/')&&!row.link) {
          const pkg=posix(resolve('/',lockDir,key)).slice(1)||'.';
          if(packages.has(pkg)){
            represented.add(pkg);const manifest=manifests.find(m=>posix(dirname(m.path))===pkg);
            for(const field of depFields){
              check(isDeepStrictEqual(row[field]??{},manifest.data[field]??{}),`${path}: manifest/lock ${field} drift in ${pkg}`);
              for(const name of Object.keys(row[field]??{}))if(field!=='optionalDependencies'&&!(field==='peerDependencies'&&manifest.data.peerDependenciesMeta?.[name]?.optional))check(resolveDependency(rows,key,name),`${path}: declared dependency missing from installed lock graph ${name}`);
            }
          }
          continue;
        }
        if(row.link)continue;
        const tool=packageName(key,row),e=entries.get(tool);count++;observed.add(tool);
        if(npmBan(tool,e)) {
          const owners=[...(g.owners.get(key)??new Set([lockDir]))];
          for(const owner of owners)add('banned-packages',tool,[path+'#'+key],{package_dir:owner,scopable:scopeablePackage(tool)});
          continue;
        }
        if(e?.version) {
          const axeException=tool==='axe-core'&&key!=='node_modules/axe-core'&&e.exception&&e.approved_by&&/^4\.13\.\d+$/.test(row.version)&&[...g.incoming.get(key)??[]].some(parent=>packageName(parent,rows[parent])==='@axe-core/playwright'&&/^~4\.13(?:\.\d+)?$/.test(rows[parent].dependencies?.['axe-core']??''));
          check(axeException||row.version===e.version,`${path}: installed ${key} disagrees with exact lock`);
        }
        if(e?.status==='transitive-only') {
          const parents=[...g.incoming.get(key)??[]].map(parent=>packageName(parent,rows[parent]));
          check(parents.length&&parents.every(name=>e.dependants.includes(name)),`${path}: forbidden transitive parent for ${tool}`);
        }
      }
      return count;
    });
    for(const pkg of packages)if(!represented.has(pkg))add('npm-lock','package missing from lock packages map',[pkg]);

    run('go-modules',()=> {
      try {
        goAudit=auditGoModules({root,config,files,entries,lock,onObserved:tool=>observed.add(tool),onBanned:(tool,path)=>add('banned-packages',tool,[path])});
      } catch(error) {goAudit=error.goAudit;throw error;}
      return goAudit.modules.reduce((count,module)=>count+module.requirements.length,0);
    });
    for(const path of files.filter(p=>/(?:^|\/)tsconfig[^/]*\.json$/.test(p)))run('tsconfig:'+path,()=> {
      const p=parseJSONC(readLocal(root,path)),o=p.compilerOptions??{},pkg=posix(dirname(path));
      check(!('baseUrl' in o)&&!('downlevelIteration' in o)&&o.target?.toLowerCase()!=='es5'&&!['node','node10','classic'].includes(o.moduleResolution?.toLowerCase())&&!['amd','umd','system','none'].includes(o.module?.toLowerCase())&&!['esModuleInterop','allowSyntheticDefaultImports','alwaysStrict'].some(k=>o[k]===false),`${path}: removed TS7 option`);
      for(const [name,targets] of Object.entries(o.paths??{}))if(Array.isArray(targets)&&targets.some(t=>typeof t==='string'&&/preact\/compat(?:$|\/)/.test(t))) {
        const owners=[...packages].filter(p=>p==='.'||path.startsWith(p+'/')).sort((a,b)=>b.length-a.length);
        add('compat-paths',`${name} -> preact/compat`,[path],{package_dir:owners[0]??pkg,scopable:true});
      }
      return 1;
    });
    run('node-config',()=> {
      const nvm=files.filter(p=>p.split('/').at(-1)==='.nvmrc'),rc=files.filter(p=>p.split('/').at(-1)==='.npmrc');
      check(nvm.length&&rc.length,'.nvmrc and .npmrc are required');
      for(const p of nvm)check(readLocal(root,p).trim()===entries.get('node')?.version,`${p}: Node pin differs`);
      for(const p of rc)check(readLocal(root,p)==='save-exact=true\nengine-strict=true\n',`${p}: npm configuration differs`);
      return nvm.length+rc.length;
    });
    run('docker-toolchain',()=> {
      const text=readLocal(root,'Dockerfile.toolchain');let count=0;
      if(lock.toolchain_image?.dockerfile_sha256)check(sha(readFileSync(localPath(root,'Dockerfile.toolchain')))===lock.toolchain_image.dockerfile_sha256,'toolchain Dockerfile hash differs from built image provenance');
      for(const e of lock.tools.filter(e=>e.build_arg)) {
        const value=text.match(new RegExp(`^ARG ${e.build_arg}=(.*)$`,'m'))?.[1];count++;
        if(e.build_arg==='PG_MAJOR'){check(value==='__PROD_PG_MAJOR__'||value===e.version,'PG_MAJOR differs');continue;}
        check(value===(e.build_arg_value??e.version),`Dockerfile.toolchain ${e.build_arg} differs`);
        if(e.build_arg_sha256)check(text.match(new RegExp(`^ARG ${e.build_arg_sha256}=(.*)$`,'m'))?.[1]===(e.sha256_linux_x64??e.sha256_linux_amd64),`Dockerfile.toolchain ${e.build_arg_sha256} differs`);
      }
      check(count,'toolchain has no audited build args');return count;
    });
    const dockerfiles=files.filter(p=>/(?:^|\/)Dockerfile(?:\.[^/]*)?$/.test(p));
    if(!dockerfiles.length)add('docker-images','no Dockerfiles audited',[]);
    for(const path of dockerfiles)run('docker:'+path,()=> {
      const text=readLocal(root,path),args=new Map([...text.matchAll(/^ARG\s+(\w+)=(.*)$/gm)].map(m=>[m[1],m[2]])),stages=new Set();let count=0;
      for(const m of text.matchAll(/^FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?/gmi)) {
        let ref=m[1].replace(/\$\{(\w+)\}/g,(_,key)=>args.get(key)??'UNRESOLVED');
        if(!stages.has(ref)) {
          const image=lock.tools.find(e=>e.kind==='image'&&`${e.image??e.version}@${e.digest}`===ref);
          check(image,`${path}: unpinned/unregistered FROM image`);observed.add(image.tool);count++;
        }
        if(m[2])stages.add(m[2]);
      }
      check(count,`${path}: no actual base images`);return count;
    });
    for(const e of lock.tools.filter(e=>e.kind==='apt'&&e.scope==='app'&&e.apps?.includes(config.app)))run('apt-floor:'+e.tool,()=> {
      const matches=dockerfiles.filter(path=>{const text=readLocal(root,path);return text.includes(e.tool)&&text.includes('dpkg --compare-versions')&&text.includes(' ge '+e.version);});
      check(matches.length,`missing Docker build assertion for apt floor ${e.tool}`);observed.add(e.tool);return matches.length;
    });
    run('gate-image-pins',()=> {
      const text=readLocal(root,'.gate.env'),env=new Map(text.split('\n').filter(l=>/^[A-Z_]+=/.test(l)).map(l=>[l.slice(0,l.indexOf('=')),l.slice(l.indexOf('=')+1)]));
      check(env.get('TOOLCHAIN_IMAGE')===lock.toolchain_image?.version&&env.get('TOOLCHAIN_DIGEST')===lock.toolchain_image?.image_id,'toolchain image/environment mismatch');
      const pg=entries.get('postgres');check(pg&&env.get('PG_MAJOR')===pg.version&&env.get('GATE_DB_IMAGE')===`${pg.image}@${pg.digest}`,'Postgres image/major mismatch');
      const a=entries.get('@playwright/test'),b=entries.get('playwright'),image=entries.get('playwright-image');
      check(a&&b&&image&&a.version===b.version&&image.version.includes(`:v${a.version}-`),'Playwright triple differs');
      return 3;
    });
    for(const e of lock.tools.filter(e=>e.scope==='app'&&e.apps?.includes(config.app)&&!['optional','banned','transitive-only'].includes(e.status)))if(!observed.has(e.tool))add('required-tool',e.tool,[]);
  }
  if(!Array.isArray(additionalFindings))throw Error('AST findings must be an array');
  findings.push(...sourceFindings(root,files,entries),...additionalFindings);
  const result=finish(findings,scope,packages);
  return {...result,...(uiAdoption?{ui_adoption:uiAdoption,...(result.status==='pass'?{reason:result.legacy_pending.length?'legacy-pending;ui-staged-pending':'ui-staged-pending'}:{})}:{}),check:lintOnly?'lint-scope':'versions-check',checks,go_audit:goAudit,counts:{manifests:manifests.length,files:files.length,go_modules:goAudit?.modules.length??0,go_receivers:config.go_dirs.length,tools:lock.tools.length},versions_lock_sha256:sha(readFileSync(localPath(root,'versions.lock.json')))};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const flags=process.argv.slice(2);
  (async()=> {
    check(flags.every(f=>f==='--toolchain')&&new Set(flags).size===flags.length,'only --toolchain is accepted');
    const result=await checkVersions({root:process.cwd(),config:taskConfig(process.cwd()),toolchain:flags.includes('--toolchain')});
    process.stdout.write(JSON.stringify(result)+'\n');if(result.status!=='pass'){for(const error of result.errors)process.stderr.write(`${error.rule}: ${error.tool_or_import} ${error.paths.join(', ')}\n`);process.exitCode=1;}
  })().catch(error=> {process.stderr.write(error.message+'\n');process.stdout.write(JSON.stringify({schema:1,status:'fail',reason:'validation-failed',errors:[{rule:'versions-check',tool_or_import:error.message,paths:[]}],legacy_pending:[]})+'\n');process.exitCode=1;});
}
