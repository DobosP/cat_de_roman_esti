// Synthetic current-context fixtures. Never emits an application gate pass or original-runtime qualification.
import * as fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
assert.equal(process.platform,'linux');assert.equal(process.cwd(),'/work');
const source=process.cwd(),base='/scratch/_temp';assert.equal(fs.realpathSync(base),base);
const parent=fs.mkdtempSync(path.join(base,'bootstrap-current-fixture-')),root=path.join(parent,'repo'),control=path.join(parent,'private');
const hash=bytes=>createHash('sha256').update(bytes).digest('hex'),json=value=>JSON.stringify(value)+'\n',checks=[],commands=[];
const put=(file,bytes)=>{const target=path.join(root,file);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,bytes);};
const wrapper=fs.readFileSync('scripts/gate.sh','utf8');
function block(name){const start=wrapper.indexOf(`<<'${name}'\n`),end=wrapper.indexOf(`\n${name}\n`,start);assert(start>=0&&end>start);return wrapper.slice(start+name.length+5,end);}
const env={...process.env,GATE_SHA:'a'.repeat(40),GATE_TREE_SHA256:'b'.repeat(64),TOOLCHAIN_DIGEST:'sha256:'+'c'.repeat(64),GATE_DIRTY:'false',GOMAXPROCS:'4',CSP_STAGE:'report-only'};
const config={role:'consumer',app:'cat_de_roman_esti',npm_dir:'kit-tools',vendor_dir:'frontend/vendor',go_dirs:['server'],ui_adoption:{mode:'staged-react',until:'S1-M2',legacy:{version:'0.3.0',archive_sha256:'d'.repeat(64),source_sha:'e'.repeat(40),receipt:'docs/original-runtime.json',receipt_sha256:'f'.repeat(64)}}};
function run(command,args,input){const r=spawnSync(command,args,{cwd:root,env,encoding:'utf8',input,maxBuffer:16*1024*1024});commands.push({command,args_sha256:hash(JSON.stringify(args)),exit_code:r.status,stdout_sha256:hash(r.stdout??''),stderr_sha256:hash(r.stderr??'')});return r;}
function checked(name,fn){fn();checks.push({name,status:'pass'});}
let capturePath,expectedPath,currentTarget;
function current(target){
 currentTarget=target;const directory=target.replaceAll(':','-');const capture={schema:1,target,sha:env.GATE_SHA,tree_sha256:env.GATE_TREE_SHA256,toolchain_digest:env.TOOLCHAIN_DIGEST,config,config_sha256:hash(JSON.stringify(config))};
 capturePath=path.join(control,`capture-${directory}.json`);expectedPath=path.join(control,`expected-${directory}.json`);fs.writeFileSync(capturePath,json(capture));
 put(`.gate/${directory}/wrapper-kit-config.json`,json(capture));const owner=run('python3',['-I','-',capturePath,expectedPath],block('PY_CURRENT_CONTEXT'));assert.equal(owner.status,0,owner.stderr);
 const raw=fs.readFileSync(expectedPath);put('.gate/wrapper-current.json',raw);put(`.gate/${directory}/wrapper-current.json`,raw);return JSON.parse(raw);
}
function guard(){return run('python3',['-I','-',expectedPath,root,currentTarget.replaceAll(':','-')],block('PY_CURRENT_VERIFY'));}
function native(target,success=true){const r=run('task',['--silent',target]);if(success)assert.equal(r.status,0,r.stderr);else assert.notEqual(r.status,0);return r;}
try{
 fs.mkdirSync(control,{recursive:true});put('Taskfile.yml',fs.readFileSync('Taskfile.yml'));put('package.json',json({name:'synthetic-current-fixture',version:'1.0.0',private:true}));put('server/go.mod','module example.test/synthetic-current\n\ngo 1.27.1\n');put('server/fixture.go','package fixture\nconst Value=1\n');
 put('versions.lock.json',fs.readFileSync(path.join(source,'versions.lock.json')));
 put('.gate.env','TOOLCHAIN_DIGEST='+env.TOOLCHAIN_DIGEST+'\nCSP_STAGE=report-only\nGATE_PARALLEL_MAX=4\n');put('config.json',json(config));put('kit-tools/package.json',json({name:'@roedu/web-kit',version:'0.1.1',type:'module'}));
 for(const name of ['locate-kit.mjs','ui-adoption-config.mjs'])put('kit-tools/scripts/'+name,fs.readFileSync('web-kit/scripts/'+name));
 // The real native bootstrap and real hook/witness API execute. The fixture
 // runner only records observations; it deliberately never writes result.json.
 put('kit-tools/scripts/run-task.mjs',`import fs from 'node:fs';import {readKitConfig,publicConfig} from './locate-kit.mjs';import {createContext,validateSetupWitness} from '${source}/web-kit/scripts/run-task.mjs';export {createContext,validateSetupWitness};export async function main(target,options={}){const ctx=createContext(target,options.setupWitness?.report?.invocation);const c=readKitConfig(process.cwd(),true,target);if(options.setupWitness)validateSetupWitness(options.setupWitness,ctx);fs.writeFileSync('observed.json',JSON.stringify({target,config:publicConfig(c),toolchain_digest:ctx.toolchain_digest}));}\n`);
 put('hook.mjs',`import fs from 'node:fs';import path from 'node:path';import {createHook} from '${source}/web-kit/scripts/run-task.mjs';const target=process.argv[2],hook=createHook(target,process.argv[3]);if(target==='deps'){hook.check('npm-lock',()=>hook.run('npm',['install','--package-lock-only','--ignore-scripts']));hook.check('go-mod-tidy',()=>hook.run('go',['mod','tidy'],path.join(process.cwd(),'server')));}else hook.check('actual-fixture-config',()=>hook.assert('Actual committed config matches current phase',()=>JSON.parse(fs.readFileSync('config.json')).ui_adoption.mode==='staged-react'));process.stdout.write(JSON.stringify(hook.finish())+'\\n');\n`);
 put('Taskfile.repo.yml',`version: '3'\nsilent: true\ntasks:\n  kit-config:\n    cmds:\n      - node --input-type=module -e "import fs from 'node:fs';process.stdout.write(fs.readFileSync('config.json'))"\n  setup:\n    cmds:\n      - node hook.mjs setup '{{.INVOCATION}}'\n  deps:\n    cmds:\n      - node hook.mjs deps '{{.INVOCATION}}'\n`);
 // Historical malformed, symlink and same-identity records are not current selectors.
 for(const target of ['unit','full','build'])checked(`actual native ${target} keeps same-HEAD histories`,()=>{current(target);native(target==='unit'?'gate:unit':target==='full'?'gate:full':'build');const observed=JSON.parse(fs.readFileSync(path.join(root,'observed.json')));assert.equal(observed.target,target);assert.deepEqual(observed.config,config);assert.equal(guard().status,0);});
 const history=['unit','full','build'].map(target=>[target,fs.readFileSync(path.join(root,'.gate',target,'wrapper-kit-config.json'))]);
 put('.gate/perf/wrapper-kit-config.json','malformed historical JSON');fs.mkdirSync(path.join(root,'.gate/e2e'),{recursive:true});fs.symlinkSync('/does-not-exist',path.join(root,'.gate/e2e/wrapper-kit-config.json'));
 current('kit:sync');checked('nested native setup/assets/deps use current kit sync',()=>{native('setup');native('assets:sync');native('deps');const reusable=run(process.execPath,[path.join(source,'web-kit/scripts/kit-bootstrap.mjs'),'deps']);assert.equal(reusable.status,0,reusable.stderr);assert.equal(guard().status,0);});
 checked('forwarded executing digest survives changed desired environment',()=>{put('.gate.env','TOOLCHAIN_DIGEST=sha256:'+'9'.repeat(64)+'\nCSP_STAGE=report-only\nGATE_PARALLEL_MAX=4\n');native('assets:sync');assert.equal(JSON.parse(fs.readFileSync(path.join(root,'observed.json'))).toolchain_digest,env.TOOLCHAIN_DIGEST);});
 checked('unapproved current parent/child pair fails before hook',()=>native('gate:unit',false));
 const raw=fs.readFileSync(path.join(root,'.gate/wrapper-current.json')),record=JSON.parse(raw);
 checked('closed UUID and literal primary target refuse coercion/aliases',()=>{for(const patch of [{invocation:[record.invocation]},{target:'kit-sync'},{config_path:'.gate/unit/wrapper-kit-config.json'},{sha:'0'.repeat(40)},{config_file_sha256:'0'.repeat(64)}]){put('.gate/wrapper-current.json',json({...record,...patch}));native('assets:sync',false);}put('.gate/wrapper-current.json',raw);});
 checked('current/reference ancestors refuse symlinks without historical probing',()=>{const file=path.join(root,'.gate/wrapper-current.json');fs.unlinkSync(file);fs.symlinkSync(expectedPath,file);native('assets:sync',false);fs.unlinkSync(file);put('.gate/wrapper-current.json',raw);});
 checked('fully self-consistent historical replay fails private host guard',()=>{const old=JSON.parse(fs.readFileSync(path.join(control,'expected-unit.json')));put('.gate/wrapper-current.json',json(old));native('gate:unit');assert.notEqual(guard().status,0);put('.gate/wrapper-current.json',raw);assert.equal(guard().status,0);});
 checked('referenced metadata changes and symlinks refuse before hook',()=>{const relative=record.config_path,file=path.join(root,relative),bytes=fs.readFileSync(file);put(relative,json({...JSON.parse(bytes),config_sha256:'0'.repeat(64)}));native('assets:sync',false);put(relative,bytes);const held=file+'-held';fs.renameSync(file,held);fs.symlinkSync(held,file);native('assets:sync',false);fs.unlinkSync(file);fs.renameSync(held,file);});
 checked('missing current selector never falls back to histories',()=>{fs.unlinkSync(path.join(root,'.gate/wrapper-current.json'));native('assets:sync',false);put('.gate/wrapper-current.json',raw);});
 checked('same-HEAD histories are untouched',()=>{for(const [target,bytes] of history)assert.deepEqual(fs.readFileSync(path.join(root,'.gate',target,'wrapper-kit-config.json')),bytes);assert.equal(fs.readFileSync(path.join(root,'.gate/perf/wrapper-kit-config.json'),'utf8'),'malformed historical JSON');assert.equal(fs.lstatSync(path.join(root,'.gate/e2e/wrapper-kit-config.json')).isSymbolicLink(),true);});
 console.log(JSON.stringify({schema:1,check:'bootstrap-current-fixtures',status:'pass',checks,commands}));
}finally{fs.rmSync(parent,{recursive:true,force:true});}
