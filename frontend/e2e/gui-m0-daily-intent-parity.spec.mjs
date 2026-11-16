import { expect, test } from "@playwright/test";
import { games, gameURL } from "./games.mjs";

const day = "2026-10-08";
const previousDay = "2026-10-07";
const time = new Date(day + "T12:00:00Z");
const endpoint = (game) => `/api/wordgames/${game.key}/games`;
const createResponse = (page, game) => page.waitForResponse((response) =>
  response.request().method() === "POST" && new URL(response.url()).pathname === endpoint(game));

async function savedRound(page, game, gameId) {
  await page.addInitScript(({ key, gameId }) => {
    const slot = `cat_active_game_v1_${key}`;
    if (!sessionStorage.getItem(slot)) {
      sessionStorage.setItem(slot, "ready");
      localStorage.setItem(slot, gameId);
    }
  }, { key: game.key, gameId });
}

for (const game of games) {
  test(`${game.key} daily alias resumes the older day's still-live daily`, async ({ page, request }) => {
    await page.clock.setFixedTime(time);
    const original = await request.post(endpoint(game) + "?daily=" + previousDay);
    expect(original.status()).toBe(200);
    const { game_id: gameId } = await original.json();
    await savedRound(page, game, gameId);
    const posts = [];
    page.on("request", (request) => {
      if (request.method() === "POST" && new URL(request.url()).pathname === endpoint(game)) posts.push(request.url());
    });
    const resumed = page.waitForResponse((response) => new URL(response.url()).pathname === gameURL(game, gameId));
    await page.goto(game.path + "?challenge=daily");
    const state = await (await resumed).json();
    expect(state.daily).toBe(previousDay);
    await expect(page.locator(game.board)).toBeVisible();
    await expect(page.getByText("Jocul zilei", { exact: true })).toBeVisible();
    expect(posts).toEqual([]);
  });

  test(`${game.key} untouched daily comes before a parked free round`, async ({ page, request }) => {
    await page.clock.setFixedTime(time);
    const original = await request.post(endpoint(game) + "?seed=38");
    expect(original.status()).toBe(200);
    const { game_id: gameId } = await original.json();
    await savedRound(page, game, gameId);
    const response = createResponse(page, game);
    await page.goto(game.path);
    const started = await response;
    expect(started.status()).toBe(200);
    expect((await started.json()).daily).toBe(day);
    await expect(page.locator(game.board)).toBeVisible();
    expect(await page.evaluate((key) => localStorage.getItem(`cat_parked_free_v2_${key}`), game.key)).toBe(gameId);
  });
}

for (const game of games.filter(({ derived }) => !derived)) {
  test(`${game.key} shared easy daily ignores stored free difficulty and theme`, async ({ page }) => {
    await page.clock.setFixedTime(time);
    await page.addInitScript((key) => localStorage.setItem(`cat_free_v2_${key}`,
      JSON.stringify({ difficulty: "normal", category: "istorie" })), game.key);
    const response = createResponse(page, game);
    await page.goto(game.path + "?challenge=daily");
    const created = await response;
    const query = new URL(created.url()).searchParams;
    expect(query.get("daily")).toBe(day);
    expect(query.get("category")).toBeNull();
    expect((await created.json()).difficulty).toBe("usor");
    await expect(page.locator(game.board)).toBeVisible();
    await page.getByRole("button", { name: "Cum se joacă" }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByLabel("Dificultate")).toHaveValue("normal");
    await dialog.getByLabel("Dificultate").selectOption("greu");
    expect(await page.evaluate((key) => JSON.parse(localStorage.getItem(`cat_free_v2_${key}`)).difficulty, game.key))
      .toBe("greu");
  });
}
