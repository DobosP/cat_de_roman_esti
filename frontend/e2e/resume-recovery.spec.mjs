import { test, expect } from "@playwright/test";
import {
  games,
  activeKey,
  gameURL,
  deterministicStarts,
  solution,
  start,
  act,
  openGameOptions,
} from "./games.mjs";

const SCORES_KEY = "cat_wordgame_scores_v1";
const SCORE_LOCK = "cat_wordgame_scores_v1_transaction";
const receiptPending = (page) => page.getByText("Se verifică runda salvată…", { exact: true });
const copyResult = (page) => page.getByRole("button", { name: "Copiază rezultatul" });

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

async function holdScoreLock(page) {
  await page.evaluate(async (name) => {
    let release;
    const blocked = new Promise((resolve) => { release = resolve; });
    globalThis.__releaseScoreLock = release;
    await new Promise((acquired) => {
      void navigator.locks.request(name, async () => {
        acquired();
        await blocked;
      });
    });
  }, SCORE_LOCK);
}

async function releaseScoreLock(page) {
  await page.evaluate(() => globalThis.__releaseScoreLock());
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
      await page.getByRole("button", { name: "Începe o rundă nouă", exact: true }).click();
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

    test(`${game.key} records a terminal saved receipt once and opens a playable round`, async ({ page, request }) => {
      const terminal = await finishThroughBff(request, game);
      await deterministicStarts(page, game);
      await page.goto("/");
      await remember(page, game, terminal.game_id);
      await page.goto(game.path);

      await expect(page.locator(game.board)).toBeVisible();
      await expect(copyResult(page)).toHaveCount(0);
      await expect.poll(() => timesPlayed(page, game)).toBe(1);
      const saved = await page.evaluate((key) => localStorage.getItem(key), activeKey(game));
      expect(saved).not.toBeNull();
      expect(saved).not.toBe(terminal.game_id);

      await page.reload();
      await expect(page.locator(game.board)).toBeVisible();
      expect(await timesPlayed(page, game)).toBe(1);
    });
  }

  test("a queued terminal score keeps every saved game recoverable until its write finishes", async ({ context, request }) => {
    const holder = await context.newPage();
    await holder.goto("/");
    expect(await holder.evaluate(() => typeof navigator.locks?.request === "function")).toBe(true);

    for (const game of games) {
      const terminal = await finishThroughBff(request, game);
      let player = await context.newPage();
      await player.goto("/");
      await remember(player, game, terminal.game_id);
      await holdScoreLock(holder);

      await player.goto(game.path);
      await expect(receiptPending(player)).toBeVisible();
      expect(await player.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBe(terminal.game_id);

      await openGameOptions(player, game);
      await expect(player.getByRole("dialog")).toBeVisible();
      await player.keyboard.press("Escape");
      await player.getByRole("button", { name: "Înapoi la jocuri" }).last().click();
      await expect(player).toHaveURL(/\/$/);
      expect(await player.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBe(terminal.game_id);
      await player.goto(game.path);
      expect(await player.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBe(terminal.game_id);
      await player.reload();
      await expect(receiptPending(player)).toBeVisible();
      expect(await player.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBe(terminal.game_id);

      await player.close();
      player = await context.newPage();
      await player.goto(game.path);
      await expect(receiptPending(player)).toBeVisible();
      expect(await player.evaluate((key) => localStorage.getItem(key), activeKey(game)))
        .toBe(terminal.game_id);

      // One witness lets another tab install an unfinished daily while the
      // recovered receipt is still queued. The surviving pointer must win.
      let newerId;
      const creates = [];
      if (game.key === "intrusul") {
        const day = await player.evaluate(() => {
          const now = new Date();
          return [now.getFullYear(), now.getMonth() + 1, now.getDate()]
            .map((part) => String(part).padStart(2, "0")).join("-");
        });
        const newer = await request.post(`/api/wordgames/${game.key}/games?daily=${day}`);
        expect(newer.status()).toBe(200);
        newerId = (await newer.json()).game_id;
        await remember(holder, game, newerId);
        player.on("request", (incoming) => {
          if (incoming.method() === "POST" && new URL(incoming.url()).pathname === `/api/wordgames/${game.key}/games`) creates.push(incoming.url());
        });
      }
      await releaseScoreLock(holder);
      await expect.poll(() => timesPlayed(player, game)).toBe(1);
      await expect(player.locator(game.board)).toBeVisible();
      const saved = await player.evaluate((key) => localStorage.getItem(key), activeKey(game));
      expect(saved).not.toBe(terminal.game_id);
      if (newerId) {
        expect(saved).toBe(newerId);
        expect(creates).toEqual([]);
      }
      await player.close();
    }
    await holder.close();
  });

  for (const staleStatus of [200, 404]) {
    test(`a stale ${staleStatus} response cannot displace another tab's game`, async ({ context, page, request }) => {
      const game = games.find(({ key }) => key === "intrusul");
      const oldGame = await createThroughBff(request, game);
      const currentGame = await createThroughBff(request, game);
      await deterministicStarts(page, game);
      await page.goto("/");
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

      await page.goto(game.path, { waitUntil: "domcontentloaded" });
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
    await deterministicStarts(page, game);
    await page.goto("/");
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
    await page.goto(game.path, { waitUntil: "domcontentloaded" });
    await oldBlocked;

    await page.goto("/");
    await page.evaluate((key) => localStorage.removeItem(key), activeKey(game));
    let releaseCreate;
    const heldCreate = new Promise((resolve) => { releaseCreate = resolve; });
    let markCreateBlocked;
    const createBlocked = new Promise((resolve) => { markCreateBlocked = resolve; });
    await page.route(`**/api/wordgames/${game.key}/games?*`, async (route) => {
      markCreateBlocked();
      await heldCreate;
      await route.continue();
    }, { times: 1 });
    await page.goto(game.path, { waitUntil: "domcontentloaded" });
    await createBlocked;
    releaseOld();
    await expect(page.getByRole("main")).toHaveAttribute("aria-busy", "true");
    releaseCreate();
    await expect(page.locator(game.board)).toBeVisible();
    expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
      .not.toBe(oldGame.game_id);
  });

  test("two tabs recover one terminal receipt and append its local score once", async ({ context, page, request }) => {
    const game = games.find(({ key }) => key === "contexto");
    const terminal = await finishThroughBff(request, game);
    const otherTab = await context.newPage();
    await Promise.all([page.goto("/"), otherTab.goto("/")]);
    expect(await page.evaluate(() => typeof navigator.locks?.request === "function")).toBe(true);
    await remember(page, game, terminal.game_id);

    // Model the cross-process interleaving where both tabs read the same current pointer
    // before either synchronous remove reaches the shared storage area. The second remove
    // releases both effects; subsequent removals use the native implementation.
    const removeBarrier = `${activeKey(game)}_score_test_barrier`;
    for (const tab of [page, otherTab]) {
      await tab.addInitScript(({ active, barrier }) => {
        const originalRemove = Object.getOwnPropertyDescriptor(Storage.prototype, "removeItem")?.value;
        if (typeof originalRemove !== "function") throw new Error("Native Storage.removeItem data method required");
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
      page.goto(game.path, { waitUntil: "domcontentloaded" }),
      otherTab.goto(game.path, { waitUntil: "domcontentloaded" }),
    ];
    await gate.ready;
    gate.release();
    await Promise.all(reloads);

    await expect(copyResult(page)).toHaveCount(0);
    await expect(copyResult(otherTab)).toHaveCount(0);
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
    await otherTab.bringToFront();
    await remember(otherTab, game, terminal.game_id);
    await otherTab.reload();
    await expect(otherTab.locator(game.board)).toBeVisible();
    await expect.poll(() => timesPlayed(page, game)).toBe(1);
    await otherTab.close();
  });

  test("an older create response cannot replace a newer tab's saved round", async ({ context, page, request }) => {
    const game = games.find(({ key }) => key === "intrusul");
    await deterministicStarts(page, game);
    const gate = heldRoutes(1);
    await page.route((url) => url.pathname === `/api/wordgames/${game.key}/games`, gate.handler, { times: 1 });
    await page.goto(game.path);
    await gate.ready;
    const newer = await createThroughBff(request, game);
    const otherTab = await context.newPage();
    await otherTab.goto("/");
    await remember(otherTab, game, newer.game_id);
    const resumed = page.waitForResponse((response) => response.request().method() === "GET" &&
      new URL(response.url()).pathname === gameURL(game, newer.game_id));
    await page.bringToFront();
    gate.release();
    expect((await resumed).status()).toBe(200);
    await expect(page.locator(game.board)).toBeVisible();
    expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(newer.game_id);
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

    await expect(copyResult(page)).toHaveCount(0);
    await expect(copyResult(otherTab)).toHaveCount(0);
    await expect.poll(async () => [
      await timesPlayed(page, intrusul),
      await timesPlayed(page, perechi),
    ]).toEqual([1, 1]);
    await otherTab.close();
  });
});
