import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
for(const [source,template] of [['scripts/gate.sh','gate.sh'],['compose.gate.yml','compose.gate.yml'],['Taskfile.yml','Taskfile.yml'],['Dockerfile.toolchain','Dockerfile.toolchain']])assert.ok(readFileSync(source).equals(readFileSync(`web-kit/templates/${template}`)),`byte identity ${source}`);
const keys=p=>readFileSync(p,'utf8').split('\n').filter(line=>/^[A-Z_]+=/.test(line)).map(line=>line.split('=')[0]).sort();const a=keys('.gate.env'),b=keys('web-kit/templates/.gate.env');assert.equal(a.length,11);assert.equal(new Set(a).size,11);assert.deepEqual(a,b);assert.ok(!a.includes('CORE_TAG'),'CORE_TAG never belongs to gate environment');
console.log('template-identity: four exact files and eleven-key environment contract');
