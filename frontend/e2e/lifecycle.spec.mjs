import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, seededStarts, solution, start, solve, act } from "./games.mjs";

for (const game of games) {
  test.describe(game.key, () => {
    test.beforeEach(async ({ page }) => {
      await deterministicStarts(page, game);
    });

    test("plays a real seeded round to a server-scored result and replays", async ({ page }) => {
      const expected = solution(game);
      const state = await start(page, game);
      const { game_id: id, ...publicState } = state;
      expect(publicState).toEqual(seededStarts[game.key]);
      expect(publicState).toEqual(expected.initial);
      expect(publicState).not.toHaveProperty("score");
      expect(publicState).not.toHaveProperty("solution");
      expect(publicState).not.toHaveProperty("recipes");
      expect(publicState).not.toHaveProperty("source_id");
      if (game.key === "contexto") expect(publicState).not.toHaveProperty("target");
      await solve(page, game, expected.steps);
      await expect.poll(() => page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBeNull();
      const created = page.waitForResponse((r) => r.request().method() === "POST" &&
        new URL(r.url()).pathname === `/api/wordgames/${game.key}/games`);
      await page.getByRole("button", { name: /^Încă (?:unul|un lanț) →$/ }).click();
      expect((await (await created).json()).game_id).not.toBe(id);
      await expect(page.locator(game.board)).toBeVisible();
    });

    test("preserves earned progress and mistakes through reload", async ({ page, request }) => {
      const state = await start(page, game);
      const practiced = await act(page, game, solution(game).practice);
      expect(practiced.status()).toBe(200);
      const expected = await (await request.get(gameURL(game, state.game_id))).json();
      expect(expected.won).toBe(false);
      expect(expected).not.toEqual(state);
      const resumed = page.waitForResponse((r) => r.request().method() === "GET" &&
        new URL(r.url()).pathname === gameURL(game, state.game_id));
      await page.reload();
      expect(await (await resumed).json()).toEqual(expected);
      await expect(page.locator(game.board)).toBeVisible();
      expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBe(state.game_id);
    });

    test("recovers an expired saved ID into a playable fresh start", async ({ page }) => {
      const state = await start(page, game);
      await page.route(`**${gameURL(game, state.game_id)}`, (route) => route.fulfill({
        status: 404, contentType: "application/json", body: JSON.stringify({ detail: "Joc inexistent" }),
      }), { times: 1 });
      await page.reload();
      await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
      expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBeNull();
      const fresh = await start(page, game);
      expect(fresh.game_id).not.toBe(state.game_id);
    });

    test("can retry a failed create without leaving the game", async ({ page }) => {
      await page.goto(game.path);
      await page.route(`**/api/wordgames/${game.key}/games?*`, (route) => route.fulfill({
        status: 503, contentType: "application/json",
        body: JSON.stringify({ detail: "Serviciu indisponibil temporar." }),
      }), { times: 1 });
      await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
      await expect(page.getByText(/Serviciu indisponibil temporar\.|Nu am putut porni jocul/))
        .toBeVisible();
      await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
      const created = page.waitForResponse((r) => r.request().method() === "POST" &&
        new URL(r.url()).pathname === `/api/wordgames/${game.key}/games`);
      await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
      expect((await created).status()).toBe(200);
      await expect(page.locator(game.board)).toBeVisible();
    });
  });
}
