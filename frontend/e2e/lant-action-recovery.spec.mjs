import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, solution, start, act } from "./games.mjs";

const game = games.find(({ key }) => key === "lant");
const scoresKey = "cat_wordgame_scores_v1";
const field = (page) => page.getByRole("textbox", { name: "Următorul concept" });
const verify = (page) => page.getByRole("button", { name: "Verifică jocul", exact: true });
const currentGame = (page) => page.getByRole("button", { name: "Încarcă jocul curent", exact: true });
const steps = () => solution(game).steps;
const answer = () => steps().at(-1);
const firstMove = () => steps()[0];


async function remembered(page) {
  return page.evaluate((key) => localStorage.getItem(key), activeKey(game));
}

async function played(page) {
  return page.evaluate((key) => JSON.parse(localStorage.getItem(key) || "{}").lant?.played ?? 0, scoresKey);
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

async function newerRound(request) {
  const response = await request.post("/api/wordgames/lant/games?seed=39&difficulty=usor");
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

async function approachTarget(page) {
  for (const step of steps().slice(0, -1)) {
    const response = await act(page, game, step);
    expect((await response.json()).won).toBe(false);
  }
}

const hintButton = (page) => page.getByRole("button", { name: /💡 (?:Indiciu|Mai clar)/ });
async function askHint(page, id) {
  const response = responseFor(page, id, "hint");
  await hintButton(page).click();
  return response;
}

test("a lost winning hop adopts the server result and records it once without replay", async ({ page, request }) => {
  const initial = await start(page, game);
  await approachTarget(page);
  const counts = traffic(page, initial.game_id);
  const committed = await loseCommittedResponse(page, initial.game_id, "move");
  expect((await act(page, game, answer())).status()).toBe(503);
  await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
  await expect.poll(() => played(page)).toBe(1);
  await expect.poll(() => remembered(page)).toBeNull();
  expect(committed().won).toBe(true);
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.won).toBe(true);
  expect(server.moves).toBe(steps().length);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  await expect(page.getByText("EȘTI ACUM LA", { exact: true }).locator("..").getByText(server.current.label, { exact: true })).toHaveCSS("opacity", "1");
  await page.screenshot({ path: test.info().outputPath("recovered-win.png"), fullPage: true });
  await page.reload();
  await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
  expect(await played(page)).toBe(1);
});

test("a lost earned hint restores the exact stage and resume does not escalate it", async ({ page, request }) => {
  const initial = await start(page, game);
  expect(initial.earned_hint).toBeUndefined();
  const counts = traffic(page, initial.game_id);
  const committed = await loseCommittedResponse(page, initial.game_id, "hint");
  expect((await askHint(page, initial.game_id)).status()).toBe(503);
  await expect(page.getByText("O DIRECȚIE", { exact: true })).toBeVisible();
  await expect(hintButton(page)).toBeEnabled();
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.earned_hint).toEqual(committed());
  expect(server.earned_hint.stage).toBe("direction");
  expect(server.earned_hint.hint).toBeNull();
  expect(server.earned_hint.alternatives_labels).toBeUndefined();
  expect(server.moves).toBe(0);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  await expect(page.getByText("O DIRECȚIE", { exact: true }).locator("../..")).toHaveCSS("opacity", "1");
  await page.getByText("O DIRECȚIE", { exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: test.info().outputPath("recovered-hint.png") });
  await page.reload();
  await expect(page.getByText("O DIRECȚIE", { exact: true })).toBeVisible();
  expect((await (await askHint(page, initial.game_id)).json()).stage).toBe("alternatives");
  await expect(page.getByText("VARIANTE UTILE", { exact: true })).toBeVisible();
  expect(counts.mutations).toBe(2); // The second POST is the player's next explicit request.
  expect(await played(page)).toBe(0);
});

test("a lost undo restores the earlier position and discards help earned at the undone position", async ({ page, request }) => {
  const initial = await start(page, game);
  expect((await (await act(page, game, firstMove())).json()).won).toBe(false);
  expect((await (await askHint(page, initial.game_id)).json()).stage).toBe("direction");
  const counts = traffic(page, initial.game_id);
  await loseCommittedResponse(page, initial.game_id, "undo");
  const response = responseFor(page, initial.game_id, "undo");
  await page.getByRole("button", { name: "Înapoi", exact: true }).click();
  expect((await response).status()).toBe(503);
  await expect(field(page)).toBeEnabled();
  await expect(page.locator(".hud")).toContainText("0 mutări");
  await expect(page.getByText("O DIRECȚIE", { exact: true })).toHaveCount(0);
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.current).toEqual(initial.current);
  expect(server.path).toEqual(initial.path);
  expect(server.earned_hint).toBeUndefined();
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  expect((await (await askHint(page, initial.game_id)).json()).stage).toBe("alternatives");
});

test("failed verification locks mutations and its persistent retry only reads", async ({ page, request }) => {
  await page.clock.install();
  const initial = await start(page, game);
  const counts = traffic(page, initial.game_id);
  await loseCommittedResponse(page, initial.game_id, "move");
  await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({
    status: 503, contentType: "application/json", body: "{}",
  }), { times: 1 });
  expect((await act(page, game, firstMove())).status()).toBe(503);
  await expect(verify(page)).toBeEnabled();
  await expect(page.locator(".lant-sync-recovery")).toBeInViewport();
  await expect(field(page)).toBeDisabled();
  await expect(field(page)).toHaveValue(firstMove().payload.text);
  for (const button of await page.locator(".lant-choice-grid button").all()) {
    await expect(button).toBeDisabled();
  }
  await expect(hintButton(page)).toBeDisabled();
  await expect(page.getByRole("button", { name: "Înapoi", exact: true })).toBeDisabled();
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
  await expect(field(page)).toHaveValue("");
  await expect(verify(page)).toHaveCount(0);
  await expect(page.locator(".hud")).toContainText("1 mutare");
  expect(counts).toEqual({ reads: 2, mutations: 1 });
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.moves).toBe(1);
  expect(server.won).toBe(false);
});

test("a failure before commit keeps the input and earned help without an extra request", async ({ page, request }) => {
  const initial = await start(page, game);
  const earned = await (await askHint(page, initial.game_id)).json();
  const before = await (await request.get(gameURL(game, initial.game_id))).json();
  const counts = traffic(page, initial.game_id);
  await page.route(`**${gameURL(game, initial.game_id)}/move`, (route) => route.fulfill({
    status: 503, contentType: "application/json", body: "{}",
  }), { times: 1 });
  expect((await act(page, game, firstMove())).status()).toBe(503);
  await expect(field(page)).toBeEnabled();
  await expect(field(page)).toHaveValue(firstMove().payload.text);
  await expect(page.getByText("O DIRECȚIE", { exact: true })).toBeVisible();
  expect(await (await request.get(gameURL(game, initial.game_id))).json()).toEqual(before);
  expect(before.earned_hint).toEqual(earned);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  const accepted = await act(page, game, firstMove());
  expect((await accepted.json()).moves).toBe(1);
  await expect(page.getByText("O DIRECȚIE", { exact: true })).toHaveCount(0);
  expect(counts.mutations).toBe(2);
});

for (const missing of [false, true]) {
  test(`a late ${missing ? "404" : "winning"} read cannot adopt or clear another tab's round`, async ({ page, context, request }) => {
    const initial = await start(page, game);
    const newer = await newerRound(request);
    await approachTarget(page);
    await loseCommittedResponse(page, initial.game_id, "move");
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
    await expect(page.locator(".hud")).toContainText("0 mutări");
    expect(await remembered(page)).toBe(newer.game_id);
    expect(await played(page)).toBe(0);
    await other.close();
  });
}

test("leaving during recovery preserves the old pointer and a late callback cannot overwrite a new screen", async ({ page, context, request }) => {
  const initial = await start(page, game);
  await approachTarget(page);
  await loseCommittedResponse(page, initial.game_id, "move");
  const held = await holdRecovery(page, initial.game_id);
  expect((await act(page, game, answer())).status()).toBe(503);
  await held.requested;
  await page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true }).click();
  await expect(page.getByRole("button", { name: /^Joacă Lanțul Cuvintelor —/ })).toBeVisible();
  expect(await remembered(page)).toBe(initial.game_id);
  const newer = await newerRound(request);
  const other = await saveFromOtherTab(context, newer.game_id);
  const loaded = responseFor(page, newer.game_id, "", "GET");
  await page.getByRole("button", { name: /^Joacă Lanțul Cuvintelor —/ }).click();
  expect((await loaded).status()).toBe(200);
  await expect(field(page)).toBeEnabled();
  const oldCompleted = responseFor(page, initial.game_id, "", "GET");
  held.release();
  await oldCompleted;
  await expect(page.locator(".hud")).toContainText("0 mutări");
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
  for (const suffix of ["/move", ""]) {
    await page.route(`**${gameURL(game, initial.game_id)}${suffix}`, (route) => route.fulfill({
      status: 404, contentType: "application/json", body: "{}",
    }), { times: 1 });
  }
  expect((await act(page, game, { action: "move", payload: { text: firstMove().payload.text } })).status()).toBe(404);
  await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
  expect(await remembered(page)).toBeNull();
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  expect(await played(page)).toBe(0);
});
