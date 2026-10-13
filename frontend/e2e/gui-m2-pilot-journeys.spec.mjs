// M2 pilot deep-link journeys (ADR-0197). Every ported route is entered by
// document URL and must be answered by the Preact shell (data-ui="preact");
// every other route must be the frozen legacy React bundle (data-ui="legacy").
// The motion-on project runs this file with real motion so the kit Presence
// retention/exit variant is exercised instead of finishing at duration 0.
import { test, expect } from "@playwright/test";
import { games, activeKey, gameURL, deterministicStarts, expectUi, portedRoutes, solution, start, solve, act } from "./games.mjs";

const ported = games.filter(({ path }) => portedRoutes.includes(path));
const legacy = ["/alchimie", "/cald-rece", "/lant", "/clasament"];
const motionOn = () => test.info().project.name === "motion-on";

function documentRequests(page) {
  const requests = [];
  page.on("request", (request) => {
    if (request.isNavigationRequest() && request.frame() === page.mainFrame()) requests.push(request.url());
  });
  return requests;
}

test("home deep link is the Preact shell and an unported card is a document navigation to legacy", async ({ page }) => {
  const navigations = documentRequests(page);
  await page.goto("/");
  await expectUi(page, "/");
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
  await expect(page.locator(".games-grid .game-card")).toHaveCount(6);
  await expect(page.locator(".roedu-root")).toHaveCount(1);
  expect(navigations).toHaveLength(1);
  const arrived = page.waitForURL(/\/cald-rece$/);
  await page.getByRole("button", { name: /^Joacă Cald sau Rece —/ }).click();
  await arrived;
  await expectUi(page, "/cald-rece");
  await expect(page.locator(".game-intro")).toBeVisible();
  expect(navigations).toHaveLength(2);
});

for (const game of ported) {
  test(`${game.key} deep link is served by the Preact shell and plays a seeded round`, async ({ page }) => {
    await deterministicStarts(page, game);
    const state = await start(page, game);
    expect(state.game_id.length).toBeGreaterThan(0);
    await solve(page, game, solution(game).steps);
    await expectUi(page, game.path);
    await expect.poll(() => page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBeNull();
  });

  test(`${game.key} exit returns to Home client-side without a new document`, async ({ page }) => {
    await deterministicStarts(page, game);
    const navigations = documentRequests(page);
    await start(page, game);
    expect(navigations).toHaveLength(1);
    await page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
    await expectUi(page, "/");
    expect(navigations).toHaveLength(1);
    await expect(page.locator(".app-content .roedu-presence[data-state=\"exiting\"]")).toHaveCount(0);
  });
}

test("every unported route is the frozen legacy bundle", async ({ page }) => {
  for (const route of legacy) {
    await page.goto(route);
    await expectUi(page, route);
    await expect(page.locator(".screen").first()).toBeVisible();
  }
});

test("Home circuit opens a ported daily client-side and an unported daily as a legacy document", async ({ page }) => {
  const navigations = documentRequests(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Deschide Intrusul — neterminat azi", exact: true }).click();
  await expect(page).toHaveURL(/\/intrusul\?challenge=daily$/);
  await expectUi(page, "/intrusul");
  await expect(page.getByRole("button", { name: "Joacă provocarea zilei", exact: true })).toBeFocused();
  expect(navigations).toHaveLength(1);
  await page.goBack();
  await expect(page).toHaveURL(/\/$/);
  const arrived = page.waitForURL(/\/lant\?challenge=daily$/);
  await page.getByRole("button", { name: "Deschide Lanțul Cuvintelor — neterminat azi", exact: true }).click();
  await arrived;
  await expectUi(page, "/lant");
  await expect(page.getByRole("button", { name: "Joacă provocarea zilei", exact: true })).toBeEnabled();
  expect(navigations).toHaveLength(2);
});

test("leaving Intrusul keeps the retained screen inert while a winning reply is held", async ({ page, request }) => {
  const game = games.find(({ key }) => key === "intrusul");
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const step = solution(game).steps[0];
  let entered, release;
  const requested = new Promise((resolve) => { entered = resolve; });
  const held = new Promise((resolve) => { release = resolve; });
  await page.route(`**${gameURL(game, initial.game_id)}/${step.action}`, async (route) => {
    const response = await route.fetch();
    entered();
    await held;
    await route.fulfill({ response });
  }, { times: 1 });
  const counts = { reads: 0 };
  page.on("request", (item) => {
    if (item.method() === "GET" && new URL(item.url()).pathname === gameURL(game, initial.game_id)) counts.reads += 1;
  });
  const performed = act(page, game, step);
  await requested;
  // Leave inside one evaluation so the retained frame is observed within the
  // Presence exit (180 ms with real motion), like the original Presence fixture.
  const snapshot = await page.evaluate(async ([board]) => {
    globalThis.document.querySelector('button[aria-label="Ieși la lista de jocuri"]').click();
    await new Promise((resolve) => globalThis.requestAnimationFrame(resolve));
    const exiting = globalThis.document.querySelector('.app-content .roedu-presence[data-state="exiting"]');
    const buttons = exiting ? [...exiting.querySelectorAll(`${board} button`)] : [];
    return { exiting: Boolean(exiting), buttons: buttons.length, disabled: buttons.every((button) => button.disabled) };
  }, [game.board]);
  if (motionOn()) {
    // Real motion: the kit Presence retains the exiting screen for its animation;
    // `useIsPresent()` is false there, so every retained control is disabled.
    expect(snapshot.exiting).toBe(true);
    expect(snapshot.buttons).toBeGreaterThan(0);
    expect(snapshot.disabled).toBe(true);
  }
  release();
  await performed;
  await expect(page.locator(game.board)).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
  await expect(page.locator(".app-content .roedu-presence[data-state=\"exiting\"]")).toHaveCount(0);
  expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(initial.game_id);
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem("cat_wordgame_scores_v1") || "{}").intrusul?.played ?? 0)).toBe(0);
  expect(counts.reads).toBe(0);
  expect((await (await request.get(gameURL(game, initial.game_id))).json()).won).toBe(true);
});

test("Conexiuni solved tiles leave through the Presence scale variant and the board keeps four columns", async ({ page }) => {
  const game = games.find(({ key }) => key === "conexiuni");
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const grid = page.locator(game.board);
  expect(await grid.evaluate((element) => getComputedStyle(element).gridTemplateColumns.split(/\s+/).filter(Boolean).length)).toBe(4);
  await expect(grid.locator(":scope > .roedu-presence > .connection-tile")).toHaveCount(16);
  const step = solution(game).steps[0];
  const response = page.waitForResponse((item) => item.request().method() === "POST" && new URL(item.url()).pathname === `${gameURL(game, initial.game_id)}/guess`);
  for (const label of step.labels) await grid.getByRole("button", { name: label, exact: true }).click();
  await page.getByRole("button", { name: "Verifică", exact: true }).click();
  const observed = page.waitForFunction(() => globalThis.document.getAnimations().some((animation) => {
    const target = animation.effect?.target;
    return target instanceof globalThis.Element && target.matches(".connections-grid > .roedu-presence[data-state=\"exiting\"]")
      && JSON.stringify(animation.effect.getKeyframes()).includes("scale(0.4)");
  }), undefined, { timeout: 4000 }).then(() => true, () => false);
  expect((await (await response).json()).correct).toBe(true);
  if (motionOn()) expect(await observed, "the exit keyframes must be Presence-owned scale 1 -> 0.4").toBe(true);
  await expect(grid.locator(":scope > .roedu-presence > .connection-tile")).toHaveCount(12);
  await expect(page.locator(".connections-grid > .roedu-presence[data-state=\"exiting\"]")).toHaveCount(0);
  expect(await grid.evaluate((element) => getComputedStyle(element).gridTemplateColumns.split(/\s+/).filter(Boolean).length)).toBe(4);
});
