import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, solution, start, solve } from "./games.mjs";

const SCORE_KEY = "cat_wordgame_scores_v1";
const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const createPath = (game) => `/api/wordgames/${game.key}/games`;
const createResponse = (page, game) => page.waitForResponse((response) =>
  response.request().method() === "POST" && new URL(response.url()).pathname === createPath(game));
const notice = (page) => page.getByRole("alert").filter({ hasText: "Nu am putut porni jocul." });

function options(response) {
  const params = new URL(response.url()).searchParams;
  params.delete("seed"); // The existing deterministic route adds this only for real requests.
  params.sort();
  return params.toString();
}

async function failNextCreate(page, game, hold = false) {
  let release;
  let entered;
  const held = new Promise((resolve) => { release = resolve; });
  const requested = new Promise((resolve) => { entered = resolve; });
  await page.route(`**${createPath(game)}?*`, async (route) => {
    entered();
    if (hold) await held;
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "SQL server unavailable (503): private-diagnostic" }),
    });
  }, { times: 1 });
  return { requested, release };
}

async function scoreState(page) {
  return page.evaluate((key) => localStorage.getItem(key), SCORE_KEY);
}

async function assertPersistentFailure(page) {
  await expect(notice(page)).toBeVisible();
  await expect(notice(page)).toContainText("Am păstrat opțiunile alese.");
  await expect(notice(page)).not.toContainText(/503|SQL|server|private-diagnostic/);
  await page.clock.fastForward(4000); // The old toast expired after 3.6 seconds.
  await expect(notice(page)).toBeVisible();
  await expect(notice(page)).toBeInViewport();
  await page.screenshot({ path: test.info().outputPath("persistent-failure.png"), fullPage: true });
}

for (const game of games) {
  test(`${game.key} keeps a failed new start visible and retries the selected options`, async ({ page }) => {
    await page.clock.install();
    await deterministicStarts(page, game);
    await page.goto(game.path);
    if (!game.derived) {
      await page.getByRole("group", { name: "DIFICULTATE" })
        .getByRole("button", { name: /^Normal/ }).click();
      await page.getByRole("group", { name: "CATEGORIE" }).getByRole("button").nth(1).click();
    }
    const selections = await page.getByRole("button", { pressed: true }).allTextContents();
    const originalScores = await scoreState(page);
    const failedStart = await failNextCreate(page, game, true);
    const failedResponse = createResponse(page, game);
    await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
    await failedStart.requested;
    try {
      await expect(page.locator(".game-intro")).toHaveAttribute("inert", "");
      await expect(page.locator(".game-intro")).toHaveAttribute("aria-busy", "true");
      await expect(page.locator(".game-shell-header button")).toBeDisabled();
    } finally {
      failedStart.release();
    }
    const failed = await failedResponse;
    expect(failed.status()).toBe(503);
    await assertPersistentFailure(page);
    await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
    expect(await page.getByRole("button", { pressed: true }).allTextContents()).toEqual(selections);
    expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBeNull();
    expect(await scoreState(page)).toBe(originalScores);

    const retryResponse = createResponse(page, game);
    await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
    const retried = await retryResponse;
    expect(retried.status()).toBe(200);
    expect(options(retried)).toBe(options(failed));
    const state = await retried.json();
    await expect(page.locator(game.board)).toBeVisible();
    await expect(notice(page)).toHaveCount(0);
    await expect.poll(() => page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
      .toBe(state.game_id);
    expect(await scoreState(page)).toBe(originalScores);
  });

  test(`${game.key} retains its completed result when replay creation fails`, async ({ page }) => {
    await page.setViewportSize({ ...page.viewportSize(), height: 560 });
    await page.clock.install();
    await deterministicStarts(page, game);
    await start(page, game);
    await page.getByText("Reguli și ajutor", { exact: true }).click();
    await solve(page, game, solution(game).steps);
    await expect.poll(async () => {
      const scores = JSON.parse(await scoreState(page) || "{}");
      return scores[game.key]?.played ?? 0;
    }).toBe(1);
    const originalScores = await scoreState(page);
    const copy = page.getByRole("button", { name: "Copiază rezultatul" });
    const replay = page.getByRole("button", { name: /^Încă (?:unul|un lanț) →$/ });
    await replay.scrollIntoViewIfNeeded();
    // Sticky headers and partially visible rules do not indicate scroll length.
    expect(await replay.evaluate((button) => {
      for (let parent = button.parentElement; parent; parent = parent.parentElement) {
        if (parent.scrollHeight > parent.clientHeight + 1 && parent.scrollTop > 1) return true;
      }
      return false;
    })).toBe(true);

    await failNextCreate(page, game);
    const failedResponse = createResponse(page, game);
    await replay.click();
    const failed = await failedResponse;
    expect(failed.status()).toBe(503);
    await assertPersistentFailure(page);
    await expect(copy).toBeVisible();
    await expect(replay).toBeEnabled();
    await expect(replay).toBeInViewport();
    await expect(notice(page)).toHaveCount(1);
    expect(await scoreState(page)).toBe(originalScores);

    const retriedResponse = createResponse(page, game);
    await replay.click();
    const retried = await retriedResponse;
    expect(retried.status()).toBe(200);
    expect(options(retried)).toBe(options(failed));
    const fresh = await retried.json();
    await expect(page.locator(game.board)).toBeVisible();
    await expect(notice(page)).toHaveCount(0);
    await expect(copy).toHaveCount(0);
    await expect.poll(() => page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
      .toBe(fresh.game_id);
    expect(await scoreState(page)).toBe(originalScores);
  });
}

test("alchimie retains its live round and blocks actions while another round is pending", async ({ page, request }) => {
  const game = games.find(({ key }) => key === "alchimie");
  await page.setViewportSize({ ...page.viewportSize(), height: 560 });
  await page.clock.install();
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const firstStep = solution(game).steps[0];
  await page.getByRole("button", { name: /^Toate / }).click();
  for (const label of firstStep.labels) {
    await page.locator(game.board).getByRole("button", {
      name: new RegExp(`^${escapeRegex(label)}(?:,|$)`),
    }).click();
  }
  const combine = page.locator('button[aria-label="Combină cele două concepte selectate"]');
  const another = page.locator("button.alchimie-other-board");
  await expect(combine).toBeEnabled();
  const originalScores = await scoreState(page);
  let release;
  let entered;
  const held = new Promise((resolve) => { release = resolve; });
  const requested = new Promise((resolve) => { entered = resolve; });
  const oldMutations = [];
  page.on("request", (req) => {
    if (req.method() === "POST" && new URL(req.url()).pathname.startsWith(`${gameURL(game, initial.game_id)}/`)) {
      oldMutations.push(req.url());
    }
  });
  await page.route(`**${createPath(game)}?*`, async (route) => {
    entered();
    await held;
    await route.fulfill({ status: 503, contentType: "application/json", body: "{}" });
  }, { times: 1 });
  const failedResponse = createResponse(page, game);
  await another.click();
  await requested;
  try {
    await expect(combine).toBeDisabled();
    await expect(another).toBeDisabled();
    await expect(page.locator(".game-shell-header button")).toBeDisabled();
    await combine.dispatchEvent("click");
    await another.dispatchEvent("click");
    await page.locator(".game-shell-header button").dispatchEvent("click");
    await page.keyboard.press("Enter");
    await page.keyboard.press("Escape");
    expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
      .toBe(initial.game_id);
    expect(await (await request.get(gameURL(game, initial.game_id))).json()).toEqual(initial);
    expect(oldMutations).toEqual([]);
  } finally {
    release();
  }
  expect((await failedResponse).status()).toBe(503);
  await assertPersistentFailure(page);
  await expect(another).toBeEnabled();
  await expect(another).toBeInViewport();
  await expect(combine).toBeEnabled();
  await expect(page.getByRole("button", { name: /^Scoate .* din alambic$/ })).toHaveCount(2);
  expect(await scoreState(page)).toBe(originalScores);
  expect(await (await request.get(gameURL(game, initial.game_id))).json()).toEqual(initial);

  const retryResponse = createResponse(page, game);
  await another.click();
  const retried = await retryResponse;
  expect(retried.status()).toBe(200);
  const fresh = await retried.json();
  await expect(notice(page)).toHaveCount(0);
  await expect.poll(() => page.evaluate((key) => localStorage.getItem(key), activeKey(game)))
    .toBe(fresh.game_id);
  expect(fresh.game_id).not.toBe(initial.game_id);
  expect(oldMutations).toEqual([]);
});
