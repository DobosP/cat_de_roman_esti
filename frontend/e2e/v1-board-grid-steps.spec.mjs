import { test, expect } from "@playwright/test";
import { games, deterministicStarts, start } from "./games.mjs";

const game = (key) => games.find((candidate) => candidate.key === key);
// [viewport width, browser text size in px, Conexiuni columns, Intrusul/Perechi columns]
const cases = [
  [390, 24, 2, 1],
  [1280, 24, 4, 2],
  [320, 32, 2, 1],
  [360, 16, 4, 2],
];
const boards = [
  { key: "conexiuni", tiles: 16, expected: ([, , columns]) => columns },
  { key: "intrusul", tiles: 4, expected: ([, , , columns]) => columns },
  { key: "perechi", tiles: 8, expected: ([, , , columns]) => columns },
];

// Emulates the browser's default text-size setting, so rem and em media queries both follow it.
async function textSize(page, px) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Page.setFontSizes", { fontSizes: { standard: px } });
  await expect.poll(() => page.evaluate(() =>
    Number.parseFloat(globalThis.getComputedStyle(globalThis.document.documentElement).fontSize))).toBe(px);
}

async function layout(page, width, px) {
  await page.setViewportSize({ width, height: 844 });
  await textSize(page, px);
  await page.evaluate(async () => {
    await globalThis.document.fonts.ready;
    await Promise.all(globalThis.document.getAnimations().filter((animation) =>
      Number.isFinite(animation.effect?.getComputedTiming().endTime),
    ).map((animation) => animation.finished.catch(() => {})));
  });
}

const rowsOf = (page, board) => page.locator(board).evaluate((grid) => {
  const rows = new Map();
  for (const tile of grid.querySelectorAll("button")) {
    const top = Math.round(tile.getBoundingClientRect().top);
    rows.set(top, (rows.get(top) ?? 0) + 1);
  }
  return [...rows.entries()].sort(([a], [b]) => a - b).map(([, count]) => count);
});

const linesOf = (element) => element.evaluate((node) => {
  const range = globalThis.document.createRange();
  range.selectNodeContents(node);
  return new Set([...range.getClientRects()].map((rect) => Math.round(rect.top))).size;
});

for (const board of boards) {
  test(`${board.key} board only ever shows whole rows of 4, 2 or 1 tiles`, async ({ page }) => {
    const current = game(board.key);
    await deterministicStarts(page, current);
    await start(page, current);
    await expect(page.locator(`${current.board} button`)).toHaveCount(board.tiles);
    for (const scenario of cases) {
      const [width, px] = scenario;
      await layout(page, width, px);
      const columns = board.expected(scenario);
      await expect.poll(() => rowsOf(page, current.board), `${board.key} at ${width}px / ${px}px text`)
        .toEqual(Array(board.tiles / columns).fill(columns));
      expect(await page.evaluate(() => globalThis.document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    }
  });
}

test("Lanț stacks the route on narrow text-constrained screens so long words stay whole", async ({ page }) => {
  const lant = game("lant");
  await deterministicStarts(page, lant);
  await start(page, lant);
  // Presentation stress with real KG labels; no board or response mutation.
  const words = page.locator(".lant-route .lant-route-word");
  await words.first().evaluate((word) => { word.textContent = "Transfăgărășan"; });
  await words.last().evaluate((word) => { word.textContent = "Teleenciclopedia"; });
  // Every phone stacks (30em is 480px at default text); desktop keeps the three-track route.
  for (const [width, px, stacked] of [[320, 16, true], [390, 16, true], [412, 24, true], [390, 24, true], [1280, 16, false]]) {
    await layout(page, width, px);
    const tracks = await page.locator(".lant-route").evaluate((route) =>
      globalThis.getComputedStyle(route).gridTemplateColumns.split(" ").length);
    expect(tracks, `${width}px / ${px}px text`).toBe(stacked ? 1 : 3);
    for (const word of await words.all()) expect(await linesOf(word), `${width}px / ${px}px text`).toBe(1);
    expect(await page.evaluate(() => globalThis.document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }
});

test("Alchimie inventory keeps long words whole on phones and desktop", async ({ page }) => {
  const alchimie = game("alchimie");
  await deterministicStarts(page, alchimie);
  await start(page, alchimie);
  const label = page.locator(`${alchimie.board} .alchemy-word-label`).first();
  // Real KG labels; two columns stay at default phone text, enlarged text drops to one.
  for (const [width, px, word] of [
    [320, 16, "Electricitate"], [360, 16, "Electricitate"], [360, 20, "Cinematografia"],
    [412, 24, "Cinematografia"], [390, 24, "Transfăgărășan"], [1280, 16, "Transfăgărășan"],
  ]) {
    await label.evaluate((node, text) => { node.textContent = text; }, word);
    await layout(page, width, px);
    expect(await linesOf(label), `${width}px / ${px}px text`).toBe(1);
    expect(await page.evaluate(() => globalThis.document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }
});
