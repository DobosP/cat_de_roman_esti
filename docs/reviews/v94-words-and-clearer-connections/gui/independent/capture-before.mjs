import { chromium } from '/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v94-words-and-clearer-connections/frontend/node_modules/playwright/index.mjs';
import { execFileSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';
const out='/home/dobo/work/_temp/feat__v94-words-and-clearer-connections/gui/independent';
const main='/home/dobo/work/cat_de_roman_esti';
const helper='/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v94-words-and-clearer-connections/frontend/e2e/lant_caption_seeds.py';
const browser=await chromium.launch();const reports=[];
for(const id of ['lt_geografie_239','lt_literatura_240']){
 const journey=JSON.parse(execFileSync(main+'/.venv/bin/python',[helper,id],{cwd:main,env:{...process.env,PYTHONPATH:main},encoding:'utf8'}));
 const context=await browser.newContext({viewport:{width:320,height:900},locale:'ro-RO',reducedMotion:'reduce'});const page=await context.newPage();
 await page.addInitScript(()=>document.addEventListener('DOMContentLoaded',()=>document.documentElement.style.fontSize='200%'));
 await page.route('**/api/wordgames/lant/games?*',async route=>{const url=new URL(route.request().url());for(const[k,v]of Object.entries(journey.query))url.searchParams.set(k,String(v));await route.continue({url:url.toString()});});
 await page.goto('http://127.0.0.1:8150/lant');let response=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/api/wordgames/lant/games');await page.getByRole('button',{name:/^Joacă(?: →)?$/}).click();const state=await(await response).json();
 await page.locator('.lant-choice-grid').waitFor();await page.screenshot({path:`${out}/before-${id}-choices-320-200.png`,fullPage:true});
 const hint=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/hint'));await page.getByRole('button',{name:/💡 (?:Indiciu|Mai clar)/}).click();const hintState=await(await hint).json();await page.screenshot({path:`${out}/before-${id}-hint-320-200.png`,fullPage:true});
 const path=journey.routes[0];for(const node of path.slice(1)){response=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/move'));const field=page.getByRole('textbox',{name:'Următorul concept'});await field.fill(node.label);await field.press('Enter');await response;}
 await page.locator('.game-options > summary').click();await page.getByRole('group',{name:'Traseul parcurs'}).waitFor();await page.getByRole('group',{name:'Traseul parcurs'}).scrollIntoViewIfNeeded();await page.waitForTimeout(300);const trail=await page.locator('.breadcrumb-trail').evaluate(e=>({width:e.clientWidth,scroll:e.scrollWidth,overflow:getComputedStyle(e).overflowX,text:e.innerText}));
 await page.screenshot({path:`${out}/before-${id}-earned-320-200.png`,fullPage:true});reports.push({id,query:journey.query,choices:state.choices,hint:hintState,trail,rootFont:await page.locator('html').evaluate(e=>getComputedStyle(e).fontSize)});await context.close();
}
writeFileSync(`${out}/before.json`,JSON.stringify(reports,null,2)+'\n');await browser.close();console.log(JSON.stringify(reports,null,2));
