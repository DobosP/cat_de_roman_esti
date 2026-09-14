import { chromium } from '/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v92-entry-creation-02/frontend/node_modules/playwright/index.mjs';
import {readFile,writeFile} from 'node:fs/promises';
const out='/home/dobo/work/_temp/feat__v92-entry-creation-02/verifier/gui-final';
const cases=JSON.parse(await readFile(`${out}/focus-cases.json`,'utf8'));
const browser=await chromium.launch({headless:true});const results=[];
async function geometry(page){return page.evaluate(()=>{const e=document.activeElement,b=document.querySelector('.alchemy-bench'),s=document.querySelector('.alchemy-explore-screen');const r=e.getBoundingClientRect(),br=b.getBoundingClientRect();const x=Math.max(0,Math.min(innerWidth-1,r.x+r.width/2)),y=Math.max(0,Math.min(innerHeight-1,r.y+r.height/2));const hit=document.elementFromPoint(x,y);return {active:e.getAttribute('aria-label')||e.getAttribute('aria-label')||e.tagName,activeHtml:e.outerHTML.slice(0,500),focusRect:{x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom},benchRect:{x:br.x,y:br.y,width:br.width,height:br.height,bottom:br.bottom},benchPosition:getComputedStyle(b).position,viewport:{width:innerWidth,height:innerHeight,visualHeight:visualViewport.height},scroll:s.scrollTop,visible:r.top>=0&&r.bottom<=innerHeight,behindBench:r.top<br.bottom&&r.bottom>br.top,hit:hit?.className,hitContainsFocus:hit===e||e.contains(hit),horizontalOverflow:document.documentElement.scrollWidth>innerWidth};});}
for(const index of [4,0]){
 const testCase=cases[index];const context=await browser.newContext({baseURL:'http://127.0.0.1:8156',viewport:{width:390,height:844},locale:'ro-RO',reducedMotion:'reduce'});const page=await context.newPage();
 await page.addInitScript(checkpoint=>localStorage.setItem('cat_alchimie_exploration_v1',JSON.stringify(checkpoint)),testCase.checkpoint);
 await page.goto('/alchimie');await page.locator('.alchemy-inventory-grid').waitFor();await page.waitForFunction(()=>document.querySelector('.alchemy-explore-screen')?.getAttribute('aria-busy')==='false');await page.evaluate(()=>document.fonts.ready);
 const first=page.getByRole('button',{name:testCase.a_label,exact:true}),second=page.getByRole('button',{name:testCase.b_label,exact:true});
 await first.focus();await page.keyboard.press('Enter');await second.focus();const before=await geometry(page);
 const response=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/combine'));
 await page.keyboard.press('Enter');const state=await(await response).json();await page.waitForFunction(()=>document.querySelector('.alchemy-explore-screen')?.getAttribute('aria-busy')==='false');await page.waitForTimeout(150);const after=await geometry(page);
 await page.screenshot({path:`${out}/keyboard-focus-after-case-${index}.png`});
 results.push({case:{...testCase,checkpoint:undefined},before,after,response:{result:state.result,discovered:state.discovered,message:state.message}});
 await context.close();
}
await writeFile(`${out}/keyboard-focus-after.json`,JSON.stringify(results,null,2)+'\n');console.log(JSON.stringify(results,null,2));await browser.close();
