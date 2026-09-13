import { test, expect } from "@playwright/test";
import { games, gameURL, deterministicStarts, solution, start } from "./games.mjs";

const game = games.find(({ key }) => key === "conexiuni");
const activate = (button) => test.info().project.name === "mobile" ? button.tap() : button.click();
const verify = (page) => page.getByRole("button", { name: "Verifică", exact: true });

async function settle(page) {
  await page.evaluate(async () => {
    await globalThis.document.fonts.ready;
    await Promise.all(globalThis.document.getAnimations().filter((animation) =>
      Number.isFinite(animation.effect?.getComputedTiming().endTime),
    ).map((animation) => animation.finished.catch(() => {})));
  });
}

test.beforeEach(async ({ page }) => {
  await deterministicStarts(page, game);
});

test("all sixteen tiles and the three actions fit in four columns before optional controls", async ({ page }) => {
  if (test.info().project.name === "mobile") await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(game.path);
  await expect(page.locator(".game-setup-options")).not.toHaveAttribute("open", "");
  await start(page, game);
  await settle(page);
  await expect(page.locator(".game-options")).not.toHaveAttribute("open", "");
  const tiles = page.locator(".connections-grid button");
  await expect(tiles).toHaveCount(16);
  const metrics = await tiles.evaluateAll((buttons) => ({
    width: globalThis.innerWidth, height: globalThis.innerHeight,
    columns: globalThis.getComputedStyle(buttons[0].parentElement).gridTemplateColumns.split(" ").length,
    tiles: buttons.map((button) => {
      const rect = button.getBoundingClientRect();
      return { x: rect.x, y: rect.y, right: rect.right, bottom: rect.bottom, width: rect.width, height: rect.height };
    }),
  }));
  expect(metrics.columns).toBe(4);
  expect(new Set(metrics.tiles.map(({ x }) => Math.round(x))).size).toBe(4);
  expect(new Set(metrics.tiles.map(({ y }) => Math.round(y))).size).toBe(4);
  for (const tile of metrics.tiles) {
    expect(tile.y).toBeGreaterThanOrEqual(0);
    expect(tile.bottom).toBeLessThanOrEqual(metrics.height);
    expect(tile.width).toBeGreaterThanOrEqual(44);
    expect(tile.height).toBeGreaterThanOrEqual(44);
  }
  for (const name of ["Amestecă", "Golește", "Verifică"]) {
    const bounds = await page.getByRole("button", { name, exact: true }).boundingBox();
    expect(bounds.y).toBeGreaterThanOrEqual(metrics.tiles.at(-1).bottom);
    expect(bounds.y + bounds.height).toBeLessThanOrEqual(metrics.height);
  }
  await expect(page.getByRole("button", { name: /^Indiciu/ })).toHaveCount(0);
  await test.info().attach("compact-grid-geometry", { body: JSON.stringify(metrics, null, 2), contentType: "application/json" });
  await test.info().attach("compact-grid", { body: await page.screenshot(), contentType: "image/png" });
});

test("four selections need explicit verification while shuffle and clear never spend a move", async ({ page, request }) => {
  const initial = await start(page, game);
  const step = solution(game).steps[0];
  const mutations = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname.startsWith(`${gameURL(game, initial.game_id)}/`)) {
      mutations.push(request.url());
    }
  });
  const chooseGroup = async () => {
    for (const label of step.labels) {
      await activate(page.locator(game.board).getByRole("button", { name: label, exact: true }));
    }
    await expect(page.locator(`${game.board} button[aria-pressed="true"]`)).toHaveCount(4);
    await expect(verify(page)).toBeEnabled();
  };
  await chooseGroup();
  expect(mutations).toHaveLength(0);
  const beforeShuffle = await page.locator(`${game.board} button`).allTextContents();
  await activate(page.getByRole("button", { name: "Amestecă", exact: true }));
  await expect.poll(() => page.locator(`${game.board} button`).allTextContents()).not.toEqual(beforeShuffle);
  await expect(page.locator(`${game.board} button[aria-pressed="true"]`)).toHaveCount(4);
  await activate(page.getByRole("button", { name: "Golește", exact: true }));
  await expect(page.locator(`${game.board} button[aria-pressed="true"]`)).toHaveCount(0);
  await expect(verify(page)).toBeDisabled();
  expect(mutations).toHaveLength(0);
  expect(await (await request.get(gameURL(game, initial.game_id))).json()).toEqual(initial);
  await chooseGroup();
  expect(mutations).toHaveLength(0);
  const response = page.waitForResponse((response) => response.request().method() === "POST" &&
    new URL(response.url()).pathname === `${gameURL(game, initial.game_id)}/guess`);
  await activate(verify(page));
  const result = await (await response).json();
  expect(result.correct).toBe(true);
  expect(result.solved_count).toBe(1);
  expect(result.mistakes).toBe(0);
  expect(mutations).toHaveLength(1);
  await expect(page.locator(`${game.board} button`)).toHaveCount(12);
});

test("long Romanian words remain readable at 320 pixels and doubled text without horizontal scrolling", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 844 });
  await start(page, game);
  // Presentation stress only: game state and server responses stay unchanged.
  await page.evaluate(() => {
    globalThis.document.documentElement.style.fontSize = "200%";
    const words = ["Îndeletniciri gospodărești", "Tradiții și sărbători românești", "Personalități din istoria României", "Comunitatea și viața de zi cu zi"];
    [...globalThis.document.querySelectorAll(".connection-tile")].slice(0, 4)
      .forEach((button, index) => { button.textContent = words[index]; });
  });
  await settle(page);
  const metrics = await page.locator(".connections-screen").evaluate((screen) => ({
    pageWidth: globalThis.document.documentElement.scrollWidth,
    width: globalThis.innerWidth, contentWidth: screen.scrollWidth, clientWidth: screen.clientWidth,
    tiles: [...screen.querySelectorAll(".connection-tile")].map((button) => ({
      width: button.clientWidth, contentWidth: button.scrollWidth,
      height: button.clientHeight, contentHeight: button.scrollHeight,
      fontSize: Number.parseFloat(globalThis.getComputedStyle(button).fontSize),
    })),
  }));
  expect(metrics.pageWidth).toBeLessThanOrEqual(metrics.width);
  expect(metrics.contentWidth).toBeLessThanOrEqual(metrics.clientWidth + 1);
  for (const tile of metrics.tiles) {
    expect(tile.fontSize).toBeGreaterThanOrEqual(24);
    expect(tile.contentWidth).toBeLessThanOrEqual(tile.width + 1);
    expect(tile.contentHeight).toBeLessThanOrEqual(tile.height + 1);
  }
  const shuffle = page.getByRole("button", { name: "Amestecă", exact: true });
  await shuffle.scrollIntoViewIfNeeded();
  for (const name of ["Amestecă", "Golește", "Verifică"]) {
    const button = page.getByRole("button", { name, exact: true });
    await expect(button).toBeInViewport();
    const bounds = await button.boundingBox();
    expect(bounds.x).toBeGreaterThanOrEqual(0);
    expect(bounds.x + bounds.width).toBeLessThanOrEqual(320);
  }
  await test.info().attach("doubled-text-geometry", { body: JSON.stringify(metrics, null, 2), contentType: "application/json" });
  await test.info().attach("doubled-text-actions", { body: await page.screenshot(), contentType: "image/png" });
});
