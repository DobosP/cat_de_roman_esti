import { test, expect } from "@playwright/test";
import { games, gameURL, deterministicStarts, solution, start, act } from "./games.mjs";

const game = games.find(({ key }) => key === "lant");

test("lant shows the authoritative recovered position while animation frames are paused", async ({ page, request }) => {
  await page.clock.install();
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const position = page.getByText("EȘTI ACUM LA", { exact: true }).locator("..");
  await expect(position.getByText(initial.current.label, { exact: true })).toHaveCSS("opacity", "1");
  // Hold the previous hop's transition pending while the winning response is
  // recovered. Authoritative position must never wait for a decorative exit.
  await page.clock.pauseAt(await page.evaluate(() => Date.now() + 1000));
  const steps = solution(game).steps;
  for (const step of steps.slice(0, -1)) {
    const response = await act(page, game, step);
    expect((await response.json()).won).toBe(false);
  }
  const counts = { reads: 0, mutations: 0 };
  page.on("request", (req) => {
    const path = new URL(req.url()).pathname;
    if (req.method() === "GET" && path === gameURL(game, initial.game_id)) counts.reads += 1;
    if (req.method() === "POST" && path.startsWith(`${gameURL(game, initial.game_id)}/`)) counts.mutations += 1;
  });
  await page.route(`**${gameURL(game, initial.game_id)}/move`, async (route) => {
    const committed = await route.fetch();
    expect(committed.status()).toBe(200);
    expect((await committed.json()).won).toBe(true);
    await route.fulfill({ status: 503, contentType: "application/json", body: "{}" });
  }, { times: 1 });
  expect((await act(page, game, steps.at(-1))).status()).toBe(503);
  await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.won).toBe(true);
  expect(server.moves).toBe(steps.length);
  expect(counts).toEqual({ reads: 1, mutations: 1 });
  await expect(position.getByText(server.current.label, { exact: true })).toHaveCSS("opacity", "1");
  await expect(position.locator(".lant-route-word")).toHaveCount(1);
  await page.clock.resume();
  await expect(page.getByRole("status").filter({ has: page.getByRole("button", { name: "Copiază rezultatul" }) })).toHaveCSS("opacity", "1");
  await page.screenshot({ path: test.info().outputPath("authoritative-position.png"), fullPage: true });
});
