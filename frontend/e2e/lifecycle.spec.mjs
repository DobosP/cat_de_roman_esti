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
  const text = game.key === "alchimie" ? `${state.moves} ${state.moves === 1 ? "combinație" : "combinații"}`
    : game.key === "lant" ? `${state.moves} ${state.moves === 1 ? "salt" : "salturi"}`
    : (() => {
      const attempts = state.lives ?? state.remaining_mistakes ?? state.attempts;
      return attempts === 1 ? "O încercare" : `${attempts} încercări`;
    })();
  await expect(page.locator(".game-frame-status")).toContainText(text);
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
      await page.getByRole("button", { name: "Încă o rundă", exact: true }).click();
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
      const created = page.waitForResponse((response) => response.request().method() === "POST" &&
        new URL(response.url()).pathname === `/api/wordgames/${game.key}/games`);
      await page.reload();
      const fresh = await (await created).json();
      await expect(page.locator(game.board)).toBeVisible();
      await expect.poll(() => page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBe(fresh.game_id);
      expect(fresh.game_id).not.toBe(state.game_id);
    });

    test("can retry a failed create without leaving the game", async ({ page }) => {
      await page.route(`**/api/wordgames/${game.key}/games?*`, (route) => route.fulfill({
        status: 503, contentType: "application/json",
        body: JSON.stringify({ detail: "Serviciu indisponibil temporar." }),
      }), { times: 1 });
      await page.goto(game.path);
      await expect(page.getByText(/Serviciu indisponibil temporar\.|Nu am putut porni jocul/))
        .toBeVisible();
      await expect(page.getByRole("button", { name: "Reîncearcă", exact: true })).toBeEnabled();
      const created = page.waitForResponse((r) => r.request().method() === "POST" &&
        new URL(r.url()).pathname === `/api/wordgames/${game.key}/games`);
      await page.getByRole("button", { name: "Reîncearcă", exact: true }).click();
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

test("intrusul names the last remaining mistake in the singular", async ({ page }) => {
  const game = games.find(({ key }) => key === "intrusul");
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const intruder = solution(game).steps[0].payload.id;
  let state = initial;
  for (const tile of initial.tiles.filter(({ id }) => id !== intruder).slice(0, 2)) {
    const response = await act(page, game, { action: "guess", labels: [tile.label], payload: { id: tile.id } });
    expect(response.status()).toBe(200);
    state = await response.json();
  }
  expect(state.remaining_mistakes).toBe(1);
  expect(state.lost).toBe(false);
  await visibleProgress(page, game, state);
  await expect(page.locator(".game-frame-status").getByText("O încercare", { exact: true })).toBeVisible();
});
