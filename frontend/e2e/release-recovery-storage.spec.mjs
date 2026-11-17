import { test, expect } from "@playwright/test";
import { games, solution, solve, start } from "./games.mjs";

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
    const fresh = await start(page, game);
    expect(fresh.daily).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    await expect(page.getByText("Jocul zilei", { exact: true })).toBeVisible();
  }
  expect(errors).toEqual([]);
});

for (const failure of ["denied", "quota"]) {
  test(`${failure} storage keeps a completed daily and free play until reload`, async ({ page }) => {
    const day = "2026-11-16";
    const game = { ...games.find(({ key }) => key === "intrusul"), daily: day };
    await page.clock.setFixedTime(new Date(`${day}T12:00:00Z`));
    if (failure === "denied") await denySessionStorage(page, true);
    else await page.addInitScript(() => {
      localStorage.setItem("cat_daily_v2_intrusul", "{}");
      const storage = localStorage;
      const set = Storage.prototype.setItem;
      const remove = Storage.prototype.removeItem;
      Storage.prototype.setItem = function (key, value) {
        if (this === storage) throw new DOMException("Storage full", "QuotaExceededError");
        return set.call(this, key, value);
      };
      Storage.prototype.removeItem = function (key) {
        if (this === storage) throw new DOMException("Storage denied", "SecurityError");
        return remove.call(this, key);
      };
    });
    await page.goto("/");
    const card = page.getByRole("link", { name: /^Intrusul / });
    const creates = () => page.waitForResponse((response) =>
      response.request().method() === "POST" && new URL(response.url()).pathname === "/api/wordgames/intrusul/games");
    let created = creates();
    await card.click();
    expect((await (await created).json()).daily).toBe(day);
    await solve(page, game, solution(game).steps);
    const result = page.locator(".game-result");
    await expect(result.getByRole("heading", { level: 2 })).toBeFocused();
    created = creates();
    await result.getByRole("button", { name: "Încă o rundă", exact: true }).click();
    expect((await (await created).json()).daily).toBeUndefined();
    await expect(page.locator(".game-frame-mode")).toHaveText("Rundă liberă");
    await page.getByRole("button", { name: "Înapoi la jocuri", exact: true }).click();
    await expect(card).toContainText("Gata azi");
    await page.reload();
    await expect(card).toBeVisible();
    await expect(card).not.toContainText("Gata azi");
    created = creates();
    await card.click();
    expect((await (await created).json()).daily).toBe(day);
    await expect(page.locator(".game-frame-mode")).toHaveText("Jocul zilei");
  });
}

test("a denied-storage chunk failure offers home and explicit reload without losing a saved round", async ({ page, request }) => {
  const day = "2026-11-16";
  await page.clock.setFixedTime(new Date(`${day}T12:00:00.000Z`));
  const created = await request.post(`/api/wordgames/intrusul/games?daily=${day}`);
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
  await page.getByRole("link", { name: /^Intrusul / }).click();
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
    // A short real delay keeps each failure slow on BOTH documents; the unit test
    // expires every mocked timer to cover a marker-expiry regression.
    await new Promise((resolve) => setTimeout(resolve, 300));
    await route.abort("failed");
  });
  const navigations = documentRequests(page);
  await page.goto("/");
  await page.getByRole("link", { name: /^Intrusul / }).click();
  await expect(page.getByRole("heading", { name: failureTitle, exact: true })).toBeVisible();
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


test("an AccountBar chunk failure leaves Home usable", async ({ page }) => {
  await denySessionStorage(page, true);
  await page.route("**/assets/AccountBar-*.js", (route) => route.abort("failed"));
  const navigations = documentRequests(page);
  // Assert only after the rejected import has reached an error boundary.
  const caught = page.waitForEvent("console", (message) =>
    message.type() === "error" && message.text().includes("AccountBar-"));
  await page.goto("/");
  await caught;
  await expect(page.locator(".games-grid .game-card")).toHaveCount(6);
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: /^Nu am putut încărca/ })).toHaveCount(0);
  expect(navigations).toHaveLength(1);
});
