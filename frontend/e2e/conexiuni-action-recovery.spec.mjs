import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, solution, start } from "./games.mjs";

const game = games.find(({ key }) => key === "conexiuni");
const scoresKey = "cat_wordgame_scores_v1";
const verify = (page) => page.getByRole("button", { name: "Verifică jocul", exact: true });
const currentGame = (page) => page.getByRole("button", { name: "Încarcă jocul curent", exact: true });
const clueButton = (page) => page.getByRole("button", { name: /^Indiciu/ });
const steps = () => solution(game).steps;
const wrong = (index) => ({
  payload: { ids: steps().map((step) => step.payload.ids[index]) },
  labels: steps().map((step) => step.labels[index]),
});

async function remembered(page) {
  return page.evaluate((key) => localStorage.getItem(key), activeKey(game));
}

async function played(page) {
  return page.evaluate((key) => JSON.parse(localStorage.getItem(key) || "{}").conexiuni?.played ?? 0, scoresKey);
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

async function choose(page, step) {
  const clear = page.getByRole("button", { name: "Golește", exact: true });
  if (await clear.isEnabled()) await clear.click();
  for (const label of step.labels) {
    await page.locator(game.board).getByRole("button", { name: label, exact: true }).click();
  }
}

async function guess(page, id, step) {
  await choose(page, step);
  const response = responseFor(page, id, "guess");
  await page.getByRole("button", { name: "Verifică", exact: true }).click();
  return response;
}

async function askClue(page, id) {
  const response = responseFor(page, id, "clue");
  await clueButton(page).click();
  return response;
}

async function prepare(page, request, { mistakes = 0, solved = 0 } = {}) {
  const initial = await start(page, game);
  for (let index = 0; index < mistakes; index += 1) {
    expect((await request.post(`${gameURL(game, initial.game_id)}/guess`, { data: wrong(index).payload })).status()).toBe(200);
  }
  for (const step of steps().slice(0, solved)) {
    expect((await request.post(`${gameURL(game, initial.game_id)}/guess`, { data: step.payload })).status()).toBe(200);
  }
  if (mistakes || solved) {
    await page.reload();
    await expect(page.locator(`${game.board} button`)).toHaveCount(16 - solved * 4);
    await expect(page.locator(".connections-lives")).toHaveAttribute("aria-label", `${4 - mistakes} ${mistakes === 3 ? "greșeală disponibilă" : "greșeli disponibile"}`);
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

async function newerRound(request) {
  const response = await request.post("/api/wordgames/conexiuni/games?seed=39&difficulty=usor");
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

test("a lost first clue is restored once, resumes exactly, and retains 100 points", async ({ page, request }) => {
  const initial = await prepare(page, request, { mistakes: 3 });
  const counts = traffic(page, initial.game_id);
  const committed = await loseCommittedResponse(page, initial.game_id, "clue");
  expect((await askClue(page, initial.game_id)).status()).toBe(503);
  await expect(page.locator(".connections-feedback [role=status]").filter({ hasText: "Joc sincronizat. Poți continua." })).toBeVisible();
  await expect(clueButton(page)).toContainText("1 rămas");
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.clues_used).toBe(1);
  expect(server.clues).toEqual(committed().clues);
  expect(server.solution).toBeUndefined();
  expect(server.solved).toEqual([]);
  await expect(page.getByText(server.clues[0].message, { exact: false })).toHaveCount(1);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  await page.locator(".connections-feedback").scrollIntoViewIfNeeded();
  await expect(page.locator(".connections-feedback")).toHaveCSS("opacity", "1");
  await page.screenshot({ path: test.info().outputPath("recovered-clue.png") });
  await page.reload();
  await expect(clueButton(page)).toContainText("1 rămas");
  await expect(page.getByText(server.clues[0].message, { exact: false })).toHaveCount(1);
  for (const step of steps()) expect((await guess(page, initial.game_id, step)).status()).toBe(200);
  await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
  expect((await (await request.get(gameURL(game, initial.game_id))).json()).score).toBe(150);
  await expect.poll(() => played(page)).toBe(1);
  expect(counts.mutations).toBe(5);
});

test("a lost solved group removes only its four earned tiles and leaves answers private", async ({ page, request }) => {
  const initial = await prepare(page, request);
  const counts = traffic(page, initial.game_id);
  const committed = await loseCommittedResponse(page, initial.game_id, "guess");
  expect((await guess(page, initial.game_id, steps()[0])).status()).toBe(503);
  await expect(page.locator(`${game.board} button`)).toHaveCount(12);
  await expect(page.locator(`${game.board} [aria-pressed=true]`)).toHaveCount(0);
  await expect(page.getByText(committed().category.label, { exact: true })).toBeVisible();
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.solved_count).toBe(1);
  expect(server.solved).toEqual(committed().solved);
  expect(server.solution).toBeUndefined();
  expect(server.one_away).toBeUndefined();
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  expect(await played(page)).toBe(0);
});

for (const lost of [false, true]) {
  test(`a lost committed ${lost ? "loss" : "win"} adopts the terminal score exactly once`, async ({ page, request }) => {
    const initial = await prepare(page, request, lost ? { mistakes: 3 } : { solved: 3 });
    const counts = traffic(page, initial.game_id);
    const committed = await loseCommittedResponse(page, initial.game_id, "guess");
    expect((await guess(page, initial.game_id, lost ? wrong(3) : steps()[3])).status()).toBe(503);
    await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
    await expect(page.getByText(lost ? "Ai rămas fără vieți." : "Ai găsit toate grupurile!", { exact: true })).toBeVisible();
    await expect.poll(() => played(page)).toBe(1);
    await expect.poll(() => remembered(page)).toBeNull();
    const server = await (await request.get(gameURL(game, initial.game_id))).json();
    expect(server.won).toBe(!lost);
    expect(server.lost).toBe(lost);
    expect(server.score).toBe(lost ? 0 : 1000);
    expect(server.score).toBe(committed().score);
    expect(server.solution).toHaveLength(4);
    expect(counts).toEqual({ reads: 1, mutations: 1 });
    await expect(page.getByText(lost ? "Ai rămas fără vieți." : "Ai găsit toate grupurile!", { exact: true }).locator("../..")).toHaveCSS("opacity", "1");
    await page.getByRole("button", { name: "Copiază rezultatul" }).scrollIntoViewIfNeeded();
    await expect(page.getByText("Joc reluat.", { exact: true })).toHaveCount(0);
    await page.screenshot({ path: test.info().outputPath(`recovered-${lost ? "loss" : "win"}.png`) });
    await page.reload();
    await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
    expect(await played(page)).toBe(1);
  });
}

test("failed verification persists, locks every board action, and retries by GET only", async ({ page, request }) => {
  await page.clock.install();
  const initial = await prepare(page, request, { mistakes: 3 });
  const counts = traffic(page, initial.game_id);
  await loseCommittedResponse(page, initial.game_id, "clue");
  await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({
    status: 503, contentType: "application/json", body: "{}",
  }), { times: 1 });
  expect((await askClue(page, initial.game_id)).status()).toBe(503);
  await expect(verify(page)).toBeEnabled();
  for (const button of await page.locator(`${game.board} button`).all()) await expect(button).toBeDisabled();
  for (const name of ["Verifică", "Amestecă", "Golește"]) {
    await expect(page.getByRole("button", { name, exact: true })).toBeDisabled();
  }
  await expect(clueButton(page)).toBeDisabled();
  await page.keyboard.press("Enter");
  await page.clock.fastForward(4000);
  // A fast-forward fires one animation frame; let the screen transition actually finish.
  await page.clock.runFor(500);
  await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
  await expect(verify(page)).toBeVisible();
  await page.locator(".connections-sync-recovery").scrollIntoViewIfNeeded();
  await expect(page.locator(".connections-sync-recovery")).toBeInViewport();
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  expect(await remembered(page)).toBe(initial.game_id);
  await page.screenshot({ path: test.info().outputPath("read-only-recovery.png") });
  const response = responseFor(page, initial.game_id, "", "GET");
  await verify(page).click();
  expect((await response).status()).toBe(200);
  await expect(verify(page)).toHaveCount(0);
  await expect(clueButton(page)).toBeEnabled();
  await expect(clueButton(page)).toContainText("1 rămas");
  expect((await (await request.get(gameURL(game, initial.game_id))).json()).clues_used).toBe(1);
  expect(counts).toEqual({ reads: 2, mutations: 1 });
});

test("precommit failure preserves a valid selection and earned clue without replay", async ({ page, request }) => {
  const initial = await prepare(page, request, { mistakes: 2 });
  expect((await askClue(page, initial.game_id)).status()).toBe(200);
  const before = await (await request.get(gameURL(game, initial.game_id))).json();
  const counts = traffic(page, initial.game_id);
  await page.route(`**${gameURL(game, initial.game_id)}/guess`, (route) => route.fulfill({
    status: 503, contentType: "application/json", body: "{}",
  }), { times: 1 });
  expect((await guess(page, initial.game_id, steps()[0])).status()).toBe(503);
  await expect(page.locator(".connections-feedback [role=status]").filter({ hasText: "Joc sincronizat. Poți continua." })).toBeVisible();
  await expect(page.getByRole("button", { name: "Verifică", exact: true })).toBeEnabled();
  await expect(page.locator(`${game.board} [aria-pressed=true]`)).toHaveCount(4);
  await expect(page.getByText(before.clues[0].message, { exact: false })).toHaveCount(1);
  expect(await (await request.get(gameURL(game, initial.game_id))).json()).toEqual(before);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  const response = responseFor(page, initial.game_id, "guess");
  await page.getByRole("button", { name: "Verifică", exact: true }).click();
  expect((await (await response).json()).solved_count).toBe(1);
  expect(counts.mutations).toBe(2);
});

for (const missing of [false, true]) {
  test(`a late ${missing ? "404" : "winning"} read cannot adopt or clear another tab's saved round`, async ({ page, context, request }) => {
    const initial = await prepare(page, request, { solved: 3 });
    const newer = await newerRound(request);
    await loseCommittedResponse(page, initial.game_id, "guess");
    const held = await holdRecovery(page, initial.game_id, missing);
    expect((await guess(page, initial.game_id, steps()[3])).status()).toBe(503);
    await held.requested;
    const other = await saveFromOtherTab(context, newer.game_id);
    held.release();
    await expect(currentGame(page)).toBeEnabled();
    await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toHaveCount(0);
    expect(await remembered(page)).toBe(newer.game_id);
    expect(await played(page)).toBe(0);
    const loaded = responseFor(page, newer.game_id, "", "GET");
    await currentGame(page).click();
    expect((await loaded).status()).toBe(200);
    await expect(page.locator(`${game.board} button`)).toHaveCount(16);
    expect(await remembered(page)).toBe(newer.game_id);
    expect(await played(page)).toBe(0);
    await other.close();
  });
}

test("leaving during recovery preserves its pointer and stale completion cannot change a new screen", async ({ page, context, request }) => {
  const initial = await prepare(page, request, { solved: 3 });
  await loseCommittedResponse(page, initial.game_id, "guess");
  const held = await holdRecovery(page, initial.game_id);
  expect((await guess(page, initial.game_id, steps()[3])).status()).toBe(503);
  await held.requested;
  await page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true }).click();
  await expect(page.getByRole("button", { name: /^Joacă Conexiuni —/ })).toBeVisible();
  expect(await remembered(page)).toBe(initial.game_id);
  const newer = await newerRound(request);
  const other = await saveFromOtherTab(context, newer.game_id);
  const loaded = responseFor(page, newer.game_id, "", "GET");
  await page.getByRole("button", { name: /^Joacă Conexiuni —/ }).click();
  expect((await loaded).status()).toBe(200);
  const oldCompleted = responseFor(page, initial.game_id, "", "GET");
  held.release();
  await oldCompleted;
  await expect(page.locator(`${game.board} button`)).toHaveCount(16);
  await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toHaveCount(0);
  expect(await remembered(page)).toBe(newer.game_id);
  expect(await played(page)).toBe(0);
  await other.close();
});

test("an already different saved pointer pauses before any old-round mutation", async ({ page, context, request }) => {
  const initial = await prepare(page, request);
  const newer = await newerRound(request);
  const other = await saveFromOtherTab(context, newer.game_id);
  const counts = traffic(page, initial.game_id);
  await choose(page, steps()[0]);
  await page.getByRole("button", { name: "Verifică", exact: true }).click();
  await expect(currentGame(page)).toBeEnabled();
  expect(counts).toEqual({ reads: 0, mutations: 0 });
  expect(await (await request.get(gameURL(game, initial.game_id))).json()).toEqual(initial);
  expect(await remembered(page)).toBe(newer.game_id);
  await currentGame(page).click();
  await expect(page.locator(`${game.board} button`)).toHaveCount(16);
  expect(await played(page)).toBe(0);
  await other.close();
});

test("a verified missing owned session returns to setup and conditionally clears its pointer", async ({ page, request }) => {
  const initial = await prepare(page, request);
  const counts = traffic(page, initial.game_id);
  for (const suffix of ["/guess", ""]) {
    await page.route(`**${gameURL(game, initial.game_id)}${suffix}`, (route) => route.fulfill({
      status: 404, contentType: "application/json", body: "{}",
    }), { times: 1 });
  }
  expect((await guess(page, initial.game_id, steps()[0])).status()).toBe(404);
  await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
  expect(await remembered(page)).toBeNull();
  expect(await played(page)).toBe(0);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
});

test("lost one-away feedback stays neutral and confirmed duplicate feedback still requires a change", async ({ page, request }) => {
  const initial = await prepare(page, request);
  const counts = traffic(page, initial.game_id);
  const committed = await loseCommittedResponse(page, initial.game_id, "guess");
  expect((await guess(page, initial.game_id, solution(game).practice)).status()).toBe(503);
  await expect(page.locator(".connections-feedback [role=status]").filter({ hasText: "Joc sincronizat. Poți continua." })).toBeVisible();
  expect(committed().one_away).toBe(true);
  await expect(page.locator(".connections-feedback [role=status]").filter({ hasText: "Aproape: 3 din 4. Schimbă o piesă." })).toHaveCount(0);
  const duplicate = responseFor(page, initial.game_id, "guess");
  await page.getByRole("button", { name: "Verifică", exact: true }).click();
  expect((await duplicate).status()).toBe(409);
  await expect(page.getByRole("button", { name: "Schimbă o piesă", exact: true })).toBeDisabled();
  await expect(page.locator(`${game.board} [aria-pressed=true]`)).toHaveCount(4);
  await expect(page.locator(".connections-feedback [role=status]").filter({ hasText: "Aproape: 3 din 4. Schimbă o piesă." })).toHaveCount(0);
  expect((await (await request.get(gameURL(game, initial.game_id))).json()).mistakes).toBe(1);
  expect(counts).toEqual({ reads: 2, mutations: 2 });
  expect((await guess(page, initial.game_id, steps()[0])).status()).toBe(200);
  await expect(page.locator(`${game.board} button`)).toHaveCount(12);
});

test("a confirmed duplicate remains blocked after failed verification and manual read", async ({ page, request }) => {
  const initial = await prepare(page, request);
  expect((await guess(page, initial.game_id, solution(game).practice)).status()).toBe(200);
  await expect(page.locator(".connections-feedback [role=status]").filter({ hasText: "Aproape: 3 din 4. Schimbă o piesă." })).toBeVisible();
  const counts = traffic(page, initial.game_id);
  await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({
    status: 503, contentType: "application/json", body: "{}",
  }), { times: 1 });
  expect((await guess(page, initial.game_id, solution(game).practice)).status()).toBe(409);
  await expect(verify(page)).toBeEnabled();
  await verify(page).click();
  await expect(verify(page)).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Schimbă o piesă", exact: true })).toBeDisabled();
  await expect(page.locator(`${game.board} [aria-pressed=true]`)).toHaveCount(4);
  await expect(page.locator(".connections-feedback [role=status]").filter({ hasText: "Aproape: 3 din 4. Schimbă o piesă." })).toHaveCount(0);
  expect((await (await request.get(gameURL(game, initial.game_id))).json()).mistakes).toBe(1);
  expect(counts).toEqual({ reads: 2, mutations: 1 });
});
