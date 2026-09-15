import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { chromium, expect } from '/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v95-discovery-and-game-quality/frontend/node_modules/@playwright/test/index.mjs';
const ROOT='/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v95-discovery-and-game-quality';
const OUT='/home/dobo/work/_temp/feat__v95-discovery-and-game-quality/gui/independent-browser-final';
const BASE='http://127.0.0.1:8150', OLD='http://127.0.0.1:8160', API='/api/alchimie/explore', SAVE='cat_alchimie_exploration_v1';
const hash=v=>createHash('sha256').update(v).digest('hex'),sha=p=>hash(readFileSync(p));
const sources=['frontend/src/screens/AlchimieExplore.tsx','frontend/src/api/alchimieExplore.ts','frontend/src/styles/alchimie-explore.css','cat_de_roman_esti/wordgames/alchimie_explore.py','cat_de_roman_esti/wordgames/discovery_world.py','cat_de_roman_esti/web/static/.vite/manifest.json'];
const sourceHashes=Object.fromEntries(sources.map(p=>[p,sha(ROOT+'/'+p)]));
const manifest=JSON.parse(readFileSync(ROOT+'/cat_de_roman_esti/web/static/.vite/manifest.json'));
const assets=[manifest['index.html'].file,...manifest['index.html'].css,manifest['src/screens/Alchimie.tsx'].file,...manifest['src/screens/Alchimie.tsx'].css];
const assetChecks=[];
for(const file of assets){const r=await fetch(BASE+'/'+file);assert.equal(r.status,200);const h=hash(Buffer.from(await r.arrayBuffer()));assert.equal(h,sha(ROOT+'/cat_de_roman_esti/web/static/'+file));assetChecks.push({file,sha256:h});}
const browser=await chromium.launch({headless:true});const results=[];
const word=(p,label)=>p.locator('.alchemy-inventory-grid').getByRole('button',{name:new RegExp('^'+label+'(?:,|$)')});
const response=(p,path,method='POST')=>p.waitForResponse(r=>r.request().method()===method&&new URL(r.url()).pathname===path);
const save=p=>p.evaluate(k=>localStorage.getItem(k),SAVE);
async function start({origin=BASE,width=1280,zoom=100,clock=false}={}){
 const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'}), page=await context.newPage();const requests=[],errors=[];
 page.on('request',r=>{if(new URL(r.url()).pathname.startsWith(API))requests.push({method:r.method(),path:new URL(r.url()).pathname,body:r.postData()});});page.on('pageerror',e=>errors.push(String(e)));
 if(zoom!==100)await page.addInitScript(z=>document.addEventListener('DOMContentLoaded',()=>document.documentElement.style.fontSize=z+'%'),zoom);
 if(clock)await page.clock.install();
 await page.goto(origin+'/alchimie');const wait=response(page,API);await page.getByRole('button',{name:'Începe explorarea →'}).click();const state=await(await wait).json();await expect(word(page,'Făină')).toBeEnabled();return {context,page,state,requests,errors};
}
async function clickCraft(t,a,b){await word(t.page,a).click();const wait=response(t.page,API+'/'+t.state.game_id+'/combine');await word(t.page,b).click();const data=await(await wait).json();await expect(word(t.page,a)).toBeEnabled();return data;}
async function tabTo(page,target){for(let i=0;i<70;i++){if(await target.evaluate(e=>e===document.activeElement))return;await page.keyboard.press('Tab');}throw Error('Cannot tab to '+await target.textContent());}
async function geometry(page){return page.evaluate(()=>{const screen=document.querySelector('.alchemy-screen');return {viewport:innerWidth,documentWidth:document.documentElement.scrollWidth,screenWidth:screen.clientWidth,screenScrollWidth:screen.scrollWidth,rootFont:getComputedStyle(document.documentElement).fontSize,elements:[...document.querySelectorAll('.alchemy-feedback,.alchemy-word--tried,.alchemy-word--tried .alchemy-word-label,.alchemy-word--tried .alchemy-word-meta')].map(e=>{const r=e.getBoundingClientRect();return{text:e.textContent,left:r.left,right:r.right,top:r.top,bottom:r.bottom,clientWidth:e.clientWidth,scrollWidth:e.scrollWidth,clientHeight:e.clientHeight,scrollHeight:e.scrollHeight};})};});}
try{
 // One interaction comparison on real old and new servers.
 for(const [origin,expectedPosts,label] of [[OLD,2,'baseline'],[BASE,1,'candidate']]){
  const t=await start({origin,width:390});const first=await clickCraft(t,'Făină','Cheag alimentar');assert.equal(first.result,null);
  const beforeSave=await save(t.page);let wait;
  if(label==='baseline')wait=response(t.page,API+'/'+t.state.game_id+'/combine');
  await word(t.page,'Cheag alimentar').click();if(wait)await wait;else await expect(t.page.locator('.alchemy-feedback')).toContainText('ai încercat deja');
  const posts=t.requests.filter(r=>r.path.endsWith('/combine')).length;assert.equal(posts,expectedPosts);
  const marked=await word(t.page,'Cheag alimentar').getAttribute('class');assert.equal(marked.includes('alchemy-word--tried'),label==='candidate');
  if(label==='candidate')assert.equal(await save(t.page),beforeSave);
  await t.page.screenshot({path:OUT+'/'+label+'-mobile.png',fullPage:true});
  results.push({scenario:label+'-repeat',combineRequests:posts,world:t.state.world,marked:marked.includes('alchemy-word--tried'),feedback:await t.page.locator('.alchemy-feedback').innerText(),screenshot:label+'-mobile.png',pageErrors:t.errors});assert.equal(t.errors.length,0);await t.context.close();
 }
 // Independent keyboard/drag/narrow geometry with actual repeated/reversed pair.
 {
  const t=await start({width:320,zoom:200});await clickCraft(t,'Făină','Cheag alimentar');
  await expect(word(t.page,'Cheag alimentar')).toHaveAccessibleName('Cheag alimentar, încercat fără rezultat cu Făină');
  await tabTo(t.page,word(t.page,'Cheag alimentar'));await t.page.keyboard.press('Space');await expect(word(t.page,'Cheag alimentar')).toBeFocused();
  const raw=await save(t.page),count=t.requests.length;
  await word(t.page,'Făină').click();await word(t.page,'Cheag alimentar').click();await expect(word(t.page,'Făină')).toHaveClass(/alchemy-word--tried/);
  await tabTo(t.page,word(t.page,'Făină'));await t.page.keyboard.press('Enter');await expect(word(t.page,'Făină')).toBeFocused();
  // Second identical local response must retain focus as well.
  await t.page.keyboard.press('Enter');await expect(word(t.page,'Făină')).toBeFocused();
  const geom=await geometry(t.page);assert(geom.documentWidth<=geom.viewport+1);assert(geom.screenScrollWidth<=geom.screenWidth+1);
  for(const e of geom.elements){assert(e.left>=-1&&e.right<=321,e.text+' outside viewport horizontally');assert(e.scrollWidth<=e.clientWidth+1,e.text+' horizontal clip');assert(e.scrollHeight<=e.clientHeight+1,e.text+' vertical clip');}
  await t.page.screenshot({path:OUT+'/narrow-keyboard.png',fullPage:true});
  assert.equal(t.requests.length,count);assert.equal(await save(t.page),raw);
  await word(t.page,'Cheag alimentar').click();
  await word(t.page,'Făină').dragTo(word(t.page,'Cheag alimentar'));await expect(t.page.locator('.alchemy-feedback')).toContainText('ai încercat deja');assert.equal(t.requests.length,count);
  await word(t.page,'Lapte').click();await expect(word(t.page,'Făină')).not.toHaveClass(/alchemy-word--tried/);await expect(word(t.page,'Cheag alimentar')).not.toHaveClass(/alchemy-word--tried/);
  results.push({scenario:'narrow-keyboard-reverse-drag',width:320,zoom:200,noPostOnLocal:true,saveUnchanged:true,geometry:geom,screenshot:'narrow-keyboard.png',pageErrors:t.errors});assert.equal(t.errors.length,0);await t.context.close();
 }
 // Trusted GET after lost response; a failed pre-send request cannot invent memory.
 for(const committed of [false,true]){
  const t=await start();const path=API+'/'+t.state.game_id;
  await t.page.route('**'+path+'/combine',async route=>{if(committed)await route.fetch();await route.abort('failed');},{times:1});
  await word(t.page,'Făină').click();const wait=response(t.page,path,'GET');await word(t.page,'Cheag alimentar').click();const recovered=await(await wait).json();await expect(word(t.page,'Făină')).toBeEnabled();await word(t.page,'Făină').click();
  assert.equal(recovered.empty_pairs.length,committed?1:0);assert.equal((await word(t.page,'Cheag alimentar').getAttribute('class')).includes('alchemy-word--tried'),committed);
  results.push({scenario:'lost-response-'+(committed?'committed':'not-committed'),observedCount:recovered.empty_pairs.length,postCount:t.requests.filter(r=>r.path.endsWith('/combine')).length,getRecoveryCount:t.requests.filter(r=>r.method==='GET').length,pageErrors:t.errors});assert.equal(t.errors.length,0);await t.context.close();
 }
 // Reload retains trusted live observations; expired session restores earned crafts but drops negatives.
 {
  const t=await start();let state=await clickCraft(t,'Făină','Cheag alimentar');await t.page.reload();await expect(word(t.page,'Făină')).toBeEnabled();await word(t.page,'Făină').click();await expect(word(t.page,'Cheag alimentar')).toHaveClass(/alchemy-word--tried/);
  const good=response(t.page,API+'/'+t.state.game_id+'/combine');await word(t.page,'Apă').click();state=await(await good).json();assert(state.discovered.some(x=>x.label==='Aluat'));await expect(word(t.page,'Aluat')).toBeEnabled();
  const earned=state.progress.discoveries;
  await t.page.evaluate(k=>{const s=JSON.parse(localStorage.getItem(k));s.game_id='expired-independent-v95';localStorage.setItem(k,JSON.stringify(s));},SAVE);
  const restored=response(t.page,API);await t.page.reload();state=await(await restored).json();await expect(word(t.page,'Făină')).toBeEnabled();assert.deepEqual(state.progress.discoveries,earned);assert.deepEqual(state.empty_pairs,[]);assert.notEqual(state.game_id,t.state.game_id);
  await word(t.page,'Făină').click();await expect(word(t.page,'Cheag alimentar')).not.toHaveClass(/alchemy-word--tried/);
  results.push({scenario:'reload-expired-save',liveReloadRetainedMark:true,restoredCrafts:earned.length,restoredEmptyPairs:0,pageErrors:t.errors});assert.equal(t.errors.length,0);await t.context.close();
 }
 // Repeated local acknowledgments must not refresh the 30-second trust window.
 {
  const t=await start({clock:true});const first=await clickCraft(t,'Făină','Cheag alimentar');await t.page.clock.fastForward(20_000);await word(t.page,'Cheag alimentar').click();await expect(t.page.locator('.alchemy-feedback')).toContainText('ai încercat deja');assert.equal(t.requests.filter(r=>r.path.endsWith('/combine')).length,1);
  await t.page.clock.fastForward(11_000);const wait=response(t.page,API+'/'+t.state.game_id+'/combine');await word(t.page,'Cheag alimentar').click();const aged=await(await wait).json();assert.equal(aged.revision,first.revision+1);assert.equal(t.requests.filter(r=>r.path.endsWith('/combine')).length,2);
  results.push({scenario:'freshness-not-renewed-by-local-repeat',localAt20Seconds:true,serverRecheckAt31Seconds:true,pageErrors:t.errors});assert.equal(t.errors.length,0);await t.context.close();
 }
 assert.deepEqual(Object.fromEntries(sources.map(p=>[p,sha(ROOT+'/'+p)])),sourceHashes);
 const report={kind:'v95-independent-empty-pair-browser-v1',reviewer:'codex-v95-independent-world-quality',date:'2026-09-16',candidateOrigin:BASE,baselineOrigin:OLD,passed:true,source_sha256:sourceHashes,served_assets:assetChecks,scenarios:results,script_sha256:sha(OUT+'/probe.mjs')};
 for(const r of results)if(r.screenshot)r.screenshot_sha256=sha(OUT+'/'+r.screenshot);
 writeFileSync(OUT+'/probes.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,scenarios:results.map(r=>r.scenario)},null,2));
}finally{await browser.close();}
