// Authored M0 behavior replacements on original E092; NOT RUN or qualification.
// Existing tests, original16/78 and inventory remain unchanged until real parity passes.
// Account/history inputs are explicit fictional adult presentation fixtures. Gameplay
// runs through the real local Go server and existing native solution helpers.
import { test, expect } from "@playwright/test";
import { games, deterministicStarts, solution, solve, tabTo } from "./games.mjs";

const SCORE_KEY = "cat_wordgame_scores_v1";
const FIXED_TIME = "2026-10-08T12:00:00.000Z";
const FIXED_MS = Date.parse(FIXED_TIME);
const TITLES = ["Alchimie", "Intrusul", "Perechi", "Conexiuni", "Cald sau Rece", "Lanțul Cuvintelor"];
const DISABLED_ME = { accounts_enabled: false, authenticated: false, user: null };
const SAVED_RECEIPT = "77777777-7777-4777-8777-777777777777";
const LOCAL_ENTRY = { score: 500, detail: "Rezultat local de test", at: FIXED_MS, puzzleKey: "local-existing", difficulty: "normal" };

function existingHistory() {
  return {
    alchimie: {
      best: LOCAL_ENTRY, played: 1, recent: [LOCAL_ENTRY],
      completedNonDaily: true, nonDailyCompletions: 1, nonDailyWon: true,
    },
    _completionReceipts: { version: 1, games: { alchimie: [{ id: SAVED_RECEIPT, at: FIXED_MS }] } },
  };
}

async function historyFixture(page, history) {
  await page.clock.setFixedTime(new Date(FIXED_TIME));
  // Seed only the fresh test context. Reloads must retain genuine application writes.
  await page.addInitScript(({ key, history }) => {
    if (localStorage.getItem(key) === null) localStorage.setItem(key, JSON.stringify(history));
  }, { key: SCORE_KEY, history });
}

async function anonymous(page) {
  await page.route("**/api/me", (route) => route.fulfill({ json: DISABLED_ME }));
}

const createPath = (game) => `/api/wordgames/${game.key}/games`;
const creation = (page, game) => page.waitForResponse((response) => response.request().method() === "POST"
  && new URL(response.url()).pathname === createPath(game));
const storedScores = (page) => page.evaluate((key) => localStorage.getItem(key), SCORE_KEY);

async function openFreeFromHome(page, game) {
  await page.getByRole("button", { name: new RegExp(`^Joacă ${TITLES[games.indexOf(game)]} —`) }).click();
  const created = creation(page, game);
  await page.getByRole("button", { name: /^Joacă(?: →)?$/, exact: true }).click();
  const response = await created;
  expect(response.status()).toBe(200);
  const state = await response.json();
  await expect(page.locator(game.board)).toBeVisible();
  return { response, state };
}

async function completeFree(page, game) {
  const created = await openFreeFromHome(page, game);
  const terminal = await solve(page, game, solution(game).steps);
  await expect(page.getByRole("button", { name: "Copiază rezultatul", exact: true })).toBeVisible();
  await expect.poll(async () => JSON.parse(await storedScores(page))[game.key]?.played ?? 0).toBe(1);
  return { ...created, terminal };
}

async function returnHome(page) {
  await page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
}

test("an eligible fictional adult uploads private rows by POST without restoring injected history or receipts", async ({ page }) => {
  const history = existingHistory(), original = JSON.stringify(history), uploads = [];
  const user = {
    id: 901, email: "adult-parity@example.invalid", name: "Adult parity fixture", avatar: "",
    ranking_name: "", display_name: "", show_on_ranking: false, consent_completed: true,
    can_save_progress: true, is_minor: false, parental_consent_required: false,
  };
  await historyFixture(page, history);
  await page.route("**/api/me", (route) => route.fulfill({ json: { accounts_enabled: true, authenticated: true, user } }));
  const injected = { score: 999, detail: "Injected server history must stay ignored", at: FIXED_MS };
  await page.route("**/api/me/scores", async (route) => {
    uploads.push({ method: route.request().method(), url: route.request().url(), body: route.request().postDataJSON() });
    await route.fulfill({ json: { status: "ok", entries: [{ ...injected, game: "lant" }], games: {
      lant: { best: injected, played: 999, recent: [injected] },
    }, _completionReceipts: { version: 1, games: { lant: [{ id: "server-injected", at: FIXED_MS }] } } } });
  });
  const game = games.find(({ key }) => key === "intrusul");
  await deterministicStarts(page, game);
  const firstUpload = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/me/scores");
  await page.goto("/");
  await (await firstUpload).finished();
  await expect(page.locator(".account-chip")).toContainText("Adult parity fixture");
  await page.locator(".account-chip").click();
  await expect(page.getByRole("menu")).toBeVisible();
  expect(await storedScores(page)).toBe(original);
  expect(uploads).toHaveLength(1);
  expect(uploads[0].method).toBe("POST");
  expect(new URL(uploads[0].url).origin).toBe(new URL(page.url()).origin);
  expect(uploads[0].body).toEqual({ entries: [{ game: "alchimie", score: 500, detail: LOCAL_ENTRY.detail,
    at: FIXED_MS, puzzle_key: "local-existing", daily: "", difficulty: "normal", category: "" }] });
  expect(JSON.stringify(uploads[0].body)).not.toContain(SAVED_RECEIPT);
  await page.locator(".account-chip").click();

  const latestUpload = page.waitForResponse((response) => response.request().method() === "POST"
    && new URL(response.url()).pathname === "/api/me/scores");
  const { state, terminal } = await completeFree(page, game);
  await (await latestUpload).finished();
  await returnHome(page);
  const after = JSON.parse(await storedScores(page));
  expect(uploads).toHaveLength(2);
  expect(uploads.map(({ method }) => method)).toEqual(["POST", "POST"]);
  expect(uploads[1].body.entries).toHaveLength(1);
  expect(uploads[1].body.entries[0].game).toBe("intrusul");
  expect(uploads[1].body.entries[0].score).toBe(terminal.score);
  expect(uploads[1].body.entries[0].score).toBe(after.intrusul.recent[0].score);
  expect(Object.keys(uploads[1].body.entries[0]).sort()).toEqual([
    "at", "category", "daily", "detail", "difficulty", "game", "puzzle_key", "score",
  ]);
  expect(after.alchimie.recent).toEqual(history.alchimie.recent);
  expect(after._completionReceipts.games.alchimie).toEqual(history._completionReceipts.games.alchimie);
  expect(after._completionReceipts.games.intrusul.filter(({ id }) => id === state.game_id)).toHaveLength(1);
  expect(after.intrusul.played).toBe(1);
  expect(after.lant).toBeUndefined();
  expect(after._completionReceipts.games.lant).toBeUndefined();
  await expect(page.getByText(injected.detail, { exact: true })).toHaveCount(0);
  expect(JSON.stringify(uploads.map(({ body }) => body))).not.toContain(SAVED_RECEIPT);
});

test("Home keeps the exact six-card order and sole Intrusul highlight without an empty history wall", async ({ page }) => {
  await anonymous(page);
  await historyFixture(page, {});
  await page.goto("/");
  await expect(page).toHaveTitle("Cât de român ești?");
  const cards = page.locator(".games-grid .game-card");
  await expect(cards.locator(".game-card-title")).toHaveText(TITLES);
  const featured = page.locator(".game-card--featured");
  await expect(featured).toHaveCount(1);
  await expect(featured).toHaveAccessibleName("Joacă Intrusul — Începe aici");
  await expect(page.locator(".history-section")).toBeHidden();
  const importHistory = page.getByRole("button", { name: "Importă istoricul", exact: true });
  await expect(importHistory).toBeVisible();
  const bounds = await importHistory.boundingBox();
  expect(bounds.height).toBeGreaterThanOrEqual(44);
  expect(bounds.width).toBeGreaterThanOrEqual(44);
  await tabTo(page, importHistory);
  await expect(importHistory).toBeFocused();
  expect(await storedScores(page)).toBe("{}");
});

test("Home shows actual retained history instead of its first-play import action", async ({ page }) => {
  await anonymous(page);
  const history = existingHistory();
  await historyFixture(page, history);
  await page.goto("/");
  await expect(page.locator(".history-section")).toBeVisible();
  await expect(page.locator(".history-tabs")).toBeVisible();
  await expect(page.locator(".history-section").getByText(LOCAL_ENTRY.detail, { exact: true }).first()).toBeVisible();
  await expect(page.locator(".first-play-tools")).toHaveCount(0);
  expect(await storedScores(page)).toBe(JSON.stringify(history));
});

for (const width of [320, 390, 640]) {
  test(`Home retains one whole card column and a usable import control at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 920 });
    await anonymous(page);
    await historyFixture(page, {});
    await page.goto("/");
    const cards = page.locator(".games-grid .game-card");
    await expect(cards.locator(".game-card-title")).toHaveText(TITLES);
    for (const card of await cards.all()) await expect(card).toHaveCSS("opacity", "1");
    const columns = await page.locator(".games-grid").evaluate((grid) =>
      getComputedStyle(grid).gridTemplateColumns.split(/\s+/).filter(Boolean).length);
    expect(columns).toBe(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const importHistory = page.getByRole("button", { name: "Importă istoricul", exact: true });
    await importHistory.scrollIntoViewIfNeeded();
    const bounds = await importHistory.boundingBox();
    expect(bounds.height).toBeGreaterThanOrEqual(44);
    expect(bounds.width).toBeGreaterThanOrEqual(44);
    await tabTo(page, importHistory);
    await expect(importHistory).toBeInViewport();
  });
}

for (const game of games.filter(({ derived }) => derived)) {
  test(`${game.key} sends starter state and the actual previous free ID on immediate replay`, async ({ page }) => {
    await anonymous(page);
    await historyFixture(page, {});
    await deterministicStarts(page, game);
    await page.goto("/");
    const first = await completeFree(page, game);
    const firstQuery = new URL(first.response.url()).searchParams;
    expect(firstQuery.get("starter")).toBe("1");
    expect(firstQuery.get("previous_game_id")).toBeNull();
    expect(firstQuery.get("daily")).toBeNull();
    const next = creation(page, game);
    await page.getByRole("button", { name: /^Încă unul →$/, exact: true }).click();
    const response = await next;
    expect(response.status()).toBe(200);
    const query = new URL(response.url()).searchParams;
    expect(query.get("starter")).toBe("0");
    expect(query.get("previous_game_id")).toBe(first.state.game_id);
    expect(query.get("daily")).toBeNull();
    expect((await response.json()).game_id).not.toBe(first.state.game_id);
    await expect(page.locator(game.board)).toBeVisible();
  });

  test(`${game.key} retains its actual completed free ID across Home reload for the next free start`, async ({ page }) => {
    await anonymous(page);
    await historyFixture(page, {});
    await deterministicStarts(page, game);
    await page.goto("/");
    const first = await completeFree(page, game);
    await returnHome(page);
    await page.reload();
    await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
    const second = await openFreeFromHome(page, game);
    const query = new URL(second.response.url()).searchParams;
    expect(query.get("starter")).toBe("0");
    expect(query.get("previous_game_id")).toBe(first.state.game_id);
    expect(query.get("daily")).toBeNull();
    expect(second.state.game_id).not.toBe(first.state.game_id);
    expect(JSON.parse(await storedScores(page))[game.key].played).toBe(1);
  });

  test(`${game.key} omits personalization for a daily even when a completed free ID is remembered`, async ({ page }) => {
    await anonymous(page);
    await historyFixture(page, {});
    await deterministicStarts(page, game);
    await page.goto("/");
    await completeFree(page, game);
    await returnHome(page);
    await page.getByRole("button", { name: `Deschide ${TITLES[games.indexOf(game)]} — neterminat azi`, exact: true }).click();
    const next = creation(page, game);
    await page.getByRole("button", { name: "Joacă provocarea zilei", exact: true }).click();
    const response = await next;
    expect(response.status()).toBe(200);
    const query = new URL(response.url()).searchParams;
    expect(query.get("daily")).toBe("2026-10-08");
    expect(query.get("starter")).toBeNull();
    expect(query.get("previous_game_id")).toBeNull();
    expect((await response.json()).daily).toBe("2026-10-08");
    await expect(page.locator(game.board)).toBeVisible();
    expect(JSON.parse(await storedScores(page))[game.key].played).toBe(1);
  });
}
