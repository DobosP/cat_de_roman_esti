import { test, expect } from "@playwright/test";
import { applyDoubledText } from "./fixture-text-size.mjs";
import { games, gameURL, deterministicStarts, solution, start, act } from "./games.mjs";

const game = games.find(({ key }) => key === "contexto");
const field = (page) => page.getByRole("textbox", { name: "Concept de ghicit" });
const options = (page) => page.getByRole("button", { name: "Cum se joacă", exact: true });
const candidateWords = () => ["fotbal", "stilou", "București", "măr"]
  .filter((word) => word.toLowerCase() !== solution(game).steps.at(-1).payload.text.toLowerCase());

test.beforeEach(async ({ page }) => {
  await deterministicStarts(page, game);
});

test("one tap reaches the guess field with help and secondary tools tucked away", async ({ page }) => {
  await start(page, game);
  await expect(field(page)).toBeInViewport();
  expect((await field(page).boundingBox()).y).toBeLessThan(280);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Renunț la rundă și vreau să văd răspunsul" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Recente", exact: true })).not.toBeVisible();
  await expect(page.locator("#contexto-rank-guide")).toHaveText("Un număr mai mic = mai aproape. #1 este ținta.");
  await expect(page.getByRole("button", { name: "Indiciu", exact: true })).toBeEnabled();
  await expect(page.locator(".hint-bar")).toContainText("Costă un pas.");
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
  await page.getByRole("button", { name: "Trimite", exact: true }).click();
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
  await page.getByRole("button", { name: "Recente", exact: true }).click();
  await expect(page.locator("#contexto-guess-list .contexto-guess-row > strong:first-child").first())
    .toHaveText(latest.guess.label);
  await page.getByRole("button", { name: "Bune", exact: true }).click();
  await expect(page.locator("#contexto-guess-list .contexto-guess-row > strong:first-child")).toHaveText(rankOrder);
  await options(page).click();
  await page.getByRole("button", { name: "Renunț la rundă și vreau să văd răspunsul", exact: true }).click();
  const cancel = page.getByRole("button", { name: "Nu", exact: true });
  await expect(cancel).toBeFocused();
  await expect(cancel).toBeInViewport();
  await expect(page.getByRole("button", { name: "Da, arată", exact: true })).toBeVisible();
  const pending = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(pending.gave_up).toBe(false);
  expect(pending.attempts).toBe(2);
  await cancel.click();
  await expect(page.getByRole("button", { name: "Da, arată", exact: true })).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(field(page)).toBeEnabled();
  await expect(page.locator("#contexto-guess-list .contexto-guess-row")).toHaveCount(2);
});

test("the guess field and reveal confirmation stay usable at 320px with a short viewport and doubled text", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 480 });
  await start(page, game);
  await applyDoubledText(page);
  await expect(field(page)).toBeVisible();
  await expect(page.locator(".hint-bar")).toBeVisible();
  const overflow = await page.locator(".contexto-screen").evaluate((element) => ({
    scroll: element.scrollWidth, client: element.clientWidth,
  }));
  expect(overflow.scroll).toBeLessThanOrEqual(overflow.client + 1);
  await options(page).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Renunț la rundă și vreau să văd răspunsul", exact: true }).click();
  const cancel = page.getByRole("button", { name: "Nu", exact: true });
  await expect(cancel).toBeFocused();
  await expect(cancel).toBeInViewport();
  await expect(page.getByRole("button", { name: "Da, arată", exact: true })).toBeVisible();
  const expandedOverflow = await page.locator(".contexto-screen").evaluate((element) => ({
    scroll: element.scrollWidth, client: element.clientWidth,
  }));
  expect(expandedOverflow.scroll).toBeLessThanOrEqual(expandedOverflow.client + 1);
});

test("the help sheet traps focus, closes on Escape and returns to its trigger", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await start(page, game);
  await options(page).click();
  const help = page.getByRole("dialog", { name: /Cum se joacă Cald sau Rece/ });
  await expect(help).toBeVisible();
  await expect(help.getByRole("heading", { level: 2 })).toBeFocused();
  await expect(help.getByText("Un cuvânt cald, în primele 150 de locuri.")).toBeVisible();
  const first = help.getByRole("button", { name: "Închide ajutorul" });
  await first.focus();
  await page.keyboard.press("Shift+Tab");
  await expect(help.getByRole("button", { name: "Renunț la rundă și vreau să văd răspunsul" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(help).toHaveCount(0);
  await expect(options(page)).toBeFocused();
});

test("the hint button keeps its label inside a 44px target at 320px", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 640 });
  await start(page, game);
  const clue = page.getByRole("button", { name: "Indiciu", exact: true });
  await expect(clue).toBeVisible();
  const fit = await clue.evaluate((element) => {
    const range = globalThis.document.createRange();
    range.selectNodeContents(element);
    const box = element.getBoundingClientRect();
    const text = range.getBoundingClientRect();
    return {
      scroll: element.scrollWidth, client: element.clientWidth, height: box.height,
      textInside: text.left >= box.left && text.right <= box.right && text.top >= box.top && text.bottom <= box.bottom,
    };
  });
  await test.info().attach("clue-fit", { body: JSON.stringify(fit, null, 2), contentType: "application/json" });
  expect(fit.scroll).toBeLessThanOrEqual(fit.client + 1);
  expect(fit.textInside).toBe(true);
  expect(fit.height).toBeGreaterThanOrEqual(44);
});
