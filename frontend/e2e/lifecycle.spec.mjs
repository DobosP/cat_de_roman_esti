import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, seededStarts, solution, start, solve, act } from "./games.mjs";

async function reloadState(page, game, id) {
  // A failed action may already have a recovery GET in flight. Match a request
  // issued by the new document, and read its body before any further navigation.
  let navigated = false;
  const onNavigation = (frame) => {
    if (frame === page.mainFrame()) navigated = true;
  };
  page.on("framenavigated", onNavigation);
  const body = page.waitForRequest((request) => navigated &&
    request.method() === "GET" && new URL(request.url()).pathname === gameURL(game, id))
    .then(async (request) => {
      const response = await request.response();
      expect(response).not.toBeNull();
      expect(response.status()).toBe(200);
      return response.json();
    });
  try {
    const [state] = await Promise.all([body, page.reload()]);
    return state;
  } finally {
    page.off("framenavigated", onNavigation);
  }
}

async function visibleProgress(page, game, state) {
  if (game.key === "conexiuni") {
    await expect(page.getByLabel(`${state.lives} greșeli disponibile`, { exact: true })).toBeVisible();
    return;
  }
  const label = game.key === "alchimie" ? /^Combinații$/i :
    game.key === "lant" ? /^Mutări$/i : /^Încercări$/i;
  const value = game.key === "alchimie" ? String(state.moves) :
    game.key === "lant" ? `${state.moves} ${state.moves === 1 ? "mutare" : "mutări"}` :
    game.key === "contexto" ? `${state.attempts} ${state.attempts === 1 ? "încercare" : "încercări"}` :
    `${state.remaining_mistakes} rămase`;
  await expect(page.locator(".hud .stat-badge").filter({
    has: page.locator(".stat-badge-label", { hasText: label }),
  }).locator(".stat-badge-value")).toHaveText(value);
}

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
      await visibleProgress(page, game, expected);
      expect(await reloadState(page, game, state.game_id)).toEqual(expected);
      await expect(page.locator(game.board)).toBeVisible();
      await visibleProgress(page, game, expected);
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

    test("keeps a round playable after a failed action and reload", async ({ page, request }) => {
      const state = await start(page, game);
      const step = solution(game).steps[0];
      await page.route(`**${gameURL(game, state.game_id)}/${step.action}`, (route) => route.fulfill({
        status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Încearcă din nou." }),
      }), { times: 1 });
      expect((await act(page, game, step)).status()).toBe(503);
      expect(await (await request.get(gameURL(game, state.game_id))).json()).toEqual(state);
      expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(state.game_id);
      expect(await reloadState(page, game, state.game_id)).toEqual(state);
      await expect(page.locator(game.board)).toBeVisible();
      expect((await act(page, game, step)).status()).toBe(200);
    });
  });
}
