import { chromium } from '/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v93-words-and-game-quality/frontend/node_modules/playwright/index.mjs';
import { readFileSync,writeFileSync } from 'node:fs';
const dir='/home/dobo/work/_temp/feat__v93-words-and-game-quality/gui';
const checkpoint=JSON.parse(readFileSync('/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v93-words-and-game-quality/frontend/e2e/alchimie-221-checkpoint.json','utf8')).collection;
const browser=await chromium.launch({headless:true});
const report=[];
try {for(const [port,label] of [[8160,'before'],[8150,'after']]){
 const context=await browser.newContext({baseURL:`http://127.0.0.1:${port}`,viewport:{width:390,height:844},locale:'ro-RO',reducedMotion:'reduce'});
 const response=await context.request.post('/api/alchimie/explore',{data:{progress:checkpoint.progress}});
 const state=await response.json();
 const page=await context.newPage();await page.goto('/alchimie');
 await page.evaluate(state=>localStorage.setItem('cat_alchimie_exploration_v1',JSON.stringify({version:1,game_id:state.game_id,revision:state.revision,progress:state.progress,goal_id:state.goal_id,compatible_recipe_hashes:state.compatible_recipe_hashes})),state);
 await page.reload();await page.locator('.alchemy-explore-journal > summary').click();
 const search=page.getByRole('searchbox',{name:'Caută în rețetele mele'});
 if(label==='after') await search.fill('faina');
 await page.locator('.alchemy-explore-journal').scrollIntoViewIfNeeded();
 await page.screenshot({path:`${dir}/journal-${label}.png`});
 report.push({label,port,earned:state.discovered_count,search_count:await search.count(),visible_recipes:await page.locator('.alchemy-journal-entry').count()});
 await context.close();
}writeFileSync(`${dir}/journal-captures.json`,JSON.stringify(report,null,2)+'\n');}finally{await browser.close();}
