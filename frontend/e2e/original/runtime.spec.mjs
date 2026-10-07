import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, solution, start, act } from "../games.mjs";

const SCORE_KEY = "cat_wordgame_scores_v1";
const resultButton = (page) => page.getByRole("button", { name: "Copiază rezultatul", exact: true });
const saved = (page, game) => page.evaluate((key) => localStorage.getItem(key), activeKey(game));
const scores = (page) => page.evaluate((key) => JSON.parse(localStorage.getItem(key) || "{}"), SCORE_KEY);
const exit = (page) => page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true });

async function fixture(id, suite, info, operation) {
  const assertions = [];
  const check = async (assertionId, assertion) => {
    if (assertions.some((item) => item.id === assertionId)) throw new Error("Duplicate assertion ID");
    await assertion();
    assertions.push({ id: assertionId, status: "pass", executed: true });
  };
  await operation(check);
  await info.attach("executed-original-assertions", {
    body: Buffer.from(JSON.stringify({ id, suite, executed: true, assertions })),
    contentType: "application/json",
  });
}

function traffic(page, game, id) {
  const counts = { creates: 0, mutations: 0, reads: 0, scores: 0 };
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (request.method() === "POST" && path === `/api/wordgames/${game.key}/games`) counts.creates++;
    if (request.method() === "POST" && path.startsWith(`${gameURL(game, id)}/`)) counts.mutations++;
    if (request.method() === "GET" && path === gameURL(game, id)) counts.reads++;
    if (request.method() === "POST" && path === "/api/me/scores") counts.scores++;
  });
  return counts;
}

async function hold(page, url, { fail = false } = {}) {
  let enter, release;
  const requested = new Promise((resolve) => { enter = resolve; });
  const waiting = new Promise((resolve) => { release = resolve; });
  await page.route(`**${url}`, async (route) => {
    const response = await route.fetch();
    enter();
    await waiting;
    if (fail) await route.fulfill({ status: 503, json: {} });
    else await route.fulfill({ response });
  }, { times: 1 });
  return { requested, release };
}

async function readyToWin(page, request, game) {
  const initial = await start(page, game);
  const steps = solution(game).steps;
  for (const step of steps.slice(0, -1)) {
    expect((await request.post(`${gameURL(game, initial.game_id)}/${step.action}`, { data: step.payload })).status()).toBe(200);
  }
  if (steps.length > 1) {
    await page.reload();
    await expect(page.locator(game.board)).toBeVisible();
  }
  // Wait for the original enter transition before testing its exit.
  await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
  return { initial, step: steps.at(-1) };
}

async function leavingSnapshot(page, game, clickExit = false) {
  return page.evaluate(async ([selector, leave]) => {
    const root = document.querySelector(selector)?.closest(".screen");
    window.__originalExit = { terminalAppearances: 0 };
    const observer = new MutationObserver((records) => {
      for (const record of records) for (const node of record.addedNodes) {
        if (node.nodeType === Node.ELEMENT_NODE && (node.textContent || "").includes("Copiază rezultatul")) window.__originalExit.terminalAppearances++;
      }
    });
    if (root) observer.observe(root, { childList: true, subtree: true });
    if (leave) document.querySelector('button[aria-label="Ieși la lista de jocuri"]').click();
    // Presence's ownership update precedes Framer's first opacity write. Observe
    // a real in-progress exit frame, rather than guessing which rAF starts it.
    for (let frame = 0; frame < 24; frame++) {
      await new Promise((resolve) => requestAnimationFrame(resolve));
      if (!root?.isConnected || Number(getComputedStyle(root).opacity) < 1) break;
    }
    const board = document.querySelector(selector);
    const screen = board?.closest(".screen");
    const gameKey = selector.slice(1).split("-")[0];
    const buttons = [...document.querySelectorAll(`${selector} button, .${gameKey}-actions button, .${gameKey}-sync-recovery button`)];
    const selected = document.querySelectorAll(".perechi-tile--selected").length;
    const snapshot = { mounted: Boolean(board?.isConnected), buttons: buttons.length,
      disabled: buttons.every((button) => button.disabled), opacity: screen ? getComputedStyle(screen).opacity : null, selected };
    for (const button of buttons) {
      button.click();
      button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    }
    return { ...snapshot, selectedAfter: document.querySelectorAll(".perechi-tile--selected").length };
  }, [game.board, clickExit]);
}

async function assertSingleRecord(check, page, game, id) {
  await check("resume.result-visible", async () => { await expect(resultButton(page)).toBeVisible(); });
  await check("resume.one-local-row", async () => {
    await expect.poll(async () => (await scores(page))[game.key]?.played).toBe(1);
    expect((await scores(page))[game.key].recent).toHaveLength(1);
  });
  await check("resume.one-completion-receipt", async () => {
    expect((await scores(page))._completionReceipts.games[game.key].filter((item) => item.id === id)).toHaveLength(1);
  });
  await check("resume.saved-pointer-cleared", async () => { await expect.poll(() => saved(page, game)).toBeNull(); });
}

for (const game of games.filter((game) => game.derived)) {
  test.beforeEach(async ({ page }) => { await deterministicStarts(page, game); });

  test(`original-${game.key}-intro-single-flight`, async ({ page }, info) => {
    await fixture(info.title, "behavior", info, async (check) => {
      await page.goto(game.path);
      let creates = 0;
      page.on("request", (request) => { if (request.method() === "POST" && new URL(request.url()).pathname === `/api/wordgames/${game.key}/games`) creates++; });
      const held = await hold(page, `/api/wordgames/${game.key}/games?*`);
      const response = page.waitForResponse((response) => response.request().method() === "POST" && new URL(response.url()).pathname === `/api/wordgames/${game.key}/games`);
      await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
      await held.requested;
      try {
        await check("intro.inert-and-busy", async () => {
          await expect(page.locator(".game-intro")).toHaveAttribute("inert", "");
          await expect(page.locator(".game-intro")).toHaveAttribute("aria-busy", "true");
        });
        await check("intro.all-actions-disabled", async () => {
          for (const button of await page.locator(".game-intro-actions button, .game-shell-header button").all()) await expect(button).toBeDisabled();
        });
        await check("intro.no-second-create-or-saved-pointer", async () => {
          await page.locator(".game-intro-actions").evaluate((root) => { for (const button of root.querySelectorAll("button")) button.click(); });
          expect(creates).toBe(1);
          expect(await saved(page, game)).toBeNull();
        });
      } finally { held.release(); }
      const state = await (await response).json();
      await check("intro.authoritative-board-and-pointer", async () => {
        await expect(page.locator(game.board)).toBeVisible();
        expect(await saved(page, game)).toBe(state.game_id);
        expect(state.score).toBeUndefined();
        expect(state.solution).toBeUndefined();
      });
    });
  });

  test(`original-${game.key}-leaving-actions`, async ({ page }, info) => {
    await fixture(info.title, "presence", info, async (check) => {
      const initial = await start(page, game);
      await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
      const counts = traffic(page, game, initial.game_id);
      const snapshot = await leavingSnapshot(page, game, true);
      await check("exit.mounted-controls-locked", () => {
        expect(snapshot.mounted).toBe(true);
        expect(snapshot.buttons).toBeGreaterThan(0);
        expect(snapshot.disabled).toBe(true);
        expect(Number(snapshot.opacity)).toBeLessThan(1);
        expect(snapshot.selectedAfter).toBe(snapshot.selected);
      });
      await check("exit.no-requests-or-score-writes", async () => {
        await expect(page.locator(game.board)).toHaveCount(0);
        expect(counts).toEqual({ creates: 0, mutations: 0, reads: 0, scores: 0 });
        expect((await scores(page))[game.key]?.played ?? 0).toBe(0);
        expect(await saved(page, game)).toBe(initial.game_id);
      });
    });
  });

  for (const control of ["earned-hint", "recovery-retry"]) {
    test(`original-${game.key}-leaving-${control}`, async ({ page, request }, info) => {
      await fixture(info.title, "presence", info, async (check) => {
        const initial = await start(page, game);
        const steps = solution(game).steps;
        if (control === "earned-hint") {
          const wrong = game.key === "intrusul"
            ? initial.tiles.filter((tile) => tile.id !== steps[0].payload.id).slice(0, 1).map((tile) => ({ id: tile.id }))
            : [{ ids: [steps[0].payload.ids[0], steps[1].payload.ids[0]] }, { ids: [steps[0].payload.ids[1], steps[1].payload.ids[1]] }];
          for (const payload of wrong) expect((await request.post(`${gameURL(game, initial.game_id)}/${steps[0].action}`, { data: payload })).status()).toBe(200);
          await page.reload();
          await expect(page.getByRole("button", { name: game.key === "intrusul" ? /^💡 Arată indiciul/ : /^💡 Arată o pereche/ })).toBeEnabled();
        } else {
          await page.route(`**${gameURL(game, initial.game_id)}/${steps[0].action}`, (route) => route.fulfill({ status: 503, json: {} }), { times: 1 });
          await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({ status: 503, json: {} }), { times: 1 });
          await act(page, game, steps[0]);
          await expect(page.getByRole("button", { name: "Verifică jocul", exact: true })).toBeEnabled();
        }
        await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
        const counts = traffic(page, game, initial.game_id);
        const snapshot = await leavingSnapshot(page, game, true);
        await check("exit.earned-control-is-mounted-and-disabled", () => {
          expect(snapshot.mounted).toBe(true);
          expect(snapshot.disabled).toBe(true);
          expect(snapshot.buttons).toBeGreaterThan(0);
          expect(Number(snapshot.opacity)).toBeLessThan(1);
        });
        await check("exit.earned-control-causes-no-mutation-read-record", async () => {
          await expect(page.locator(game.board)).toHaveCount(0);
          expect(counts).toEqual({ creates: 0, mutations: 0, reads: 0, scores: 0 });
          expect((await scores(page))[game.key]?.played ?? 0).toBe(0);
          expect(await saved(page, game)).toBe(initial.game_id);
        });
      });
    });
  }

  for (const phase of ["mutation", "read", "unmounted"]) {
    test(`original-${game.key}-held-winning-${phase}`, async ({ page, request }, info) => {
      await fixture(info.title, "presence", info, async (check) => {
        const { initial, step } = await readyToWin(page, request, game);
        const counts = traffic(page, game, initial.game_id);
        if (phase === "read") {
          await page.route(`**${gameURL(game, initial.game_id)}/${step.action}`, async (route) => {
            expect((await route.fetch()).status()).toBe(200);
            await route.fulfill({ status: 503, json: {} });
          }, { times: 1 });
        }
        const held = await hold(page, `${gameURL(game, initial.game_id)}${phase === "read" ? "" : `/${step.action}`}`);
        const performed = act(page, game, step);
        await held.requested;
        try {
          if (phase === "unmounted") { await exit(page).click(); await expect(page.locator(game.board)).toHaveCount(0); }
          else {
            const snapshot = await leavingSnapshot(page, game, true);
            await check("exit.reply-released-while-mounted-and-locked", () => {
              expect(snapshot.mounted).toBe(true);
              expect(snapshot.disabled).toBe(true);
              expect(Number(snapshot.opacity)).toBeLessThan(1);
            });
          }
        } finally { held.release(); }
        await performed;
        if (phase !== "unmounted") await check("stale.no-transient-terminal-adoption-during-exit", async () => {
          expect(await page.evaluate(() => window.__originalExit.terminalAppearances)).toBe(0);
        });
        await check("stale.no-record-no-result-no-extra-request", async () => {
          await expect(page.locator(game.board)).toHaveCount(0);
          await expect(resultButton(page)).toHaveCount(0);
          expect((await scores(page))[game.key]?.played ?? 0).toBe(0);
          expect(await saved(page, game)).toBe(initial.game_id);
          expect(counts).toEqual({ creates: 0, mutations: 1, reads: phase === "read" ? 1 : 0, scores: 0 });
          expect((await (await request.get(gameURL(game, initial.game_id))).json()).won).toBe(true);
        });
        await page.goto(game.path);
        await assertSingleRecord(check, page, game, initial.game_id);
        await page.evaluate(([key, id]) => localStorage.setItem(key, id), [activeKey(game), initial.game_id]);
        await page.reload();
        await check("resume.repeat-does-not-record-again", async () => {
          await expect(resultButton(page)).toBeVisible();
          await expect.poll(() => saved(page, game)).toBeNull();
          const store = await scores(page);
          expect(store[game.key].played).toBe(1);
          expect(store[game.key].recent).toHaveLength(1);
          expect(store._completionReceipts.games[game.key].filter((item) => item.id === initial.game_id)).toHaveLength(1);
          expect(counts.scores).toBe(0);
        });
      });
    });
  }

  test(`original-${game.key}-private-upload-once-after-resume`, async ({ page, request }, info) => {
    await fixture(info.title, "behavior", info, async (check) => {
      await page.route("**/api/me", (route) => route.fulfill({ json: {
        accounts_enabled: true, authenticated: true, user: {
          id: 1, email: "fixture@example.invalid", name: "Fixture", avatar: "", ranking_name: "Fixture", display_name: "Fixture",
          show_on_ranking: false, consent_completed: true, can_save_progress: true, is_minor: false, parental_consent_required: false,
        },
      } }));
      const uploads = [];
      await page.route("**/api/me/scores", async (route) => {
        uploads.push(route.request().postDataJSON());
        await route.fulfill({ json: { status: "ok" } });
      });
      const { initial, step } = await readyToWin(page, request, game);
      await expect(page.locator(".account-bar")).toBeVisible();
      const held = await hold(page, `${gameURL(game, initial.game_id)}/${step.action}`);
      const performed = act(page, game, step);
      await held.requested;
      await exit(page).click();
      held.release();
      await performed;
      await expect(page.locator(game.board)).toHaveCount(0);
      await check("upload.stale-reply-sends-nothing", () => { expect(uploads).toHaveLength(0); });
      const lobby = page.getByRole("button", { name: new RegExp(`^Joacă ${game.key === "intrusul" ? "Intrusul" : "Perechi"} —`) });
      await lobby.click();
      await assertSingleRecord(check, page, game, initial.game_id);
      await check("upload.exactly-one-earned-row", async () => {
        await expect.poll(() => uploads.length).toBe(1);
        expect(uploads[0].entries).toHaveLength(1);
        expect(uploads[0].entries[0].game).toBe(game.key);
        expect(uploads[0].entries[0].score).toBe((await scores(page))[game.key].recent[0].score);
      });
      await exit(page).click();
      await expect(resultButton(page)).toHaveCount(0);
      await page.evaluate(([key, id]) => localStorage.setItem(key, id), [activeKey(game), initial.game_id]);
      await lobby.click();
      await check("upload.repeat-resume-never-sends-second-row", async () => {
        await expect(resultButton(page)).toBeVisible();
        await expect.poll(() => saved(page, game)).toBeNull();
        expect(uploads).toHaveLength(1);
        expect((await scores(page))[game.key].played).toBe(1);
      });
    });
  });
}
