import { readFileSync,existsSync,lstatSync,realpathSync } from 'node:fs';
import { gzipSync,gunzipSync } from 'node:zlib';
import path from 'node:path';
import assert from 'node:assert/strict';
import { validate } from '../schemas/validate.mjs';
const schema=JSON.parse(readFileSync(new URL('../schemas/budgets.schema.json',import.meta.url)));
const names=set=>[...set].sort();
const equalNames=(a=[],b=[])=>JSON.stringify(names(new Set(a)))===JSON.stringify(names(new Set(b)));
function fields(value,allowed,required){assert.ok(value&&typeof value==='object'&&!Array.isArray(value),'object required');for(const key of required)assert.ok(Object.hasOwn(value,key),`missing ${key}`);for(const key of Object.keys(value))assert.ok(allowed.includes(key),`unknown config field ${key}`);}
function stringList(value){assert.ok(Array.isArray(value)&&value.every(x=>typeof x==='string'&&x),'explicit string list required');}
function measurement(scope,name,actual,limit,files){
  const row={scope,name,actual_gz:actual,limit_gz:limit.limit_gz,status:limit.limit_gz===null?'recorded':actual<=limit.limit_gz?'pass':'fail',files:names(files)};
  if(Object.hasOwn(limit,'target_gz'))Object.assign(row,{target_gz:limit.target_gz,target_status:actual<=limit.target_gz?'met':'unmet'});
  return row;
}
/** Limits come only from validated committed budgets; config contains attribution only. */
export function evaluate(budgets,manifest,routeInventory,config,assetsRoot){
  validate(schema,budgets);
  fields(config,['schema','routes','global_css','vendors'],['schema','routes','global_css','vendors']);assert.equal(config.schema,1);
  fields(config.routes,Object.keys(config.routes),[]);fields(config.vendors,Object.keys(config.vendors),[]);stringList(config.global_css);
  assert.ok(Array.isArray(routeInventory)&&routeInventory.length,'nonempty exported route inventory required');
  assert.ok(manifest&&typeof manifest==='object'&&Object.keys(manifest).length,'nonempty actual manifest required');
  const base=realpathSync(assetsRoot);
  const safeFile=file=>{assert.ok(typeof file==='string'&&file&&!path.isAbsolute(file)&&!file.split('/').some(p=>!p||p==='.'||p==='..')&&!file.includes('\\'),'unsafe asset path');const resolved=path.join(base,file);assert.ok(lstatSync(resolved).isFile()&&!lstatSync(resolved).isSymbolicLink(),'regular asset required');assert.ok(realpathSync(resolved).startsWith(base+path.sep),'asset escaped root');return resolved;};
  const size=file=>{const actual=readFileSync(safeFile(file));if(existsSync(path.join(base,file+'.gz'))){const gzip=readFileSync(safeFile(file+'.gz'));assert.ok(gunzipSync(gzip,{maxOutputLength:actual.length+1}).equals(actual),`stale gzip asset ${file}`);return gzip.length;}return gzipSync(actual,{level:6}).length;};
  for(const [key,entry] of Object.entries(manifest)){
    assert.ok(key&&entry&&typeof entry.file==='string','invalid manifest entry');safeFile(entry.file);
    for(const file of [...(entry.css??[]),...(entry.assets??[])])safeFile(file);
    for(const dep of [...(entry.imports??[]),...(entry.dynamicImports??[])])assert.ok(Object.hasOwn(manifest,dep),`missing manifest dependency ${dep}`);
  }
  const pages=new Map(),nonPages=[],known=new Set();
  for(const route of routeInventory){assert.ok(route.name&&!known.has(route.name),'duplicate or unnamed route');known.add(route.name);if(route.template)pages.set(route.name,route);else nonPages.push(route.name);}
  assert.ok(pages.size,'exported inventory has no HTML pages');
  for(const name of [...Object.keys(config.routes),...Object.keys(budgets.routes)])assert.ok(pages.has(name),`binding for unknown/non-page route ${name}`);
  const css=new Set(config.global_css);for(const file of css)assert.ok(file.endsWith('.css'),'global CSS binding must be CSS');
  const sum=set=>names(set).reduce((n,file)=>n+size(file),0);
  const collect=(key,js,styles,visited)=>{if(visited.has(key))return;visited.add(key);const entry=manifest[key];assert.ok(entry,`missing entry ${key}`);if(/\.m?js$/.test(entry.file))js.add(entry.file);else if(entry.file.endsWith('.css'))styles.add(entry.file);else assert.fail('budget entry must be JS/CSS');for(const file of entry.css??[])styles.add(file);for(const dep of entry.imports??[])collect(dep,js,styles,visited);};
  const report={schema:1,status:'pass',global_css:measurement('global-css','global',sum(css),budgets.css.global,css),routes:[],vendors:[],unused_limits:[],non_page_routes:nonPages.sort(),vitals_limits:budgets.vitals,unmeasured_metrics:['lcp_ms','inp_ms']};
  const usedClasses=new Set(),usedVendors=new Set();
  for(const name of names(new Set(pages.keys()))){
    const binding=config.routes[name];fields(binding,['class','entries','islands','widgets','vendors'],['class','entries']);stringList(binding.entries);stringList(binding.islands??[]);stringList(binding.widgets??[]);
    const limit=budgets.js[binding.class];assert.ok(limit&&Object.hasOwn(limit,'limit_gz'),'unknown route budget class');
    if(Object.keys(budgets.routes).length){const declared=budgets.routes[name];assert.ok(declared,`route missing from committed budgets ${name}`);assert.ok(binding.class===declared.class&&equalNames(binding.islands,declared.islands)&&equalNames(binding.widgets,declared.widgets),'binding disagrees with committed route budget');}
    usedClasses.add(binding.class);const js=new Set(),styles=new Set(css),visited=new Set();
    for(const entry of [...binding.entries,...(binding.islands??[]),...(binding.widgets??[])])collect(entry,js,styles,visited);
    for(const vendor of binding.vendors??[]){fields(vendor,['name','entry','eager'],['name','entry','eager']);assert.equal(typeof vendor.eager,'boolean');assert.ok(vendor.name&&vendor.entry&&budgets.js['vendor-gated'][vendor.name],'vendor lacks committed budget');assert.equal(config.vendors[vendor.name],vendor.entry,'vendor binding disagrees with global declaration');usedVendors.add(vendor.name);if(vendor.eager)collect(vendor.entry,js,styles,visited);}
    report.routes.push({name,class:binding.class,js:measurement('route-js',name,sum(js),limit,js),css:measurement('route-css',name,sum(styles),budgets.css.global,styles)});
  }
  for(const name of Object.keys(config.vendors).sort()){
    const limit=budgets.js['vendor-gated'][name];assert.ok(limit,'vendor lacks committed limit');const js=new Set(),styles=new Set();collect(config.vendors[name],js,styles,new Set());report.vendors.push(measurement('vendor-gated',name,sum(js),limit,js));usedVendors.add(name);
  }
  for(const name of ['server-page','island-route','cat-initial'])if(!usedClasses.has(name))report.unused_limits.push({name:`js.${name}`,limit_gz:budgets.js[name].limit_gz,...(Object.hasOwn(budgets.js[name],'target_gz')?{target_gz:budgets.js[name].target_gz}:{}),reason:'no route declares this class'});
  for(const name of Object.keys(budgets.js['vendor-gated']))if(!usedVendors.has(name))report.unused_limits.push({name:`js.vendor-gated.${name}`,limit_gz:budgets.js['vendor-gated'][name].limit_gz,reason:'no vendor binding declares this asset'});
  report.unused_limits.sort((a,b)=>a.name.localeCompare(b.name));
  if([report.global_css,...report.routes.flatMap(r=>[r.js,r.css]),...report.vendors].some(row=>row.status==='fail'))report.status='fail';
  return report;
}
/** Gate schema uses the same measured limits/actuals with a stable explicit name. */
export function gateBudgets(report){return Object.fromEntries([report.global_css,...report.routes.flatMap(r=>[r.js,r.css]),...report.vendors].map(row=>[`${row.scope}:${row.name}`,{limit:row.limit_gz,actual:row.actual_gz,status:row.status}]));}
