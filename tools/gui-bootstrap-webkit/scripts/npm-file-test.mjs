import { mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';
const scratch=mkdtempSync('/scratch/_temp/npm-file-');
function npm(args,cwd){const r=spawnSync('npm',args,{cwd,encoding:'utf8'});assert.equal(r.status,0,`${r.stdout}\n${r.stderr}`);return r.stdout;}
try {
  const fixture=`${scratch}/fixture`,consumer=`${scratch}/consumer`;mkdirSync(fixture);mkdirSync(consumer);
  writeFileSync(`${fixture}/package.json`,JSON.stringify({name:'roedu-local-file-fixture',version:'1.0.0',type:'module',files:['index.js']}));
  writeFileSync(`${fixture}/index.js`,'export const localFixture = true;\n');
  npm(['pack','--ignore-scripts','--pack-destination',scratch],fixture);
  writeFileSync(`${consumer}/package.json`,JSON.stringify({name:'roedu-install-fixture',version:'1.0.0',private:true}));
  npm(['install','--ignore-scripts','--allow-remote=none',`file:${scratch}/roedu-local-file-fixture-1.0.0.tgz`],consumer);
  assert.equal(JSON.parse(readFileSync(`${consumer}/node_modules/roedu-local-file-fixture/package.json`)).version,'1.0.0');
  console.log('npm 12 local file tarball installs with allow-remote=none');
}finally{rmSync(scratch,{recursive:true,force:true});}
