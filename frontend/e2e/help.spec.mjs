import { test, expect } from "@playwright/test";
import { GAME_HELP } from "../src/gameHelp.mjs";
import { games, gameURL, deterministicStarts, tabTo, start, act, solution, openAlchemyDisclosure, openGameOptions } from "./games.mjs";

for (const game of games) {
  test(`${game.key} rules preserve the round and focused choices`, async ({ page, request }, testInfo) => {
    // Observe the fresh intro before registering the deterministic create route.
    await page.goto(game.path);
    const intro = page.locator(".game-intro");
    await expect(intro).toBeVisible();
    const guide = intro.getByRole("list", { name: "Cum joci", exact: true });
    await expect(guide).toHaveJSProperty("tagName", "OL");
    const guideItems = guide.locator(":scope > li");
    await expect(guideItems).toHaveCount(3);
    const guideLabels = {
      alchimie: ["Atinge un cuvânt", "Atinge altul", "Descoperă automat"],
      intrusul: ["Privește cele patru", "Atinge intrusul", "Descoperă legătura"],
      perechi: ["Atinge un cuvânt", "Atinge perechea", "Găsește-le pe toate"],
      conexiuni: ["Alege patru", "Verifică", "Găsește grupul"],
      contexto: ["Scrie un cuvânt", "Vezi căldura", "Apropie-te"],
      lant: ["Alege o legătură", "Fă un salt", "Ajungi la țintă"],
    }[game.key];
    for (const [index, label] of guideLabels.entries()) {
      await expect(guideItems.nth(index).getByText(label, { exact: true })).toBeVisible();
    }
    if (["alchimie", "contexto", "lant", "conexiuni"].includes(game.key)) {
      await openGameOptions(page, game, { setup: true });
      const difficulty = intro.getByRole("group", { name: "DIFICULTATE", exact: true });
      await expect(difficulty.getByRole("button", { pressed: true })).toHaveCount(1);
      await expect(difficulty.getByRole("button", { name: /^Ușor(?:\s|$)/ })).toHaveAttribute("aria-pressed", "true");
    }
    await deterministicStarts(page, game);
    const initial = await start(page, game);
    const help = page.locator("details.game-help");
    const toggle = help.locator("summary");
    await expect(help).not.toHaveAttribute("open");
    await expect(toggle).toBeVisible();
    expect(await help.evaluate((element) => element.parentElement.closest("details"))).toBeNull();

    // A ready selection used to make global Enter handlers consume the help key.
    const selectedCount = { alchimie: 1, conexiuni: 4, perechi: 1 }[game.key] ?? 0;
    for (let index = 0; index < selectedCount; index += 1) {
      await page.locator(game.board).getByRole("button").nth(index).click();
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
    await expect(help).toHaveAttribute("open", "");
    for (const copy of Object.values(GAME_HELP[game.key])) {
      await expect(help.getByText(copy, { exact: true })).toBeVisible();
    }
    expect((await toggle.boundingBox()).height).toBeGreaterThanOrEqual(44);
    const width = await page.evaluate(() => ({
      content: globalThis.document.documentElement.scrollWidth, viewport: globalThis.innerWidth,
    }));
    expect(width.content).toBeLessThanOrEqual(width.viewport);
    const current = await request.get(gameURL(game, initial.game_id));
    expect(await current.json()).toEqual(initial);
    if (keyboard) await page.keyboard.press("Space");
    else await toggle.click();
    await expect(help).not.toHaveAttribute("open");
    await expect(toggle).toBeVisible();
    expect(await help.evaluate((element) => element.parentElement.closest("details"))).toBeNull();
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
