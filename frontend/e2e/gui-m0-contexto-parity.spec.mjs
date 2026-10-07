// Authored NOT RUN. Native requests exercise the real CaldRece app. The two
// labelled public-field projections qualify presentation only, not backend
// suggestion/temperature decisions. Touch emulation is not a device checkpoint.
import { test, expect } from "@playwright/test";
import { games, gameURL, deterministicStarts, solution, start, act, openGameOptions } from "./games.mjs";

test.use({ hasTouch: true });
const game = games.find(({ key }) => key === "contexto");
const field = (page) => page.getByRole("textbox", { name: "Concept de ghicit", exact: true });
const clueCards = (page) => page.getByLabel("Indicii folosite", { exact: true });
const confirmation = (page) => page.locator("#contexto-reveal-confirmation");
const answer = () => solution(game).steps.at(-1);
const safeWords = () => ["fotbal", "stilou", "București", "măr"].filter((word) =>
  word.toLocaleLowerCase("ro-RO") !== answer().payload.text.toLocaleLowerCase("ro-RO"));
const reply = (page, id, action) => page.waitForResponse((response) =>
  response.request().method() === "POST" && new URL(response.url()).pathname === `${gameURL(game, id)}/${action}`);

function traffic(page) {
  const mutations = [];
  page.on("request", (request) => {
    const pathname = new URL(request.url()).pathname;
    if (request.method() === "POST" && pathname.startsWith("/api/wordgames/contexto/games/")) {
      mutations.push({ pathname, ...(pathname.endsWith("/guess") ? { body: request.postDataJSON() } : {}) });
    }
  });
  return mutations;
}
async function guess(page, text) {
  const response = await act(page, game, { action: "guess", payload: { text } });
  expect(response.status()).toBe(200);
  const body = await response.json();
  await expect(field(page)).toBeEnabled();
  return body;
}
async function categoryStage(page) {
  const initial = await start(page, game);
  for (const word of safeWords().slice(0, 3)) {
    const accepted = await guess(page, word);
    expect(accepted.ok).toBe(true); expect(accepted.won).toBe(false);
  }
  const response = reply(page, initial.game_id, "clue");
  await page.getByRole("button", { name: "Indiciu", exact: true }).click();
  const received = await response;
  expect(received.status()).toBe(200);
  const state = await received.json();
  expect(state.clue_kind).toBe("category");
  expect(state.clue_available).toBe(true);
  return { initial, state };
}
async function armReveal(page) {
  await openGameOptions(page, game);
  await page.getByRole("button", { name: "Arată răspunsul", exact: true }).click();
  await expect(confirmation(page)).toBeVisible();
}
async function projectionNote(testInfo, kind, original, fields) {
  await testInfo.attach(`contexto-${kind}-presentation-scope`, {
    body: JSON.stringify({ scope: "NON-NATIVE public-field DOM presentation projection", kind,
      real_game_id: original.game_id ?? null, real_guess_id: original.guess?.id ?? null,
      projected_fields: fields, validates_backend_decision: false }, null, 2),
    contentType: "application/json",
  });
}

test.beforeEach(async ({ page }) => deterministicStarts(page, game));

test("real warmer clue clears armed reveal, fills safely on coarse pointer and survives accepted/rejected guesses", async ({ page, request }) => {
  expect(await page.evaluate(() => matchMedia("(pointer: coarse)").matches)).toBe(true);
  const { initial, state } = await categoryStage(page);
  const mutations = traffic(page);
  await armReveal(page);
  const response = reply(page, initial.game_id, "clue");
  await page.getByRole("button", { name: "Mai cald", exact: true }).click();
  const received = await response;
  expect(received.status()).toBe(200);
  const warm = await received.json();
  expect(warm.game_id).toBe(initial.game_id);
  expect(warm.clue_kind).toBe("warmer");
  expect(warm.word).toEqual(warm.warm_clue);
  expect(warm.warm_clue.rank).toBeGreaterThan(1);
  expect(warm.clues_used).toBe(state.clues_used + 1);
  expect(warm).not.toHaveProperty("target");
  await expect(confirmation(page)).toHaveCount(0);
  await expect(clueCards(page)).toHaveCount(1);
  await expect(clueCards(page)).toHaveAttribute("aria-live", "polite");
  await expect(clueCards(page)).toContainText(state.clue.category.label);
  await expect(clueCards(page)).toContainText(`#${warm.warm_clue.rank}`);
  const fill = page.getByRole("button", { name: `Pune ${warm.warm_clue.label} în câmpul de răspuns`, exact: true });
  await expect(fill).toBeVisible();
  expect((await fill.boundingBox()).height).toBeGreaterThanOrEqual(44);
  const options = page.locator(".game-options > summary");
  await options.focus(); await expect(options).toBeFocused();
  const beforeFill = mutations.length;
  await fill.tap();
  await expect(field(page)).toHaveValue(warm.warm_clue.label);
  await expect(field(page)).not.toBeFocused();
  expect(mutations).toHaveLength(beforeFill);
  const untouched = await request.get(gameURL(game, initial.game_id));
  expect(untouched.status()).toBe(200);
  expect((await untouched.json()).attempts).toBe(warm.attempts);
  const accepted = await guess(page, warm.warm_clue.label);
  expect(accepted.ok).toBe(true); expect(accepted.won).toBe(false);
  expect(accepted.attempts).toBe(warm.attempts + 1);
  await expect(clueCards(page)).toContainText(state.clue.category.label);
  await expect(fill).toBeVisible();
  const rejected = await guess(page, "qqqqno_such_word");
  expect(rejected.ok).toBe(false);
  expect(rejected.attempts).toBe(accepted.attempts);
  expect(rejected.clues_used).toBe(warm.clues_used);
  await expect(field(page)).toHaveValue("qqqqno_such_word");
  await expect(clueCards(page)).toContainText(state.clue.category.label);
  await expect(fill).toBeVisible();
  await expect(clueCards(page)).toContainText(`#${warm.warm_clue.rank}`);
  // The service issues one non-target warmer word, then has no further safe clue.
  expect(rejected.clue_available).toBe(false);
  expect(rejected.next_clue_kind).toBeUndefined();
  const exhausted = page.getByRole("button", { name: "Indiciu", exact: true });
  await expect(exhausted).toBeDisabled();
  await expect(exhausted).toHaveAttribute("title", "Nu mai există un indiciu sigur");
  await expect(page.locator("#contexto-clue-cost")).toHaveText("Nu mai sunt indicii pentru această rundă.");
  expect(mutations.filter(({ pathname }) => pathname.endsWith("/giveup"))).toEqual([]);
});

test("each real latest accepted guess has one exact server-authored comparison announcement", async ({ page }) => {
  await start(page, game);
  for (const text of safeWords().slice(0, 3)) {
    const body = await guess(page, text);
    expect(body.ok).toBe(true); expect(body.won).toBe(false);
    const comparison = page.locator(".contexto-comparison");
    await expect(comparison).toHaveCount(1);
    await expect(comparison).toHaveClass(new RegExp(`contexto-comparison--${body.feedback.kind}(?:\\s|$)`));
    await expect(comparison.locator(".contexto-comparison-copy > strong")).toHaveText(body.guess.label);
    await expect(comparison.locator(".contexto-comparison-copy > span")).toHaveText(body.feedback.message);
    await expect(comparison.locator(".contexto-comparison-rank")).toHaveText(`#${body.guess.rank}`);
    await expect(comparison).toHaveAttribute("role", "status");
    await expect(comparison).toHaveAttribute("aria-live", "polite");
    await expect(page.getByRole("status").filter({ hasText: body.feedback.message })).toHaveCount(1);
  }
});

const TEMPERATURES = [
  ["Fierbinte", "Fierbinte", "🔥", "rgb(255, 93, 59)"],
  ["Cald", "Cald", "♨️", "rgb(244, 162, 89)"],
  ["Caldut", "Călduț", "🌤️", "rgb(255, 209, 102)"],
  ["Rece", "Rece", "❄️", "rgb(142, 197, 255)"],
  ["Foarte rece", "Foarte rece", "🥶", "rgb(132, 190, 248)"],
  ["Inghetat", "Înghețat", "🧊", "rgb(123, 184, 242)"],
];
for (const [token, label, icon, color] of TEMPERATURES) {
  test(`public temperature presentation maps ${token} to the exact localized label/icon/color`, async ({ page }, testInfo) => {
    const initial = await start(page, game);
    await page.route(`**${gameURL(game, initial.game_id)}/guess`, async (route) => {
      const response = await route.fetch(); expect(response.status()).toBe(200);
      const body = await response.json(); expect(body.ok).toBe(true); expect(body.won).toBe(false);
      await projectionNote(testInfo, "temperature", { ...body, game_id: initial.game_id }, ["guess.temperature", "guesses[matching-id].temperature"]);
      const projected = { ...body, guess: { ...body.guess, temperature: token },
        guesses: body.guesses.map((item) => item.id === body.guess.id ? { ...item, temperature: token } : item) };
      await route.fulfill({ json: projected });
    }, { times: 1 });
    const body = await guess(page, safeWords()[0]);
    const row = page.locator("#contexto-guess-list .contexto-guess-row").filter({ has: page.getByText(body.guess.label, { exact: true }) });
    await expect(row).toHaveCount(1);
    await expect(row.getByText(label, { exact: true })).toBeVisible();
    await expect(row.getByText(icon, { exact: true })).toBeVisible();
    await expect(row.getByText(label, { exact: true })).toHaveCSS("color", color);
    await expect(row.getByText(`#${body.guess.rank}`, { exact: true })).toBeVisible();
  });
}

test("the real winning guess renders Gasit as Găsit with its exact icon/color and retires comparison", async ({ page }) => {
  await start(page, game);
  const response = await act(page, game, answer());
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.ok).toBe(true); expect(body.won).toBe(true);
  expect(body.guess.temperature).toBe("Gasit"); expect(body.guess.rank).toBe(1);
  const row = page.locator("#contexto-guess-list .contexto-guess-row").filter({ has: page.getByText(body.guess.label, { exact: true }) });
  await expect(row.getByText("Găsit", { exact: true })).toBeVisible();
  await expect(row.getByText("🎯", { exact: true })).toBeVisible();
  await expect(row.getByText("Găsit", { exact: true })).toHaveCSS("color", "rgb(95, 217, 155)");
  await expect(page.locator(".contexto-comparison")).toHaveCount(0);
});

test("real fuzzy correction preserves typed text, clears on editing and echoes the exact token only on confirmation", async ({ page, request }) => {
  // Seed0 / 'Mihai Eminscu' is the existing native fixture's non-target correction.
  await page.route("**/api/wordgames/contexto/games?*", async (route) => {
    const url = new URL(route.request().url()); url.searchParams.set("seed", "0");
    await route.continue({ url: url.toString() });
  });
  const initial = await start(page, game), mutations = traffic(page), typed = "Mihai Eminscu";
  const first = await guess(page, typed);
  expect(first.ok).toBe(false); expect(first.needs_confirmation).toBe(true);
  expect(first.resolved_label).toBe("Mihai Eminescu"); expect(first.attempts).toBe(0);
  await expect(field(page)).toHaveValue(typed);
  const chip = page.getByRole("button", { name: `Joacă ${first.resolved_label}`, exact: true });
  await expect(chip).toBeVisible();
  expect(mutations[0].body).toEqual({ text: typed });
  await field(page).fill("Mihai Eminescu");
  await expect(chip).toHaveCount(0); expect(mutations).toHaveLength(1);
  const untouched = await request.get(gameURL(game, initial.game_id)); expect(untouched.status()).toBe(200);
  expect((await untouched.json()).attempts).toBe(0);
  const rejected = await guess(page, typed);
  expect(rejected.needs_confirmation).toBe(true); expect(rejected.attempts).toBe(0);
  const confirmedReply = reply(page, initial.game_id, "guess");
  await page.getByRole("button", { name: `Joacă ${rejected.resolved_label}`, exact: true }).click();
  const received = await confirmedReply; expect(received.status()).toBe(200);
  const confirmed = await received.json();
  expect(confirmed.ok).toBe(true); expect(confirmed.won).toBe(false); expect(confirmed.attempts).toBe(1);
  expect(confirmed.guess.label).toBe(rejected.resolved_label);
  expect(mutations.map(({ body }) => body)).toEqual([{ text: typed }, { text: typed }, { text: typed, confirm: rejected.resolved_token }]);
  await expect(field(page)).toHaveValue("");
  await expect(page.locator(".contexto-confirm-chip")).toHaveCount(0);
  expect(typeof confirmed.message).toBe("string");
  await expect(page.getByRole("status").filter({ hasText: confirmed.message })).toHaveCount(1);
});

test("a public safe-suggestion presentation fills/focuses without POST and dismisses an armed reveal", async ({ page }, testInfo) => {
  const initial = await start(page, game), accepted = await guess(page, safeWords()[0]);
  expect(accepted.ok).toBe(true); expect(accepted.won).toBe(false);
  const mutations = traffic(page);
  await page.route(`**${gameURL(game, initial.game_id)}/guess`, async (route) => {
    const response = await route.fetch(); expect(response.status()).toBe(200);
    const body = await response.json(); expect(body.ok).toBe(false);
    await projectionNote(testInfo, "safe-suggestion", { ...body, game_id: initial.game_id }, ["suggestions"]);
    await route.fulfill({ json: { ...body, suggestions: [accepted.guess.label] } });
  }, { times: 1 });
  const rejected = await guess(page, "qqqqno_such_word");
  expect(rejected.attempts).toBe(accepted.attempts);
  await armReveal(page);
  const before = mutations.length;
  const choice = page.getByRole("button", { name: accepted.guess.label, exact: true });
  await expect(choice).toHaveAttribute("type", "button");
  await choice.click();
  await expect(field(page)).toHaveValue(accepted.guess.label);
  await expect(field(page)).toBeFocused();
  await expect(confirmation(page)).toHaveCount(0);
  expect(mutations).toHaveLength(before);
});

test("typing and actual new-game/exit lifecycles dismiss reveal without giving up either round", async ({ page }) => {
  const initial = await start(page, game), mutations = traffic(page);
  await armReveal(page); await field(page).fill("curiozitate");
  await expect(confirmation(page)).toHaveCount(0); expect(mutations).toEqual([]);
  await armReveal(page);
  await page.getByRole("button", { name: "Începe alt joc", exact: true }).click();
  await expect(confirmation(page)).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeVisible();
  const response = page.waitForResponse((result) => result.request().method() === "POST"
    && new URL(result.url()).pathname === "/api/wordgames/contexto/games");
  await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
  const received = await response; expect(received.status()).toBe(200);
  const next = await received.json(); expect(next.game_id).not.toBe(initial.game_id);
  await expect(field(page)).toHaveValue("");
  await armReveal(page);
  await page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true }).click();
  await expect(page).toHaveURL(/\/$/); await expect(confirmation(page)).toHaveCount(0);
  expect(mutations.filter(({ pathname }) => pathname.endsWith("/giveup"))).toEqual([]);
});
