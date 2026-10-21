// KFA-1: browser replacement for the retired source check
// lant-recovery-feedback.test.mjs "Lanț announces the new position".
import { test, expect } from "@playwright/test";
import { games, deterministicStarts, solution, start, act } from "./games.mjs";

const game = games.find(({ key }) => key === "lant");

test("the current position is a polite atomic live region on a live board and silent after the win", async ({ page }) => {
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const current = page.locator(".lant-current");
  const live = async (label) => {
    await expect(current).toHaveCount(1);
    await expect(current.locator(".lant-route-word")).toHaveText(label);
    await expect(current).toHaveAttribute("aria-live", "polite");
    await expect(current).toHaveAttribute("aria-atomic", "true");
  };

  await live(initial.current.label);
  const steps = solution(game).steps;
  for (const step of steps.slice(0, -1)) {
    const response = await act(page, game, step);
    expect(response.status()).toBe(200);
    const moved = await response.json();
    expect(moved.won).toBe(false);
    await live(moved.current.label);
  }

  const response = await act(page, game, steps.at(-1));
  expect(response.status()).toBe(200);
  const won = await response.json();
  expect(won.won).toBe(true);
  await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
  await expect(current).toHaveCount(1);
  await expect(current.locator(".lant-route-word")).toHaveText(won.current.label);
  await expect(current).toHaveAttribute("aria-live", "off");
  await expect(current).toHaveAttribute("aria-atomic", "true");
});
