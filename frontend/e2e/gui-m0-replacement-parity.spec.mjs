// Authored M0 behavior replacements on original E092; NOT RUN or qualification.
// Existing tests, original16/78 and inventory remain unchanged until real parity passes.
// Account/history inputs are explicit fictional adult presentation fixtures. Gameplay
// runs through the real local Go server and existing native solution helpers.
import { test, expect } from "@playwright/test";
import { games, deterministicStarts, solution, solve, tabTo } from "./games.mjs";

const SCORE_KEY = "cat_wordgame_scores_v1";
const FIXED_TIME = "2026-10-08T12:00:00.000Z";
const FIXED_MS = Date.parse(FIXED_TIME);
const TITLES = ["Intrusul", "Perechi", "Conexiuni", "Lanțul Cuvintelor", "Cald sau Rece", "Alchimie"];
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
  const created = creation(page, game);
  await page.locator(`.games-grid a[href="${game.path}"]`).click();
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
  await page.locator(".game-result").getByRole("button", { name: "Înapoi la jocuri", exact: true }).click();
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

const homeCards = (page) => page.locator(".games-grid a.game-card");

async function openResults(page, keyboard = false) {
  const results = page.getByRole("button", { name: "Rezultatele mele", exact: true });
  if (keyboard) {
    await tabTo(page, results);
    await page.keyboard.press("Enter");
  } else {
    await results.click();
  }
  const dialog = page.getByRole("dialog", { name: "Rezultatele mele", exact: true });
  await expect(dialog).toBeVisible();
  return dialog;
}

test("Home keeps the approved six-card order and opens import in the results sheet", async ({ page }) => {
  await anonymous(page);
  await historyFixture(page, {});
  await page.goto("/");
  await expect(page).toHaveTitle("Cât de român ești?");
  await expect(homeCards(page).locator("strong")).toHaveText(TITLES);
  await expect(homeCards(page).locator("img")).toHaveCount(6);
  await expect(page.getByRole("button", { name: "Importă istoricul" })).toHaveCount(0);
  const dialog = await openResults(page, true);
  const importHistory = dialog.getByRole("button", { name: "Importă istoricul", exact: true });
  const bounds = await importHistory.boundingBox();
  expect(bounds.height).toBeGreaterThanOrEqual(44);
  expect(bounds.width).toBeGreaterThanOrEqual(44);
  await tabTo(page, importHistory);
  await expect(importHistory).toBeFocused();
  expect(await storedScores(page)).toBe("{}");
});

test("the results sheet shows retained steps and leaves legacy numeric history intact", async ({ page }) => {
  await anonymous(page);
  const history = existingHistory();
  const modern = { ...LOCAL_ENTRY, at: FIXED_MS + 1, steps: 2, puzzleKey: "steps-existing" };
  history.alchimie.recent.push(modern);
  history.alchimie.played += 1;
  await historyFixture(page, history);
  await page.goto("/");
  const dialog = await openResults(page);
  const round = dialog.getByRole("listitem");
  await expect(round).toHaveCount(1);
  await expect(round).toContainText("Alchimie");
  await expect(round).toContainText("2 pași");
  await expect(dialog.getByText(LOCAL_ENTRY.detail, { exact: true })).toHaveCount(0);
  await expect(dialog.getByRole("button", { name: "Exportă istoricul" })).toBeVisible();
  expect(await storedScores(page)).toBe(JSON.stringify(history));
});

for (const width of [320, 390, 640]) {
  test(`Home retains two whole card columns and a usable import control at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 920 });
    await anonymous(page);
    await historyFixture(page, {});
    await page.goto("/");
    const cards = homeCards(page);
    await expect(cards.locator("strong")).toHaveText(TITLES);
    const columns = await page.locator(".games-grid").evaluate((grid) =>
      getComputedStyle(grid).gridTemplateColumns.split(/\s+/).filter(Boolean).length);
    expect(columns).toBe(2);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const dialog = await openResults(page, true);
    const importHistory = dialog.getByRole("button", { name: "Importă istoricul", exact: true });
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
    await page.getByRole("button", { name: "Încă o rundă", exact: true }).click();
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
    await page.clock.setFixedTime(new Date("2026-10-09T12:00:00.000Z"));
    const next = creation(page, game);
    await page.locator(`.games-grid a[href="${game.path}"]`).click();
    const response = await next;
    expect(response.status()).toBe(200);
    const query = new URL(response.url()).searchParams;
    expect(query.get("daily")).toBe("2026-10-09");
    expect(query.get("starter")).toBeNull();
    expect(query.get("previous_game_id")).toBeNull();
    expect((await response.json()).daily).toBe("2026-10-09");
    await expect(page.locator(game.board)).toBeVisible();
    expect(JSON.parse(await storedScores(page))[game.key].played).toBe(1);
  });
}
