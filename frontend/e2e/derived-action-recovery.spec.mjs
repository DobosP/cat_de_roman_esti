import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, solution, start, act } from "./games.mjs";

const verify = (page) => page.getByRole("button", { name: "Verifică jocul", exact: true });
const currentGame = (page) => page.getByRole("button", { name: "Încarcă jocul curent", exact: true });
const result = (page) => page.getByRole("button", { name: "Copiază rezultatul", exact: true });
const saved = (page, game) => page.evaluate((key) => localStorage.getItem(key), activeKey(game));
const played = (page, game) => page.evaluate((key) => JSON.parse(localStorage.getItem("cat_wordgame_scores_v1") || "{}")[key]?.played ?? 0, game.key);
const server = async (request, game, id) => (await request.get(gameURL(game, id))).json();
const hint = (page, game) => page.getByRole("button", { name: game.key === "intrusul" ? "💡 Arată indiciul" : "💡 Arată o pereche", exact: true });
const cue = (page, game) => page.locator(game.key === "intrusul" ? ".intrusul-clue" : ".perechi-hint");

function traffic(page, game, id) {
  const counts = { reads: 0, mutations: 0 };
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (request.method() === "GET" && path === gameURL(game, id)) counts.reads += 1;
    if (request.method() === "POST" && path.startsWith(`${gameURL(game, id)}/`)) counts.mutations += 1;
  });
  return counts;
}

function wrongSteps(game, initial) {
  const steps = solution(game).steps;
  if (game.key === "intrusul") return initial.tiles.filter((tile) => tile.id !== steps[0].payload.id)
    .map((tile) => ({ action: "guess", payload: { id: tile.id }, labels: [tile.label] }));
  return [...steps[0].payload.ids.flatMap((a) => steps[1].payload.ids.map((b) => [a, b])),
    [steps[0].payload.ids[0], steps[2].payload.ids[0]], [steps[0].payload.ids[1], steps[2].payload.ids[0]]]
    .map((ids) => ({ action: "match", payload: { ids }, labels: ids.map((id) => initial.tiles.find((tile) => tile.id === id).label) }));
}

async function prepare(page, request, game, mode = "practice") {
  const initial = await start(page, game);
  const steps = solution(game).steps;
  const wrong = wrongSteps(game, initial);
  let setup = [];
  let step = solution(game).practice;
  if (mode === "match") step = steps[0];
  if (mode === "hint") setup = wrong.slice(0, game.key === "intrusul" ? 1 : 2);
  if (mode === "win") { setup = steps.slice(0, -1); step = steps.at(-1); }
  if (mode === "loss") { setup = wrong.slice(0, initial.remaining_mistakes - 1); step = wrong[initial.remaining_mistakes - 1]; }
  for (const move of setup) expect((await request.post(`${gameURL(game, initial.game_id)}/${move.action}`, { data: move.payload })).status()).toBe(200);
  if (setup.length) { await page.reload(); await expect(page.locator(game.board)).toBeVisible(); }
  const action = mode === "hint" ? "hint" : step.action;
  const perform = async (options = {}) => {
    if (mode !== "hint") return act(page, game, step, options);
    const response = page.waitForResponse((response) => response.request().method() === "POST" && new URL(response.url()).pathname === `${gameURL(game, initial.game_id)}/hint`);
    await hint(page, game).click();
    return response;
  };
  return { initial, step, action, perform };
}

async function loseResponse(page, game, id, action, commit = true) {
  let body;
  await page.route(`**${gameURL(game, id)}/${action}`, async (route) => {
    if (commit) {
      const response = await route.fetch();
      expect(response.status()).toBe(200);
      body = await response.json();
    }
    await route.fulfill({ status: 503, json: {} });
  }, { times: 1 });
  return () => body;
}

async function holdResponse(page, game, id, action = "", missing = false) {
  let entered;
  let release;
  const requested = new Promise((resolve) => { entered = resolve; });
  const held = new Promise((resolve) => { release = resolve; });
  await page.route(`**${gameURL(game, id)}${action ? `/${action}` : ""}`, async (route) => {
    const response = await route.fetch();
    entered();
    await held;
    if (missing) await route.fulfill({ status: 404, json: {} });
    else await route.fulfill({ response });
  }, { times: 1 });
  return { requested, release };
}

async function replaceSaved(context, request, game, remove = false) {
  const fresh = remove ? null : await (await request.post(`/api/wordgames/${game.key}/games?seed=39&starter=1`)).json();
  const tab = await context.newPage();
  await tab.goto("/");
  await tab.evaluate(([key, id]) => id === null ? localStorage.removeItem(key) : localStorage.setItem(key, id), [activeKey(game), fresh?.game_id ?? null]);
  return { tab, fresh };
}

async function allLocked(page, game) {
  await expect(page.locator(`.${game.key}-feedback`)).toHaveCount(0);
  for (const button of await page.locator(`${game.board} button, .${game.key}-actions button`).all()) await expect(button).toBeDisabled();
}

async function screenshot(page, name) {
  await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
  await page.screenshot({ path: test.info().outputPath(name), fullPage: true });
}

for (const game of games.filter(({ derived }) => derived)) {
  test.describe(game.key, () => {
    test.beforeEach(async ({ page }) => deterministicStarts(page, game));

    for (const mode of ["practice", ...(game.key === "perechi" ? ["match"] : []), "hint", "win", "loss"]) {
      test(`lost committed ${mode} recovers exact earned state with one GET`, async ({ page, request }) => {
        const { initial, action, perform } = await prepare(page, request, game, mode);
        const counts = traffic(page, game, initial.game_id);
        const committed = await loseResponse(page, game, initial.game_id, action);
        expect((await perform({ keyboard: game.key === "perechi" && mode === "match" })).status()).toBe(503);
        const fresh = await server(request, game, initial.game_id);
        for (const field of ["tiles", "mistakes", "hints_used", ...(game.key === "intrusul" ? ["wrong_ids", "attempts", "clue"] : ["solved_pairs", "solved_count", "actions", "hint"])]) expect(fresh[field]).toEqual(committed()[field]);
        if (mode === "win" || mode === "loss") {
          await expect(result(page)).toBeVisible();
          await expect.poll(() => played(page, game)).toBe(1);
          await expect.poll(() => saved(page, game)).toBeNull();
          expect(fresh[mode === "win" ? "won" : "lost"]).toBe(true);
          expect(fresh.score).toBe(committed().score);
          await screenshot(page, `recovered-${mode}.png`);
          await page.reload();
          await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
          expect(await played(page, game)).toBe(1);
        } else {
          expect(fresh.solution).toBeUndefined();
          expect(fresh.score).toBeUndefined();
          if (mode === "hint") {
            await expect(cue(page, game)).toContainText(game.key === "intrusul" ? fresh.clue.label : fresh.hint.label);
            expect(fresh.hints_used).toBe(1);
            await expect(page.getByRole("button", { name: "Indiciu folosit", exact: true })).toBeDisabled();
            await screenshot(page, "recovered-hint.png");
            await page.reload();
            await expect(cue(page, game)).toBeVisible();
            expect((await server(request, game, initial.game_id)).hints_used).toBe(1);
          } else {
            await expect(page.locator(`.${game.key}-feedback`)).toContainText("înregistrată");
            if (mode === "match") {
              for (const tile of fresh.solved_pairs[0].tiles) await expect(page.locator(".perechi-solved")).toContainText(tile.label);
              const focused = await page.locator(`${game.board} button:focus`).count();
              expect(focused).toBe(1);
            } else if (game.key === "intrusul") await expect(page.locator(".intrusul-tile--tried")).toHaveCount(1);
          }
          expect(await played(page, game)).toBe(0);
        }
        expect(counts).toEqual({ reads: mode === "hint" ? 2 : 1, mutations: 1 });
      });
    }

    test("failed reads persist and repeated manual verification never replays the paid hint", async ({ page, request }) => {
      const { initial, action, perform } = await prepare(page, request, game, "hint");
      const counts = traffic(page, game, initial.game_id);
      await loseResponse(page, game, initial.game_id, action);
      await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({ status: 503, json: {} }), { times: 2 });
      await perform();
      await expect(verify(page)).toBeEnabled();
      await allLocked(page, game);
      await verify(page).click();
      await expect(verify(page)).toBeEnabled();
      await allLocked(page, game);
      await page.waitForTimeout(4000);
      await expect(verify(page)).toBeVisible();
      expect(counts).toEqual({ reads: 2, mutations: 1 });
      expect(await saved(page, game)).toBe(initial.game_id);
      await screenshot(page, "persistent-read-only-retry.png");
      await verify(page).click();
      await expect(verify(page)).toHaveCount(0);
      await expect(cue(page, game)).toBeVisible();
      expect((await server(request, game, initial.game_id)).hints_used).toBe(1);
      expect(counts).toEqual({ reads: 3, mutations: 1 });
    });

    if (game.key === "perechi") {
      test("a keyboard match retains focus recovery through a failed GET and manual retry", async ({ page, request }) => {
        const { initial, action, perform } = await prepare(page, request, game, "match");
        const counts = traffic(page, game, initial.game_id);
        await loseResponse(page, game, initial.game_id, action);
        await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({ status: 503, json: {} }), { times: 1 });
        await perform({ keyboard: true });
        await expect(verify(page)).toBeEnabled();
        await allLocked(page, game);
        await verify(page).click();
        await expect(verify(page)).toHaveCount(0);
        await expect(page.locator(`${game.board} button:focus`)).toHaveCount(1);
        await expect(page.locator(`${game.board} button`)).toHaveCount(6);
        expect((await server(request, game, initial.game_id)).solved_count).toBe(1);
        expect(counts).toEqual({ reads: 2, mutations: 1 });
      });
    }

    test("a cleared saved pointer between verification attempts cannot revive an old win", async ({ page, request, context }) => {
      const { initial, action, perform } = await prepare(page, request, game, "win");
      const counts = traffic(page, game, initial.game_id);
      await loseResponse(page, game, initial.game_id, action);
      await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({ status: 503, json: {} }), { times: 1 });
      await perform();
      await expect(verify(page)).toBeEnabled();
      await allLocked(page, game);
      const { tab } = await replaceSaved(context, request, game, true);
      await verify(page).click();
      await expect(currentGame(page)).toBeEnabled();
      await allLocked(page, game);
      await expect(result(page)).toHaveCount(0);
      expect(await played(page, game)).toBe(0);
      expect(await saved(page, game)).toBeNull();
      expect(counts).toEqual({ reads: 1, mutations: 1 });
      await currentGame(page).click();
      await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
      expect(await played(page, game)).toBe(0);
      await tab.close();
    });

    test("an uncommitted action reads unchanged state without inventing progress", async ({ page, request }) => {
      const { initial, action, perform } = await prepare(page, request, game);
      const counts = traffic(page, game, initial.game_id);
      await loseResponse(page, game, initial.game_id, action, false);
      await perform();
      await expect(page.locator(`.${game.key}-feedback`)).toHaveText("Joc sincronizat. Poți continua.");
      expect(await server(request, game, initial.game_id)).toEqual(initial);
      expect(counts).toEqual({ reads: 1, mutations: 1 });
    });

    for (const phase of ["mutation", "read"]) {
      test(`a wrong game id in ${phase} cannot replace the displayed round`, async ({ page, request }) => {
        const { initial, action, perform } = await prepare(page, request, game, "hint");
        const counts = traffic(page, game, initial.game_id);
        if (phase === "read") await loseResponse(page, game, initial.game_id, action);
        await page.route(`**${gameURL(game, initial.game_id)}${phase === "mutation" ? `/${action}` : ""}`, async (route) => {
          const response = await route.fetch();
          await route.fulfill({ json: { ...await response.json(), game_id: "wrong-session" } });
        }, { times: 1 });
        await perform();
        if (phase === "read") {
          await expect(verify(page)).toBeEnabled();
          await allLocked(page, game);
          await verify(page).click();
        }
        await expect(cue(page, game)).toBeVisible();
        expect(await saved(page, game)).toBe(initial.game_id);
        expect(counts).toEqual({ reads: phase === "mutation" ? 1 : 2, mutations: 1 });
      });
    }

    test("owned confirmed 404 returns to intro and forgets only the missing round", async ({ page, request }) => {
      const { initial, action, perform } = await prepare(page, request, game);
      const counts = traffic(page, game, initial.game_id);
      await loseResponse(page, game, initial.game_id, action);
      await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({ status: 404, json: {} }), { times: 1 });
      await perform();
      await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
      expect(await saved(page, game)).toBeNull();
      expect(counts).toEqual({ reads: 1, mutations: 1 });
    });

    test("an already changed saved pointer prevents a mutation and loads the current round", async ({ page, request, context }) => {
      const { initial } = await prepare(page, request, game, "hint");
      const counts = traffic(page, game, initial.game_id);
      const { tab, fresh } = await replaceSaved(context, request, game);
      await hint(page, game).click();
      await expect(currentGame(page)).toBeEnabled();
      await allLocked(page, game);
      expect(counts).toEqual({ reads: 0, mutations: 0 });
      await currentGame(page).click();
      await expect(currentGame(page)).toHaveCount(0);
      await expect(page.locator(game.board)).toBeVisible();
      expect(await saved(page, game)).toBe(fresh.game_id);
      expect((await server(request, game, initial.game_id)).hints_used).toBe(0);
      await tab.close();
    });

    for (const phase of ["mutation", "read", "missing-read", "removed-pointer"]) {
      test(`a changed saved round rejects an old winning ${phase} completion without scoring`, async ({ page, request, context }) => {
        const { initial, action, perform } = await prepare(page, request, game, "win");
        const counts = traffic(page, game, initial.game_id);
        const mutation = phase === "mutation" || phase === "removed-pointer";
        if (!mutation) await loseResponse(page, game, initial.game_id, action);
        const held = await holdResponse(page, game, initial.game_id, mutation ? action : "", phase === "missing-read");
        const performed = perform();
        await held.requested;
        const { tab, fresh } = await replaceSaved(context, request, game, phase === "removed-pointer");
        held.release();
        await performed;
        await expect(currentGame(page)).toBeEnabled();
        await expect(result(page)).toHaveCount(0);
        await allLocked(page, game);
        expect(await played(page, game)).toBe(0);
        expect(await saved(page, game)).toBe(fresh?.game_id ?? null);
        expect(counts).toEqual({ reads: mutation ? 0 : 1, mutations: 1 });
        await currentGame(page).click();
        await expect(currentGame(page)).toHaveCount(0);
        if (fresh) await expect(page.locator(game.board)).toBeVisible();
        else await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
        expect(await played(page, game)).toBe(0);
        await tab.close();
      });
    }

    test("browser Back preserves the saved round when a winning reply arrives during departure", async ({ page, request }) => {
      await page.goto("/");
      const title = game.key === "intrusul" ? "Intrusul" : "Perechi";
      await page.getByRole("button", { name: new RegExp(`^Joacă ${title} —`) }).click();
      const created = page.waitForResponse((response) => response.request().method() === "POST" && new URL(response.url()).pathname === `/api/wordgames/${game.key}/games`);
      await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
      const initial = await (await created).json();
      await expect(page.locator(game.board)).toBeVisible();
      const steps = solution(game).steps;
      for (const step of steps.slice(0, -1)) await act(page, game, step);
      const counts = traffic(page, game, initial.game_id);
      const held = await holdResponse(page, game, initial.game_id, steps.at(-1).action);
      const performed = act(page, game, steps.at(-1));
      await held.requested;
      await page.goBack();
      await expect(page).toHaveURL("/");
      held.release();
      await performed;
      await expect(page.locator(game.board)).toHaveCount(0);
      expect(await played(page, game)).toBe(0);
      expect(await saved(page, game)).toBe(initial.game_id);
      expect(counts).toEqual({ reads: 0, mutations: 1 });
      expect((await server(request, game, initial.game_id)).won).toBe(true);
    });

    for (const phase of ["mutation", "read", "unmounted"]) {
      test(`exit invalidates a held winning ${phase} reply and resume records once`, async ({ page, request }) => {
        const { initial, action, perform } = await prepare(page, request, game, "win");
        const counts = traffic(page, game, initial.game_id);
        if (phase === "read") await loseResponse(page, game, initial.game_id, action);
        const held = await holdResponse(page, game, initial.game_id, phase === "read" ? "" : action);
        const performed = perform();
        await held.requested;
        await page.getByRole("button", { name: "Ieși la lista de jocuri" }).click();
        if (phase === "unmounted") await expect(page.locator(game.board)).toHaveCount(0);
        held.release();
        await performed;
        await expect(page.locator(game.board)).toHaveCount(0);
        expect(await played(page, game)).toBe(0);
        expect(await saved(page, game)).toBe(initial.game_id);
        expect(counts).toEqual({ reads: phase === "read" ? 1 : 0, mutations: 1 });
        await page.goto(game.path);
        await expect(result(page)).toBeVisible();
        await expect.poll(() => played(page, game)).toBe(1);
        expect((await server(request, game, initial.game_id)).won).toBe(true);
      });
    }
  });
}
