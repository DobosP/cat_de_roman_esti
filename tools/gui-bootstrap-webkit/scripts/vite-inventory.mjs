import { readFileSync,writeFileSync,readdirSync,lstatSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join,relative,resolve,sep } from 'node:path';
export const INVENTORY='.roedu-vite-bundle.json';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
export function sourceInventory(root) {
  const files=[];
  function walk(dir) {
    for(const name of readdirSync(dir).sort()) {
      const path=join(dir,name),stat=lstatSync(path);
      if(stat.isSymbolicLink())throw new Error('source inventory refuses symlinks');
      if(stat.isDirectory())walk(path);
      else if(stat.isFile())files.push({path:relative(root,path).split(sep).join('/'),sha256:hash(readFileSync(path))});
      else throw new Error('source inventory contains nonregular entry');
    }
  }
  walk(join(root,'src'));
  return {files,sha256:hash(JSON.stringify(files))};
}
/** Final writeBundle output is authoritative, including actual shared chunks.
 * Existing declarations remain intact because Vite emptyOutDir remains false. */
export default function roeduOutputInventory() {
  let root,outDir;
  return {
    name:'roedu-output-inventory',apply:'build',enforce:'post',
    configResolved(config){root=resolve(config.root);outDir=resolve(root,config.build.outDir);},
    writeBundle(options,bundle) {
      const directory=options.dir?resolve(options.dir):outDir;
      const outputs=Object.entries(bundle).sort(([a],[b])=>a.localeCompare(b)).map(([name,item])=> {
        if(name.startsWith('/')||name.split('/').includes('..'))throw new Error('unsafe Vite output filename');
        const bytes=readFileSync(join(directory,name));
        return {path:name,type:item.type,sha256:hash(bytes),bytes:bytes.length,
          ...(item.type==='chunk'?{isEntry:item.isEntry,imports:item.imports,dynamicImports:item.dynamicImports}:{}),
        };
      });
      if(!outputs.some(x=>x.type==='chunk'&&x.isEntry))throw new Error('actual Vite output has no entry chunks');
      writeFileSync(join(directory,INVENTORY),JSON.stringify({schema:1,source:sourceInventory(root),outputs},null,2)+'\n');
    },
  };
}
