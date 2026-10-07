import { readFileSync,writeFileSync,mkdirSync } from 'node:fs';
import { gunzipSync,brotliDecompressSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
const target=process.argv[2];assert.ok(['unit','full'].includes(target));const root='web-kit/sample/embedfs/dist/',manifest=JSON.parse(readFileSync(root+'.vite/manifest.json')),files=new Set();
for(const entry of Object.values(manifest))for(const file of [entry.file,...entry.css??[]])if(/\.(?:css|js)$/.test(file))files.add(file);
assert.ok(files.size>0);const hashes=[];
for(const file of [...files].sort()){
  const raw=readFileSync(root+file);assert.deepEqual(gunzipSync(readFileSync(root+file+'.gz')),raw,`final gzip bytes ${file}`);assert.deepEqual(brotliDecompressSync(readFileSync(root+file+'.br')),raw,`final Brotli bytes ${file}`);
  hashes.push({file,bytes:raw.length,gz:readFileSync(root+file+'.gz').length,br:readFileSync(root+file+'.br').length,sha256:createHash('sha256').update(raw).digest('hex')});
}
mkdirSync(`.gate/${target}`,{recursive:true});writeFileSync(`.gate/${target}/precompression.json`,JSON.stringify({schema:1,sha:process.env.GATE_SHA,tree_sha256:process.env.GATE_TREE_SHA256,files:hashes},null,2)+'\n');console.log(`precompression: ${hashes.length} real final JS/CSS files verified in gzip and Brotli`);
