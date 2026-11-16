import { test, expect } from "@playwright/test";
import { games, deterministicStarts, solution, start } from "./games.mjs";

const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

test("a lost first Intrusul round is history, never a record", async ({ page }) => {
  const game = games.find(({ key }) => key === "intrusul");
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const intruder = solution(game).steps[0].payload.id;
  for (const tile of initial.tiles.filter(({ id }) => id !== intruder)) {
    await page.locator(game.board).getByRole("button", {
      name: new RegExp(`^${escapeRegex(tile.label)}(?:,|$)`),
    }).click();
  }
  await expect(page.getByRole("heading", { name: "Nu a ieșit de data asta" })).toBeVisible();
  // Wait for the local history write so a late completion cannot slip past the check.
  await expect.poll(() => page.evaluate(() =>
    JSON.parse(localStorage.getItem("cat_wordgame_scores_v1") || "{}").intrusul?.played ?? 0,
  )).toBe(1);
  await expect(page.getByText("Perfect", { exact: true })).toHaveCount(0);
  await expect(page.locator(".game-result")).toContainText("3 pași");
  expect(await page.evaluate(() =>
    JSON.parse(localStorage.getItem("cat_wordgame_scores_v1")).intrusul.best,
  )).toBeNull();
});
