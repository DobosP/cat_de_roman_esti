import { test, expect } from "@playwright/test";
import { applyDoubledText } from "./fixture-text-size.mjs";
import { games, deterministicStarts, start } from "./games.mjs";

const game = games.find(({ key }) => key === "conexiuni");
const messages = [
  "Alege patru cuvinte care merg împreună.",
  "Mai alege 3.",
  "Mai alege 2.",
  "Mai alege 1.",
  "Grup gata de verificat.",
];

for (const width of [320, 390]) for (const textScale of [1, 2]) {
  test(`selection and remaining mistakes never overlap at ${width}px and ${textScale * 100}% text`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await deterministicStarts(page, game);
    await start(page, game);
    if (textScale === 2) await applyDoubledText(page);
    await page.evaluate(() => globalThis.document.fonts.ready);
    const board = page.locator(".connections-grid");
    const frame = page.locator(".game-frame");
    const status = frame.locator(".game-frame-status");
    const coach = frame.locator(".coach-line");
    for (const [selected, message] of messages.entries()) {
      if (selected) await board.getByRole("button").nth(selected - 1).click();
      await expect(board.locator('button[aria-pressed="true"]')).toHaveCount(selected);
      await expect(coach).toHaveText(message);
      await expect(status.getByText("4 încercări", { exact: true })).toBeVisible();
      const boxes = await frame.evaluate((element) => {
        const band = element.querySelector(".game-frame-status");
        const coachLine = element.querySelector(".coach-line");
        const box = (part) => ({
          rect: part.getBoundingClientRect().toJSON(), client: part.clientWidth, scroll: part.scrollWidth,
        });
        return {
          frame: element.getBoundingClientRect().toJSON(), band: box(band), coach: box(coachLine),
          counters: [...band.children].map(box),
        };
      });
      const bounded = ({ rect, client, scroll }, parent) => {
        expect(rect.width).toBeGreaterThan(35);
        expect(rect.left).toBeGreaterThanOrEqual(parent.left);
        expect(rect.right).toBeLessThanOrEqual(parent.right);
        expect(scroll).toBeLessThanOrEqual(client + 1);
      };
      bounded(boxes.coach, boxes.frame);
      for (const counter of boxes.counters) bounded(counter, boxes.band.rect);
      expect(boxes.band.rect.bottom).toBeLessThanOrEqual(boxes.coach.rect.top);
      const [attempts, mode] = boxes.counters.map(({ rect }) => rect);
      expect(attempts.left < mode.right && mode.left < attempts.right &&
        attempts.top < mode.bottom && mode.top < attempts.bottom).toBe(false);
      expect(await page.locator(".connections-screen").evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
    }
  });
}
