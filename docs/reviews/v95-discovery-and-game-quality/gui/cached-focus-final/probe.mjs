import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {chromium,expect} from '/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v95-discovery-and-game-quality/frontend/node_modules/@playwright/test/index.mjs';
const ROOT='/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v95-discovery-and-game-quality';
const OUT='/home/dobo/work/_temp/feat__v95-discovery-and-game-quality/gui/cached-focus-final';
const BASE='http://127.0.0.1:8150',API='/api/alchimie/explore';
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const manifest=JSON.parse(readFileSync(ROOT+'/cat_de_roman_esti/web/static/.vite/manifest.json'));
const asset=manifest['src/screens/Alchimie.tsx'].file;
const res=await fetch(BASE+'/'+asset);assert.equal(res.status,200);assert.equal(createHash('sha256').update(Buffer.from(await res.arrayBuffer())).digest('hex'),hash(ROOT+'/cat_de_roman_esti/web/static/'+asset));
const browser=await chromium.launch({headless:true});const results=[];
const word=(page,label)=>page.locator('.alchemy-inventory-grid').getByRole('button',{name:new RegExp('^'+label+'(?:,|$)')});
const reply=(page,path,method='POST')=>page.waitForResponse(r=>r.request().method()===method&&new URL(r.url()).pathname===path);
async function focus(page){return page.evaluate(()=>{const e=document.activeElement;const r=e.getBoundingClientRect();return {tag:e.tagName,text:e.textContent,aria:e.getAttribute('aria-label'),top:r.top,bottom:r.bottom,visible:r.top>=0&&r.bottom<=innerHeight,scrollTop:document.querySelector('.screen-pad')?.scrollTop};});}
try{
 for(const mode of ['ordinary-controls','committed-response-loss','uncommitted-response-loss','normal-success']){
  const context=await browser.newContext({viewport:{width:320,height:844},reducedMotion:'reduce'});const page=await context.newPage();const reqs=[];
  await page.addInitScript(()=>{window.__focusLog=[];window.addEventListener('focusin',e=>window.__focusLog.push({tag:e.target.tagName,label:e.target.getAttribute('aria-label'),text:e.target.textContent}));});
  page.on('request',r=>{if(new URL(r.url()).pathname.startsWith(API))reqs.push({method:r.method(),path:new URL(r.url()).pathname});});
  await page.goto(BASE+'/alchimie');const start=reply(page,API);await page.getByRole('button',{name:'Începe explorarea →'}).click();const initial=await(await start).json();const url=API+'/'+initial.game_id;
  await word(page,'Făină').focus();await page.keyboard.press('Enter');let r=reply(page,url+'/combine');await word(page,'Cheag alimentar').focus();await page.keyboard.press('Enter');await r;await expect(word(page,'Cheag alimentar')).toBeEnabled();
  const checkpoints=[{step:'after-first-empty',focus:await focus(page)}];
  for(let n=1;n<=2;n++){await word(page,'Cheag alimentar').focus();await page.keyboard.press('Enter');await expect(page.locator('.alchemy-feedback')).toContainText('ai încercat deja');await expect(word(page,'Cheag alimentar')).toBeFocused();checkpoints.push({step:'cached-'+n,focus:await focus(page)});}
  const count=reqs.filter(r=>r.path.endsWith('/combine')).length;assert.equal(count,1);
  if(mode==='ordinary-controls'){
   await page.keyboard.press('Escape');checkpoints.push({step:'escape',focus:await focus(page)});
   await page.keyboard.press('Tab');await page.keyboard.press('Enter');checkpoints.push({step:'select-next-with-tab-enter',focus:await focus(page)});
   await page.locator('.alchemy-library-tools > summary').focus();await page.keyboard.press('Enter');const search=page.getByRole('searchbox',{name:'Caută în colecție'});await search.focus();await search.fill('lapte');checkpoints.push({step:'search',focus:await focus(page)});
   await word(page,'Lapte').focus();await page.keyboard.press('Escape');await page.keyboard.press('Enter');checkpoints.push({step:'choose-search-result',focus:await focus(page)});
  }else{
   if(mode.includes('response-loss')){
    await page.route('**'+url+'/combine',async route=>{if(mode.startsWith('committed'))await route.fetch();await route.abort('failed');},{times:1});
    r=reply(page,url,'GET');
   }else r=reply(page,url+'/combine');
   await word(page,'Apă').focus();checkpoints.push({step:'water-before-enter',focus:await focus(page)});await page.keyboard.press('Enter');const data=await(await r).json();await expect(word(page,'Apă')).toBeEnabled();
   await page.waitForTimeout(100);checkpoints.push({step:'after-other-operation',focus:await focus(page)});
   results.push({mode,checkpoints,postEmptyRequests:count,finalMessage:await page.locator('.alchemy-feedback').first().innerText(),discoveries:data.progress.discoveries,focusEvents:await page.evaluate(()=>window.__focusLog)});
   await page.screenshot({path:OUT+'/'+mode+'.png',fullPage:true});await context.close();continue;
  }
  results.push({mode,checkpoints,postEmptyRequests:count,focusEvents:await page.evaluate(()=>window.__focusLog)});await context.close();
 }
 writeFileSync(OUT+'/results.json',JSON.stringify({source_sha256:hash(ROOT+'/frontend/src/screens/AlchimieExplore.tsx'),asset,asset_sha256:hash(ROOT+'/cat_de_roman_esti/web/static/'+asset),results},null,2)+'\n');console.log(JSON.stringify(results.map(x=>({mode:x.mode,checkpoints:x.checkpoints})),null,2));
}finally{await browser.close();}
