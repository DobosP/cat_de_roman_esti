import { test as base,expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFileSync,writeFileSync,mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import path from 'node:path';
import { validate } from '../schemas/validate.mjs';
const require=createRequire(import.meta.url);
const budgetsSchema=JSON.parse(readFileSync(new URL('../schemas/budgets.schema.json',import.meta.url)));
export { expect };
export function committedBudgets(){const value=JSON.parse(readFileSync('budgets.json'));validate(budgetsSchema,value);return value;}
export const test=base.extend({
  throttle:[async({page},use)=>{
    const t=committedBudgets().vitals.throttle;
    const cdp=await page.context().newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate',{rate:t.cpu});await cdp.send('Network.enable');
    await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:t.rtt_ms,downloadThroughput:t.down_kbps*1000/8,uploadThroughput:t.down_kbps*1000/8});
    try{await use(cdp);}finally{await cdp.detach();}
  },{auto:true}],
});
export function axeFingerprint(results){return createHash('sha256').update(JSON.stringify(results.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,html:n.html})).sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b)))})).sort((a,b)=>a.id.localeCompare(b.id)))).digest('hex');}
/** Use the installed locked axe source rather than a bundled mismatched release. */
export async function auditAxe(page){const axeSource=readFileSync(require.resolve('axe-core'),'utf8');const results=await new AxeBuilder({page,axeSource}).analyze();return {results,fingerprint:axeFingerprint(results),axe_source_sha256:createHash('sha256').update(axeSource).digest('hex')};}
/** Register web-vitals once before navigation and receive actual browser callbacks. */
export async function observeVitals(page){
  const metrics=[];await page.exposeBinding('__roeduVital',(_source,metric)=>{if(!['LCP','INP'].includes(metric.name)||!Number.isFinite(metric.value)||typeof metric.id!=='string')throw Error('Malformed actual Web Vital callback');metrics.push(metric);});
  const modulePath=require.resolve('web-vitals'),source=readFileSync(path.join(path.dirname(modulePath),'web-vitals.iife.js'),'utf8');
  await page.addInitScript({content:source+';webVitals.onLCP(m=>window.__roeduVital({name:m.name,id:m.id,value:m.value,rating:m.rating,entries:m.entries.length}),{reportAllChanges:true});webVitals.onINP(m=>window.__roeduVital({name:m.name,id:m.id,value:m.value,rating:m.rating,entries:m.entries.length}),{reportAllChanges:true,durationThreshold:0});'});
  return {metrics,source_sha256:createHash('sha256').update(source).digest('hex')};
}
export function writeBrowserMeasurement(name,data){if(!/^[a-z-]+$/.test(name))throw Error('Unsafe measurement name');mkdirSync('.gate/full',{recursive:true});const result={schema:1,sha:process.env.GATE_SHA,tree_sha256:process.env.GATE_TREE_SHA256,app_image_id:process.env.GATE_APP_IMAGE_ID,...data};writeFileSync(`.gate/full/${name}-measurement.json`,JSON.stringify(result,null,2)+'\n');return result;}
export const browserPin='mcr.microsoft.com/playwright:v1.63.0-noble';
export const screenshotConfig={snapshotPathTemplate:'{testDir}/../../../baselines/core/chromium/{testFilePath}/{arg}{ext}',expect:{toHaveScreenshot:{animations:'disabled',caret:'hide',maxDiffPixels:0}},metadata:{playwright_image:browserPin}};
