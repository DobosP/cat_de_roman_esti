// Authored M0 replacements; NOT RUN during authoring. These cases use ordinary
// local-server guesses/clues and the existing private native fixture helper.
// No state, response, clue metadata or recovery failure is fabricated.
import { test, expect } from "@playwright/test";
import { games, gameURL, deterministicStarts, solution, start } from "./games.mjs";

const game = games.find(({ key }) => key === "conexiuni");
const verify = (page) => page.getByRole("button", { name: "Verifică", exact: true });
const clueButton = (page) => page.getByRole("button", { name: /^Indiciu(?: |$)/ });
const responseFor = (page, id, action) => page.waitForResponse((response) =>
  response.request().method() === "POST" &&
  new URL(response.url()).pathname === `${gameURL(game, id)}/${action}`);

async function begin(page) {
  const plan = solution(game);
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const { game_id, ...stable } = initial;
  expect(game_id.length).toBeGreaterThan(0);
  expect(stable).toEqual(plan.initial);
  expect(plan.steps).toHaveLength(4);
  expect(plan.steps.every((step) => step.payload.ids.length === 4)).toBe(true);
  return { initial, plan };
}

function tile(page, initial, id) {
  const item = initial.tiles.find((candidate) => candidate.id === id);
  expect(item, `native fixture tile ${id} must exist on the actual board`).toBeDefined();
  return page.locator(game.board).getByRole("button", { name: item.label, exact: true });
}

async function choose(page, initial, ids) {
  const clear = page.getByRole("button", { name: "Golește", exact: true });
  if (await clear.isEnabled()) await clear.click();
  for (const id of ids) await tile(page, initial, id).click();
  await expect(page.locator(`${game.board} button[aria-pressed="true"]`)).toHaveCount(4);
  await expect(verify(page)).toBeEnabled();
}

async function guess(page, initial, ids) {
  await choose(page, initial, ids);
  const pending = responseFor(page, initial.game_id, "guess");
  await verify(page).click();
  const response = await pending;
  expect(response.status()).toBe(200);
  const state = await response.json();
  expect(state.ok).toBe(true);
  return state;
}

async function saved(request, id) {
  const response = await request.get(gameURL(game, id));
  expect(response.status()).toBe(200);
  return response.json();
}

function mutations(page, id) {
  const seen = [];
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (request.method() === "POST" && path.startsWith(`${gameURL(game, id)}/`)) {
      seen.push({ path, body: request.postData() === null ? null : request.postDataJSON() });
    }
  });
  return seen;
}

async function unscopedEnter(page) {
  // Exercise the actual screen-level Enter handler, rather than Enter activating
  // the focused tile/shuffle button. The changed-set positive control below
  // proves that this focus arrangement really reaches the submission path.
  await page.evaluate(() => globalThis.document.activeElement?.blur());
  await page.keyboard.press("Enter");
  await page.evaluate(() => new Promise((resolve) => {
    globalThis.requestAnimationFrame(() => globalThis.requestAnimationFrame(resolve));
  }));
}

for (const reversed of [false, true]) {
  test(`retained one-away set survives board reorder and blocks button/Enter retries (${reversed ? "reverse" : "forward"} selection order)`, async ({ page, request }) => {
    const { initial, plan } = await begin(page);
    const ids = [...plan.practice.payload.ids];
    if (reversed) ids.reverse();
    const posts = mutations(page, initial.game_id);
    const oneAway = await guess(page, initial, ids);
    expect(oneAway.correct).toBe(false);
    expect(oneAway.one_away).toBe(true);
    expect(oneAway.lost).toBe(false);
    expect(oneAway.mistakes).toBe(1);
    expect(oneAway.lives).toBe(initial.lives - 1);
    expect(posts).toHaveLength(1);
    expect(posts[0].body.ids).toEqual(ids);
    const guidance = page.locator(".connections-feedback [role=status]")
      .filter({ hasText: "Aproape: 3 din 4. Schimbă o piesă." });
    await expect(guidance).toBeVisible();
    const blocked = page.getByRole("button", { name: "Schimbă o piesă", exact: true });
    await expect(blocked).toBeDisabled();
    const selected = page.locator(`${game.board} button[aria-pressed="true"]`);
    const labels = ids.map((id) => initial.tiles.find((item) => item.id === id).label).sort((left, right) => left < right ? -1 : left > right ? 1 : 0);
    expect((await selected.allTextContents()).map((text) => text.trim()).sort((left, right) => left < right ? -1 : left > right ? 1 : 0)).toEqual(labels);

    const before = await page.locator(`${game.board} button`).allTextContents();
    await page.getByRole("button", { name: "Amestecă", exact: true }).click();
    await expect.poll(() => page.locator(`${game.board} button`).allTextContents()).not.toEqual(before);
    expect((await selected.allTextContents()).map((text) => text.trim()).sort((left, right) => left < right ? -1 : left > right ? 1 : 0)).toEqual(labels);
    await expect(guidance).toBeVisible();
    await expect(blocked).toBeDisabled();
    // Native HTMLElement.click respects the disabled control. It cannot spend
    // another life; the independent screen-level Enter path must also refuse.
    await blocked.evaluate((button) => button.click());
    await unscopedEnter(page);
    expect(posts).toHaveLength(1);
    const unchanged = await saved(request, initial.game_id);
    expect(unchanged.mistakes).toBe(oneAway.mistakes);
    expect(unchanged.lives).toBe(oneAway.lives);
    expect(unchanged.solved).toEqual(oneAway.solved);
    await expect(selected).toHaveCount(4);

    // Change exactly the outsider, then Enter must reach the real server and
    // solve the native fixture's first group. This is not a duplicate-recovery
    // case and no response is dropped, replaced or specially fulfilled.
    const correctIds = plan.steps[0].payload.ids;
    const outsider = ids.find((id) => !correctIds.includes(id));
    const missing = correctIds.find((id) => !ids.includes(id));
    expect(outsider).toBeDefined();
    expect(missing).toBeDefined();
    await tile(page, initial, outsider).click();
    await tile(page, initial, missing).click();
    await expect(verify(page)).toBeEnabled();
    const pending = responseFor(page, initial.game_id, "guess");
    await unscopedEnter(page);
    const response = await pending;
    expect(response.status()).toBe(200);
    const corrected = await response.json();
    expect(corrected.correct).toBe(true);
    expect(corrected.solved_count).toBe(1);
    expect(corrected.mistakes).toBe(oneAway.mistakes);
    expect(posts).toHaveLength(2);
    expect([...posts[1].body.ids].sort((left, right) => left < right ? -1 : left > right ? 1 : 0)).toEqual([...correctIds].sort((left, right) => left < right ? -1 : left > right ? 1 : 0));
    await expect(page.locator(`${game.board} button`)).toHaveCount(12);
    await expect(guidance).toHaveCount(0);
    await expect(page.locator(`${game.board} button[aria-pressed="true"]`)).toHaveCount(0);
  });
}

test("real mistakes gate both clues, count down the second and remove the exhausted action", async ({ page, request }) => {
  const { initial, plan } = await begin(page);
  const posts = mutations(page, initial.game_id);
  const countdown = page.locator(".connections-hint-status");
  expect(initial.clues_used).toBe(0);
  expect(initial.clue_available).toBe(false);
  await expect(clueButton(page)).toHaveCount(0);
  await expect(countdown).toHaveText("Indiciu disponibil după încă 2 greșeli.");

  // One member from each of the four real groups produces distinct wrong sets
  // without solving a group or encountering retained one-away retry behavior.
  const wrong = (index) => plan.steps.map((step) => step.payload.ids[index]);
  const firstMistake = await guess(page, initial, wrong(0));
  expect(firstMistake.correct).toBe(false);
  expect(firstMistake.one_away).toBe(false);
  expect(firstMistake.mistakes).toBe(1);
  expect(firstMistake.clue_available).toBe(false);
  await expect(clueButton(page)).toHaveCount(0);
  await expect(countdown).toHaveText("Indiciu disponibil după încă 1 greșeală.");

  const secondMistake = await guess(page, initial, wrong(1));
  expect(secondMistake.correct).toBe(false);
  expect(secondMistake.one_away).toBe(false);
  expect(secondMistake.mistakes).toBe(2);
  expect(secondMistake.clues_used).toBe(0);
  expect(secondMistake.clue_available).toBe(true);
  await expect(countdown).toHaveCount(0);
  await expect(clueButton(page)).toBeEnabled();
  await expect(clueButton(page)).toHaveAttribute("title", "Arată începutul unei categorii");
  await expect(clueButton(page)).toContainText("−100 pct");
  await expect(clueButton(page)).not.toContainText("1 rămas");

  async function takeClue() {
    const pending = responseFor(page, initial.game_id, "clue");
    await clueButton(page).click();
    const response = await pending;
    expect(response.status()).toBe(200);
    const state = await response.json();
    expect(state.ok).toBe(true);
    const visible = page.locator(".connections-feedback [role=status]")
      .filter({ hasText: state.clue.message });
    await expect(visible).toBeVisible();
    await expect(visible).toHaveAttribute("aria-live", "polite");
    return state;
  }

  const firstClue = await takeClue();
  expect(firstClue.clues_used).toBe(1);
  expect(firstClue.clues).toHaveLength(1);
  expect(firstClue.clue_available).toBe(false);
  expect(firstClue.mistakes).toBe(secondMistake.mistakes);
  expect(firstClue.lives).toBe(secondMistake.lives);
  await expect(clueButton(page)).toHaveCount(0);
  await expect(countdown).toHaveText("Indiciu disponibil după încă 1 greșeală.");

  const thirdMistake = await guess(page, initial, wrong(2));
  expect(thirdMistake.correct).toBe(false);
  expect(thirdMistake.one_away).toBe(false);
  expect(thirdMistake.mistakes).toBe(3);
  expect(thirdMistake.clues_used).toBe(1);
  expect(thirdMistake.clue_available).toBe(true);
  await expect(countdown).toHaveCount(0);
  await expect(clueButton(page)).toBeEnabled();
  await expect(clueButton(page)).toContainText("1 rămas");
  const secondClue = await takeClue();
  expect(secondClue.clues_used).toBe(2);
  expect(secondClue.clues).toHaveLength(2);
  expect(secondClue.clues[0]).toEqual(firstClue.clues[0]);
  expect(secondClue.clue_available).toBe(false);
  expect(secondClue.mistakes).toBe(thirdMistake.mistakes);
  expect(secondClue.lives).toBe(thirdMistake.lives);
  expect(secondClue.lost).toBe(false);
  await expect(countdown).toHaveText("Indicii folosite");
  await expect(clueButton(page)).toHaveCount(0);
  await expect(page.locator(".connections-hint-action")).toHaveCount(0);
  for (const clue of secondClue.clues) {
    await expect(page.locator(".connections-feedback [role=status]")
      .filter({ hasText: clue.message })).toBeVisible();
  }
  expect(posts.map(({ path }) => path.slice(path.lastIndexOf("/") + 1)))
    .toEqual(["guess", "guess", "clue", "guess", "clue"]);
  await unscopedEnter(page);
  expect(posts).toHaveLength(5);
  const persisted = await saved(request, initial.game_id);
  expect(persisted.clues).toEqual(secondClue.clues);
  expect(persisted.clues_used).toBe(2);
  expect(persisted.clue_available).toBe(false);
  expect(persisted.lives).toBe(1);
});
