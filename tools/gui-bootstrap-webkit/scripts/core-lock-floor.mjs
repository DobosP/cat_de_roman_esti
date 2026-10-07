import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, relative, resolve } from 'node:path';
import { inside, localPath, posix, readLocal } from '../lint/validation-files.mjs';
import { readTarGz, isPythonBytecodePath } from './kit-sync.mjs';
// Read regular npm tar entries in memory; never extract paths, links or files.
export function tarFile(bytes,name) {
  const entries=readTarGz(bytes);
  for(const file of entries.keys())if(isPythonBytecodePath(file))throw new Error(`Excluded Python bytecode/cache in core-floor archive: ${file}`);
  const found=entries.get(name);
  if(!found)throw new Error(`npm archive lacks ${name}`);
  if(found.type!=='file')throw new Error('npm lock must be a regular archive file');
  return found.data;
}
export function consumerCoreFloor(root,config,manifests) {
  const candidates=manifests.flatMap(({path,data})=> {
    const spec=data.dependencies?.['@roedu/web-kit']??data.devDependencies?.['@roedu/web-kit'];
    return spec?[{path,spec}]:[];
  });
  if(!candidates.length)throw new Error('consumer needs the vendored @roedu/web-kit dependency');
  const floors=[];
  for(const {path,spec} of candidates) {
    if(!spec.startsWith('file:')||!spec.endsWith('.tgz'))throw new Error('web-kit must use a vendored file tarball');
    const archive=resolve(root,dirname(path),spec.slice(5));
    const vendor=localPath(root,config.vendor_dir);
    if(!inside(vendor,archive))throw new Error('web-kit tarball outside configured vendor_dir');
    const rel=posix(relative(root,archive)),bytes=readFileSync(localPath(root,rel));
    const actual=createHash('sha256').update(bytes).digest('hex');
    const recorded=readLocal(root,rel+'.sha256').trim().split(/\s+/)[0];
    if(!/^[a-f0-9]{64}$/.test(recorded)||recorded!==actual)throw new Error('vendored web-kit hash mismatch');
    floors.push(JSON.parse(tarFile(bytes,'package/versions.lock.json')));
  }
  // Exact deep comparisons are done by versions-check; here all consumers of
  // the tarball must first agree on the same complete incoming core lock bytes.
  if(floors.some(f=>JSON.stringify(f)!==JSON.stringify(floors[0])))throw new Error('multiple packages use different web-kit core floors');
  return floors[0];
}
