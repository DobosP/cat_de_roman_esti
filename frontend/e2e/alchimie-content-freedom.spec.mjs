import { test, expect } from "@playwright/test";
import { games, deterministicStarts, start } from "./games.mjs";

const game = games.find(({ key }) => key === "alchimie");
const word = (page, label) => page.locator(game.board).getByRole("button", {
  name: new RegExp(`^${label}(?:,|$)`),
});
const activate = (button) => test.info().project.name === "mobile" ? button.tap() : button.click();
const reply = (page) => page.waitForResponse((response) => response.request().method() === "POST"
  && new URL(response.url()).pathname.endsWith("/combine"));

test.beforeEach(async ({ page }) => deterministicStarts(page, game));

for (const [left, right] of [
  ["Dinamo București", "Rapid București"],
  ["Dinamo București", "CFR Cluj"],
  ["CFR Cluj", "FCSB"],
]) {
  test(`${left} and ${right} now have the same coherent club recipe`, async ({ page }) => {
    const initial = await start(page, game);
    expect(initial.recipe_summary.pairs).toBe(9);
    await activate(word(page, left));
    const first = reply(page);
    await activate(word(page, right));
    const crafted = await (await first).json();
    expect(crafted.discovered.map((item) => item.label)).toEqual(["Club sportiv"]);
    expect(crafted.target.id).toBeNull();
    expect(crafted.recipes).toBeUndefined();
    expect(crafted.routes).toBeUndefined();
    await expect(page.getByRole("button", { name: "Scoate Club sportiv din alambic" })).toBeVisible();
    const last = reply(page);
    await activate(word(page, "Cristina Neagu"));
    const won = await (await last).json();
    expect(won.won).toBe(true);
    expect(won.moves).toBe(2);
    expect(won.score).toBe(1000);
  });
}

test("empty experiments stay free while a real two-craft solution still completes", async ({ page }) => {
  await start(page, game);
  await activate(word(page, "Cristina Neagu"));
  for (const partner of ["Dinamo București", "Rapid București", "FCSB"]) {
    const empty = reply(page);
    await activate(word(page, partner));
    const result = await (await empty).json();
    expect(result.discovered).toEqual([]);
    await expect(page.locator(".alchemy-feedback")).toContainText("Fără penalizare.");
    await expect(page.getByRole("button", { name: "Scoate Cristina Neagu din alambic" })).toBeVisible();
  }
  const first = reply(page);
  await activate(word(page, "Echipă națională"));
  expect((await (await first).json()).discovered.map((item) => item.label)).toContain("Handbal feminin");
  await expect(page.getByRole("button", { name: "Scoate Handbal feminin din alambic" })).toBeVisible();
  const last = reply(page);
  await activate(word(page, "Cristina Neagu"));
  const won = await (await last).json();
  expect(won.won).toBe(true);
  expect(won.moves).toBe(5);
  expect(won.hints_used).toBe(0);
  expect(won.score).toBe(1000);
});
