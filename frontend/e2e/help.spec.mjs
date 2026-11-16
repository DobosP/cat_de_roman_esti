import { test, expect } from "@playwright/test";
import { GAME_HELP } from "../src/gameHelp.mjs";
import { games, gameURL, deterministicStarts, tabTo, start, act, solution, openAlchemyDisclosure } from "./games.mjs";

for (const game of games) {
  test(`${game.key} rules preserve the round and focused choices`, async ({ page, request }, testInfo) => {
    await deterministicStarts(page, game);
    const initial = await start(page, game);
    const toggle = page.getByRole("button", { name: "Cum se joacă", exact: true });
    const help = page.getByRole("dialog", { name: /Cum se joacă/ });
    await expect(help).toHaveCount(0);

    // A ready selection used to make global Enter handlers consume the help key.
    const selectedCount = { alchimie: 1, conexiuni: 4, perechi: 1 }[game.key] ?? 0;
    const selectable = game.key === "alchimie"
      ? page.locator(game.board).getByRole("button", { disabled: false })
      : page.locator(game.board).getByRole("button");
    for (let index = 0; index < selectedCount; index += 1) {
      await selectable.nth(index).click();
    }
    if (["contexto", "lant"].includes(game.key)) {
      await page.locator(game.board).fill("curiozitate");
    }
    const posts = [];
    page.on("request", (request) => {
      if (request.method() === "POST" && request.url().includes("/api/wordgames/")) posts.push(request.url());
    });
    const keyboard = testInfo.project.name === "desktop";
    if (keyboard) {
      await tabTo(page, toggle);
      await page.keyboard.press("Enter");
    } else {
      await toggle.click();
    }
    await expect(help).toBeVisible();
    await expect(help.locator(".game-help-instructions > li")).toHaveText([
      GAME_HELP[game.key].goal, GAME_HELP[game.key].feedback, GAME_HELP[game.key].recovery,
    ]);
    await expect(help.locator(".game-help-ladder > li")).toHaveText(GAME_HELP[game.key].ladder);
    await expect(help.getByText(GAME_HELP[game.key].steps, { exact: true })).toBeVisible();
    expect((await toggle.boundingBox()).height).toBeGreaterThanOrEqual(44);
    const width = await page.evaluate(() => ({
      content: globalThis.document.documentElement.scrollWidth, viewport: globalThis.innerWidth,
    }));
    expect(width.content).toBeLessThanOrEqual(width.viewport);
    const current = await request.get(gameURL(game, initial.game_id));
    expect(await current.json()).toEqual(initial);
    if (keyboard) await page.keyboard.press("Escape");
    else await help.getByRole("button", { name: "Închide ajutorul" }).click();
    await expect(help).toHaveCount(0);
    await expect(toggle).toBeFocused();
    expect(posts).toEqual([]);
    if (selectedCount) {
      await expect(page.locator(game.board).locator('[aria-pressed="true"]')).toHaveCount(selectedCount);
    }
    if (["contexto", "lant"].includes(game.key)) {
      await expect(page.locator(game.board)).toHaveValue("curiozitate");
    }
  });
}

test("Alchimie shows earned connection directions and keeps them after reload", async ({ page }) => {
  const game = games.find((entry) => entry.key === "alchimie");
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  await expect(page.locator(".alchemy-earned-links")).toHaveCount(0);
  const response = await act(page, game, solution(game).practice);
  expect(response.status()).toBe(200);
  const earned = await response.json();
  const items = earned.inventory.filter((item) => item.links.length > 0);
  expect(items.length).toBeGreaterThan(0);
  async function visibleLinks() {
    await openAlchemyDisclosure(page, ".alchemy-discoveries");
    for (const item of items) {
      const evidence = page.locator(".alchemy-earned-links").filter({
        has: page.getByText(`Legături descoperite: ${item.label}`, { exact: true }),
      });
      for (const link of item.links) {
        await expect(evidence.getByRole("listitem").filter({
          hasText: `${link.source.label} — ${link.label} → ${link.target.label}`,
        })).toBeVisible();
      }
    }
  }
  await visibleLinks();
  const resumed = page.waitForResponse((result) => result.request().method() === "GET" &&
    new URL(result.url()).pathname === gameURL(game, initial.game_id)).then((result) => result.json());
  const [restored] = await Promise.all([resumed, page.reload()]);
  expect(restored.inventory).toEqual(earned.inventory);
  await visibleLinks();
});
