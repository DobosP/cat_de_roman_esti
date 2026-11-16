import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, solution, start, act } from "./games.mjs";

// The retained-frame witnesses use actual motion in both browser projects.
test.use({ reducedMotion: "no-preference" });

const SCORE_KEY = "cat_wordgame_scores_v1";
const resultButton = (page) => page.getByRole("button", { name: "Copiază rezultatul", exact: true });
const saved = (page, game) => page.evaluate((key) => localStorage.getItem(key), activeKey(game));
const scores = (page) => page.evaluate((key) => JSON.parse(localStorage.getItem(key) || "{}"), SCORE_KEY);
const exit = (page) => page.locator(".game-frame-band").getByRole("button", { name: "Înapoi la jocuri", exact: true });
const createPath = (game) => `/api/wordgames/${game.key}/games`;
const created = (page, game) => page.waitForResponse((response) =>
  response.request().method() === "POST" && new URL(response.url()).pathname === createPath(game));

async function fixture(id, suite, info, operation) {
  const assertions = [];
  const check = async (assertionId, assertion) => {
    if (assertions.some((item) => item.id === assertionId)) throw new Error("Duplicate assertion ID");
    await assertion();
    assertions.push({ id: assertionId, status: "pass", executed: true });
  };
  await operation(check);
  await info.attach("executed-redesign-assertions", {
    body: Buffer.from(JSON.stringify({ id, suite, executed: true, assertions })),
    contentType: "application/json",
  });
}

function traffic(page, game, id) {
  const counts = { creates: 0, mutations: 0, reads: 0, scores: 0 };
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (request.method() === "POST" && path === createPath(game)) counts.creates++;
    if (request.method() === "POST" && path.startsWith(`${gameURL(game, id)}/`)) counts.mutations++;
    if (request.method() === "GET" && path === gameURL(game, id)) counts.reads++;
    if (request.method() === "POST" && path === "/api/me/scores") counts.scores++;
  });
  return counts;
}

async function hold(page, url) {
  let enter, release;
  const requested = new Promise((resolve) => { enter = resolve; });
  const waiting = new Promise((resolve) => { release = resolve; });
  await page.route(`**${url}`, async (route) => {
    const response = await route.fetch();
    enter();
    await waiting;
    await route.fulfill({ response });
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
  // Wait for the enter transition before testing the retained exit.
  await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
  return { initial, step: steps.at(-1) };
}

async function leavingSnapshot(page, game) {
  return page.evaluate(async ([selector, key]) => {
    const root = document.querySelector(selector)?.closest(".screen");
    if (!root) throw new Error("Expected a mounted game screen");
    window.__redesignExit = { terminalAppearances: 0 };
    const observer = new MutationObserver((records) => {
      for (const record of records) for (const node of record.addedNodes) {
        if (node instanceof globalThis.Element && (node.matches(".game-result") || node.querySelector(".game-result"))) {
          window.__redesignExit.terminalAppearances++;
        }
      }
    });
    observer.observe(root, { childList: true, subtree: true });
    root.querySelector('.game-frame-band button[aria-label="Înapoi la jocuri"]').click();
    // The kit retains this frame for its motion exit. Wait for that actual
    // ownership transition before sampling and probing its stale controls.
    for (let frame = 0; frame < 24; frame++) {
      await new Promise((resolve) => requestAnimationFrame(resolve));
      if (!root.isConnected || root.closest('.roedu-presence[data-state="exiting"]')) break;
    }
    const board = root.querySelector(selector);
    const buttons = [...root.querySelectorAll(`${selector} button, .hint-bar button, .${key}-sync-recovery button`)];
    const selected = () => root.querySelectorAll(".perechi-tile[aria-pressed='true']").length;
    const snapshot = { mounted: Boolean(board?.isConnected), inert: root.hasAttribute("inert"),
      buttons: buttons.length, disabled: buttons.every((button) => button.disabled),
      opacity: getComputedStyle(root).opacity, selected: selected() };
    for (const button of buttons) {
      button.click();
      button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    }
    return { ...snapshot, selectedAfter: selected() };
  }, [game.board, game.key]);
}

async function assertSingleRecord(check, page, game, id, enter, prefix = "resume") {
  const response = created(page, game);
  await enter();
  const reply = await response;
  expect(reply.status()).toBe(200);
  const next = await reply.json();
  await check(prefix + ".fresh-free-board", async () => {
    expect(next.game_id).not.toBe(id);
    expect(next.daily).toBeUndefined();
    await expect(page.locator(game.board)).toBeVisible();
    await expect(page.locator(".game-frame-mode")).toHaveText("Rundă liberă");
    await expect(resultButton(page)).toHaveCount(0);
  });
  await check(prefix + ".one-local-row", async () => {
    await expect.poll(async () => (await scores(page))[game.key]?.played).toBe(1);
    const rows = (await scores(page))[game.key].recent;
    expect(rows).toHaveLength(1);
    expect(rows[0].steps).toBe(0);
  });
  await check(prefix + ".one-completion-receipt", async () => {
    expect((await scores(page))._completionReceipts.games[game.key].filter((item) => item.id === id)).toHaveLength(1);
  });
  await check(prefix + ".saved-pointer-replaced", async () => {
    await expect.poll(() => saved(page, game)).toBe(next.game_id);
  });
}

for (const game of games.filter((entry) => entry.derived)) {
  test.describe(game.key, () => {
    test.beforeEach(async ({ page }) => { await deterministicStarts(page, game); });

    test(`redesign-${game.key}-one-tap-single-flight`, async ({ page }, info) => {
      await fixture(info.title, "behavior", info, async (check) => {
        let creates = 0;
        page.on("request", (request) => {
          if (request.method() === "POST" && new URL(request.url()).pathname === createPath(game)) creates++;
        });
        const held = await hold(page, createPath(game) + "?*");
        const response = created(page, game);
        await page.goto(game.path);
        await held.requested;
        try {
          await check("entry.frame-busy-and-board-absent", async () => {
            await expect(page.locator(".game-frame")).toHaveAttribute("aria-busy", "true");
            await expect(page.locator(game.board)).toHaveCount(0);
          });
          await check("entry.all-navigation-controls-disabled", async () => {
            const controls = await page.locator(".game-frame-band button").all();
            expect(controls).toHaveLength(2);
            for (const button of controls) await expect(button).toBeDisabled();
          });
          await check("entry.no-second-create-or-saved-pointer", async () => {
            await page.locator(".game-frame-band").evaluate((root) => {
              for (const button of root.querySelectorAll("button")) button.click();
              // A visibility signal while the already-visible entry is pending
              // must not start a second valid POST.
              document.dispatchEvent(new Event("visibilitychange"));
            });
            expect(creates).toBe(1);
            expect(await saved(page, game)).toBeNull();
          });
        } finally { held.release(); }
        const reply = await response;
        expect(reply.status()).toBe(200);
        const state = await reply.json();
        await check("entry.authoritative-board-and-pointer", async () => {
          await expect(page.locator(game.board)).toBeVisible();
          await expect.poll(() => saved(page, game)).toBe(state.game_id);
          expect(state.steps).toBe(0);
          expect(state.perfect).toBe(false);
          expect(state.score).toBeUndefined();
          expect(state.solution).toBeUndefined();
        });
      });
    });

    test(`redesign-${game.key}-leaving-actions`, async ({ page }, info) => {
      await fixture(info.title, "presence", info, async (check) => {
        const initial = await start(page, game);
        await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
        const counts = traffic(page, game, initial.game_id);
        const snapshot = await leavingSnapshot(page, game);
        await check("exit.mounted-controls-locked", () => {
          expect(snapshot.mounted).toBe(true);
          expect(snapshot.inert).toBe(true);
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
      test(`redesign-${game.key}-leaving-${control}`, async ({ page, request }, info) => {
        await fixture(info.title, "presence", info, async (check) => {
          const initial = await start(page, game);
          const steps = solution(game).steps;
          if (control === "earned-hint") {
            const wrong = game.key === "intrusul"
              ? initial.tiles.filter((tile) => tile.id !== steps[0].payload.id).slice(0, 1).map((tile) => ({ id: tile.id }))
              : [{ ids: [steps[0].payload.ids[0], steps[1].payload.ids[0]] }, { ids: [steps[0].payload.ids[1], steps[1].payload.ids[1]] }];
            for (const payload of wrong) expect((await request.post(`${gameURL(game, initial.game_id)}/${steps[0].action}`, { data: payload })).status()).toBe(200);
            await page.reload();
            await expect(page.getByRole("button", { name: "Indiciu", exact: true })).toBeEnabled();
          } else {
            await page.route(`**${gameURL(game, initial.game_id)}/${steps[0].action}`, (route) => route.fulfill({ status: 503, json: {} }), { times: 1 });
            await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({ status: 503, json: {} }), { times: 1 });
            await act(page, game, steps[0]);
            await expect(page.getByRole("button", { name: "Verifică jocul", exact: true })).toBeEnabled();
          }
          await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
          const counts = traffic(page, game, initial.game_id);
          const snapshot = await leavingSnapshot(page, game);
          await check("exit.earned-control-is-mounted-and-disabled", () => {
            expect(snapshot.mounted).toBe(true);
            expect(snapshot.inert).toBe(true);
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
      test(`redesign-${game.key}-held-winning-${phase}`, async ({ page, request }, info) => {
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
              const snapshot = await leavingSnapshot(page, game);
              await check("exit.reply-released-while-mounted-and-locked", () => {
                expect(snapshot.mounted).toBe(true);
                expect(snapshot.inert).toBe(true);
                expect(snapshot.disabled).toBe(true);
                expect(Number(snapshot.opacity)).toBeLessThan(1);
              });
            }
          } finally { held.release(); }
          await performed;
          if (phase !== "unmounted") await check("stale.no-transient-terminal-adoption-during-exit", async () => {
            expect(await page.evaluate(() => window.__redesignExit.terminalAppearances)).toBe(0);
          });
          await check("stale.no-record-no-result-no-extra-request", async () => {
            await expect(page.locator(game.board)).toHaveCount(0);
            await expect(resultButton(page)).toHaveCount(0);
            expect((await scores(page))[game.key]?.played ?? 0).toBe(0);
            expect(await saved(page, game)).toBe(initial.game_id);
            expect(counts).toEqual({ creates: 0, mutations: 1, reads: phase === "read" ? 1 : 0, scores: 0 });
            expect((await (await request.get(gameURL(game, initial.game_id))).json()).won).toBe(true);
          });
          await assertSingleRecord(check, page, game, initial.game_id, () => page.goto(game.path));
          await page.evaluate(([key, id]) => localStorage.setItem(key, id), [activeKey(game), initial.game_id]);
          await assertSingleRecord(check, page, game, initial.game_id, () => page.reload(), "resume-repeat");
          await check("resume.no-account-upload", () => { expect(counts.scores).toBe(0); });
        });
      });
    }

    test(`redesign-${game.key}-private-upload-once-after-resume`, async ({ page, request }, info) => {
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
        const lobby = page.locator(`.games-grid a[href="${game.path}"]`);
        await assertSingleRecord(check, page, game, initial.game_id, () => lobby.click());
        await check("upload.exactly-one-earned-row", async () => {
          await expect.poll(() => uploads.length).toBe(1);
          expect(uploads[0].entries).toHaveLength(1);
          expect(uploads[0].entries[0].game).toBe(game.key);
          expect(uploads[0].entries[0].score).toBe((await scores(page))[game.key].recent[0].score);
        });
        await exit(page).click();
        await expect(lobby).toBeVisible();
        await expect(resultButton(page)).toHaveCount(0);
        await page.evaluate(([key, id]) => localStorage.setItem(key, id), [activeKey(game), initial.game_id]);
        await assertSingleRecord(check, page, game, initial.game_id, () => lobby.click(), "upload-repeat");
        await check("upload.repeat-resume-never-sends-second-row", () => { expect(uploads).toHaveLength(1); });
      });
    });
  });
}
