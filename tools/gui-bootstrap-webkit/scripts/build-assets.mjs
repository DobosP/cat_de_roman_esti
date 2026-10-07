import { readFileSync,writeFileSync,readdirSync,copyFileSync,mkdirSync,lstatSync,unlinkSync } from 'node:fs';
import { gzipSync,brotliCompressSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import { dirname,join,relative,resolve,sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { INVENTORY,sourceInventory } from './vite-inventory.mjs';

const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const portable=value=>value.split(sep).join('/');
function files(root) {
  const out=[];
  function walk(dir) {
    for(const name of readdirSync(dir).sort()) {
      const path=join(dir,name),stat=lstatSync(path);
      if(stat.isSymbolicLink())throw new Error('asset processing refuses symlinks');
      if(stat.isDirectory())walk(path);else if(stat.isFile())out.push(portable(relative(root,path)));else throw new Error('asset processing refuses nonregular files');
    }
  }
  walk(root);return out;
}
export function buildAssets(root=process.cwd()) {
  root=resolve(root);const dist=join(root,'dist');
  const inventory=JSON.parse(readFileSync(join(dist,INVENTORY),'utf8'));
  if(inventory.schema!==1||!Array.isArray(inventory.outputs)||!inventory.outputs.length)throw new Error('actual Vite bundle inventory required');
  if(inventory.source?.sha256!==sourceInventory(root).sha256)throw new Error('Vite inventory does not bind current src tree');
  const expected=new Set(),removed=[],copied=[];
  for(const item of inventory.outputs) {
    if(typeof item.path!=='string'||item.path.startsWith('/')||item.path.split('/').includes('..')||expected.has(item.path))throw new Error('unsafe/duplicate bundle inventory output');
    const path=join(dist,item.path),bytes=readFileSync(path);if(hash(bytes)!==item.sha256||bytes.length!==item.bytes)throw new Error('written Vite output differs from inventory');
    expected.add(item.path);
  }
  for(const item of inventory.outputs.filter(x=>x.type==='chunk'))for(const imported of [...item.imports,...item.dynamicImports]) {
    if(imported.startsWith('.')||expected.has(imported)) {
      const target=portable(relative(dist,resolve(dirname(join(dist,item.path)),imported)));
      if(!expected.has(target)&&!expected.has(imported))throw new Error('Vite chunk references output outside actual bundle');
    }
  }
  const cssSources=files(join(root,'src')).filter(p=>p.endsWith('.css'));
  for(const path of cssSources) {
    const dest=join(dist,path);mkdirSync(dirname(dest),{recursive:true});copyFileSync(join(root,'src',path),dest);expected.add(path);copied.push(path);
  }
  for(const name of ['tokens','theme-teacher','theme-cat','theme-social']) {
    const path=name+'.css';copyFileSync(join(root,'src/tokens',path),join(dist,path));expected.add(path);copied.push(path);
  }
  // Declarations survive. Compiler state is never a distribution asset; collect
  // stale caches as well as obsolete runtime assets and their sidecars.
  for(const path of files(dist)) {
    const base=path.replace(/\.(?:gz|br)$/,'');
    if(base.endsWith('.tsbuildinfo')||(/\.(?:js|mjs|cjs|css)$/.test(base)&&!expected.has(base))) {unlinkSync(join(dist,path));removed.push(path);}
  }
  const measured=[];
  for(const path of [...expected].filter(p=>/\.(?:js|mjs|cjs|css)$/.test(p)).sort()) {
    const bytes=readFileSync(join(dist,path)),gz=gzipSync(bytes),br=brotliCompressSync(bytes);
    writeFileSync(join(dist,path+'.gz'),gz);writeFileSync(join(dist,path+'.br'),br);
    if(path.endsWith('.css')) {
      // An external-module stub resolves this exact CSS filename in strict
      // bundler TS configurations; no ambient wildcard hides broken CSS paths.
      writeFileSync(join(dist,path.replace(/\.css$/,'.d.css.ts')),'// Plain stylesheet side-effect module.\nexport {};\n');
    }
    measured.push({path,bytes:bytes.length,gz:gz.length,br:br.length,sha256:hash(bytes)});
  }
  // Published inventory is independent of previous build state. Preserve the
  // report shape while keeping volatile pruning diagnostics in stdout only.
  const report={schema:1,source_sha256:inventory.source.sha256,inventory_sha256:hash(readFileSync(join(dist,INVENTORY))),removed:[],copied_css:[...new Set(copied)].sort(),assets:measured};
  writeFileSync(join(dist,'.roedu-asset-report.json'),JSON.stringify(report,null,2)+'\n');
  return {...report,removed:removed.sort()};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  try{process.stdout.write(JSON.stringify(buildAssets())+'\n');}catch(error){process.stderr.write(error.message+'\n');process.exitCode=1;}
}
