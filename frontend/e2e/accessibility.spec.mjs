import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { games, deterministicStarts, start, solve, solution } from "./games.mjs";

async function accessible(page, testInfo, state) {
  // Audit settled colors, not a transient frame of a Framer Motion opacity fade.
  await expect.poll(() => page.locator("button.roedu-btn--primary:not(:disabled)").evaluateAll((buttons) =>
    buttons.every((button) => {
      for (let element = button; element; element = element.parentElement) {
        if (Number(globalThis.getComputedStyle(element).opacity) < 0.999) return false;
      }
      return true;
    }),
  )).toBe(true);
  await page.evaluate(async () => {
    await globalThis.document.fonts.ready;
    await Promise.all(globalThis.document.getAnimations().filter((animation) =>
      Number.isFinite(animation.effect?.getComputedTiming().endTime),
    ).map((animation) => animation.finished.catch(() => {})));
  });
  const audit = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  const violations = audit.violations.map(({ id, impact, nodes }) => ({
    id, impact, nodes: nodes.map(({ target, failureSummary }) => ({ target, failureSummary })),
  }));
  await testInfo.attach(`${state}-accessibility`, {
    body: JSON.stringify(violations, null, 2), contentType: "application/json",
  });
  expect.soft(violations, `${state} WCAG A/AA violations`).toEqual([]);
  const width = await page.evaluate(() => ({
    content: globalThis.document.documentElement.scrollWidth, viewport: globalThis.innerWidth,
  }));
  expect.soft(width.content, `${state} should fit viewport`).toBeLessThanOrEqual(width.viewport);
}

for (const game of games) {
  test(`${game.key} intro, live board and result are accessible without page overflow`, async ({ page }, testInfo) => {
    await deterministicStarts(page, game);
    await page.goto(game.path);
    await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
    await accessible(page, testInfo, "intro");
    const controls = { keyboard: testInfo.project.name === "desktop" };
    await start(page, game, controls);
    await accessible(page, testInfo, "live");
    await solve(page, game, solution(game).steps, controls);
    await accessible(page, testInfo, "result");
  });
}
