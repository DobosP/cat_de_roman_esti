import { readFileSync,mkdtempSync,rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';
const dir=mkdtempSync('/scratch/_temp/tokens-check-');
try {
  const r=spawnSync('node',['src/tokens/generate.mjs',dir],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
  for(const f of ['tokens.css','tokens.ts','theme-teacher.css','theme-cat.css','theme-social.css'].map(x=>'src/tokens/'+x).concat('web-kit/tokens/tokens.go'))assert.deepEqual(readFileSync(f),readFileSync(`${dir}/${f}`),`generated drift: ${f}`);
  assert.deepEqual(readFileSync('web-kit/tokens/testdata/tokens.json'),readFileSync('src/tokens/tokens.json'),'packaged Go DTCG fixture drift');
  console.log('gen-check: all six committed token outputs byte-identical');
}finally{rmSync(dir,{recursive:true,force:true});}
