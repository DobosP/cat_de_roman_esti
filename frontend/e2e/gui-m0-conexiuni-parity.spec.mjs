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
    const guidance = page.locator(".coach-line[role=status]")
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

test("three immediate clues preserve lives, reveal earned details and reject an extra request", async ({ page, request }) => {
  const { initial, plan } = await begin(page);
  const posts = mutations(page, initial.game_id);
  expect(initial.hints_left).toBe(3);
  expect(initial.clues_used).toBe(0);
  await expect(clueButton(page)).toBeEnabled();
  await expect(page.getByText("Costă un pas.", { exact: true })).toBeVisible();
  const clues = [];
  for (let rung = 1; rung <= 3; rung += 1) {
    const pending = responseFor(page, initial.game_id, "clue");
    await clueButton(page).click();
    const response = await pending;
    expect(response.status()).toBe(200);
    const state = await response.json();
    expect(state.hint_level).toBe(rung);
    expect(state.hints_left).toBe(3 - rung);
    expect(state.steps).toBe(rung);
    expect(state.lives).toBe(initial.lives);
    expect(state.mistakes).toBe(0);
    clues.push(state.clue);
    await expect(page.locator(".coach-line[role=status]")).toContainText(state.clue.message);
  }
  expect(clues[0].label).toBeUndefined();
  expect(clues[0].tile).toBeUndefined();
  expect(clues[1].label).toBeTruthy();
  expect(clues[1].tile).toBeUndefined();
  expect(clues[2].tile.id).toBeTruthy();
  await expect(page.getByRole("button", { name: "Fără indicii" })).toBeDisabled();
  const previous = await saved(request, initial.game_id);
  const extra = await request.post(gameURL(game, initial.game_id) + "/clue");
  expect(extra.status()).toBe(400);
  expect(await saved(request, initial.game_id)).toEqual(previous);
  const wrong = await guess(page, initial, plan.practice.payload.ids);
  expect(wrong.one_away).toBe(true);
  expect(wrong.steps).toBe(4);
  expect(wrong.lives).toBe(initial.lives - 1);
  expect(posts.map(({ path }) => path.slice(path.lastIndexOf("/") + 1)))
    .toEqual(["clue", "clue", "clue", "guess"]);
});
