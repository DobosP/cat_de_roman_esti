import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { applyDoubledText } from "./fixture-text-size.mjs";
import { games, solution, solve, start, tabTo } from "./games.mjs";

const day = "2026-11-16";
const place = { better_than_pct: 55, tier: "top_half", rounds: 1284 };
const labels = ["Perfect", "Top 10%", "Prima jumătate", "Ai reușit"];

async function fixDay(page) {
  await page.clock.setFixedTime(new Date(`${day}T10:00:00Z`));
}

// Keep the live moves and current result shape. Supply a valid enabled-server
// payload for this presentation check while the standard gate has counts off.
async function supplyPlace(page, game, action) {
  const suffix = "/" + action;
  const prefix = `/api/wordgames/${game.key}/games/`;
  await page.route((url) => url.pathname.startsWith(prefix) && url.pathname.endsWith(suffix), async (route) => {
    const response = await route.fetch();
    const result = await response.json();
    if (result.won) await route.fulfill({ response, json: { ...result, place } });
    else await route.fulfill({ response });
  });
}

for (const [key, action, colorScheme] of [["contexto", "guess", "light"], ["lant", "move", "dark"]]) {
  test(`${key} keeps the optional daily place from the winning response in ${colorScheme} mode`, async ({ page }) => {
    const game = { ...games.find((candidate) => candidate.key === key), daily: day };
    await page.emulateMedia({ colorScheme, reducedMotion: "reduce" });
    await page.setViewportSize({ width: 390, height: 844 });
    await fixDay(page);
    await supplyPlace(page, game, action);
    const initial = await start(page, game);
    expect(initial.daily).toBe(day);
    expect(initial.place).toBeUndefined();
    expect((await solve(page, game, solution(game).steps)).place).toEqual(place);
    const result = page.locator(".game-result");
    const availableLabels = key === "contexto" ? labels.slice(1) : labels;
    await expect(result.getByRole("heading", { level: 2 })).toBeFocused();
    await expect(result.getByRole("heading", { name: "Prima jumătate azi" })).toBeVisible();
    await expect(result.getByRole("img", { name: `Podium cu treptele ${availableLabels.join(", ")}. Treapta ta este Prima jumătate.` })).toBeVisible();
    await expect(result.locator(".board-place-label")).toHaveText(availableLabels);
    await expect(result.locator(".board-place-chart")).toHaveCSS("grid-template-columns",
      key === "contexto" ? /^(?:\S+\s+){2}\S+$/ : /^(?:\S+\s+){3}\S+$/);
    await expect(result.locator('[data-tier="top_10"] .board-place-bar')).toHaveCSS("height", "64px");
    await expect(result.locator('[data-tier="top_half"] .board-place-bar')).toHaveCSS("height", "46px");
    await expect(result.locator('[data-tier="completed"] .board-place-bar')).toHaveCSS("height", "30px");
    await expect(result.locator("[data-current] .board-place-label")).toHaveText("Prima jumătate");
    await expect(result.locator(".board-place-count")).toContainText("1.284 de runde încheiate");
    await expect(result).toContainText("Mai bine decât 55% dintre rundele încheiate pe tabla de azi.");

    await page.evaluate(() => document.fonts.ready);
    const audit = await new AxeBuilder({ page }).include(".game-result")
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(audit.violations.map(({ id, nodes }) => ({ id, targets: nodes.map(({ target }) => target) }))).toEqual([]);

    await page.setViewportSize({ width: 320, height: 844 });
    await applyDoubledText(page);
    const clippedLabels = await result.locator(".board-place-label").evaluateAll((items) =>
      items.filter((label) => {
        const { left, right } = label.getBoundingClientRect();
        return label.scrollWidth > label.clientWidth || left < 0 || right > innerWidth;
      }).map((label) => label.textContent),
    );
    expect(clippedLabels).toEqual([]);
    for (const name of ["Încă o rundă", "Înapoi la jocuri"]) {
      const button = result.getByRole("button", { name, exact: true });
      await tabTo(page, button);
      await expect(button).toBeInViewport();
    }

    await page.emulateMedia({ forcedColors: "active" });
    for (const bar of await result.locator(".board-place-bar").all()) {
      await expect(bar).toHaveCSS("border-top-style", "solid");
    }
  });
}

test("the standard gate's disabled counts do not render a podium", async ({ page }) => {
  const game = { ...games.find(({ key }) => key === "intrusul"), daily: day };
  await fixDay(page);
  await start(page, game);
  expect((await solve(page, game, solution(game).steps)).place).toBeUndefined();
  await expect(page.locator(".board-place")).toHaveCount(0);
});

test("a replay omits the podium even when the server sends a place", async ({ page }) => {
  const game = { ...games.find(({ key }) => key === "intrusul"), daily: day };
  await fixDay(page);
  await page.addInitScript((date) => {
    globalThis.localStorage.setItem("cat_daily_v2_intrusul", JSON.stringify({ [date]: 1 }));
  }, day);
  await supplyPlace(page, game, "guess");
  const replayRequest = page.waitForRequest((request) => request.method() === "POST" &&
    new URL(request.url()).pathname === "/api/wordgames/intrusul/games");
  await start(page, game);
  expect(new URL((await replayRequest).url()).searchParams.get("replay")).toBe("true");
  await expect(page.locator(".game-frame-mode")).toHaveText("Reluare");
  expect((await solve(page, game, solution(game).steps)).place).toEqual(place);
  await expect(page.locator(".board-place")).toHaveCount(0);
  await expect(page.locator(".game-result-perfect")).toHaveCount(0);
});
