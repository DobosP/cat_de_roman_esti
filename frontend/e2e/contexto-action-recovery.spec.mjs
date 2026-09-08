import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, solution, start, act } from "./games.mjs";

const game = games.find(({ key }) => key === "contexto");
const scoresKey = "cat_wordgame_scores_v1";
const field = (page) => page.getByRole("textbox", { name: "Concept de ghicit" });
const verify = (page) => page.getByRole("button", { name: "Verifică jocul", exact: true });
const currentGame = (page) => page.getByRole("button", { name: "Încarcă jocul curent", exact: true });
const answer = () => solution(game).steps.at(-1);
const nonAnswer = () => ["fotbal", "stilou", "București", "măr"]
  .filter((word) => word.toLowerCase() !== answer().payload.text.toLowerCase());

async function remembered(page) {
  return page.evaluate((key) => localStorage.getItem(key), activeKey(game));
}

async function played(page) {
  return page.evaluate((key) => JSON.parse(localStorage.getItem(key) || "{}").contexto?.played ?? 0, scoresKey);
}

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
  return page.waitForResponse((response) =>
    response.request().method() === method && new URL(response.url()).pathname === path);
}

async function loseCommittedResponse(page, id, action) {
  let committed;
  await page.route(`**${gameURL(game, id)}/${action}`, async (route) => {
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    committed = await response.json();
    await route.fulfill({
      status: 503, contentType: "application/json",
      body: JSON.stringify({ detail: "Upstream response was lost after commit." }),
    });
  }, { times: 1 });
  return () => committed;
}

async function threeGuesses(page) {
  for (const text of nonAnswer().slice(0, 3)) {
    const response = await act(page, game, { action: "guess", payload: { text } });
    expect(response.status()).toBe(200);
    expect((await response.json()).won).toBe(false);
  }
}

async function newerRound(request) {
  const response = await request.post("/api/wordgames/contexto/games?seed=39&difficulty=usor");
  expect(response.status()).toBe(200);
  return response.json();
}

async function saveFromOtherTab(context, id) {
  const other = await context.newPage();
  await other.goto("/");
  await other.evaluate(([key, value]) => localStorage.setItem(key, value), [activeKey(game), id]);
  return other;
}

async function holdRecovery(page, id, missing = false) {
  let entered;
  let release;
  const requested = new Promise((resolve) => { entered = resolve; });
  const held = new Promise((resolve) => { release = resolve; });
  await page.route(`**${gameURL(game, id)}`, async (route) => {
    const response = await route.fetch();
    entered();
    await held;
    if (missing) await route.fulfill({ status: 404, contentType: "application/json", body: "{}" });
    else await route.fulfill({ response });
  }, { times: 1 });
  return { requested, release };
}

test.beforeEach(async ({ page }) => {
  await deterministicStarts(page, game);
});

test("a lost winning response adopts the server result and records it once without replay", async ({ page, request }) => {
  const initial = await start(page, game);
  const counts = traffic(page, initial.game_id);
  const committed = await loseCommittedResponse(page, initial.game_id, "guess");
  expect((await act(page, game, answer())).status()).toBe(503);
  await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
  await expect.poll(() => played(page)).toBe(1);
  await expect.poll(() => remembered(page)).toBeNull();
  expect(committed().won).toBe(true);
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.won).toBe(true);
  expect(server.attempts).toBe(1);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  await page.reload();
  await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
  expect(await played(page)).toBe(1);
});

test("a lost paid clue response restores the clue without consuming another one", async ({ page, request }) => {
  const initial = await start(page, game);
  await threeGuesses(page);
  const counts = traffic(page, initial.game_id);
  await loseCommittedResponse(page, initial.game_id, "clue");
  const failed = responseFor(page, initial.game_id, "clue");
  await page.getByRole("button", { name: "Indiciu", exact: true }).click();
  expect((await failed).status()).toBe(503);
  await expect(field(page)).toBeEnabled();
  await expect(page.getByLabel("Indicii folosite")).toBeVisible();
  await expect(page.getByRole("button", { name: "Mai cald", exact: true })).toBeEnabled();
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.clues_used).toBe(1);
  expect(server.clue).toBeDefined();
  expect(server.attempts).toBe(3);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  expect(await played(page)).toBe(0);
});

test("a lost give-up response reveals only the server's terminal answer without a score", async ({ page, request }) => {
  const initial = await start(page, game);
  const counts = traffic(page, initial.game_id);
  await loseCommittedResponse(page, initial.game_id, "giveup");
  await page.getByRole("button", { name: "Răspuns", exact: true }).click();
  const failed = responseFor(page, initial.game_id, "giveup");
  await page.getByRole("button", { name: "Da, arată", exact: true }).click();
  expect((await failed).status()).toBe(503);
  await expect(page.getByText("Conceptul secret era:", { exact: true })).toBeVisible();
  await expect.poll(() => remembered(page)).toBeNull();
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.gave_up).toBe(true);
  expect(server.won).toBe(false);
  expect(server.attempts).toBe(0);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  expect(await played(page)).toBe(0);
});

test("failed verification locks mutations and its persistent retry only reads", async ({ page, request }) => {
  await page.clock.install();
  const initial = await start(page, game);
  const counts = traffic(page, initial.game_id);
  await loseCommittedResponse(page, initial.game_id, "guess");
  await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({
    status: 503, contentType: "application/json", body: "{}",
  }), { times: 1 });
  const text = nonAnswer()[0];
  expect((await act(page, game, { action: "guess", payload: { text } })).status()).toBe(503);
  await expect(verify(page)).toBeEnabled();
  await expect(page.locator(".contexto-sync-recovery")).toBeInViewport();
  await expect(field(page)).toBeDisabled();
  await expect(field(page)).toHaveValue(text);
  for (const button of await page.locator(".contexto-action-row button").all()) {
    await expect(button).toBeDisabled();
  }
  await page.keyboard.press("Enter");
  await page.clock.fastForward(4000);
  await expect(verify(page)).toBeVisible();
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  expect(await remembered(page)).toBe(initial.game_id);
  await page.screenshot({ path: test.info().outputPath("read-only-recovery.png"), fullPage: true });

  const restored = responseFor(page, initial.game_id, "", "GET");
  await verify(page).click();
  expect((await restored).status()).toBe(200);
  await expect(field(page)).toBeEnabled();
  await expect(field(page)).toHaveValue(text);
  await expect(verify(page)).toHaveCount(0);
  await expect(page.locator(".hud")).toContainText("1 încercare");
  expect(counts).toEqual({ reads: 2, mutations: 1 });
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.attempts).toBe(1);
  expect(server.won).toBe(false);
});

test("a failure before commit keeps input and authoritative counters unchanged", async ({ page, request }) => {
  const initial = await start(page, game);
  const counts = traffic(page, initial.game_id);
  await page.route(`**${gameURL(game, initial.game_id)}/guess`, (route) => route.fulfill({
    status: 503, contentType: "application/json", body: "{}",
  }), { times: 1 });
  const text = nonAnswer()[0];
  expect((await act(page, game, { action: "guess", payload: { text } })).status()).toBe(503);
  await expect(field(page)).toBeEnabled();
  await expect(field(page)).toHaveValue(text);
  expect(await (await request.get(gameURL(game, initial.game_id))).json()).toEqual(initial);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  const accepted = await act(page, game, { action: "guess", payload: { text } });
  expect((await accepted.json()).attempts).toBe(1);
  expect(counts.mutations).toBe(2); // The second POST came from this explicit user action.
});

for (const missing of [false, true]) {
  test(`a late ${missing ? "404" : "winning"} read cannot adopt or clear another tab's round`, async ({ page, context, request }) => {
    const initial = await start(page, game);
    const newer = await newerRound(request);
    await loseCommittedResponse(page, initial.game_id, "guess");
    const held = await holdRecovery(page, initial.game_id, missing);
    expect((await act(page, game, answer())).status()).toBe(503);
    await held.requested;
    const other = await saveFromOtherTab(context, newer.game_id);
    held.release();
    await expect(currentGame(page)).toBeEnabled();
    await expect(field(page)).toBeDisabled();
    await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toHaveCount(0);
    expect(await remembered(page)).toBe(newer.game_id);
    expect(await played(page)).toBe(0);
    const loaded = responseFor(page, newer.game_id, "", "GET");
    await currentGame(page).click();
    expect((await loaded).status()).toBe(200);
    await expect(field(page)).toBeEnabled();
    await expect(page.locator(".hud")).toContainText("0 încercări");
    expect(await remembered(page)).toBe(newer.game_id);
    expect(await played(page)).toBe(0);
    await other.close();
  });
}

test("leaving during recovery preserves the old pointer and a late callback cannot overwrite a new screen", async ({ page, context, request }) => {
  const initial = await start(page, game);
  await loseCommittedResponse(page, initial.game_id, "guess");
  const held = await holdRecovery(page, initial.game_id);
  expect((await act(page, game, answer())).status()).toBe(503);
  await held.requested;
  await page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true }).click();
  await expect(page.getByRole("button", { name: /^Joacă Cald sau Rece —/ })).toBeVisible();
  expect(await remembered(page)).toBe(initial.game_id);
  const newer = await newerRound(request);
  const other = await saveFromOtherTab(context, newer.game_id);
  const loaded = responseFor(page, newer.game_id, "", "GET");
  await page.getByRole("button", { name: /^Joacă Cald sau Rece —/ }).click();
  expect((await loaded).status()).toBe(200);
  await expect(field(page)).toBeEnabled();
  const oldCompleted = responseFor(page, initial.game_id, "", "GET");
  held.release();
  await oldCompleted;
  await expect(page.locator(".hud")).toContainText("0 încercări");
  await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toHaveCount(0);
  expect(await remembered(page)).toBe(newer.game_id);
  expect(await played(page)).toBe(0);
  await other.close();
});

test("an already different saved pointer pauses before any old-round mutation", async ({ page, context, request }) => {
  const initial = await start(page, game);
  const newer = await newerRound(request);
  const other = await saveFromOtherTab(context, newer.game_id);
  const counts = traffic(page, initial.game_id);
  await field(page).fill(answer().payload.text);
  await field(page).press("Enter");
  await expect(currentGame(page)).toBeEnabled();
  expect(counts).toEqual({ reads: 0, mutations: 0 });
  expect(await (await request.get(gameURL(game, initial.game_id))).json()).toEqual(initial);
  expect(await remembered(page)).toBe(newer.game_id);
  const loaded = responseFor(page, newer.game_id, "", "GET");
  await currentGame(page).click();
  expect((await loaded).status()).toBe(200);
  await expect(field(page)).toBeEnabled();
  expect(await remembered(page)).toBe(newer.game_id);
  expect(await played(page)).toBe(0);
  await other.close();
});

test("a verified missing owned session returns to setup and clears only that pointer", async ({ page }) => {
  const initial = await start(page, game);
  const counts = traffic(page, initial.game_id);
  for (const suffix of ["/guess", ""]) {
    await page.route(`**${gameURL(game, initial.game_id)}${suffix}`, (route) => route.fulfill({
      status: 404, contentType: "application/json", body: "{}",
    }), { times: 1 });
  }
  expect((await act(page, game, { action: "guess", payload: { text: nonAnswer()[0] } })).status()).toBe(404);
  await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
  expect(await remembered(page)).toBeNull();
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  expect(await played(page)).toBe(0);
});
