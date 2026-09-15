import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {chromium,expect} from './browser-deps/node_modules/@playwright/test/index.mjs';
const ROOT='/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v96-words-and-input-clarity';
const OUT='/home/dobo/work/_temp/feat__v96-words-and-input-clarity/critique',BASE='http://127.0.0.1:8150';
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const browser=await chromium.launch({headless:true});const reports=[];
const reply=(p,path,method='POST')=>p.waitForResponse(r=>r.request().method()===method&&new URL(r.url()).pathname===path);
const word=(p,label)=>p.locator('.alchemy-inventory-grid').getByRole('button',{name:new RegExp('^'+label+'(?:,|$)')});
const focus=p=>p.evaluate(()=>({tag:document.activeElement.tagName,label:document.activeElement.getAttribute('aria-label'),text:document.activeElement.textContent?.slice(0,100)}));
async function snapshot(p,name){await p.waitForTimeout(450);await p.screenshot({path:OUT+'/'+name+'.png',fullPage:true});return p.evaluate(()=>({viewport:[innerWidth,innerHeight],documentWidth:document.documentElement.scrollWidth,buttons:[...document.querySelectorAll('button')].filter(e=>e.getBoundingClientRect().width>0).map(e=>{const r=e.getBoundingClientRect();return{text:e.textContent,aria:e.getAttribute('aria-label'),disabled:e.disabled,box:[r.x,r.y,r.width,r.height],inViewport:r.top>=0&&r.bottom<=innerHeight};}),headings:[...document.querySelectorAll('h1,h2,h3')].map(e=>e.textContent),openDisclosures:[...document.querySelectorAll('details[open]>summary')].map(e=>e.textContent)}));}
try{
 for(const game of [{key:'intrusul',path:'/intrusul',board:'.intrusul-grid',seed:38},{key:'perechi',path:'/perechi',board:'.perechi-grid',seed:38},{key:'conexiuni',path:'/conexiuni',board:'.connections-grid',seed:9,category:'viata_de_roman',difficulty:'normal'},{key:'lant',path:'/lant',board:'.lant-choice-grid',seed:19,category:'gastronomie',difficulty:'usor'},{key:'contexto',path:'/cald-rece',seed:19,category:'viata_de_roman',difficulty:'usor'}]){
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.route('**/api/wordgames/'+game.key+'/games?*',async route=>{const u=new URL(route.request().url());u.searchParams.set('seed',String(game.seed));if(game.category)u.searchParams.set('category',game.category);if(game.difficulty)u.searchParams.set('difficulty',game.difficulty);await route.continue({url:u.toString()});});
  await page.goto(BASE+game.path);const creating=reply(page,'/api/wordgames/'+game.key+'/games');await page.getByRole('button',{name:/^Joacă(?: →)?$/}).click();const initial=await(await creating).json();const api='/api/wordgames/'+game.key+'/games/'+initial.game_id;
  if(game.board)await page.locator(game.board).waitFor();else await page.getByRole('textbox',{name:'Concept de ghicit'}).waitFor();
  const initialView=await snapshot(page,game.key+'-initial'),steps=[];
  if(game.key==='contexto'){
   const input=page.getByRole('textbox',{name:'Concept de ghicit'});
   for(const text of ['unealtă','fier','scule','reparație','metal','clește']){
    await input.fill(text);const wait=reply(page,api+'/guess');await input.press('Enter');const result=await(await wait).json();if(!result.won)await expect(input).toBeEnabled();
    await page.waitForTimeout(450);const notices=await page.locator('.card').allTextContents();steps.push({input:text,result,focus:await focus(page),visibleNotices:notices.filter(t=>t.includes('Nu cunosc')||t.includes('Ai vrut'))});
    if(text==='fier'||text==='reparație')await snapshot(page,'contexto-unknown-'+(text==='fier'?'fier':'reparatie'));
   }
   assert(steps.at(-1).result.won);
  }else if(game.key==='conexiuni'){
   const tiles=page.locator(game.board+' button');for(let i=0;i<4;i++)await tiles.nth(i).click();const wait=reply(page,api+'/guess');await page.getByRole('button',{name:'Verifică',exact:true}).click();steps.push(await(await wait).json());
  }else if(game.key==='intrusul'){
   const wait=reply(page,api+'/guess');await page.locator(game.board+' button').first().click();steps.push(await(await wait).json());
  }else if(game.key==='perechi'){
   await page.locator(game.board+' button').nth(0).click();const wait=reply(page,api+'/match');await page.locator(game.board+' button').nth(1).click();steps.push(await(await wait).json());
  }else{
   const input=page.getByRole('textbox',{name:'Următorul concept'});for(const text of ['Pâine','Firimitură']){await input.fill(text);const wait=reply(page,api+'/move');await input.press('Enter');steps.push(await(await wait).json());if(!steps.at(-1).won)await expect(input).toBeEnabled();}
   assert(steps.at(-1).won);
  }
  const afterView=await snapshot(page,game.key+'-after');reports.push({game:game.key,public_start:game,initial,initialView,steps,afterView,errors});await context.close();
 }
 // Fresh landed-V95 Alchimie recovery, without stale cached refs or a forced restore.
 for(const committed of [false,true]){
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'}),page=await context.newPage();await page.goto(BASE+'/alchimie');const creating=reply(page,'/api/alchimie/explore');await page.getByRole('button',{name:'Începe explorarea →'}).click();const state=await(await creating).json();const api='/api/alchimie/explore/'+state.game_id;
  const initialView=await snapshot(page,'alchimie-initial-'+committed);
  await page.route('**'+api+'/combine',async route=>{if(committed)await route.fetch();await route.abort('failed');},{times:1});
  await word(page,'Făină').focus();await page.keyboard.press('Enter');await word(page,'Apă').focus();const before=await focus(page),wait=reply(page,api,'GET');await page.keyboard.press('Enter');const recovered=await(await wait).json();await expect(word(page,'Apă')).toBeEnabled();const after=await focus(page);await page.keyboard.press('Tab');const afterTab=await focus(page);
  reports.push({game:'alchimie',committed,initialView,focusBefore:before,focusAfterRecovery:after,focusAfterTab:afterTab,recovered,view:await snapshot(page,'alchimie-recovery-'+committed)});await context.close();
 }
 const report={kind:'v96-six-game-gui-kickoff-v1',status:'Critique evidence, not implementation or approval',baseline:'1457786',origin:BASE,source_sha256:{'manifest':sha(ROOT+'/cat_de_roman_esti/web/static/.vite/manifest.json'),'alchimieScreen':sha(ROOT+'/frontend/src/screens/AlchimieExplore.tsx'),'contextoScreen':sha(ROOT+'/frontend/src/screens/CaldRece.tsx')},reports,script_sha256:sha(OUT+'/browser_probe.mjs')};
 writeFileSync(OUT+'/browser-probe.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(reports.map(r=>({game:r.game,committed:r.committed,focusAfterRecovery:r.focusAfterRecovery,focusAfterTab:r.focusAfterTab,unknown:r.steps?.filter(x=>x.input&&x.result&&!x.result.ok).map(x=>({input:x.input,message:x.result.message,notices:x.visibleNotices}))})),null,2));
}finally{await browser.close();}
