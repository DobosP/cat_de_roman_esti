import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";

const BASE = "/api/alchimie/explore";
const SAVE = "cat_alchimie_exploration_v1";
const checkpoint = JSON.parse(readFileSync(new URL("./alchimie-221-checkpoint.json", import.meta.url), "utf8")).collection;
const journal = (page) => page.locator(".alchemy-explore-journal");
const search = (page) => page.getByRole("searchbox", { name: "Caută în rețetele mele" });

async function resumeJournal(page, request) {
  const response = await request.post(BASE, { data: { progress: checkpoint.progress } });
  expect(response.ok()).toBe(true);
  const state = await response.json();
  await page.goto("/alchimie");
  await page.evaluate(({ key, state }) => localStorage.setItem(key, JSON.stringify({
    version: 1, game_id: state.game_id, revision: state.revision,
    progress: state.progress, goal_id: state.goal_id,
    compatible_recipe_hashes: state.compatible_recipe_hashes,
  })), { key: SAVE, state });
  await page.reload();
  await expect(page.locator(".alchemy-inventory-grid")).toBeVisible();
  await journal(page).locator(":scope > summary").click();
  await expect(journal(page).locator("article")).toHaveCount(state.discovered_count);
  return state;
}

test("earned recipes can be found by result or ingredient without accents", async ({ page, request }) => {
  const state = await resumeJournal(page, request);
  expect(state.discovered_count).toBeGreaterThan(100);
  const saved = await page.evaluate((key) => localStorage.getItem(key), SAVE);
  const requests = [];
  page.on("request", (request) => { if (request.url().includes("/api/")) requests.push(request.url()); });
  await search(page).fill("CLATITE");
  await expect(journal(page).locator("article")).not.toHaveCount(0);
  await expect(journal(page).locator("article").first()).toContainText("Clătite");
  await expect(journal(page)).not.toContainText("Nicio rețetă găsită");
  await search(page).fill("faina");
  const recipes = journal(page).locator("article");
  expect(await recipes.count()).toBeGreaterThan(1);
  for (const row of await recipes.all()) await expect(row.locator("h3")).toContainText("Făină");
  expect(await recipes.count()).toBeLessThan(state.discovered_count);
  expect(await page.evaluate((key) => localStorage.getItem(key), SAVE)).toBe(saved);
  expect(requests).toHaveLength(0);
});

test("empty journal search recovers in one action and keeps the crafting selection", async ({ page, request }) => {
  await page.setViewportSize({ width: 320, height: 480 });
  const state = await resumeJournal(page, request);
  await page.locator(".alchemy-word:enabled").first().click();
  const selected = await page.locator(".alchemy-word[aria-pressed=true]").getAttribute("aria-label");
  await search(page).fill("zzzz");
  await expect(journal(page).getByText("Nicio rețetă găsită. Încearcă alt cuvânt sau șterge căutarea.")).toBeVisible();
  await journal(page).locator(":scope > summary").click();
  await expect(journal(page).locator(":scope > summary")).toContainText("Căutare: zzzz");
  await journal(page).locator(":scope > summary").click();
  await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
  const reset = page.getByRole("button", { name: "Șterge căutarea din rețete", exact: true });
  await reset.focus();
  await reset.scrollIntoViewIfNeeded();
  await expect(reset).toBeInViewport();
  expect((await reset.boundingBox()).height).toBeGreaterThanOrEqual(44);
  await page.keyboard.press("Enter");
  await expect(search(page)).toBeFocused();
  await expect(search(page)).toHaveValue("");
  await expect(journal(page).locator("article")).toHaveCount(state.discovered_count);
  await expect(page.locator(".alchemy-word[aria-pressed=true]")).toHaveAttribute("aria-label", selected);
  await search(page).fill("ou");
  await search(page).press("Escape");
  await expect(search(page)).toHaveValue("");
  await expect(page.locator(".alchemy-word[aria-pressed=true]")).toHaveAttribute("aria-label", selected);
  expect(await journal(page).evaluate((element) => element.scrollWidth <= element.clientWidth + 1)).toBe(true);
});

test("a fresh journal exposes no unearned recipes or search controls", async ({ page }) => {
  await page.goto("/alchimie");
  await page.getByRole("button", { name: "Începe explorarea →" }).click();
  await journal(page).locator(":scope > summary").click();
  await expect(journal(page)).toContainText("Prima rețetă apare aici când creezi un cuvânt nou.");
  await expect(journal(page).locator("article")).toHaveCount(0);
  await expect(search(page)).toHaveCount(0);
});
