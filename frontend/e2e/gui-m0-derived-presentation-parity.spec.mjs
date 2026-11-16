// Authored NOT RUN. These are ordinary native API/DOM presentation assertions.
// No private React access, synthetic derived board or backend qualification claim.
import { test, expect } from "@playwright/test";
import { games, gameURL, deterministicStarts, solution, start, solve } from "./games.mjs";

const quick = games.filter(({ derived }) => derived);
const perechi = quick.find(({ key }) => key === "perechi");
const intrusul = quick.find(({ key }) => key === "intrusul");
const escape = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const tile = (page, game, label) => page.locator(game.board).getByRole("button", { name: new RegExp(`^${escape(label)}(?:,|$)`) });
const created = (page, game) => page.waitForResponse((response) => response.request().method() === "POST"
  && new URL(response.url()).pathname === `/api/wordgames/${game.key}/games`);
const actionReply = (page, game, id, action) => page.waitForResponse((response) => response.request().method() === "POST"
  && new URL(response.url()).pathname === `${gameURL(game, id)}/${action}`);
async function heldCreate(page, game) {
  let arrive, release;
  const requested = new Promise((resolve) => { arrive = resolve; });
  const waiting = new Promise((resolve) => { release = resolve; });
  const captured = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname === `/api/wordgames/${game.key}/games`) captured.push(request.url());
  });
  await page.route(`**/api/wordgames/${game.key}/games?*`, async (route) => {
    const url = new URL(route.request().url());
    // Preserve actual starter/previous-ID options; only stabilize the real seed.
    url.searchParams.set("seed", "38");
    const response = await route.fetch({ url: url.toString() });
    expect(response.status()).toBe(200);
    arrive(); await waiting; await route.fulfill({ response });
  }, { times: 1 });
  return { requested, release, captured };
}

for (const game of quick) {
  test(`${game.key} immediate hints spend steps without spending attempts`, async ({ page, request }) => {
    await deterministicStarts(page, game);
    const initial = await start(page, game);
    await expect(page.getByText("Costă un pas.", { exact: true })).toBeVisible();
    const hint = page.getByRole("button", { name: "Indiciu", exact: true });
    let last = initial;
    for (let spent = 1; spent <= initial.hints_left; spent += 1) {
      const response = actionReply(page, game, initial.game_id, "hint");
      await hint.click();
      const received = await response;
      expect(received.status()).toBe(200);
      last = await received.json();
      expect(last.steps).toBe(spent);
      expect(last.remaining_mistakes).toBe(initial.remaining_mistakes);
      expect(last.hints_left).toBe(initial.hints_left - spent);
    }
    await expect(page.getByRole("button", { name: "Fără indicii" })).toBeDisabled();
    const extra = await request.post(gameURL(game, initial.game_id) + "/hint");
    expect(extra.status()).toBe(400);
    const current = await (await request.get(gameURL(game, initial.game_id))).json();
    expect(current.steps).toBe(last.steps);
    expect(current.hint_level).toBe(last.hint_level);
    await expect(page.locator(".coach-line[role=status]"))
      .toContainText(last.clue?.message ?? "Atinge cele două cuvinte marcate.");
  });

  test(`${game.key} held initial creation keeps one pending frame and issues one request`, async ({ page }) => {
    await deterministicStarts(page, game);
    const hold = await heldCreate(page, game), response = created(page, game);
    await page.goto(game.path);
    await hold.requested;
    try {
      await expect(page.locator(".game-frame")).toHaveAttribute("aria-busy", "true");
      await expect(page.locator(game.board)).toHaveCount(0);
      await page.keyboard.press("Enter");
      expect(hold.captured).toHaveLength(1);
    } finally { hold.release(); }
    expect((await response).status()).toBe(200);
    await expect(page.locator(game.board)).toBeVisible();
    await expect(page.locator(".game-frame")).not.toHaveAttribute("aria-busy", "true");
    expect(hold.captured).toHaveLength(1);
  });

  test(`${game.key} held new round disables duplicate result actions`, async ({ page }) => {
    await deterministicStarts(page, game);
    await start(page, game);
    await solve(page, game, solution(game).steps);
    const result = page.locator(".game-result");
    const again = result.getByRole("button", { name: "Încă o rundă" });
    const hold = await heldCreate(page, game), response = created(page, game);
    await again.click();
    await hold.requested;
    try {
      await expect(again).toBeDisabled();
      await expect(page.locator(".game-frame")).toHaveAttribute("aria-busy", "true");
      await again.dispatchEvent("click");
      expect(hold.captured).toHaveLength(1);
    } finally { hold.release(); }
    expect((await response).status()).toBe(200);
    await expect(page.locator(game.board)).toBeVisible();
    await expect(result).toHaveCount(0);
    expect(hold.captured).toHaveLength(1);
  });

  test(`${game.key} only free starts use the starter board option`, async ({ page }) => {
    await deterministicStarts(page, game);
    const first = created(page, game);
    await start(page, game);
    expect(new URL((await first).url()).searchParams.get("starter")).toBe("1");
    await solve(page, game, solution(game).steps);
    await expect.poll(() => page.evaluate((key) =>
      JSON.parse(localStorage.getItem("cat_wordgame_scores_v1") || "{}")[key]?.nonDailyWon, game.key)).toBe(true);
    const next = created(page, game);
    await page.locator(".game-result").getByRole("button", { name: "Încă o rundă" }).click();
    expect(new URL((await next).url()).searchParams.get("starter")).toBe("0");
  });
}

test("Intrusul daily frame identifies today's board without introducing a difficulty label", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2026-10-08T12:00:00.000Z"));
  const response = created(page, intrusul);
  await page.goto(intrusul.path);
  const received = await response;
  expect(received.status()).toBe(200);
  expect((await received.json()).daily).toBe("2026-10-08");
  expect(new URL(received.url()).searchParams.get("starter")).toBeNull();
  const status = page.locator(".game-frame-status");
  await expect(status.getByText("Jocul zilei")).toBeVisible();
  await expect(status).not.toContainText(/nivel|greu|normal|ușor/i);
});

async function keyboardPair(page, state, step, focusedId) {
  const partner = step.payload.ids.find((id) => id !== focusedId);
  const partnerTile = tile(page, perechi, state.tiles.find(({ id }) => id === partner).label);
  await partnerTile.focus(); await page.keyboard.press("Space");
  await expect(partnerTile).toHaveAttribute("aria-pressed", "true");
  const focused = tile(page, perechi, state.tiles.find(({ id }) => id === focusedId).label);
  await focused.focus(); await expect(focused).toBeFocused();
  const response = actionReply(page, perechi, state.game_id, "match");
  await page.keyboard.press("Space"); return response;
}

test("real Perechi earned pairs leave the grid and keyboard focus follows next, wrap and the result owner", async ({ page }) => {
  await deterministicStarts(page, perechi); let state = await start(page, perechi);
  const steps = solution(perechi).steps;
  const middleId = state.tiles[3].id, first = steps.find(({ payload }) => payload.ids.includes(middleId));
  expect(first).toBeDefined();
  const firstReply = await keyboardPair(page, state, first, middleId); expect(firstReply.status()).toBe(200); state = await firstReply.json();
  expect(state.correct).toBe(true); expect(state.solved_count).toBe(1);
  const middleIndex = state.tiles.findIndex(({ id }) => id === middleId);
  const next = state.tiles.slice(middleIndex + 1).find(({ solved }) => !solved);
  expect(next).toBeDefined(); expect(next.id).not.toBe(state.tiles.find(({ solved }) => !solved).id);
  await expect(tile(page, perechi, next.label)).toBeFocused();
  await expect(page.locator(`${perechi.board} button`)).toHaveCount(6);
  const history = page.getByLabel("Perechi găsite", { exact: true });
  await expect(history).toBeVisible();
  const earned = state.solved_pairs[0];
  await expect(history.getByText(earned.label, { exact: true })).toBeVisible();
  await expect(history.getByText(earned.tiles.map(({ label }) => label).join(" + "), { exact: true })).toBeVisible();
  for (const item of earned.tiles) await expect(tile(page, perechi, item.label)).toHaveCount(0);
  const last = state.tiles.filter(({ solved }) => !solved).at(-1);
  const wrapStep = steps.find(({ payload }) => payload.ids.includes(last.id)); expect(wrapStep).toBeDefined();
  const wrapReply = await keyboardPair(page, state, wrapStep, last.id); expect(wrapReply.status()).toBe(200); state = await wrapReply.json();
  expect(state.correct).toBe(true); expect(state.solved_count).toBe(2);
  await expect(tile(page, perechi, state.tiles.find(({ solved }) => !solved).label)).toBeFocused();
  await expect(page.locator(`${perechi.board} button`)).toHaveCount(4);
  for (const pair of state.solved_pairs) await expect(history.getByText(pair.label, { exact: true })).toBeVisible();
  const remainingSteps = steps.filter(({ payload }) => payload.ids.every((id) => !state.tiles.find((item) => item.id === id).solved));
  for (const step of remainingSteps) {
    const response = await keyboardPair(page, state, step, step.payload.ids[1]); expect(response.status()).toBe(200); state = await response.json();
  }
  expect(state.won).toBe(true);
  const heading = page.getByRole("heading", { name: "Toate se potrivesc!", exact: true });
  await expect(heading).toBeVisible();
  await expect(heading).toBeFocused();
});

test("Perechi preserves deliberately moved help focus while a real keyboard match response is held", async ({ page }) => {
  await deterministicStarts(page, perechi); const state = await start(page, perechi), step = solution(perechi).steps[0];
  let arrive, release;
  const requested = new Promise((resolve) => { arrive = resolve; });
  const waiting = new Promise((resolve) => { release = resolve; });
  await page.route(`**${gameURL(perechi, state.game_id)}/match`, async (route) => {
    const response = await route.fetch(); expect(response.status()).toBe(200);
    arrive(); await waiting; await route.fulfill({ response });
  }, { times: 1 });
  const response = keyboardPair(page, state, step, step.payload.ids[1]);
  await requested;
  const help = page.getByRole("button", { name: "Cum se joacă" });
  try { await help.focus(); await expect(help).toBeFocused(); }
  finally { release(); }
  const received = await response; expect(received.status()).toBe(200); const matched = await received.json();
  expect(matched.correct).toBe(true);
  await expect(page.locator(`${perechi.board} button`)).toHaveCount(6);
  // Source-grounded expected failure at the original implementation: its match
  // focus branch lacks the current external-focus guard present in the hint path.
  // Keep the requested contract strict; the owning S1 lane must resolve any failure.
  await expect(help).toBeFocused();
  await expect(page.locator(`${perechi.board} button:focus`)).toHaveCount(0);
});

test("real Perechi terminal loss moves keyboard-owned tile focus to the authoritative result owner", async ({ page, request }) => {
  await deterministicStarts(page, perechi); let state = await start(page, perechi);
  const initial = state, steps = solution(perechi).steps;
  // Same native cross-pair loss path as derived-action-recovery:23–29.
  // Distinct tiles from different real solution pairs make six genuine mistakes.
  const wrongIds = [
    ...steps[0].payload.ids.flatMap((a) => steps[1].payload.ids.map((b) => [a, b])),
    [steps[0].payload.ids[0], steps[2].payload.ids[0]],
    [steps[0].payload.ids[1], steps[2].payload.ids[0]],
  ];
  expect(initial.remaining_mistakes).toBe(wrongIds.length);
  expect(new Set(wrongIds.map((ids) => [...ids].sort((left, right) => left < right ? -1 : left > right ? 1 : 0).join("+"))).size).toBe(wrongIds.length);
  for (const [index, ids] of wrongIds.entries()) {
    const step = { action: "match", payload: { ids } };
    const focused = tile(page, perechi, state.tiles.find(({ id }) => id === ids[1]).label);
    await expect(focused).toBeEnabled();
    const response = await keyboardPair(page, state, step, ids[1]);
    expect(response.status()).toBe(200); state = await response.json();
    expect(state.game_id).toBe(initial.game_id);
    expect(state.correct).toBe(false); expect(state.repeated).toBe(false);
    expect(state.mistakes).toBe(index + 1);
    expect(state.remaining_mistakes).toBe(initial.remaining_mistakes - index - 1);
    expect(state.won).toBe(false); expect(state.lost).toBe(index === wrongIds.length - 1);
    if (!state.lost) await expect(page.locator(`${perechi.board} button`)).toHaveCount(initial.tiles.length);
  }
  const authoritative = await request.get(gameURL(perechi, initial.game_id));
  expect(authoritative.status()).toBe(200); const saved = await authoritative.json();
  expect(saved.lost).toBe(true); expect(saved.won).toBe(false);
  expect(saved.mistakes).toBe(state.mistakes); expect(saved.remaining_mistakes).toBe(0);
  await expect(page.locator(perechi.board)).toHaveCount(0);
  const heading = page.getByRole("heading", { name: "Acestea erau perechile", exact: true });
  await expect(heading).toBeVisible();
  await expect(heading).toBeFocused();
});
