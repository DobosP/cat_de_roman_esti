import { readFileSync,writeFileSync,mkdtempSync,mkdirSync,rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';
import path from 'node:path';
const root=process.cwd();
const records=JSON.parse(readFileSync('web-kit/testdata/versions/registry.json'));
// Fixture dates preserve observed day precision; synthetic tag mutation tests fallback.
const base=JSON.parse(readFileSync('versions.lock.json'));
const dir=mkdtempSync('/scratch/_temp/resolver-test-');
try {
  mkdirSync(`${dir}/web-kit`);writeFileSync(`${dir}/package.json`,'{}');writeFileSync(`${dir}/web-kit/package.json`,'{}');
  const selected=base.tools.filter(e=>['preact','@babel/core'].includes(e.tool));
  const resolve=(tools,fixture=records)=>{
    writeFileSync(`${dir}/versions.lock.json`,JSON.stringify({...base,tools}));writeFileSync(`${dir}/fixture.json`,JSON.stringify(fixture));
    const out=spawnSync('node',[path.join(root,'web-kit/scripts/resolve-versions.mjs'),'--fixture',`${dir}/fixture.json`],{cwd:dir,encoding:'utf8'});return out;
  };
  assert.equal(resolve(selected).status,0,'recorded current stable resolution');
  assert.equal(JSON.parse(readFileSync(`${dir}/versions.lock.json`)).tools.find(x=>x.tool==='@babel/core').version,'7.29.7','approved Babel7 exception');
  const prerelease=structuredClone(records);prerelease['https://registry.npmjs.org/preact']['dist-tags'].latest='11.0.0-rc.4';
  assert.equal(resolve(selected,prerelease).status,0,'non-prerelease fallback');
  const higher=structuredClone(selected);higher[0].version='12.0.0';assert.notEqual(resolve(higher).status,0,'no downgrade');
  const unavailable=structuredClone(records);unavailable['https://registry.npmjs.org/preact'].versions={'11.0.0-rc.4':{}};unavailable['https://registry.npmjs.org/preact']['dist-tags'].latest='11.0.0-rc.4';assert.notEqual(resolve(selected,unavailable).status,0,'prerelease-only refusal');
  console.log('resolver fixtures: observed stable/Babel7, prerelease fallback, downgrade and unavailable stable guards');
}finally{rmSync(dir,{recursive:true,force:true});}
