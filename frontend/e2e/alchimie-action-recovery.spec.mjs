import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, solution, start, act } from "./games.mjs";

const game = games.find(({ key }) => key === "alchimie");
const verify = (page) => page.getByRole("button", { name: "Verifică jocul", exact: true });
const currentGame = (page) => page.getByRole("button", { name: "Încarcă jocul curent", exact: true });
const hintButton = (page) => page.getByRole("button", { name: "💡 Indiciu", exact: true });
const resetButton = (page) => page.getByRole("button", { name: /Reia același joc/ });
const combineButton = (page) => page.getByRole("button", { name: "Combină cele două concepte selectate" });
const steps = () => solution(game).steps;
const remembered = (page) => page.evaluate((key) => localStorage.getItem(key), activeKey(game));
const played = (page) => page.evaluate(() => JSON.parse(localStorage.getItem("cat_wordgame_scores_v1") || "{}").alchimie?.played ?? 0);
const serverState = async (request, id) => (await request.get(gameURL(game, id))).json();

function traffic(page, id) {
  const counts = { reads: 0, mutations: 0 };
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (request.method() === "GET" && path === gameURL(game, id)) counts.reads += 1;
    if (request.method() === "POST" && path.startsWith(`${gameURL(game, id)}/`)) counts.mutations += 1;
  });
  return counts;
}

function responseFor(page, id, action, method = "POST") {
  const path = action ? `${gameURL(game, id)}/${action}` : gameURL(game, id);
  return page.waitForResponse((response) => response.request().method() === method && new URL(response.url()).pathname === path);
}

async function unlock(request, id, inventory) {
  let state = await serverState(request, id);
  for (let a = 0; a < inventory.length && !state.hint_available; a += 1) {
    for (let b = a + 1; b < inventory.length && !state.hint_available; b += 1) {
      const response = await request.post(`${gameURL(game, id)}/combine`, { data: { a: inventory[a].id, b: inventory[b].id } });
      expect(response.status()).toBe(200);
      state = await response.json();
    }
  }
  expect(state.hint_available).toBe(true);
  return state;
}

async function prepare(page, request, { hints = 0, solved = 0 } = {}) {
  const initial = await start(page, game);
  for (const step of steps().slice(0, solved)) {
    expect((await request.post(`${gameURL(game, initial.game_id)}/combine`, { data: step.payload })).status()).toBe(200);
  }
  for (let index = 0; index < hints; index += 1) {
    await unlock(request, initial.game_id, initial.inventory);
    if (index < hints - 1) {
      expect((await request.post(`${gameURL(game, initial.game_id)}/hint`)).status()).toBe(200);
    }
  }
  if (hints || solved) {
    await page.reload();
    await expect(page.locator(game.board)).toBeVisible();
    if (hints) await expect(hintButton(page)).toBeEnabled();
  }
  return initial;
}

async function loseCommittedResponse(page, id, action) {
  let committed;
  await page.route(`**${gameURL(game, id)}/${action}`, async (route) => {
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    committed = await response.json();
    await route.fulfill({ status: 503, contentType: "application/json", body: "{}" });
  }, { times: 1 });
  return () => committed;
}

async function askHint(page, id) {
  const response = responseFor(page, id, "hint");
  await hintButton(page).click();
  return response;
}

async function saveFromOtherTab(context, request) {
  const fresh = await (await request.post("/api/wordgames/alchimie/games?seed=39&difficulty=usor")).json();
  const other = await context.newPage();
  await other.goto("/");
  await other.evaluate(([key, id]) => localStorage.setItem(key, id), [activeKey(game), fresh.game_id]);
  return { other, fresh };
}

async function holdResponse(page, id, action = "", missing = false) {
  let entered;
  let release;
  const requested = new Promise((resolve) => { entered = resolve; });
  const held = new Promise((resolve) => { release = resolve; });
  await page.route(`**${gameURL(game, id)}${action ? `/${action}` : ""}`, async (route) => {
    const response = await route.fetch();
    entered();
    await held;
    if (missing) await route.fulfill({ status: 404, contentType: "application/json", body: "{}" });
    else await route.fulfill({ response });
  }, { times: 1 });
  return { requested, release };
}

async function settledScreenshot(page, name, target) {
  await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
  await expect(page.getByText("Joc reluat.", { exact: true })).toHaveCount(0);
  if (target) await target.scrollIntoViewIfNeeded();
  await page.screenshot({ path: test.info().outputPath(name) });
}

test.beforeEach(async ({ page }) => deterministicStarts(page, game));

test("lost productive combine restores the exact earned inventory and private target", async ({ page, request }) => {
  const initial = await prepare(page, request);
  const counts = traffic(page, initial.game_id);
  const committed = await loseCommittedResponse(page, initial.game_id, "combine");
  expect((await act(page, game, steps()[0])).status()).toBe(503);
  await expect(page.getByText("Joc sincronizat. Poți continua.", { exact: true })).toBeVisible();
  const fresh = await serverState(request, initial.game_id);
  expect(fresh.inventory).toEqual(committed().inventory);
  expect(fresh.target.id).toBeNull();
  expect(fresh.discovered).toBeUndefined();
  expect(fresh.already_tried).toBeUndefined();
  expect(fresh.moves).toBe(1);
  await page.getByRole("button", { name: /^Toate / }).click();
  for (const item of committed().discovered) {
    await expect(page.locator(game.board).getByRole("button", { name: new RegExp(`^${item.label}(?:,|$)`) })).toBeVisible();
  }
  await expect(page.getByRole("button", { name: /^Scoate .* din alambic$/ })).toHaveCount(0);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  expect(await played(page)).toBe(0);
  await settledScreenshot(page, "recovered-inventory.png", page.locator(game.board));
});

for (const hints of [1, 2]) {
  test(`lost paid ${hints === 1 ? "output" : "pair"} clue survives GET and resume without another charge`, async ({ page, request }) => {
    const initial = await prepare(page, request, { hints });
    const counts = traffic(page, initial.game_id);
    const committed = await loseCommittedResponse(page, initial.game_id, "hint");
    expect((await askHint(page, initial.game_id)).status()).toBe(503);
    await expect(page.locator(".alchemy-earned-hint")).toBeVisible();
    const fresh = await serverState(request, initial.game_id);
    expect(fresh.hints_used).toBe(hints);
    expect(fresh.earned_hint).toEqual(committed().earned_hint);
    expect(fresh.earned_hint.hint_kind).toBe(hints === 1 ? "output" : "pair");
    expect(fresh.target.id).toBeNull();
    expect(fresh.hint_available).toBe(false);
    await expect(page.locator(".alchemy-earned-hint")).toHaveText(fresh.earned_hint.message);
    await expect(hintButton(page)).toHaveCount(0);
    await expect(page.getByRole("button", { name: /^Scoate .* din alambic$/ })).toHaveCount(hints === 1 ? 0 : 2);
    expect(counts).toEqual({ reads: 1, mutations: 1 });
    await settledScreenshot(page, `recovered-hint-${hints}.png`, page.locator(".alchemy-earned-hint"));
    await page.reload();
    await expect(page.locator(".alchemy-earned-hint")).toHaveText(fresh.earned_hint.message);
    expect((await serverState(request, initial.game_id)).hints_used).toBe(hints);
    expect(counts).toEqual({ reads: 2, mutations: 1 });
  });
}

test("lost reset restores original seeds, clears cue and experiment memory once", async ({ page, request }) => {
  const initial = await prepare(page, request, { hints: 1 });
  expect((await askHint(page, initial.game_id)).status()).toBe(200);
  const counts = traffic(page, initial.game_id);
  const committed = await loseCommittedResponse(page, initial.game_id, "reset");
  const response = responseFor(page, initial.game_id, "reset");
  await resetButton(page).click();
  expect((await response).status()).toBe(503);
  await expect(page.getByText("Joc sincronizat. Poți continua.", { exact: true })).toBeVisible();
  const fresh = await serverState(request, initial.game_id);
  expect(fresh.moves).toBe(0);
  expect(fresh.attempted_count).toBe(0);
  expect(fresh.hints_used).toBe(0);
  expect(fresh.inventory).toEqual(initial.inventory);
  expect(fresh).toEqual(committed());
  await expect(page.locator(".alchemy-earned-hint")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^Scoate .* din alambic$/ })).toHaveCount(0);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
});

test("lost winning combine records the terminal score exactly once", async ({ page, request }) => {
  const initial = await prepare(page, request, { solved: steps().length - 1 });
  const counts = traffic(page, initial.game_id);
  const committed = await loseCommittedResponse(page, initial.game_id, "combine");
  expect((await act(page, game, steps().at(-1))).status()).toBe(503);
  await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
  await expect.poll(() => played(page)).toBe(1);
  await expect.poll(() => remembered(page)).toBeNull();
  const fresh = await serverState(request, initial.game_id);
  expect(fresh.won).toBe(true);
  expect(fresh.score).toBe(1000);
  expect(fresh.score).toBe(committed().score);
  expect(fresh.target.id).not.toBeNull();
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  await expect(page.getByText("Ai făurit ținta!", { exact: true }).locator("../..")).toHaveCSS("opacity", "1");
  await settledScreenshot(page, "recovered-win.png", page.getByRole("button", { name: "Copiază rezultatul" }));
  await page.reload();
  await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
  expect(await played(page)).toBe(1);
});

test("failed verification persists, locks mutations and retries by GET only", async ({ page, request }) => {
  await page.clock.install();
  const initial = await prepare(page, request, { hints: 1 });
  const counts = traffic(page, initial.game_id);
  await loseCommittedResponse(page, initial.game_id, "hint");
  await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({ status: 503, contentType: "application/json", body: "{}" }), { times: 1 });
  expect((await askHint(page, initial.game_id)).status()).toBe(503);
  await expect(verify(page)).toBeEnabled();
  for (const button of await page.locator(`${game.board} button`).all()) await expect(button).toBeDisabled();
  await expect(combineButton(page)).toBeDisabled();
  await expect(resetButton(page)).toBeDisabled();
  await expect(hintButton(page)).toBeDisabled();
  await page.keyboard.press("Enter");
  await page.clock.fastForward(4000);
  await page.clock.runFor(500);
  await expect(verify(page)).toBeVisible();
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  expect(await remembered(page)).toBe(initial.game_id);
  await settledScreenshot(page, "read-only-recovery.png", page.locator(".alchemy-sync-recovery"));
  const response = responseFor(page, initial.game_id, "", "GET");
  await verify(page).click();
  expect((await response).status()).toBe(200);
  await expect(verify(page)).toHaveCount(0);
  await expect(page.locator(".alchemy-earned-hint")).toBeVisible();
  expect(counts).toEqual({ reads: 2, mutations: 1 });
  expect((await serverState(request, initial.game_id)).hints_used).toBe(1);
});

test("an uncommitted failed combine reads unchanged state without inventing discovery", async ({ page, request }) => {
  const initial = await prepare(page, request);
  const counts = traffic(page, initial.game_id);
  await page.route(`**${gameURL(game, initial.game_id)}/combine`, (route) => route.fulfill({ status: 503, contentType: "application/json", body: "{}" }), { times: 1 });
  expect((await act(page, game, steps()[0])).status()).toBe(503);
  await expect(page.getByText("Joc sincronizat. Poți continua.", { exact: true })).toBeVisible();
  const fresh = await serverState(request, initial.game_id);
  expect(fresh.moves).toBe(0);
  expect(fresh.inventory).toEqual(initial.inventory);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
});

test("a GET with another game id fails closed until an owned read succeeds", async ({ page, request }) => {
  const initial = await prepare(page, request);
  const counts = traffic(page, initial.game_id);
  await loseCommittedResponse(page, initial.game_id, "combine");
  await page.route(`**${gameURL(game, initial.game_id)}`, async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    await route.fulfill({ json: { ...body, game_id: "wrong-session" } });
  }, { times: 1 });
  await act(page, game, steps()[0]);
  await expect(verify(page)).toBeEnabled();
  expect(await remembered(page)).toBe(initial.game_id);
  await verify(page).click();
  await expect(verify(page)).toHaveCount(0);
  expect(counts).toEqual({ reads: 2, mutations: 1 });
});

test("an owned confirmed 404 forgets only that round and returns to setup", async ({ page, request }) => {
  const initial = await prepare(page, request);
  const counts = traffic(page, initial.game_id);
  await loseCommittedResponse(page, initial.game_id, "combine");
  await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({ status: 404, contentType: "application/json", body: "{}" }), { times: 1 });
  await act(page, game, steps()[0]);
  await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
  expect(await remembered(page)).toBeNull();
  expect(counts).toEqual({ reads: 1, mutations: 1 });
});

test("another tab's pointer prevents mutation and loads its current round", async ({ page, request, context }) => {
  const initial = await prepare(page, request, { hints: 1 });
  const counts = traffic(page, initial.game_id);
  const { other, fresh } = await saveFromOtherTab(context, request);
  await hintButton(page).click();
  await expect(currentGame(page)).toBeEnabled();
  expect(counts).toEqual({ reads: 0, mutations: 0 });
  await currentGame(page).click();
  await expect(currentGame(page)).toHaveCount(0);
  await expect(page.locator(game.board)).toBeVisible();
  expect(await remembered(page)).toBe(fresh.game_id);
  expect((await serverState(request, initial.game_id)).hints_used).toBe(0);
  await other.close();
});

for (const phase of ["mutation", "read", "missing-read"]) {
  test(`a changed saved round rejects an old ${phase} completion`, async ({ page, request, context }) => {
    const initial = await prepare(page, request, { hints: 1 });
    const counts = traffic(page, initial.game_id);
    if (phase !== "mutation") await loseCommittedResponse(page, initial.game_id, "hint");
    const held = await holdResponse(page, initial.game_id, phase === "mutation" ? "hint" : "", phase === "missing-read");
    const clicked = hintButton(page).click();
    await held.requested;
    const { other, fresh } = await saveFromOtherTab(context, request);
    held.release();
    await clicked;
    await expect(currentGame(page)).toBeEnabled();
    await expect(page.locator(".alchemy-earned-hint")).toHaveCount(0);
    expect(await remembered(page)).toBe(fresh.game_id);
    expect(counts).toEqual({ reads: phase === "mutation" ? 0 : 1, mutations: 1 });
    await currentGame(page).click();
    await expect(currentGame(page)).toHaveCount(0);
    expect(await remembered(page)).toBe(fresh.game_id);
    await other.close();
  });
}

for (const phase of ["mutation", "read"]) {
  test(`unmount invalidates an old ${phase} reply and preserves owned progress for resume`, async ({ page, request }) => {
    const initial = await prepare(page, request, { hints: 1 });
    const counts = traffic(page, initial.game_id);
    if (phase === "read") await loseCommittedResponse(page, initial.game_id, "hint");
    const held = await holdResponse(page, initial.game_id, phase === "mutation" ? "hint" : "");
    const clicked = hintButton(page).click();
    await held.requested;
    await page.getByRole("button", { name: "Ieși la lista de jocuri" }).click();
    held.release();
    await clicked;
    await expect(page.locator(game.board)).toHaveCount(0);
    expect(await remembered(page)).toBe(initial.game_id);
    expect(await played(page)).toBe(0);
    expect(counts).toEqual({ reads: phase === "mutation" ? 0 : 1, mutations: 1 });
    await page.goto(game.path);
    await expect(page.locator(".alchemy-earned-hint")).toBeVisible();
    expect((await serverState(request, initial.game_id)).hints_used).toBe(1);
  });
}

test("failed verification can start a fresh round without replaying the old action", async ({ page, request }) => {
  const initial = await prepare(page, request, { hints: 1 });
  const counts = traffic(page, initial.game_id);
  await loseCommittedResponse(page, initial.game_id, "hint");
  await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({ status: 503, contentType: "application/json", body: "{}" }), { times: 1 });
  await askHint(page, initial.game_id);
  await expect(verify(page)).toBeEnabled();
  await page.locator(".alchimie-other-board").click();
  await expect(verify(page)).toHaveCount(0);
  await expect.poll(() => remembered(page)).not.toBe(initial.game_id);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  expect((await serverState(request, initial.game_id)).hints_used).toBe(1);
});
