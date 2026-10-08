// Authored NOT RUN. These are ordinary native API/DOM presentation assertions.
// No private React access, synthetic derived board or backend qualification claim.
import { test, expect } from "@playwright/test";
import { games, gameURL, deterministicStarts, solution, start, act, solve } from "./games.mjs";

const quick = games.filter(({ derived }) => derived);
const perechi = quick.find(({ key }) => key === "perechi");
const intrusul = quick.find(({ key }) => key === "intrusul");
const STARTER = "Primele runde sunt mai blânde. Câștigă una și deblochezi tot catalogul.";
const escape = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const tile = (page, game, label) => page.locator(game.board).getByRole("button", { name: new RegExp(`^${escape(label)}(?:,|$)`) });
const created = (page, game) => page.waitForResponse((response) => response.request().method() === "POST"
  && new URL(response.url()).pathname === `/api/wordgames/${game.key}/games`);
const actionReply = (page, game, id, action) => page.waitForResponse((response) => response.request().method() === "POST"
  && new URL(response.url()).pathname === `${gameURL(game, id)}/${action}`);
const hintLabel = (game) => game.key === "intrusul" ? "💡 Arată indiciul · −150 pct" : "💡 Arată o pereche · −150 pct";
const remaining = (value) => `${value} ${value === 1 ? "rămasă" : "rămase"}`;

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
  test(`${game.key} exposes its exact initial locked-hint threshold and only prices the unlocked action`, async ({ page }) => {
    await deterministicStarts(page, game);
    const initial = await start(page, game), steps = solution(game).steps;
    const lockedText = game.key === "intrusul"
      ? "Indiciu disponibil după prima greșeală." : "Indiciu disponibil după două greșeli.";
    await expect(page.getByText(lockedText, { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: hintLabel(game), exact: true })).toHaveCount(0);
    const header = page.locator(".game-shell-header");
    await expect(header.getByText("GREȘELI", { exact: true })).toBeVisible();
    await expect(header.getByText(remaining(initial.remaining_mistakes), { exact: true })).toBeVisible();
    const wrong = game.key === "intrusul"
      ? initial.tiles.filter(({ id }) => id !== steps[0].payload.id).slice(0, 1)
        .map(({ id, label }) => ({ action: "guess", payload: { id }, labels: [label] }))
      : steps[1].payload.ids.map((id) => ({ action: "match", payload: { ids: [steps[0].payload.ids[0], id] },
        labels: [steps[0].payload.ids[0], id].map((key) => initial.tiles.find(({ id }) => id === key).label) }));
    let state;
    for (const [index, step] of wrong.entries()) {
      const response = await act(page, game, step); expect(response.status()).toBe(200); state = await response.json();
      expect(state.won).toBe(false); expect(state.lost).toBe(false);
      expect(state.remaining_mistakes).toBe(initial.remaining_mistakes - index - 1);
      await expect(header.getByText(remaining(state.remaining_mistakes), { exact: true })).toBeVisible();
      if (game.key === "perechi" && index === 0) {
        await expect(page.getByText(lockedText, { exact: true })).toBeVisible();
        await expect(page.getByRole("button", { name: hintLabel(game), exact: true })).toHaveCount(0);
      }
    }
    expect(state.hint_available).toBe(true);
    const hint = page.getByRole("button", { name: hintLabel(game), exact: true });
    await expect(hint).toBeVisible(); await expect(hint).toBeEnabled();
    await expect(page.getByText(lockedText, { exact: true })).toHaveCount(0);
    await expect(hint).toHaveAttribute("title", game.key === "intrusul"
      ? "Arată legătura celor trei cuvinte. Costă 150 de puncte."
      : "Marchează o pereche nerezolvată. Costă 150 de puncte.");
  });

  test(`${game.key} successful held creation has exact busy header copy and one native create`, async ({ page }) => {
    await deterministicStarts(page, game); await page.goto(game.path);
    const hold = await heldCreate(page, game), response = created(page, game);
    const play = page.getByRole("button", { name: /^Joacă(?: →)?$/ });
    await play.click(); await hold.requested;
    try {
      const header = page.getByRole("button", { name: "Se pregătește jocul", exact: true });
      await expect(header).toBeDisabled(); await expect(header).toHaveAttribute("aria-busy", "true");
      await expect(header).toContainText("Se pregătește…");
      await expect(play).toBeDisabled();
      await expect(page.locator(".game-intro")).toHaveAttribute("inert", "");
      await expect(page.locator(".game-intro")).toHaveAttribute("aria-busy", "true");
      await play.dispatchEvent("click"); await header.dispatchEvent("click");
      await page.keyboard.press("Enter"); expect(hold.captured).toHaveLength(1);
    } finally { hold.release(); }
    const received = await response; expect(received.status()).toBe(200);
    await expect(page.locator(game.board)).toBeVisible();
    const exit = page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true });
    await expect(exit).toBeEnabled(); await expect(exit).not.toHaveAttribute("aria-busy", "true");
    expect(hold.captured).toHaveLength(1);
  });

  test(`${game.key} successful held replay disables result actions and retains exact pending labels with one create`, async ({ page }) => {
    await deterministicStarts(page, game); await start(page, game);
    const won = await solve(page, game, solution(game).steps); expect(won.won).toBe(true);
    const copy = page.getByRole("button", { name: "Copiază rezultatul", exact: true });
    await expect(copy).toBeVisible();
    const hold = await heldCreate(page, game), response = created(page, game);
    await page.getByRole("button", { name: "Încă unul →", exact: true }).click();
    await hold.requested;
    try {
      const pending = page.getByRole("button", { name: "Se pregătește…", exact: true });
      await expect(pending).toBeDisabled(); await expect(copy).toBeDisabled();
      await expect(page.getByRole("button", { name: "Meniu", exact: true })).toBeDisabled();
      const header = page.getByRole("button", { name: "Se pregătește jocul", exact: true });
      await expect(header).toBeDisabled(); await expect(header).toHaveAttribute("aria-busy", "true");
      await expect(header).toContainText("Se pregătește…");
      await pending.dispatchEvent("click"); await page.keyboard.press("Enter");
      expect(hold.captured).toHaveLength(1);
    } finally { hold.release(); }
    const received = await response; expect(received.status()).toBe(200);
    await expect(page.locator(game.board)).toBeVisible();
    await expect(copy).toHaveCount(0); expect(hold.captured).toHaveLength(1);
  });

  test(`${game.key} starter explanation is visible before graduation and absent on its later intro`, async ({ page }) => {
    await deterministicStarts(page, game); await page.goto(game.path);
    await expect(page.getByText(STARTER, { exact: true })).toBeVisible();
    await start(page, game); const won = await solve(page, game, solution(game).steps); expect(won.won).toBe(true);
    await expect.poll(() => page.evaluate((key) => JSON.parse(localStorage.getItem("cat_wordgame_scores_v1") || "{}")[key]?.nonDailyWon, game.key)).toBe(true);
    await page.getByRole("button", { name: "Meniu", exact: true }).click();
    await expect(page).toHaveURL(/\/$/); await page.goto(game.path);
    await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeVisible();
    await expect(page.getByText(STARTER, { exact: true })).toHaveCount(0);
  });
}

test("Intrusul daily HUD shows only daily/error state without an invented level badge", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2026-10-08T12:00:00.000Z"));
  await deterministicStarts(page, intrusul); await page.goto(intrusul.path);
  const response = created(page, intrusul);
  await page.getByRole("button", { name: "Provocarea zilei", exact: true }).click();
  const received = await response; expect(received.status()).toBe(200); const state = await received.json();
  expect(state.daily).toBe("2026-10-08");
  const header = page.locator(".game-shell-header");
  await expect(header.getByText("ZILNIC", { exact: true })).toBeVisible();
  await expect(header.getByText("GREȘELI", { exact: true })).toBeVisible();
  await expect(header.getByText(remaining(state.remaining_mistakes), { exact: true })).toBeVisible();
  await expect(header.getByText("NIVEL", { exact: true })).toHaveCount(0);
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
  const owner = page.locator('div[tabindex="-1"]').filter({ has: heading });
  await expect(owner).toHaveCount(1); await expect(owner).toBeFocused();
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
  const help = page.locator(".game-help > summary");
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
  expect(new Set(wrongIds.map((ids) => [...ids].sort().join("+"))).size).toBe(wrongIds.length);
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
  const owner = page.locator('div[tabindex="-1"]').filter({ has: heading });
  await expect(owner).toHaveCount(1); await expect(owner).toBeFocused();
});
