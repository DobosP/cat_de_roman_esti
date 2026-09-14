import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";

const BASE = "/api/alchimie/explore";
const SAVE = "cat_alchimie_exploration_v1";
const checkpoint = JSON.parse(readFileSync(new URL("./alchimie-221-checkpoint.json", import.meta.url), "utf8")).collection;
const responseTo = (page, path) => page.waitForResponse((response) =>
  response.request().method() === "POST" && new URL(response.url()).pathname === path);
const library = (page) => page.getByRole("region", { name: "Colecția ta", exact: true });

for (const width of [320, 390]) {
  test(`a closed search recovers in one action at ${width}px without losing the chosen word`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/alchimie");
    const created = responseTo(page, BASE);
    await page.getByRole("button", { name: "Începe explorarea →" }).click();
    const state = await (await created).json();
    const firstWord = page.locator(".alchemy-word").first();
    const firstLabel = await firstWord.getAttribute("aria-label");
    await firstWord.click();
    await page.locator(".alchemy-library-tools > summary").click();
    await page.getByRole("searchbox", { name: "Caută în colecție" }).fill("zzzz");
    await page.locator(".alchemy-library-tools > summary").click();
    await expect(page.getByRole("searchbox")).not.toBeVisible();
    await expect(page.getByText("Niciun cuvânt găsit.", { exact: true })).toBeVisible();
    const savedBefore = await page.evaluate((key) => localStorage.getItem(key), SAVE);
    const reset = page.getByRole("button", { name: "Șterge căutarea", exact: true });
    await expect(reset).toBeInViewport();
    const box = await reset.boundingBox();
    expect(box.width).toBeGreaterThanOrEqual(44);
    expect(box.height).toBeGreaterThanOrEqual(44);
    const posts = [];
    page.on("request", (request) => { if (request.method() === "POST") posts.push(request.url()); });
    await reset.focus();
    await page.keyboard.press("Enter");
    await expect(page.locator(".alchemy-word")).toHaveCount(state.inventory.length);
    await expect(page.locator(".alchemy-word[aria-pressed=true]")).toHaveAttribute("aria-label", firstLabel);
    await expect(library(page)).toBeFocused();
    await expect(page.locator(".alchemy-library-tools")).not.toHaveAttribute("open", "");
    expect(await page.evaluate((key) => localStorage.getItem(key), SAVE)).toBe(savedBefore);
    expect(posts).toHaveLength(0);
    await page.keyboard.press("Tab");
    await expect(page.locator(".alchemy-library-tools > summary")).toBeFocused();
  });
}

test("a completed collection shows every earned word, searches locally and preserves its journal", async ({ page, request }) => {
  await page.setViewportSize({ width: 320, height: 844 });
  // Start from earned historical progress, then use public hints for later additions.
  // Completion follows the current API rather than a fixed concept count.
  let response = await request.post(BASE, { data: { progress: checkpoint.progress } });
  expect(response.ok()).toBe(true);
  let state = await response.json();
  for (let steps = 0; !state.complete && steps < 256; steps += 1) {
    await request.post(`${BASE}/${state.game_id}/hint`, { data: {} });
    state = await (await request.post(`${BASE}/${state.game_id}/hint`, { data: {} })).json();
    expect(state.hint.stage).toBe("pair");
    const [a, b] = state.hint.pair.map((word) => word.id);
    response = await request.post(`${BASE}/${state.game_id}/combine`, { data: { a, b } });
    expect(response.ok()).toBe(true);
    state = await response.json();
  }
  expect(state.complete).toBe(true);
  await page.goto("/alchimie");
  await page.evaluate(({ key, state }) => localStorage.setItem(key, JSON.stringify({
    version: 1, game_id: state.game_id, revision: state.revision,
    progress: state.progress, goal_id: state.goal_id,
    compatible_recipe_hashes: state.compatible_recipe_hashes,
  })), { key: SAVE, state });
  await page.reload();
  await expect(page.locator(".alchemy-explore-complete")).toBeVisible();
  await expect(page.locator(".alchemy-word")).toHaveCount(state.inventory.length);
  await expect(page.locator(".alchemy-word:enabled")).toHaveCount(0);
  await expect(page.locator(".alchemy-craft-prompt")).toHaveText("Răsfoiește cuvintele sau deschide „Rețetele mele”.");
  await expect(page.locator(".alchemy-workspace")).not.toContainText("Continuă să descoperi");
  await expect(page.getByRole("checkbox")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "💡 O idee?", exact: true })).toHaveCount(0);
  const savedBefore = await page.evaluate((key) => localStorage.getItem(key), SAVE);
  await page.locator(".alchemy-library-tools > summary").click();
  await page.getByRole("searchbox").fill("zzzz");
  await page.locator(".alchemy-library-tools > summary").click();
  await page.getByRole("button", { name: "Șterge căutarea", exact: true }).click();
  await expect(page.locator(".alchemy-word")).toHaveCount(state.inventory.length);
  await page.locator(".alchemy-explore-journal > summary").click();
  await expect(page.locator(".alchemy-journal-entry")).toHaveCount(state.discovered_count);
  expect(await page.evaluate((key) => localStorage.getItem(key), SAVE)).toBe(savedBefore);
  await page.reload();
  await expect(page.locator(".alchemy-word")).toHaveCount(state.inventory.length);
});

test("search reset keeps keyboard recovery visible in a short viewport with doubled text", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 360 });
  await page.goto("/alchimie");
  await page.getByRole("button", { name: "Începe explorarea →" }).click();
  await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
  await page.locator(".alchemy-library-tools > summary").click();
  await page.getByRole("searchbox").fill("zzzz");
  await page.locator(".alchemy-library-tools > summary").click();
  const reset = page.getByRole("button", { name: "Șterge căutarea", exact: true });
  await reset.focus();
  await reset.scrollIntoViewIfNeeded();
  await expect(reset).toBeInViewport();
  await page.keyboard.press("Enter");
  await expect(library(page)).toBeFocused();
  await expect(library(page).getByRole("heading", { name: "Cuvintele tale" })).toBeInViewport();
  expect(await page.locator(".alchemy-screen").evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
});
