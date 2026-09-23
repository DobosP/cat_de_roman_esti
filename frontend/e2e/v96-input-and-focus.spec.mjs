/* global document, innerWidth */
import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";

const BASE = "/api/alchimie/explore";
const word = (p, label) => p.locator(".alchemy-inventory-grid").getByRole("button", { name: new RegExp(`^${label}(?:,|$)`) });
const response = (p, path, method = "POST") => p.waitForResponse(r => r.request().method() === method && new URL(r.url()).pathname === path);
async function begin(page) {
  await page.goto("/alchimie");
  const pending = response(page, BASE);
  await page.getByRole("button", { name: "Începe explorarea →" }).click();
  return (await pending).json();
}
for (const committed of [false, true]) for (const moved of [false, true]) {
  test(`recovery of ${committed ? "committed" : "uncommitted"} crafting ${moved ? "respects moved focus" : "restores activated word"}`, async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 844 });
    await page.addInitScript(() => document.addEventListener("DOMContentLoaded", () => { document.documentElement.style.fontSize = "200%"; }));
    const state = await begin(page);
    let release;
    const gate = new Promise(resolve => { release = resolve; });
    let combineRequests = 0;
    let recoveryReads = 0;
    page.on("request", request => {
      if (request.method() === "GET" && new URL(request.url()).pathname === `${BASE}/${state.game_id}`) recoveryReads += 1;
    });
    // Retain the interceptor through recovery, matching the depleted-input case
    // below; removing the final one-shot route can strand the immediate GET.
    await page.route(`**${BASE}/${state.game_id}/combine`, async route => {
      combineRequests += 1;
      if (combineRequests !== 1) { await route.continue(); return; }
      if (committed) expect((await route.fetch()).status()).toBe(200);
      await gate;
      await route.abort("failed");
    });
    await word(page, "Făină").click();
    await word(page, "Apă").focus();
    const post = page.waitForRequest(r => r.url().endsWith("/combine"));
    await word(page, "Apă").press("Enter");
    await post;
    const library = page.getByRole("region", { name: "Colecția ta" });
    if (moved) await library.focus();
    const recovered = response(page, `${BASE}/${state.game_id}`, "GET");
    release();
    const fresh = await (await recovered).json();
    expect(fresh.inventory.some(i => i.label === "Aluat")).toBe(committed);
    await expect(page.getByText("Colecție sincronizată. Poți continua.")).toBeVisible();
    await expect(moved ? library : word(page, "Apă")).toBeFocused();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    if (!moved) {
      const box = await word(page, "Apă").boundingBox();
      expect(box.y).toBeGreaterThanOrEqual(0);
      expect(box.y + box.height).toBeLessThanOrEqual(844);
    }
    expect(combineRequests).toBe(1);
    expect(recoveryReads).toBe(1);
  });
}

test("unsupported Cald sau Rece words are explicitly free and do not suggest unrelated spelling", async ({ page }) => {
  await page.goto("/cald-rece");
  const created = response(page, "/api/wordgames/contexto/games");
  await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
  const state = await (await created).json();
  const field = page.getByRole("textbox", { name: "Concept de ghicit" });
  for (const text of ["fier", "reparație", "scule", "rechizite"]) {
    await field.fill(text);
    const guessed = response(page, `/api/wordgames/contexto/games/${state.game_id}/guess`);
    await field.press("Enter");
    const result = await (await guessed).json();
    expect(result.ok).toBe(false);
    expect(result.attempts).toBe(0);
    expect(result.suggestions).not.toContain("fluier");
    expect(result.suggestions).not.toContain("pârâu");
    await expect(page.locator(".card").getByText(/Nu ai pierdut nicio încercare/)).toBeVisible();
    await expect(field).toHaveValue(text);
    await expect(field).toBeFocused();
  }
});

test("a lost final craft restores collection focus when both inputs are depleted", async ({ page }) => {
  const checkpoint = JSON.parse(readFileSync(new URL("./alchimie-221-checkpoint.json", import.meta.url), "utf8")).collection;
  checkpoint.revision = 85;
  checkpoint.goal_id = null;
  checkpoint.progress.discoveries = checkpoint.progress.discoveries.slice(0, 85);
  await page.goto("/alchimie");
  await page.evaluate(value => localStorage.setItem("cat_alchimie_exploration_v1", JSON.stringify(value)), checkpoint);
  const restored = response(page, BASE);
  await page.reload();
  const state = await (await restored).json();
  let combineRequests = 0;
  let recoveryReads = 0;
  page.on("request", request => {
    if (request.method() === "GET" && new URL(request.url()).pathname === `${BASE}/${state.game_id}`) recoveryReads += 1;
  });
  // Keep interception active while abort triggers GET: removing the final one-shot
  // route can race Chromium's interception teardown and strand that recovery read.
  await page.route(`**${BASE}/${state.game_id}/combine`, async route => {
    combineRequests += 1;
    if (combineRequests !== 1) { await route.continue(); return; }
    const committed = await route.fetch();
    expect(committed.status()).toBe(200);
    await route.abort("failed");
  });
  await word(page, "Lipie").click();
  await word(page, "Friptură").focus();
  const recovered = response(page, `${BASE}/${state.game_id}`, "GET");
  await word(page, "Friptură").press("Enter");
  const fresh = await (await recovered).json();
  expect(fresh.inventory.some(i => i.label === "Șaorma cu de toate")).toBe(true);
  await expect(page.getByRole("region", { name: "Colecția ta" })).toBeFocused();
  expect(combineRequests).toBe(1);
  expect(recoveryReads).toBe(1);
});
