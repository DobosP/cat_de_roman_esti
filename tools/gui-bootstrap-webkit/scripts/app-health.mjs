import assert from 'node:assert/strict';
import { readFileSync,writeFileSync,mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
assert.ok(process.env.GATE_APP_URL,'full requires live app URL');
assert.match(process.env.GATE_APP_IMAGE_ID??'',/^sha256:[0-9a-f]{64}$/,'host built/running immutable image ID');
const r=await fetch(`${process.env.GATE_APP_URL}/healthz`);assert.equal(r.status,200);console.log(await r.text());
const identityResponse=await fetch(`${process.env.GATE_APP_URL}/__gate/identity`);assert.equal(identityResponse.status,200);
const identity=await identityResponse.json();assert.equal(identity.sha,process.env.GATE_SHA);assert.equal(identity.tree_sha256,process.env.GATE_TREE_SHA256);
assert.equal(identity.versions_lock_sha256,createHash('sha256').update(readFileSync('versions.lock.json')).digest('hex'));
const build=spawnSync('npm',['run','build:sample'],{stdio:'inherit'});assert.equal(build.status,0,'independent runner asset build');
assert.equal(identity.manifest_sha256,createHash('sha256').update(readFileSync('web-kit/sample/embedfs/dist/.vite/manifest.json')).digest('hex'),'actual runtime asset manifest matches independent source build');console.log('actual image source/tree/asset/lock witness',identity);
const manifest=JSON.parse(readFileSync('web-kit/sample/embedfs/dist/.vite/manifest.json'));
const entries=new Set(),files=new Set();
function visit(key){if(entries.has(key))return;entries.add(key);const entry=manifest[key];assert.ok(entry,`entry closure missing ${key}`);files.add(entry.file);for(const file of [...entry.css??[],...entry.assets??[]])files.add(file);for(const dep of [...entry.imports??[],...entry.dynamicImports??[]])visit(dep);}
visit('src/sample/main.ts');
const assetBodies=[];
for(const file of files){assert.ok(!file.startsWith('/')&&!file.split('/').includes('..'),'relative manifest file');const requested=new URL(`/static/${file}`,process.env.GATE_APP_URL).href;const response=await fetch(requested,{redirect:'error'});assert.equal(response.status,200,`live asset ${file}`);assert.equal(response.url,requested,'asset origin/path binding');const actual=Buffer.from(await response.arrayBuffer()),expected=readFileSync(`web-kit/sample/embedfs/dist/${file}`);assert.deepEqual(actual,expected,`live asset body ${file} differs from independent build`);assetBodies.push({file,url:response.url,bytes:actual.length,sha256:createHash('sha256').update(actual).digest('hex')});}
assert.ok(assetBodies.some(x=>x.file.endsWith('.js'))&&assetBodies.some(x=>x.file.endsWith('.css')),'actual JS and CSS closure required');
mkdirSync('.gate/full',{recursive:true});writeFileSync('.gate/full/app-witness.json',JSON.stringify({schema:1,sha:process.env.GATE_SHA,tree_sha256:process.env.GATE_TREE_SHA256,app_image_id:process.env.GATE_APP_IMAGE_ID,identity,entry:'src/sample/main.ts',entries:[...entries],assets:assetBodies},null,2)+'\n');
