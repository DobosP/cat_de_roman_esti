import { readFileSync,writeFileSync,mkdirSync,rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import path from 'node:path';
import assert from 'node:assert/strict';
const lane=process.argv[2],target=process.argv[3]??'full';
assert.equal(target,'full');assert.match(lane??'',/^[a-z][a-z-]*$/);assert.match(process.env.GATE_SHA??'',/^[a-f0-9]{40}([a-f0-9]{24})?$/);assert.match(process.env.GATE_TREE_SHA256??'',/^[a-f0-9]{64}$/);assert.match(process.env.GATE_APP_IMAGE_ID??'',/^sha256:[a-f0-9]{64}$/);
for(const suffix of ['', '-discovery', '-execution'])rmSync(`.gate/${target}/browser-${lane}${suffix}.json`,{force:true});
const inventoryBytes=readFileSync('web-kit/sample/e2e/inventory.json');
const inventory=JSON.parse(inventoryBytes);assert.equal(inventory.schema,1);
const expected=inventory.cases.filter(x=>x.lane===lane);assert.ok(expected.length,'committed lane inventory is required');
assert.equal(new Set(inventory.cases.map(x=>`${x.project}:${x.file}:${x.title}`)).size,inventory.cases.length,'committed cases must be distinct');assert.ok(expected.every(x=>x.project==='motion-on'&&x.title.startsWith(`${lane} `)),'committed lane must bind the actual project and title');
function report(list){
  const args=['node_modules/@playwright/test/cli.js','test','--project=motion-on',`--grep=${lane}`,'--reporter=json'];if(list)args.push('--list');
  const r=spawnSync('node',args,{encoding:'utf8',maxBuffer:32*1024*1024});if(r.stderr)process.stderr.write(r.stderr);
  mkdirSync(`.gate/${target}`,{recursive:true});writeFileSync(`.gate/${target}/browser-${lane}-${list?'discovery':'execution'}.json`,r.stdout);
  const data=JSON.parse(r.stdout);const failed=collect(data).filter(c=>c.results?.some(r=>r.status!=='passed')).map(c=>({id:c.id,title:c.title,status:c.status,results:c.results}));
  assert.equal(r.status,0,`Playwright ${list?'list':'execution'} failed: ${JSON.stringify(failed)}; errors=${JSON.stringify(data.errors??[])}`);
  assert.deepEqual(data.errors??[],[],'browser global errors');return data;
}
function collect(data){const cases=[];const visit=suite=>{for(const spec of suite.specs??[])for(const test of spec.tests??[]){
  const file=path.isAbsolute(spec.file)?path.relative(process.cwd(),spec.file):path.relative(process.cwd(),path.resolve(data.config.rootDir,spec.file));
  cases.push({id:spec.id,project:test.projectName,file,title:spec.title,expectedStatus:test.expectedStatus,status:test.status,results:test.results,ok:spec.ok});
}for(const child of suite.suites??[])visit(child);};for(const suite of data.suites??[])visit(suite);return cases;}
const key=x=>`${x.project}:${x.file}:${x.title}`;
const listed=collect(report(true));assert.deepEqual(listed.map(key).sort(),expected.map(key).sort(),'actual discovery must equal committed case inventory');
assert.equal(new Set(listed.map(x=>x.id)).size,listed.length,'distinct actual browser case IDs');
const executed=report(false),cases=collect(executed);assert.deepEqual(cases.map(key).sort(),expected.map(key).sort(),'executed matrix differs from committed cases');assert.deepEqual(cases.map(x=>x.id).sort(),listed.map(x=>x.id).sort(),'discovery/execution IDs differ');
for(const c of cases){assert.ok(c.id,'actual browser case ID');assert.equal(c.expectedStatus,'passed','case expectation cannot be skipped or failed');assert.equal(c.status,'expected');assert.equal(c.ok,true);assert.equal(c.results.length,1,'retries/duplicate results forbidden');assert.equal(c.results[0].retry,0);assert.equal(c.results[0].status,'passed');assert.ok(c.results[0].duration>=0);}
assert.equal(executed.stats.expected,expected.length);for(const k of ['unexpected','skipped','flaky'])assert.equal(executed.stats[k],0,`browser ${k} forbidden`);
const receipt={schema:1,lane,sha:process.env.GATE_SHA,tree_sha256:process.env.GATE_TREE_SHA256,app_image_id:process.env.GATE_APP_IMAGE_ID,inventory_sha256:createHash('sha256').update(inventoryBytes).digest('hex'),expected_count:expected.length,cases};
mkdirSync(`.gate/${target}`,{recursive:true});writeFileSync(`.gate/${target}/browser-${lane}.json`,JSON.stringify(receipt,null,2)+'\n');
console.log(`browser ${lane}: ${cases.length} actual IDs passed, no skip/retry/partial matrix`);
