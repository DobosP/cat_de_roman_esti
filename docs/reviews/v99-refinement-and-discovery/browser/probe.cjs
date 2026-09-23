const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(path.join(process.argv[3], 'playwright'));
const base = process.argv[2], out = __dirname;
const captions = { 'Înghețată': ['înghețată cu aromă de cacao', 'înghețată în variantă cu lapte'], 'Chec': ['chec în variantă cu cacao', 'chec servit alături de lapte'] };
const receipt = { kind: 'v99-caption-browser-probe-v1', checked_on: new Date().toISOString(), browser: 'msedge', cases: [], screenshots: [], limitations: ['Headless system Edge and emulated viewport/text sizing; no physical-device or human enjoyment test.'] };
let browser;
async function tabTo(page, target) {
  await target.waitFor({ state: 'visible' });
  assert(await target.isEnabled());
  for (let i = 0; i < 80; i++) {
    if (await target.evaluate(e => e === document.activeElement)) return;
    await page.keyboard.press('Tab');
  }
  throw Error('Control unreachable with Tab');
}
async function press(page, target) { await tabTo(page, target); await page.keyboard.press('Space'); }
async function hasText(locator, text) { await locator.filter({ hasText: text }).waitFor({ state: 'visible' }); }
function responseFor(page, id, action, method = 'POST') {
  return page.waitForResponse(r => r.request().method() === method && new URL(r.url()).pathname === `/api/wordgames/lant/games/${id}${action ? '/' + action : ''}`);
}
async function json(response) { assert.equal(response.status(), 200); return response.json(); }
async function fits(page, record, phase) {
  const dimensions = await page.locator('.lant-choice-grid button, .lant-hint-panel, .breadcrumb-trail, .lant-trail-step, .lant-trail-relation, .lant-trail-step .chip, .word-hop-input input').evaluateAll(elements => ({
    viewport: document.documentElement.clientWidth, document: document.documentElement.scrollWidth,
    fontSize: getComputedStyle(document.documentElement).fontSize,
    elements: elements.filter(e => e.getClientRects().length).map(e => ({ left: e.getBoundingClientRect().left, right: e.getBoundingClientRect().right, width: e.clientWidth, scroll: e.scrollWidth }))
  }));
  assert(dimensions.document <= dimensions.viewport + 1, 'Document horizontal overflow');
  for (const e of dimensions.elements) {
    assert(e.left >= -1 && e.right <= dimensions.viewport + 1, 'Caption element outside horizontal viewport');
    assert(e.scroll <= e.width + 1, 'Caption element horizontal overflow');
  }
  assert.equal(dimensions.fontSize, record.mobile ? '32px' : '16px');
  record.geometry.push({ phase, viewport: dimensions.viewport, document: dimensions.document, fontSize: dimensions.fontSize, checked_elements: dimensions.elements.length, max_internal_overflow: Math.max(0, ...dimensions.elements.map(e => e.scroll-e.width)) });
}
async function runCase(mobile, via) {
  const record = { id: `${mobile ? 'mobile320-text200' : 'desktop1280'}-${via === 'Chec' ? 'chec' : 'inghetata'}`, mobile, viewport: { width: mobile ? 320 : 1280, height: 900 }, route: ['Cacao', via, 'Lapte'], captions: captions[via], geometry: [], errors: [], status: 'running' };
  receipt.cases.push(record);
  const context = await browser.newContext({ viewport: record.viewport, reducedMotion: 'reduce' });
  const page = await context.newPage(); page.setDefaultTimeout(12000);
  const mutations = [], creates = [];
  page.on('pageerror', e => record.errors.push(e.message));
  page.on('request', r => { const p = new URL(r.url()).pathname; if (r.method() === 'POST' && p.startsWith('/api/wordgames/lant/games/')) mutations.push(p.split('/').at(-1)); if (r.method() === 'POST' && p === '/api/wordgames/lant/games') creates.push(p); });
  try {
    if (mobile) await page.addInitScript(() => document.addEventListener('DOMContentLoaded', () => { document.documentElement.style.fontSize = '200%'; }));
    await page.route('**/api/wordgames/lant/games?*', async route => {
      const u = new URL(route.request().url());
      for (const [k,v] of Object.entries({ seed: '0', category: 'gastronomie', difficulty: 'usor' })) u.searchParams.set(k,v);
      await route.continue({ url: u.toString() });
    });
    await page.goto(base + '/lant');
    const created = page.waitForResponse(r => r.request().method() === 'POST' && new URL(r.url()).pathname === '/api/wordgames/lant/games');
    await press(page, page.getByRole('button', { name: /^Joacă(?: →)?$/ }));
    let state = await json(await created); const id = state.game_id; const url = base + `/api/wordgames/lant/games/${id}`;
    assert.equal(state.start.label, 'Cacao'); assert.equal(state.target.label, 'Lapte'); assert.equal(state.moves, 0); assert.equal(state.path.length, 1);
    await page.getByRole('textbox', { name: 'Următorul concept' }).waitFor({ state: 'visible' });
    for (const [label, texts] of Object.entries(captions)) {
      assert.equal(state.choices.find(c => c.label === label).relation, texts[0]);
      await hasText(page.getByRole('button', { name: `Salt la ${label}: ${texts[0]}`, exact: true }), texts[0]);
      assert(!JSON.stringify(state).includes(texts[1]), 'Future-step caption leaked at start');
    }
    record.initial_choices = state.choices;
    await fits(page, record, 'opening');
    if (via === 'Înghețată') {
      const hinted = responseFor(page, id, 'hint');
      await press(page, page.getByRole('button', { name: /^💡 Indiciu$/ }));
      const hint = await json(await hinted);
      assert.equal(hint.stage, 'direction'); assert.equal(hint.hint, null);
      assert(state.choices.some(c => c.relation === hint.relation));
      await hasText(page.locator('.lant-hint-panel'), hint.relation);
      const before = [...mutations]; const fetched = responseFor(page, id, '', 'GET');
      await page.reload(); const recovered = await json(await fetched);
      await hasText(page.locator('.lant-hint-panel'), hint.relation);
      assert.deepEqual(recovered.earned_hint, hint); assert.equal(recovered.moves, 0); assert.deepEqual(recovered.path,state.path); assert.deepEqual(mutations,before);
      record.hint = { stage: hint.stage, relation: hint.relation, already_visible: true, recovered_moves: recovered.moves };
      await fits(page,record,'hint-restored');
    }
    const first = responseFor(page,id,'move');
    await press(page,page.getByRole('button',{ name: `Salt la ${via}: ${captions[via][0]}`, exact: true }));
    state = await json(await first); assert(state.ok); assert.equal(state.moves,1); assert.equal(state.path.at(-1).relation,captions[via][0]);
    await hasText(page.locator('.lant-current'),via);
    await hasText(page.getByRole('button',{ name: `Salt la Lapte: ${captions[via][1]}`, exact: true }),captions[via][1]);
    const persisted = await json(await page.request.get(url)); assert.deepEqual(persisted.path,state.path); assert.equal(persisted.moves,1);
    const before = [...mutations]; const fetched = responseFor(page,id,'','GET');
    await page.reload(); const restored = await json(await fetched);
    await hasText(page.locator('.lant-current'),via);
    assert.deepEqual(restored.path,state.path); assert.equal(restored.moves,1); assert.deepEqual(mutations,before);
    const options = page.locator('.game-options > summary');
    await press(page,options);
    const trail = page.getByRole('group',{ name: 'Traseul parcurs' });
    await hasText(trail,captions[via][0]); await fits(page,record,'earned-first-step-restored');
    await press(page,options);
    const input = page.getByRole('textbox',{ name: 'Următorul concept' });
    await tabTo(page,input); await input.fill('Lapte');
    const final = responseFor(page,id,'move'); await input.press('Enter');
    state = await json(await final); assert(state.ok && state.won); assert.equal(state.moves,2); assert.equal(state.score,1000);
    const saved = await json(await page.request.get(url)); assert.deepEqual(saved.path,state.path); assert.equal(saved.moves,2);
    await page.getByRole('button',{ name: 'Copiază rezultatul' }).waitFor({ state: 'visible' });
    await press(page,options);
    for (const caption of captions[via]) await hasText(trail,caption);
    await tabTo(page,trail); await trail.scrollIntoViewIfNeeded(); await fits(page,record,'won-earned-trail');
    assert.equal(mutations.filter(m => m==='move').length,2); assert.equal(mutations.filter(m => m==='hint').length,via==='Înghețată'?1:0); assert.equal(creates.length,1); assert.deepEqual(record.errors,[]);
    record.moves=state.moves; record.score=state.score; record.path=saved.path; record.post_actions=mutations; record.create_requests=creates.length; record.reloads=via==='Înghețată'?2:1; record.keyboard='Tab/Space to start, hint, first hop, options and trail; focused textbox with Lapte + Enter for final hop';
    if (mobile) { const filename=`${record.id}.png`; await page.screenshot({ path:path.join(out,filename),fullPage:true,animations:'disabled' }); receipt.screenshots.push(filename); }
    record.status='pass';
  } catch (e) {
    record.status='fail'; record.failure=e.stack;
    await page.screenshot({ path:path.join(out,record.id+'-failure.png'),fullPage:true }).catch(()=>{});
  } finally { await context.close(); }
  fs.writeFileSync(path.join(out,'probe-result.json'),JSON.stringify(receipt,null,2)+'\n');
}
(async()=>{ try {
  browser=await chromium.launch({ channel:'msedge',headless:true }); receipt.browser_version=browser.version();
  for (const mobile of [false,true]) for (const via of ['Înghețată','Chec']) await runCase(mobile,via);
} catch(e) { receipt.launch_error=e.stack; } finally {
  if(browser) await browser.close();
  receipt.status=receipt.cases.length===4 && receipt.cases.every(c=>c.status==='pass')?'pass':'fail';
  fs.writeFileSync(path.join(out,'probe-result.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify({status:receipt.status,cases:receipt.cases.map(c=>({id:c.id,status:c.status,failure:c.failure?.split('\n')[0]})),screenshots:receipt.screenshots}));
  if(receipt.status!=='pass') process.exitCode=1;
}})();
