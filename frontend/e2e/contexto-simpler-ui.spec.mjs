import { test, expect } from "@playwright/test";
import { games, gameURL, deterministicStarts, solution, start, act } from "./games.mjs";

const game = games.find(({ key }) => key === "contexto");
const field = (page) => page.getByRole("textbox", { name: "Concept de ghicit" });
const options = (page) => page.locator(".game-options > summary");
const candidateWords = () => ["fotbal", "stilou", "București", "măr"]
  .filter((word) => word.toLowerCase() !== solution(game).steps.at(-1).payload.text.toLowerCase());

test.beforeEach(async ({ page }) => {
  await deterministicStarts(page, game);
});

test("one start reaches the guess field with setup and secondary tools tucked away", async ({ page }) => {
  await page.goto(game.path);
  await expect(page.locator(".game-setup-options")).not.toHaveAttribute("open", "");
  await expect(page.getByRole("button", { name: "Normal", exact: true })).not.toBeVisible();
  await start(page, game);
  await expect(field(page)).toBeInViewport();
  expect((await field(page).boundingBox()).y).toBeLessThan(280);
  await expect(page.locator(".game-options")).not.toHaveAttribute("open", "");
  await expect(page.getByRole("button", { name: "Răspuns", exact: true })).not.toBeVisible();
  await expect(page.getByRole("button", { name: "Recente", exact: true })).not.toBeVisible();
  await expect(page.locator("#contexto-rank-guide")).toHaveText("Un număr mai mic = mai aproape. #1 este ținta.");
  await expect(page.getByRole("button", { name: "Cum citesc #?", exact: true })).toHaveCount(0);
  await expect(page.locator("#contexto-clue-cost")).toBeVisible();
  await expect(page.getByRole("button", { name: "Indiciu în 3", exact: true }))
    .toHaveAccessibleDescription("−120 puncte / indiciu");
});

test("Enter and the submit button both leave the field ready for the next guess", async ({ page }) => {
  const initial = await start(page, game);
  const [first, second] = candidateWords();
  const firstReply = await act(page, game, { action: "guess", payload: { text: first } });
  const firstResult = await firstReply.json();
  expect(firstResult.attempts).toBe(1);
  await expect(field(page)).toBeFocused();
  await expect(field(page)).toHaveValue("");
  await expect(page.locator("#contexto-guess-list")).toContainText(firstResult.guess.label);

  await field(page).fill(second);
  const secondReply = page.waitForResponse((response) =>
    response.request().method() === "POST" && new URL(response.url()).pathname === `${gameURL(game, initial.game_id)}/guess`);
  await page.getByRole("button", { name: "Ghicește", exact: true }).click();
  expect((await (await secondReply).json()).attempts).toBe(2);
  await expect(field(page)).toBeFocused();
  await expect(field(page)).toHaveValue("");
  await expect(page.locator("#contexto-guess-list .contexto-guess-row")).toHaveCount(2);
});

test("a delayed guess preserves focus moved deliberately into game options", async ({ page }) => {
  const initial = await start(page, game);
  let release;
  let signalRequest;
  const held = new Promise((resolve) => { release = resolve; });
  const requested = new Promise((resolve) => { signalRequest = resolve; });
  await page.route(`**${gameURL(game, initial.game_id)}/guess`, async (route) => {
    const response = await route.fetch();
    signalRequest();
    await held;
    await route.fulfill({ response });
  }, { times: 1 });
  await field(page).fill(candidateWords()[0]);
  await field(page).press("Enter");
  await requested;
  await expect(field(page)).toBeDisabled();
  await options(page).focus();
  await expect(options(page)).toBeFocused();
  release();
  await expect(field(page)).toBeEnabled();
  await expect(options(page)).toBeFocused();
});

test("the options menu preserves explicit reveal confirmation and optional recent ordering", async ({ page, request }) => {
  const initial = await start(page, game);
  let latest;
  for (const text of candidateWords().slice(0, 2)) {
    latest = await (await act(page, game, { action: "guess", payload: { text } })).json();
    await expect(field(page)).toBeEnabled();
  }
  const rankOrder = latest.guesses.map((guess) => guess.label);
  await options(page).click();
  await page.getByRole("button", { name: "Recente", exact: true }).click();
  await expect(page.locator("#contexto-guess-list .contexto-guess-row strong").first())
    .toHaveText(latest.guess.label);
  await page.getByRole("button", { name: "Bune", exact: true }).click();
  await expect(page.locator("#contexto-guess-list .contexto-guess-row strong")).toHaveText(rankOrder);
  await page.getByRole("button", { name: "Răspuns", exact: true }).click();
  const cancel = page.getByRole("button", { name: "Nu", exact: true });
  await expect(cancel).toBeFocused();
  await expect(cancel).toBeInViewport();
  await expect(page.getByRole("button", { name: "Da, arată", exact: true })).toBeVisible();
  const pending = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(pending.gave_up).toBe(false);
  expect(pending.attempts).toBe(2);
  await cancel.click();
  await expect(page.getByRole("button", { name: "Da, arată", exact: true })).toHaveCount(0);
  await options(page).click();
  await expect(field(page)).toBeEnabled();
  await expect(page.locator("#contexto-guess-list .contexto-guess-row")).toHaveCount(2);
});

test("the guess field and reveal confirmation stay usable at 320px with a short viewport and doubled text", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 480 });
  await start(page, game);
  await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
  await expect(field(page)).toBeVisible();
  await expect(page.locator("#contexto-clue-cost")).toBeVisible();
  const overflow = await page.locator(".contexto-screen").evaluate((element) => ({
    scroll: element.scrollWidth, client: element.clientWidth,
  }));
  expect(overflow.scroll).toBeLessThanOrEqual(overflow.client + 1);
  await options(page).click();
  await expect(page.getByRole("button", { name: "Începe alt joc", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Răspuns", exact: true }).click();
  const cancel = page.getByRole("button", { name: "Nu", exact: true });
  await expect(cancel).toBeFocused();
  await expect(cancel).toBeInViewport();
  await expect(page.getByRole("button", { name: "Da, arată", exact: true })).toBeVisible();
  const expandedOverflow = await page.locator(".contexto-screen").evaluate((element) => ({
    scroll: element.scrollWidth, client: element.clientWidth,
  }));
  expect(expandedOverflow.scroll).toBeLessThanOrEqual(expandedOverflow.client + 1);
});
