import { expect, test } from "@playwright/test";
import { activeKey, games, gameURL, openGameOptions, start } from "./games.mjs";

const day = "2026-11-16";
const game = { ...games.find(({ key }) => key === "lant"), daily: day };

// The standard browser gate keeps board counts off. Use a real daily creation
// and supply the enabled response field for these frontend behavior checks.
async function startReportableDaily(page) {
  await page.clock.setFixedTime(new Date(`${day}T10:00:00Z`));
  await page.route((url) => url.pathname === "/api/wordgames/lant/games", async (route) => {
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    const round = await response.json();
    await route.fulfill({ response, json: { ...round, can_report_give_up: true } });
  }, { times: 1 });
  const initial = await start(page, game);
  expect(initial.daily).toBe(day);
  expect(initial.can_report_give_up).toBe(true);
  return initial;
}

for (const lostResponse of [false, true]) {
  test(`an enabled Lanț give-up shows the server result ${lostResponse ? "after GET recovery" : "from POST"}`, async ({ page }) => {
    const initial = await startReportableDaily(page);
    const path = gameURL(game, initial.game_id);
    const terminal = { ...initial, gave_up: true, won: false, perfect: false, choices: [], steps: 2 };
    delete terminal.can_report_give_up;
    const requests = [];
    page.on("request", (request) => {
      const pathname = new URL(request.url()).pathname;
      if (pathname === path || pathname === `${path}/giveup`) {
        requests.push([request.method(), pathname, request.postData()]);
      }
    });
    await page.route((url) => url.pathname === `${path}/giveup`, (route) => lostResponse
      ? route.fulfill({ status: 503, json: { detail: "Răspuns indisponibil." } })
      : route.fulfill({ json: terminal }));
    await page.route((url) => url.pathname === path, (route) => route.fulfill({ json: terminal }));

    await openGameOptions(page, game);
    await page.getByRole("button", { name: "Renunț la rundă", exact: true }).click();
    const result = page.locator(".game-result");
    await expect(result.getByRole("heading", { name: "Ai renunțat la rundă" })).toBeFocused();
    await expect(result).toContainText(`Ținta era ${initial.target.label}.`);
    await expect(result.getByText("2 pași", { exact: true })).toBeVisible();
    await expect(result.locator(".game-result-perfect, .board-place")).toHaveCount(0);
    await expect.poll(() => page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBeNull();
    expect(requests).toEqual(lostResponse
      ? [["POST", `${path}/giveup`, null], ["GET", path, null]]
      : [["POST", `${path}/giveup`, null]]);
  });
}

test("leaving a reportable daily with the back button keeps it active", async ({ page }) => {
  const initial = await startReportableDaily(page);
  const path = gameURL(game, initial.game_id);
  const requests = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname === `${path}/giveup`) requests.push(request.method());
  });

  await page.getByRole("button", { name: "Înapoi la jocuri", exact: true }).click();
  const link = page.getByRole("link", { name: /Lanțul Cuvintelor/ });
  await expect(link).toBeVisible();
  expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(initial.game_id);

  const resumed = page.waitForResponse((response) =>
    response.request().method() === "GET" && new URL(response.url()).pathname === path);
  await link.click();
  expect((await (await resumed).json()).won).toBe(false);
  await expect(page.locator(game.board)).toBeVisible();
  await expect(page.locator(".game-result")).toHaveCount(0);
  expect(requests).toEqual([]);
});
