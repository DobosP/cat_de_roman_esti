import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { games, deterministicStarts } from "./games.mjs";

const game = games.find(({ key }) => key === "alchimie");
const savedCollectionKey = "cat_alchimie_exploration_v1";
const oldCollection = JSON.parse(readFileSync(new URL("./alchimie-111-checkpoint.json", import.meta.url), "utf8")).collection;

async function expectTargetEntry(page) {
  await expect(page.locator(game.board)).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Modul Alchimie" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Începe explorarea →" })).toHaveCount(0);
}

test("Alchimie opens a target round from the Home card and its daily alias resumes it", async ({ page }) => {
  await page.goto("/");
  await page.locator('.games-grid a[href="/alchimie"]').click();
  await expect(page).toHaveURL(/\/alchimie$/);
  await expectTargetEntry(page);
  const target = await page.locator(".alchemy-bench .alchemy-target").textContent();
  await page.goto("/alchimie?challenge=daily");
  await expectTargetEntry(page);
  await expect(page.locator(".alchemy-bench .alchemy-target")).toHaveText(target);
});

test("old Alchimie links open target rounds and preserve the raw exploration save", async ({ page }) => {
  await deterministicStarts(page, game);
  await page.goto("/");
  const raw = JSON.stringify(oldCollection);
  await page.evaluate(({ key, value }) => localStorage.setItem(key, value), { key: savedCollectionKey, value: raw });
  const exploreRequests = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.startsWith("/api/alchimie/explore")) exploreRequests.push(request.url());
  });
  for (const route of ["/alchimie", "/alchimie?mode=challenges", "/alchimie?mode=explore"]) {
    await page.goto(route);
    await expect(page).toHaveURL(new URL(route, page.url()).href);
    await expectTargetEntry(page);
    expect(await page.evaluate((key) => localStorage.getItem(key), savedCollectionKey)).toBe(raw);
  }
  await expect(page.locator(".alchemy-bench .alchemy-target")).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Modul Alchimie" })).toHaveCount(0);
  expect(await page.evaluate((key) => localStorage.getItem(key), savedCollectionKey)).toBe(raw);
  expect(exploreRequests).toEqual([]);
});
