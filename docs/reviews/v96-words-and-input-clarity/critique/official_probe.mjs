import {chromium} from './browser-deps/node_modules/@playwright/test/index.mjs';
import {writeFileSync} from 'node:fs';
const OUT='/home/dobo/work/_temp/feat__v96-words-and-input-clarity/critique';
const browser=await chromium.launch({headless:true});const results=[];
try{for(const [key,url]of [['contexto','https://contexto.me/'],['wiki-game','https://www.thewikigame.com/'],['weaver','https://wordwormdormdork.com/']]){
 const context=await browser.newContext({viewport:{width:390,height:844}}),page=await context.newPage();let error=null;
 try{await page.goto(url,{waitUntil:'domcontentloaded',timeout:18000});await page.waitForTimeout(1500);}catch(e){error=String(e);}
 const text=await page.locator('body').innerText();console.log(JSON.stringify({key,url,title:await page.title(),text:text.slice(0,6500),buttons:await page.locator('button').allTextContents(),inputs:await page.locator('input').evaluateAll(es=>es.map(e=>({placeholder:e.placeholder,aria:e.getAttribute('aria-label')}))),error}));
 await page.screenshot({path:OUT+'/official-'+key+'.png',fullPage:true});results.push({key,url,title:await page.title(),error,screenshot:'official-'+key+'.png'});await context.close();
}writeFileSync(OUT+'/official-probe.json',JSON.stringify({kind:'v96-primary-interface-visit-v1',results},null,2)+'\n');}finally{await browser.close();}
