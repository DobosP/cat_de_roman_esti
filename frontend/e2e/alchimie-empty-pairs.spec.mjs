/* global document */
import { test, expect } from "@playwright/test";

const BASE = "/api/alchimie/explore";
const SAVE = "cat_alchimie_exploration_v1";
const word = (page, label) => page.locator(".alchemy-inventory-grid").getByRole("button", { name: new RegExp(`^${label}(?:,|$)`) });
const reply = (page, path, method = "POST") => page.waitForResponse((r) => r.request().method() === method && new URL(r.url()).pathname === path);
const rawSave = (page) => page.evaluate((key) => localStorage.getItem(key), SAVE);

async function begin(page) {
  await page.goto("/alchimie");
  const response = reply(page, BASE);
  await page.getByRole("button", { name: "Începe explorarea →" }).click();
  const state = await (await response).json();
  expect(state.empty_pairs).toEqual([]);
  await expect(word(page, "Făină")).toBeEnabled();
  return state;
}
async function miss(page, state) {
  await word(page, "Făină").click();
  const response = reply(page, `${BASE}/${state.game_id}/combine`);
  await word(page, "Cheag alimentar").click();
  const result = await (await response).json();
  expect(result.result).toBeNull();
  await expect(word(page, "Cheag alimentar")).toHaveClass(/alchemy-word--tried/);
  return result;
}

test("observed empty partners are marked and repeated/reversed taps need no new request", async ({ page, request }) => {
  const state = await miss(page, await begin(page));
  await expect(page.locator(".alchemy-feedback")).toContainText("Făină + Cheag alimentar");
  await expect(word(page, "Cheag alimentar")).toHaveAccessibleName("Cheag alimentar, încercat fără rezultat cu Făină");
  const saved = await rawSave(page);
  const posts = [];
  page.on("request", (r) => { if (r.method() === "POST") posts.push(r.url()); });
  await word(page, "Cheag alimentar").click();
  await expect(page.locator(".alchemy-feedback")).toContainText("ai încercat deja");
  await expect(word(page, "Făină")).toHaveAttribute("aria-pressed", "true");
  await word(page, "Făină").click();
  await word(page, "Cheag alimentar").click();
  await expect(word(page, "Făină")).toHaveClass(/alchemy-word--tried/);
  await word(page, "Făină").focus();
  await page.keyboard.press("Enter");
  await expect(word(page, "Făină")).toBeFocused();
  await expect(word(page, "Cheag alimentar")).toHaveAttribute("aria-pressed", "true");
  expect(posts).toHaveLength(0);
  expect(await rawSave(page)).toBe(saved);
  const current = await (await request.get(`${BASE}/${state.game_id}`)).json();
  expect(current.revision).toBe(state.revision);
  expect(current.progress.discoveries).toEqual([]);
  expect(JSON.parse(saved)).not.toHaveProperty("empty_pairs");
});

test("GET reload and goal changes preserve observations without blocking a valid recipe", async ({ page }) => {
  const state = await miss(page, await begin(page));
  await page.reload();
  await expect(word(page, "Făină")).toBeEnabled();
  await word(page, "Făină").click();
  await expect(word(page, "Cheag alimentar")).toHaveClass(/alchemy-word--tried/);
  await page.locator(".alchemy-explore-goal > summary").click();
  const response = reply(page, `${BASE}/${state.game_id}/goal`);
  await page.getByLabel("Obiectiv opțional", { exact: true }).selectOption({ index: 1 });
  expect((await (await response).json()).empty_pairs).toEqual(state.empty_pairs);
  await word(page, "Făină").click();
  await expect(word(page, "Apă")).not.toHaveClass(/alchemy-word--tried/);
  const crafted = reply(page, `${BASE}/${state.game_id}/combine`);
  await word(page, "Apă").click();
  const fresh = await (await crafted).json();
  expect(fresh.discovered.some((item) => item.label === "Aluat")).toBe(true);
  expect(fresh.empty_pairs).toEqual(state.empty_pairs);
});

for (const committed of [false, true]) {
  test(`lost ${committed ? "committed" : "uncommitted"} empty reply trusts only recovery GET`, async ({ page }) => {
    const state = await begin(page);
    let combineRequests = 0;
    let recoveryReads = 0;
    page.on("request", (request) => {
      if (request.method() === "GET" && new URL(request.url()).pathname === `${BASE}/${state.game_id}`) recoveryReads += 1;
    });
    // Retain interception while the immediate recovery GET is in flight.
    await page.route(`**${BASE}/${state.game_id}/combine`, async (route) => {
      combineRequests += 1;
      if (combineRequests !== 1) { await route.continue(); return; }
      if (committed) expect((await route.fetch()).status()).toBe(200);
      await route.abort("failed");
    });
    await word(page, "Făină").click();
    const recovered = reply(page, `${BASE}/${state.game_id}`, "GET");
    await word(page, "Cheag alimentar").click();
    expect((await (await recovered).json()).empty_pairs).toHaveLength(committed ? 1 : 0);
    await expect(word(page, "Făină")).toBeEnabled();
    await word(page, "Făină").click();
    if (committed) await expect(word(page, "Cheag alimentar")).toHaveClass(/alchemy-word--tried/);
    else await expect(word(page, "Cheag alimentar")).not.toHaveClass(/alchemy-word--tried/);
    expect(combineRequests).toBe(1);
    expect(recoveryReads).toBe(1);
  });
}

test("cached acknowledgment honors changed saved-collection ownership", async ({ page }) => {
  await miss(page, await begin(page));
  const foreign = await page.evaluate((key) => {
    const value = JSON.parse(localStorage.getItem(key));
    value.game_id = "another-tab-collection";
    const raw = JSON.stringify(value);
    localStorage.setItem(key, raw);
    return raw;
  }, SAVE);
  const posts = [];
  page.on("request", (r) => { if (r.method() === "POST") posts.push(r.url()); });
  await word(page, "Cheag alimentar").click();
  await expect(page.getByRole("alert")).toContainText("Colecția s-a schimbat în altă filă.");
  expect(posts).toHaveLength(0);
  expect(await rawSave(page)).toBe(foreign);
});

test("an aged observation rechecks the server and a newer book clears old markers", async ({ page }) => {
  await page.clock.install();
  const state = await miss(page, await begin(page));
  await page.clock.fastForward(31_000);
  const retry = reply(page, `${BASE}/${state.game_id}/combine`);
  await word(page, "Cheag alimentar").click();
  expect((await (await retry).json()).revision).toBe(state.revision + 1);
  await expect(word(page, "Cheag alimentar")).toBeEnabled();
  // Model the GET upgrade contract; backend tests exercise actual compatible recipes.
  await page.route(`**${BASE}/${state.game_id}`, async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    body.compatible_recipe_hashes.push(body.progress.recipe_hash);
    body.progress.recipe_hash = "f".repeat(64);
    body.world.total_recipes += 1;
    body.empty_pairs = [];
    await route.fulfill({ response, json: body });
  }, { times: 1 });
  await page.reload();
  await expect(word(page, "Făină")).toBeEnabled();
  await word(page, "Făină").click();
  await expect(word(page, "Cheag alimentar")).not.toHaveClass(/alchemy-word--tried/);
  expect(JSON.parse(await rawSave(page)).progress.recipe_hash).toBe("f".repeat(64));
});

test("empty feedback and marked keyboard partner fit 320px with doubled text", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 844 });
  await page.addInitScript(() => {
    document.addEventListener("DOMContentLoaded", () => { document.documentElement.style.fontSize = "200%"; });
  });
  await miss(page, await begin(page));
  const partner = word(page, "Cheag alimentar");
  await partner.focus();
  await partner.scrollIntoViewIfNeeded();
  await page.keyboard.press("Enter");
  await expect(partner).toBeFocused();
  await expect(partner).toBeInViewport();
  expect(await page.locator(".alchemy-screen").evaluate((e) => e.scrollWidth <= e.clientWidth + 1)).toBe(true);
  await expect(partner).toContainText("Încercat");
});

for (const committed of [false, true]) {
  test(`identical cached retries cannot restore stale focus after a lost ${committed ? "committed" : "uncommitted"} craft`, async ({ page }) => {
    const state = await miss(page, await begin(page));
    const tried = word(page, "Cheag alimentar");
    await tried.focus();
    await tried.press("Enter");
    await expect(page.getByText(/ai încercat deja această pereche/)).toBeVisible();
    await tried.press("Enter");
    await expect(tried).toBeFocused();
    let combineRequests = 0;
    let recoveryReads = 0;
    page.on("request", (request) => {
      if (request.method() === "GET" && new URL(request.url()).pathname === `${BASE}/${state.game_id}`) recoveryReads += 1;
    });
    // Keep interception active through the immediate recovery GET, as in the
    // depleted-input recovery case: final one-shot teardown can strand that read.
    await page.route(`**${BASE}/${state.game_id}/combine`, async (route) => {
      combineRequests += 1;
      if (combineRequests !== 1) { await route.continue(); return; }
      if (committed) expect((await route.fetch()).status()).toBe(200);
      await route.abort("failed");
    });
    const recovered = reply(page, `${BASE}/${state.game_id}`, "GET");
    await word(page, "Apă").focus();
    await word(page, "Apă").press("Enter");
    const fresh = await (await recovered).json();
    expect(fresh.inventory.some((item) => item.label === "Aluat")).toBe(committed);
    await expect(page.getByText("Colecție sincronizată. Poți continua.")).toBeVisible();
    await expect(tried).not.toBeFocused();
    await expect(word(page, "Făină")).toBeEnabled();
    expect(combineRequests).toBe(1);
    expect(recoveryReads).toBe(1);
  });
}
