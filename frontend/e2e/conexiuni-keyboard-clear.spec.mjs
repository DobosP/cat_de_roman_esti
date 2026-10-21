// KFA-1: browser replacement for the retired source check
// persistent-game-navigation.test.mjs "Escape still clears a Conexiuni selection".
import { test, expect } from "@playwright/test";
import { games, gameURL, deterministicStarts, solution, start } from "./games.mjs";

const game = games.find(({ key }) => key === "conexiuni");
const pressed = (page) => page.locator(`${game.board} button[aria-pressed="true"]`);

test("Escape and Backspace each clear a live selection without spending a move", async ({ page }) => {
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const labels = solution(game).steps[0].labels.slice(0, 2);
  const mutations = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname.startsWith(`${gameURL(game, initial.game_id)}/`)) {
      mutations.push(request.url());
    }
  });
  const choose = async () => {
    for (const label of labels) {
      await page.locator(game.board).getByRole("button", { name: label, exact: true }).click();
    }
    await expect(pressed(page)).toHaveCount(2);
    await expect(page.locator(game.board).getByRole("button", { name: labels[1], exact: true })).toBeFocused();
  };

  await choose();
  await page.keyboard.press("Escape");
  await expect(pressed(page)).toHaveCount(0);

  await choose();
  await page.keyboard.press("Backspace");
  await expect(pressed(page)).toHaveCount(0);

  await expect(page.locator(`${game.board} button`)).toHaveCount(16);
  await expect(page.getByRole("button", { name: "Verifică", exact: true })).toBeDisabled();
  expect(mutations).toEqual([]);
});
