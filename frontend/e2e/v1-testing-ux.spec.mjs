import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, start, solve, solution, act } from "./games.mjs";

const createPath = (game) => `/api/wordgames/${game.key}/games`;
const isCreate = (game) => (response) => response.request().method() === "POST" && new URL(response.url()).pathname === createPath(game);
const homeCard = (page, game) => page.locator(`.games-grid a[href="${game.path}"]`);
const dayInBrowser = (page) => page.evaluate(() => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
});

for (const game of games) {
  test(`${game.key} starts today's daily once when its card is activated`, async ({ page }) => {
    await page.clock.setFixedTime(new Date("2026-11-16T12:00:00.000Z"));
    await page.goto("/");
    const creates = [];
    page.on("request", (request) => {
      if (request.method() === "POST" && new URL(request.url()).pathname === createPath(game)) creates.push(request.url());
    });
    const expectedDay = await dayInBrowser(page);
    await homeCard(page, game).focus();
    expect(creates).toHaveLength(0);
    const created = page.waitForResponse(isCreate(game));
    await page.keyboard.press("Enter");
    const response = await created;
    expect(response.status()).toBe(200);
    expect(new URL(response.url()).searchParams.get("daily")).toBe(expectedDay);
    expect((await response.json()).daily).toBe(expectedDay);
    await expect(page.locator(game.board)).toBeVisible();
    await expect(page.locator(".game-frame-mode")).toHaveText("Jocul zilei");
    expect(creates).toHaveLength(1);
  });

  test(`${game.key} daily link starts a free round when today's daily is done`, async ({ page }) => {
    await deterministicStarts(page, game);
    const created = page.waitForResponse(isCreate(game));
    await page.goto(`${game.path}?challenge=daily`);
    const response = await created;
    expect(response.status()).toBe(200);
    expect(new URL(response.url()).searchParams.get("daily")).toBeNull();
    expect((await response.json()).daily).toBeFalsy();
    await expect(page.locator(game.board)).toBeVisible();
    await expect(page.locator(".game-frame-mode")).toHaveText("Rundă liberă");
  });
}

test("a finished daily marks its Home card and one tap enters a free round", async ({ page }) => {
  const game = games.find(({ key }) => key === "lant");
  await page.clock.setFixedTime(new Date("2026-11-16T12:00:00.000Z"));
  await page.goto("/");
  const expectedDay = await dayInBrowser(page);
  const created = page.waitForResponse(isCreate(game));
  await homeCard(page, game).click();
  expect((await (await created).json()).daily).toBe(expectedDay);
  await solve(page, game, solution({ ...game, daily: expectedDay }).steps);
  await page.locator(".game-result").getByRole("button", { name: "Înapoi la jocuri" }).click();
  await expect(homeCard(page, game)).toContainText("Gata azi");
  const free = page.waitForResponse(isCreate(game));
  await homeCard(page, game).click();
  expect((await (await free).json()).daily).toBeFalsy();
  await expect(page.locator(".game-frame-mode")).toHaveText("Rundă liberă");
});

test("first visit presents six descriptive illustrated game choices without daily completion badges", async ({ page }) => {
  await page.goto("/");
  const cards = page.locator(".games-grid a.game-card");
  await expect(cards).toHaveCount(6);
  await expect(cards.locator("img[alt='']")).toHaveCount(6);
  await expect(cards.locator("span:not(.game-card-done)")).toHaveCount(6);
  await expect(cards.locator(".game-card-done")).toHaveCount(0);
});

test("one-tap entry resumes an unfinished daily without creating a new round", async ({ page, request }) => {
  const game = games.find(({ key }) => key === "intrusul");
  await page.clock.setFixedTime(new Date("2026-11-16T12:00:00.000Z"));
  const initial = await start(page, game);
  expect(initial.daily).toBe(await dayInBrowser(page));
  await page.getByRole("button", { name: "Înapoi la jocuri", exact: true }).click();
  const creates = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname === createPath(game)) creates.push(request.url());
  });
  await homeCard(page, game).click();
  await expect(page.locator(game.board)).toBeVisible();
  expect(creates).toHaveLength(0);
  expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(initial.game_id);
  expect(await (await request.get(gameURL(game, initial.game_id))).json()).toEqual(initial);
  expect((await (await act(page, game, solution({ ...game, daily: initial.daily }).steps[0])).json()).won).toBe(true);

  const created = page.waitForResponse(isCreate(game));
  await page.getByRole("button", { name: "Încă o rundă", exact: true }).click();
  const response = await created;
  expect(response.status()).toBe(200);
  expect(new URL(response.url()).searchParams.get("daily")).toBeNull();
  expect((await response.json()).daily).toBeFalsy();
  await expect(page.locator(game.board)).toBeVisible();
  expect(creates).toHaveLength(1);
});

for (const game of games.filter(({ derived }) => derived)) {
  test(`${game.key} replay is the first result action and creates just one new round`, async ({ page }) => {
    await deterministicStarts(page, game);
    await start(page, game);
    await solve(page, game, solution(game).steps, { keyboard: true });
    const replay = page.getByRole("button", { name: "Încă o rundă", exact: true });
    await expect(replay.locator("..").getByRole("button").first()).toHaveText("Încă o rundă");
    await expect(page.getByRole("button", { name: "Schimbă opțiunile", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Copiază rezultatul", exact: true })).toBeVisible();
    const creates = [];
    page.on("request", (request) => {
      if (request.method() === "POST" && new URL(request.url()).pathname === createPath(game)) creates.push(request.url());
    });
    const created = page.waitForResponse((response) => response.request().method() === "POST" && new URL(response.url()).pathname === createPath(game));
    await replay.click();
    expect((await created).status()).toBe(200);
    await expect(page.locator(game.board)).toBeVisible();
    expect(creates).toHaveLength(1);
  });
}

test("Perechi distinguishes mistakes remaining from successful attempts", async ({ page }) => {
  const game = games.find(({ key }) => key === "perechi");
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const budget = page.locator(".game-frame-status");
  await expect(budget).toContainText(`${initial.remaining_mistakes} încercări`);
  const result = await (await act(page, game, solution(game).steps[0])).json();
  expect(result.solved_count).toBe(1);
  expect(result.remaining_mistakes).toBe(initial.remaining_mistakes);
  await expect(budget).toContainText(`${initial.remaining_mistakes} încercări`);
});
