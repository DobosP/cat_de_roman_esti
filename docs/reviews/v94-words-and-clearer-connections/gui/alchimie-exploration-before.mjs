import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync } from "node:fs";

const BASE = "/api/alchimie/explore";
const SAVE = "cat_alchimie_exploration_v1";
const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const word = (page, label) => page.locator(".alchemy-inventory-grid").getByRole("button", { name: new RegExp(`^${escapeRegex(label)}(?:,|$)`) });
const responseTo = (page, path, method = "POST") => page.waitForResponse((response) => response.request().method() === method && new URL(response.url()).pathname === path);
const saved = (page) => page.evaluate((key) => JSON.parse(localStorage.getItem(key) || "null"), SAVE);
const EXPANDED_CHECKPOINT = JSON.parse(readFileSync(new URL("./alchimie-111-checkpoint.json", import.meta.url), "utf8"));
const LARGE_CHECKPOINT = JSON.parse(readFileSync(new URL("./alchimie-221-checkpoint.json", import.meta.url), "utf8"));
const LATEST_CHECKPOINT = JSON.parse(readFileSync(new URL("./alchimie-221-expanded-checkpoint.json", import.meta.url), "utf8"));

// The original 75-concept world shipped in 2257766. This historical checkpoint must
// keep its original fingerprint; changing it would hide a broken upgrade path.
const LEGACY_COLLECTION = {
  version: 1,
  game_id: "expired-original-kitchen-session",
  revision: 3,
  goal_id: "paine",
  progress: {
    world_id: "bucataria-romaneasca-v1",
    recipe_hash: "8b52b6ca9f7d83c804b8ed5cfb3489c6215b64b116583f1fc393569d551b182c",
    discoveries: [
      ["n_v24_food_pantry_faina", "n_v4gas_apa"],
      ["n_v84_food_aluat", "n_v84_food_cuptor"],
      ["n_v24_food_pantry_faina", "n_v4gas_ou"],
    ],
  },
};

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
  await page.locator(".alchemy-library-tools > summary").click();
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
  await page.locator(".alchemy-explore-goal > summary").click();
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

test("the original kitchen collection upgrades without losing recipes, pantry supplies or its chosen goal", async ({ page }) => {
  await page.goto("/alchimie");
  await page.evaluate(({ key, collection }) => localStorage.setItem(key, JSON.stringify(collection)), {
    key: SAVE, collection: LEGACY_COLLECTION,
  });
  const restore = responseTo(page, BASE);
  await page.reload();
  const response = await restore;
  expect(response.status()).toBe(200);
  const restored = await response.json();
  expect(restored.progress.world_id).toBe(LEGACY_COLLECTION.progress.world_id);
  expect(restored.progress.recipe_hash).not.toBe(LEGACY_COLLECTION.progress.recipe_hash);
  expect(restored.compatible_recipe_hashes).toContain(LEGACY_COLLECTION.progress.recipe_hash);
  expect(restored.world.total_concepts).toBeGreaterThan(75);
  expect(restored.world.total_recipes).toBeGreaterThan(57);
  expect(restored.discovered_count).toBe(3);
  expect(restored.goal_id).toBe("paine");
  expect(restored.goals.find((goal) => goal.id === "paine").completed).toBe(true);
  const owned = restored.inventory.map((item) => item.id);
  for (const id of [
    "n_v84_food_aluat", "n_v4gas_paine", "n_v3gas_paste",
    "n_v4gas_fruct", "n_v24_food_pantry_zahar", "n_v24_food_imported_fruit_lamaie",
    "n_v24_food_salad_veg_castravete", "n_v4gas_legume",
  ]) expect(owned).toContain(id);
  expect(restored.progress.discoveries).toEqual(LEGACY_COLLECTION.progress.discoveries);
  await expect.poll(async () => (await saved(page))?.progress.recipe_hash).toBe(restored.progress.recipe_hash);
  expect((await saved(page)).compatible_recipe_hashes).toContain(LEGACY_COLLECTION.progress.recipe_hash);
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.getByLabel("Obiectiv opțional", { exact: true })).toHaveValue("paine");
  const next = await discover(page, restored);
  expect(next.discovered_count).toBe(4);
  await page.reload();
  await expect(page.getByLabel("Obiectiv opțional", { exact: true })).toBeEnabled();
  expect((await saved(page)).progress).toEqual(next.progress);
});

test("a completed 111-concept collection keeps every earned item and opens the larger world", async ({ page }) => {
  const checkpoint = EXPANDED_CHECKPOINT.collection;
  await page.goto("/alchimie");
  await page.evaluate(({ key, collection }) => localStorage.setItem(key, JSON.stringify(collection)), {
    key: SAVE, collection: checkpoint,
  });
  const restore = responseTo(page, BASE);
  await page.reload();
  const response = await restore;
  expect(response.status()).toBe(200);
  const restored = await response.json();
  expect(restored.progress.recipe_hash).not.toBe(checkpoint.progress.recipe_hash);
  expect(restored.compatible_recipe_hashes).toEqual(expect.arrayContaining([
    LEGACY_COLLECTION.progress.recipe_hash, checkpoint.progress.recipe_hash,
  ]));
  expect(restored.world.total_concepts).toBeGreaterThan(111);
  expect(restored.world.total_recipes).toBeGreaterThan(116);
  expect(restored.complete).toBe(false);
  expect(restored.discovered_count).toBe(58);
  expect(restored.goal_id).toBe("cornulete");
  expect(restored.goals.find((goal) => goal.id === "cornulete").completed).toBe(true);
  expect(restored.inventory.map((item) => item.id)).toEqual(expect.arrayContaining(EXPANDED_CHECKPOINT.owned_ids));
  expect(restored.progress.discoveries).toEqual(checkpoint.progress.discoveries);
  await expect.poll(async () => (await saved(page))?.progress.recipe_hash).toBe(restored.progress.recipe_hash);
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.getByLabel("Obiectiv opțional", { exact: true })).toHaveValue("cornulete");
  const query = page.getByRole("searchbox", { name: "Caută în colecție" });
  await page.locator(".alchemy-library-tools > summary").click();
  await query.fill("cornulete");
  await expect(word(page, "Cornulețe")).toBeVisible();
  await query.press("Escape");
  await page.locator(".alchemy-explore-journal > summary").click();
  await expect(page.locator(".alchemy-journal-entry")).toHaveCount(58);
  await page.locator(".alchemy-explore-journal > summary").click();
  const next = await discover(page, restored);
  expect(next.discovered_count).toBe(59);
  expect(next.progress.discoveries.slice(0, 58)).toEqual(checkpoint.progress.discoveries);
  await page.reload();
  await expect(page.getByLabel("Obiectiv opțional", { exact: true })).toBeEnabled();
  expect((await saved(page)).progress).toEqual(next.progress);
  expect(await page.evaluate((key) => new TextEncoder().encode(localStorage.getItem(key)).byteLength, SAVE)).toBeLessThan(64 * 1024);
  expect(await page.evaluate(() => globalThis.document.documentElement.scrollWidth <= globalThis.innerWidth)).toBe(true);
});

for (const [name, previous] of [["285-recipe", LARGE_CHECKPOINT], ["288-recipe", LATEST_CHECKPOINT]]) {
  test(`a completed221-word ${name} save keeps its journal and opens the new discoveries`, async ({ page }) => {
    const checkpoint = previous.collection;
    await page.goto("/alchimie");
    await page.evaluate(({ key, collection }) => localStorage.setItem(key, JSON.stringify(collection)), {
      key: SAVE, collection: checkpoint,
    });
    const response = responseTo(page, BASE);
    await page.reload();
    const restored = await (await response).json();
    expect(restored.progress.recipe_hash).not.toBe(checkpoint.progress.recipe_hash);
    expect(restored.compatible_recipe_hashes).toContain(checkpoint.progress.recipe_hash);
    expect(restored.world.total_concepts).toBeGreaterThan(221);
    expect(restored.world.total_recipes).toBeGreaterThan(288);
    expect(restored.complete).toBe(false);
    expect(restored.discovered_count).toBe(117);
    expect(restored.inventory.map((item) => item.id).sort()).toEqual(previous.owned_ids);
    expect(restored.progress.discoveries).toEqual(checkpoint.progress.discoveries);
    expect(restored.goal_id).toBe(checkpoint.goal_id);
    await expect.poll(async () => (await saved(page))?.progress).toEqual(restored.progress);
    await expect(page.getByRole("alert")).toHaveCount(0);
    await page.locator(".alchemy-explore-journal > summary").click();
    await expect(page.locator(".alchemy-journal-entry")).toHaveCount(117);
    await page.locator(".alchemy-explore-journal > summary").click();
    const next = await discover(page, restored);
    expect(next.discovered_count).toBe(118);
    expect(next.progress.discoveries.slice(0,117)).toEqual(checkpoint.progress.discoveries);
    await page.reload();
    await expect(page.locator(".alchemy-collection-count")).toContainText("222 /");
    expect((await saved(page)).progress).toEqual(next.progress);
  });
}

for (const example of [
  { prefix: 45, first: "Aluat", second: "Portocală", result: "Chec", focus: "Aluat" },
  { prefix: 65, first: "Nucă", second: "Pătrunjel", result: "Pesto", focus: null },
]) {
  test(`deep keyboard crafting keeps ${example.focus ?? "the collection"} focus visible`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const checkpoint = structuredClone(LARGE_CHECKPOINT.collection);
    checkpoint.revision = example.prefix;
    checkpoint.goal_id = null;
    checkpoint.progress.discoveries = checkpoint.progress.discoveries.slice(0, example.prefix);
    await page.goto("/alchimie");
    await page.evaluate(({ key, value }) => localStorage.setItem(key, JSON.stringify(value)), {
      key: SAVE, value: checkpoint,
    });
    const response = responseTo(page, BASE);
    await page.reload();
    const state = await (await response).json();
    await word(page, example.first).click();
    const second = word(page, example.second);
    await second.focus();
    await second.scrollIntoViewIfNeeded();
    const crafted = responseTo(page, `${BASE}/${state.game_id}/combine`);
    await page.keyboard.press("Enter");
    const result = await (await crafted).json();
    expect(result.discovered.some((item) => item.label === example.result)).toBe(true);
    const focused = example.focus ? word(page, example.focus) : page.getByRole("region", { name: "Colecția ta" });
    await expect(focused).toBeFocused();
    await expect.poll(async () => {
      const box = await focused.boundingBox();
      const bench = await page.locator(".alchemy-bench").boundingBox();
      return box.y >= bench.y + bench.height && box.y < 844;
    }).toBe(true);
    if (example.focus) expect((await focused.boundingBox()).y + (await focused.boundingBox()).height).toBeLessThanOrEqual(844);
  });
}

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
    // The route fade can start after mount; audit the settled screen colors.
    await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
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

for (const width of [390, 320]) {
  test(`exploration starts with all eight words visible at ${width}px without opening optional tools`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    const state = await begin(page);
    await expect(page.locator(".screen")).toHaveCSS("opacity", "1");
    await page.evaluate(() => globalThis.document.fonts.ready);
    await expect(page.locator(".alchemy-explore-goal")).not.toHaveAttribute("open");
    await expect(page.locator(".alchemy-library-tools")).not.toHaveAttribute("open");
    await expect(page.locator(".alchemy-word")).toHaveCount(8);
    for (const tile of await page.locator(".alchemy-word").all()) {
      await expect(tile).toBeInViewport({ ratio: 1 });
      const box = await tile.boundingBox();
      expect(box.width).toBeGreaterThanOrEqual(44);
      expect(box.height).toBeGreaterThanOrEqual(44);
    }
    expect(await page.locator(".alchemy-explore-screen").evaluate((element) => element.scrollTop)).toBe(0);
    const mutations = [];
    page.on("request", (request) => {
      if (request.method() === "POST" && request.url().includes(`${BASE}/${state.game_id}/`)) mutations.push(request.url());
    });
    await word(page, state.inventory[0].label).click();
    for (const selector of [".alchemy-explore-goal", ".alchemy-library-tools"]) {
      const summary = page.locator(`${selector} > summary`);
      await summary.click();
      await expect(page.locator(selector)).toHaveAttribute("open", "");
      await summary.click();
    }
    await expect(word(page, state.inventory[0].label)).toHaveAttribute("aria-pressed", "true");
    expect(mutations).toEqual([]);
  });
}

test("exploration keeps bottom-of-collection craft feedback visible and lets short views scroll normally", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  let state = await begin(page);
  for (let index = 0; index < 8; index += 1) state = await discover(page, state);
  expect(state.inventory.filter((item) => item.status === "active").length).toBeGreaterThan(16);
  const selected = page.getByRole("button", { name: /^Scoate .* din alambic$/ });
  if (await selected.count()) await selected.click();
  const active = page.locator(".alchemy-word:not(:disabled)");
  await active.last().click();
  const response = responseTo(page, `${BASE}/${state.game_id}/combine`);
  await active.nth(-2).click();
  const result = await (await response).json();
  await expect(page.locator(".alchemy-bench .alchemy-feedback").first()).toContainText(result.message);
  await expect(page.locator(".alchemy-bench .alchemy-feedback").first()).toBeInViewport({ ratio: 1 });
  await expect(page.locator(".alchemy-bench")).toHaveCSS("position", "sticky");
  expect(await page.locator(".alchemy-explore-screen").evaluate((element) => element.scrollTop)).toBeGreaterThan(100);
  await page.setViewportSize({ width: 320, height: 360 });
  await expect(page.locator(".alchemy-bench")).toHaveCSS("position", "static");
  await page.evaluate(() => { globalThis.document.documentElement.style.fontSize = "200%"; });
  await active.last().scrollIntoViewIfNeeded();
  await expect(active.last()).toBeInViewport({ ratio: 1 });
  expect(await page.evaluate(() => globalThis.document.documentElement.scrollWidth <= globalThis.innerWidth)).toBe(true);
});
