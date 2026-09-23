import { test, expect } from "@playwright/test";
import { games, start, deterministicStarts } from "./games.mjs";

const chunk = "**/assets/Intrusul-*.js";
const activeKey = "cat_active_game_v1_intrusul";
const recoveryKey = "cat_release_recovery_v1";
const failureTitle = "Nu am putut încărca jocul.";

async function denySessionStorage(page, both = false) {
  await page.addInitScript((names) => {
    for (const name of names) Object.defineProperty(globalThis, name, {
      configurable: true,
      get() { throw new DOMException("Storage denied", "SecurityError"); },
    });
  }, both ? ["sessionStorage", "localStorage"] : ["sessionStorage"]);
}

function documentRequests(page) {
  const requests = [];
  page.on("request", (request) => {
    if (request.isNavigationRequest() && request.frame() === page.mainFrame()) requests.push(request);
  });
  return requests;
}

test("denied localStorage and sessionStorage getters still allow all six games", async ({ page }) => {
  await denySessionStorage(page, true);
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
  await expect(page.locator(".games-grid .game-card")).toHaveCount(6);
  for (const game of games) {
    await deterministicStarts(page, game);
    await start(page, game);
  }
  // Alchimie's default exploration entry must also work without local storage.
  await page.goto("/alchimie");
  const explored = page.waitForResponse((response) => response.request().method() === "POST" &&
    new URL(response.url()).pathname === "/api/alchimie/explore");
  await page.getByRole("button", { name: "Începe explorarea →" }).click();
  expect((await explored).status()).toBe(200);
  await expect(page.locator(".alchemy-inventory-grid")).toBeVisible();
  expect(errors).toEqual([]);
});

test("a denied-storage chunk failure offers home and explicit reload without losing a saved round", async ({ page, request }) => {
  const created = await request.post("/api/wordgames/intrusul/games?seed=38");
  expect(created.status()).toBe(200);
  const saved = await created.json();
  await page.addInitScript(({ key, id }) => localStorage.setItem(key, id), { key: activeKey, id: saved.game_id });
  await denySessionStorage(page);
  await page.route(chunk, (route) => route.abort("failed"));
  const navigations = documentRequests(page);
  const creates = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname === "/api/wordgames/intrusul/games") creates.push(request.url());
  });

  await page.goto("/intrusul");
  await expect(page.getByRole("heading", { name: failureTitle, exact: true })).toBeFocused();
  await expect(page.getByRole("alert")).toContainText("Reîncarcă pagina sau alege alt joc.");
  expect(navigations).toHaveLength(1);
  expect(await page.evaluate((key) => localStorage.getItem(key), activeKey)).toBe(saved.game_id);

  await page.getByRole("link", { name: "Înapoi la jocuri", exact: true }).click();
  await expect(page.locator(".games-grid .game-card")).toHaveCount(6);
  await page.getByRole("button", { name: /^Joacă Intrusul —/ }).click();
  await expect(page.getByRole("heading", { name: failureTitle, exact: true })).toBeVisible();
  expect(navigations).toHaveLength(1);

  await page.unroute(chunk);
  const loaded = page.waitForResponse((response) => response.request().isNavigationRequest());
  await page.getByRole("button", { name: "Reîncarcă pagina", exact: true }).click();
  await loaded;
  await expect(page.locator(".intrusul-grid")).toBeVisible();
  expect(navigations).toHaveLength(2);
  expect(creates).toHaveLength(0);
  expect(await page.evaluate((key) => localStorage.getItem(key), activeKey)).toBe(saved.game_id);
});

test("a slowly failing chunk reloads once then exposes recovery on the next document", async ({ page }) => {
  await page.route(chunk, async (route) => {
    // Exceed the previous 10-second marker expiry on BOTH documents.
    await new Promise((resolve) => setTimeout(resolve, 11_000));
    await route.abort("failed");
  });
  const navigations = documentRequests(page);
  await page.goto("/");
  await page.getByRole("button", { name: /^Joacă Intrusul —/ }).click();
  await expect(page.getByRole("heading", { name: failureTitle, exact: true })).toBeVisible({ timeout: 30_000 });
  expect(navigations).toHaveLength(2);
  expect(await page.evaluate((key) => sessionStorage.getItem(key), recoveryKey)).toBe("/intrusul");
  const suppressed = await page.evaluate(() => Array.from({ length: 3 }, () => {
    const error = new Event("vite:preloadError", { cancelable: true });
    globalThis.dispatchEvent(error);
    return error.defaultPrevented;
  }));
  expect(suppressed).toEqual([false, false, false]);
  expect(navigations).toHaveLength(2);
});


test("an AccountBar chunk failure also reaches a readable bounded recovery screen", async ({ page }) => {
  await denySessionStorage(page, true);
  await page.route("**/assets/AccountBar-*.js", (route) => route.abort("failed"));
  const navigations = documentRequests(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: failureTitle, exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Reîncarcă pagina", exact: true })).toBeEnabled();
  expect(navigations).toHaveLength(1);
  await page.unroute("**/assets/AccountBar-*.js");
  await page.getByRole("button", { name: "Reîncarcă pagina", exact: true }).click();
  await expect(page.locator(".games-grid .game-card")).toHaveCount(6);
  expect(navigations).toHaveLength(2);
});
