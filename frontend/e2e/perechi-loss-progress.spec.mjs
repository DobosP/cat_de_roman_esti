// Valid until: Cat e092478aa3737f7956c9730caa809a7932bfdbb9 or this draft changes — then treat as history.
// SOURCE CANDIDATE ONLY: authored cases, NOT RUN, NOT APPLIED.
// Uses the actual React /perechi route and saved-game/match API boundaries.
// Synthetic presentation fixtures are not backend/content, 16/78, device or release proof.
// Keep v42-derived-loss-and-starter.test.mjs unchanged until real equivalent coverage earns replacement.
import { expect, test } from "@playwright/test";

const ACTIVE_KEY = "cat_active_game_v1_perechi";
const PAIRS = [
  { label: "Pereche de test unu", tiles: [{ id: "p1a", label: "Cuvânt unu A" }, { id: "p1b", label: "Cuvânt unu B" }] },
  { label: "Pereche de test doi", tiles: [{ id: "p2a", label: "Cuvânt doi A" }, { id: "p2b", label: "Cuvânt doi B" }] },
  { label: "Pereche de test trei", tiles: [{ id: "p3a", label: "Cuvânt trei A" }, { id: "p3b", label: "Cuvânt trei B" }] },
  { label: "Pereche de test patru", tiles: [{ id: "p4a", label: "Cuvânt patru A" }, { id: "p4b", label: "Cuvânt patru B" }] },
];

function liveState(gameId, solvedCount, mistakes) {
  return {
    game_id: gameId,
    tiles: PAIRS.flatMap((pair, index) => pair.tiles.map((tile) => ({ ...tile, solved: index < solvedCount }))),
    solved_pairs: PAIRS.slice(0, solvedCount),
    solved_count: solvedCount,
    remaining_pairs: 4 - solvedCount,
    mistakes,
    remaining_mistakes: 6 - mistakes,
    actions: solvedCount + mistakes,
    hint_available: mistakes >= 2,
    hints_used: 0,
    won: false,
    lost: false,
  };
}

function lossResponse(live) {
  return {
    ...live,
    mistakes: 6,
    remaining_mistakes: 0,
    actions: live.actions + 1,
    hint_available: false,
    lost: true,
    score: 0,
    share: `cat_de_roman_esti · Perechi · 6 greșeli\n${"🟩".repeat(live.solved_count)}${"⬜".repeat(4 - live.solved_count)}`,
    solution: PAIRS,
    ok: true,
    correct: false,
    repeated: false,
  };
}

function winResponse(live) {
  return {
    ...liveState(live.game_id, 4, 0),
    hint_available: false,
    won: true,
    score: 1000,
    share: "cat_de_roman_esti · Perechi · 0 greșeli\n🟩🟩🟩🟩",
    solution: PAIRS,
    ok: true,
    correct: true,
    pair: PAIRS[3],
  };
}

async function installPresentationFixture(page, live, response, expectedIds = []) {
  const unexpected = [];
  let release;
  let observe;
  const held = new Promise((resolve) => { release = resolve; });
  const matched = new Promise((resolve) => { observe = resolve; });
  let matchSeen = false;

  await page.addInitScript(({ key, gameId }) => {
    window.localStorage.setItem(key, gameId);
  }, { key: ACTIVE_KEY, gameId: live.game_id });

  await page.route("**/api/wordgames/perechi/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    const sessionPath = `/api/wordgames/perechi/games/${live.game_id}`;
    if (request.method() === "GET" && pathname === sessionPath) {
      await route.fulfill({ status: 200, json: live });
      return;
    }
    if (response && !matchSeen && request.method() === "POST" && pathname === `${sessionPath}/match`) {
      matchSeen = true;
      observe({ method: request.method(), pathname, body: request.postDataJSON() });
      await held;
      await route.fulfill({ status: 200, json: response });
      return;
    }
    unexpected.push({ method: request.method(), pathname });
    await route.fulfill({ status: 500, json: { detail: "Unexpected presentation-fixture request" } });
  });

  const resumed = page.waitForResponse((item) => item.request().method() === "GET"
    && new URL(item.url()).pathname === `/api/wordgames/perechi/games/${live.game_id}`);
  await page.goto("/perechi");
  expect((await resumed).status()).toBe(200);
  await expect(page.locator(".perechi-grid")).toBeVisible();
  await expect(page.locator(".perechi-grid").getByRole("button")).toHaveCount(8 - 2 * live.solved_count);
  await expect(page.locator(".perechi-solved-row")).toHaveCount(live.solved_count);
  expect(unexpected).toEqual([]);
  return { matched, release, unexpected, expectedIds };
}

const lossLine = (page) => page.getByText(/^Ai găsit [0-4] din 4 perechi\.$/);

async function expectNoReveal(page, solvedCount) {
  await expect(page.locator(".perechi-solution")).toHaveCount(0);
  await expect(lossLine(page)).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Acestea erau perechile", exact: true })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Toate se potrivesc!", exact: true })).toHaveCount(0);
  // Earned pair labels may already appear in solved rows; unearned pair labels must not.
  for (const pair of PAIRS.slice(solvedCount)) {
    await expect(page.getByText(pair.label, { exact: true })).toHaveCount(0);
  }
}

async function submitHeldPair(page, fixture, live) {
  try {
    for (const id of fixture.expectedIds) {
      const tile = live.tiles.find((item) => item.id === id);
      await page.locator(".perechi-grid").getByRole("button", { name: tile.label, exact: true }).click();
    }
    expect(await fixture.matched).toEqual({
      method: "POST",
      pathname: `/api/wordgames/perechi/games/${live.game_id}/match`,
      body: { ids: fixture.expectedIds },
    });
    await expect(page.locator(".perechi-grid").getByRole("button").first()).toBeDisabled();
    await expectNoReveal(page, live.solved_count);
  } finally {
    fixture.release();
  }
}

for (const solvedCount of [0, 1, 2]) {
  test(`Perechi loss progress renders ${solvedCount} earned pairs out of four only after the terminal match`, async ({ page }) => {
    const live = liveState(`loss-progress-${solvedCount}`, solvedCount, 5);
    // Two remaining words from different pairs make an incorrect sixth attempt.
    const ids = [PAIRS[solvedCount].tiles[0].id, PAIRS[solvedCount + 1].tiles[0].id];
    const fixture = await installPresentationFixture(page, live, lossResponse(live), ids);
    await expectNoReveal(page, solvedCount);
    await submitHeldPair(page, fixture, live);

    await expect(page.getByRole("heading", { name: "Acestea erau perechile", exact: true })).toBeVisible();
    const progress = page.locator(".perechi-solution > p");
    await expect(progress).toHaveCount(1);
    expect(await progress.evaluate((node) => node.tagName)).toBe("P");
    await expect(progress).toHaveText(`Ai găsit ${solvedCount} din 4 perechi.`);
    await expect(lossLine(page)).toHaveCount(1);
    for (const [property, value] of [["margin-top", "0px"], ["margin-right", "0px"], ["margin-bottom", "2px"], ["margin-left", "0px"]]) {
      await expect(progress).toHaveCSS(property, value);
    }
    await expect(page.locator(".perechi-solution > span > strong")).toHaveText(PAIRS.map((pair) => pair.label));
    expect(fixture.unexpected).toEqual([]);
  });
}

test("Perechi win reveals all four pairs without the loss-progress paragraph", async ({ page }) => {
  const live = liveState("loss-progress-win", 3, 0);
  const ids = PAIRS[3].tiles.map((tile) => tile.id);
  const fixture = await installPresentationFixture(page, live, winResponse(live), ids);
  await expectNoReveal(page, live.solved_count);
  await submitHeldPair(page, fixture, live);
  await expect(page.getByRole("heading", { name: "Toate se potrivesc!", exact: true })).toBeVisible();
  await expect(page.locator(".perechi-solution > span > strong")).toHaveText(PAIRS.map((pair) => pair.label));
  await expect(page.locator(".perechi-solution > p")).toHaveCount(0);
  await expect(lossLine(page)).toHaveCount(0);
  expect(fixture.unexpected).toEqual([]);
});

test("Perechi terminal loss without solution does not render a reveal or progress paragraph", async ({ page }) => {
  const live = liveState("loss-progress-no-solution", 1, 5);
  const response = lossResponse(live);
  delete response.solution;
  // Defensive guard case: the actual service normally includes solution on terminal responses.
  const ids = [PAIRS[1].tiles[0].id, PAIRS[2].tiles[0].id];
  const fixture = await installPresentationFixture(page, live, response, ids);
  await expectNoReveal(page, live.solved_count);
  await submitHeldPair(page, fixture, live);
  // This positive state-transition witness precedes the negative reveal assertions.
  await expect(page.locator(".perechi-grid")).toHaveCount(0);
  await expectNoReveal(page, live.solved_count);
  expect(fixture.unexpected).toEqual([]);
});

test("Perechi live response with unexpected solution still hides unearned answers and progress", async ({ page }) => {
  const live = { ...liveState("loss-progress-not-finished", 2, 5), solution: PAIRS };
  // Defensive guard case: a legitimate live service response does not contain solution.
  const fixture = await installPresentationFixture(page, live);
  await expectNoReveal(page, live.solved_count);
  await expect(page.locator(".perechi-grid").getByRole("button").first()).toBeEnabled();
  expect(fixture.unexpected).toEqual([]);
});
