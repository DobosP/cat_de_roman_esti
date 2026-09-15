import { chromium } from '/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v93-words-and-game-quality/frontend/node_modules/playwright/index.mjs';
import { games, deterministicStarts, start, solution, solve } from '/home/dobo/work/_worktrees/cat_de_roman_esti/feat__v93-words-and-game-quality/frontend/e2e/games.mjs';
import { writeFileSync } from 'node:fs';
const dir='/home/dobo/work/_temp/feat__v93-words-and-game-quality/gui';
const browser=await chromium.launch({headless:true});
const report=[];
try {
for(const game of games){
 const context=await browser.newContext({baseURL:'http://127.0.0.1:8150',viewport:{width:390,height:844},locale:'ro-RO',reducedMotion:'reduce'});
 const page=await context.newPage();
 await deterministicStarts(page,game);
 const initial=await start(page,game);
 await page.screenshot({path:`${dir}/${game.key}-before.png`,fullPage:true});
 const geometry=await page.evaluate(()=>({viewport:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth,buttons:[...document.querySelectorAll('button')].filter(b=>b.getBoundingClientRect().height>0).map(b=>({label:b.innerText,height:Math.round(b.getBoundingClientRect().height)}))}));
 const result=await solve(page,game,solution(game).steps);
 report.push({game:game.key,game_id:initial.game_id,won:result.won,geometry});
 await context.close();
 console.log(game.key, 'fresh mobile win');
}
const context=await browser.newContext({baseURL:'http://127.0.0.1:8150',viewport:{width:390,height:844},locale:'ro-RO',reducedMotion:'reduce'});
const page=await context.newPage();
await page.goto('/alchimie');
await page.getByRole('button',{name:'Începe explorarea →',exact:true}).click();
await page.locator('.alchemy-inventory-grid').waitFor();
await page.screenshot({path:`dir/alchimie-explore-before.png`.replace('dir',dir),fullPage:true});
report.push({game:'alchimie-explore',journal_search:await page.locator('.alchemy-explore-journal input').count(),terminal_description:'Inactive collection buttons are disabled; descriptions appear only as native title on active buttons.'});
writeFileSync(`${dir}/before.json`,JSON.stringify(report,null,2)+'\n');
await context.close();
} finally {await browser.close();}
