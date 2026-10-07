import { dirname, posix } from 'node:path';
export const packageName = (key,row) => row?.name || (key.includes('node_modules/') ? key.split('node_modules/').at(-1) : null);
export const refs = row => ({...row?.dependencies,...row?.devDependencies,...row?.optionalDependencies,...row?.peerDependencies});
export function resolveDependency(packages,parent,name) {
  let cursor=parent;
  while(true) {
    const candidate=(cursor?cursor+'/':'')+'node_modules/'+name;
    if(candidate in packages)return candidate;
    if(!cursor)break;
    const next=posix.dirname(cursor);cursor=next==='.'?'':next;
  }
  return null;
}
export function graph(packages,lockDir,manifestDirs) {
  const incoming=new Map(),owners=new Map();
  for(const [key,row] of Object.entries(packages))for(const name of Object.keys(refs(row))) {
    const target=resolveDependency(packages,key,name);
    if(target) {if(!incoming.has(target))incoming.set(target,new Set());incoming.get(target).add(key);}
  }
  const seeds=Object.keys(packages).filter(k=>!k.includes('node_modules/')&&!packages[k].link);
  function visit(key,owner,seen) {
    if(seen.has(key))return;seen.add(key);
    if(!owners.has(key))owners.set(key,new Set());owners.get(key).add(owner);
    const row=packages[key];if(!row)return;
    if(row.link&&typeof row.resolved==='string'&&packages[row.resolved])visit(row.resolved,owner,seen);
    for(const name of Object.keys(refs(row))) {const target=resolveDependency(packages,key,name);if(target)visit(target,owner,seen);}
  }
  for(const key of seeds) {
    const candidate=posix.normalize((lockDir==='.'?'':lockDir+'/')+key).replace(/\/$/,'')||'.';
    if(manifestDirs.has(candidate))visit(key,candidate,new Set());
  }
  return {incoming,owners};
}
