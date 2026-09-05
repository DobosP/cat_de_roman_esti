import { test, expect } from "@playwright/test";
import {
  games,
  activeKey,
  gameURL,
  deterministicStarts,
  solution,
  start,
  act,
} from "./games.mjs";

const SCORES_KEY = "cat_wordgame_scores_v1";

async function createThroughBff(request, game) {
  const query = new URLSearchParams({ seed: "38", difficulty: "usor" });
  if (game.derived) query.set("starter", "1");
  const response = await request.post(
    `/api/wordgames/${game.key}/games?${query}`,
  );
  expect(response.status()).toBe(200);
  return response.json();
}

async function finishThroughBff(request, game) {
  const state = await createThroughBff(request, game);
  let terminal;
  for (const step of solution(game).steps) {
    const response = await request.post(
      `${gameURL(game, state.game_id)}/${step.action}`,
      { data: step.payload },
    );
    expect(response.status()).toBe(200);
    terminal = await response.json();
  }
  expect(terminal.won).toBe(true);
  return { ...terminal, game_id: state.game_id };
}

async function remember(page, game, gameId) {
  await page.evaluate(
    ([key, id]) => localStorage.setItem(key, id),
    [activeKey(game), gameId],
  );
}

async function timesPlayed(page, game) {
  return page.evaluate(
    ([scoresKey, gameKey]) => {
      const scores = JSON.parse(localStorage.getItem(scoresKey) || "{}");
      return scores[gameKey]?.played ?? 0;
    },
    [SCORES_KEY, game.key],
  );
}

function heldRoutes(expected) {
  let arrivals = 0;
  let markReady;
  let release;
  const ready = new Promise((resolve) => { markReady = resolve; });
  const held = new Promise((resolve) => { release = resolve; });
  return {
    ready,
    release,
    handler: async (route) => {
      arrivals += 1;
      if (arrivals === expected) markReady();
      await held;
      await route.continue();
    },
  };
}

test.describe("V74 saved-game recovery", () => {
  for (const game of games) {
    test(`${game.key} retains a transiently unavailable game and retries it`, async ({ page, request }) => {
      await deterministicStarts(page, game);
      const state = await start(page, game);
      const practiced = await act(page, game, solution(game).practice);
      expect(practiced.status()).toBe(200);
      const expected = await (await request.get(gameURL(game, state.game_id))).json();

      await page.route(`**${gameURL(game, state.game_id)}`, (route) => route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Serviciu indisponibil temporar." }),
      }), { times: 1 });
      await page.reload();

      await expect(page.getByRole("alert")).toContainText(
        "Nu am putut relua jocul salvat. Nu l-am șters.",
      );
      expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBe(state.game_id);

      // Choosing a new round must not remove the saved-round fallback if create fails.
      await page.route(`**/api/wordgames/${game.key}/games?*`, (route) => route.fulfill({
        status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Temporar indisponibil." }),
      }), { times: 1 });
      const failedCreate = page.waitForResponse((response) => response.request().method() === "POST" &&
        new URL(response.url()).pathname === `/api/wordgames/${game.key}/games`);
      await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
      expect((await failedCreate).status()).toBe(503);
      await expect(page.getByRole("button", { name: "Reîncearcă reluarea" })).toBeEnabled();
      expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(state.game_id);

      const resumed = page.waitForResponse((response) =>
        response.request().method() === "GET" &&
        new URL(response.url()).pathname === gameURL(game, state.game_id));
      await page.getByRole("button", { name: "Reîncearcă reluarea" }).click();
      expect(await (await resumed).json()).toEqual(expected);
      await expect(page.locator(game.board)).toBeVisible();
      await expect(page.getByRole("alert")).toHaveCount(0);
    });

    test(`${game.key} recovers a terminal game and scores it exactly once`, async ({ page, request }) => {
      const terminal = await finishThroughBff(request, game);
      await page.goto(game.path);
      await remember(page, game, terminal.game_id);
      await page.reload();

      await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
      await expect.poll(() => timesPlayed(page, game)).toBe(1);
      await expect.poll(() => page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBeNull();

      await page.reload();
      await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
      expect(await timesPlayed(page, game)).toBe(1);
    });
  }

  for (const staleStatus of [200, 404]) {
    test(`a stale ${staleStatus} response cannot displace another tab's game`, async ({ context, page, request }) => {
      const game = games.find(({ key }) => key === "intrusul");
      const oldGame = await createThroughBff(request, game);
      const currentGame = await createThroughBff(request, game);
      await page.goto(game.path);
      await remember(page, game, oldGame.game_id);

      let release;
      const held = new Promise((resolve) => { release = resolve; });
      let markBlocked;
      const blocked = new Promise((resolve) => { markBlocked = resolve; });
      await page.route(`**${gameURL(game, oldGame.game_id)}`, async (route) => {
        markBlocked();
        await held;
        if (staleStatus === 404) {
          await route.fulfill({
            status: 404,
            contentType: "application/json",
            body: JSON.stringify({ detail: "Joc inexistent" }),
          });
        } else {
          await route.continue();
        }
      }, { times: 1 });

      await page.reload({ waitUntil: "domcontentloaded" });
      await blocked;
      const otherTab = await context.newPage();
      await otherTab.goto("/");
      await remember(otherTab, game, currentGame.game_id);
      release();

      await expect(page.getByRole("alert")).toContainText(
        "Jocul salvat s-a schimbat în altă filă.",
      );
      expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBe(currentGame.game_id);
      await page.getByRole("button", { name: "Încarcă jocul curent" }).click();
      await expect(page.locator(game.board)).toBeVisible();
      expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBe(currentGame.game_id);
      await otherTab.close();
    });
  }

  test("an unmounted resume cannot finish a newer route's create loading", async ({ page, request }) => {
    const game = games.find(({ key }) => key === "intrusul");
    const oldGame = await createThroughBff(request, game);
    await page.goto(game.path);
    await remember(page, game, oldGame.game_id);

    let releaseOld;
    const heldOld = new Promise((resolve) => { releaseOld = resolve; });
    let markOldBlocked;
    const oldBlocked = new Promise((resolve) => { markOldBlocked = resolve; });
    await page.route(`**${gameURL(game, oldGame.game_id)}`, async (route) => {
      markOldBlocked();
      await heldOld;
      await route.continue().catch(() => {});
    }, { times: 1 });
    await page.reload({ waitUntil: "domcontentloaded" });
    await oldBlocked;

    await page.goto("/");
    await page.evaluate((key) => localStorage.removeItem(key), activeKey(game));
    await deterministicStarts(page, game);
    await page.goto(game.path);

    let releaseCreate;
    const heldCreate = new Promise((resolve) => { releaseCreate = resolve; });
    let markCreateBlocked;
    const createBlocked = new Promise((resolve) => { markCreateBlocked = resolve; });
    await page.route(`**/api/wordgames/${game.key}/games?*`, async (route) => {
      markCreateBlocked();
      await heldCreate;
      await route.continue();
    }, { times: 1 });
    await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
    await createBlocked;
    releaseOld();
    await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeDisabled();
    releaseCreate();
    await expect(page.locator(game.board)).toBeVisible();
    expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
      .not.toBe(oldGame.game_id);
  });

  test("two tabs adopt one terminal session but append its local score once", async ({ context, page, request }) => {
    const game = games.find(({ key }) => key === "contexto");
    const terminal = await finishThroughBff(request, game);
    const otherTab = await context.newPage();
    await Promise.all([page.goto(game.path), otherTab.goto(game.path)]);
    expect(await page.evaluate(() => typeof navigator.locks?.request === "function")).toBe(true);
    await remember(page, game, terminal.game_id);

    // Model the cross-process interleaving where both tabs read the same current pointer
    // before either synchronous remove reaches the shared storage area. The second remove
    // releases both effects; subsequent removals use the native implementation.
    const removeBarrier = `${activeKey(game)}_score_test_barrier`;
    for (const tab of [page, otherTab]) {
      await tab.addInitScript(({ active, barrier }) => {
        const originalRemove = Storage.prototype.removeItem;
        Storage.prototype.removeItem = function removeItem(key) {
          if (key !== active || localStorage.getItem(`${barrier}_done`) === "1") {
            return originalRemove.call(this, key);
          }
          const count = Number(localStorage.getItem(barrier) || "0") + 1;
          localStorage.setItem(barrier, String(count));
          if (count < 2) return;
          localStorage.setItem(`${barrier}_done`, "1");
          originalRemove.call(this, barrier);
          return originalRemove.call(this, key);
        };
      }, { active: activeKey(game), barrier: removeBarrier });
    }

    const gate = heldRoutes(2);
    await page.route(`**${gameURL(game, terminal.game_id)}`, gate.handler, { times: 1 });
    await otherTab.route(`**${gameURL(game, terminal.game_id)}`, gate.handler, { times: 1 });
    const reloads = [
      page.reload({ waitUntil: "domcontentloaded" }),
      otherTab.reload({ waitUntil: "domcontentloaded" }),
    ];
    await gate.ready;
    gate.release();
    await Promise.all(reloads);

    await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
    await expect(otherTab.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
    await expect.poll(() => timesPlayed(page, game)).toBe(1);
    await expect.poll(() => page.evaluate(
      ([scoresKey, gameKey]) => {
        const board = JSON.parse(localStorage.getItem(scoresKey) || "{}");
        return board[gameKey]?.recent?.length ?? 0;
      },
      [SCORES_KEY, game.key],
    )).toBe(1);

    // Reintroducing the same still-live terminal ID exercises the persisted receipt, rather
    // than relying on the normal terminal effect having removed the resume pointer.
    await remember(page, game, terminal.game_id);
    await page.reload();
    await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
    await expect.poll(() => timesPlayed(page, game)).toBe(1);
    await otherTab.close();
  });

  test("simultaneous terminal sessions from different games preserve both score rows", async ({ context, page, request }) => {
    const intrusul = games.find(({ key }) => key === "intrusul");
    const perechi = games.find(({ key }) => key === "perechi");
    const [intrusulTerminal, perechiTerminal] = await Promise.all([
      finishThroughBff(request, intrusul),
      finishThroughBff(request, perechi),
    ]);
    const otherTab = await context.newPage();
    await Promise.all([page.goto("/"), otherTab.goto("/")]);
    await remember(page, intrusul, intrusulTerminal.game_id);
    await remember(page, perechi, perechiTerminal.game_id);

    const gate = heldRoutes(2);
    await page.route(`**${gameURL(intrusul, intrusulTerminal.game_id)}`, gate.handler, { times: 1 });
    await otherTab.route(`**${gameURL(perechi, perechiTerminal.game_id)}`, gate.handler, { times: 1 });
    const navigations = [
      page.goto(intrusul.path, { waitUntil: "domcontentloaded" }),
      otherTab.goto(perechi.path, { waitUntil: "domcontentloaded" }),
    ];
    await gate.ready;
    gate.release();
    await Promise.all(navigations);

    await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
    await expect(otherTab.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
    await expect.poll(async () => [
      await timesPlayed(page, intrusul),
      await timesPlayed(page, perechi),
    ]).toEqual([1, 1]);
    await otherTab.close();
  });
});
