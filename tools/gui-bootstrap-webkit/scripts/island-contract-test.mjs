import { build } from 'vite';
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import path from 'node:path';
const input=JSON.parse(await new Promise(resolve=>{let data='';process.stdin.setEncoding('utf8');process.stdin.on('data',part=>data+=part);process.stdin.on('end',()=>resolve(data));}));
const result=await build({configFile:false,logLevel:'error',build:{write:false,lib:{entry:path.resolve('src/behaviors/islands.ts'),formats:['es']},rolldownOptions:{output:{codeSplitting:false,minify:true}}}});
const chunks=(Array.isArray(result)?result:[result]).flatMap(item=>item.output).filter(item=>item.type==='chunk');assert.equal(chunks.length,1);const moduleURL='data:text/javascript;base64,'+Buffer.from(chunks[0].code).toString('base64');
const browser=await chromium.launch({headless:true});
try{
  const page=await browser.newPage();await page.setContent(input.html);
  const observed=await page.evaluate(async({moduleURL,nonce,expected})=>{
    const {loadIslands}=await import(moduleURL),roots=[...document.querySelectorAll('[data-island]')],scripts=[...document.scripts],events=[],contexts=[],disposed=new Set();
    const dom=roots.map(root=>{const id=root.dataset.props,script=document.getElementById(id);if(script?.type!=='application/json'||script.nonce!==nonce)throw Error('Go JSON ID/type/nonce contract');const props=JSON.parse(script.textContent);if(props.message!==expected.message||props.mode!==root.dataset.load)throw Error('Go JSON escaping/props contract');return {key:root.dataset.island,id,mode:root.dataset.load,nonce:script.nonce};});
    const registry=Object.fromEntries(dom.map(item=>[item.key,async()=>({mount(root,props,ctx){if(ctx.nonce!==nonce||props.mode!==root.dataset.load)throw Error('Loader ctx/props disagrees with Go');contexts.push(ctx);const child=document.createElement('p');child.textContent=props.message;root.append(child);return()=>disposed.add(item.key);}})]));
    document.addEventListener('island:mounted',event=>events.push({type:event.type,key:event.detail.key,error:event.detail.error}));
    const stop=loadIslands(registry,document,nonce);const interaction=roots.find(root=>root.dataset.load==='interaction');interaction.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));
    await new Promise((resolve,reject)=>{const until=performance.now()+3000;const poll=()=>{if(events.length===4)resolve();else if(performance.now()>until)reject(Error('All four real load modes must mount'));else requestAnimationFrame(poll);};poll();});
    if(roots.some(root=>root.textContent!==expected.message))throw Error('Loader must commit decoded Go props');stop();stop();
    return {dom,script_count:scripts.length,events,aborted:contexts.filter(ctx=>ctx.signal.aborted).length,disposed:disposed.size};
  },{moduleURL,nonce:input.nonce,expected:input.expected});
  assert.deepEqual(observed.dom.map(item=>item.mode),['eager','visible','idle','interaction']);assert.equal(new Set(observed.dom.map(item=>item.id)).size,4);assert.equal(observed.script_count,4);assert.equal(observed.events.length,4);assert.ok(observed.events.every(item=>item.type==='island:mounted'&&item.error===null&&observed.dom.some(root=>root.key===item.key)));assert.equal(observed.aborted,4);assert.equal(observed.disposed,4);
  await page.setContent(input.html);
  const rejected=await page.evaluate(async({moduleURL,nonce})=>{const {loadIslands}=await import(moduleURL);const root=document.querySelector('[data-island]');document.getElementById(root.dataset.props).nonce='mismatched';let failed=0,mounted=0;root.addEventListener('island:failed',()=>failed++);const stop=loadIslands({[root.dataset.island]:async()=>({mount(){mounted++;return()=>{};}})},root,nonce);await new Promise(resolve=>requestAnimationFrame(resolve));stop();return {failed,mounted,body:root.textContent};},{moduleURL,nonce:input.nonce});
  assert.deepEqual(rejected,{failed:1,mounted:0,body:'Server skeleton'});
  process.stdout.write(JSON.stringify({schema:1,...observed,rejected})+'\n');
}finally{await browser.close();}
