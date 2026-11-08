import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { games, deterministicStarts, start } from "./games.mjs";

const game = games.find(({ key }) => key === "alchimie");
const savedCollectionKey = "cat_alchimie_exploration_v1";
const oldCollection = JSON.parse(readFileSync(new URL("./alchimie-111-checkpoint.json", import.meta.url), "utf8")).collection;

async function expectTargetEntry(page) {
  await expect(page.locator(".game-intro")).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Modul Alchimie" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Începe explorarea →" })).toHaveCount(0);
}

test("the daily circuit and arcade card open the same target game", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Deschide Alchimie — neterminat azi", exact: true }).click();
  await expect(page).toHaveURL(/\/alchimie\?.*challenge=daily/);
  await expectTargetEntry(page);
  await expect(page.getByRole("button", { name: "Joacă provocarea zilei", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true }).click();
  await page.getByRole("button", { name: /^Joacă Alchimie —/ }).click();
  await expect(page).toHaveURL(/\/alchimie$/);
  await expectTargetEntry(page);
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
  const initial = await start(page, { ...game, path: "/alchimie?mode=explore" });
  await expect(page.locator(".alchemy-bench .alchemy-target")).toContainText(initial.target.label);
  await expect(page.getByRole("navigation", { name: "Modul Alchimie" })).toHaveCount(0);
  expect(await page.evaluate((key) => localStorage.getItem(key), savedCollectionKey)).toBe(raw);
  expect(exploreRequests).toEqual([]);
});
