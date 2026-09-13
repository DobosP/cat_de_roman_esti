import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const BASE = "/api/alchimie/explore";
const SAVE = "cat_alchimie_exploration_v1";
const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const word = (page, label) => page.locator(".alchemy-inventory-grid").getByRole("button", { name: new RegExp(`^${escapeRegex(label)}(?:,|$)`) });
const responseTo = (page, path, method = "POST") => page.waitForResponse((response) => response.request().method() === method && new URL(response.url()).pathname === path);
const saved = (page) => page.evaluate((key) => JSON.parse(localStorage.getItem(key) || "null"), SAVE);

async function begin(page) {
  await page.goto("/alchimie");
  await expect(page.getByRole("heading", { name: "O lume de descoperit." })).toBeVisible();
  const response = responseTo(page, BASE);
  await page.getByRole("button", { name: "Începe explorarea →" }).click();
  const result = await response;
  expect(result.status()).toBe(200);
  const state = await result.json();
  await expect(page.getByLabel("Obiectiv opțional", { exact: true })).toBeEnabled();
  return state;
}

async function getPair(page, state) {
  let response = responseTo(page, `${BASE}/${state.game_id}/hint`);
  await page.getByRole("button", { name: "💡 O idee?", exact: true }).click();
  let current = await (await response).json();
  expect(current.hint.stage).toBe("output");
  expect(current.hint.pair).toBeNull();
  response = responseTo(page, `${BASE}/${state.game_id}/hint`);
  await page.getByRole("button", { name: "Arată-mi perechea", exact: true }).click();
  current = await (await response).json();
  expect(current.hint.stage).toBe("pair");
  await expect(word(page, current.hint.pair[0].label)).toHaveAttribute("aria-pressed", "true");
  return current;
}

async function discover(page, state) {
  const current = await getPair(page, state);
  const response = responseTo(page, `${BASE}/${state.game_id}/combine`);
  // The first hint ingredient is already selected: one tap applies the suggestion.
  await word(page, current.hint.pair[1].label).click();
  const result = await (await response).json();
  expect(result.discovered).toHaveLength(1);
  await expect.poll(async () => (await saved(page))?.revision).toBe(result.revision);
  return result;
}

test("exploration is the clean default, saves discoveries, searches accents and restores expired sessions", async ({ page }) => {
  let state = await begin(page);
  expect(state.goal_id).toBeNull();
  state = await discover(page, state);
  const checkpoint = await saved(page);
  const get = responseTo(page, `${BASE}/${state.game_id}`, "GET");
  await page.reload();
  const resumed = await (await get).json();
  expect(resumed.progress).toEqual(state.progress);
  await expect(page.getByLabel("Obiectiv opțional", { exact: true })).toBeEnabled();
  const query = page.getByRole("searchbox", { name: "Caută în colecție" });
  const item = resumed.inventory.at(-1);
  await query.fill(item.label.normalize("NFD").replace(/\p{M}/gu, ""));
  await expect(word(page, item.label)).toBeVisible();
  await query.press("Escape");
  await expect(query).toHaveValue("");
  await page.evaluate((key) => {
    const value = JSON.parse(localStorage.getItem(key));
    value.game_id = "expired-exploration-session";
    localStorage.setItem(key, JSON.stringify(value));
  }, SAVE);
  const restore = responseTo(page, BASE);
  await page.reload();
  const restored = await (await restore).json();
  expect(restored.game_id).not.toEqual(state.game_id);
  expect(restored.progress).toEqual(checkpoint.progress);
  expect(restored.inventory).toEqual(state.inventory);
  await expect.poll(async () => (await saved(page))?.game_id).toBe(restored.game_id);
  expect(await page.evaluate(() => localStorage.getItem("cat_wordgame_scores_v1"))).toBeNull();
});

test("optional goal completion keeps exploration playable and pantry gifts arrive automatically", async ({ page }) => {
  let state = await begin(page);
  const goalId = state.goals[0].id;
  const goalResponse = responseTo(page, `${BASE}/${state.game_id}/goal`);
  await page.getByLabel("Obiectiv opțional", { exact: true }).selectOption(goalId);
  state = await (await goalResponse).json();
  for (let steps = 0; steps < 32 && !state.goals.find((goal) => goal.id === goalId).completed; steps += 1) state = await discover(page, state);
  expect(state.goals.find((goal) => goal.id === goalId).completed).toBe(true);
  await expect(page.locator(".alchemy-explore-goal")).toContainText("Poți continua");
  expect(state.complete).toBe(false);
  const count = state.discovered_count;
  state = await discover(page, state);
  expect(state.discovered_count).toBe(count + 1);
  while (state.discovered_count < 3) state = await discover(page, state);
  expect(state.unlocked.length).toBeGreaterThan(0);
  expect(state.inventory.length).toBeGreaterThan(state.seed_count + state.discovered_count);
  await page.locator(".alchemy-explore-journal > summary").click();
  await expect(page.locator(".alchemy-journal-entry")).toHaveCount(state.discovered_count);
  const clear = responseTo(page, `${BASE}/${state.game_id}/goal`);
  await page.getByLabel("Obiectiv opțional", { exact: true }).selectOption("");
  const free = await (await clear).json();
  expect(free.inventory).toEqual(state.inventory);
  expect(free.goal_id).toBeNull();
});

test("dragging a suggested word onto its partner crafts directly", async ({ page }) => {
  const initial = await begin(page);
  const state = await getPair(page, initial);
  const response = responseTo(page, `${BASE}/${state.game_id}/combine`);
  await word(page, state.hint.pair[0].label).dragTo(word(page, state.hint.pair[1].label));
  const result = await (await response).json();
  expect(result.discovered_count).toBe(1);
  await expect.poll(async () => (await saved(page))?.progress.discoveries.length).toBe(1);
});

test("a lost combine response reconciles once without submitting the recipe twice", async ({ page }) => {
  const initial = await begin(page);
  const state = await getPair(page, initial);
  let posts = 0;
  await page.route(`**${BASE}/${state.game_id}/combine`, async (route) => {
    posts += 1;
    await route.fetch();
    await route.abort("failed");
  });
  const recovered = responseTo(page, `${BASE}/${state.game_id}`, "GET");
  await word(page, state.hint.pair[1].label).click();
  const current = await (await recovered).json();
  expect(current.discovered_count).toBe(1);
  await expect(page.getByText("Colecție sincronizată. Poți continua.", { exact: true })).toBeVisible();
  await expect.poll(async () => (await saved(page))?.progress.discoveries.length).toBe(1);
  expect(posts).toBe(1);
});

test("failed recovery blocks mutations until the authoritative collection reloads", async ({ page }) => {
  const initial = await begin(page);
  const state = await getPair(page, initial);
  await page.route(`**${BASE}/${state.game_id}/combine`, async (route) => { await route.fetch(); await route.abort("failed"); }, { times: 1 });
  await page.route(`**${BASE}/${state.game_id}`, async (route) => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "private diagnostic" }) }), { times: 1 });
  await word(page, state.hint.pair[1].label).click();
  await expect(page.getByRole("alert")).toContainText("Nu am putut verifica colecția.");
  await expect(page.getByRole("alert")).not.toContainText("private diagnostic");
  await expect(page.getByLabel("Obiectiv opțional", { exact: true })).toBeDisabled();
  const recovered = responseTo(page, `${BASE}/${state.game_id}`, "GET");
  await page.getByRole("button", { name: "Încarcă colecția", exact: true }).click();
  expect((await (await recovered).json()).discovered_count).toBe(1);
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect.poll(async () => (await saved(page))?.progress.discoveries.length).toBe(1);
});

test("a second tab cannot overwrite newer saved progress", async ({ page, context }) => {
  let state = await begin(page);
  const other = await context.newPage();
  await other.goto("/alchimie?mode=explore");
  await expect(other.getByLabel("Obiectiv opțional", { exact: true })).toBeEnabled();
  // GET resume preserves the same save. This tab now advances that shared session.
  state = await discover(page, state);
  await expect(other.getByRole("alert")).toContainText("Colecția s-a schimbat în altă filă.");
  await expect(other.getByLabel("Obiectiv opțional", { exact: true })).toBeDisabled();
  await other.getByRole("button", { name: "Încarcă colecția", exact: true }).click();
  await expect(other.getByRole("alert")).toHaveCount(0);
  expect((await saved(other)).progress).toEqual(state.progress);
  await other.close();
});

test("a malformed local checkpoint stays preserved with visible recovery", async ({ page }) => {
  await page.addInitScript((key) => localStorage.setItem(key, "{broken-checkpoint"), SAVE);
  await page.goto("/alchimie");
  await expect(page.getByRole("alert")).toContainText("Colecția salvată nu poate fi încărcată.");
  await expect(page.getByRole("button", { name: "Începe explorarea →" })).toBeDisabled();
  expect(await page.evaluate((key) => localStorage.getItem(key), SAVE)).toBe("{broken-checkpoint");
  await page.getByRole("link", { name: "Provocări", exact: true }).click();
  await expect(page.getByRole("button", { name: "Joacă →", exact: true })).toBeEnabled();
});

test("a checkpoint from a different recipe book is retained when restore is rejected", async ({ page }) => {
  await begin(page);
  await page.evaluate((key) => {
    const value = JSON.parse(localStorage.getItem(key));
    value.game_id = "expired-exploration-session";
    value.progress.recipe_hash = "0".repeat(64);
    localStorage.setItem(key, JSON.stringify(value));
  }, SAVE);
  const original = await saved(page);
  const restore = responseTo(page, BASE);
  await page.reload();
  expect((await restore).status()).toBe(409);
  await expect(page.getByRole("alert")).toContainText("Colecția salvată nu poate fi încărcată.");
  expect(await saved(page)).toEqual(original);
});

test("the daily circuit opens scored challenges while the arcade card opens exploration", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Deschide Alchimie — neterminat azi", exact: true }).click();
  await expect(page).toHaveURL(/\/alchimie\?mode=challenges$/);
  await expect(page.getByRole("button", { name: "Provocarea zilei", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true }).click();
  await page.getByRole("button", { name: /^Joacă Alchimie —/ }).click();
  await expect(page.getByRole("button", { name: "Începe explorarea →" })).toBeVisible();
});

test("exploration intro, active collection and earned recipes are accessible", async ({ page }, testInfo) => {
  if (testInfo.project.name === "desktop") await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/alchimie");
  await expect(page.getByRole("button", { name: "Începe explorarea →" })).toBeEnabled();
  async function audit(label) {
    await page.evaluate(async () => { await globalThis.document.fonts.ready; await Promise.all(globalThis.document.getAnimations().filter((animation) => Number.isFinite(animation.effect?.getComputedTiming().endTime)).map((animation) => animation.finished.catch(() => {}))); });
    const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(result.violations.map(({ id, nodes }) => ({ id, targets: nodes.map(({ target }) => target) }))).toEqual([]);
    expect(await page.evaluate(() => globalThis.document.documentElement.scrollWidth <= globalThis.innerWidth)).toBe(true);
    expect(await page.locator(".alchemy-explore-screen").evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`${label}.png`), fullPage: true });
  }
  await audit("exploration-intro");
  const state = await begin(page);
  if (testInfo.project.name === "desktop") {
    for (const button of await page.locator(".alchemy-inventory-grid button").all()) await expect(button).toBeInViewport({ ratio: 1 });
  }
  await discover(page, state);
  await audit("exploration-live");
  await page.locator(".alchemy-explore-journal > summary").click();
  await audit("exploration-recipes");
  await page.setViewportSize({ width: 320, height: 850 });
  await page.evaluate(() => { globalThis.document.documentElement.style.fontSize = "200%"; });
  await audit("exploration-320-text-zoom");
});
