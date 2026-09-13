import { test, expect } from "@playwright/test";
import { games, gameURL, deterministicStarts, solution, start } from "./games.mjs";

const quickGames = games.filter(({ derived }) => derived);
const activate = (locator, testInfo) => testInfo.project.name === "mobile" ? locator.tap() : locator.click();

async function prepareHint(page, request, game) {
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const steps = solution(game).steps;
  const wrongMoves = game.key === "intrusul"
    ? [{ action: "guess", payload: { id: initial.tiles.find((tile) => tile.id !== steps[0].payload.id).id } }]
    : steps[1].payload.ids.map((id) => ({ action: "match", payload: { ids: [steps[0].payload.ids[0], id] } }));
  for (const move of wrongMoves) {
    const response = await request.post(`${gameURL(game, initial.game_id)}/${move.action}`, { data: move.payload });
    expect(response.status()).toBe(200);
  }
  await page.reload();
  const hint = page.locator(`.${game.key}-actions`).getByRole("button", { name: /−150 pct/ });
  await expect(hint).toBeVisible();
  await expect(hint).toBeEnabled();
  return { initial, hint };
}

for (const game of quickGames) {
  test(`${game.key} keeps the complete initial board visible on a narrow phone`, async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 740 });
    await deterministicStarts(page, game);
    await start(page, game);
    await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
    await expect(page.locator(".game-options")).not.toHaveAttribute("open");
    await expect(page.locator(`${game.board} button`)).toHaveCount(game.key === "intrusul" ? 4 : 8);
    await expect(page.locator(`.${game.key}-actions button`)).toHaveCount(0);
    for (const tile of await page.locator(`${game.board} button`).all()) {
      const bounds = await tile.boundingBox();
      expect(bounds.y).toBeGreaterThanOrEqual(0);
      expect(bounds.y + bounds.height).toBeLessThanOrEqual(740);
      expect(bounds.width).toBeGreaterThanOrEqual(44);
      expect(bounds.height).toBeGreaterThanOrEqual(44);
    }
    expect(await page.evaluate(() => globalThis.document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  });

  test(`${game.key} makes an unlocked hint explicit, priced and persistent`, async ({ page, request }, testInfo) => {
    const { initial, hint } = await prepareHint(page, request, game);
    const mutations = [];
    page.on("request", (request) => {
      if (request.method() === "POST" && new URL(request.url()).pathname.startsWith(`${gameURL(game, initial.game_id)}/`)) mutations.push(request.url());
    });
    await activate(page.locator(".game-options > summary"), testInfo);
    await activate(page.locator(".game-help > summary"), testInfo);
    expect(mutations).toHaveLength(0);
    const response = page.waitForResponse((response) => response.request().method() === "POST" &&
      new URL(response.url()).pathname === `${gameURL(game, initial.game_id)}/hint`);
    await activate(hint, testInfo);
    const earned = await (await response).json();
    expect(earned.hints_used).toBe(1);
    const cue = page.locator(game.key === "intrusul" ? ".intrusul-clue" : ".perechi-hint");
    await expect(cue).toBeVisible();
    await expect(page.locator(`.${game.key}-actions button`)).toHaveCount(0);
    await page.reload();
    await expect(cue).toBeVisible();
    expect(mutations).toHaveLength(1);
  });

  test(`${game.key} restores usable board focus after keyboard hint activation`, async ({ page, request }) => {
    const { initial, hint } = await prepareHint(page, request, game);
    const mutations = [];
    page.on("request", (request) => {
      if (request.method() === "POST" && new URL(request.url()).pathname.startsWith(`${gameURL(game, initial.game_id)}/`)) mutations.push(request.url());
    });
    await hint.focus();
    const response = page.waitForResponse((response) => response.request().method() === "POST" &&
      new URL(response.url()).pathname === `${gameURL(game, initial.game_id)}/hint`);
    await page.keyboard.press("Enter");
    expect((await (await response).json()).hints_used).toBe(1);
    await expect(hint).toHaveCount(0);
    const focused = page.locator(`${game.board} button:focus`);
    await expect(focused).toHaveCount(1);
    await expect(focused).toBeEnabled();
    if (game.key === "intrusul") await expect(focused).not.toHaveClass(/intrusul-tile--tried/);
    else await expect(focused).toHaveClass(/perechi-tile--hinted/);
    expect(mutations).toHaveLength(1);
  });

  test(`${game.key} preserves options focus while a keyboard hint response is held`, async ({ page, request }) => {
    const { initial, hint } = await prepareHint(page, request, game);
    let release;
    let entered;
    const held = new Promise((resolve) => { release = resolve; });
    const requested = new Promise((resolve) => { entered = resolve; });
    await page.route(`**${gameURL(game, initial.game_id)}/hint`, async (route) => {
      const response = await route.fetch();
      entered();
      await held;
      await route.fulfill({ response });
    }, { times: 1 });
    try {
      await hint.focus();
      await page.keyboard.press("Enter");
      await requested;
      const options = page.locator(".game-options > summary");
      await options.focus();
      await page.keyboard.press("Enter");
      await expect(page.locator(".game-options")).toHaveAttribute("open", "");
      await expect(options).toBeFocused();
      release();
      await expect(hint).toHaveCount(0);
      await expect(page.locator(game.key === "intrusul" ? ".intrusul-clue" : ".perechi-hint")).toBeVisible();
      await expect(options).toBeFocused();
      await expect(page.locator(`${game.board} button:focus`)).toHaveCount(0);
    } finally {
      release();
    }
  });
}

test("Perechi cancels on retap and submits a pair on the second word only", async ({ page }, testInfo) => {
  const game = quickGames.find(({ key }) => key === "perechi");
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const step = solution(game).steps[0];
  const first = page.locator(game.board).getByRole("button", { name: step.labels[0], exact: true });
  const second = page.locator(game.board).getByRole("button", { name: step.labels[1], exact: true });
  const mutations = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname === `${gameURL(game, initial.game_id)}/match`) mutations.push(request.url());
  });
  await activate(first, testInfo);
  await expect(first).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".perechi-instruction")).toContainText(step.labels[0]);
  await expect(page.getByRole("button", { name: "Golește", exact: true })).toHaveCount(0);
  await activate(first, testInfo);
  await expect(first).toHaveAttribute("aria-pressed", "false");
  expect(mutations).toHaveLength(0);
  await activate(first, testInfo);
  const response = page.waitForResponse((response) => response.request().method() === "POST" &&
    new URL(response.url()).pathname === `${gameURL(game, initial.game_id)}/match`);
  await activate(second, testInfo);
  expect((await (await response).json()).solved_count).toBe(1);
  await expect(page.locator(`${game.board} button`)).toHaveCount(6);
  expect(mutations).toHaveLength(1);
  const boardBounds = await page.locator(game.board).boundingBox();
  const solvedBounds = await page.locator(".perechi-solved").boundingBox();
  expect(solvedBounds.y).toBeGreaterThan(boardBounds.y + boardBounds.height);
});
