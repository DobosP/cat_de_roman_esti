// Final mapped recovery lifecycle replacements. Authored NOT RUN. Every game,
// reply, correction message and score below must come from the real native API.
// Native policy confirms non-target corrections; a correction to the TARGET is
// accepted directly, so no fictional confirmation-token target branch is used.
import { test, expect } from "@playwright/test";
import { games, gameURL, deterministicStarts, solution, start, act, openGameOptions } from "./games.mjs";

const game = games.find(({ key }) => key === "contexto");
const field = (page) => page.getByRole("textbox", { name: "Concept de ghicit", exact: true });
const rejectedWord = "qqqqno_such_word";
const responseFor = (page, id, action, method = "POST") => page.waitForResponse((response) =>
  response.request().method() === method && new URL(response.url()).pathname === `${gameURL(game, id)}${action ? `/${action}` : ""}`);
function traffic(page) {
  const mutations = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname.startsWith("/api/wordgames/contexto/games/")) {
      mutations.push({ path: new URL(request.url()).pathname, ...(request.url().endsWith("/guess") ? { body: request.postDataJSON() } : {}) });
    }
  });
  return mutations;
}
async function nativeGuess(page, text) {
  const response = await act(page, game, { action: "guess", payload: { text } });
  expect(response.status()).toBe(200); const body = await response.json();
  await expect(field(page)).toBeEnabled(); return body;
}
const recoveryCard = (page, message) => page.locator(".contexto-screen .card").filter({ hasText: message });
async function recovery(page) {
  const rejected = await nativeGuess(page, rejectedWord);
  expect(rejected.ok).toBe(false); expect(rejected.won).toBe(false);
  expect(typeof rejected.message).toBe("string");
  await expect(field(page)).toHaveValue(rejectedWord);
  await expect(recoveryCard(page, rejected.message)).toBeVisible();
  await expect(page.getByRole("status").filter({ hasText: rejected.message })).toHaveCount(1);
  return rejected;
}
async function cleared(page, message) {
  await expect(recoveryCard(page, message)).toHaveCount(0);
  await expect(page.getByRole("status").filter({ hasText: message })).toHaveCount(0);
}
test.beforeEach(async ({ page }) => deterministicStarts(page, game));

test("a real corrected target win retains the actual server correction message in the result owner", async ({ page }) => {
  // Existing native differential fixture: unthemed/usor seed-31 reveals
  // Las Fierbinți. A one-character omission exercises the real fuzzy resolver.
  await page.route("**/api/wordgames/contexto/games?*", async (route) => {
    const url = new URL(route.request().url()); url.searchParams.set("seed", "-31");
    await route.continue({ url: url.toString() });
  });
  const initial = await start(page, game), mutations = traffic(page), typed = "Las Fierbinț";
  const response = await act(page, game, { action: "guess", payload: { text: typed } });
  expect(response.status()).toBe(200); const won = await response.json();
  expect(won.ok).toBe(true); expect(won.won).toBe(true);
  expect(won.target.label).toBe("Las Fierbinți"); expect(won.guess.label).toBe(won.target.label);
  expect(typeof won.message).toBe("string"); expect(won.message.length).toBeGreaterThan(0);
  expect(won.message).toBe(`Am înțeles: ${won.target.label}.`);
  expect(won).not.toHaveProperty("needs_confirmation");
  expect(mutations).toEqual([{ path: `${gameURL(game, initial.game_id)}/guess`, body: { text: typed } }]);
  const heading = page.getByRole("heading", { name: "Ai găsit conceptul!", exact: true });
  await expect(heading).toBeVisible();
  const result = page.getByRole("status").filter({ has: heading });
  await expect(result).toHaveCount(1);
  await expect(result).toContainText(won.message);
  await expect(result.locator("span.muted").filter({ hasText: won.message })).toHaveCount(1);
  await expect(page.locator(".contexto-confirm-chip")).toHaveCount(0);
  await expect(field(page)).toHaveValue(""); await expect(field(page)).toBeDisabled();
});

test("Escape clears actual unknown recovery and text without posting another guess", async ({ page, request }) => {
  const initial = await start(page, game), mutations = traffic(page), rejected = await recovery(page);
  expect(mutations).toHaveLength(1);
  await field(page).press("Escape");
  await expect(field(page)).toHaveValue(""); await cleared(page, rejected.message);
  expect(mutations).toHaveLength(1);
  const current = await request.get(gameURL(game, initial.game_id)); expect(current.status()).toBe(200);
  expect((await current.json()).attempts).toBe(rejected.attempts);
});

test("owned resume clears obsolete recovery and text while retaining the exact native round", async ({ page }) => {
  const initial = await start(page, game), mutations = traffic(page), rejected = await recovery(page);
  const resumed = responseFor(page, initial.game_id, "", "GET");
  await page.reload(); const response = await resumed; expect(response.status()).toBe(200); const state = await response.json();
  expect(state.game_id).toBe(initial.game_id); expect(state.attempts).toBe(rejected.attempts);
  await expect(field(page)).toBeEnabled(); await expect(field(page)).toHaveValue("");
  await cleared(page, rejected.message); expect(mutations).toHaveLength(1);
});

test("a real paid clue clears obsolete unknown recovery without converting it to another toast", async ({ page }) => {
  const initial = await start(page, game);
  const target = solution(game).steps.at(-1).payload.text.toLocaleLowerCase("ro-RO");
  for (const text of ["fotbal", "stilou", "București", "măr"].filter((word) => word.toLocaleLowerCase("ro-RO") !== target).slice(0, 3)) {
    const accepted = await nativeGuess(page, text); expect(accepted.ok).toBe(true); expect(accepted.won).toBe(false);
  }
  const rejected = await recovery(page), mutations = traffic(page);
  expect(rejected.clue_available).toBe(true);
  const response = responseFor(page, initial.game_id, "clue");
  await page.getByRole("button", { name: "Indiciu", exact: true }).click();
  const received = await response; expect(received.status()).toBe(200); const state = await received.json();
  expect(state.game_id).toBe(initial.game_id); expect(state.clues_used).toBe(rejected.clues_used + 1);
  expect(state.attempts).toBe(rejected.attempts); expect(state.won).toBe(false);
  await expect(page.getByLabel("Indicii folosite", { exact: true })).toBeVisible();
  await cleared(page, rejected.message);
  expect(mutations.map(({ path }) => path)).toEqual([`${gameURL(game, initial.game_id)}/clue`]);
});

test("real giveup clears obsolete unknown recovery from the terminal result without posting another guess", async ({ page }) => {
  const initial = await start(page, game), rejected = await recovery(page), mutations = traffic(page);
  await openGameOptions(page, game);
  await page.getByRole("button", { name: "Arată răspunsul", exact: true }).click();
  const response = responseFor(page, initial.game_id, "giveup");
  await page.getByRole("button", { name: "Da, arată", exact: true }).click();
  const received = await response; expect(received.status()).toBe(200); const state = await received.json();
  expect(state.game_id).toBe(initial.game_id); expect(state.gave_up).toBe(true); expect(state.won).toBe(false);
  const heading = page.getByRole("heading", { name: "Conceptul secret era:", exact: true });
  await expect(heading).toBeVisible();
  await expect(page.getByRole("status").filter({ has: heading })).not.toContainText(rejected.message);
  await cleared(page, rejected.message);
  expect(mutations.map(({ path }) => path)).toEqual([`${gameURL(game, initial.game_id)}/giveup`]);
});
