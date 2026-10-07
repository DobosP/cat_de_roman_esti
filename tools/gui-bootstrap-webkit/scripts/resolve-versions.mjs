import { readFileSync,writeFileSync } from 'node:fs';
import assert from 'node:assert/strict';
const fixture=process.argv.indexOf('--fixture');
const recorded=fixture<0?null:JSON.parse(readFileSync(process.argv[fixture+1]));
const get=async url=>{if(recorded){assert.ok(url in recorded,`missing fixture ${url}`);return recorded[url];}const r=await fetch(url);assert.ok(r.ok,`${url}: ${r.status}`);return r.json();};
const stable=v=>/^v?\d+\.\d+\.\d+$/.test(v);
const cmp=(a,b)=>{const aa=a.replace(/^v/,'').split('.').map(Number),bb=b.replace(/^v/,'').split('.').map(Number);for(let i=0;i<3;i++)if(aa[i]!==bb[i])return aa[i]-bb[i];return 0;};
export function selectStable(metadata,major){return Object.keys(metadata.versions).filter(v=>stable(v)&&(!major||v.startsWith(`${major}.`))).sort(cmp).at(-1);}
const lock=JSON.parse(readFileSync('versions.lock.json'));
const date=new Date().toISOString().slice(0,10);
for(const e of lock.tools.filter(e=>e.scope==='core'&&e.version&&e.status!=='banned')){
  if(['playwright','@playwright/test','playwright-image','postgres'].includes(e.tool))continue;
  let v=e.version,source=e.source,released=e.released;
  if(e.kind==='npm'){
    const url=`https://registry.npmjs.org/${e.tool}`;const m=await get(url);
    v=e.tool==='@babel/core'?selectStable(m,7):stable(m['dist-tags'].latest)?m['dist-tags'].latest:selectStable(m);
    assert.ok(v&&stable(v),`${e.tool}: no stable release`);source=`${url}/${v}`;released=m.time?.[v]?.slice(0,10);
  } else if(e.kind==='gomod') {
    const url=`https://proxy.golang.org/${e.tool}/@latest`;const m=await get(url);v=m.Version;assert.ok(stable(v),`${e.tool}: prerelease/pseudo-version`);source=`https://proxy.golang.org/${e.tool}/@v/${v}.info`;released=m.Time.slice(0,10);
  } else if(e.kind==='runtime'&&e.tool==='node'){
    const m=(await get('https://nodejs.org/dist/index.json')).filter(x=>stable(x.version)).sort((a,b)=>cmp(a.version,b.version)).at(-1);v=m.version.slice(1);released=m.date;
    if(v!==e.version)throw new Error(`TOOLCHAIN REBUILD NEEDED node ${e.version}->${v}; checksum/image review required`);
  } else if(e.kind==='runtime'&&e.tool==='go'){
    const m=(await get('https://go.dev/dl/?mode=json')).filter(x=>x.stable).sort((a,b)=>cmp(a.version.slice(2),b.version.slice(2))).at(-1);v=m.version.slice(2);
    if(v!==e.version)throw new Error(`TOOLCHAIN REBUILD NEEDED go ${e.version}->${v}`);
  } else if(e.kind==='image') continue;
  assert.ok(cmp(v,e.version)>=0,`${e.tool}: downgrade ${e.version}->${v}`);
  if(e.rebuild&&v!==e.version)throw new Error(`TOOLCHAIN REBUILD NEEDED ${e.tool} ${e.version}->${v}`);
  console.log(`${e.tool} ${e.version} -> ${v} (${source}, ${date})`);
  e.version=v;e.source=source;e.date=date;if(released)e.released=released;
}
lock.resolved=date;writeFileSync('versions.lock.json',JSON.stringify(lock,null,2)+'\n');
for(const file of ['package.json','web-kit/package.json']){
  const p=JSON.parse(readFileSync(file));for(const group of ['dependencies','devDependencies'])for(const name of Object.keys(p[group]??{})){
    const e=lock.tools.find(e=>e.tool===name);if(e)p[group][name]=e.version;
  }writeFileSync(file,JSON.stringify(p,null,2)+'\n');
}
