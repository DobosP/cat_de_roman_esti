// Authored M0 replacements; NOT RUN during authoring. Saved IDs refer to real
// ordinary local-server sessions. The clock supplies a deterministic browser
// date; the explicit 503 fixture below refuses a create before any server commit.
// No game state, score, solution or daily metadata is manufactured.
import { test, expect } from "@playwright/test";
import {
  games, activeKey, gameURL, deterministicStarts, solution, solve, openGameOptions,
} from "./games.mjs";

const TODAY = "2026-10-08";
const OLDER = "2026-09-23";
const FIXED_TIME = "2026-10-08T12:00:00.000Z";
const SCORE_KEY = "cat_wordgame_scores_v1";
const BYPASS = "Ai continuat jocul liber început. Provocarea zilei te așteaptă după ce îl termini.";
const TITLES = {
  alchimie: "Alchimie", intrusul: "Intrusul", perechi: "Perechi",
  conexiuni: "Conexiuni", contexto: "Cald sau Rece", lant: "Lanțul Cuvintelor",
};
const FREE_LABEL = {
  alchimie: "Joacă →", intrusul: "Joacă", perechi: "Joacă",
  conexiuni: "Joacă", contexto: "Joacă", lant: "Joacă →",
};
const createPath = (game) => `/api/wordgames/${game.key}/games`;
const created = (page, game) => page.waitForResponse((response) =>
  response.request().method() === "POST" &&
  new URL(response.url()).pathname === createPath(game));

function circuitURL(game) {
  const url = new URL(game.path, "http://local.invalid");
  url.searchParams.set("challenge", "daily");
  return `${url.pathname}${url.search}`;
}

async function clock(page) {
  await page.clock.setFixedTime(new Date(FIXED_TIME));
}

async function realSavedRound(request, game, daily) {
  const query = new URLSearchParams({ seed: "38", difficulty: "usor" });
  if (daily) query.set("daily", daily);
  else if (game.derived) query.set("starter", "1");
  const response = await request.post(`${createPath(game)}?${query}`);
  expect(response.status()).toBe(200);
  expect(new URL(response.url()).searchParams.get("daily")).toBe(daily ?? null);
  const state = await response.json();
  expect(state.won).toBe(false);
  expect(state.lost ?? false).toBe(false);
  if (daily) expect(state.daily).toBe(daily);
  else expect(state.daily).toBeFalsy();
  return state;
}

async function rememberAndResume(page, game, initial) {
  // This is the existing saved-ID browser fixture, bound to an actual created
  // session. It does not supply a GET body or overwrite application score writes.
  await page.addInitScript(([key, id]) => {
    if (localStorage.getItem(key) === null) localStorage.setItem(key, id);
  }, [activeKey(game), initial.game_id]);
  const creates = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname === createPath(game)) {
      creates.push(request.url());
    }
  });
  const resumed = page.waitForResponse((response) => response.request().method() === "GET" &&
    new URL(response.url()).pathname === gameURL(game, initial.game_id));
  await page.goto(circuitURL(game));
  const response = await resumed;
  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual(initial);
  await expect(page.locator(game.board)).toBeVisible();
  expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
    .toBe(initial.game_id);
  expect(creates).toHaveLength(0);
  return creates;
}

async function assertSuppliedDate(page, game, daily) {
  const display = daily === OLDER ? "23.09.2026" : "08.10.2026";
  if (["intrusul", "perechi", "conexiuni"].includes(game.key)) {
    const badge = page.locator(".stat-badge").filter({ hasText: "ZILNIC" });
    await expect(badge.locator(".stat-badge-value")).toHaveText(display);
  } else if (game.key === "alchimie") {
    await expect(page.locator(".alchemy-theme")).toContainText(display);
  } else {
    await openGameOptions(page, game);
    if (game.key === "lant") {
      await expect(page.locator(".lant-round-details"))
        .toContainText(`Provocarea zilei: ${display}.`);
    } else {
      await expect(page.locator(".game-options .stat-badge").filter({ hasText: display }))
        .toContainText(`📅 ${display}`);
    }
  }
}

async function recentScore(page, game) {
  return page.evaluate(([key, gameKey]) =>
    JSON.parse(localStorage.getItem(key) || "{}")[gameKey]?.recent?.[0] ?? null,
  [SCORE_KEY, game.key]);
}

for (const game of games) {
  test(`${game.key} daily intent changes only intro action order and initial focus`, async ({ page }) => {
    await clock(page);
    await page.goto(game.path);
    let actions = page.locator(".game-intro-actions").getByRole("button");
    await expect(actions).toHaveCount(2);
    await expect(actions.nth(0)).toHaveAccessibleName(FREE_LABEL[game.key]);
    await expect(actions.nth(1)).toHaveAccessibleName("Provocarea zilei");
    await expect(actions.nth(0)).toBeFocused();
    await page.goto("/");
    await page.getByRole("button", {
      name: `Deschide ${TITLES[game.key]} — neterminat azi`, exact: true,
    }).click();
    actions = page.locator(".game-intro-actions").getByRole("button");
    await expect(actions).toHaveCount(2);
    await expect(actions.nth(0)).toHaveAccessibleName("Joacă provocarea zilei");
    await expect(actions.nth(1)).toHaveAccessibleName("Joacă liber");
    await expect(actions.nth(0)).toBeFocused();
  });

  for (const variant of ["free", "today", "older"]) {
    test(`${game.key} circuit resumes a real ${variant} round with the correct single notice, intent and supplied date`, async ({ page, request }) => {
      await clock(page);
      const daily = variant === "today" ? TODAY : variant === "older" ? OLDER : undefined;
      const initial = await realSavedRound(request, game, daily);
      const creates = await rememberAndResume(page, game, initial);
      const notice = page.getByText(BYPASS, { exact: true });
      if (variant === "free") {
        await expect(notice).toHaveCount(1);
        await expect(notice).toBeVisible();
        await expect(page.getByText("Joc reluat.", { exact: true })).toHaveCount(0);
      } else {
        await expect(notice).toHaveCount(0);
        await assertSuppliedDate(page, game, daily);
      }
      await expect.poll(() => new URL(page.url()).searchParams.get("challenge"))
        .toBe(variant === "today" ? null : "daily");
      if (game.key === "alchimie") {
        expect(new URL(page.url()).searchParams.get("mode")).toBe("challenges");
      }
      expect(creates).toHaveLength(0);
      const persisted = await request.get(gameURL(game, initial.game_id));
      expect(persisted.status()).toBe(200);
      expect(await persisted.json()).toEqual(initial);

      if (variant === "older") {
        // Finish the actual supplied-day session through the ordinary UI. The
        // resulting score metadata must retain that raw day, not today's day or
        // the Romanian display string. No synthetic score/history is seeded.
        const fixture = { ...game, daily };
        const plan = solution(fixture);
        const stable = { ...initial };
        delete stable.game_id;
        expect(stable).toEqual(plan.initial);
        const terminal = await solve(page, game, plan.steps);
        // Lanț's move response deliberately omits daily; the actual public GET
        // binds the supplied day for every game without inventing response fields.
        const finished = await request.get(gameURL(game, initial.game_id));
        expect(finished.status()).toBe(200);
        const persistedTerminal = await finished.json();
        expect(persistedTerminal.won).toBe(true);
        expect(persistedTerminal.daily).toBe(OLDER);
        await expect.poll(async () => (await recentScore(page, game))?.daily).toBe(OLDER);
        const entry = await recentScore(page, game);
        expect(entry.score).toBe(terminal.score);
        expect(entry.puzzleKey).toContain(`daily-${OLDER}`);
        expect(entry.puzzleKey).not.toContain("23.09.2026");
        expect(entry.puzzleKey).not.toContain(`daily-${TODAY}`);
      }
    });
  }
}

for (const game of games.filter(({ key }) => ["conexiuni", "contexto", "lant"].includes(key))) {
  test(`${game.key} daily create carries the player's real Normal choice without a category query`, async ({ page }) => {
    await clock(page);
    // Do not intercept or rewrite creation options: the captured query must come
    // directly from the actual Normal picker and secondary daily action.
    await page.goto(game.path);
    await openGameOptions(page, game, { setup: true });
    const normal = page.locator(".game-setup-options").getByRole("button", { name: /^Normal/ });
    await normal.click();
    await expect(normal).toHaveAttribute("aria-pressed", "true");
    const pending = created(page, game);
    await page.getByRole("button", { name: "Provocarea zilei", exact: true }).click();
    const response = await pending;
    expect(response.status()).toBe(200);
    const query = new URL(response.url()).searchParams;
    expect(query.get("difficulty")).toBe("normal");
    expect(query.get("daily")).toBe(TODAY);
    expect(query.get("category")).toBeNull();
    const state = await response.json();
    expect(state.difficulty).toBe("normal");
    expect(state.daily).toBe(TODAY);
    await expect(page.locator(game.board)).toBeVisible();
  });
}

for (const game of games.filter(({ derived }) => derived)) {
  test(`${game.key} failed daily create retains the result offer until real success and normal free replay`, async ({ page, request }) => {
    await clock(page);
    await deterministicStarts(page, game);
    const initial = await realSavedRound(request, game);
    const creates = await rememberAndResume(page, game, initial);
    await expect(page.getByText(BYPASS, { exact: true })).toBeVisible();
    await solve(page, game, solution(game).steps);
    await expect.poll(() => page.evaluate(([key, gameKey]) =>
      JSON.parse(localStorage.getItem(key) || "{}")[gameKey]?.played ?? 0,
    [SCORE_KEY, game.key])).toBe(1);
    const offer = page.getByRole("button", { name: "Joacă provocarea zilei →", exact: true });
    await expect(offer).toBeEnabled();
    await expect(offer.locator("..").getByRole("button").first())
      .toHaveAccessibleName("Joacă provocarea zilei →");

    // Explicit precommit transport-failure fixture: this route never calls the
    // server, so it cannot manufacture a committed daily or a winning result.
    await page.route(`**${createPath(game)}?*`, (route) => route.fulfill({
      status: 503, json: { detail: "Daily create unavailable before commit (test fixture)." },
    }), { times: 1 });
    const failed = created(page, game);
    await offer.click();
    const refused = await failed;
    expect(refused.status()).toBe(503);
    expect(new URL(refused.url()).searchParams.get("daily")).toBe(TODAY);
    await expect.poll(() => new URL(page.url()).searchParams.get("challenge")).toBeNull();
    await expect(page.locator(".start-failure-notice[role=alert]"))
      .toContainText("Nu am putut porni jocul. Am păstrat opțiunile alese. Poți încerca din nou.");
    await expect(offer).toBeEnabled();
    expect(creates).toHaveLength(1);
    const old = await request.get(gameURL(game, initial.game_id));
    expect(old.status()).toBe(200);
    expect((await old.json()).won).toBe(true);

    const retry = created(page, game);
    await offer.click();
    const accepted = await retry;
    expect(accepted.status()).toBe(200);
    const acceptedQuery = new URL(accepted.url()).searchParams;
    expect(acceptedQuery.get("daily")).toBe(TODAY);
    expect(acceptedQuery.get("starter")).toBeNull();
    expect(acceptedQuery.get("previous_game_id")).toBeNull();
    const daily = await accepted.json();
    expect(daily.daily).toBe(TODAY);
    expect(daily.game_id).not.toBe(initial.game_id);
    await expect(page.locator(game.board)).toBeVisible();
    await expect(page.locator(".start-failure-notice[role=alert]")).toHaveCount(0);
    expect(creates).toHaveLength(2);
    await solve(page, game, solution({ ...game, daily: TODAY }).steps);
    const replay = page.getByRole("button", { name: "Joacă liber →", exact: true });
    await expect(replay).toBeEnabled();
    await expect(offer).toHaveCount(0);
    const free = created(page, game);
    await replay.click();
    const next = await free;
    expect(next.status()).toBe(200);
    expect(new URL(next.url()).searchParams.get("daily")).toBeNull();
    const nextState = await next.json();
    expect(nextState.daily).toBeFalsy();
    expect(nextState.game_id).not.toBe(daily.game_id);
    await expect(page.locator(game.board)).toBeVisible();
    expect(creates).toHaveLength(3);
  });
}
